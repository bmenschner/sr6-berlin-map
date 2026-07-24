# Shadowrun-Stadtkarten – interaktive PWA

Die veröffentlichte Hybrid-PWA ist unter **[bmenschner.github.io/sr6-berlin-map](https://bmenschner.github.io/sr6-berlin-map/)** erreichbar. Die Anwendung ist für mehrere Shadowrun-Städte vorbereitet; Berlin 2080 ist das erste vollständige Stadtpaket.

`index.html` ist die einzige reguläre Anwendung für GitHub Pages und die installierbare Hybrid-PWA. Sie lädt nur das gewählte Stadtpaket und speichert es anschließend für den Offlinebetrieb.

Die modulare PWA wird über die HTTPS-Adresse oder einen lokalen Webserver geöffnet, weil Browser externe JSON-Stadtpakete unter `file://` blockieren können. PWA-Installation, Service Worker und automatische Updates funktionieren nur über HTTPS oder einen lokalen Webserver. Für die Offline-Nutzung muss die Webapp mindestens einmal vollständig online geladen worden sein.

Für die lokale Vorschau genügt unter Windows ein Doppelklick auf `Karte-lokal-starten.cmd`. Das Startsymbol verwendet die vorhandene Ubuntu-WSL-Umgebung, startet den Kartenserver unter `http://127.0.0.1:8765/?dev=1` und öffnet die Karte automatisch im Standardbrowser. Der lokale Entwicklungsmodus umgeht alte PWA-Daten, deaktiviert für diese Vorschau den Service Worker und lädt die Stadtdateien immer direkt aus dem Projektordner. Läuft genau dieser Kartenserver bereits, wird nur die Karte geöffnet. Zum Beenden wird das minimierte Fenster **„Shadowrun Kartenserver“** geschlossen.

Über **„Online / Offline“** in der oberen Menüleiste wird die Kartenbasis ohne Seitenwechsel umgeschaltet. Online stehen OSM, die verstärkte CARTO-Beschriftung und ÜK50 zur Verfügung. Offline werden alle externen Kartenebenen entfernt und die eingebettete Shadowrun-Übersicht aktiviert; Zoom, Kartenposition, Auswahl, Marker, Personen, Suche, Grenzen und Detailkarten bleiben erhalten. Eine manuelle Offlinewahl wird gespeichert. Bricht bei gewähltem Onlinemodus die Verbindung ab, schaltet die App vorübergehend offline und kehrt nach Wiederherstellung automatisch online zurück.

Über **„App installieren“** lässt sich die GitHub-Pages-Ausgabe in unterstützten Browsern als eigenständige Anwendung installieren. Chromium-Browser öffnen den nativen Installationsdialog; auf iPhone und iPad zeigt die Karte die passende Home-Bildschirm-Anleitung. Der Service Worker trennt Anwendung, Laufzeitdaten und versionierte Stadtpakete. Für die gewählte Stadt werden Manifest, Orte, Personen, Grenzen, Beschriftungen und Offline-Kartenbasis gespeichert. Externe OSM-, CARTO- und ÜK50-Kacheln werden nicht für Offlinegebiete vorgeladen. Sobald eine neue App-Version bereitsteht, erscheint ein kontrollierter Aktualisierungshinweis.

Über **„Light / Dark“** in der oberen Menüleiste lässt sich die gesamte Oberfläche umschalten. Der Lightmode übernimmt die helle Papier-, Magenta-, Anthrazit-, Türkis- und Orange-Palette der Berlin-2080-Karten v06; der gewählte Modus bleibt beim nächsten Öffnen erhalten. Marker, Gebietsstatus, exterritoriale Flächen sowie die einzeln aktivierbaren Bezirks-, Stadtteil-, Umland- und Stadtgrenzen wechseln auf abgestimmte kontrastreiche Farben, ohne ihre Ebenenfunktion zu verlieren.

Mit **„Orte / Personen“** wechselt die Seitenleiste zwischen dem Standortkatalog und derzeit 84 Berliner Persönlichkeiten sowie 72 Gangdossiers. Die Kategorie **„Gangs“** führt die Gruppen mit Typ, Größe, Gefahrenstufe, Editionsbeschreibung und Quelle. Historische Gangbeschreibungen aus der gemeinsamen SR1/SR2-Veröffentlichung und aus SR5 werden im selben Dossier über die Editionsschalter neben dem aktuellen SR6-Stand angeboten. Personen und Gruppen werden – soweit eindeutig belegt – mit bestehenden physischen oder virtuellen Orten und Stadtgebieten verbunden. Die optionale Ebene **„Personenbezüge“** hebt diese verknüpften Marker hervor und erzeugt keine zusätzlichen Standortmarker.

Die Suche arbeitet unabhängig vom gewählten Umschalter und durchsucht immer Orte und Personen gemeinsam. Der globale Suchindex ist stadtübergreifend: Ein Treffer aus einer anderen Stadt wechselt beim Öffnen automatisch in deren Stadtpaket. Direktlinks enthalten deshalb optional die Stadt, zum Beispiel `?city=berlin-2080&person=nakaira`.

Im Ebenenmenü lassen sich die vorhandenen Spielversionen **SR3**, **SR4**, **SR5** und **SR6** getrennt ein- und ausblenden. Ein Ort oder eine Person, der beziehungsweise die in mehreren Editionen vorkommt, bleibt dabei ein gemeinsamer Listeneintrag und ein gemeinsamer Marker. Die Ebenen bestimmen nur die normale Karten- und Listenansicht; die Suche bleibt bewusst vollständig und macht auch einen Treffer aus einer ausgeblendeten Edition vorübergehend sichtbar.

In den Detailkarten stehen bei mehreren vorhandenen Editionen direkt über dem Quellenauszug Umschaltflächen wie **SR3 / SR4 / SR5 / SR6** bereit. Quellenangaben tragen die zugehörige Edition in Klammern. Wo eine Edition einen Eintrag zwar belegt, aber noch kein eigener Auszug hinterlegt ist, zeigt die Karte einen gekennzeichneten Quellennachweis statt einen Text aus einer anderen Edition als editionsspezifisch auszugeben.

## Quellenbasis

Für die Recherche stehen offizielle PDFs und durchsuchbare TXT-Exporte der Editionen SR1 bis SR6 zur Verfügung. Ergänzende Informationen aus Shadowhelix werden immer als externe Quelle gekennzeichnet. Die vollständige Quellenrangfolge und die verbindlichen Kennzeichnungsregeln stehen in [SOURCES.md](SOURCES.md).

## Einheitliche Begriffe

- **Datenmaterial/Quellen** umfasst sämtliche vermerkten offiziellen PDFs, TXT-Extrakte und eindeutig gekennzeichneten externen Informationen aus Shadowhelix.
- **Orte** umfasst alle Kategorien von Karteneinträgen und geografischen Inhalten.
- **Personen** umfasst alle Personengruppen und personenbezogenen Einträge.

Diese Oberbegriffe werden einheitlich in der Projektdokumentation und bei der weiteren Bearbeitung verwendet.

## Mehrstadt-Architektur

`data/cities.json` ist das Stadtverzeichnis. Jede Stadt besitzt unter `data/STADT-ID/` ein eigenes Manifest sowie getrennte Dateien für Orte, Personen, Detailkarten, Gebietsstatus, Bezirke, Stadtteile, Umland, Stadtgrenze, Beschriftungen und Quellen. Schwere Bilder liegen unter `assets/cities/STADT-ID/` und werden nur bei Bedarf geladen. Die Online-PWA hält dadurch keine Stadtgeometrien mehr direkt in `index.html`.

Ein neues Stadtpaket wird in dieser Reihenfolge ergänzt:

1. Stadt in `data/cities.json` registrieren.
2. `manifest.json` mit Kartenmittelpunkt, Zoom, Grenzen und Dateiverweisen anlegen.
3. Orte als GeoJSON und Personen als JSON hinzufügen.
4. Bezirks-, Stadtteil-, Gebiets- und Umlandgrenzen ergänzen.
5. Offline-Kartenbasis und optionale Detailkarten unter `assets/cities/` ablegen.
6. Globalen Suchindex neu erzeugen und `tools/validate_city_data.py` ausführen.

Alle Orts- und Personenobjekte besitzen zusätzlich zu ihren bisherigen IDs eine stadtweit stabile `global_id`. Personenverknüpfungen werden beim Erzeugen gegen vorhandene Orte geprüft. Der Validator verhindert doppelte IDs, ungültige Koordinaten, fehlende Dateien und nicht auflösbare Personenbezüge.

Der Berlin-Generator erzeugt aus einer Datenbasis das modulare Stadtpaket und die PWA-Einstiegsseite. Quellen werden dabei einem Editionskatalog zugeordnet; Orte und Personen erhalten strukturierte Quellen, Spielversionen und editionsweise Beschreibungen. Neue Städte benötigen keine Änderungen am Kartenlader oder an der Stadtwahl.

Die Gebietsflächen bilden eine überschneidungsfreie Partition mit der verbindlichen Reihenfolge `EXTER > Anarcho > Normal`. **EXTER** liegt zusätzlich als eigenständiger, harter Layer in `exterritorial.geojson`; Anarcho- und Normalflächen folgen vollständig den Lore-Bezirks- und Umlandgrenzen und werden anschließend um die EXTER-Flächen beschnitten. Alle drei Gebietsarten sind in der Ebenenauswahl einzeln schaltbar und beim Start aktiviert. Straßen, Autobahnen und Bahntrassen werden im Zweifel vollständig dem Konzerngebiet zugeschlagen, die Grenze verläuft also an der konzernabgewandten Außenkante. Flughafenflächen erhalten zusätzlich eine plausible Sicherheitszone bis zur nächsten verteidigbaren Barriere.

Renrakusan und Z-IC Tegel sind nach diesem Verfahren geprüft. Renrakusan basiert auf dem früheren Ortsteil Prenzlauer Berg mit seinen durch ÜK50 und Lore belegten Grenzkorridoren, darunter Ringbahn/A100, Bornholmer Straße, Wisbyer Straße und Ostseestraße. Die amtliche Grundgeometrie wird defensiv nach außen erweitert, damit angrenzende Straßen- und Bahnflächen vollständig zum Konzerngebiet gehören. Bei Z-IC Tegel folgen Flughafen und Verkehrskorridore Bernauer Straße, A111 und Kurt-Schumacher-Damm; der gesamte Tegeler See einschließlich Großem Malchsee wird beansprucht, während Alt-Tegel an der tatsächlichen Außenkante des Tegeler Forsts endet. Nur an der Dicken Marie liegt eine kleine, quellenbelegte Sicherheitszone im Wald. AGC Siemensstadt, S-K Tempelhof und AZT Schönwalde bleiben bis zu ihrem jeweiligen Detailabgleich ausdrücklich als vorläufig gekennzeichnet. Für einen vollständigen Neuaufbau benötigt `tools/reconcile_zone_topology.py` die Python-Bibliothek `shapely`.

Über **„Detailkarten“** öffnet sich ein eingebettetes, zoombares Kartenarchiv mit:

- zehn Orts-, Gebäude- und Kiezplänen (Babylon, Hauergasse, Kasbah, Kellerclubs, Osramhöfe, Schrapnell, Emma-Goldman-Schulkiez, Spreeland Funpark, Blauer Engel und Vesuv),
- dem Bezirksplan von Renrakusan,
- dem Liniennetzplan der Berliner Magnetschwebebahnen,
- zwei hochauflösenden Berlin-Referenzkarten v06.

Zugehörige Ortspläne sind zusätzlich direkt am jeweiligen Marker verlinkt. Die allgemeine Kellerclub-Karte sowie Netz- und Referenzkarten liegen nur im Kartenarchiv, damit keine künstlichen oder doppelten Standortmarker entstehen. Ein bestimmter Plan kann auch über `?atlas=schluessel` geöffnet werden, zum Beispiel `?atlas=hauergasse`.

Der Standortkatalog enthält sämtliche nummerierten Einträge 001–430 der v06-Übersichts- und Detailkarten. Die 42 Einträge der Renrakusan-Einzelkarte wurden mit deren genaueren Positionen verknüpft; das zuvor fehlende Otogibanshi-Viertel (S9) ist ergänzt. Wiederholte Filialen der Kanagawa Komfort Hotels werden als fünf Kartenmarker unter einem gemeinsamen Listeneintrag dargestellt. Die alphabetische Seitenleiste zeigt den vollständigen Katalog ohne frühere Begrenzung auf 180 Zeilen. Einzelne Einträge lassen sich über `?marker=ID` direkt öffnen, beispielsweise `?marker=168`.

Für die Beschreibungen wurde der vollständige bereitgestellte SR6-Textkorpus mit 125 Dateien abgeglichen. 19 zuvor reine Kartenangaben besitzen nun redaktionell zusammengefasste Quellenbeschreibungen mit Buch- und Seitenverweis, darunter acht Renrakusan-Orte sowie weitere v06-Marker wie Goldstein, Juanita’s, das Bundeswehrkrankenhaus Berlin-Oranienburg und das Z-IC-Forschungsklinikum. Kartenangaben ohne eindeutig zuordenbaren Fließtext bleiben bewusst als solche gekennzeichnet.

## Hinweise

Dies ist ein inoffizielles, nichtkommerzielles Fanprojekt. Shadowrun und zugehörige Bezeichnungen sowie Inhalte der verwendeten Quellenbücher verbleiben bei den jeweiligen Rechteinhabern. Kartengrundlagen und Grenzdaten werden in der Anwendung den jeweiligen Anbietern zugeordnet, darunter OpenStreetMap-Mitwirkende, Geoportal Berlin und GeoBasis-DE/LGB.
