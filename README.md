# Shadowrun Berlin 2080 – interaktive Karte

Dieses Repository enthält zwei Ausgaben derselben interaktiven Berlin-Karte:

- `shadowrun-berlin-2080-karte.html` – Online-Version mit OpenStreetMap, einer kontrastreichen CARTO-Straßennamenebene und der amtlichen Berlin-Karte ÜK50. Die benötigte Leaflet-Bibliothek liegt unter `output/map/vendor/`.
- `shadowrun-berlin-2080-karte-offline.html` – transportable Einzeldatei mit eingebetteter Kartenbibliothek, Markern, Beschreibungen, Grenzen und einer für flüssiges Zoomen optimierten Shadowrun-Kartenbasis. OSM und ÜK50 bleiben optionale Online-Ebenen.

Beide Dateien können direkt im Browser geöffnet werden. Für die Offline-Version werden keine weiteren lokalen Dateien benötigt.

Über **„Detailkarten“** öffnet sich ein eingebettetes, zoombares Kartenarchiv mit:

- zehn Orts-, Gebäude- und Kiezplänen (Babylon, Hauergasse, Kasbah, Kellerclubs, Osramhöfe, Schrapnell, Emma-Goldman-Schulkiez, Spreeland Funpark, Blauer Engel und Vesuv),
- dem Bezirksplan von Renrakusan,
- dem Liniennetzplan der Berliner Magnetschwebebahnen,
- zwei hochauflösenden Berlin-Referenzkarten v06.

Zugehörige Ortspläne sind zusätzlich direkt am jeweiligen Marker verlinkt. Die allgemeine Kellerclub-Karte sowie Netz- und Referenzkarten liegen nur im Kartenarchiv, damit keine künstlichen oder doppelten Standortmarker entstehen. Ein bestimmter Plan kann auch über `?atlas=schluessel` geöffnet werden, zum Beispiel `?atlas=hauergasse`.

## Hinweise

Dies ist ein inoffizielles, nichtkommerzielles Fanprojekt. Shadowrun und zugehörige Bezeichnungen sowie Inhalte der verwendeten Quellenbücher verbleiben bei den jeweiligen Rechteinhabern. Kartengrundlagen und Grenzdaten werden in der Anwendung den jeweiligen Anbietern zugeordnet, darunter OpenStreetMap-Mitwirkende, Geoportal Berlin und GeoBasis-DE/LGB.
