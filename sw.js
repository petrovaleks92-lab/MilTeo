const CACHE = 'milteo-v5';
const SHELL = ['./', 'index.html', 'i18n.js', 'manifest.json', 'icon-192.png', 'icon-512.png', 'badge-96.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Netzwerk zuerst, bei fehlender Verbindung die gespeicherte Seite
self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(
    fetch(e.request, { cache: 'no-cache' }).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
      return res;
    }).catch(() => caches.match(e.request).then(r => r || caches.match('index.html')))
  );
});

// Push-Mitteilungen vom Server (Timer, Termine, Chat)
self.addEventListener('push', (e) => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (_) {}
  e.waitUntil(self.registration.showNotification(d.title || 'Milteo', {
    body: d.body || '',
    icon: 'icon-192.png',      // grosses App-Logo in der Mitteilung
    badge: 'badge-96.png',     // einfarbiges Symbol für die Statusleiste (Android färbt es selbst)
    tag: d.tag || undefined,
    renotify: !!d.tag,
    vibrate: [250, 120, 250],
    data: { url: d.url || './' },
  }));
});

self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || './';
  e.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
      for (const c of list) {
        if ('focus' in c) { c.postMessage({ type: 'open', url }); return c.focus(); }
      }
      return clients.openWindow(new URL(url, self.registration.scope).href);
    })
  );
});
