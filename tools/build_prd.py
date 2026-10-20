#!/usr/bin/env python3
"""Compatibility wrapper for legacy PRD PDF build."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    # Regenerate volume 01 and build its PDF
    subprocess.check_call([sys.executable, str(ROOT / "tools" / "generate_volumes.py")], cwd=ROOT)
    subprocess.check_call(
        [sys.executable, str(ROOT / "tools" / "build_documentation.py"), "--volume", "01"],
        cwd=ROOT,
    )
    src = ROOT / "docs" / "pdf" / "01-product-requirements.pdf"
    dst = ROOT / "docs" / "AI-Smart-Security-Platform-PRD.pdf"
    dst.write_bytes(src.read_bytes())
    print(f"Legacy PRD PDF updated: {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
