(() => {
  const asArray = value => Array.isArray(value) ? value : [];
  const query = new URLSearchParams(window.location.search);
  const localDevelopment = query.get('dev') === '1'
    && ['127.0.0.1', 'localhost'].includes(window.location.hostname);
  const developmentRequestId = localDevelopment ? `${Date.now()}` : '';

  async function fetchJson(url) {
    const requestUrl = new URL(url, document.baseURI);
    if (developmentRequestId) requestUrl.searchParams.set('_dev', developmentRequestId);
    const response = await fetch(requestUrl, { cache: localDevelopment ? 'no-store' : 'no-cache' });
    if (!response.ok) throw new Error(`Stadtdatei konnte nicht geladen werden (${response.status}): ${requestUrl}`);
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

  function mergeUnique(first, second, key = value => JSON.stringify(value)) {
    const result = [];
    const seen = new Set();
    [...asArray(first), ...asArray(second)].forEach(value => {
      const signature = key(value);
      if (seen.has(signature)) return;
      seen.add(signature);
      result.push(value);
    });
    return result;
  }

  function mergeAugmentation(target, augmentation) {
    return {
      ...target,
      ...augmentation,
      id: target.id,
      global_id: target.global_id,
      aliases: mergeUnique(target.aliases, augmentation.aliases, value => value),
      editions: mergeUnique(target.editions, augmentation.editions, value => value),
      sources: mergeUnique(target.sources, augmentation.sources),
      map_sources: mergeUnique(target.map_sources, augmentation.map_sources),
      locations: mergeUnique(target.locations, augmentation.locations, value => `${value.id}:${value.relation}`),
      edition_descriptions: {
        ...(target.edition_descriptions || {}),
        ...(augmentation.edition_descriptions || {}),
      },
    };
  }

  function applyAugmentations(entries, augmentations, getId) {
    const byId = new Map(asArray(augmentations).map(item => [item.id, item]));
    return entries.map(entry => {
      const augmentation = byId.get(getId(entry));
      if (!augmentation) return entry;
      if (entry.properties) {
        return { ...entry, properties: mergeAugmentation(entry.properties, augmentation) };
      }
      return mergeAugmentation(entry, augmentation);
    });
  }

  function assembleData(manifest, packages) {
    const rawPlaces = [
      ...asArray(packages.places.features),
      ...asArray(packages.virtualPlaces && packages.virtualPlaces.features),
      ...asArray(packages.historicalPlaces && packages.historicalPlaces.features),
    ];
    const places = featureCollection(
      packages.places.name || `${manifest.name} Orte`,
      applyAugmentations(rawPlaces, packages.placeAugmentations, feature => feature.properties.id),
    );
    const people = applyAugmentations(
      [...asArray(packages.people), ...asArray(packages.historicalPeople)],
      packages.personAugmentations,
      person => person.id,
    );
    const zones = packages.zones;
    const exterritorial = packages.exterritorial || zones;
    const outskirts = packages.outskirts;
    const boundary = packages.boundary;
    const statusFeatures = asArray(zones.features)
      .filter(feature => ['normal', 'anarcho'].includes(feature.properties && feature.properties.status));
    const corporateFeatures = asArray(exterritorial.features)
      .filter(feature => feature.properties && feature.properties.status === 'corporate')
      .map(feature => ({
        ...feature,
        properties: { ...feature.properties, color: '#f5f06a' },
      }));

    return {
      geojson: places,
      persons: people,
      availableEditions: asArray(manifest.availableEditions),
      atlas: asArray(packages.atlas),
      areaStatus: featureCollection(zones.name || 'Gebietsstatus', statusFeatures),
      corporateAreas: featureCollection(exterritorial.name || 'Exterritoriale Konzerngebiete', corporateFeatures),
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
      'places', 'people', 'atlas', 'zones', 'exterritorial', 'districts',
      'neighborhoods', 'outskirts', 'boundary', 'labels',
    ];
    const fileUrls = Object.fromEntries(requiredFiles.map(key => {
      const relativePath = manifest.files && manifest.files[key];
      if (!relativePath) throw new Error(`Im Manifest von ${city.name} fehlt die Datei „${key}“.`);
      return [key, new URL(relativePath, manifestUrl).href];
    }));
    const entries = await Promise.all(requiredFiles.map(async key => [key, await fetchJson(fileUrls[key])]));
    const packages = Object.fromEntries(entries);
    for (const key of ['virtualPlaces', 'historicalPlaces', 'historicalPeople', 'placeAugmentations', 'personAugmentations']) {
      if (!manifest.files || !manifest.files[key]) continue;
      packages[key] = await fetchJson(new URL(manifest.files[key], manifestUrl).href);
    }
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
