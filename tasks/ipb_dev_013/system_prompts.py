"""System prompts for ipb_dev_013."""
from pathlib import Path
_VARIANTS_DIR = Path(__file__).parent / "variants"
PROMPTS = {
    v: (_VARIANTS_DIR / f"{v}.md").read_text()
    for v in ["exact","fuzzy","misleading","target_known"]
    if (_VARIANTS_DIR / f"{v}.md").exists()
}
