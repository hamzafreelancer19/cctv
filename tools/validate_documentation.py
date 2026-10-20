#!/usr/bin/env python3
"""Validate enterprise documentation sources."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOLUMES = ROOT / "docs" / "volumes"
MANIFEST = ROOT / "docs" / "document-manifest.json"
TRACE = ROOT / "docs" / "traceability-matrix.csv"

REQUIRED_VOLUMES = [f"{i:02d}-" for i in range(1, 11)]
ID_PATTERN = re.compile(r"\b(BR|FR|NFR|UC|DB|API|AI|UI|OPS|TEST|RISK)-[A-Z0-9-]+\b")


def main() -> int:
    errors: list[str] = []

    for prefix in REQUIRED_VOLUMES:
        matches = list(VOLUMES.glob(f"{prefix}*.md"))
        if not matches:
            errors.append(f"Missing volume source with prefix {prefix}")

    all_ids: set[str] = set()
    for md in VOLUMES.glob("*.md"):
        text = md.read_text(encoding="utf-8")
        if "TODO" in text or "TBD" in text:
            errors.append(f"Unresolved placeholder in {md.name}")
        ids = set(ID_PATTERN.findall(text))
        # fix: findall with groups returns only prefix; use finditer
        ids = {m.group(0) for m in ID_PATTERN.finditer(text)}
        all_ids.update(ids)
        if len(text.splitlines()) < 50:
            errors.append(f"Volume too short (<50 lines): {md.name}")

    if not TRACE.exists():
        errors.append("Missing traceability matrix")
    else:
        with TRACE.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            if len(rows) < 5:
                errors.append("Traceability matrix has fewer than 5 rows")

    if MANIFEST.exists():
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if len(data.get("volumes", [])) < 10:
            errors.append("Manifest missing volume entries")

    print(f"Discovered {len(all_ids)} unique requirement/API IDs across volumes")
    if errors:
        print("Validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("Validation PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
