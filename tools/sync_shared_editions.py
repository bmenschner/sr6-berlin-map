#!/usr/bin/env python3
"""Mirror verified shared SR1/SR2 material without duplicating entities."""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CITY_DIR = ROOT / "data" / "berlin-2080"
SR1_BOOK_ID = "deutschland-in-den-schatten"
SR2_BOOK_ID = "deutschland-in-den-schatten-1993"
SR1_TITLE = "Deutschland in den Schatten (Ausgabe 1992)"
SR2_TITLE = "Deutschland in den Schatten (Ausgabe 1993)"
EDITION_ORDER = ["SR1", "SR2", "SR3", "SR4", "SR5", "SR6"]


def sr2_source(source: dict) -> dict:
    mirrored = copy.deepcopy(source)
    mirrored["bookId"] = SR2_BOOK_ID
    mirrored["title"] = SR2_TITLE
    mirrored["edition"] = "SR2"
    citation = mirrored.get("citation", "")
    if citation.startswith("Deutschland in den Schatten"):
        suffix = citation[len("Deutschland in den Schatten") :]
        mirrored["citation"] = f"{SR2_TITLE}{suffix}"
    return mirrored


def source_signature(source: dict) -> tuple:
    return (
        source.get("bookId"),
        source.get("edition"),
        source.get("citation"),
        source.get("purpose"),
    )


def mirror_entry(entry: dict) -> bool:
    descriptions = entry.get("edition_descriptions")
    if not isinstance(descriptions, dict) or "SR1" not in descriptions:
        return False

    sr1_description = descriptions["SR1"]
    sr1_description_sources = sr1_description.get("sources", [])
    if not any(source.get("bookId") == SR1_BOOK_ID for source in sr1_description_sources):
        return False

    changed = False
    for source in entry.get("sources", []):
        if source.get("bookId") == SR1_BOOK_ID and source.get("title") != SR1_TITLE:
            source["title"] = SR1_TITLE
            changed = True
    for source in sr1_description_sources:
        if source.get("bookId") == SR1_BOOK_ID and source.get("title") != SR1_TITLE:
            source["title"] = SR1_TITLE
            changed = True

    existing_sources = {source_signature(source) for source in entry.get("sources", [])}
    mirrored_sources = [
        sr2_source(source)
        for source in entry.get("sources", [])
        if source.get("bookId") == SR1_BOOK_ID
    ]
    for source in mirrored_sources:
        if source_signature(source) not in existing_sources:
            entry.setdefault("sources", []).append(source)
            existing_sources.add(source_signature(source))
            changed = True

    if "SR2" not in entry.get("editions", []):
        entry.setdefault("editions", []).append("SR2")
        entry["editions"].sort(key=EDITION_ORDER.index)
        changed = True

    mirrored_description = copy.deepcopy(sr1_description)
    mirrored_description["sources"] = [
        sr2_source(source) if source.get("bookId") == SR1_BOOK_ID else copy.deepcopy(source)
        for source in sr1_description_sources
    ]
    if descriptions.get("SR2") != mirrored_description:
        descriptions["SR2"] = mirrored_description
        changed = True
    return changed


def entries_from(payload) -> list[dict]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and payload.get("type") == "FeatureCollection":
        return [feature.get("properties", {}) for feature in payload.get("features", [])]
    raise ValueError("Nicht unterstütztes Datenformat")


def sync_file(path: Path) -> tuple[int, bool]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    count = 0
    changed = False
    for entry in entries_from(payload):
        if mirror_entry(entry):
            count += 1
            changed = True
    if changed:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return count, changed


def main() -> int:
    files = [
        CITY_DIR / "places.geojson",
        CITY_DIR / "virtual-places.geojson",
        CITY_DIR / "historical-places.geojson",
        CITY_DIR / "place-augmentations.json",
        CITY_DIR / "people.json",
        CITY_DIR / "historical-people.json",
        CITY_DIR / "person-augmentations.json",
    ]
    total = 0
    for path in files:
        count, changed = sync_file(path)
        total += count
        state = "aktualisiert" if changed else "unverändert"
        print(f"{path.relative_to(ROOT)}: {count} Datensätze {state}")
    print(f"Gemeinsame SR1/SR2-Zuweisungen: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
