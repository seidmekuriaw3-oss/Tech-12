// Kill-switch service worker: unregisters itself and clears all caches.
// This ensures no old/broken SW intercepts fetch requests.

self.addEventListener('install', event => {
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(keys.map(k => caches.delete(k))))
            .then(() => self.registration.unregister())
            .then(() => self.clients.matchAll())
            .then(clients => clients.forEach(client => {
                if (client.url && 'navigate' in client) {
                    // Don't force reload — just let the page continue naturally
                }
            }))
    );
});

// Pass everything straight through — no caching, no interception.
self.addEventListener('fetch', event => {
    event.respondWith(fetch(event.request));
});
