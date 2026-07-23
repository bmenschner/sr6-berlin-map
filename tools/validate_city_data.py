#!/usr/bin/env python3
"""Validate all static Shadowrun city packages before publication."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data/cities.json"


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Ungültige JSON-Datei {path.relative_to(ROOT)}: {error}") from error


def validate_coordinates(coordinates, label: str) -> None:
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError(f"{label}: Koordinaten fehlen")
    if isinstance(coordinates[0], (int, float)):
        if len(coordinates) < 2:
            raise ValueError(f"{label}: Koordinatenpaar ist unvollständig")
        lon, lat = coordinates[:2]
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"{label}: ungültige Koordinaten {lon}, {lat}")
        return
    for item in coordinates:
        validate_coordinates(item, label)


def validate_feature_collection(payload: dict, label: str) -> None:
    if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise ValueError(f"{label}: keine gültige FeatureCollection")
    for index, feature in enumerate(payload["features"]):
        geometry = feature.get("geometry") or {}
        validate_coordinates(geometry.get("coordinates"), f"{label}, Feature {index + 1}")


def validate_city(city: dict, global_ids: set[str]) -> tuple[int, int]:
    manifest_path = ROOT / city["manifest"]
    manifest = read_json(manifest_path)
    if manifest.get("id") != city.get("id"):
        raise ValueError(f"{manifest_path.relative_to(ROOT)}: Stadt-ID stimmt nicht mit cities.json überein")
    city_dir = manifest_path.parent
    required = {"places", "people", "atlas", "zones", "districts", "neighborhoods", "outskirts", "boundary", "labels"}
    missing = sorted(required - set(manifest.get("files", {})))
    if missing:
        raise ValueError(f"{city['id']}: fehlende Dateiverweise: {', '.join(missing)}")
    for path in manifest["files"].values():
        if not (city_dir / path).exists():
            raise ValueError(f"{city['id']}: Datei fehlt: {path}")

    places = read_json(city_dir / manifest["files"]["places"])
    validate_feature_collection(places, f"{city['id']} Orte")
    place_ids: set[object] = set()
    for feature in places["features"]:
        properties = feature.get("properties") or {}
        place_id = properties.get("id")
        if place_id in place_ids:
            raise ValueError(f"{city['id']}: doppelte Orts-ID {place_id}")
        place_ids.add(place_id)
        global_id = properties.get("global_id")
        if not global_id or global_id in global_ids:
            raise ValueError(f"{city['id']}: fehlende oder doppelte globale Orts-ID {global_id}")
        global_ids.add(global_id)
        if not properties.get("name") or not properties.get("category"):
            raise ValueError(f"{city['id']}: Ort {place_id} ohne Name oder Kategorie")

    people = read_json(city_dir / manifest["files"]["people"])
    person_ids: set[object] = set()
    for person in people:
        person_id = person.get("id")
        if person_id in person_ids:
            raise ValueError(f"{city['id']}: doppelte Personen-ID {person_id}")
        person_ids.add(person_id)
        global_id = person.get("global_id")
        if not global_id or global_id in global_ids:
            raise ValueError(f"{city['id']}: fehlende oder doppelte globale Personen-ID {global_id}")
        global_ids.add(global_id)
        for link in person.get("locations", []):
            if link.get("id") not in place_ids:
                raise ValueError(f"{city['id']}: {person.get('name')} verweist auf unbekannten Ort {link.get('id')}")

    for key in ("zones", "districts", "neighborhoods", "outskirts", "boundary"):
        validate_feature_collection(read_json(city_dir / manifest["files"][key]), f"{city['id']} {key}")

    atlas = read_json(city_dir / manifest["files"]["atlas"])
    atlas_ids = set()
    for plan in atlas:
        if plan.get("key") in atlas_ids:
            raise ValueError(f"{city['id']}: doppelte Detailkarten-ID {plan.get('key')}")
        atlas_ids.add(plan.get("key"))
        image_path = (city_dir / plan["image"]).resolve()
        if not image_path.exists():
            raise ValueError(f"{city['id']}: Detailkarte fehlt: {plan['image']}")

    offline_base = manifest.get("assets", {}).get("offlineBase")
    if offline_base and not (city_dir / offline_base).resolve().exists():
        raise ValueError(f"{city['id']}: Offline-Kartenbasis fehlt: {offline_base}")
    return len(place_ids), len(person_ids)


def main() -> int:
    registry = read_json(REGISTRY_PATH)
    cities = registry.get("cities", [])
    if not cities:
        raise ValueError("data/cities.json enthält keine Städte")
    city_ids = [city.get("id") for city in cities]
    if len(city_ids) != len(set(city_ids)):
        raise ValueError("data/cities.json enthält doppelte Stadt-IDs")
    if sum(bool(city.get("default")) for city in cities) != 1:
        raise ValueError("Genau eine Stadt muss als Standard markiert sein")

    global_ids: set[str] = set()
    total_places = 0
    total_people = 0
    for city in cities:
        places, people = validate_city(city, global_ids)
        total_places += places
        total_people += people
        print(f"OK {city['name']} {city.get('year', '')}: {places} Orte, {people} Personen")

    search_index = read_json(ROOT / "data/search-index.json")
    if len(search_index.get("items", [])) != total_places + total_people:
        raise ValueError("Der globale Suchindex ist unvollständig")
    print(f"OK Gesamt: {len(cities)} Stadtpaket(e), {total_places} Orte, {total_people} Personen")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        print(f"FEHLER: {error}", file=sys.stderr)
        raise SystemExit(1)
