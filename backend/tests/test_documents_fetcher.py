"""The SSRF-guarded fetcher.

``_is_disallowed`` carries the actual security decision and is tested directly, with
no I/O at all. ``fetch_url``'s scheme/host checks run before any resolution, so those
are also offline. Two tests do touch the real network — resolving ``localhost`` (never
leaves the machine) and one fetch against ``https://example.com/``, IANA's own
stable example domain, chosen so the pin-and-connect path this module hand-rolls is
proven against a real TLS handshake and not just its own unit tests.
"""

import ipaddress

import pytest

from app.config import Settings
from app.documents.fetcher import _is_disallowed, _pin, _resolve_and_pin, fetch_url
from app.errors import ValidationError

DB = "postgresql+asyncpg://glance:glance@localhost:5432/glance"


def _settings(**overrides) -> Settings:
    return Settings(database_url=DB, _env_file=None, **overrides)


def _ip(text: str):
    return ipaddress.ip_address(text)


@pytest.mark.parametrize(
    "address,reason",
    [
        ("10.1.2.3", "RFC1918"),
        ("172.16.0.1", "RFC1918"),
        ("192.168.1.1", "RFC1918"),
        ("127.0.0.1", "loopback"),
        ("169.254.169.254", "link-local / cloud metadata"),
        ("224.0.0.1", "multicast"),
        ("::1", "IPv6 loopback"),
        ("fc00::1", "IPv6 unique local"),
        ("fe80::1", "IPv6 link-local"),
        ("::ffff:127.0.0.1", "IPv4-mapped IPv6 loopback — the classic bypass"),
        ("::ffff:10.0.0.5", "IPv4-mapped IPv6 RFC1918"),
    ],
)
def test_disallowed_addresses_are_rejected(address, reason):
    assert _is_disallowed(_ip(address), denied=[]) is True, reason


@pytest.mark.parametrize("address", ["93.184.216.34", "2001:4860:4860::8888"])
def test_ordinary_public_addresses_are_allowed(address):
    assert _is_disallowed(_ip(address), denied=[]) is False


def test_an_operator_denylist_blocks_an_otherwise_public_address():
    """DOCUMENTS_FETCH_DENIED_CIDRS covers ranges no built-in rule knows about — a
    plant's own address space, for instance."""
    denied = [ipaddress.ip_network("93.184.0.0/16")]
    assert _is_disallowed(_ip("93.184.216.34"), denied=denied) is True
    assert _is_disallowed(_ip("93.184.216.34"), denied=[]) is False


def test_pin_prefers_ipv4_over_ipv6():
    """A resolver returning both is picked from a set — nondeterministic order — and on
    a host where outbound IPv6 isn't actually routed (this sandbox included), pinning
    whichever one came out first can silently connect to an unreachable address. A live
    run against this exact fetcher failed exactly this way."""
    assert _pin({"2606:4700:10::6814:179a", "93.184.216.34"}) == "93.184.216.34"


def test_pin_falls_back_to_ipv6_when_nothing_else_resolved():
    assert _pin({"2606:4700:10::6814:179a"}) == "2606:4700:10::6814:179a"


async def test_only_https_is_allowed():
    with pytest.raises(ValidationError, match="https"):
        await fetch_url("http://example.com/", _settings())


async def test_a_url_with_no_host_is_refused_before_any_lookup():
    with pytest.raises(ValidationError):
        await fetch_url("https:///no-host-here", _settings())


async def test_resolving_localhost_is_refused_as_loopback():
    """A real resolution (localhost never leaves the machine, so this needs no
    network), proving resolve -> validate -> reject end to end, not just the
    classifier in isolation."""
    with pytest.raises(ValidationError):
        await _resolve_and_pin("localhost", _settings())


async def test_a_denylist_covering_the_whole_internet_refuses_a_real_public_host():
    """DOCUMENTS_FETCH_DENIED_CIDRS threaded all the way from Settings through to the
    fetch — proven against a real resolution rather than a mocked one. No connection is
    ever opened: resolution is rejected before any socket is touched."""
    settings = _settings(documents_fetch_denied_cidrs=["0.0.0.0/0", "::/0"])
    with pytest.raises(ValidationError):
        await fetch_url("https://example.com/", settings)


async def test_fetching_a_real_https_url_pins_the_resolved_address_and_succeeds():
    """The one test in this suite allowed to touch a real external host — it exists to
    prove the hand-rolled IP-pinning transport (fetcher.py's _PinnedHTTPTransport)
    actually completes a real TLS handshake against the address it resolved, with SNI
    and certificate verification still checked against the real hostname. Everything
    else about the fetcher is covered without leaving the machine.
    """
    fetched = await fetch_url("https://example.com/", _settings())

    assert fetched.content_type == "text/html"
    assert b"Example Domain" in fetched.content
    assert fetched.final_url == "https://example.com/"


async def test_fetching_a_response_over_the_size_limit_is_refused():
    settings = _settings(documents_fetch_max_bytes=10)  # example.com's page is well over 10 bytes
    with pytest.raises(ValidationError, match="size limit"):
        await fetch_url("https://example.com/", settings)
