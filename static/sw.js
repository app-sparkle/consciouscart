const CACHE_NAME = "consciouscart-v1";
const STATIC_ASSETS = ["/static/css/main.css", "/static/js/app.js", "/static/js/geo.js"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS)));
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});