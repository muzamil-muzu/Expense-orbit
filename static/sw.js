const CACHE_NAME = 'expenseorbit-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/style.css',
  '/static/manifest.json',
  'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        // Use catch so it doesn't fail if 3rd party assets block
        return cache.addAll(ASSETS_TO_CACHE).catch(err => console.log('Cache addAll error', err));
      })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

self.addEventListener('fetch', (event) => {
  // Only handle GET requests
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached response or fetch from network
        return response || fetch(event.request).catch(() => {
            // Basic offline fallback for navigation requests
            if (event.request.mode === 'navigate') {
                return new Response(`
                    <div style="font-family: sans-serif; padding: 20px; text-align: center; color: white; background: #0f172a; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                        <h2>You are offline</h2>
                        <p>Reconnect to the internet to access ExpenseOrbit.</p>
                    </div>
                `, {
                    headers: { 'Content-Type': 'text/html' }
                });
            }
        });
      })
  );
});
