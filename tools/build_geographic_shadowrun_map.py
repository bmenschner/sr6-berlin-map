#!/usr/bin/env python3
"""Build the geographic, tile-based Shadowrun Berlin 2080 map package."""

from __future__ import annotations

import base64
import json
import math
import re
import subprocess
import unicodedata
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter
try:
    from tools.reconcile_zone_topology import reconcile as reconcile_zone_topology
except ModuleNotFoundError:
    from reconcile_zone_topology import reconcile as reconcile_zone_topology


ROOT = Path("/mnt/c/Users/Privat/Documents/Shadowrun/Chatgpt")
CITY_ID = "berlin-2080"
PUBLIC_DATA_DIR = ROOT / "data"
CITY_DATA_DIR = PUBLIC_DATA_DIR / CITY_ID
CITY_ASSET_DIR = ROOT / "assets/cities" / CITY_ID
CITY_DETAIL_PLAN_DIR = CITY_ASSET_DIR / "detail-maps"
CITY_OFFLINE_BASE = CITY_ASSET_DIR / "offline-base.webp"
EDITION_ORDER = ["SR1", "SR2", "SR3", "SR4", "SR5", "SR6"]
SOURCE_BOOKS = [
    {"id": "deutschland-in-den-schatten", "title": "Deutschland in den Schatten (Ausgabe 1992)", "edition": "SR1", "patterns": ["Deutschland in den Schatten"]},
    {"id": "deutschland-in-den-schatten-1993", "title": "Deutschland in den Schatten (Ausgabe 1993)", "edition": "SR2", "patterns": ["Deutschland in den Schatten (Ausgabe 1993)"]},
    {"id": "brennpunkt-adl", "title": "Brennpunkt ADL", "edition": "SR3", "patterns": ["Brennpunkt ADL"]},
    {"id": "deutschland-in-den-schatten-ii", "title": "Deutschland in den Schatten II", "edition": "SR3", "patterns": ["Deutschland in den Schatten II"]},
    {"id": "berlin-4d", "title": "Berlin 4D", "edition": "SR4", "patterns": ["Berlin 4D"]},
    {"id": "datapuls-berlin", "title": "Datapuls: Berlin", "edition": "SR5", "patterns": ["Datapuls Berlin", "Datapuls: Berlin"]},
    {"id": "datapuls-kunstraub", "title": "Datapuls: Kunstraub", "edition": "SR5", "patterns": ["Datapuls: Kunstraub"]},
    {"id": "datapuls-10-konzerne", "title": "Datapuls: 10 Konzerne", "edition": "SR5", "patterns": ["Datapuls: 10 Konzerne"]},
    {"id": "berlin-2080", "title": "Berlin 2080", "edition": "SR6", "patterns": ["Berlin 2080"]},
    {"id": "netzgewitter", "title": "Netzgewitter", "edition": "SR6", "patterns": ["Netzgewitter"]},
    {"id": "schattenleben-berlin", "title": "Schattenleben: Berlin", "edition": "SR6", "patterns": ["Schattenleben Berlin", "Schattenleben: Berlin"]},
    {"id": "renrakusan", "title": "Renrakusan-Bezirksplan", "edition": "SR6", "patterns": ["Renrakusan-"]},
    {"id": "sr6-quellenkorpus", "title": "Shadowrun-6D-Quellenkorpus", "edition": "SR6", "patterns": ["Shadowrun-6D-Quellenkorpus"]},
    {"id": "schattenload-2019", "title": "Schattenload 2019", "edition": "SR6", "patterns": ["Schattenload 12/2019", "Schattenload Dezember 2019"]},
    {"id": "schattenload-2020", "title": "Schattenload 2020", "edition": "SR6", "patterns": ["Schattenload 12/2020"]},
    {"id": "auswurfschock", "title": "Auswurfschock", "edition": "SR6", "patterns": ["Auswurfschock"]},
    {"id": "hinter-dem-vorhang", "title": "Hinter dem Vorhang", "edition": "SR6", "patterns": ["Hinter dem Vorhang"]},
    {"id": "schlagschatten", "title": "Schlagschatten", "edition": "SR6", "patterns": ["Schlagschatten"]},
]
CATALOG = ROOT / "output/data/berlin-2080-katalog.json"
DESCRIPTIONS = ROOT / "output/data/berlin-2080-beschreibungen.json"
SOURCE_SVG = ROOT / "tmp/pdfs/berlin-uebersicht.svg"
SOURCE_PDF = Path(
    "/mnt/c/Users/Privat/Documents/Shadowrun/Shadowrun 6D/02 - Quellenband/"
    "Shadowrun 6D - Berlin 2080 Maps/berlin_karte_v04_uebersicht_web.pdf"
)
SOURCE_RENDER = ROOT / "tmp/pdfs/berlin-uebersicht-150.png"
MAP_DIR = ROOT / "output/map"
OVERLAY_SVG = MAP_DIR / "berlin-2080-shadowrun-vektorebene.svg"
OFFLINE_BASE_WEBP = MAP_DIR / "berlin-2080-offline-basis.webp"
GEOJSON = ROOT / "output/data/berlin-2080-geopunkte.geojson"
ZONES_GEOJSON = ROOT / "output/data/berlin-2080-gebiete.geojson"
DISTRICT_BOUNDARIES_GEOJSON = ROOT / "output/data/berlin-2080-bezirksgrenzen.geojson"
NEIGHBORHOOD_BOUNDARIES_GEOJSON = ROOT / "output/data/berlin-2080-stadtteilgrenzen.geojson"
UMLAND_BOUNDARIES_GEOJSON = ROOT / "output/data/berlin-2080-umlandgebiete.geojson"
CORPUS_SPOTS_JSON = ROOT / "output/data/berlin-2080-zusatzorte.json"
OFFICIAL_DISTRICTS = ROOT / "tmp/geo-data/berlin-bezirke-alkis.geojson"
OFFICIAL_NEIGHBORHOODS = ROOT / "tmp/geo-data/berlin-ortsteile-alkis.geojson"
OFFICIAL_BRANDENBURG_MUNICIPALITIES = ROOT / "tmp/geo-data/brandenburg-gemeinden.geojson"
BOUNDARY_SOURCE = ROOT / "tmp/berlin-stadtgrenze-nominatim.geojson"
BOUNDARY_GEOJSON = ROOT / "output/data/berlin-stadtgrenze.geojson"
TEMPLATE = ROOT / "tmp/build-visual/berlin-geographic-map-template.html"
PWA_HTML = ROOT / "index.html"
SOURCE_MAP_DIR = Path(
    "/mnt/c/Users/Privat/Documents/Shadowrun/Shadowrun 6D/02 - Quellenband/"
    "Shadowrun 6D - Berlin 2080 Maps"
)
DETAIL_PLAN_DIR = MAP_DIR / "detailplaene"


DETAIL_ATLAS = [
    {
        "key": "babylon",
        "title": "Das Babylon",
        "kind": "Gebäudeplan",
        "source": "SR6_Berlin2080_Disko-Babylon.pdf",
        "marker_ids": [6],
        "summary": (
            "Mehrgeschossiger Plan der Diskothek an der Sokarenallee 23A mit Foyer, Ballsaal, Lounge, Tanzfläche, "
            "Bühne, DJ-Bereich, Büros und Parkdeck. Die Legende unterscheidet 17 Funktionsbereiche."
        ),
    },
    {
        "key": "hauergasse",
        "title": "Kneipenkiez Hauergasse",
        "kind": "Kiezplan",
        "source": "SR6_Berlin2080_Hauergasse.pdf",
        "marker_ids": [17],
        "summary": (
            "Innenplan des verzweigten Kneipenkiezes mit Zugängen aus Q-Mall und Lietzenburger Straße. "
            "63 nummerierte Bars, Imbisse, Cafés, Clubs und Kleinstbetriebe sind in der Legende verortet."
        ),
    },
    {
        "key": "kasbah",
        "title": "Kasbah Teehaus",
        "kind": "Gebäudeplan",
        "source": "SR6_Berlin2080_Kasbah-Teehaus.pdf",
        "marker_ids": [80],
        "summary": (
            "Grundriss des Teehauses am Fatima-Al-Masuma-Park mit Erdgeschoss, Dachterrasse, Eckturm und Hamam. "
            "Eingezeichnet sind außerdem Sicherheitskomponenten und ein geheimer Kellerzugang."
        ),
    },
    {
        "key": "kellerclubs",
        "title": "Berliner Kellerclubs",
        "kind": "Schauplatzmodule",
        "source": "SR6_Berlin2080_Kellerclubs.pdf",
        "marker_ids": [],
        "summary": (
            "Zwölf schematische Kellerclub-Bausteine von A bis L mit Treppen, Mieterkellern, Zugängen, Rampen "
            "und einem mobilen DJ-Truck. Als universeller Schauplatz keinem einzelnen Marker zugeordnet."
        ),
    },
    {
        "key": "osramhoefe",
        "title": "Schattenmarkt Osramhöfe",
        "kind": "Arealplan",
        "source": "SR6_Berlin2080_Osramhofe.pdf",
        "marker_ids": [116],
        "summary": (
            "Arealplan des Schattenmarktes an der Oudenarder Straße mit sechs Höfen, Fabrik, Zitadelle, Schloss, "
            "Bastion, Zugängen und nummerierten Marktbereichen."
        ),
    },
    {
        "key": "schrapnell",
        "title": "Schattendestille Schrapnell",
        "kind": "Gebäudeplan",
        "source": "SR6_Berlin2080_Schrapnell.pdf",
        "marker_ids": [44],
        "summary": (
            "Grundriss der Schattendestille mit Wohnung, Barbereich, Billardtisch, Warenlager, Mieterkellerzugang "
            "und geschütztem Meeting-Raum einschließlich der eingezeichneten Sicherungen."
        ),
    },
    {
        "key": "schulkiez",
        "title": "Schulkiez Emma Goldman",
        "kind": "Kiezplan",
        "source": "SR6_Berlin2080_Schulkiez.pdf",
        "marker_ids": [324],
        "summary": (
            "Lageplan des Schulkiezes zwischen Rathenower, Krupp- und Noam-Chomsky-Straße. Er verortet Grund- und "
            "Hauptstufe, Kita, Wohn- und Hilfseinrichtungen, Jugendclub, Sportflächen und das Sternschutz-Revier."
        ),
    },
    {
        "key": "spreeland",
        "title": "Spreeland Funpark",
        "kind": "Arealplan",
        "source": "SR6_Berlin2080_Spreeland-Funpark.pdf",
        "marker_ids": [151],
        "summary": (
            "Plan des Vergnügungsparks an der Müller-Breslau-Straße 14 mit 15 nummerierten Attraktionen und "
            "Zugängen sowie den angrenzenden Zoo-, Universitäts- und M-Bahn-Anlagen."
        ),
    },
    {
        "key": "blauer-engel",
        "title": "Varieté Blauer Engel",
        "kind": "Gebäudeplan",
        "source": "SR6_Berlin2080_Variete-BlauerEngel.pdf",
        "marker_ids": [8],
        "summary": (
            "Erd- und Untergeschoss des Varieté-Theaters in der Oranienburger Straße 7 mit Bühne, Bar, Fundus, "
            "Büros, Garderobe, Hintereingang und separat erschlossenen Wohnungen."
        ),
    },
    {
        "key": "vesuv",
        "title": "Vesuv-Automatencasino",
        "kind": "Gebäudeplan",
        "source": "SR6_Berlin2080_VesuvCasino.pdf",
        "marker_ids": [158],
        "summary": (
            "Vier Ebenen des Vesuv in Gropiusstadt: Automatencasino, Nachtclub, Büros und Tresor. Die Legende "
            "verzeichnet 20 Funktionsbereiche sowie die umliegenden Geschäfte."
        ),
    },
    {
        "key": "renrakusan",
        "title": "Renrakusan – Bezirksplan",
        "kind": "Bezirksplan",
        "source": "renrakusan-01-final.png",
        "marker_ids": [451],
        "summary": (
            "Detailplan des Renraku-Bezirks mit 42 verzeichneten Referenzen aus Nachtleben, Einkauf, Hotels, "
            "Freizeit, Konzernen, Gastronomie und sonstigen Orten sowie dem internen Bezirksverlauf."
        ),
    },
    {
        "key": "netzspinne",
        "title": "Liniennetz der Berliner Magnetschwebebahnen",
        "kind": "Verkehrsnetz",
        "source": "netzspinne_2080.png",
        "marker_ids": [],
        "summary": (
            "Schematischer Liniennetzplan der M-Bahn-Linien M1 bis M19 mit Innenstadt-Knoten, Flughäfen und "
            "Verbindungen in das Berliner Lore-Umland."
        ),
    },
    {
        "key": "berlin-v06-uebersicht",
        "title": "Berlin 2080 – Übersicht v06",
        "kind": "Referenzkarte",
        "source": "berlin_karte_v06_Seite_1.png",
        "marker_ids": [],
        "summary": (
            "Hochauflösende Übersicht von Berlin und dem Lore-Umland mit Gebietsstatus, Arkologien, Verkehrsachsen "
            "und dem nummerierten Gesamtkatalog. Sie dient der Gegenprüfung der geografischen Hauptkarte."
        ),
    },
    {
        "key": "berlin-v06-details",
        "title": "Berlin 2080 – Detailkarten v06",
        "kind": "Referenzkarte",
        "source": "berlin_karte_v06_Seite_2.png",
        "marker_ids": [],
        "summary": (
            "Detailansichten von Berlin-Mitte und Dreamland mit Straßenzügen, Bezirks- und Kiezbezeichnungen, "
            "M-Bahn-Stationen und den präziser gesetzten Ortsnummern."
        ),
    },
]


# Affine georeferencing of the supplied Renrakusan street map. The fit uses the
# matching official v06 overview markers as control points, while the local
# positions below come from the much more precise district map.
RENRAKUSAN_TRANSFORM = {
    "lon": (0.000026683113163058353, -0.000002482695933224508, 13.400471423806545),
    "lat": (0.0000008183261436534028, -0.000014427031131603388, 52.55637035140492),
}


RENRAKUSAN_MAP_MARKERS = {
    1: [("A2", 1358.5, 873.5)],
    5: [("A10", 1138.0, 85.5)],
    7: [("A5", 2615.0, 1443.5)],
    12: [("A7", 1460.0, 379.0)],
    21: [("A11", 1295.0, 1085.5)],
    22: [("A4", 1930.0, 1511.5)],
    27: [("A6", 1780.0, 812.5)],
    38: [("A8", 1296.0, 294.5)],
    41: [("A3", 1124.0, 1526.5)],
    42: [("A9", 461.0, 51.5)],
    64: [("B3", 2308.0, 1116.0)],
    73: [("B8", 1455.0, 18.0)],
    75: [("B5", 1335.0, 1729.5)],
    76: [("B7", 1310.0, 86.0)],
    85: [("B6", 1614.0, 1239.5)],
    86: [("B2", 1063.0, 600.5)],
    87: [("B1", 2295.0, 1915.0)],
    97: [("B4", 2321.0, 1735.5)],
    128: [("E2", 676.5, 1751.0)],
    132: [("E1", 1433.0, 1087.5)],
    139: [("F3", 1488.0, 261.5)],
    140: [("F1", 505.0, 979.5)],
    141: [("F2", 1113.0, 1606.5)],
    168: [
        ("H1", 747.0, 610.5),
        ("H1", 2028.0, 930.5),
        ("H1", 2947.0, 1481.5),
        ("H1", 845.0, 1676.5),
        ("H1", 2015.0, 1865.0),
    ],
    181: [("H2", 2101.0, 1264.0)],
    194: [("K1", 1076.0, 1692.5)],
    202: [("K2", 1050.0, 2274.5)],
    205: [("K3", 1028.0, 1019.0)],
    225: [("R2", 1677.0, 383.5)],
    230: [("R1", 1262.5, 1184.5)],
    231: [("R4", 1588.0, 78.5)],
    242: [("R3", 2820.0, 1613.0)],
    271: [("A1", 1409.0, 683.5)],
    283: [("S1", 1680.0, 319.5)],
    304: [("S6", 1539.0, 320.5)],
    306: [("S5", 597.0, 85.5)],
    337: [("S8", 78.0, 93.5)],
    341: [("S4", 1290.0, 201.5)],
    345: [("S3", 748.0, 2040.0)],
    351: [("S2", 1428.0, 577.5)],
    400: [("S7", 902.0, 121.0)],
    475: [("S9", 1652.0, 1811.5)],
}


# Hand-checked prose matches from the complete SR6 text corpus. These replace
# generic map-only descriptions only where the location can be identified
# unambiguously in a source text.
DESCRIPTION_OVERRIDES = {
    38: {
        "full": (
            "Das an Dreamland angrenzende Rotlichtkiez Inferno bedient vor allem Kundschaft aus Renrakusan. "
            "Viele Clubs richten Namen, Speisen und Getränke an japanische, vietnamesische oder chinesische Gäste; "
            "Engelsdrogen und sexuelle Dienstleistungen gehören ebenfalls zum Milieu."
        ),
        "source": "Berlin 2080, S. 93",
    },
    50: {
        "full": (
            "Die lang gezogene Discoröhre mit eigener Außenrolltreppe wurde nach langem Leerstand im Retrolook "
            "einer grellen Flugzeugkabine wiedereröffnet. Unter dem pulsierenden Auge treffen CorpPop, bunte "
            "Synthcocktails und Beschäftigte von AGC und MSI aufeinander; Schlägereien vor dem Ausgang sind keine Seltenheit."
        ),
        "source": "Berlin 2080, S. 70",
    },
    75: {
        "full": (
            "Hadesu ist ein als Zerberus-Streichelcafé inszeniertes Themenlokal in Renrakusan. Es gehört zu einer "
            "Reihe bewusst überzeichneter Erlebnisgastronomien des Konzernbezirks."
        ),
        "source": "Berlin 2080, S. 63",
    },
    76: {
        "full": (
            "Die Havanna Club Lounge liegt im Umfeld der kubanischen Botschaft und des Konsulats im Arminer Ex-Kiez. "
            "Ihr werden der beste Rum und die besten Zigarren Berlins nachgesagt – vorausgesetzt, man erhält Zutritt."
        ),
        "source": "Berlin 2080, S. 91",
    },
    97: {
        "full": (
            "Das Vampir Kafe ist ein ausdrücklich vampirisch inszeniertes Themenlokal in Renrakusan und Teil der "
            "auffälligen Erlebnisgastronomie des Konzernbezirks."
        ),
        "source": "Berlin 2080, S. 63",
    },
    185: {
        "full": (
            "Der AGC Tower Berlin zählt neben der MSI-Miniarkologie zu den beiden sichtbaren Wahrzeichen von AG Chemie "
            "in der Stadt. Der Werkschutz nutzt den Turm außerdem als Kontaktpunkt für diskrete Aufträge rund um "
            "Bedrohungen des AGC-Standorts Siemensstadt."
        ),
        "source": "Berlin 2080, S. 108; Schattenleben Berlin, S. 10",
    },
    225: {
        "full": (
            "Das künstlerisch vollgestellte Caligari Diner liegt an der Straßenfront des alten Stummfilmkinos Delphi. "
            "Betreiberin Magdalena von Lieven verwahrt den Schlüssel zum beschädigten Kino und vermietet es trotz "
            "schwacher Stromversorgung und alter Schäden tageweise als abgeschirmte Treff- und Veranstaltungsstätte."
        ),
        "source": "Berlin 2080, S. 94",
    },
    227: {
        "full": (
            "Das Anarcho-Café an der Prenzlauer Promenade 187 verbindet bezahlbares Essen mit politischem Szeneleben. "
            "Betreiberin Mimi pflegt Kontakte zu Kiezwachen und anarchistischen Gruppen; das Goldstein gilt als "
            "neutraler Boden, Auftragsbörse und diskreter Treffpunkt mit separatem Hinterzimmer."
        ),
        "source": "Schattenload Dezember 2019, S. 4",
    },
    229: {
        "full": (
            "Juanita’s ist ein beliebtes aztlanisches Grillrestaurant unter orkischer Leitung und regelmäßiger Treffpunkt "
            "verschiedener Orkgruppen. Wer das Vertrauen der Besitzerin gewinnt, kann auf Schmuggelware aus einem "
            "versteckten Kühlraumanbau sowie Informationen gegen Geld oder Gefälligkeiten zugreifen."
        ),
        "source": "Berlin 2080, S. 32",
    },
    247: {
        "full": (
            "Die Alte Nationalgalerie gehört auf der Museumsinsel zum Berliner Bestand der Preußenstiftung. "
            "Sie ist damit Teil des dicht gesicherten Kulturkomplexes, dessen Kunstbestände und Zuständigkeiten "
            "im Datapuls Kunstraub als mögliche Ziele und Schauplätze behandelt werden."
        ),
        "source": "Datapuls: Kunstraub, S. 11",
    },
    283: {
        "full": (
            "Das Pankower Punk- und Anarchiemuseum befindet sich im Max-Stirner-Haus an der Spitze von Heinersdorfer- "
            "und Gustav-Adolf-Straße. Im selben Gebäude sitzt das Musiklabel Black Pirate, das seit Jahrzehnten "
            "anarchistische Talente fördert."
        ),
        "source": "Berlin 2080, S. 94",
    },
    296: {
        "full": (
            "Die Anarchistische-Schwarze-Kreuz-Klinik wird von Dr. Mark Rosinski geleitet. Als Wortführer der gemäßigten "
            "Eiswerder-Fraktion steht er politisch gegen Talabanis offensiven Kurs, bleibt als leitender Mediziner und "
            "langjähriger Geburtshelfer der Inselgemeinschaft aber nahezu unersetzlich."
        ),
        "source": "Berlin 2080, S. 96",
    },
    306: {
        "full": (
            "Botschaft und Konsulat Kubas befinden sich wie schon zu DDR-Zeiten im Arminer Ex-Kiez. Zum diplomatischen "
            "Umfeld gehört die schwer zugängliche Havanna Club Lounge, die für Rum und Zigarren einen hervorragenden Ruf besitzt."
        ),
        "source": "Berlin 2080, S. 91",
    },
    310: {
        "full": (
            "Der junge Bundeswehrstandort betreibt das einzige staatliche Krankenhaus Berlins, das Patientinnen und "
            "Patienten auch ohne Vertrag aufnimmt. Die abgelegene Lage begrenzt den Andrang; Bundeswehr- und THW-Ärzte "
            "nutzen den Einsatz zugleich als Vorbereitung auf medizinische Hilfsmissionen."
        ),
        "source": "Berlin 2080, S. 54",
    },
    345: {
        "full": (
            "Die Inazo-Aneki-Zwillingstürme gehören zu den begehrtesten Wohnadressen Berlins und prägen mit der "
            "Miyako-Arkologie das Bild Renrakusans. Ihre austauschbaren Wohnkapseln sitzen an zentralen Tragkernen; "
            "automatisierte Läden sowie ein Dachgarten mit Sentō und Panoramabar ergänzen den Komplex."
        ),
        "source": "Berlin 2080, S. 61–62",
    },
    347: {
        "full": (
            "Das Institut für Astrale Erkundung und Sicherheit unterhält in Berlin-Oranienburg eine ständige Niederlassung. "
            "Gemeinsam mit Bundeswehr und Dr.-Faustus-Gesellschaft bearbeitet es magische Bedrohungen, astrale Überwachung "
            "und die Sicherung gefährlicher Astralräume; die Belegschaft ist überwiegend magisch begabt."
        ),
        "source": "Schlagschatten, S. 145",
    },
    370: {
        "full": (
            "Nördlich der zwergischen Agrarkommune Lutkenau beginnt das Nordreinickendorfer Ödland. Nur ein Teil der "
            "verfallenden Wohnblöcke ist noch bewohnt, andere sind einsturzgefährdet oder bereits kollabiert; DeMeKo "
            "nutzt die Ruinenkulisse regelmäßig für Zombie- und Endzeitproduktionen."
        ),
        "source": "Berlin 2080, S. 59",
    },
    371: {
        "full": (
            "Die Hortbau-Anlage wechselte nach einem Gebietstausch von Tempelhof zu Kreuzhain. Weil eine islamische "
            "Gemeinde das Grundstück für eine Koranschule beansprucht, haben sich die Bewohner unter der trollischen "
            "Chansonette Claudia Proteskov gegen Verwaltung und drohende Verdrängung organisiert."
        ),
        "source": "Berlin 2080, S. 44",
    },
    403: {
        "full": (
            "Das Z-IC-Forschungsklinikum im ehemaligen Tegeler Flughafenterminal zählt zu den modernsten Einrichtungen "
            "Europas. Unter Führung von EuroMedis arbeiten mehrere Z-IC-Töchter interdisziplinär an experimentellen "
            "Behandlungen; besonders die Schönheitschirurgie ist dauerhaft stark ausgelastet."
        ),
        "source": "Berlin 2080, S. 76 und 113",
    },
}


PERSONS = [
    {
        "id": "paul-reinhard-zoeller",
        "name": "Dr. Paul Reinhard Zöller",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Erster Bürgermeister und BERVAG-Generaldirektor",
        "affiliation": "BERVAG, Handelskammer Berlin",
        "status": "Aktiv",
        "summary": "Zöller führt seit 2078 die Berliner Regierung und zugleich die BERVAG.",
        "description": (
            "Der wirtschaftspolitisch profilierte Erste Bürgermeister wirbt für Berlin als europäischen Banken- und "
            "Wirtschaftsstandort. Hinter seinem freundlichen öffentlichen Auftreten steht ein harter Geschäftsmann, "
            "der diskrete Schattenkontakte über seinen Sicherheitsapparat pflegt."
        ),
        "source": "Berlin 2080, S. 116",
        "locations": [
            {"id": 190, "relation": "Amtssitz und Verwaltung"},
            {"id": 449, "relation": "Bezirksabgeordneter von Mitte"},
        ],
    },
    {
        "id": "morek-pfluegler",
        "name": "Morek Pflügler",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Zweiter Bürgermeister und Leiter des Schlichtungsausschusses",
        "affiliation": "BERVAG, Lichtenberg",
        "status": "Aktiv",
        "metatype": "Zwerg",
        "summary": "Pflügler vermittelt zwischen Berlins Machtblöcken und entscheidet festgefahrene Konflikte.",
        "description": (
            "Der Lichtenberger Pfarrer gilt als einer der Architekten der Berliner Einigung. Als Leiter des mächtigen "
            "Schlichtungsausschusses versucht er unlösbare Streitfälle zusammenzuführen und greift dafür bei Bedarf "
            "auch auf präzise Schattenarbeit zurück."
        ),
        "source": "Berlin 2080, S. 116–117",
        "locations": [
            {"id": 190, "relation": "Rats- und Verwaltungsarbeit"},
            {"id": 442, "relation": "Bezirksabgeordneter von Lichtenberg"},
        ],
    },
    {
        "id": "takeshi-ozu",
        "name": "Takeshi Ozu",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Dritter Bürgermeister und Vertreter Renrakusans",
        "affiliation": "Renraku, BERVAG",
        "status": "Aktiv",
        "summary": "Ozu verantwortet Ratskanzlei, Protokoll, Öffentlichkeitsarbeit und den Schutz der Bezirksabgeordneten.",
        "description": (
            "Der Renraku-Konzernpolitiker stieg nach dem Verschwinden Ichiro Koizumis und dem Tod Michael Koslowskis "
            "zum Dritten Bürgermeister auf. Seine Karriere, seine Konzernloyalität und mehrere ungeklärte Vorgänge "
            "machen ihn für Berlins Schatten besonders interessant."
        ),
        "source": "Berlin 2080, S. 117",
        "locations": [
            {"id": 451, "relation": "Vertreter von Renrakusan"},
            {"id": 205, "relation": "Renraku-Machtzentrum"},
        ],
    },
    {
        "id": "franziska-landolt",
        "name": "Dr. Franziska Landolt",
        "aliases": [],
        "category": "Konzerne",
        "role": "Geschäftsführerin von Saeder-Krupp Berlin und Bezirksabgeordnete",
        "affiliation": "Saeder-Krupp",
        "status": "Aktiv",
        "summary": "Landolt ist S-Ks Berliner Powerfrau und eine international erfahrene Social-Engineering-Expertin.",
        "description": (
            "Die makellos auftretende Konzernmanagerin vertritt S-K Tempelhof und soll zugleich als Troubleshooterin "
            "für S-K Prime arbeiten. Über Mittelsleute ist sie tief mit dem Berliner Schattenmarkt verbunden."
        ),
        "source": "Berlin 2080, S. 117",
        "locations": [{"id": 208, "relation": "S-K-Zentrale Der Hort"}],
    },
    {
        "id": "sofia-nordin",
        "name": "Sofia Nordin",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Umstrittene Reinickendorfer Bezirksabgeordnete und Wirtschaftsvertreterin",
        "affiliation": "CVP, Schering/Zeta-ImpChem",
        "status": "Amt umstritten",
        "summary": "Nordins Gebietsabtretung an Z-IC Tegel löste in Reinickendorf eine politische Krise aus.",
        "description": (
            "Als Leiterin des Reinickeforums vertrat Nordin zentrale Wirtschaftsinteressen des Bezirks. Nach der "
            "Abtretung großer Gebiete an Z-IC wurde sie von der Bezirksversammlung abgesetzt; die Rechtmäßigkeit "
            "dieser Entscheidung ist innerhalb der Lore weiterhin umstritten."
        ),
        "source": "Berlin 2080, S. 58–59 und 76–77",
        "locations": [
            {"id": 440, "relation": "Politisches Zentrum Reinickendorf"},
            {"id": 212, "relation": "Konzernbezug Schering"},
        ],
    },
    {
        "id": "wladimir-bronstein",
        "name": "Wladimir Igorewitsch Bronstein",
        "aliases": ["Wladimir I. Bronstein"],
        "category": "Politik und Verwaltung",
        "role": "Bezirksabgeordneter von Pankow",
        "affiliation": "KPD, Vory-Umfeld",
        "status": "Aktiv",
        "summary": "Der Altstalinist ringt nach Gargaris Tod um politischen Einfluss und sein eigenes Überleben.",
        "description": (
            "Bronstein kompensiert sein begrenztes Stimmgewicht durch Dogmatik, Medienpräsenz und Kontakte zu "
            "Konzerngegnern. Im Machtkampf der zersplitterten Pankower Vory versucht er, nicht nur zu bestehen, "
            "sondern am Ende als politischer Gewinner übrig zu bleiben."
        ),
        "source": "Berlin 2080, S. 117–118",
        "locations": [{"id": 441, "relation": "Bezirksabgeordneter von Pankow"}],
    },
    {
        "id": "lena-rabeja",
        "name": "Lena Rabeja",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Bezirksabgeordnete von Köpenick und Vermittlerin",
        "affiliation": "Komitee 23fünf, KPD",
        "status": "Aktiv",
        "metatype": "Elfin",
        "summary": "Rabeja verbindet kommunistische Politik mit einem weitreichenden Netz aus Kontakten und Gefälligkeiten.",
        "description": (
            "Die schon während des Status F erfolgreiche Vermittlerin besitzt ein außergewöhnlich dichtes Berliner "
            "Beziehungsnetz. Über dieses konnte sie unter anderem Shiawase zu Investitionen und zur Unterstützung "
            "Köpenicks bewegen."
        ),
        "source": "Berlin 2080, S. 117–118",
        "locations": [{"id": 444, "relation": "Bezirksabgeordnete von Köpenick"}],
    },
    {
        "id": "mitra-oezguen",
        "name": "Mitra Özgün",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Erwachte Bezirksabgeordnete und Vermittlerin",
        "affiliation": "Kreuzhain, Nizam Islami",
        "status": "Aktiv",
        "summary": "Özgün war eine zentrale Vermittlerin der Berliner Anarchie und der späteren Einigung.",
        "description": (
            "Die Erwachte gehörte bereits im anarchistischen Kreuzberg zu den wichtigsten Vermittlerinnen. Gemeinsam "
            "mit Morek Pflügler öffnete sie den Dialog mit den Konzernen und prägte damit die politische Neuordnung Berlins."
        ),
        "source": "Berlin 2080, S. 43–44 und 117",
        "locations": [{"id": 450, "relation": "Bezirksabgeordnete von Kreuzhain"}],
    },
    {
        "id": "milena-kilic",
        "name": "Milena Kilic",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Bezirksabgeordnete von Chawi",
        "affiliation": "Charlottenburg-Wilmersdorf",
        "status": "Aktiv",
        "summary": "Kilic vertritt den politisch und wirtschaftlich vielstimmigen Bezirk Chawi in der BAV.",
        "description": (
            "Ihre Stellung entsteht in einem Bezirk, in dem DeMeKo, Einzelhandel, Immobilieninteressen und lokale "
            "Organisationen miteinander konkurrieren. In der Bezirksabgeordnetenversammlung gilt sie als eine der "
            "deutlich wahrnehmbaren Stimmen der Normbezirke."
        ),
        "source": "Berlin 2080, S. 34 und 117",
        "locations": [{"id": 446, "relation": "Bezirksabgeordnete von Chawi"}],
    },
    {
        "id": "aleksandr-sukrow",
        "name": "Aleksandr Sukrow",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Bezirksabgeordneter von Gropiusstadt",
        "affiliation": "Gropiusstadt, Horde- und Vory-Umfeld",
        "status": "Aktiv",
        "summary": "Der Hexer hält sich politisch, indem er Gegner überlebt und bei Konflikten Runner einsetzt.",
        "description": (
            "Sukrow bewegt sich zwischen Neo-Anarchisten, Horde und Vory. Seine robuste Machtbasis und die Bereitschaft, "
            "Schattenkräfte gegen Feinde einzusetzen, machen ihn zu einem besonders runrelevanten Bezirksvertreter."
        ),
        "source": "Berlin 2080, S. 117–119",
        "locations": [{"id": 448, "relation": "Bezirksabgeordneter von Gropiusstadt"}],
    },
    {
        "id": "jurek-fletscher-kowalczyk",
        "name": "Jurek „Fletscher“ Kowalczyk",
        "aliases": ["Fletscher"],
        "category": "Aktivisten und Widerstand",
        "role": "Bezirksabgeordneter von Spandau und ehemaliger Eiswerder-Anführer",
        "affiliation": "Neo-Anarchisten, Eiswerder",
        "status": "Aktiv",
        "metatype": "Troll",
        "summary": "Fletscher machte Spandau zum Alternativbezirk und wurde damit zugleich Hoffnungsträger und Zielscheibe.",
        "description": (
            "Der frühere Kopf der Eiswerder-Anarchisten wurde 2077 zum Bezirksabgeordneten gewählt. Sein Versuch, "
            "zwischen Alternativen und Normalbevölkerung zu vermitteln, verschärfte zugleich den Konflikt mit den "
            "militanten Kräften auf der Inselfestung."
        ),
        "source": "Berlin 2080, S. 94–96 und 118–119",
        "locations": [
            {"id": 445, "relation": "Bezirksabgeordneter von Spandau"},
            {"id": 323, "relation": "Früherer Anführer von Eiswerder"},
        ],
    },
    {
        "id": "jaromir-kotov",
        "name": "Jaromir Kotov",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Bezirksabgeordneter von Marzahn und Finanzmagnat",
        "affiliation": "Marzahn, Vory-Umfeld",
        "status": "Aktiv",
        "summary": "Kotov verbindet politisches Amt, beträchtliches Vermögen und Verbindungen in das Vory-Milieu.",
        "description": (
            "Der exilrussische Finanzmagnat gehört zu den Berliner Bezirksvertretern, die sich Unterstützung direkt "
            "kaufen können. Seine Stellung in Marzahn wird von wirtschaftlicher Macht und dem dortigen Vory-Einfluss geprägt."
        ),
        "source": "Berlin 2080, S. 117–119",
        "locations": [{"id": 443, "relation": "Bezirksabgeordneter von Marzahn"}],
    },
    {
        "id": "aslan-oezdemir",
        "name": "Aslan Özdemir",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Bezirksabgeordneter von Falkensee und Clanpatriarch",
        "affiliation": "Özdemir-Clan, Falkensee",
        "status": "Aktiv",
        "summary": "Der Dönerunternehmer und Clanpatriarch verfügt in Falkensee über Personal, Geld und politische Reichweite.",
        "description": (
            "Özdemir stützt seine Macht auf den Familienclan und dessen weitreichende Geschäfte. Das Netzwerk kann "
            "politische Interessen ebenso durchsetzen wie Übernahmen und Bereinigungen im kriminellen Umfeld."
        ),
        "source": "Berlin 2080, S. 117–119",
        "locations": [{"id": 453, "relation": "Bezirksabgeordneter von Falkensee"}],
    },
    {
        "id": "ralph-faber",
        "name": "Ralph Faber",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Bezirksabgeordneter von Oranienburg und ehemaliger Oberst",
        "affiliation": "Bundesgrenzschutz",
        "status": "Aktiv",
        "summary": "Faber vertritt den schwer gesicherten BGS-Bezirk Oranienburg gegenüber dem Berliner Rat.",
        "description": (
            "Der ehemalige Oberst reagiert mit stoischer Ruhe auf den politischen Druck aus Berlin. Unter seiner "
            "Vertretung wächst die militärische Präsenz in Oranienburg, was regelmäßig Spekulationen über die Absichten der ADL nährt."
        ),
        "source": "Berlin 2080, S. 117–118",
        "locations": [
            {"id": 454, "relation": "Bezirksabgeordneter von Oranienburg"},
            {"id": 302, "relation": "BGS-Machtzentrum"},
        ],
    },
    {
        "id": "fabian-von-wittich",
        "name": "Fabian von Wittich",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Bezirksabgeordneter von Potsdam",
        "affiliation": "CVP, Preußenstiftung",
        "status": "Aktiv",
        "summary": "Von Wittich vertritt Potsdam mit Rückhalt aus Partei- und Stiftungsmitteln.",
        "description": (
            "Seine politische Basis liegt im Zusammenspiel von Preußenstiftung, Draco Foundation und konservativen "
            "Netzwerken. Anders als viele alternative Politiker kann er notwendige Unterstützung unmittelbar finanzieren."
        ),
        "source": "Berlin 2080, S. 117–119",
        "locations": [{"id": 455, "relation": "Bezirksabgeordneter von Potsdam"}],
    },
    {
        "id": "ferdinand-cazares",
        "name": "Ferdinand Cazares",
        "aliases": [],
        "category": "Konzerne",
        "role": "Bezirksabgeordneter von Aztech-Schönwalde",
        "affiliation": "Aztechnology",
        "status": "Aktiv",
        "metatype": "Ork",
        "summary": "Cazares vertritt Aztechnology im extraterritorialen Schönwalde und muss sich vor allem mit dem BGS arrangieren.",
        "description": (
            "Der öffentlich smart auftretende Konzernpolitiker steht zwischen Aztechnologys Berliner Interessen und "
            "den ständigen Kontrollen sowie Behinderungen durch den Bundesgrenzschutz an den Außengrenzen des Bezirks."
        ),
        "source": "Berlin 2080, S. 117–118",
        "locations": [
            {"id": 452, "relation": "Bezirksabgeordneter von Aztech-Schönwalde"},
            {"id": 188, "relation": "Aztechnology-Arkologie"},
        ],
    },
    {
        "id": "robert-schlueter-junior",
        "name": "Dr. Robert Schlüter junior",
        "aliases": [],
        "category": "Konzerne",
        "role": "MSI-Chef und Bezirksabgeordneter von AGC Siemensstadt",
        "affiliation": "MSI, AG Chemie",
        "status": "Aktiv",
        "summary": "Schlüter führt MSI und vertritt den stark abgeschotteten Konzernbezirk Siemensstadt.",
        "description": (
            "Der zurückgezogen lebende Konzernchef verlässt Siemensstadt nur selten. Seine Arbeit konzentriert sich "
            "auf den digitalen und industriellen Komplex von MSI und AG Chemie, der im Bezirk nahezu alle Strukturen dominiert."
        ),
        "source": "Berlin 2080, S. 117–118",
        "locations": [
            {"id": 206, "relation": "MSI-Arkologie"},
            {"id": 185, "relation": "AGC-Wahrzeichen"},
        ],
    },
    {
        "id": "nathan-thompson",
        "name": "Nathan Thompson",
        "aliases": [],
        "category": "Konzerne",
        "role": "Bezirksabgeordneter von Z-IC Tegel",
        "affiliation": "Zeta-ImpChem/Schering",
        "status": "Aktiv",
        "summary": "Thompson führt den Konzernbezirk Tegel mit verschärfter Sicherheit und steht im Fall Koslowski unter Verdacht.",
        "description": (
            "Der britische Konzernpolitiker reagierte auf den Tod seines Vorgängers mit engmaschigen Kontrollen, "
            "Kameras und Sicherheitskräften. Zugleich wird er weiterhin als Hauptverdächtiger im ungeklärten Mordfall Koslowski behandelt."
        ),
        "source": "Berlin 2080, S. 76 und 117–118",
        "locations": [
            {"id": 403, "relation": "Z-IC-Kernanlage in Tegel"},
            {"id": 218, "relation": "Zeta Business Club"},
        ],
    },
    {
        "id": "doreen-katschmarek",
        "name": "Doreen Katschmarek",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Bezirksabgeordnete von Strausberg",
        "affiliation": "ESP, Strausberg",
        "status": "Aktiv",
        "summary": "Katschmarek verbindet grüne Politik mit dem Kampf gegen die Shiawase-Müllhalden vor Strausberg.",
        "description": (
            "Die Bezirksvertreterin gewann 2078 erneut mit einer groß angelegten Umweltkampagne. Im Mittelpunkt stehen "
            "Grundwasser, Luftverschmutzung, Seuchen und die wachsende Dämonenrattenplage der benachbarten Exterritorialgebiete."
        ),
        "source": "Berlin 2080, S. 72 und 117",
        "locations": [{"id": 457, "relation": "Bezirksabgeordnete von Strausberg"}],
    },
    {
        "id": "izabella-buzek",
        "name": "Izabella Buzek",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Bezirksabgeordnete von Zehlendorf",
        "affiliation": "Proteus, Zehlendorf",
        "status": "Aktiv",
        "summary": "Buzek vertritt das hochgesicherte Zehlendorf mit enger Bindung an Proteus und Evo.",
        "description": (
            "Ihre politische Stellung ruht auf dem Einfluss von Proteus und Evo im wohlhabenden Südwesten. Die "
            "Zehlendorfer Platte bildet dabei eines der sichtbarsten Macht- und Forschungszentren ihres Umfelds."
        ),
        "source": "Berlin 2080, S. 117",
        "locations": [
            {"id": 447, "relation": "Bezirksabgeordnete von Zehlendorf"},
            {"id": 217, "relation": "Proteus-Machtzentrum"},
        ],
    },
    {
        "id": "gregor-thielke",
        "name": "Gregor Thielke",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "Bezirksabgeordneter von Schönefeld",
        "affiliation": "CVP, Messerschmitt-Kawasaki",
        "status": "Aktiv",
        "summary": "Thielke vertritt den von Messerschmitt-Kawasaki geprägten Bezirk überraschend gemäßigt.",
        "description": (
            "Der M-K-nahe Politiker versucht, Konzerninteressen und die rasante Entwicklung Schönefelds in der BAV "
            "zu vertreten. Die harte Sicherheitspolitik überlässt er weitgehend dem örtlichen M-K-Sicherheitsapparat."
        ),
        "source": "Berlin 2080, S. 64 und 117",
        "locations": [
            {"id": 456, "relation": "Bezirksabgeordneter von Schönefeld"},
            {"id": 204, "relation": "Messerschmitt-Kawasaki-Fabrik"},
        ],
    },
    {
        "id": "nakaira",
        "name": "Nakaira",
        "aliases": [],
        "category": "Medien und Kultur",
        "role": "Medienpersönlichkeit, Chefredakteurin und Moderatorin",
        "affiliation": "BeOneLive (B1L), früher Sender 44",
        "status": "Aktiv",
        "summary": "Nakaira ist eine der bekanntesten Stimmen Berlins und verbindet Medienprominenz mit neo-anarchistischer Vergangenheit.",
        "description": (
            "Ihre frühen, unter Gefahr gedrehten Videos und bissigen Kommentare machten sie in der alternativen Szene "
            "bekannt. Heute moderiert sie mehrere B1L-Formate, prägt Politik-, Mode- und Szenedebatten und engagiert "
            "Runner sowohl zum Selbstschutz als auch für neue Geschichten."
        ),
        "source": "Berlin 2080, S. 21–22",
        "locations": [],
        "scope": "Berlinweit; kein eindeutig kartierter B1L-Standort",
    },
    {
        "id": "daemonika",
        "name": "Daemonika",
        "aliases": ["möglicherweise Osiris"],
        "category": "Medien und Kultur",
        "role": "Sängerin und pro-anarchistische Aktivistin",
        "affiliation": "Black Pirate",
        "status": "Aktiv; Identität ungeklärt",
        "summary": "Daemonika wurde mit aggressivem Punk und German Hardstyle zur Berliner Anarchie-Ikone.",
        "description": (
            "Seit ihrem Durchbruch 2078 verbindet sie Kultstatus, politische Provokation und Aufrufe zu Widerstand. "
            "Die offizielle Biografie ihres Labels gilt als erfunden; auffällige Cybergliedmaßen nähren Spekulationen "
            "über eine Verbindung zur verschwundenen Performerin Osiris."
        ),
        "source": "Berlin 2080, S. 94–95",
        "locations": [{"id": 304, "relation": "Musiklabel Black Pirate"}],
    },
    {
        "id": "leila-talabani",
        "name": "Leila Talabani",
        "aliases": [],
        "category": "Aktivisten und Widerstand",
        "role": "Anführerin der militanten Eiswerder-Fraktion",
        "affiliation": "Eisheiligen, Axis-F-Umfeld",
        "status": "Aktiv",
        "metatype": "Elfin",
        "summary": "Talabani will Eiswerder als Trainingslager und Festung für den erwarteten Endkampf ausbauen.",
        "description": (
            "Die weißhaarige Elfin führt die militante Fraktion der Inselfestung und ist gut mit Axis F vernetzt. "
            "Ihre Aufrüstungspolitik steht den gemäßigteren Kräften um Fletscher und Rosinski unversöhnlich gegenüber."
        ),
        "source": "Berlin 2080, S. 95–96",
        "locations": [{"id": 323, "relation": "Machtbasis Eiswerder"}],
    },
    {
        "id": "mark-rosinski",
        "name": "Dr. Mark Rosinski",
        "aliases": [],
        "category": "Schatten und Szene",
        "role": "Leitender Mediziner der ASK-Klinik Eiswerder",
        "affiliation": "Anarchistisches Schwarzes Kreuz",
        "status": "Aktiv",
        "summary": "Rosinski ist medizinisch nahezu unersetzlich und politisch der wichtigste offene Gegner Talabanis auf Eiswerder.",
        "description": (
            "Der Klinikleiter steht für den gemäßigten Kurs der Inselfestung. Obwohl er nach dem Weggang anderer "
            "Gemäßigter zunehmend isoliert ist, sichern ihm seine medizinische Bedeutung und seine lange Geschichte "
            "mit der Inselgemeinschaft eine außergewöhnlich feste Stellung."
        ),
        "source": "Berlin 2080, S. 96",
        "locations": [{"id": 296, "relation": "Leitung der ASK-Klinik"}],
    },
    {
        "id": "fienchen",
        "name": "Fienchen",
        "aliases": [],
        "category": "Schatten und Szene",
        "role": "Shadowtalkerin, Aktivistin und Berliner Vermittlungsfigur",
        "affiliation": "LiVeGen, Initiative Berliner Vollbewaffnung",
        "status": "Aktiv",
        "summary": "Fienchen gehört zu den prägnantesten Stimmen der alternativen Berliner Politik und Schattenszene.",
        "description": (
            "Durch ihre Arbeit für die Lichtenberger Verwaltungs-Genossenschaft und die Initiative Berliner "
            "Vollbewaffnung besitzt sie Einblick in Sicherheits-, Rechts- und Kiezfragen. Trotz ihres provokanten "
            "Auftretens wird sie als mögliche politische Nachfolgerin Morek Pflüglers gehandelt."
        ),
        "source": "Berlin 2080, S. 119",
        "locations": [{"id": 442, "relation": "Politisches Umfeld Lichtenberg"}],
    },
    {
        "id": "arkady-tichonow",
        "name": "Arkady Tichonow",
        "aliases": [],
        "category": "Medien und Kultur",
        "role": "Exilrussischer Science-Fiction-Schriftsteller und politischer Berater",
        "affiliation": "Vertrauter von Lena Rabeja; mutmaßliches E-Wall-Umfeld",
        "status": "Aktiv",
        "summary": "Tichonow verbindet literarische Prominenz mit radikaler Technikpolitik und mutmaßlichen Sprawlguerilla-Kontakten.",
        "description": (
            "Der Schriftsteller propagiert eine KI-gesteuerte realkommunistische Welttechnokratie. Als enger Vertrauter "
            "Lena Rabejas und wegen angeblicher Beziehungen zu E-Wall steht er unter Beobachtung des Verfassungsschutzes."
        ),
        "source": "Berlin 2080, S. 118 und 138",
        "locations": [{"id": 444, "relation": "Politisches Umfeld Köpenick"}],
    },
    {
        "id": "kazimira-kaschmir-burakgazi",
        "name": "Kazimira „Kaschmir“ Burakgazi",
        "aliases": ["Kaschmir"],
        "category": "Schatten und Szene",
        "role": "Schieberin, Informationsbrokerin und Betreiberin des Café Cezve",
        "affiliation": "Cezve-Clan, Kreuzbasar-Kiez",
        "status": "Aktiv",
        "metatype": "Elfin",
        "summary": "Kaschmir gehört mit ihrem über Jahrzehnte gewachsenen Netzwerk zu den einflussreichsten Connections der Berliner Schatten.",
        "description": (
            "Die unauffällige Betreiberin des Café Cezve übernahm das Informationsgeschäft von Altug Burakgazi. "
            "Viele später legendäre Runner erhielten über sie oder den Cezve-Clan ihre erste Chance; zugleich sorgt "
            "sie mit ihrem lokalen Netz für Schutz, Arbeit und Informationen im Kreuzbasar-Kiez."
        ),
        "source": "Schattenleben: Berlin, S. 7",
        "locations": [{"id": 68, "relation": "Betreiberin und zentrale Connection"}],
    },
    {
        "id": "saif-alhazred",
        "name": "Saif Alhazred",
        "aliases": [],
        "category": "Schatten und Szene",
        "role": "Vermittler, Rufmörder und diskordianischer Hohepriester",
        "affiliation": "Nemessiden, diskordianische Szene",
        "status": "Aktiv",
        "metatype": "Östlicher Drake",
        "summary": "Alhazred ist einer der ältesten Vermittler Berlins und ein gefürchteter professioneller Rufkiller.",
        "description": (
            "Der politisch neutrale Meistermanipulator verbindet die einflussreiche diskordianische Szene mit den "
            "Nemessiden, einer Gang professioneller Persönlichkeitsattentäter. Er verlässt seinen luxuriösen Rückzugsort "
            "unter dem Zankapfel nur selten und setzt für seine Ziele bevorzugt Mittelsleute und Runner ein."
        ),
        "source": "Schattenleben: Berlin, S. 8",
        "locations": [{"id": 99, "relation": "Thronsaal, Tempel und Hammam im Keller"}],
    },
    {
        "id": "sigma",
        "name": "Sigma",
        "aliases": [],
        "category": "Konzerne",
        "role": "Evo-Konzernhai und Auftraggeber",
        "affiliation": "Evo",
        "status": "Aktiv",
        "summary": "Sigma vermittelt rücksichtslose Konzernjobs rund um Biotechnologie, Gentechnik und Transhumanismus.",
        "description": (
            "Tey verkörpert den Berliner Typus des Konzernhais: ehrgeizig, brutal und vor allem sich selbst verpflichtet. "
            "Schwarze Visitenkarten mit Sigma-Zeichen und RFID-Kontakt dienen als Markenzeichen; selbst höfliche "
            "Geschäftspartner müssen jederzeit mit einem Verrat rechnen."
        ),
        "source": "Schattenleben: Berlin, S. 8–9",
        "locations": [{"id": 196, "relation": "Konzernumfeld Evo Berlin"}],
    },
    {
        "id": "xabier-ezkibel",
        "name": "Dr. Xabier Ezkibel",
        "aliases": [],
        "category": "Schatten und Szene",
        "role": "Ripperdoc und Betreiber der Triage-Privatklinik",
        "affiliation": "Kreuzbasar-Kiez, Cezve-Clan",
        "status": "Aktiv",
        "metatype": "Elf",
        "summary": "Ezkibel operiert seit den 2040ern und gilt als medizinisches Gedächtnis des Kreuzbasars.",
        "description": (
            "Der erfahrene elfische Straßendoc ist ein langjähriger Verbündeter Kaschmirs und des Cezve-Clans. "
            "Neben diskreter Behandlung bietet seine ungewöhnlich lange Berliner Laufbahn Zugang zu Informationen "
            "aus den frühen Jahrzehnten der lokalen Schatten- und Kiezgeschichte."
        ),
        "source": "Berlin 2080, S. 44 und 154; Schattenleben: Berlin, S. 7",
        "locations": [{"id": 392, "relation": "Betreiber der Klinik"}],
    },
    {
        "id": "astrid-brugger",
        "name": "Dr. Astrid Brugger",
        "aliases": [],
        "category": "Konzerne",
        "role": "CEO der Schering Pharma AG",
        "affiliation": "Schering, Zeta-ImpChem",
        "status": "Aktiv",
        "summary": "Brugger steht nominell über den übrigen Berliner Z-IC-Vertretern und gibt bei Schering den Ton an.",
        "description": (
            "Unter ihrer Leitung erreichte Schering den größten Berliner Marktanteil bei Medikamenten und Medizingütern. "
            "Sie kontrolliert ein stadtweites Netz aus Verwaltung, Forschung, Produktion, Vertrieb und teils getarnten Laboren."
        ),
        "source": "Berlin 2080, S. 112",
        "locations": [{"id": 212, "relation": "Unternehmenssitz und Machtzentrum"}],
    },
    {
        "id": "mathias-anger",
        "name": "Dr. Mathias Anger",
        "aliases": [],
        "category": "Konzerne",
        "role": "Berliner Leiter von Messerschmitt-Kawasaki",
        "affiliation": "Messerschmitt-Kawasaki, Saeder-Krupp",
        "status": "Aktiv",
        "summary": "Anger steuert Produktion und Flughafenbetrieb in Schönefeld und gilt als harter Gegner der Sprawlguerilla.",
        "description": (
            "Der M-K-Chef verwaltet den Konzern seit den frühen 2070ern wieder von Schönefeld aus. Er sorgt für den "
            "Betrieb der gewaltigen Fabrik und des Flughafens BSI und verfolgt gegenüber Berliner Anarchisten eine "
            "ausgesprochen kompromisslose Linie."
        ),
        "source": "Berlin 2080, S. 63 und 106",
        "locations": [{"id": 204, "relation": "Leitung der M-K-Fabrik"}],
    },
    {
        "id": "arndt-wilhelm-koerting",
        "name": "Dr. Arndt-Wilhelm Koerting",
        "aliases": [],
        "category": "Konzerne",
        "role": "Mitglied der Doppelspitze von AG Chemie Berlin",
        "affiliation": "AG Chemie",
        "status": "Aktiv",
        "summary": "Koerting lenkt AG Chemie gemeinsam mit Robert Schlüter junior und verfügt über tiefe Pharmaerfahrung.",
        "description": (
            "Der frühere Schering-Chef bildet mit dem charismatischeren MSI-Leiter Schlüter die Berliner AGC-Doppelspitze. "
            "Sein Einfluss reicht von der Schwerindustrie Siemensstadts bis in Universitäten, Chemie- und Pharmanetzwerke."
        ),
        "source": "Berlin 2080, S. 107",
        "locations": [{"id": 185, "relation": "AGC-Führungszentrum"}],
    },
    {
        "id": "takumi-hanzo",
        "name": "Takumi Hanzo",
        "aliases": [],
        "category": "Konzerne",
        "role": "Deutschlandchef von Shiawase und Shiawase Envirotech",
        "affiliation": "Shiawase",
        "status": "Aktiv; Stellung geschwächt",
        "summary": "Hanzo führt Shiawases Deutschlandgeschäft aus Köpenick und ringt um Einfluss im Familienkonzern.",
        "description": (
            "Mit der Verlegung der Deutschlandzentrale nach Berlin verknüpfte Hanzo Shiawases Umweltgeschäft eng mit "
            "Köpenick. Sein anhaltender Streit mit dem früheren Deutschlandchef Leonard Berger und der Machtverlust "
            "seines Förderers Korin Yamana gefährden jedoch seine Position."
        ),
        "source": "Berlin 2080, S. 106",
        "locations": [{"id": 444, "relation": "Sitz der deutschen Shiawase-Zentrale"}],
    },
    {
        "id": "oskar-reuter",
        "name": "Oskar Reuter",
        "aliases": [],
        "category": "Konzerne",
        "role": "Gesamtleiter der Proteus-Sicherheit in Berlin",
        "affiliation": "Proteus",
        "status": "Aktiv",
        "summary": "Reuter ist ein langjähriger Berliner Sicherheitskommandeur und kompromissloser Konzernhardliner.",
        "description": (
            "Der frühere Kommandeur der Friedenstruppen von 2060 prägt Proteus' Berliner Sicherheitsapparat stärker "
            "als der offizielle Geschäftsführer. Er träumt weiterhin vom endgültigen Sieg über das anarchistische Berlin."
        ),
        "source": "Berlin 2080, S. 73",
        "locations": [{"id": 217, "relation": "Proteus-Sicherheitszentrale"}],
    },
    {
        "id": "roman-sigorski",
        "name": "Roman Sigorski",
        "aliases": [],
        "category": "Konzerne",
        "role": "Sicherheitschef von Saeder-Krupp Berlin",
        "affiliation": "Saeder-Krupp",
        "status": "Aktiv",
        "summary": "Sigorski gilt als wichtiger Mittelsmann zwischen Franziska Landolt und Berlins Schatten.",
        "description": (
            "Der Sicherheitschef gehört zu den diskreten Akteuren, über die S-Ks Berliner Geschäftsführung Runner und "
            "andere Schattenkräfte erreichen kann. Damit ist er ein zentraler operativer Arm Landolts außerhalb offizieller Konzernwege."
        ),
        "source": "Berlin 2080, S. 116",
        "locations": [{"id": 208, "relation": "S-K-Sicherheitszentrale"}],
    },
    {
        "id": "isabelle-jandorf",
        "name": "Dr. Isabelle Jandorf",
        "aliases": [],
        "category": "Politik und Verwaltung",
        "role": "ADL-Botschafterin und BERVAG-Kulturdirektorin",
        "affiliation": "ADL, BERVAG, Preußenstiftung",
        "status": "Aktiv",
        "summary": "Jandorf verbindet Diplomatie, Berliner Kulturpolitik und das schattenkundige Netzwerk der Preußenstiftung.",
        "description": (
            "Die Kunstexpertin wirkte maßgeblich an der Berliner Einigung mit und vertritt die ADL dauerhaft im Rat. "
            "Als BERVAG-Kulturdirektorin und Aufsichtsrätin der Preußenstiftung verfügt sie über Kontakte zu Spezialisten "
            "für Wiederbeschaffung, Kunstraub und diskrete Kulturmissionen."
        ),
        "source": "Berlin 2080, S. 116–117; Datapuls: Kunstraub, S. 12",
        "locations": [
            {"id": 301, "relation": "Diplomatische und politische Arbeit"},
            {"id": 284, "relation": "Umfeld der Preußenstiftung"},
        ],
    },
    {
        "id": "yilmaz-wojenko",
        "name": "Yilmaz Wojenko",
        "aliases": [],
        "category": "Sicherheit und Justiz",
        "role": "BERVAG-Polizeidirektor und früherer Erster Bürgermeister",
        "affiliation": "BERVAG, PsiAid",
        "status": "Aktiv",
        "summary": "Wojenko leitet die zentralen Polizeiaufgaben Berlins und gehört zu den Initiatoren des Kassandra-Systems.",
        "description": (
            "Der frühere Regierungschef verfügt als Polizeidirektor über einen umfassenden Aufklärungsapparat. Seine "
            "PsiAid-Verbindungen, die Kontrolle zentraler Polizeiaufgaben und seine Rolle beim Marschall-Pilotprojekt "
            "machen ihn zu einem der mächtigsten Sicherheitsakteure der Stadt."
        ),
        "source": "Berlin 2080, S. 8, 121 und 161; Datapuls: Berlin, S. 18",
        "locations": [
            {"id": 190, "relation": "Amt als Polizeidirektor"},
            {"id": 292, "relation": "Langjähriges PsiAid-Umfeld"},
        ],
    },
    {
        "id": "aiko-koizumi",
        "name": "Aiko Koizumi",
        "aliases": ["Aiko Kuizumi"],
        "category": "Politik und Verwaltung",
        "role": "BERVAG-Verkehrsdirektorin",
        "affiliation": "BERVAG, Renraku",
        "status": "Aktiv",
        "summary": "Koizumi verantwortet den Berliner Verkehr und wirkt am stadtweiten Kassandra-Überwachungssystem mit.",
        "description": (
            "Die Tochter des verschwundenen Renraku-Bezirksvertreters Ichiro Koizumi bewegt sich unter erheblichem "
            "Sicherheitsdruck. Eine zwölfköpfige Samurai-Leibgarde schützt sie, während sie BERVAG-Verkehrssysteme "
            "und Renrakus Überwachungskompetenz miteinander verknüpft."
        ),
        "source": "Berlin 2080, S. 8 und 116; Datapuls: Berlin, S. 18",
        "locations": [
            {"id": 190, "relation": "Amt als Verkehrsdirektorin"},
            {"id": 205, "relation": "Renraku-Umfeld"},
        ],
    },
    {
        "id": "tanja-cattarius",
        "name": "Tanja Cattarius",
        "aliases": [],
        "category": "Sicherheit und Justiz",
        "role": "Sternschutz-Chefermittlerin im Mordfall Koslowski",
        "affiliation": "Sternschutz",
        "status": "Aktiv",
        "summary": "Cattarius führt die weiterhin politisch brisante Untersuchung zum Tod des Z-IC-Vertreters Michael Koslowski.",
        "description": (
            "Die Chefermittlerin behandelt den ungeklärten Mord als möglichen Z-IC-Insiderjob. Dadurch berührt ihre "
            "Arbeit unmittelbar die Machtverhältnisse im Konzernbezirk Tegel und die Stellung Nathan Thompsons."
        ),
        "source": "Berlin 2080, S. 116–117",
        "locations": [{"id": 385, "relation": "Sternschutz-Ermittlungsumfeld"}],
    },
    {
        "id": "nadjeska-drakova-girkin",
        "name": "Nadjeska „Drakova“ Girkin",
        "aliases": ["Drakova"],
        "category": "Unterwelt",
        "role": "Vory-Anführerin und frühere Sovetnika Gargaris",
        "affiliation": "Drakova-Organisatzi",
        "status": "Aktiv",
        "summary": "Drakova kontrolliert große Teile des Berliner Vory-Erbes und führt ihr Syndikat aus den Osramhöfen.",
        "description": (
            "Nach Gargaris Tod zog die erfahrene Schieberin erhebliche Macht, Geschäfte und Territorien an sich. "
            "Ihre elfische Führungsriege, mögliche Drachenverbindungen und der Konflikt mit rivalisierenden Vory-Lideri "
            "machen sie zur gefährlichsten Unterweltfigur im Nordosten Berlins."
        ),
        "source": "Berlin 2080, S. 124–125",
        "locations": [{"id": 116, "relation": "Hauptquartier und Machtbasis"}],
    },
    {
        "id": "bal-balrog-kovac",
        "name": "Bal „Balrog“ Kovac",
        "aliases": ["Balrog"],
        "category": "Unterwelt",
        "role": "Troll-Boss der Horde und Herrscher Gropiusstadts",
        "affiliation": "Die Horde",
        "status": "Aktiv",
        "metatype": "Troll",
        "summary": "Balrog führt die Horde und beherrscht mit ihr den Gangbezirk Gropiusstadt.",
        "description": (
            "Der Troll-Boss etablierte die Horde nach blutigen Kämpfen als dominierende Macht des Bezirks. Von Block X "
            "aus verbindet er Gangherrschaft, Wettgeschäft und den Versuch, die Horde als Polizeidienst anerkennen zu lassen."
        ),
        "source": "Berlin 2080, S. 37–38 und 133",
        "locations": [
            {"id": 9, "relation": "Hauptquartier der Horde"},
            {"id": 448, "relation": "Beherrschtes Territorium"},
        ],
    },
    {
        "id": "ioanna-tsantidis",
        "name": "Ioanna Tsantidis",
        "aliases": [],
        "category": "Unterwelt",
        "role": "Ork-Hexe und Führungskraft der Horde",
        "affiliation": "Die Horde",
        "status": "Aktiv",
        "metatype": "Orkin",
        "summary": "Tsantidis bildet gemeinsam mit Balrog die sichtbare Machtspitze der Horde in Gropiusstadt.",
        "description": (
            "Die Ork-Hexe gehört zu Balrogs wichtigsten Lieutenants und ergänzt die rohe Gangmacht um magische Kompetenz. "
            "Ihre Stellung verbindet die Führung von Block X mit den berlinweiten Operationen der Horde."
        ),
        "source": "Berlin 2080, S. 37 und 133",
        "locations": [
            {"id": 9, "relation": "Führungszentrum der Horde"},
            {"id": 448, "relation": "Machtbasis Gropiusstadt"},
        ],
    },
    {
        "id": "takeo-maeda",
        "name": "Takeo Maeda",
        "aliases": [],
        "category": "Unterwelt",
        "role": "Kopf der Berliner Yakuza und Befehlsgeber der 99 Ronin",
        "affiliation": "Makahashi-Gumi, 99 Ronin",
        "status": "Aktiv",
        "summary": "Maeda führt seit rund einem Jahrzehnt die Berliner Yakuza und ihre hochmobile Bosozoku-Strikeforce.",
        "description": (
            "Der erfahrene Oyabun stabilisiert die Yakuza durch strategische Geschäfte, externe Runner und die "
            "blitzschnell einsetzbaren 99 Ronin. Seine Organisation nutzt die Unruhe der konkurrierenden Berliner Syndikate."
        ),
        "source": "Berlin 2080, S. 126–127",
        "locations": [{"id": 451, "relation": "Schwerpunkt japanischer Konzern- und Unterweltnetzwerke"}],
    },
    {
        "id": "ahmad-khalil",
        "name": "„Prinz“ Ahmad Khalil",
        "aliases": ["Saif ad-Din Abu Tariq Ahmad Khalil"],
        "category": "Unterwelt",
        "role": "Emir von Kreuzberg und Patriarch der Familie Khalil",
        "affiliation": "Emirat Kreuzberg, Familie Khalil",
        "status": "Aktiv",
        "summary": "Ahmad Khalil ist der Erste unter Gleichen der Familienoberhäupter im Berliner Emirat.",
        "description": (
            "Der Patriarch übernahm 2077 nach dem Tod seines Vaters Umar die Führung der reichsten und mächtigsten "
            "Familie des Emirats. Seine Autorität beruht auf Familienmacht, religiöser Stellung und dem Ausgleich "
            "zwischen den zahlreichen Einflussgebieten Kreuzbergs."
        ),
        "source": "Berlin 2080, S. 85–86",
        "locations": [{"id": 382, "relation": "Politisches und religiöses Umfeld des Emirats"}],
    },
    {
        "id": "daniel-moratti",
        "name": "Daniel Moratti",
        "aliases": [],
        "category": "Unterwelt",
        "role": "Baulöwe und Oberhaupt der Berliner Italo-Mafia",
        "affiliation": "Familie Moratti",
        "status": "Aktiv; öffentlich zurückgezogen",
        "summary": "Moratti verbindet legale Bauwirtschaft mit der Führung der Berliner Mafia.",
        "description": (
            "Der Baulöwe kappte öffentlich zahlreiche Verbindungen zur Unterwelt und überließ das Tagesgeschäft seiner "
            "rechten Hand Davide Cefarillo. Hinter der Fassade bleibt er jedoch das Oberhaupt einer Familie, deren Bau-, "
            "Schmuggel- und BTL-Geschäfte berlinweit wirken."
        ),
        "source": "Berlin 2080, S. 36 und 129–130",
        "locations": [],
        "scope": "Berlinweit; Schwerpunkt Bauwirtschaft und westlicher Außenring",
    },
    {
        "id": "abbas-tauhd-abu-el-hawa",
        "name": "Abbas Khaliq „Tauh’d“ Abu El Hawa",
        "aliases": ["Tauh’d"],
        "category": "Unterwelt",
        "role": "Anführer der Berliner Grauen Wölfe",
        "affiliation": "Graue Wölfe",
        "status": "Aktiv",
        "summary": "Tauh’d übernahm nach Asena Buluts Tod die Berliner Wölfe und richtete sie gegen die Sprawlguerilla aus.",
        "description": (
            "Der langjährige Vertrauensmann vereinte rasch die patriarchalen Fraktionen des Rudels. Seine Kontakte in das "
            "Emirat und zu radikalen Islamisten verschaffen ihm neue Optionen, isolieren die Berliner Wölfe aber zugleich "
            "von anderen Rudeln."
        ),
        "source": "Berlin 2080, S. 126–127",
        "locations": [{"id": 450, "relation": "Schwerpunkt der neuen Bündnisse und Konflikte"}],
    },
    {
        "id": "daisy-fix",
        "name": "Daisy Fix",
        "aliases": [],
        "category": "Unterwelt",
        "role": "Likedeeler-Schieberin und einflussreiche Schattenstimme",
        "affiliation": "Likedeeler",
        "status": "Aktiv",
        "summary": "Daisy ist eine der wichtigsten Berliner Beschafferinnen und prägt die lokale Likedeeler-Fraktion.",
        "description": (
            "Über ihr Netzwerk beschafft sie Waren aus allen Himmelsrichtungen und schleust sie an Zoll, Polizei, "
            "Konzernen und Syndikaten vorbei. Ihre wirtschaftlich orientierte Fraktion besitzt innerhalb der Berliner "
            "Likedeeler besonders großen Einfluss und weitreichende Kontakte auf Havel und Spree."
        ),
        "source": "Berlin 2080, S. 127–128",
        "locations": [{"id": 233, "relation": "Einer der ausgewiesenen Likedeeler-Treffpunkte"}],
    },
    {
        "id": "safiya-dafiya",
        "name": "Safiya Dafiya",
        "aliases": [],
        "category": "Schatten und Szene",
        "role": "Shadowtalkerin und Berliner Unterweltexpertin",
        "affiliation": "Panoptikum, Berliner Schattenszene",
        "status": "Aktiv",
        "summary": "Safiya kommentiert besonders fundiert das Emirat, die Grauen Wölfe und Berlins kriminelle Netzwerke.",
        "description": (
            "Die wiederkehrende Schattenstimme liefert Einordnungen zu Familienclans, Scharia-Gebieten, Syndikaten und "
            "magischen Gefahren. Ihre Beiträge zeigen detaillierte Ortskenntnis und belastbare Verbindungen in die "
            "Kreuzhainer sowie berlinweite Unterweltszene."
        ),
        "source": "Berlin 2080, S. 85–86, 126–127 und weitere",
        "locations": [{"id": 450, "relation": "Thematischer und sozialer Schwerpunkt"}],
    },
    {
        "id": "baba-iveta-jankulovski",
        "name": "Baba Iveta Jankulovski",
        "aliases": [],
        "category": "Unterwelt",
        "role": "Matriarchin eines orkischen Familienclans",
        "affiliation": "Jankulovski-Clan",
        "status": "Aktiv",
        "summary": "Baba Iveta gilt als lebende Legende der Kreuzhainer Ork-Clans.",
        "description": (
            "Als Übermutter einer riesigen Familie verfügt sie im gesamten Bezirk über Nachkommen und Verwandte, die "
            "ihr gehorchen. Dieses dichte Clan- und Kieznetz macht sie zu einer außergewöhnlich einflussreichen lokalen Machtfigur."
        ),
        "source": "Berlin 2080, S. 128",
        "locations": [{"id": 450, "relation": "Familien- und Machtbasis"}],
    },
    {
        "id": "davide-che-cefarillo",
        "name": "Davide „Che“ Cefarillo",
        "aliases": ["Che"],
        "category": "Unterwelt",
        "role": "Operativer Leiter der Moratti-Geschäfte",
        "affiliation": "Familie Moratti",
        "status": "Aktiv",
        "metatype": "Ork",
        "summary": "Cefarillo hält als rechte Hand Daniel Morattis die Berliner Geschäfte der Familie am Laufen.",
        "description": (
            "Während Moratti öffentlich zurückgezogen lebt, organisiert Cefarillo Bauprojekte, BTL-Schmuggel und das "
            "Tagesgeschäft. Seine Fixierung auf die Shader und das enorme Kopfgeld auf den Alten Fritz erzeugen zusätzliche Konflikte."
        ),
        "source": "Berlin 2080, S. 129–130",
        "locations": [],
        "scope": "Berlinweit; operative Geschäfte der Italo-Mafia",
    },
    {
        "id": "anne-archiste",
        "name": "Anne Archiste",
        "aliases": [],
        "category": "Schatten und Szene",
        "role": "Veteranin der Berliner Schattennetze und Chronistin",
        "affiliation": "Panoptikum, Schattenland Berlin",
        "status": "Aktiv",
        "summary": "Anne gehört zu den traditionsreichsten Stimmen der Berliner Schatten und bewahrt deren digitales Erbe.",
        "description": (
            "Nach längerer Abwesenheit kehrte die erfahrene Shadowtalkerin nach Berlin zurück. Sie kommentiert Stadt, "
            "Konzerne und Szene mit jahrzehntelanger Perspektive und betreut aktuelle sowie historische Dateien des "
            "nachgebildeten Schattenland-Berlin-Knotens."
        ),
        "source": "Berlin 2080, S. 10 und 141; Datapuls: Berlin, S. 4",
        "locations": [],
        "scope": "Berlinweit und im Schwarzen Netz",
    },
    {
        "id": "nanta-nierenstich",
        "name": "Nanta Nierenstich",
        "aliases": [],
        "category": "Medien und Kultur",
        "role": "Schwoof-Sängerin",
        "affiliation": "Black Pirate Records",
        "status": "Aktiv",
        "summary": "Nanta ist ein großer Berliner Musikstar mit bodenständigen, leicht anarchischen Mitsingtexten.",
        "description": (
            "Ihre Schwoof-Musik verbindet Berliner Alltagsnähe, eingängige Refrains und eine anarchische Grundhaltung. "
            "Gemeinsam mit Daemonika gehört sie zu den beiden großen Aushängeschildern des unabhängigen Labels Black Pirate."
        ),
        "source": "Berlin 2080, S. 171; Hinter dem Vorhang, S. 163",
        "locations": [{"id": 304, "relation": "Plattenlabel und künstlerisches Umfeld"}],
    },
    {
        "id": "doria-grey",
        "name": "Doria Grey",
        "aliases": [],
        "category": "Medien und Kultur",
        "role": "Industrial-Künstlerin",
        "affiliation": "Retrosic Records",
        "status": "Aktiv",
        "summary": "Doria Grey ist eine berühmte Industrial-Künstlerin und seit den 2070ern fest mit Retrosic Records verbunden.",
        "description": (
            "Mit „Into the Shadows“ gelang ihr bereits in den 2070ern der Durchbruch. Ihr schneller Aufstieg machte auch "
            "Retrosic Records bekannt; dem Label werden wegen dieser engen Verbindung Kontakte in die Schatten nachgesagt."
        ),
        "source": "Berlin 2080, S. 171; Hinter dem Vorhang, S. 163",
        "locations": [],
        "scope": "Berliner Musik- und Clubszene",
    },
    {
        "id": "sara-rosskotten",
        "name": "Dr. Sara Rosskotten",
        "aliases": [],
        "category": "Medien und Kultur",
        "role": "Geschäftsführerin der Preußenstiftung",
        "affiliation": "Preußenstiftung",
        "status": "Aktiv",
        "summary": "Rosskotten lenkt eine der mächtigsten deutschen Kunstinstitutionen von Potsdam aus.",
        "description": (
            "Die frühere Konzernlobbyistin führt die Stiftung deutlich diskreter als ihr Vorgänger und versteht es, "
            "Verhandlungspartner mit feinen Mitteln unter Druck zu setzen. Kunstrückführung, Denkmalschutz und eigene "
            "Schattenaufträge gehören zum politischen und operativen Instrumentarium der Stiftung."
        ),
        "source": "Datapuls: Kunstraub, S. 10–13",
        "locations": [{"id": 284, "relation": "Hauptsitz der Preußenstiftung"}],
    },
    {
        "id": "gerard-truesdale",
        "name": "Gérard Truesdale",
        "aliases": [],
        "category": "Schatten und Szene",
        "role": "Concierge des Adlon und diskreter Vermittler",
        "affiliation": "Hotel Adlon",
        "status": "Aktiv",
        "metatype": "Elf",
        "summary": "Truesdale erfüllt den mächtigsten Gästen des Adlon selbst ausgefallene Wünsche und besitzt zahllose Kontakte.",
        "description": (
            "Der elfische Adept folgt dem Weg des Sprechers und verbindet außergewöhnlichen Charme mit einem dichten "
            "Netz aus VIP-, Konzern- und Szenekontakten. In dem als neutraler Kontaktbörse geltenden Luxushotel ist er "
            "eine ideale diskrete Schnittstelle zu Berlins einflussreichsten Besuchern."
        ),
        "source": "Berlin 4D, S. 61",
        "locations": [{"id": 161, "relation": "Concierge und Kontaktvermittler"}],
    },
    {
        "id": "swonimir-kalauk",
        "name": "Swonimir Kalauk",
        "aliases": [],
        "category": "Magie und Erwachte",
        "role": "Sorbischer Priester und Begründer des Spreewaldpakts",
        "affiliation": "Sorbische magische Tradition",
        "status": "Aktiv oder historisch wirksam",
        "summary": "Kalauk schuf den Pakt, der Sorben vor den Erwachten Wesen und Geistern des Spreewalds schützt.",
        "description": (
            "Der Priester verband sorbischen katholischen Glauben und erwachte schamanische Praxis. Sein Abkommen mit "
            "dem Spreewald schützt Menschen sorbischer Abstammung, solange sie Natur, Ruhe und örtliche Gepflogenheiten achten."
        ),
        "source": "Schattenleben: Berlin, S. 6",
        "locations": [{"id": 366, "relation": "Nördlicher Rand des erwachenden Spreewalds"}],
    },
    {
        "id": "krypt",
        "name": "Krypt",
        "aliases": [],
        "category": "Matrix und Technik",
        "role": "Cracker-Legende und CryptoLink-Entwickler",
        "affiliation": "Berliner Cracker-Syndikat",
        "status": "Untergetaucht",
        "summary": "Krypt arbeitet an einem angeblich unknackbar verschlüsselten Kommlink für freie Bürger.",
        "description": (
            "Nach mehreren Attentatsversuchen tauchte die Berliner Matrixlegende mit einem CryptoLink-Prototypen unter. "
            "Der Cracker-Host The Void gilt als praktisch einziger Ort, an dem Krypt gelegentlich noch erreichbar ist."
        ),
        "source": "Berlin 2080, S. 141",
        "locations": [],
        "scope": "The Void im Schwarzen Netz; kein physischer Standort bekannt",
    },
]


def renrakusan_coordinates(entity_id: int) -> list[list[float]]:
    coordinates = []
    for _, x, y in RENRAKUSAN_MAP_MARKERS.get(entity_id, []):
        lon = sum(value * coefficient for value, coefficient in zip((x, y, 1), RENRAKUSAN_TRANSFORM["lon"]))
        lat = sum(value * coefficient for value, coefficient in zip((x, y, 1), RENRAKUSAN_TRANSFORM["lat"]))
        coordinates.append([round(lon, 6), round(lat, 6)])
    return coordinates


# Affine georeferencing derived from landmarks printed on the published maps.
# x/y are percentages of the PDF page; outputs are WGS84 longitude/latitude.
TRANSFORMS = {
    "overview": {
        "lon": (0.013844928661472161, 0.00015954598762771277, 12.578068071564207),
        "lat": (0.00003703504573993041, -0.005504799155130857, 52.80660870449488),
    },
    "Mitte": {
        "lon": (0.0012504293744836636, -0.00005069585595454673, 13.31054605912534),
        "lat": (-0.000020288380552124785, -0.0005409664219113708, 52.530854294324826),
    },
    "Dreamland": {
        "lon": (0.0005221137792543844, 0.0007459250734189737, 13.343454830130401),
        "lat": (0.00017813108962128066, -0.0005071743402715878, 52.583351125399574),
    },
}


DISTRICTS = [
    {
        "id": 440,
        "name": "Reinickendorf",
        "lat": 52.6378,
        "lon": 13.2756,
        "pages": "57–59",
        "description": (
            "Reinickendorf ist nach der Abtretung des wirtschaftlich starken Tegeler Zentrums an Z-IC/Schering "
            "politisch und wirtschaftlich erschüttert. Der flächenreiche Bezirk besteht überwiegend aus niedriger, "
            "teils verfallener Bebauung; nur einzelne Hochhaussiedlungen und Konzernenklaven stechen heraus. "
            "Anarchistische Kräfte gewinnen Zulauf, während Geschäftsleute und Parteien um die Zukunft des Bezirks ringen."
        ),
    },
    {
        "id": 441,
        "name": "Pankow",
        "lat": 52.6163,
        "lon": 13.4700,
        "pages": "53–55",
        "description": (
            "Pankow ist nach dem Tod des russischen Mafiapaten Pjotr Gargari eine zersplitterte Machtbasis der Vory. "
            "Zwischen alten Plattenbauten, weitläufigen Einfamilienhaussiedlungen und großem Leerstand sortieren die "
            "Syndikate ihre Geschäfte neu. Noch ist der Bezirk keine offene Kriegszone, doch Rivalen warten auf den "
            "Moment, in dem die russischen Fraktionen sich endgültig gegenseitig schwächen."
        ),
    },
    {
        "id": 442,
        "name": "Lichtenberg",
        "lat": 52.5540,
        "lon": 13.5820,
        "pages": "45–47",
        "description": (
            "Lichtenberg organisiert Versorgung, Sicherheit und Verwaltung weitgehend über anarchosyndikalistische "
            "Kollektive. Genossenschaftliche Netze halten Plattenbauten, Wohnsiedlungen und selbst das umgerüstete "
            "Heizkraftwerk Klingenberg am Laufen. Die ausgeprägte Selbstorganisation und alternative Kommunikationsnetze "
            "machen den Bezirk zugleich zu einem wichtigen Rückzugsraum der Sprawlguerilla."
        ),
    },
    {
        "id": 443,
        "name": "Marzahn",
        "lat": 52.4880,
        "lon": 13.6200,
        "pages": "47–49",
        "description": (
            "Marzahn steckt nach dem Tod des „Zaren von Berlin“ in einem gewaltsamen Machtvakuum. Vory-Fraktionen, "
            "große Gangs und kleinere Profiteure kämpfen zwischen verfallenen Wohngebieten, Schrottplätzen und belasteten "
            "Industrieflächen um Reviere und Warenströme. Die Lage ist gefährlich, eröffnet Schattenleuten aber lukrative "
            "Geschäfte mit Transporten, Nachschub und den aufstrebenden Machtspielern."
        ),
    },
    {
        "id": 444,
        "name": "Köpenick",
        "lat": 52.4100,
        "lon": 13.5700,
        "pages": "39–41",
        "description": (
            "Köpenick versteht sich als freiwilliger Außenseiter Berlins. Zwischen sauberen Wasserläufen, Hanffeldern, "
            "Hausbooten und kleinen Cafés pflegen Freidenker, Künstler, Ökokommunen und die Hexen der Müggelberge eine "
            "vergleichsweise friedliche, naturnahe Lebensweise. Dezentrale Selbstversorgung und die Abneigung gegen die "
            "Megakonzerne verbinden die sehr unterschiedlichen Gemeinschaften."
        ),
    },
    {
        "id": 445,
        "name": "Spandau",
        "lat": 52.4780,
        "lon": 13.1450,
        "pages": "67–70",
        "description": (
            "Spandau entstand nach der Berliner Einigung wieder als eigener alternativer Bezirk, nachdem Aztechnology und "
            "AG Chemie das vernachlässigte Gebiet abgestoßen hatten. Starker Lokalpatriotismus trifft auf leerstehende "
            "Siedlungen, schnell alternde Neubauten und wenige sehr wohlhabende Enklaven im Südwesten. Aztechnology, "
            "Familienclans und nationalistische Vereinsnetzwerke bleiben einflussreiche Machtfaktoren."
        ),
    },
    {
        "id": 446,
        "name": "Chawi",
        "lat": 52.5000,
        "lon": 13.2680,
        "pages": "32–34",
        "description": (
            "Chawi, die alltägliche Kurzform von Charlottenburg-Wilmersdorf, ist Berlins große Adresse für Vergnügen, "
            "Kultur und Konsum. High Society, Partygänger, Künstler, Einwanderer und Straßenvolk teilen sich belebte "
            "Einkaufsachsen, dichte Wohnkieze und exklusive Villenkolonien. DeMeKo prägt das öffentliche Bild, doch nahezu "
            "jeder Konzern und zahlreiche unabhängige Gruppen besitzen hier eigene Interessen."
        ),
    },
    {
        "id": 447,
        "name": "Zehlendorf",
        "lat": 52.4230,
        "lon": 13.2580,
        "pages": "72–74",
        "description": (
            "Zehlendorf zählt zu den größten, reichsten und grünsten Bezirken des früheren Konzernwestens. Der sichere, "
            "vergleichsweise tolerante Bezirk wird von den Anlagen Evos und von Proteus geprägt und weist besonders viele "
            "transgen oder auffällig modifizierte Bewohner auf. Unter der gepflegten Oberfläche liegen alte Fuchi-Tunnel, "
            "Konzernbunker und die unfertige, besetzte Kowloon-Arkologie."
        ),
    },
    {
        "id": 448,
        "name": "Gropiusstadt",
        "lat": 52.4460,
        "lon": 13.4350,
        "pages": "37–39",
        "description": (
            "Gropiusstadt ist ein von der Horde beherrschtes Gang-Königreich zwischen abgeschotteten Konzernbezirken. "
            "Terror und Unterdrückung sichern einen fragilen Frieden in den verfallenden, zu Festungen umgebauten "
            "Wohnblöcken. Cybears-Spiele, Gladiatorenkämpfe und inszeniertes Anarcho-Flair locken zahlungskräftige "
            "Besucher an, während die Bewohner mit dem gewalttätigen Herrschaftssystem leben müssen."
        ),
    },
    {
        "id": 449,
        "name": "Mitte",
        "lat": 52.5160,
        "lon": 13.3900,
        "pages": "49–51",
        "description": (
            "Mitte ist Schaufenster, Machtzentrum und touristisches Gesicht der Freistadt. Sehenswürdigkeiten, Clubs, "
            "Hotels sowie die Repräsentanzbauten von Banken und Konzernen konzentrieren sich in den City-Arealen. Nur "
            "wenige Straßenzüge weiter beginnen ruhige oder vernachlässigte Wohnkieze; Sicherheit und Investitionen folgen "
            "vor allem der glänzenden Fassade des Zentrums."
        ),
    },
    {
        "id": 450,
        "name": "Kreuzhain",
        "lat": 52.4920,
        "lon": 13.4580,
        "pages": "41–45",
        "description": (
            "Kreuzhain versteht sich als gelebter friedlicher Status Fluxus. Kieze, Policlubs und Interessengruppen "
            "verhindern dauerhafte Machtkonzentration durch wechselnde Bündnisse und erfahrene Vermittler. Der bunte "
            "Multikulti-, Kunst- und Partybezirk bleibt trotz Gentrifizierung lebendig, steht aber unter Druck durch "
            "Konflikte an den Schariagebieten und die Unruhe der Berliner Unterwelt."
        ),
    },
    {
        "id": 451,
        "name": "Renrakusan",
        "lat": 52.5450,
        "lon": 13.4900,
        "pages": "59–62",
        "description": (
            "Renrakusan ist Renrakus dicht bebauter Modellbezirk einer vollständig vernetzten Smart City. Der frühere "
            "Prenzlauer Berg wurde weitgehend abgerissen und im Neo-Tokio-Stil mit Arkologien, Passagen, Holos und "
            "automatisierten Verkehrs- und Warenströmen neu errichtet. Strenge Sicherheitsgesetze, lückenlose technische "
            "Kontrolle und die Konzernpolizei bestimmen den Alltag."
        ),
    },
]


UMLAND_AREAS = [
    {
        "id": 452,
        "name": "Aztech-Schönwalde",
        "municipalities": ["Schönwalde-Glien"],
        "pages": "30–32",
        "description": (
            "Aztech-Schönwalde ist eine von Aztechnology geformte Konzernlandschaft im Nordwesten Berlins. "
            "Zwischen Wald, Feuchtwiesen und Mooren liegen Forschungsstationen, Zuchtkomplexe, weitläufige "
            "Crittergehege und abgeschirmte Hallen. Alte Siedlungen wurden entvölkert oder zu Geisterorten, während "
            "neue Anlagen vor allem Forschung, Aufzucht sowie die Verarbeitung und Verteilung von Nahrung bedienen."
        ),
    },
    {
        "id": 453,
        "name": "Falkensee",
        "municipalities": ["Falkensee"],
        "pages": "35–37",
        "description": (
            "Falkensee bildet den äußersten westlichen Rand des Berliner Sprawls. Verfallene Infrastruktur, ruinierte "
            "Wohngebiete und brachliegende Flächen prägen den alternativen Bezirk, dessen wenige bewohnbare Blöcke "
            "nahe Spandau liegen. Kleine Gangs, Schmuggler, der Özdemir-Clan und Vory-Interessen ringen um die knappen "
            "Warenströme, während Aztech die nördliche Grenze streng abschirmt."
        ),
    },
    {
        "id": 454,
        "name": "Oranienburg",
        "municipalities": ["Oranienburg", "Leegebruch", "Velten", "Birkenwerder", "Hohen Neuendorf"],
        "pages": "51–53",
        "description": (
            "Oranienburg reicht laut Lore von Birkenwerder und Borgsdorf über Velten und Leegebruch bis zur alten "
            "Stadt Oranienburg. Im ländlichen Westen dominiert der Bundesgrenzschutz, im heruntergekommenen Süden "
            "leben viele Verdrängte, und im Nordosten kontrolliert die Investorengruppe Oranienburg das restaurierte "
            "Zentrum. Militär, Grenzpolitik, Wohlstandsenklaven und anarchistische Rückzugsorte liegen dicht beieinander."
        ),
    },
    {
        "id": 455,
        "name": "Potsdam",
        "municipalities": ["Potsdam"],
        "pages": "55–57",
        "description": (
            "Potsdam ist ein Bezirk der Extreme. Altstadt, Sanssouci und die Schlösser werden zur idealisierten "
            "preußischen Schaubühne für Touristen und Eliten umgebaut. Dagegen gelten Babelsberg und Drewitz als "
            "abgehängt, während der Westen und Norden von einem brüchigen Mittelstand geprägt sind. Hinter der "
            "historischen Fassade treffen Prestigeprojekte, soziale Spannungen und verborgene Interessen aufeinander."
        ),
    },
    {
        "id": 456,
        "name": "Schönefeld",
        "municipalities": ["Schönefeld", "Blankenfelde-Mahlow"],
        "pages": "62–64",
        "description": (
            "Schönefeld ist Flughafen, Industriebezirk und logistisches Tor zugleich. Rund um Berlin-Schönefeld "
            "International, Messerschmitt-Kawasaki und zahlreiche Zulieferer verbinden sich Fertigungshallen, "
            "Werkstraßen und gepflegte Wohngebiete zu einem dauerhaft arbeitenden Komplex. Konzernsicherheit schützt "
            "die legalen Warenströme ebenso wie die Schattenwege, die sich in deren Zwischenräumen öffnen."
        ),
    },
    {
        "id": 457,
        "name": "Strausberg",
        "municipalities": ["Strausberg"],
        "pages": "70–72",
        "description": (
            "Strausberg liegt als einziger Berliner Lore-Bezirk vollständig außerhalb des Autobahnrings. Zwischen "
            "zerstörten Militäranlagen entstanden abgeschirmte Fabrikfestungen, Zulieferbetriebe, Schutthalden und "
            "verseuchte Brachen. Die Mischung aus Konzerninseln, ärmlichen Siedlungen und zahlreichen Verstecken macht "
            "das abgelegene Industriegebiet zugleich gefährlich und besonders attraktiv für Schattenoperationen."
        ),
    },
]


# Additional, explicitly localizable Berlin locations found outside the original
# Berlin-2080 map legend. Names are kept source-faithful; approximate placements
# are clearly marked instead of pretending street-level precision.
CORPUS_SPOTS = [
    {
        "id": 458,
        "name": "Die grüne Neune",
        "category": "Restaurants",
        "lat": 52.505485,
        "lon": 13.297067,
        "source": "Schattenload 12/2020",
        "pages": "2",
        "placement": "Adressgenau: Leonhardtstraße 9, Chawi",
        "accuracy": "Adressgenau",
        "description": (
            "Das vegane High-End-Restaurant von Paul-Rufus Klupp verbindet bewusst zurückhaltende AR mit einem "
            "organisch inszenierten Gastraum, Koi-Teich und handwerklicher Küche. Nach mehreren Auszeichnungen gerät "
            "der einstige Szeneliebling durch die neue Konkurrenz auf der gegenüberliegenden Straßenseite wirtschaftlich "
            "unter Druck und wird zum Ausgangspunkt der Mission „Küchenkrieg“."
        ),
    },
    {
        "id": 459,
        "name": "Umami",
        "category": "Restaurants",
        "lat": 52.505152,
        "lon": 13.296735,
        "source": "Schattenload 12/2020",
        "pages": "2–3",
        "placement": "Adressgenau: Leonhardtstraße 20, Chawi",
        "accuracy": "Adressgenau",
        "description": (
            "Das Umami kombiniert teures Restaurant, Bar-Lounge und Szeneclub in einem dunklen, von Monitorflächen "
            "und bewegten Lichtmotiven geprägten Kubus. Besitzerin Sofia al-Aziz lässt Gerichte der grünen Neune "
            "kopieren und versetzt viele Speisen heimlich mit einem suchterzeugenden Spreewald-Extrakt, das Gäste "
            "rasch zu Stammkunden macht."
        ),
    },
    {
        "id": 460,
        "name": "Lasterburg",
        "category": "Sonstige Spots",
        "lat": 52.506362,
        "lon": 13.458719,
        "source": "Schattenload 12/2019",
        "pages": "7",
        "placement": "Straßengenau: Modersohnstraße, Kreuzhain",
        "accuracy": "Straßengenau",
        "description": (
            "Die Lasterburg gilt als älteste Berliner Wagenburg. Rund dreißig überwiegend von Familien bewohnte Wagen "
            "bilden eine eng verbundene Gemeinschaft in der Modersohnstraße. Sprecher Khan und die Hexe Alisha sind "
            "die wichtigsten Ansprechpersonen der traditionsreichen Rollheimer-Siedlung."
        ),
    },
    {
        "id": 461,
        "name": "Schinderclanburg",
        "category": "Sonstige Spots",
        "lat": 52.582071,
        "lon": 13.247710,
        "source": "Schattenload 12/2019",
        "pages": "7",
        "placement": "Quellenabgeleitet: Baustelle am Schwarzen Weg, Z-IC Tegel",
        "accuracy": "Straßengenau",
        "description": (
            "Die Schinderclanburg wechselt mit den Baustellen ihrer Bewohner den Standort und steht derzeit am "
            "Schwarzen Weg in Tegel. Etwa fünfzig Wagen gehören zu der arbeitsamen Rollheimer-Sippe. Die geschäftige "
            "Sprecherin Patrizia organisiert Arbeit und Zusammenhalt, steht jedoch mutmaßlich unter Druck des Ringbunds."
        ),
    },
    {
        "id": 462,
        "name": "Mobilkommune 030",
        "category": "Sonstige Spots",
        "lat": 52.421000,
        "lon": 13.682000,
        "source": "Schattenload 12/2019",
        "pages": "7",
        "placement": "Gebietsgenau: wechselnder Standort im Raum Köpenick",
        "accuracy": "Mobiler Standort",
        "description": (
            "Die kleine Mobilkommune 030 umfasst etwa zehn Wagen und zieht häufig innerhalb Köpenicks um. Sie ist für "
            "illegale und besonders riskante Aufträge bekannt. Der elfische Sprecher Joker vermittelt Jobs, während "
            "der Gnom Florentin als außergewöhnlich fähiger Schrauber und Rigger gilt."
        ),
    },
    {
        "id": 463,
        "name": "Taka-Tuka",
        "category": "Sonstige Spots",
        "lat": 52.495795,
        "lon": 13.408960,
        "source": "Schattenload 12/2019",
        "pages": "7",
        "placement": "Quellenabgeleitet: Schattenhafen am Urbanhafen",
        "accuracy": "Gebietsgenau",
        "description": (
            "Taka-Tuka ist Berlins einzige größere Hausboot-Burg. Zwölf Boote liegen gegenwärtig im Schattenhafen am "
            "Urbanhafen und bilden eine schwimmende Rollheimer-Gemeinschaft. Offizieller Sprecher ist der meist "
            "berauschte Kirk; tatsächlich hält die Hexe Jade den Verband zusammen."
        ),
    },
    {
        "id": 464,
        "name": "Kreuzweg64",
        "category": "Sonstige Spots",
        "lat": 52.502700,
        "lon": 13.334400,
        "source": "Schattenload 12/2019",
        "pages": "7",
        "placement": "Quellenabgeleitet: Baubrache gegenüber der Hauergasse",
        "accuracy": "Gebietsgenau",
        "description": (
            "Kreuzweg64 dient im Westen der Stadt als Zwischenstation für Konzernaussteiger. Rund zwanzig Wagen stehen "
            "derzeit auf einer Baubrache gegenüber der Hauergasse. Die von der Elfin Charona und dem Trollhexer Schelle "
            "geführte Gemeinschaft ist den umliegenden Konzerninteressen entsprechend lästig."
        ),
    },
    {
        "id": 465,
        "name": "Slawenburg",
        "category": "Sonstige Spots",
        "lat": 52.412000,
        "lon": 13.644000,
        "source": "Schattenload 12/2019",
        "pages": "7",
        "placement": "Gebietsgenau: wechselnder Standort in Köpenick",
        "accuracy": "Mobiler Standort",
        "description": (
            "Die Slawenburg ist eine extreme Lowtech-Kommune aus Kutschen, Zelten und Jurten in Köpenick. Ihre rund "
            "zwanzig Behausungen bilden eine frei organisierte Großfamilie. Zu den prägenden Personen gehören der "
            "Troll Jaxa, der Adept Cernebog und die elfische Hexe Baba Vorona."
        ),
    },
    {
        "id": 466,
        "name": "Biberburg",
        "category": "Sonstige Spots",
        "lat": 52.515423,
        "lon": 13.184848,
        "source": "Schattenload 12/2019",
        "pages": "7",
        "placement": "Straßengenau: Gatower Straße, Spandau",
        "accuracy": "Straßengenau",
        "description": (
            "Die Biberburg besteht aus etwa fünfzehn Wagen an der Gatower Straße am Rand der Gartenstadt Gatow. Die "
            "kleine Rollheimer-Gemeinschaft wird vom Ork Ratschke vertreten; die menschliche Priesterin Josie übernimmt "
            "die spirituelle Betreuung und hilft bei Konflikten mit dem schwierigen Umfeld."
        ),
    },
    {
        "id": 467,
        "name": "Höllendorf / Fuchi-Labor",
        "category": "Sonstige Spots",
        "lat": 52.526351,
        "lon": 13.500553,
        "source": "Auswurfschock",
        "pages": "180–183",
        "placement": "Straßengenau: Industriegebiet Herzbergstraße, Marzahn/Lichtenberg",
        "accuracy": "Straßengenau",
        "description": (
            "Das „Höllendorf“ ist ein von der Neuen Faschistischen Alternative kontrollierter Teil des Industriegebiets "
            "Herzbergstraße. Zwischen Drogenproduktion, Waffenplagiaten und improvisierter Miliz liegt unter drei "
            "unscheinbaren Gebäuden ein vergessenes Fuchi-Labor samt alter Kabelmatrix-Hardware – und dem verborgenen "
            "Einfluss einer gefährlichen KI."
        ),
    },
    {
        "id": 468,
        "name": "Trismegistos",
        "category": "Einkaufen",
        "lat": 52.557701,
        "lon": 13.345319,
        "source": "Datapuls: 10 Konzerne",
        "pages": "20–22",
        "placement": "Gebietsgenau: begrünter Innenhof im Englischen Viertel, Wedding",
        "accuracy": "Gebietsgenau",
        "description": (
            "Der alte Taliskramladen Trismegistos ist der Ursprung des heutigen Trismeg-Konzerns. Die unscheinbare "
            "Filiale liegt im begrünten Innenhof eines Wohnblocks im Englischen Viertel. Werkstatt und frühere "
            "Wohnräume könnten noch genutzt werden; die Geschichte des Ladens ist eng mit Reinhardt Fuchs und dem "
            "freien Geist Aurek verbunden."
        ),
    },
    {
        "id": 469,
        "name": "Trismeg-Hauptgeschäftsstelle",
        "category": "Konzerne",
        "lat": 52.542787,
        "lon": 13.367000,
        "source": "Datapuls: 10 Konzerne",
        "pages": "20–22",
        "placement": "Quellenabgeleitet: Bürokomplex nahe M-Bahnhof Wedding",
        "accuracy": "Gebietsgenau",
        "description": (
            "Trismegs Berliner Hauptgeschäftsstelle belegt mehrere Etagen eines Bürokomplexes nahe dem Bahnhof Wedding. "
            "Von hier führt Elyse Fuchs den auf magische Produkte, erschwingliche Foki und jugendliche Zielgruppen "
            "spezialisierten A-Konzern. Hinter den populären Marken arbeitet Aurek an Verzauberungen mit beunruhigenden "
            "Verbindungen zu den Träumen ihrer Nutzer."
        ),
    },
    {
        "id": 470,
        "name": "Preußens Arkadien",
        "category": "Sonstige Spots",
        "lat": 52.411284,
        "lon": 13.087545,
        "source": "Datapuls: 10 Konzerne",
        "pages": "23–25",
        "placement": "Adressgenau: Glienicker Horn und Villa Kampffmeyer, Potsdam",
        "accuracy": "Gebietsgenau",
        "description": (
            "Preußens Arkadien entstand als eine der ersten abgeschlossenen Luxus-Wohnenklaven Deutschlands rund um "
            "die Villa Kampffmeyer am Glienicker Horn. Klassizistische Villen, Jachthafen und dauerhafte Sicherheits- "
            "sowie Versorgungsdienste wurden zum Ausgangspunkt des heutigen Arkadia-Konzerns und seines Netzes aus "
            "maßgeschneiderten Gated Communities."
        ),
    },
    {
        "id": 471,
        "name": "Eden Apartments",
        "category": "Sonstige Spots",
        "lat": 52.456900,
        "lon": 13.322700,
        "source": "Datapuls: 10 Konzerne",
        "pages": "24–25",
        "placement": "Bezirksgenau: Steglitz",
        "accuracy": "Bezirksgenau",
        "description": (
            "Die Eden Apartments sind ein einzelnes, von Arkadia geschütztes Wohnobjekt in Steglitz. Die Anlage steht "
            "beispielhaft für den Konzernansatz, bestehende Luxusimmobilien über eigene Matrixarchitektur, Sensorik und "
            "Sicherheitsdienste zu einer abgeschirmten Enklave für zahlungskräftige Bewohner zu machen."
        ),
    },
    {
        "id": 472,
        "name": "Lenné Höfe",
        "category": "Sonstige Spots",
        "lat": 52.497200,
        "lon": 13.425500,
        "source": "Datapuls: 10 Konzerne",
        "pages": "24–25",
        "placement": "Bezirksgenau: verborgenes Altbauensemble in Kreuzhain",
        "accuracy": "Bezirksgenau",
        "description": (
            "Die Lenné Höfe sind ein verborgenes Ensemble luxuriöser Altbauwohnungen in Kreuzhain. Arkadia verbindet "
            "die einzelnen Häuser technisch und organisatorisch zu einer geschlossenen Wohnenklave. Das nach außen "
            "unscheinbare Objekt schützt vermögende Bewohner durch gestaffelte Hosts, Überwachung und diskrete Dienste."
        ),
    },
    {
        "id": 473,
        "name": "Elysium Estates",
        "category": "Sonstige Spots",
        "lat": 52.488934,
        "lon": 13.204700,
        "source": "Datapuls: 10 Konzerne",
        "pages": "24–25",
        "placement": "Straßengenau: Villenenklave an der Havelchaussee",
        "accuracy": "Straßengenau",
        "description": (
            "Die Elysium Estates bilden eine weitläufige Villenenklave an der Havelchaussee. Arkadia integriert Tore, "
            "Zugangskontrollen, Wachpersonal, Sensoren und Hausdienste in eine gemeinsame Sicherheitsarchitektur. "
            "Bewohner kaufen damit nicht nur Schutz, sondern auch Zugang zu den gesellschaftlichen Netzwerken der "
            "Berliner Oberschicht."
        ),
    },
    {
        "id": 474,
        "name": "Pfandleihe Köpenick",
        "category": "Einkaufen",
        "lat": 52.441400,
        "lon": 13.558900,
        "source": "Datapuls: Kunstraub",
        "pages": "21–22",
        "placement": "Quellenabgeleitet: Köpenicker Zentrum, nahe dem Stroganoff",
        "accuracy": "Gebietsgenau",
        "description": (
            "Die unlizenzierte Pfandleihe Köpenick entwickelte sich vom Status-F-Leihhaus zu einer Adresse für "
            "hochkarätige Pfänder wie Daten, Artefakte, Militärtechnik und gestohlene Kunst. Betreiberin Clara Moser "
            "unterhält enge Kontakte zur autonomen Szene. Eine angeschlossene Fälscherwerkstatt zerlegt, verändert oder "
            "legitimiert problematische Ware."
        ),
    },
    {
        "id": 475,
        "name": "Otogibanshi-Viertel",
        "category": "Sonstige Spots",
        "lat": renrakusan_coordinates(475)[0][1],
        "lon": renrakusan_coordinates(475)[0][0],
        "source": "Renrakusan-Detailkarte",
        "pages": "S9",
        "placement": "Straßengenau aus dem Renrakusan-Bezirksplan georeferenziert",
        "accuracy": "Detailkarte",
        "description": (
            "Das Otogibanshi-Viertel ist als Standort S9 auf dem Renrakusan-Bezirksplan verzeichnet. "
            "Seine Position folgt der Einzelkarte; eine weiterführende Ortsbeschreibung ist in der "
            "vorliegenden Kartenlegende nicht enthalten."
        ),
    },
]


def district_preview(description: str, limit: int = 165) -> str:
    if len(description) <= limit:
        return description
    return description[:limit].rsplit(" ", 1)[0] + "…"


def build_district_features(districts: list[dict]) -> list[dict]:
    features = []
    for district in districts:
        description = district["description"]
        pages = district["pages"]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [district["lon"], district["lat"]]},
                "properties": {
                    "id": district["id"],
                    "name": district["name"],
                    "category": "Bezirke",
                    "detail_map": "",
                    "source_pages": f"Berlin 2080: {pages}",
                    "map_source": "Berlin 2080 Karte v04 – Bezirkslayout",
                    "placement_note": "Marker am Flächenschwerpunkt der straßengenauen ALKIS-Bezirksbasis",
                    "accuracy": "Lore-Bezirk",
                    "source_map": "district",
                    "source_panel": "overview",
                    "description_preview": district_preview(description),
                    "description_full": description,
                    "description_source": f"Berlin 2080, S. {pages}",
                    "description_kind": "Bezirksprofil",
                    "description_has_more": len(description) > 165,
                    "detail_plans": ["renrakusan"] if district["id"] == 451 else [],
                },
            }
        )
    return features


def district_entities(districts: list[dict]) -> list[dict]:
    return [
        {
            "id": district["id"],
            "name": district["name"],
            "map_label": district["name"],
            "category": "Bezirke",
            "detail_map": "",
            "source_pages": f"Berlin 2080: {district['pages']}",
            "map_source": "Berlin 2080 Karte v04 – Bezirkslayout",
            "placement_note": "Marker am Flächenschwerpunkt der straßengenauen ALKIS-Bezirksbasis",
        }
        for district in districts
    ]


def build_umland_features(areas: list[dict]) -> list[dict]:
    features = []
    for area in areas:
        description = area["description"]
        pages = area["pages"]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [area["lon"], area["lat"]]},
                "properties": {
                    "id": area["id"],
                    "name": area["name"],
                    "category": "Umlandgebiete",
                    "detail_map": "",
                    "source_pages": f"Berlin 2080: {pages}",
                    "map_source": "Berlin 2080 Karte v04 – Lore-Umland",
                    "placement_note": "Marker am Flächenschwerpunkt der amtlichen Brandenburger Gemeindegrundlage",
                    "accuracy": "Lore-Umland",
                    "source_map": "outskirts",
                    "source_panel": "overview",
                    "description_preview": district_preview(description),
                    "description_full": description,
                    "description_source": f"Berlin 2080, S. {pages}",
                    "description_kind": "Umlandprofil",
                    "description_has_more": len(description) > 165,
                },
            }
        )
    return features


def umland_entities(areas: list[dict]) -> list[dict]:
    return [
        {
            "id": area["id"],
            "name": area["name"],
            "map_label": area["name"],
            "category": "Umlandgebiete",
            "detail_map": "",
            "source_pages": f"Berlin 2080: {area['pages']}",
            "map_source": "Berlin 2080 Karte v04 – Lore-Umland",
            "placement_note": "Marker am Flächenschwerpunkt der amtlichen Brandenburger Gemeindegrundlage",
        }
        for area in areas
    ]


def build_corpus_features(spots: list[dict]) -> list[dict]:
    features = []
    for spot in spots:
        description = spot["description"]
        renrakusan_spot = spot["id"] == 475
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [spot["lon"], spot["lat"]]},
                "properties": {
                    "id": spot["id"],
                    "name": spot["name"],
                    "category": spot["category"],
                    "detail_map": "",
                    "source_pages": f"{spot['source']}: {spot['pages']}",
                    "map_source": "Renrakusan-Bezirksplan, Stand März 2080" if renrakusan_spot else "Shadowrun-6D-Quellenkorpus",
                    "placement_note": spot["placement"],
                    "accuracy": spot["accuracy"],
                    "source_map": "renrakusan" if renrakusan_spot else "corpus",
                    "source_panel": "Renrakusan" if renrakusan_spot else spot["source"],
                    "description_preview": district_preview(description),
                    "description_full": description,
                    "description_source": f"{spot['source']}, S. {spot['pages']}",
                    "description_kind": "Karteneintrag" if renrakusan_spot else "Quellenerweiterung",
                    "description_has_more": len(description) > 165,
                    "detail_plans": ["renrakusan"] if spot["id"] == 475 else [],
                    "alternate_locations": [],
                },
            }
        )
    return features


def corpus_entities(spots: list[dict]) -> list[dict]:
    return [
        {
            "id": spot["id"],
            "name": spot["name"],
            "map_label": spot["name"],
            "category": spot["category"],
            "detail_map": "",
            "source_pages": f"{spot['source']}: {spot['pages']}",
            "map_source": "Shadowrun-6D-Quellenkorpus",
            "placement_note": spot["placement"],
        }
        for spot in spots
    ]


def canonical_location_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name.casefold())
    normalized = "".join(character for character in normalized if not unicodedata.combining(character))
    normalized = re.sub(r"^(?:der|die|das)\s+", "", normalized)
    return re.sub(r"[^a-z0-9]+", "", normalized)


def validate_additional_spots(catalog: dict, districts: list[dict], umland: list[dict], spots: list[dict]) -> None:
    existing = {
        canonical_location_name(item["name"]): item["name"]
        for item in catalog["entities"] + districts + umland
    }
    seen_names = set()
    seen_ids = {item["id"] for item in catalog["entities"] + districts + umland}
    seen_coordinates = set()
    for spot in spots:
        canonical = canonical_location_name(spot["name"])
        if canonical in existing:
            raise ValueError(f"Duplicate location '{spot['name']}' matches '{existing[canonical]}'")
        if canonical in seen_names:
            raise ValueError(f"Duplicate additional location name: {spot['name']}")
        if spot["id"] in seen_ids:
            raise ValueError(f"Duplicate location id: {spot['id']}")
        coordinate = (round(spot["lat"], 6), round(spot["lon"], 6))
        if coordinate in seen_coordinates:
            raise ValueError(f"Duplicate additional marker coordinates: {spot['name']}")
        seen_names.add(canonical)
        seen_ids.add(spot["id"])
        seen_coordinates.add(coordinate)


CURRENT_TO_LORE = {
    "Mitte": "Mitte",
    "Friedrichshain-Kreuzberg": "Kreuzhain",
    "Pankow": "Pankow / Renrakusan",
    "Charlottenburg-Wilmersdorf": "Chawi",
    "Spandau": "Spandau",
    "Steglitz-Zehlendorf": "Zehlendorf",
    "Tempelhof-Schöneberg": "Chawi / S-K Tempelhof",
    "Neukölln": "Gropiusstadt",
    "Treptow-Köpenick": "Köpenick",
    "Marzahn-Hellersdorf": "Marzahn",
    "Lichtenberg": "Lichtenberg",
    "Reinickendorf": "Reinickendorf",
}


DISTRICT_CENTER_BASES = {
    "Reinickendorf": {"districts": ["Reinickendorf"]},
    "Pankow": {
        "neighborhoods": [
            "Weißensee", "Blankenburg", "Heinersdorf", "Karow", "Stadtrandsiedlung Malchow", "Pankow",
            "Blankenfelde", "Buch", "Französisch Buchholz", "Niederschönhausen", "Rosenthal", "Wilhelmsruh",
        ]
    },
    "Lichtenberg": {"districts": ["Lichtenberg"]},
    "Marzahn": {"districts": ["Marzahn-Hellersdorf"]},
    "Köpenick": {"districts": ["Treptow-Köpenick"]},
    "Spandau": {"districts": ["Spandau"]},
    "Chawi": {"districts": ["Charlottenburg-Wilmersdorf"], "neighborhoods": ["Schöneberg", "Friedenau"]},
    "Zehlendorf": {"districts": ["Steglitz-Zehlendorf"]},
    "Gropiusstadt": {"districts": ["Neukölln"]},
    "Mitte": {"districts": ["Mitte"]},
    "Kreuzhain": {"districts": ["Friedrichshain-Kreuzberg"]},
    "Renrakusan": {"neighborhoods": ["Prenzlauer Berg"]},
}


def ring_centroid(ring: list[list[float]]) -> tuple[float, float, float]:
    twice_area = 0.0
    cx = 0.0
    cy = 0.0
    for first, second in zip(ring, ring[1:]):
        cross = first[0] * second[1] - second[0] * first[1]
        twice_area += cross
        cx += (first[0] + second[0]) * cross
        cy += (first[1] + second[1]) * cross
    if abs(twice_area) < 1e-15:
        lon = sum(point[0] for point in ring) / len(ring)
        lat = sum(point[1] for point in ring) / len(ring)
        return lon, lat, 0.0
    return cx / (3 * twice_area), cy / (3 * twice_area), abs(twice_area / 2)


def geometry_centroid(geometry: dict) -> tuple[float, float, float]:
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    weighted_lon = 0.0
    weighted_lat = 0.0
    total_area = 0.0
    for polygon in polygons:
        lon, lat, area = ring_centroid(polygon[0])
        weighted_lon += lon * area
        weighted_lat += lat * area
        total_area += area
    return weighted_lon / total_area, weighted_lat / total_area, total_area


def center_lore_districts(official_districts: dict, official_neighborhoods: dict) -> list[dict]:
    districts_by_name = {feature["properties"]["namgem"]: feature for feature in official_districts["features"]}
    neighborhoods_by_name = {feature["properties"]["nam"]: feature for feature in official_neighborhoods["features"]}
    centered = []
    for district in DISTRICTS:
        sources = DISTRICT_CENTER_BASES[district["name"]]
        features = [districts_by_name[name] for name in sources.get("districts", [])]
        features.extend(neighborhoods_by_name[name] for name in sources.get("neighborhoods", []))
        centroids = [geometry_centroid(feature["geometry"]) for feature in features]
        total_area = sum(item[2] for item in centroids)
        updated = dict(district)
        updated["lon"] = round(sum(lon * area for lon, _, area in centroids) / total_area, 6)
        updated["lat"] = round(sum(lat * area for _, lat, area in centroids) / total_area, 6)
        centered.append(updated)
    return centered


def geometry_polygons(geometry: dict) -> list[list[list[list[float]]]]:
    if geometry["type"] == "MultiPolygon":
        return geometry["coordinates"]
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"]]
    raise ValueError(f"Unsupported geometry type: {geometry['type']}")


def prepare_umland_areas(official_municipalities: dict) -> tuple[list[dict], dict]:
    municipalities_by_name = {
        feature["properties"]["gem_name"]: feature for feature in official_municipalities["features"]
    }
    centered_areas = []
    boundary_features = []
    for area in UMLAND_AREAS:
        missing = [name for name in area["municipalities"] if name not in municipalities_by_name]
        if missing:
            raise KeyError(f"Missing Brandenburg municipalities for {area['name']}: {', '.join(missing)}")
        basis_features = [municipalities_by_name[name] for name in area["municipalities"]]
        polygons = [
            polygon
            for feature in basis_features
            for polygon in geometry_polygons(feature["geometry"])
        ]
        geometry = {"type": "MultiPolygon", "coordinates": polygons}
        lon, lat, _ = geometry_centroid(geometry)
        updated = dict(area)
        updated["lon"] = round(lon, 6)
        updated["lat"] = round(lat, 6)
        centered_areas.append(updated)
        boundary_features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "name": area["name"],
                    "basis": ", ".join(area["municipalities"]),
                    "source": "GeoBasis-DE/LGB – Verwaltungsgebiete Brandenburg",
                },
            }
        )
    boundaries = {
        "type": "FeatureCollection",
        "name": "Shadowrun Berlin 2080 Lore-Umland Brandenburg",
        "features": boundary_features,
    }
    return centered_areas, boundaries


def geometry_bounds(geometries: list[dict]) -> list[list[float]]:
    points = [
        point
        for geometry in geometries
        for polygon in geometry_polygons(geometry)
        for ring in polygon
        for point in ring
    ]
    longitudes = [point[0] for point in points]
    latitudes = [point[1] for point in points]
    return [[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]]


def prepare_boundary_layers(official_districts: dict, official_neighborhoods: dict) -> tuple[dict, dict]:
    district_features = []
    for feature in official_districts["features"]:
        current_name = feature["properties"]["namgem"]
        district_features.append(
            {
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": {
                    "name": CURRENT_TO_LORE[current_name],
                    "basis": current_name,
                    "source": "Geoportal Berlin – ALKIS Bezirke",
                },
            }
        )
    prenzlauer_berg = next(
        feature for feature in official_neighborhoods["features"] if feature["properties"]["nam"] == "Prenzlauer Berg"
    )
    district_features.append(
        {
            "type": "Feature",
            "geometry": prenzlauer_berg["geometry"],
            "properties": {
                "name": "Renrakusan",
                "basis": "Prenzlauer Berg",
                "source": "Berlin 2080 / Geoportal Berlin – ALKIS Ortsteile",
            },
        }
    )
    neighborhood_features = [
        {
            "type": "Feature",
            "geometry": feature["geometry"],
            "properties": {
                "name": feature["properties"]["nam"],
                "source": "Geoportal Berlin – ALKIS Ortsteile",
            },
        }
        for feature in official_neighborhoods["features"]
    ]
    return (
        {"type": "FeatureCollection", "name": "Shadowrun Berlin 2080 Bezirksgrenzen", "features": district_features},
        {"type": "FeatureCollection", "name": "Berlin Stadtteilgrenzen", "features": neighborhood_features},
    )


def apply_transform(marker: dict) -> tuple[float, float]:
    key = marker["panel"] if marker["map"] == "details" else "overview"
    transform = TRANSFORMS[key]
    x = float(marker["x_pct"])
    y = float(marker["y_pct"])
    lon = transform["lon"][0] * x + transform["lon"][1] * y + transform["lon"][2]
    lat = transform["lat"][0] * x + transform["lat"][1] * y + transform["lat"][2]
    return round(lon, 6), round(lat, 6)


def choose_marker(entity: dict, markers: list[dict]) -> dict | None:
    candidates = [marker for marker in markers if marker["id"] == entity["id"]]
    if not candidates:
        return None
    detail_map = entity.get("detail_map")
    if detail_map:
        for marker in candidates:
            if marker["map"] == "details" and marker["panel"] == detail_map:
                return marker
    for marker in candidates:
        if marker["map"] == "overview":
            return marker
    return candidates[0]


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous[:2]
        x2, y2 = current[:2]
        if (y1 > lat) != (y2 > lat):
            intersection = (x2 - x1) * (lat - y1) / (y2 - y1) + x1
            if lon < intersection:
                inside = not inside
        previous = current
    return inside


def point_in_geometry(lon: float, lat: float, geometry: dict) -> bool:
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    for polygon in polygons:
        if point_in_ring(lon, lat, polygon[0]) and not any(point_in_ring(lon, lat, hole) for hole in polygon[1:]):
            return True
    return False


def build_geojson(catalog: dict, allowed_geometries: list[dict], descriptions: dict[int, dict]) -> dict:
    features = []
    detail_plans_by_marker = {
        marker_id: [plan["key"] for plan in DETAIL_ATLAS if marker_id in plan["marker_ids"]]
        for marker_id in {marker_id for plan in DETAIL_ATLAS for marker_id in plan["marker_ids"]}
    }
    for entity in catalog["entities"]:
        marker = choose_marker(entity, catalog["markers"])
        renrakusan_points = renrakusan_coordinates(entity["id"])
        if marker is None and not renrakusan_points:
            continue
        marker_coordinate = apply_transform(marker) if marker else None
        if renrakusan_points:
            if marker_coordinate and len(renrakusan_points) > 1:
                primary = min(
                    renrakusan_points,
                    key=lambda coordinate: (coordinate[0] - marker_coordinate[0]) ** 2
                    + (coordinate[1] - marker_coordinate[1]) ** 2,
                )
                renrakusan_points = [primary] + [point for point in renrakusan_points if point != primary]
            lon, lat = renrakusan_points[0]
        else:
            lon, lat = marker_coordinate
        inside_lore_scope = any(point_in_geometry(lon, lat, geometry) for geometry in allowed_geometries)
        inside_published_v06 = 12.8583 <= lon <= 13.9786 and 52.2608 <= lat <= 52.8103
        if not inside_lore_scope and not (entity["id"] <= 430 and inside_published_v06):
            continue
        if renrakusan_points:
            accuracy = "Renrakusan-Detailkarte"
        elif marker["map"] == "details":
            accuracy = "Detailkarte"
        elif marker.get("placement") == "Offizieller Kartenmarker":
            accuracy = "Übersichtskarte"
        else:
            accuracy = "Quellenabgeleitet"
        detail_plans = detail_plans_by_marker.get(entity["id"], [])
        if renrakusan_points and "renrakusan" not in detail_plans:
            detail_plans = [*detail_plans, "renrakusan"]
        if renrakusan_points:
            map_source = "Renrakusan-Bezirksplan, Stand März 2080"
            placement_note = "Aus der Renrakusan-Einzelkarte georeferenziert"
            source_map = "renrakusan"
            source_panel = "Renrakusan"
        else:
            map_source = (
                "Berlin 2080 Karte v06 – Detailkarten"
                if marker["map"] == "details"
                else "Berlin 2080 Karte v06 – Übersicht"
            )
            placement_note = entity.get("placement_note", "")
            source_map = marker["map"]
            source_panel = marker["panel"]
        properties = {
            "id": entity["id"],
            "name": entity["name"],
            "category": entity["category"],
            "detail_map": entity.get("detail_map", ""),
            "source_pages": entity.get("source_pages", ""),
            "map_source": map_source,
            "placement_note": placement_note,
            "accuracy": accuracy,
            "source_map": source_map,
            "source_panel": source_panel,
            "description_preview": descriptions[entity["id"]]["preview"],
            "description_full": descriptions[entity["id"]]["full"],
            "description_source": descriptions[entity["id"]]["source"],
            "description_kind": descriptions[entity["id"]]["kind"],
            "description_has_more": descriptions[entity["id"]]["has_more"],
            "detail_plans": detail_plans,
            "alternate_locations": renrakusan_points[1:] if len(renrakusan_points) > 1 else [],
        }
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": properties,
            }
        )
    return {
        "type": "FeatureCollection",
        "name": "Shadowrun Berlin 2080 Orte",
        "features": features,
    }


def build_cropped_overlay() -> None:
    raw = SOURCE_SVG.read_text(encoding="utf-8")
    raw, count = re.subn(
        r'<svg xmlns="http://www\.w3\.org/2000/svg" xmlns:xlink="http://www\.w3\.org/1999/xlink" width="2494\.49pt" height="1666\.77pt" viewBox="0 0 2494\.49 1666\.77" version="1\.2">',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        'width="1989.49" height="1666.77" viewBox="505 0 1989.49 1666.77" version="1.2">',
        raw,
        count=1,
    )
    if count != 1:
        raise RuntimeError("Could not crop the source SVG: unexpected root element")
    OVERLAY_SVG.write_text(raw, encoding="utf-8")


def build_offline_base() -> None:
    """Create a compact raster base that browsers can pan and zoom efficiently."""
    with Image.open(SOURCE_RENDER) as source:
        image = source.convert("RGB")
    crop_left = round(image.width * (505 / 2494.49))
    image = image.crop((crop_left, 0, image.width, image.height))
    image = ImageEnhance.Brightness(image).enhance(1.08)
    image = ImageEnhance.Contrast(image).enhance(1.12)
    image = ImageEnhance.Color(image).enhance(0.92)
    image.save(OFFLINE_BASE_WEBP, "WEBP", quality=88, method=6)
    CITY_ASSET_DIR.mkdir(parents=True, exist_ok=True)
    CITY_OFFLINE_BASE.write_bytes(OFFLINE_BASE_WEBP.read_bytes())


def build_detail_atlas() -> list[dict]:
    """Render and compress all supplied detail maps for lazy in-browser viewing."""
    Image.MAX_IMAGE_PIXELS = None
    DETAIL_PLAN_DIR.mkdir(parents=True, exist_ok=True)
    CITY_DETAIL_PLAN_DIR.mkdir(parents=True, exist_ok=True)
    atlas = []
    for plan in DETAIL_ATLAS:
        source = SOURCE_MAP_DIR / plan["source"]
        if not source.exists():
            raise FileNotFoundError(f"Detail map missing: {source}")
        if source.suffix.lower() == ".pdf":
            render_prefix = DETAIL_PLAN_DIR / f"{plan['key']}-render"
            subprocess.run(
                [
                    "pdftoppm",
                    "-f",
                    "1",
                    "-singlefile",
                    "-png",
                    "-r",
                    "150",
                    str(source),
                    str(render_prefix),
                ],
                check=True,
            )
            image_path = render_prefix.with_suffix(".png")
        else:
            image_path = source
        with Image.open(image_path) as raw_image:
            image = raw_image.convert("RGB")
        image.thumbnail((2400, 2000), Image.LANCZOS)
        target = DETAIL_PLAN_DIR / f"{plan['key']}.webp"
        image.save(target, "WEBP", quality=84, method=6)
        public_target = CITY_DETAIL_PLAN_DIR / target.name
        public_target.write_bytes(target.read_bytes())
        atlas.append(
            {
                "key": plan["key"],
                "title": plan["title"],
                "kind": plan["kind"],
                "source": plan["source"],
                "summary": plan["summary"],
                "markerIds": plan["marker_ids"],
                "width": image.width,
                "height": image.height,
                "image": "data:image/webp;base64," + base64.b64encode(target.read_bytes()).decode("ascii"),
            }
        )
    return atlas


ZONE_RULES = {
    "magenta": {
        "label": "Shadowrun-Zone Magenta",
        "color": "#ff16a4",
        "minimum": 20000,
        "test": lambda r, g, b: r > 70 and b > 45 and r > g * 2.3 and b > g * 2.0 and r - b < 80,
    },
    "grau": {
        "label": "Shadowrun-Zone Grau",
        "color": "#4b515d",
        "minimum": 20000,
        "test": lambda r, g, b: 35 < r < 135 and abs(r - g) < 13 and abs(g - b) < 13,
    },
    "orange": {
        "label": "Shadowrun-Enklave Orange",
        "color": "#ffa326",
        "minimum": 800,
        "test": lambda r, g, b: r > 145 and 65 < g < 190 and b < 125 and r - g > 28 and g - b > 25,
    },
    "tuerkis": {
        "label": "Shadowrun-Sondergebiet Türkis",
        "color": "#50d9c8",
        "minimum": 2000,
        "test": lambda r, g, b: (
            105 < r < 205 and 125 < g < 215 and 115 < b < 205 and g - r > 8 and b - r > 0 and abs(g - b) < 28
        ),
    },
}

CORPORATE_COMPONENT_LABELS = {
    2: "Z-IC Tegel / AGC Siemensstadt",
    3: "Renrakusan",
    4: "S-K Tempelhof",
}

AREA_STATUS = {
    "magenta": {"status": "normal", "label": "Normales Gebiet", "color": "#ff2ea6"},
    "grau": {"status": "anarcho", "label": "Anarcho-Gebiet", "color": "#59616e"},
    "orange": {"status": "corporate", "label": "Exterritoriales Konzerngebiet", "color": "#f5f06a"},
}


def build_area_status(zones: dict) -> dict:
    features = []
    for feature in zones["features"]:
        properties = feature["properties"]
        status = AREA_STATUS[properties["zone_type"]]
        label = status["label"]
        if properties["zone_type"] == "orange":
            corporate_name = CORPORATE_COMPONENT_LABELS.get(properties["component"])
            if corporate_name:
                label = f"{label} · {corporate_name}"
        features.append(
            {
                **feature,
                "properties": {
                    **properties,
                    "status": status["status"],
                    "label": label,
                    "color": status["color"],
                },
            }
        )
    return {"type": "FeatureCollection", "name": "Gebietsstatus Berlin 2080", "features": features}


def stable_slug(value: object) -> str:
    normalized = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "eintrag"


def search_text(*values: object) -> str:
    flattened: list[str] = []
    for value in values:
        if isinstance(value, dict):
            flattened.extend(str(item) for item in value.values())
        elif isinstance(value, list):
            flattened.extend(str(item) for item in value)
        elif value is not None:
            flattened.append(str(value))
    return unicodedata.normalize("NFKD", " ".join(flattened)).encode("ascii", "ignore").decode("ascii").lower()


def source_book(citation: str) -> dict | None:
    folded = citation.casefold()
    for book in SOURCE_BOOKS:
        if any(pattern.casefold() in folded for pattern in book["patterns"]):
            return book
    return None


def parse_source_references(value: str, purpose: str) -> list[dict]:
    references = []
    for raw in re.split(r"\s*;\s*", value or ""):
        citation = raw.strip()
        if not citation:
            continue
        book = source_book(citation)
        references.append(
            {
                "bookId": book["id"] if book else "unclassified",
                "title": book["title"] if book else citation,
                "edition": book["edition"] if book else "UNKLAR",
                "citation": citation,
                "purpose": purpose,
            }
        )
    return references


def deduplicate_sources(references: list[dict]) -> list[dict]:
    result = []
    seen = set()
    for reference in references:
        normalized_citation = reference["citation"].casefold()
        normalized_citation = re.sub(r",?\s*s\.\s*", ":", normalized_citation)
        normalized_citation = re.sub(r"\s*:\s*", ":", normalized_citation)
        normalized_citation = re.sub(r"\s+", "", normalized_citation)
        key = (reference["edition"], normalized_citation)
        if key in seen:
            continue
        seen.add(key)
        result.append(reference)
    return result


def edition_sort_key(edition: str) -> int:
    return EDITION_ORDER.index(edition) if edition in EDITION_ORDER else -1


def build_edition_descriptions(
    name: str,
    references: list[dict],
    description_source: str,
    description_kind: str,
    preview: str,
    full: str,
    has_more: bool,
) -> dict:
    description_references = parse_source_references(description_source, "description")
    description_editions = {
        reference["edition"]
        for reference in description_references
        if reference["edition"] in EDITION_ORDER
    }
    editions = sorted(
        {reference["edition"] for reference in references if reference["edition"] in EDITION_ORDER},
        key=edition_sort_key,
    )
    descriptions = {}
    for edition in editions:
        edition_sources = [reference for reference in references if reference["edition"] == edition]
        if edition in description_editions:
            descriptions[edition] = {
                "kind": description_kind,
                "preview": preview,
                "full": full,
                "hasMore": has_more,
                "hasExcerpt": True,
                "sources": edition_sources,
            }
        else:
            notice = (
                f"{name} ist in den ausgewerteten Quellen dieser Edition belegt. "
                f"Ein eigener {edition}-Quellenauszug ist noch nicht hinterlegt."
            )
            descriptions[edition] = {
                "kind": "Quellennachweis",
                "preview": notice,
                "full": notice,
                "hasMore": False,
                "hasExcerpt": False,
                "sources": edition_sources,
            }
    return descriptions


def enrich_payload_with_editions(payload: dict) -> list[str]:
    available = set()
    for feature in payload["geojson"]["features"]:
        properties = feature["properties"]
        references = deduplicate_sources(
            parse_source_references(properties.get("source_pages", ""), "reference")
            + parse_source_references(properties.get("description_source", ""), "description")
            + parse_source_references(properties.get("map_source", ""), "map")
        )
        descriptions = build_edition_descriptions(
            properties["name"],
            references,
            properties.get("description_source", ""),
            properties.get("description_kind", "Quellenauszug"),
            properties.get("description_preview", ""),
            properties.get("description_full", ""),
            bool(properties.get("description_has_more")),
        )
        editions = sorted(descriptions, key=edition_sort_key)
        properties["sources"] = references
        properties["map_sources"] = parse_source_references(properties.get("map_source", ""), "map")
        properties["editions"] = editions
        properties["edition_descriptions"] = descriptions
        available.update(editions)

    for person in payload["persons"]:
        references = deduplicate_sources(parse_source_references(person.get("source", ""), "description"))
        descriptions = build_edition_descriptions(
            person["name"], references, person.get("source", ""), "Personendossier",
            person.get("summary", ""), person.get("description", ""), True,
        )
        editions = sorted(descriptions, key=edition_sort_key)
        person["sources"] = references
        person["editions"] = editions
        person["edition_descriptions"] = descriptions
        available.update(editions)

    payload["availableEditions"] = sorted(available, key=edition_sort_key)
    return payload["availableEditions"]


def write_json(path: Path, payload: object, *, readable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if readable:
        serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    path.write_text(serialized + "\n", encoding="utf-8")


def update_city_registry() -> dict:
    registry_path = PUBLIC_DATA_DIR / "cities.json"
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    else:
        registry = {"schemaVersion": 1, "cities": []}
    berlin = {
        "id": CITY_ID,
        "name": "Berlin",
        "year": 2080,
        "manifest": f"data/{CITY_ID}/manifest.json",
        "default": True,
    }
    cities = [city for city in registry.get("cities", []) if city.get("id") != CITY_ID]
    if any(city.get("default") for city in cities):
        berlin["default"] = False
    cities.append(berlin)
    registry = {"schemaVersion": 1, "cities": sorted(cities, key=lambda city: city["name"])}
    write_json(registry_path, registry, readable=True)
    return registry


def merge_unique(first, second):
    result = []
    seen = set()
    for value in [*(first or []), *(second or [])]:
        signature = json.dumps(value, sort_keys=True, ensure_ascii=False)
        if signature in seen:
            continue
        seen.add(signature)
        result.append(value)
    return result


def apply_augmentations(entries: list, augmentations: list, *, properties: bool = False) -> None:
    by_id = {entry["id"]: entry for entry in augmentations}
    for entry in entries:
        target = entry.get("properties", {}) if properties else entry
        augmentation = by_id.get(target.get("id"))
        if not augmentation:
            continue
        for key, value in augmentation.items():
            if key in {"id", "global_id"}:
                continue
            if key in {"aliases", "editions", "sources", "map_sources", "locations"}:
                target[key] = merge_unique(target.get(key), value)
            elif key == "edition_descriptions":
                target[key] = {**target.get(key, {}), **value}
            else:
                target[key] = value


def build_global_search_index(registry: dict) -> dict:
    items = []
    for city in registry.get("cities", []):
        manifest_path = ROOT / city["manifest"]
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        city_dir = manifest_path.parent
        places = json.loads((city_dir / manifest["files"]["places"]).read_text(encoding="utf-8"))
        for key in ("virtualPlaces", "historicalPlaces"):
            supplemental_path = manifest.get("files", {}).get(key)
            if supplemental_path:
                supplemental = json.loads((city_dir / supplemental_path).read_text(encoding="utf-8"))
                places["features"].extend(supplemental.get("features", []))
        place_augmentations_path = manifest.get("files", {}).get("placeAugmentations")
        if place_augmentations_path:
            apply_augmentations(
                places["features"],
                json.loads((city_dir / place_augmentations_path).read_text(encoding="utf-8")),
                properties=True,
            )
        people = json.loads((city_dir / manifest["files"]["people"]).read_text(encoding="utf-8"))
        historical_people_path = manifest.get("files", {}).get("historicalPeople")
        if historical_people_path:
            people.extend(json.loads((city_dir / historical_people_path).read_text(encoding="utf-8")))
        person_augmentations_path = manifest.get("files", {}).get("personAugmentations")
        if person_augmentations_path:
            apply_augmentations(
                people,
                json.loads((city_dir / person_augmentations_path).read_text(encoding="utf-8")),
            )
        city_label = f"{city['name']} {city.get('year', '')}".strip()
        for feature in places.get("features", []):
            properties = feature["properties"]
            items.append(
                {
                    "cityId": city["id"],
                    "cityName": city["name"],
                    "cityLabel": city_label,
                    "type": "place",
                    "id": properties["id"],
                    "globalId": properties.get("global_id"),
                    "name": properties["name"],
                    "category": properties.get("category", "Ort"),
                    "editions": properties.get("editions", []),
                    "search": search_text(
                        properties.get("name"), properties.get("category"), properties.get("description_full"),
                        properties.get("description_source"), properties.get("source_pages"), properties.get("aliases"),
                        properties.get("editions"), properties.get("edition_descriptions"),
                    ),
                }
            )
        for person in people:
            items.append(
                {
                    "cityId": city["id"],
                    "cityName": city["name"],
                    "cityLabel": city_label,
                    "type": "person",
                    "id": person["id"],
                    "globalId": person.get("global_id"),
                    "name": person["name"],
                    "category": person.get("category", "Person"),
                    "entityType": person.get("entity_type", "person"),
                    "editions": person.get("editions", []),
                    "search": search_text(
                        person.get("name"), person.get("aliases"), person.get("category"), person.get("role"),
                        person.get("affiliation"), person.get("summary"), person.get("description"), person.get("source"),
                        person.get("members"), person.get("danger"), person.get("editions"), person.get("edition_descriptions"),
                    ),
                }
            )
    index = {"schemaVersion": 1, "items": items}
    write_json(PUBLIC_DATA_DIR / "search-index.json", index)
    return index


def write_city_package(payload: dict, registry: dict) -> dict:
    places = json.loads(json.dumps(payload["geojson"], ensure_ascii=False))
    global_ids: dict[object, str] = {}
    for feature in places["features"]:
        properties = feature["properties"]
        legacy_id = properties["id"]
        global_id = f"{CITY_ID}:place:{legacy_id}-{stable_slug(properties['name'])}"
        properties["legacy_id"] = legacy_id
        properties["global_id"] = global_id
        global_ids[legacy_id] = global_id

    people = json.loads(json.dumps(payload["persons"], ensure_ascii=False))
    for person in people:
        person["global_id"] = f"{CITY_ID}:person:{stable_slug(person['id'])}"
        for link in person.get("locations", []):
            if link.get("id") in global_ids:
                link["global_id"] = global_ids[link["id"]]

    atlas = []
    for plan in payload["atlas"]:
        atlas.append(
            {
                **plan,
                "image": f"../../assets/cities/{CITY_ID}/detail-maps/{plan['key']}.webp",
            }
        )

    zones = json.loads(json.dumps(payload["areaStatus"], ensure_ascii=False))
    exterritorial = {
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
    files = {
        "places": "places.geojson",
        "virtualPlaces": "virtual-places.geojson",
        "historicalPlaces": "historical-places.geojson",
        "placeAugmentations": "place-augmentations.json",
        "people": "people.json",
        "historicalPeople": "historical-people.json",
        "personAugmentations": "person-augmentations.json",
        "atlas": "atlas.json",
        "zones": "zones.geojson",
        "exterritorial": "exterritorial.geojson",
        "districts": "districts.geojson",
        "neighborhoods": "neighborhoods.geojson",
        "outskirts": "outskirts.geojson",
        "boundary": "city-boundary.geojson",
        "labels": "labels.json",
        "sources": "sources.json",
    }
    sources = sorted(
        {
            value
            for feature in places["features"]
            for value in (
                feature["properties"].get("source_pages"),
                feature["properties"].get("description_source"),
                feature["properties"].get("map_source"),
            )
            if value
        }
        | {person["source"] for person in people if person.get("source")}
        | {"Netzgewitter, S. 18-19"}
    )
    manifest = {
        "schemaVersion": 1,
        "id": CITY_ID,
        "name": "Berlin",
        "year": 2080,
        "dataVersion": 13,
        "availableEditions": payload["availableEditions"],
        "center": [52.5200066, 13.404954],
        "zoom": 10,
        "overlayBounds": payload["overlayBounds"],
        "cityBounds": payload["cityBounds"],
        "regionBounds": payload["regionBounds"],
        "summary": payload["summary"],
        "files": files,
        "assets": {"offlineBase": f"../../assets/cities/{CITY_ID}/offline-base.webp"},
    }
    write_json(CITY_DATA_DIR / files["places"], places)
    write_json(CITY_DATA_DIR / files["people"], people, readable=True)
    write_json(CITY_DATA_DIR / files["atlas"], atlas, readable=True)
    write_json(CITY_DATA_DIR / files["zones"], zones)
    write_json(CITY_DATA_DIR / files["exterritorial"], exterritorial)
    write_json(CITY_DATA_DIR / files["districts"], payload["districtBoundaries"])
    write_json(CITY_DATA_DIR / files["neighborhoods"], payload["neighborhoodBoundaries"])
    write_json(CITY_DATA_DIR / files["outskirts"], payload["umlandBoundaries"])
    write_json(CITY_DATA_DIR / files["boundary"], payload["boundary"])
    write_json(CITY_DATA_DIR / files["labels"], payload["loreLabels"], readable=True)
    write_json(
        CITY_DATA_DIR / files["sources"],
        {
            "schemaVersion": 1,
            "books": [
                {"id": book["id"], "title": book["title"], "edition": book["edition"]}
                for book in SOURCE_BOOKS
            ],
            "citations": sources,
        },
        readable=True,
    )
    write_json(CITY_DATA_DIR / "manifest.json", manifest, readable=True)
    build_global_search_index(registry)
    return manifest


def connected_components(mask: Image.Image, minimum: int) -> list[set[int]]:
    width, height = mask.size
    pixels = bytearray(1 if value else 0 for value in mask.getdata())
    result = []
    for index, value in enumerate(pixels):
        if value != 1:
            continue
        stack = [index]
        pixels[index] = 2
        component = set()
        while stack:
            current = stack.pop()
            component.add(current)
            x = current % width
            for neighbor in (current - 1, current + 1, current - width, current + width):
                if 0 <= neighbor < width * height and pixels[neighbor] == 1 and abs(neighbor % width - x) <= 1:
                    pixels[neighbor] = 2
                    stack.append(neighbor)
        if len(component) >= minimum:
            result.append(component)
    return result


def trace_component(component: set[int], width: int, height: int) -> list[tuple[int, int]]:
    start_index = min(component, key=lambda item: (item // width, item % width))
    start = (start_index % width, start_index // width)
    directions = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    point = start
    backtrack = (start[0] - 1, start[1])
    initial = (point, backtrack)
    outline = [point]
    for _ in range(width * height * 2):
        relative = (backtrack[0] - point[0], backtrack[1] - point[1])
        direction_index = directions.index(relative) if relative in directions else 4
        found = None
        for offset in range(1, 9):
            candidate_index = (direction_index + offset) % 8
            x = point[0] + directions[candidate_index][0]
            y = point[1] + directions[candidate_index][1]
            if 0 <= x < width and 0 <= y < height and y * width + x in component:
                previous = (direction_index + offset - 1) % 8
                backtrack = (point[0] + directions[previous][0], point[1] + directions[previous][1])
                found = (x, y)
                break
        if found is None:
            break
        point = found
        if (point, backtrack) == initial:
            break
        outline.append(point)
    return outline


def simplify(points: list[tuple[int, int]], tolerance: float) -> list[tuple[int, int]]:
    if len(points) < 3:
        return points
    start, end = points[0], points[-1]
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    denominator = math.hypot(dx, dy)
    distance = 0.0
    index = 0
    for offset, point in enumerate(points[1:-1], 1):
        if denominator == 0:
            current = math.hypot(point[0] - start[0], point[1] - start[1])
        else:
            current = abs(dy * point[0] - dx * point[1] + end[0] * start[1] - end[1] * start[0]) / denominator
        if current > distance:
            distance = current
            index = offset
    if distance > tolerance:
        return simplify(points[: index + 1], tolerance)[:-1] + simplify(points[index:], tolerance)
    return [start, end]


def build_zone_geojson(boundary_geometry: dict) -> dict:
    if not SOURCE_RENDER.exists():
        SOURCE_RENDER.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["pdftoppm", "-f", "1", "-singlefile", "-png", "-r", "150", str(SOURCE_PDF), str(SOURCE_RENDER.with_suffix(""))],
            check=True,
        )
    source = Image.open(SOURCE_RENDER).convert("RGB")
    left = int(source.width * 0.203)
    source = source.crop((left, 0, source.width, source.height))
    # Keep enough source-map resolution for street-scale status borders. The
    # former 1100 px working copy and broad morphology shifted visible edges by
    # several hundred metres at Berlin scale.
    source.thumbnail((1100, 1000), Image.LANCZOS)
    width, height = source.size
    source_pixels = source.load()
    features = []
    for zone_type, rule in ZONE_RULES.items():
        mask = Image.new("L", source.size, 0)
        mask_pixels = mask.load()
        for y in range(height):
            for x in range(width):
                if rule["test"](*source_pixels[x, y]):
                    mask_pixels[x, y] = 255
        if zone_type == "orange":
            # Preserve the street-scale outline of the small corporate zones.
            mask = (
                mask.filter(ImageFilter.MaxFilter(3))
                .filter(ImageFilter.MinFilter(3))
                .filter(ImageFilter.MaxFilter(3))
                .filter(ImageFilter.MinFilter(3))
            )
        else:
            # The city-wide fills contain many labels and road cut-outs that
            # must be closed before their outer edge can be traced.
            mask = (
                mask.filter(ImageFilter.MaxFilter(9))
                .filter(ImageFilter.MinFilter(9))
                .filter(ImageFilter.MaxFilter(5))
                .filter(ImageFilter.MinFilter(5))
            )
        allowed_components = {
            "magenta": {1},
            "grau": {2, 3},
            "orange": {1, 2, 3, 4},
            "tuerkis": set(),
        }
        for component_index, component in enumerate(connected_components(mask, rule["minimum"]), 1):
            if component_index not in allowed_components[zone_type]:
                continue
            outline = trace_component(component, width, height)
            outline = simplify(outline + [outline[0]], 1.0)
            coordinates = []
            for x, y in outline:
                x_percent = 20.3 + x / (width - 1) * 79.7
                y_percent = y / (height - 1) * 100
                lon_coeff = TRANSFORMS["overview"]["lon"]
                lat_coeff = TRANSFORMS["overview"]["lat"]
                lon = lon_coeff[0] * x_percent + lon_coeff[1] * y_percent + lon_coeff[2]
                lat = lat_coeff[0] * x_percent + lat_coeff[1] * y_percent + lat_coeff[2]
                coordinates.append([round(lon, 6), round(lat, 6)])
            if coordinates[0] != coordinates[-1]:
                coordinates.append(coordinates[0])
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [coordinates]},
                    "properties": {
                        "zone_type": zone_type,
                        "label": rule["label"],
                        "color": rule["color"],
                        "source": "Berlin 2080 Karte v04 - Übersicht",
                        "component": component_index,
                    },
                }
            )
    return {"type": "FeatureCollection", "name": "Shadowrun Berlin 2080 Gebietsflächen", "features": features}


def main() -> None:
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    catalog = json.loads(CATALOG.read_text(encoding="utf-8-sig"))
    description_payload = json.loads(DESCRIPTIONS.read_text(encoding="utf-8"))
    descriptions = {item["id"]: item for item in description_payload["descriptions"]}
    for entity_id, override in DESCRIPTION_OVERRIDES.items():
        full = override["full"]
        descriptions[entity_id] = {
            **descriptions[entity_id],
            "preview": district_preview(full),
            "full": full,
            "source": override["source"],
            "kind": "Quellenzusammenfassung",
            "has_more": len(full) > 165,
        }
    official_districts = json.loads(OFFICIAL_DISTRICTS.read_text(encoding="utf-8"))
    official_neighborhoods = json.loads(OFFICIAL_NEIGHBORHOODS.read_text(encoding="utf-8"))
    official_municipalities = json.loads(OFFICIAL_BRANDENBURG_MUNICIPALITIES.read_text(encoding="utf-8"))
    centered_districts = center_lore_districts(official_districts, official_neighborhoods)
    district_boundaries, neighborhood_boundaries = prepare_boundary_layers(official_districts, official_neighborhoods)
    centered_umland, umland_boundaries = prepare_umland_areas(official_municipalities)
    validate_additional_spots(catalog, centered_districts, centered_umland, CORPUS_SPOTS)
    CORPUS_SPOTS_JSON.write_text(
        json.dumps(
            {
                "name": "Zusätzliche eindeutige Orte aus dem Shadowrun-6D-Quellenkorpus",
                "deduplication": "Normalisierter Namensabgleich gegen Kartenlegende, Bezirke, Umland und Zusatzorte",
                "locations": CORPUS_SPOTS,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    DISTRICT_BOUNDARIES_GEOJSON.write_text(
        json.dumps(district_boundaries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    NEIGHBORHOOD_BOUNDARIES_GEOJSON.write_text(
        json.dumps(neighborhood_boundaries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    UMLAND_BOUNDARIES_GEOJSON.write_text(
        json.dumps(umland_boundaries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    boundary_source = json.loads(BOUNDARY_SOURCE.read_text(encoding="utf-8"))
    boundary_feature = boundary_source["features"][0]
    boundary = {
        "type": "FeatureCollection",
        "name": "Berlin Stadtgrenze",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Berlin", "source": "OpenStreetMap/Nominatim"},
                "geometry": boundary_feature["geometry"],
            }
        ],
    }
    BOUNDARY_GEOJSON.write_text(json.dumps(boundary, ensure_ascii=False, indent=2), encoding="utf-8")
    allowed_geometries = [boundary_feature["geometry"]] + [
        feature["geometry"] for feature in umland_boundaries["features"]
    ]
    scope = {
        "type": "FeatureCollection",
        "name": "Berlin und Lore-Umland",
        "features": boundary["features"] + umland_boundaries["features"],
    }
    # Keep every numbered location printed on the supplied v06 overview reachable,
    # including the outer Brandenburg markers beyond the named lore districts.
    region_bounds = [[52.2608, 12.8583], [52.8103, 13.9786]]
    geojson = build_geojson(catalog, allowed_geometries, descriptions)
    geojson["features"].extend(build_district_features(centered_districts))
    geojson["features"].extend(build_umland_features(centered_umland))
    geojson["features"].extend(build_corpus_features(CORPUS_SPOTS))
    GEOJSON.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")
    zones = build_zone_geojson(boundary_feature["geometry"])
    ZONES_GEOJSON.write_text(json.dumps(zones, ensure_ascii=False, indent=2), encoding="utf-8")
    area_status = reconcile_zone_topology(
        build_area_status(zones),
        district_boundaries,
        neighborhood_boundaries,
        umland_boundaries,
    )
    build_cropped_overlay()
    build_offline_base()
    detail_atlas = build_detail_atlas()
    entity_ids = {feature["properties"]["id"] for feature in geojson["features"]}
    person_ids = [person["id"] for person in PERSONS]
    if len(person_ids) != len(set(person_ids)):
        raise ValueError("Duplicate person IDs")
    for person in PERSONS:
        missing_locations = [link["id"] for link in person.get("locations", []) if link["id"] not in entity_ids]
        if missing_locations:
            raise KeyError(f"Missing location links for {person['name']}: {missing_locations}")

    payload = {
        "geojson": geojson,
        "zones": zones,
        "areaStatus": area_status,
        "corporateAreas": {
            "type": "FeatureCollection",
            "name": "Exterritoriale Konzerngebiete",
            "features": [
                {
                    **feature,
                    "properties": {
                        **feature["properties"],
                        "label": CORPORATE_COMPONENT_LABELS.get(
                            feature["properties"]["component"], feature["properties"]["label"]
                        ),
                        "color": "#f5f06a",
                    },
                }
                for feature in area_status["features"]
                if feature["properties"]["zone_type"] == "orange"
            ],
        },
        "districtBoundaries": district_boundaries,
        "neighborhoodBoundaries": neighborhood_boundaries,
        "umlandBoundaries": umland_boundaries,
        "boundary": boundary,
        "scope": scope,
        "atlas": detail_atlas,
        "persons": PERSONS,
        "loreLabels": [
            *[
                {"name": district["name"], "lat": district["lat"], "lon": district["lon"], "type": "district"}
                for district in centered_districts
            ],
            *[
                {"name": area["name"], "lat": area["lat"], "lon": area["lon"], "type": "outskirts"}
                for area in centered_umland
            ],
            {"name": "Z-IC Tegel", "lat": 52.5770, "lon": 13.3040, "type": "corporate"},
            {"name": "AGC Siemensstadt", "lat": 52.5480, "lon": 13.2760, "type": "corporate"},
            {"name": "S-K Tempelhof", "lat": 52.4540, "lon": 13.4050, "type": "corporate"},
            {"name": "Dreamland", "lat": 52.5570, "lon": 13.4480, "type": "special"},
            {"name": "Jevuhl", "lat": 52.5390, "lon": 13.2920, "type": "special"},
            {"name": "Westhafen", "lat": 52.5390, "lon": 13.3370, "type": "special"}
        ],
        "entities": (
            catalog["entities"]
            + district_entities(centered_districts)
            + umland_entities(centered_umland)
            + corpus_entities(CORPUS_SPOTS)
        ),
        "summary": catalog["summary"],
        "overlayBounds": [[52.2608, 12.8583], [52.8103, 13.9786]],
        "cityBounds": [[52.3382448, 13.088345], [52.6755087, 13.7611609]],
        "regionBounds": region_bounds,
    }
    enrich_payload_with_editions(payload)
    registry = update_city_registry()
    write_city_package(payload, registry)
    template = TEMPLATE.read_text(encoding="utf-8")
    hybrid_html = (
        template.replace("__MAP_DATA__", "null")
        .replace("__CITY_REGISTRY__", "null")
        .replace("__OFFLINE_BASE_URL__", json.dumps(""))
        .replace("__HYBRID_APP__", "true")
    )
    PWA_HTML.write_text(hybrid_html, encoding="utf-8")
    print(f"PWA HTML: {PWA_HTML} ({PWA_HTML.stat().st_size:,} bytes)")
    print(f"GeoJSON: {GEOJSON} ({len(geojson['features'])} placed locations)")
    print(f"Vector zones: {ZONES_GEOJSON} ({len(zones['features'])} polygons)")
    print(f"District boundaries: {DISTRICT_BOUNDARIES_GEOJSON} ({len(district_boundaries['features'])} features)")
    print(f"Neighborhood boundaries: {NEIGHBORHOOD_BOUNDARIES_GEOJSON} ({len(neighborhood_boundaries['features'])} features)")
    print(f"Lore outskirts: {UMLAND_BOUNDARIES_GEOJSON} ({len(umland_boundaries['features'])} features)")
    print(f"Additional corpus spots: {CORPUS_SPOTS_JSON} ({len(CORPUS_SPOTS)} locations)")
    print(f"Berlin boundary: {BOUNDARY_GEOJSON}")
    print(f"Reference overlay: {OVERLAY_SVG} ({OVERLAY_SVG.stat().st_size:,} bytes)")
    print(f"Offline raster base: {OFFLINE_BASE_WEBP} ({OFFLINE_BASE_WEBP.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
