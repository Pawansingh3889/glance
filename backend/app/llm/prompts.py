"""Load versioned prompt files by name.

Prompts are code: they live under ``prompts/`` and are loaded by name + version
(e.g. ``generate_template_v1``), never inlined as string literals in services.
"""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str, **placeholders: str) -> str:
    """The prompt text, with any ``{{NAME}}`` placeholders substituted.

    Substitution is a plain replace on a doubled-brace token rather than ``str.format``:
    prompt files are prose that legitimately contains braces (JSON examples, option
    lists), and ``format`` would raise on every one of them.

    A placeholder left unfilled is an error, not a blank. A prompt that reached the model
    still saying ``{{LANGUAGE}}`` would produce plausible output in the wrong language,
    which is precisely the kind of quiet wrongness this codebase refuses.
    """
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {name}")
    text = path.read_text(encoding="utf-8").strip()

    for key, value in placeholders.items():
        text = text.replace(f"{{{{{key}}}}}", value)

    if "{{" in text:
        leftover = text[text.index("{{") : text.index("{{") + 40]
        raise ValueError(f"Prompt {name} has an unfilled placeholder near: {leftover!r}")
    return text
