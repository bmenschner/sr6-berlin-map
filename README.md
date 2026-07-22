# Shadowrun Berlin 2080 – interaktive Karte

Die veröffentlichte Hybrid-PWA ist unter **[bmenschner.github.io/sr6-berlin-map](https://bmenschner.github.io/sr6-berlin-map/)** erreichbar. Das Repository enthält drei Ausgaben derselben interaktiven Berlin-Karte:

- `index.html` – Hauptanwendung für GitHub Pages und installierbare Hybrid-PWA. Sie verwendet online die vollständigen Straßenkarten und wechselt manuell oder bei Verbindungsabbruch auf die eingebettete Offline-Kartenbasis.
- `shadowrun-berlin-2080-karte.html` – Online-Version mit OpenStreetMap, einer kontrastreichen CARTO-Straßennamenebene und der amtlichen Berlin-Karte ÜK50. Die benötigte Leaflet-Bibliothek liegt unter `output/map/vendor/`.
- `shadowrun-berlin-2080-karte-offline.html` – transportable Einzeldatei mit eingebetteter Kartenbibliothek, Markern, Beschreibungen, Grenzen und einer für flüssiges Zoomen optimierten Shadowrun-Kartenbasis. OSM und ÜK50 bleiben optionale Online-Ebenen.

Alle drei Dateien können direkt im Browser geöffnet werden. Für die Offline-Version werden keine weiteren lokalen Dateien benötigt. PWA-Installation, Service Worker und automatische Updates funktionieren aus Sicherheitsgründen nur über die HTTPS-Adresse oder einen lokalen Webserver, nicht über `file://`.

Über **„Online / Offline“** in der oberen Menüleiste wird die Kartenbasis ohne Seitenwechsel umgeschaltet. Online stehen OSM, die verstärkte CARTO-Beschriftung und ÜK50 zur Verfügung. Offline werden alle externen Kartenebenen entfernt und die eingebettete Shadowrun-Übersicht aktiviert; Zoom, Kartenposition, Auswahl, Marker, Personen, Suche, Grenzen und Detailkarten bleiben erhalten. Eine manuelle Offlinewahl wird gespeichert. Bricht bei gewähltem Onlinemodus die Verbindung ab, schaltet die App vorübergehend offline und kehrt nach Wiederherstellung automatisch online zurück.

Über **„App installieren“** lässt sich die GitHub-Pages-Ausgabe in unterstützten Browsern als eigenständige Anwendung installieren. Chromium-Browser öffnen den nativen Installationsdialog; auf iPhone und iPad zeigt die Karte die passende Home-Bildschirm-Anleitung. Der Service Worker speichert ausschließlich die Anwendung, ihre eingebettete Kartenbasis und die App-Symbole. Externe OSM-, CARTO- und ÜK50-Kacheln werden nicht für Offlinegebiete vorgeladen. Sobald eine neue App-Version bereitsteht, erscheint ein kontrollierter Aktualisierungshinweis.

Über **„Light / Dark“** in der oberen Menüleiste lässt sich die gesamte Oberfläche umschalten. Der Lightmode übernimmt die helle Papier-, Magenta-, Anthrazit-, Türkis- und Orange-Palette der Berlin-2080-Karten v06; der gewählte Modus bleibt beim nächsten Öffnen erhalten. Marker, Gebietsstatus, exterritoriale Flächen sowie die einzeln aktivierbaren Bezirks-, Stadtteil-, Umland- und Stadtgrenzen wechseln auf abgestimmte kontrastreiche Farben, ohne ihre Ebenenfunktion zu verlieren.

Mit **„Orte / Personen“** wechselt die Seitenleiste zwischen dem Standortkatalog und 27 kuratierten Berliner Persönlichkeiten. Die Personen-Dossiers enthalten Rolle, Zugehörigkeit, Quellenbeleg und – soweit eindeutig belegt – Verknüpfungen zu bestehenden Orten oder Bezirken. 26 Personen besitzen solche Bezüge; Nakaira wird bewusst nur als berlinweit geführt, ohne einen erfundenen Kartenpunkt. Die optionale Ebene **„Personenbezüge“** hebt verknüpfte bestehende Marker hervor und erzeugt keine zusätzlichen Standortmarker.

Die Suche arbeitet unabhängig vom gewählten Umschalter und durchsucht immer Orte und Personen gemeinsam. Sie berücksichtigt unter anderem Namen, Aliasse, Beschreibungen, Rollen, Zugehörigkeiten, Quellen und Seitenangaben und gruppiert die Treffer nach **„Orte“** und **„Personen“**. Dadurch findet beispielsweise eine Personensuche auch den zugeordneten Ort. Personen lassen sich über `?person=schluessel` direkt öffnen, zum Beispiel `?person=nakaira`.

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
