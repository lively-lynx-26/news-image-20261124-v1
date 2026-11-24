#!/usr/bin/env python3
"""Copy the finished front page into the harness output directory.

Entry program for the make.fun news-image-20261124 bounty. The image
itself (entry.png, 1024x1024) is a newspaper front page summing up
Tuesday 24 November 2026 in 35 dated stories across 7 regions. This
program only places a byte-exact copy of that image where the harness
expects the entry output, then proves the copy is identical. Both
the SHA-256 digest and the file size are checked, so a truncated
or corrupted copy can never pass as the finished entry.

Output directory: MAKEFUN_OUTPUT_DIR when it names a writable
directory; otherwise a folder named "output" next to this file. The
output directory is never deleted and never hard-coded to /output.
"""

import hashlib
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "entry.png"
EXPECTED_SHA256 = "64561de926496120a2b22d0f5527975161a6712161f4adff7f293cbce41f63cc"
EXPECTED_SIZE = 176114  # bytes; the front page must be at most 1 MiB


def _is_writable(directory):
    """Return True when we can create and remove a file in directory."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False
    probe = directory / ".makefun-write-probe"
    try:
        probe.write_bytes(b"probe")
        probe.unlink()
    except OSError:
        return False
    return True


def resolve_output_dir():
    """Pick the output directory, probing writability before trusting it."""
    wanted = os.environ.get("MAKEFUN_OUTPUT_DIR", "").strip()
    if wanted:
        candidate = Path(wanted).expanduser()
        if _is_writable(candidate):
            return candidate
        print(
            "MAKEFUN_OUTPUT_DIR {!r} is not writable; falling back "
            "to the repository output folder.".format(wanted),
            file=sys.stderr,
        )
    fallback = HERE / "output"
    if not _is_writable(fallback):
        raise RuntimeError("no writable output directory available")
    return fallback


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    if not SOURCE.is_file():
        print("missing source image: {}".format(SOURCE), file=sys.stderr)
        return 1
    output_dir = resolve_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / "entry.png"
    shutil.copyfile(SOURCE, destination)
    actual_size = destination.stat().st_size
    if actual_size != EXPECTED_SIZE:
        destination.unlink(missing_ok=True)
        print(
            "output has the wrong size (got {} bytes, want {}); "
            "refusing to finish.".format(actual_size, EXPECTED_SIZE),
            file=sys.stderr,
        )
        return 1
    actual = sha256_of(destination)
    if actual != EXPECTED_SHA256:
        destination.unlink(missing_ok=True)
        print(
            "output does not match the expected image "
            "(got {}, want {}); refusing to finish.".format(
                actual, EXPECTED_SHA256
            ),
            file=sys.stderr,
        )
        return 1
    print("wrote {} (sha256 {})".format(destination, actual))
    return 0


if __name__ == "__main__":
    sys.exit(main())
