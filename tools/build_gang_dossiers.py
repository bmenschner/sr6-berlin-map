#!/usr/bin/env python3
"""Create group dossiers from the official Berlin 2080 gang radar."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "output/data/berlin-2080-katalog.json"
PLACES_PATH = ROOT / "data/berlin-2080/places.geojson"
PEOPLE_PATH = ROOT / "data/berlin-2080/people.json"
DATASET_ID = "berlin-2080-gangradar"
HISTORY_DATASET_ID = "deutschland-in-den-schatten-gangs"


SR1_GANGS = [
    {
        "name": "Magnifiker",
        "type": "Magisch aktive Trick- und Diebesgang",
        "members": "ca. 200",
        "preview": "Die Magnifiker setzen Illusionen und kleine Geister ein, um Passanten zu erschrecken und zu bestehlen.",
        "full": "Die ausschließlich männliche Gang versteht sich als Zusammenschluss von Magiern. Ihre bevorzugte Masche verbindet illusionistische Schocks, kleine Geister und anschließend geforderte oder entwendete Zahlungen.",
    },
    {
        "name": "Surfturf",
        "type": "U-Bahn- und Thrill-Gang",
        "members": "?",
        "preview": "Surfturf lebt in der Berliner U-Bahn und verbindet riskantes Bahn-Surfen mit dem Handel von Flugechseneiern.",
        "full": "Die Mitglieder hängen sich mit Cybersaugern außen an Züge, suchen in Tunneln nach verwertbaren Flugechseneiern und provozieren dabei Fahrgäste und Gefahren der erwachten Unterwelt.",
    },
    {
        "name": "White Skins",
        "type": "Rassistische Terrorgang",
        "members": "?",
        "preview": "Die White Skins verfolgen eine extrem rassistische Ideologie und führen gewaltsame angebliche Abstammungstests durch.",
        "full": "Die Gang tritt mit pseudowissenschaftlichen Gentests auf, sperrt Straßenzüge ab und greift alle Menschen an, die nicht ihrem konstruierten Reinheitsbild entsprechen.",
    },
    {
        "name": "Red Skins",
        "type": "Straßengang",
        "members": "?",
        "preview": "Die Red Skins sind erbitterte Gegner der White Skins und werden wegen ähnlicher äußerer Merkmale häufig mit ihnen verwechselt.",
        "full": "Die Gang trägt Glatzen mit gläsernen Schädelimplantaten, ist jedoch nicht an der Ideologie der White Skins interessiert. Viele ihrer Kämpfe entstehen aus Verwechslungen und daraus folgender Gegenwehr.",
    },
    {
        "name": "Die Horde",
        "type": "Ork-Gang",
        "members": "?",
        "preview": "Die frühe Horde besteht aus besonders großen Orks und ist für brutale Angriffe auf Außenstehende bekannt.",
        "full": "Bereits in den frühen Berliner Quellen erscheint die Horde als gewalttätige Ork-Gang. Diese historische Beschreibung bildet den Ausgangspunkt ihrer späteren Entwicklung zur dominierenden Macht Gropiusstadts.",
    },
    {
        "name": "Kreuzritter",
        "type": "Religiöse Terrorgang",
        "members": "?",
        "preview": "Die Kreuzritter verfolgen vermeintliche Ketzer mit ritualisierter und demonstrativer Gewalt.",
        "full": "Die fanatische Gang verbindet ein radikales christliches Selbstbild mit Entführungen, Folter und Hinrichtungen von Personen, die sie zu Sündern erklärt.",
    },
    {
        "name": "Die Grünen Barden",
        "type": "Minnesänger- und Thrill-Gang",
        "members": "?",
        "preview": "Die Grünen Barden treten als moderne Minnesänger auf und reagieren auf Zurückweisung mit Gewalt.",
        "full": "Die Gruppe entstand aus einer Mode um wiederentdeckte mittelalterliche Lieder. Hinter ihrem romantischen Auftreten steht ein erzwungenes Werben, bei dem Zurückweisung gefährliche Folgen haben kann.",
    },
    {
        "name": "Streiter Gottes",
        "type": "Religiöse Kampfgruppe",
        "members": "?",
        "preview": "Die Streiter Gottes bilden den Berliner Arm der Ritter Christi und unterstützen religiöse Gruppen als bewaffnete Verbündete.",
        "full": "Die Gang versteht verschiedene Religionen als Teile einer höheren Macht. Sie meidet manche innerreligiösen Konflikte, tritt gegen erklärte Gottlose jedoch offen und organisiert an.",
    },
    {
        "name": "Jihad B",
        "type": "Religiös-extremistische Gang",
        "members": "?",
        "preview": "Jihad B entwickelt sich von einer Weltuntergangssekte zu einer radikal-islamistischen Berliner Gang.",
        "full": "Die Gruppe begann mit dem Ziel, den erwarteten Weltuntergang durch Anschläge zu beschleunigen. Später wird sie als radikalisierte Gang beschrieben, die für gewaltsame Aufträge eingesetzt wird.",
    },
]


REGION_LINKS: dict[str, list[tuple[int, str]]] = {
    "agc siemensstadt": [(185, "Aktionsraum im Umfeld der AGC-Siemensstadt")],
    "azt schönwalde": [(452, "Aktionsraum in Aztech-Schönwalde")],
    "chawi": [(446, "Bekanntes Revier Chawi")],
    "chawi (q-mall)": [(119, "Schwerpunkt Q-Mall"), (446, "Bekanntes Revier Chawi")],
    "falkensee": [(453, "Bekanntes Revier Falkensee")],
    "gropiusstadt": [(448, "Bekanntes Revier Gropiusstadt")],
    "köpenick": [(444, "Bekanntes Revier Köpenick")],
    "kreuzhain (emirat)": [(450, "Bekanntes Revier im Emirat Kreuzhain")],
    "lichtenberg": [(442, "Bekanntes Revier Lichtenberg")],
    "marzahn": [(443, "Bekanntes Revier Marzahn")],
    "mitte": [(449, "Bekanntes Revier Mitte")],
    "mitte (moabit)": [(449, "Bekanntes Revier Moabit im Bezirk Mitte")],
    "mitte (wedding)": [(449, "Bekanntes Revier Wedding im Bezirk Mitte")],
    "oranienburg": [(454, "Bekanntes Revier Oranienburg")],
    "reinickendorf": [(440, "Bekanntes Revier Reinickendorf")],
    "renrakusan": [(451, "Bekanntes Revier Renrakusan")],
    "s-k tempelhof": [(424, "Aktionsraum S-K Tempelhof")],
    "schönefeld": [(456, "Bekanntes Revier Schönefeld")],
    "spandau (gatow)": [(333, "Bekanntes Revier Gartenstadt Gatow"), (445, "Aktionsraum Spandau")],
    "spandau (kladow)": [(445, "Bekanntes Revier Kladow im Bezirk Spandau")],
    "spandau (nord)": [(445, "Bekanntes Revier im Norden Spandaus")],
    "strausberg": [(457, "Bekanntes Revier Strausberg")],
    "z-ic tegel": [(440, "Aktionsraum im Z-IC-kontrollierten Tegel")],
    "zehlendorf": [(447, "Bekanntes Revier Zehlendorf")],
}

SPECIAL_LINKS: dict[str, list[tuple[int, str]]] = {
    "Die Horde": [(9, "Hauptquartier Block X"), (448, "Beherrschtes Territorium Gropiusstadt")],
    "Hackbirds": [(480, "Heimathost NeverCore")],
}


def stable_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


def scope_text(region: str) -> str:
    if not region:
        return "Berlinweit; im Gangradar ist kein engeres Revier ausgewiesen"
    if region == "Matrix":
        return "Berliner Matrix; kein physischer Einzelstandort"
    if region == "Überall":
        return "Berlinweit; kein einzelnes Revier"
    if region == "Innenring":
        return "Berliner Innenring; kein einzelner Bezirk"
    return region


def build_description(name: str, gang_type: str, members: str, danger: int, region: str) -> tuple[str, str]:
    type_label = gang_type or "Gang ohne näher ausgewiesenen Typ"
    member_label = f"etwa {members} Mitglieder" if members not in {"?", "var."} else (
        "eine wechselnde Mitgliederzahl" if members == "var." else "eine nicht bezifferte Mitgliederzahl"
    )
    region_label = (
        f"Als Schwerpunkt nennt die Quelle {region}."
        if region and region not in {"Überall", "Matrix"}
        else (
            "Die Gruppe operiert in der Berliner Matrix."
            if region == "Matrix"
            else "Die Gruppe ist keinem einzelnen Berliner Revier zugeordnet."
        )
    )
    preview = f"{name} wird als {type_label} mit {member_label} und Gefahrenstufe {danger} von 5 geführt."
    full = f"{preview} {region_label} Die Einstufung stammt aus dem Berliner Gangradar und beschreibt die Gruppe als Ganzes, nicht einzelne Mitglieder."
    return preview, full


def main() -> int:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    places = json.loads(PLACES_PATH.read_text(encoding="utf-8"))["features"]
    virtual_path = PLACES_PATH.with_name("virtual-places.geojson")
    if virtual_path.exists():
        places.extend(json.loads(virtual_path.read_text(encoding="utf-8"))["features"])
    place_by_id = {feature["properties"]["id"]: feature["properties"] for feature in places}

    people = json.loads(PEOPLE_PATH.read_text(encoding="utf-8"))
    people = [
        entry
        for entry in people
        if entry.get("dataset") not in {DATASET_ID, HISTORY_DATASET_ID}
    ]
    used_ids = {entry["id"] for entry in people}
    used_names = {entry["name"].casefold() for entry in people}
    created = []

    current_region = ""
    for gang in catalog["gangs"]:
        if gang["region"]:
            current_region = gang["region"]
        region = current_region
        name = gang["name"]
        person_id = stable_slug(name)
        if person_id in used_ids or name.casefold() in used_names:
            person_id = f"{person_id}-gang"
        used_ids.add(person_id)
        used_names.add(name.casefold())

        links = SPECIAL_LINKS.get(name, REGION_LINKS.get(region.casefold(), []))
        locations = []
        for place_id, relation in links:
            place = place_by_id.get(place_id)
            if not place:
                raise ValueError(f"Unbekannter Ort {place_id} für {name}")
            locations.append(
                {
                    "id": place_id,
                    "relation": relation,
                    "global_id": place["global_id"],
                }
            )

        preview, full = build_description(
            name,
            gang["type"],
            gang["members"],
            gang["danger"],
            region,
        )
        citation = "Berlin 2080, S. 130–133"
        source = {
            "bookId": "berlin-2080",
            "title": "Berlin 2080",
            "edition": "SR6",
            "citation": citation,
            "purpose": "description",
        }
        created.append(
            {
                "id": person_id,
                "name": name,
                "aliases": [],
                "category": "Gangs",
                "entity_type": "group",
                "dataset": DATASET_ID,
                "role": gang["type"] or "Berliner Gang",
                "affiliation": region or "Berliner Gangszene",
                "status": "Aktiv (Stand 2080)",
                "members": gang["members"],
                "danger": gang["danger"],
                "summary": preview,
                "description": full,
                "source": citation,
                "locations": locations,
                "scope": scope_text(region),
                "sources": [source],
                "editions": ["SR6"],
                "edition_descriptions": {
                    "SR6": {
                        "kind": "Gruppendossier",
                        "preview": preview,
                        "full": full,
                        "hasMore": True,
                        "hasExcerpt": True,
                        "sources": [source],
                    }
                },
                "global_id": f"berlin-2080:person:{person_id}",
            }
        )

    group_by_name = {entry["name"].casefold(): entry for entry in created}
    history_sources = [
        {
            "bookId": "deutschland-in-den-schatten",
            "title": "Deutschland in den Schatten (Ausgabe 1992)",
            "edition": "SR1",
            "citation": "Deutschland in den Schatten, S. 58–59",
            "purpose": "description",
        },
        {
            "bookId": "deutschland-in-den-schatten-1993",
            "title": "Deutschland in den Schatten (Ausgabe 1993)",
            "edition": "SR2",
            "citation": "Deutschland in den Schatten (Ausgabe 1993), S. 58–59",
            "purpose": "description",
        },
    ]
    for gang in SR1_GANGS:
        existing = group_by_name.get(gang["name"].casefold())
        descriptions = {
            source["edition"]: {
                "kind": "Gruppendossier",
                "preview": gang["preview"],
                "full": gang["full"],
                "hasMore": True,
                "hasExcerpt": True,
                "sources": [source],
            }
            for source in history_sources
        }
        if existing:
            existing["sources"] = [*history_sources, *existing["sources"]]
            existing["editions"] = ["SR1", "SR2", *existing["editions"]]
            existing["edition_descriptions"].update(descriptions)
            existing["source"] = f"Deutschland in den Schatten, S. 58–59 (SR1/SR2); {existing['source']}"
            continue

        name = gang["name"]
        person_id = stable_slug(name)
        if person_id in used_ids or name.casefold() in used_names:
            person_id = f"{person_id}-gang"
        used_ids.add(person_id)
        used_names.add(name.casefold())
        links = SPECIAL_LINKS.get(name, [])
        locations = [
            {
                "id": place_id,
                "relation": relation,
                "global_id": place_by_id[place_id]["global_id"],
            }
            for place_id, relation in links
        ]
        created.append(
            {
                "id": person_id,
                "name": name,
                "aliases": [],
                "category": "Gangs",
                "entity_type": "group",
                "dataset": HISTORY_DATASET_ID,
                "role": gang["type"],
                "affiliation": "Berliner Gangszene",
                "status": "Historisch belegt (2053)",
                "members": gang["members"],
                "danger": None,
                "summary": gang["preview"],
                "description": gang["full"],
                "source": "Deutschland in den Schatten, S. 58–59 (SR1/SR2)",
                "locations": locations,
                "scope": "Berlinweit; kein engeres Revier belegt",
                "sources": history_sources,
                "editions": ["SR1", "SR2"],
                "edition_descriptions": descriptions,
                "global_id": f"berlin-2080:person:{person_id}",
            }
        )

    PEOPLE_PATH.write_text(
        json.dumps(people + created, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{len(created)} Gangdossiers erzeugt; insgesamt {len(people) + len(created)} Personen und Gruppen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
