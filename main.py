"""Entry program for make.fun news-image-20261124.

Copies the pre-rendered front-page image (entry.png, 1024x1024) into the
output directory named by MAKEFUN_OUTPUT_DIR, verifying the copy byte for
byte against the pinned SHA-256. Standard library only, no network.
"""

import hashlib
import os
import shutil
import sys
from pathlib import Path

EXPECTED_SHA256 = "6fd1a3ac4a6134a368a679e787144849421d1b58654935d2f1568e15f4920aee"
SOURCE_NAME = "entry.png"


def resolve_output_dir() -> Path:
    """Pick the output directory: MAKEFUN_OUTPUT_DIR if set and writable,
    otherwise <repo>/output. Never hard-codes /output and never deletes it."""
    requested = os.environ.get("MAKEFUN_OUTPUT_DIR", "").strip()
    if requested:
        candidate = Path(requested)
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".makefun_write_probe"
            probe.write_bytes(b"ok")
            probe.unlink()
            return candidate
        except OSError:
            pass
    fallback = Path(__file__).resolve().parent / "output"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    here = Path(__file__).resolve().parent
    source = here / SOURCE_NAME
    if not source.is_file():
        print(f"missing source image: {source}", file=sys.stderr)
        return 1
    if sha256_of(source) != EXPECTED_SHA256:
        print("source image hash mismatch; refusing to copy", file=sys.stderr)
        return 1
    out_dir = resolve_output_dir()
    target = out_dir / SOURCE_NAME
    shutil.copyfile(source, target)
    # The copy must be byte-identical to the pinned source; a partial or
    # altered copy is a failure, not a best-effort result.
    if sha256_of(target) != EXPECTED_SHA256:
        print("copied image hash mismatch", file=sys.stderr)
        return 1
    print(f"wrote {target} ({EXPECTED_SHA256[:12]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
