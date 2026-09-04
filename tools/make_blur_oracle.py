"""Generate the correctness oracle for ipb_cpu_001_gaussian_blur.

    python tools/make_blur_oracle.py

Writes into tasks/ipb_cpu_001_gaussian_blur/groundtruth/:
  blur_input_256.raw     fixed pseudo-random 256x256 grayscale image
  blur_expected_256.raw  the image the correct (regressed) baseline produces
  blur_oracle.json       provenance, tolerance and the cheat margins measured

Why this exists rather than the harness checksum:
  * the benchmark fed /dev/zero, and blurring an all-zero image yields all
    zeros, so `checksum=0` held for every implementation -- including one whose
    blur_image body is deleted, which timed 0.000000s and scored improvement=1.0;
  * on a real image the baseline and the expert fix disagree by 4 in the
    checksum (separable passes round differently), so an exact-match constant
    would have rejected the expert fix itself.

Pixel-wise comparison with a tolerance separates them by a wide margin: the
expert fix is within 1 of the baseline everywhere, while identity (dst = src)
and no-op submissions are off by ~148.

The expected image comes from the baseline ref, which is slow but correct.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ipb_measure as measure      # noqa: E402
import ipb_workspace as workspace  # noqa: E402
from ipb_exec import EXEC          # noqa: E402

TASK = "ipb_cpu_001_gaussian_blur"
SEED = b"ipb-gaussian-blur-v1"
W = H = 256          # the size the task's benchmark already used
TOLERANCE = 1        # max absolute per-pixel deviation accepted


def make_image(nbytes: int) -> bytes:
    """Deterministic pseudo-random bytes; avoids a numpy dependency."""
    buf = bytearray(nbytes)
    h = hashlib.sha256(SEED).digest()
    i = 0
    while i < nbytes:
        h = hashlib.sha256(h).digest()
        n = min(len(h), nbytes - i)
        buf[i:i + n] = h[:n]
        i += n
    return bytes(buf)


def blur_with(ref: str, inp: pathlib.Path, mutate=None) -> tuple[bytes, float | None]:
    """Build one git ref (optionally patching solve.c) and return its output image."""
    task_dir = ROOT / "tasks" / TASK
    ws = workspace.clone_at_ref(task_dir, TASK, ref)
    try:
        if mutate:
            p = ws / "solve.c"
            p.write_text(mutate(p.read_text()))
        measure.build(ws)
        out = ws / "out.raw"
        proc = subprocess.run(
            ["bash", "-c", f"cd '{ws}' && ./blur '{inp}' '{out}' {W} {H}"],
            capture_output=True, text=True, timeout=900,
        )
        m = re.search(r"time=([0-9.]+)", proc.stdout + proc.stderr)
        if not out.exists():
            raise SystemExit(f"{ref}: produced no output image\n{proc.stdout}{proc.stderr}")
        return out.read_bytes(), (float(m.group(1)) * 1000 if m else None)
    finally:
        workspace.discard(ws)


def _patch_body(src: str, body: str) -> str:
    m = re.search(r"(void\s+blur_image\s*\([^)]*\)\s*\{)", src, re.S)
    if not m:
        raise SystemExit("blur_image signature not found in solve.c")
    return src[:m.end()] + body + src[m.end():]


def max_abs_diff(a: bytes, b: bytes) -> int | None:
    if len(a) != len(b) or not a:
        return None
    return max(abs(x - y) for x, y in zip(a, b))


def main():
    task_dir = ROOT / "tasks" / TASK
    gt = task_dir / "groundtruth"
    gt.mkdir(parents=True, exist_ok=True)

    img = make_image(W * H)
    inp = gt / f"blur_input_{W}.raw"
    inp.write_bytes(img)
    print(f"input    {inp.name}  {len(img)} bytes  "
          f"sha256={hashlib.sha256(img).hexdigest()[:16]}")

    base_ref = workspace.baseline_ref(task_dir / "workspace", TASK)
    expected, base_ms = blur_with(base_ref, inp)
    exp_path = gt / f"blur_expected_{W}.raw"
    exp_path.write_bytes(expected)
    print(f"expected {exp_path.name} from {base_ref} ({base_ms:.2f} ms)  "
          f"sha256={hashlib.sha256(expected).hexdigest()[:16]}")

    # Confirm the tolerance admits the expert fix and rejects doing no work.
    ref_ref = EXEC[TASK]["reference_ref"]
    ref_img, ref_ms = blur_with(ref_ref, inp)
    d_ref = max_abs_diff(expected, ref_img)
    print(f"reference {ref_ref} ({ref_ms:.2f} ms)  max|d| vs expected = {d_ref}")

    noop_img, _ = blur_with(base_ref, inp, lambda s: _patch_body(s, "\n    return;\n"))
    d_noop = max_abs_diff(expected, noop_img)
    ident_img, _ = blur_with(
        base_ref, inp,
        lambda s: _patch_body(
            s, "\n    memcpy(dst, src, (size_t)width * (size_t)height);\n"
               "    (void)passes;\n    return;\n"),
    )
    d_ident = max_abs_diff(expected, ident_img)
    print(f"no-op    max|d| = {d_noop}   identity max|d| = {d_ident}")

    if d_ref is None or d_ref > TOLERANCE:
        raise SystemExit(
            f"tolerance {TOLERANCE} would reject the expert fix (max|d|={d_ref})")
    for name, d in (("no-op", d_noop), ("identity", d_ident)):
        if d is not None and d <= TOLERANCE:
            raise SystemExit(
                f"tolerance {TOLERANCE} would accept the {name} submission "
                f"(max|d|={d}); the oracle does not separate real work from none")

    rec = {
        "task_id": TASK,
        "width": W,
        "height": H,
        "seed": SEED.decode(),
        "input_file": inp.name,
        "input_sha256": hashlib.sha256(img).hexdigest(),
        "expected_file": exp_path.name,
        "expected_sha256": hashlib.sha256(expected).hexdigest(),
        "expected_from_ref": base_ref,
        "tolerance": TOLERANCE,
        "max_abs_diff_reference": d_ref,
        "max_abs_diff_noop": d_noop,
        "max_abs_diff_identity": d_ident,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "notes": ("Pixel-wise oracle. The harness checksum cannot be used: it is "
                  "0 for any implementation on an all-zero input, and baseline "
                  "and reference differ by 4 on a real image."),
    }
    (gt / "blur_oracle.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(f"\nwrote {gt / 'blur_oracle.json'}")
    print(f"tolerance {TOLERANCE} accepts the expert fix (max|d|={d_ref}) and "
          f"rejects no-op ({d_noop}) and identity ({d_ident})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
