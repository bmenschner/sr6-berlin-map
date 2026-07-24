const APP_CACHE = 'sr6-app-v16';
const RUNTIME_CACHE = 'sr6-runtime-v16';
const APP_ENTRY = new URL('./index.html', self.registration.scope).href;
const APP_SHELL = [
  './index.html',
  './app/city-loader.js',
  './data/cities.json',
  './data/search-index.json',
  './manifest.webmanifest',
  './output/map/vendor/leaflet.css',
  './output/map/vendor/leaflet.js',
  './output/map/vendor/images/layers.png',
  './output/map/vendor/images/layers-2x.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png'
];

async function cacheCityPackage(manifestUrl) {
  const manifestResponse = await fetch(manifestUrl, { cache: 'no-cache' });
  if (!manifestResponse.ok) throw new Error(`Stadtmanifest nicht erreichbar: ${manifestResponse.status}`);
  const manifest = await manifestResponse.clone().json();
  const cacheName = `sr6-city-${manifest.id}-v${manifest.dataVersion}`;
  const cityCache = await caches.open(cacheName);
  const fileUrls = Object.values(manifest.files || {}).map(path => new URL(path, manifestUrl).href);
  const assetUrls = manifest.assets && manifest.assets.offlineBase
    ? [new URL(manifest.assets.offlineBase, manifestUrl).href]
    : [];
  await cityCache.put(manifestUrl, manifestResponse);
  await cityCache.addAll([...fileUrls, ...assetUrls]);
  const cityPrefix = `sr6-city-${manifest.id}-v`;
  const keys = await caches.keys();
  await Promise.all(keys.filter(key => key.startsWith(cityPrefix) && key !== cacheName).map(key => caches.delete(key)));
  return cacheName;
}

self.addEventListener('install', event => {
  event.waitUntil(caches.open(APP_CACHE).then(cache => cache.addAll(APP_SHELL)));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => (
        (key.startsWith('sr6-app-') && key !== APP_CACHE)
        || (key.startsWith('sr6-runtime-') && key !== RUNTIME_CACHE)
        || key.startsWith('sr6-berlin-2080-')
      )).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
  if (event.data && event.data.type === 'CACHE_CITY' && event.data.manifestUrl) {
    event.waitUntil(cacheCityPackage(event.data.manifestUrl));
  }
});

self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then(response => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(APP_CACHE).then(cache => cache.put(APP_ENTRY, copy));
          }
          return response;
        })
        .catch(() => caches.match(APP_ENTRY))
    );
    return;
  }

  if (url.origin !== self.location.origin || request.method !== 'GET') return;

  if (url.pathname.includes('/data/')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          if (response.ok) caches.open(RUNTIME_CACHE).then(cache => cache.put(request, response.clone()));
          return response;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  event.respondWith(
    caches.match(request).then(cached => {
      const network = fetch(request)
        .then(response => {
          if (response.ok) caches.open(RUNTIME_CACHE).then(cache => cache.put(request, response.clone()));
          return response;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
