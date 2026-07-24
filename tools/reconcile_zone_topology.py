#!/usr/bin/env python3
"""Turn independently traced Berlin status zones into a disjoint partition."""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

try:
    from shapely.geometry import Polygon, box, mapping, shape
    from shapely.ops import transform, unary_union
except ImportError as error:
    Polygon = box = mapping = shape = transform = unary_union = None
    SHAPELY_IMPORT_ERROR = error
else:
    SHAPELY_IMPORT_ERROR = None


ROOT = Path(__file__).resolve().parents[1]
CITY_DIR = ROOT / "data" / "berlin-2080"
ZONES_PATH = CITY_DIR / "zones.geojson"
RAW_ZONES_PATH = ROOT / "output" / "data" / "berlin-2080-gebiete.geojson"
DISTRICTS_PATH = CITY_DIR / "districts.geojson"
NEIGHBORHOODS_PATH = CITY_DIR / "neighborhoods.geojson"
OUTSKIRTS_PATH = CITY_DIR / "outskirts.geojson"
EXTRATERRITORIAL_PATH = CITY_DIR / "exterritorial.geojson"
EXTER_BOUNDARY_GUIDES_PATH = CITY_DIR / "exter-boundary-guides.geojson"
EARTH_RADIUS_METERS = 6_378_137
RENRAKUSAN_DEFENSIVE_EXPANSION_METERS = 45
ZIC_BERNAUER_EXCLUSION_METERS = 12
ZIC_A111_CLAIM_METERS = 32
ZIC_KSD_CLAIM_METERS = 22
ZIC_DICKE_MARIE_SECURITY_ZONE_METERS = 90

NORMAL_DISTRICT_BASES = {
    "Mitte",
    "Charlottenburg-Wilmersdorf",
    "Steglitz-Zehlendorf",
    "Tempelhof-Schöneberg",
    "Reinickendorf",
}
ANARCHO_DISTRICT_BASES = {
    "Friedrichshain-Kreuzberg",
    "Pankow",
    "Spandau",
    "Neukölln",
    "Treptow-Köpenick",
    "Marzahn-Hellersdorf",
    "Lichtenberg",
}
NORMAL_OUTSKIRTS = {"Potsdam", "Schönefeld", "Strausberg"}
ANARCHO_OUTSKIRTS = {"Falkensee", "Oranienburg"}

COMMON_BASIS = (
    "Berlin 2080 Karte v06; Lore-Bezirke aus Berlin 2080 und Netzgewitter; "
    "ALKIS-Bezirksgrenzen und amtliche Gemeindegeometrien"
)
COMMON_SOURCES = [
    "Berlin 2080 Karte v06 - Übersicht",
    "Berlin 2080, S. 27-77",
    "Netzgewitter, S. 18-19",
    "Berlin 4D, S. 84",
]

CORPORATE_NOTES = {
    1: [
        "AZT Schönwalde ist auf den offiziellen Berlin-2080-Übersichten als orange Exterritorialfläche im Lore-Umland markiert.",
        "Der Straßen-, Gewässer- und Siedlungsabgleich dieser Fläche steht noch aus.",
    ],
    2: [
        "Die Grenze des Flughafengeländes folgt im Westen und Südwesten der Bernauer Straße; der Straßenkörper bleibt außerhalb des Z-IC.",
        "Die Kleingartenanlagen zwischen Flughafengelände und Berlin-Spandauer-Schifffahrtskanal bleiben bis an die Bernauer Straße Bestandteil des Z-IC.",
        "Die A111 wird als vollständiger, verteidigbarer Verkehrskorridor beansprucht; der Kurt-Schumacher-Damm setzt diese Grenze nach Süden fort.",
        "Der gesamte Tegeler See einschließlich Großem Malchsee sowie Hasselwerder, Lindwerder und Reiswerder gehört zum Z-IC.",
        "Alt-Tegel wird bis zur tatsächlichen Außenkante des Tegeler Forsts beansprucht; die Waldfläche selbst bleibt Reinickendorf.",
        "An der Dicken Marie wird nur die im Quellenband belegte lokale Z-IC-Sicherheitszone ergänzt, nicht der umliegende Forst.",
        "Die Grenze zur AGC-Siemensstadt wird beim Standort Gotcha ausdrücklich erwähnt.",
    ],
    5: [
        "AGC Siemensstadt umfasst das frühere Siemensstadt und den früher Charlottenburg-Nord genannten Bereich Siemensstätten.",
        "Berlin 2080 bezeichnet den gesamten Konzernbezirk ausdrücklich als exterritorial.",
        "Die Außengrenze folgt deshalb den amtlichen Ortsteilgrenzen von Siemensstadt und Charlottenburg-Nord.",
    ],
    3: [
        "Renrakusan entspricht dem vollständig neu aufgebauten Konzernbezirk auf Basis des früheren Prenzlauer Bergs.",
        "Nur große historische Straßenverläufe, darunter die frühere Prenzlauer Allee, blieben erhalten.",
        "Die amtliche Ortsteilgrenze von Prenzlauer Berg liefert die Grundlinie an Ringbahn/A100, Bornholmer Straße, Wisbyer Straße, Ostseestraße und den südlichen Hauptstraßen.",
        "Die Grenze wurde defensiv nach außen erweitert, damit Straßen- und Bahnkorridore vollständig zum Konzerngebiet gehören.",
    ],
    4: [
        "S-K Tempelhof wird durch Flughafen Tempelhof und die angrenzenden Konzernquartiere bestimmt.",
        "Berlin 4D beschreibt die bewachte Flughafenmauer an der Schillerpromenade als Grenze zu Kreuzberg.",
        "Berlin 2080 nennt Alt-Tempelhof südlich und Neukölln beziehungsweise Rixdorf östlich des Flughafens.",
    ],
}

CORPORATE_REVIEW = {
    1: ("pending", "Vorläufig - geografischer Detailabgleich ausstehend"),
    2: ("reviewed", "Geprüft - Z-IC Tegel, EXTER-Neuzeichnung Phase 3"),
    3: ("reviewed", "Geprüft - Renrakusan, EXTER-Neuzeichnung Phase 1"),
    4: ("pending", "Vorläufig - geografischer Detailabgleich ausstehend"),
    5: ("pending", "Vorläufig - geografischer Detailabgleich ausstehend"),
}


def require_shapely() -> None:
    if SHAPELY_IMPORT_ERROR is not None:
        raise RuntimeError(
            "Shapely fehlt. Unter Ubuntu kann es mit "
            "`sudo apt-get install python3-shapely` installiert werden."
        ) from SHAPELY_IMPORT_ERROR


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def cleaned(feature):
    return shape(feature["geometry"]).buffer(0)


def reference_union(features: list[dict], property_name: str, accepted: set[str]):
    geometries = [
        cleaned(feature)
        for feature in features
        if feature.get("properties", {}).get(property_name) in accepted
    ]
    return unary_union(geometries).buffer(0)


def buffer_meters(geometry, distance: float):
    """Buffer a WGS84 geometry in Web Mercator metres for street-corridor claims."""

    def project(lon, lat, z=None):
        x = EARTH_RADIUS_METERS * math.radians(lon)
        limited_lat = max(min(lat, 89.5), -89.5)
        y = EARTH_RADIUS_METERS * math.log(
            math.tan(math.pi / 4 + math.radians(limited_lat) / 2)
        )
        return x, y

    def unproject(x, y, z=None):
        lon = math.degrees(x / EARTH_RADIUS_METERS)
        lat = math.degrees(2 * math.atan(math.exp(y / EARTH_RADIUS_METERS)) - math.pi / 2)
        return lon, lat

    projected = transform(project, geometry)
    latitude_scale = math.cos(math.radians(geometry.centroid.y))
    expanded = projected.buffer(distance / latitude_scale, join_style=2)
    return transform(unproject, expanded).buffer(0)


def exter_boundary_guides() -> dict[str, object]:
    if not EXTER_BOUNDARY_GUIDES_PATH.exists():
        raise FileNotFoundError(
            f"EXTER-Grenzleitlinien fehlen: {EXTER_BOUNDARY_GUIDES_PATH}"
        )
    guides = load(EXTER_BOUNDARY_GUIDES_PATH)
    return {
        feature["properties"]["id"]: shape(feature["geometry"])
        for feature in guides["features"]
    }


def refine_zic_tegel(raw_geometry, neighborhoods: dict):
    """Rebuild Z-IC Tegel around defensible road and water boundaries."""

    guides = exter_boundary_guides()
    required = {
        "zic-bernauer-strasse",
        "zic-a111",
        "zic-kurt-schumacher-damm-sued",
        "zic-tegeler-see",
        "zic-grosser-malchsee",
        "zic-tegeler-forst-sued",
        "zic-dicke-marie",
    }
    missing = required.difference(guides)
    if missing:
        raise ValueError(
            "Z-IC-Grenzleitlinien unvollständig: " + ", ".join(sorted(missing))
        )

    bernauer = guides["zic-bernauer-strasse"]
    a111 = guides["zic-a111"]
    kurt_schumacher_damm = guides["zic-kurt-schumacher-damm-sued"]
    tegeler_see = guides["zic-tegeler-see"]
    grosser_malchsee = guides["zic-grosser-malchsee"]
    tegeler_forst = guides["zic-tegeler-forst-sued"]
    dicke_marie = guides["zic-dicke-marie"]

    bernauer_coords = list(bernauer.coords)
    a111_coords = list(a111.coords)
    if bernauer_coords[0][0] > bernauer_coords[-1][0]:
        bernauer_coords.reverse()
    if a111_coords[0][1] < a111_coords[-1][1]:
        a111_coords.reverse()

    # Bernauer Straße and A111 form the two hard sides of the old airport
    # lobe. The far-south closing points only bound the construction mask;
    # the actual coverage still comes from the official raster footprint.
    airport_mask = Polygon(
        [
            *bernauer_coords,
            *a111_coords,
            (13.305, 52.542),
            (13.235, 52.542),
            bernauer_coords[0],
        ]
    ).buffer(0)

    airport = raw_geometry.intersection(airport_mask)
    airport = airport.difference(
        buffer_meters(bernauer, ZIC_BERNAUER_EXCLUSION_METERS)
    )

    # The new northern claim is rebuilt from the modern Tegel locality, but
    # stops exactly at the mapped woodland edge. This fills Alt-Tegel and the
    # harbour without retaining the raster artefacts that protruded into the
    # Tegeler Forst.
    tegel_locality = reference_union(
        neighborhoods["features"],
        "name",
        {"Tegel"},
    )
    alt_tegel = (
        tegel_locality
        .intersection(box(13.252, 52.5748, 13.322, 52.6002))
        .difference(tegeler_forst)
        .buffer(0)
    )

    a111_claim = buffer_meters(a111, ZIC_A111_CLAIM_METERS).intersection(
        box(13.27, 52.54, 13.33, 52.58)
    )
    ksd_claim = buffer_meters(
        kurt_schumacher_damm,
        ZIC_KSD_CLAIM_METERS,
    ).intersection(box(13.27, 52.532, 13.32, 52.542))
    dicke_marie_claim = buffer_meters(
        dicke_marie,
        ZIC_DICKE_MARIE_SECURITY_ZONE_METERS,
    )

    return unary_union(
        [
            alt_tegel,
            airport,
            tegeler_see,
            grosser_malchsee,
            dicke_marie_claim,
            a111_claim,
            ksd_claim,
        ]
    ).intersection(box(13.225, 52.532, 13.34, 52.61)).buffer(0)


def normalize_raw_zones(zones: dict) -> dict:
    """Add status properties when the unreconciled raster extraction is used."""
    statuses = {
        "magenta": ("normal", "Normales Gebiet", "#ff2ea6"),
        "grau": ("anarcho", "Anarcho-Gebiet", "#59616e"),
        "orange": ("corporate", "Exterritoriales Konzerngebiet", "#f5f06a"),
    }
    corporate_labels = {
        1: "AZT Schönwalde",
        2: "Z-IC Tegel / AGC Siemensstadt",
        3: "Renrakusan",
        4: "S-K Tempelhof",
    }
    features = []
    for feature in zones["features"]:
        properties = feature["properties"]
        if "status" in properties:
            features.append(feature)
            continue
        status, label, color = statuses[properties["zone_type"]]
        if status == "corporate":
            label = f"{label} · {corporate_labels[properties['component']]}"
        features.append(
            {
                **feature,
                "properties": {
                    **properties,
                    "status": status,
                    "label": label,
                    "color": color,
                },
            }
        )
    return {**zones, "features": features}


def status_feature(status: str, geometry):
    style = {
        "normal": ("magenta", "Normales Gebiet", "#ff2ea6"),
        "anarcho": ("grau", "Anarcho-Gebiet", "#59616e"),
    }[status]
    notes = [
        (
            "Die gemeinsame Normal-/Anarchogrenze folgt vollständig den Lore-Bezirken. "
            "Die amtlichen Bezirks- und Gemeindegrenzen korrigieren dabei sowohl "
            "Überlappungen als auch falsch zugeordnete Einzelstreifen der Rastervorlage."
        )
    ]
    if status == "anarcho":
        notes.append(
            "Netzgewitter, S. 18-19, ordnet den Caligarikiez dem Pankower Dreamland zu "
            "und zeigt Pankow nördlich der Wisbyer Straße unmittelbar an Renrakusan anschließend."
        )
    return {
        "type": "Feature",
        "geometry": mapping(geometry.buffer(0)),
        "properties": {
            "zone_type": style[0],
            "label": style[1],
            "color": style[2],
            "source": "Berlin 2080 Karte v06 - Übersicht",
            "component": 1,
            "status": status,
            "topology": "disjoint",
            "basis": COMMON_BASIS,
            "lore_boundary_sources": COMMON_SOURCES,
            "lore_boundary_notes": notes,
        },
    }


def corporate_feature(feature: dict, geometry, component: int, label: str, basis: str):
    review_status, review_label = CORPORATE_REVIEW[component]
    properties = {
        **feature["properties"],
        "component": component,
        "label": f"Exterritoriales Konzerngebiet · {label}",
        "topology": "disjoint",
        "basis": basis,
        "boundary_review_status": review_status,
        "boundary_review_label": review_label,
        "lore_boundary_sources": COMMON_SOURCES,
        "lore_boundary_notes": CORPORATE_NOTES.get(
            component,
            ["Die Grenze folgt der farblich markierten Exterritorialfläche der offiziellen Übersichtskarte."],
        ),
    }
    return {"type": "Feature", "geometry": mapping(geometry.buffer(0)), "properties": properties}


def corporate_features(features: list[dict], districts: dict, neighborhoods: dict):
    by_component = {
        feature["properties"]["component"]: feature
        for feature in features
    }
    raw_aztech = cleaned(by_component[1])
    raw_west = cleaned(by_component[2])
    raw_tempelhof = cleaned(by_component[4])

    agc = reference_union(
        neighborhoods["features"],
        "name",
        {"Siemensstadt", "Charlottenburg-Nord"},
    )
    renrakusan_base = reference_union(districts["features"], "name", {"Renrakusan"})
    renrakusan = buffer_meters(
        renrakusan_base,
        RENRAKUSAN_DEFENSIVE_EXPANSION_METERS,
    )
    if agc.is_empty or renrakusan.is_empty:
        raise ValueError("Amtliche Referenzgeometrie für AGC Siemensstadt oder Renrakusan fehlt")

    # The overview joins Z-IC and AGC in one orange raster component. Split it
    # at the exact AGC district edge before the status partition is calculated.
    zic = refine_zic_tegel(
        raw_west.difference(agc).buffer(0),
        neighborhoods,
    )
    candidates = [
        corporate_feature(
            by_component[1],
            raw_aztech,
            1,
            "AZT Schönwalde",
            "Berlin 2080 Karten v04/v06; vorläufige Farbfläche im Lore-Umland",
        ),
        corporate_feature(
            by_component[2],
            zic,
            2,
            "Z-IC Tegel",
            (
                "Berlin 2080, S. 75-77; Berlin 2080 Karte v06; ÜK50- und "
                "OpenStreetMap-Abgleich von Bernauer Straße, A111 und "
                "Kurt-Schumacher-Damm; Tegeler See einschließlich Großem "
                "Malchsee und Inseln; Alt-Tegel bis zum Tegeler Forst"
            ),
        ),
        corporate_feature(
            by_component[2],
            agc,
            5,
            "AGC Siemensstadt",
            "Berlin 2080, S. 28-31; ALKIS-Ortsteile Siemensstadt und Charlottenburg-Nord",
        ),
        corporate_feature(
            by_component[3],
            renrakusan,
            3,
            "Renrakusan",
            (
                "Berlin 2080, S. 60-63 und S. 89; Netzgewitter, S. 18-19; "
                "ALKIS-Ortsteil Prenzlauer Berg; ÜK50-Straßen- und Bahnabgleich; "
                f"{RENRAKUSAN_DEFENSIVE_EXPANSION_METERS} m defensive Korridorerweiterung"
            ),
        ),
        corporate_feature(
            by_component[4],
            raw_tempelhof,
            4,
            "S-K Tempelhof",
            "Berlin 2080 Karte v06; Flughafenmauer, Fliegerviertel, Alt-Tempelhof und Karl-Marx-Straße",
        ),
    ]

    result = []
    occupied = None
    for feature in candidates:
        geometry = cleaned(feature)
        if occupied is not None:
            geometry = geometry.difference(occupied).buffer(0)
        occupied = geometry if occupied is None else unary_union([occupied, geometry]).buffer(0)
        properties = {
            **feature["properties"],
        }
        result.append({"type": "Feature", "geometry": mapping(geometry.buffer(0)), "properties": properties})
    return result


def reconcile(zones: dict, districts: dict, neighborhoods: dict, outskirts: dict) -> dict:
    require_shapely()
    zones = normalize_raw_zones(zones)
    by_status: dict[str, list[dict]] = {}
    for feature in zones["features"]:
        by_status.setdefault(feature["properties"]["status"], []).append(feature)

    raw_normal = unary_union([cleaned(feature) for feature in by_status["normal"]]).buffer(0)
    raw_anarcho = unary_union([cleaned(feature) for feature in by_status["anarcho"]]).buffer(0)
    corporate = corporate_features(by_status["corporate"], districts, neighborhoods)
    corporate_union = unary_union([cleaned(feature) for feature in corporate]).buffer(0)
    previous_overlap = (
        raw_normal.intersection(raw_anarcho).area
        + raw_normal.intersection(corporate_union).area
        + raw_anarcho.intersection(corporate_union).area
    )

    normal_reference = unary_union(
        [
            reference_union(districts["features"], "basis", NORMAL_DISTRICT_BASES),
            reference_union(outskirts["features"], "name", NORMAL_OUTSKIRTS),
        ]
    ).buffer(0)
    anarcho_reference = unary_union(
        [
            reference_union(districts["features"], "basis", ANARCHO_DISTRICT_BASES),
            reference_union(outskirts["features"], "name", ANARCHO_OUTSKIRTS),
        ]
    ).buffer(0)

    # Build a complete, exclusive partition from the hard Lore boundaries.
    # EXTER wins first, the anarchist districts win the shared civil boundary,
    # and normal territory receives only the remaining district area.
    anarcho = anarcho_reference.difference(corporate_union).buffer(0)
    normal = (
        normal_reference
        .difference(corporate_union)
        .difference(anarcho)
        .buffer(0)
    )
    referenced = unary_union([normal_reference, anarcho_reference]).buffer(0)
    classified_reference = unary_union([normal, anarcho, corporate_union]).buffer(0)
    unclassified_reference = referenced.difference(classified_reference).buffer(0)

    features = [
        status_feature("normal", normal),
        status_feature("anarcho", anarcho),
        *corporate,
    ]
    for first, second in itertools.combinations(features, 2):
        overlap = cleaned(first).intersection(cleaned(second)).area
        if overlap > 1e-12:
            raise ValueError(
                f"Gebietsüberlappung bleibt bestehen: "
                f"{first['properties']['label']} / {second['properties']['label']} ({overlap})"
            )

    unresolved_overlap = sum(
        cleaned(first).intersection(cleaned(second)).area
        for first, second in itertools.combinations(features, 2)
    )
    return {
        "type": "FeatureCollection",
        "name": "Shadowrun Berlin 2080 - disjunkte Gebietsflächen",
        "topology": {
            "model": "exclusive-partition",
            "priority": ["corporate", "anarcho", "normal"],
            "previous_overlap_area_degrees_squared": round(previous_overlap, 12),
            "unresolved_overlap_area_degrees_squared": round(unresolved_overlap, 12),
            "unclassified_reference_area_degrees_squared": round(
                unclassified_reference.area, 12
            ),
            "basis": COMMON_BASIS,
        },
        "features": features,
    }


def exterritorial_collection(zones: dict) -> dict:
    return {
        "type": "FeatureCollection",
        "name": "Shadowrun Berlin 2080 - EXTER",
        "topology": {
            "model": "independent-hard-layer",
            "priority": 1,
            "policy": (
                "Verkehrs- und Bahnkorridore vollständig beansprucht; "
                "im Zweifel bis zur nächsten verteidigbaren Außengrenze."
            ),
        },
        "features": [
            feature
            for feature in zones["features"]
            if feature.get("properties", {}).get("status") == "corporate"
        ],
    }


def main() -> int:
    require_shapely()
    if not RAW_ZONES_PATH.exists():
        raise FileNotFoundError(
            f"Unbereinigte Ausgangsflächen fehlen: {RAW_ZONES_PATH}. "
            "Bitte zuerst tools/build_geographic_shadowrun_map.py ausführen."
        )
    zones = load(RAW_ZONES_PATH)
    districts = load(DISTRICTS_PATH)
    neighborhoods = load(NEIGHBORHOODS_PATH)
    outskirts = load(OUTSKIRTS_PATH)
    result = reconcile(zones, districts, neighborhoods, outskirts)
    ZONES_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    exterritorial = exterritorial_collection(result)
    EXTRATERRITORIAL_PATH.write_text(
        json.dumps(exterritorial, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"{len(result['features'])} disjunkte Gebietsflächen und "
        f"{len(exterritorial['features'])} EXTER-Flächen geschrieben; "
        f"ungeklärte Überlappung: "
        f"{result['topology']['unresolved_overlap_area_degrees_squared']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
