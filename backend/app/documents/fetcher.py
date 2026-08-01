"""Guarded fetcher for the URL half of "give it a form or a link, discuss it".

User-supplied URLs fetched server-side are the textbook SSRF vector. Every control
here maps to a concrete step: scheme allowlist, resolve-then-check (every check runs
against a resolved address, never the raw URL string), pin the validated address for
the actual connection so a second, unvalidated DNS lookup at connect time can't rebind
to something else, re-validate on every redirect, and hard limits on time/size/content
type. Network-level egress isolation (routing this fetcher through a firewall that only
permits outbound 443 to the internet) is a deployment concern, not this module's job —
everything below is the application-layer half of the control, meant to fail closed on
its own but not meant to be the only layer.
"""

import asyncio
import ipaddress
import logging
import socket
import ssl
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpcore
import httpx

from app.config import Settings
from app.documents.parsing import SUPPORTED_CONTENT_TYPES
from app.errors import ValidationError

logger = logging.getLogger("app.documents.fetcher")

_ALLOWED_SCHEME = "https"


@dataclass(frozen=True)
class FetchedDocument:
    content: bytes
    content_type: str
    final_url: str


class _PinnedNetworkBackend(httpcore.AsyncNetworkBackend):
    """Dials the pre-validated address regardless of the hostname httpcore is given.

    httpcore normally resolves the request's hostname itself, at connect time — a
    second, unvalidated lookup after the one this fetcher already checked. That gap is
    the DNS-rebinding bypass: the attacker's domain resolves to a public address for
    the check and a private one moments later for the real fetch. Ignoring the
    hostname here and always dialling the address this fetcher already validated
    closes it. The Host header and TLS SNI are untouched — httpx derives those from the
    request's URL, not from what a network backend connects to, so certificate
    validation still checks the real hostname.
    """

    def __init__(self, pinned_ip: str) -> None:
        self._pinned_ip = pinned_ip
        self._inner = httpcore.AnyIOBackend()

    # noqa: ASYNC109 on `timeout` below — overrides httpcore.AsyncNetworkBackend's own
    # signature, which httpcore calls by keyword; it can't be renamed or dropped.
    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,  # noqa: ASYNC109
        local_address: str | None = None,
        socket_options: object = None,
    ) -> httpcore.AsyncNetworkStream:
        return await self._inner.connect_tcp(
            self._pinned_ip,
            port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,  # type: ignore[arg-type]
        )

    async def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,  # noqa: ASYNC109
        socket_options: object = None,
    ) -> httpcore.AsyncNetworkStream:
        raise NotImplementedError("the document fetcher never uses a unix socket")

    async def sleep(self, seconds: float) -> None:
        await self._inner.sleep(seconds)


class _PinnedHTTPTransport(httpx.AsyncHTTPTransport):
    def __init__(self, pinned_ip: str) -> None:
        super().__init__()
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=ssl.create_default_context(),
            network_backend=_PinnedNetworkBackend(pinned_ip),
            retries=0,
        )


def _is_disallowed(
    ip: ipaddress.IPv4Address | ipaddress.IPv6Address,
    denied: list[ipaddress.IPv4Network | ipaddress.IPv6Network],
) -> bool:
    # An IPv4-mapped IPv6 address (::ffff:127.0.0.1) is the classic bypass for a check
    # that only inspects the outer address family — validate the embedded v4 address.
    mapped = ip.ipv4_mapped if isinstance(ip, ipaddress.IPv6Address) else None
    if mapped is not None:
        ip = mapped
    if (
        ip.is_private  # RFC1918 and the other IANA special-use blocks
        or ip.is_loopback
        or ip.is_link_local  # covers 169.254.169.254, the cloud metadata address
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return True
    return any(ip in network for network in denied if ip.version == network.version)


async def _resolve_and_pin(hostname: str, settings: Settings) -> str:
    """Resolve once, validate every candidate, and return one address to connect to.

    Every resolved address is checked, not just the one that ends up pinned — a
    resolver can return a mix of addresses, and trusting "the first one looked fine"
    reopens the gap this function exists to close.
    """
    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValidationError(f"Could not resolve host: {hostname}") from exc
    candidates = {str(info[4][0]) for info in infos}
    if not candidates:
        raise ValidationError(f"Could not resolve host: {hostname}")
    denied = [ipaddress.ip_network(cidr) for cidr in settings.documents_fetch_denied_cidrs]
    for raw_ip in candidates:
        ip = ipaddress.ip_address(raw_ip)
        if _is_disallowed(ip, denied):
            logger.warning(
                "fetch refused: host=%s resolved=%s reason=disallowed_address", hostname, ip
            )
            raise ValidationError(
                "That URL's host resolves to an address this service will not fetch."
            )
    return _pin(candidates)


def _pin(candidates: set[str]) -> str:
    """Pick one validated address to connect to, preferring IPv4.

    ``candidates`` is a set, so iterating it directly picks an arbitrary one — on a
    host where outbound IPv6 is not actually routed (common in constrained or
    sandboxed environments, this one included) that arbitrarily selects an address
    DNS validated but nothing can reach, and the fetch fails with a connection error
    that looks unrelated to the real cause. IPv4 reachability is the far safer default
    to assume.
    """
    ipv4 = [c for c in candidates if ipaddress.ip_address(c).version == 4]
    return ipv4[0] if ipv4 else next(iter(candidates))


async def fetch_url(url: str, settings: Settings) -> FetchedDocument:
    """Fetch a user-supplied URL under every control in the design note's §5.

    Redirects are followed manually, capped at ``documents_fetch_max_redirects``, and
    each hop re-runs scheme/resolve/validate from scratch — a public URL that
    redirects to a private one is the standard bypass for a check that only ever looks
    at the URL the user typed.
    """
    current = url
    for hop in range(settings.documents_fetch_max_redirects + 1):
        parsed = urlsplit(current)
        if parsed.scheme != _ALLOWED_SCHEME:
            raise ValidationError("Only https:// URLs can be fetched.")
        if not parsed.hostname:
            raise ValidationError("That URL has no host.")
        pinned_ip = await _resolve_and_pin(parsed.hostname, settings)
        transport = _PinnedHTTPTransport(pinned_ip=pinned_ip)
        timeout = httpx.Timeout(settings.documents_fetch_timeout_seconds)
        try:
            async with (
                httpx.AsyncClient(
                    transport=transport, follow_redirects=False, timeout=timeout
                ) as client,
                client.stream("GET", current) as response,
            ):
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise ValidationError("Redirected with no Location header.")
                    current = urljoin(current, location)
                    logger.info("fetch redirect: original=%s hop=%d -> %s", url, hop, current)
                    continue
                if response.status_code != 200:
                    raise ValidationError(
                        f"Fetch failed: the server returned {response.status_code}."
                    )
                content_type = (
                    response.headers.get("content-type", "").split(";")[0].strip().lower()
                )
                if content_type not in SUPPORTED_CONTENT_TYPES:
                    raise ValidationError(f"Unsupported content type: {content_type or 'unknown'}.")
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > settings.documents_fetch_max_bytes:
                        raise ValidationError("The fetched document exceeded the size limit.")
                logger.info(
                    "fetch ok: url=%s resolved_ip=%s bytes=%d content_type=%s",
                    url,
                    pinned_ip,
                    len(body),
                    content_type,
                )
                return FetchedDocument(
                    content=bytes(body), content_type=content_type, final_url=current
                )
        except httpx.HTTPError as exc:
            logger.warning("fetch failed: url=%s resolved_ip=%s error=%s", url, pinned_ip, exc)
            raise ValidationError(f"Could not fetch that URL: {exc}") from exc
    raise ValidationError("Too many redirects.")
