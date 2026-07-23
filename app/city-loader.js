(() => {
  const asArray = value => Array.isArray(value) ? value : [];

  async function fetchJson(url) {
    const response = await fetch(url, { cache: 'no-cache' });
    if (!response.ok) throw new Error(`Stadtdatei konnte nicht geladen werden (${response.status}): ${url}`);
    return response.json();
  }

  function resolveCity(registry, requestedCityId) {
    const cities = asArray(registry && registry.cities);
    if (!cities.length) throw new Error('Das Stadtverzeichnis enthält keine Städte.');
    return cities.find(city => city.id === requestedCityId)
      || cities.find(city => city.default)
      || cities[0];
  }

  function featureCollection(name, features) {
    return { type: 'FeatureCollection', name, features };
  }

  function assembleData(manifest, packages) {
    const places = packages.places;
    const zones = packages.zones;
    const outskirts = packages.outskirts;
    const boundary = packages.boundary;
    const corporateFeatures = asArray(zones.features)
      .filter(feature => feature.properties && feature.properties.status === 'corporate')
      .map(feature => ({
        ...feature,
        properties: { ...feature.properties, color: '#f5f06a' },
      }));

    return {
      geojson: places,
      persons: asArray(packages.people),
      atlas: asArray(packages.atlas),
      areaStatus: zones,
      corporateAreas: featureCollection('Exterritoriale Konzerngebiete', corporateFeatures),
      districtBoundaries: packages.districts,
      neighborhoodBoundaries: packages.neighborhoods,
      umlandBoundaries: outskirts,
      boundary,
      scope: featureCollection(
        `${manifest.name} und Lore-Umland`,
        [...asArray(boundary.features), ...asArray(outskirts.features)],
      ),
      loreLabels: asArray(packages.labels),
      entities: asArray(places.features).map(feature => feature.properties),
      summary: manifest.summary || {},
      overlayBounds: manifest.overlayBounds,
      cityBounds: manifest.cityBounds,
      regionBounds: manifest.regionBounds,
    };
  }

  async function loadExternalPackage(city, manifestUrl) {
    const manifest = await fetchJson(manifestUrl);
    const requiredFiles = [
      'places', 'people', 'atlas', 'zones', 'districts',
      'neighborhoods', 'outskirts', 'boundary', 'labels',
    ];
    const fileUrls = Object.fromEntries(requiredFiles.map(key => {
      const relativePath = manifest.files && manifest.files[key];
      if (!relativePath) throw new Error(`Im Manifest von ${city.name} fehlt die Datei „${key}“.`);
      return [key, new URL(relativePath, manifestUrl).href];
    }));
    const entries = await Promise.all(requiredFiles.map(async key => [key, await fetchJson(fileUrls[key])]));
    const packages = Object.fromEntries(entries);
    packages.atlas = asArray(packages.atlas).map(plan => ({
      ...plan,
      image: /^data:/.test(plan.image || '') ? plan.image : new URL(plan.image, fileUrls.atlas).href,
    }));
    return {
      manifest,
      manifestUrl,
      data: assembleData(manifest, packages),
      offlineBase: manifest.assets && manifest.assets.offlineBase
        ? new URL(manifest.assets.offlineBase, manifestUrl).href
        : '',
    };
  }

  async function load(options = {}) {
    const registryUrl = new URL(options.registryUrl || 'data/cities.json', document.baseURI).href;
    const registry = options.embeddedRegistry || await fetchJson(registryUrl);
    const city = resolveCity(registry, options.requestedCityId);
    if (options.embeddedData) {
      return {
        registry,
        city,
        manifest: {
          id: city.id,
          name: city.name,
          year: city.year,
          regionBounds: options.embeddedData.regionBounds,
        },
        data: options.embeddedData,
        offlineBase: options.embeddedOfflineBase || '',
      };
    }
    const manifestUrl = new URL(city.manifest, document.baseURI).href;
    const cityPackage = await loadExternalPackage(city, manifestUrl);
    return { registry, city, ...cityPackage };
  }

  async function loadSearchIndex(url = 'data/search-index.json') {
    return fetchJson(new URL(url, document.baseURI).href);
  }

  window.SR6CityLoader = { load, loadSearchIndex };
})();
