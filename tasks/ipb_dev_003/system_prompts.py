"""System prompts for ipb_dev_003 variants."""

from pathlib import Path

_TASK_DIR = Path(__file__).parent
_VARIANTS_DIR = _TASK_DIR / "variants"

def _load_variant(name: str) -> str:
    """Load variant prompt from markdown file."""
    variant_file = _VARIANTS_DIR / f"{name}.md"
    if variant_file.exists():
        return variant_file.read_text()
    return ""

# Load all variants
PROMPTS = {
    "exact": _load_variant("exact"),
    "target_known": _load_variant("target_known"),
    "fuzzy": _load_variant("fuzzy"),
    "misleading": _load_variant("misleading"),
}
