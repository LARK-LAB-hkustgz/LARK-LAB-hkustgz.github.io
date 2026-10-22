/* Cache only content-versioned original images. HTML always uses the network. */
"use strict";
const CACHE = "lark-original-images-v1";
const MAX_ENTRIES = 128;
const inFlight = new Map();

self.addEventListener("install", event => {
  event.waitUntil(self.skipWaiting());
});
self.addEventListener("activate", event => {
  event.waitUntil(self.clients.claim());
});

async function remember(request, response) {
  try {
    const cache = await caches.open(CACHE);
    // Remove older content versions of this image; do not let the cache grow forever.
    const url = new URL(request.url);
    for (const key of await cache.keys()) {
      if (new URL(key.url).pathname === url.pathname && key.url !== request.url) {
        await cache.delete(key);
      }
    }
    await cache.put(request, response);
    const keys = await cache.keys();
    for (const key of keys.slice(0, Math.max(0, keys.length - MAX_ENTRIES))) {
      await cache.delete(key);
    }
  } catch (_) {
    // Storage disabled/full must not prevent the original image from displaying.
  }
}

self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin ||
      !url.searchParams.has("v") ||
      !(url.pathname.startsWith("/assets/images/") || url.pathname.startsWith("/blog/")) ||
      !/\.(png|jpe?g|webp|gif|avif)$/i.test(url.pathname)) return;
  event.respondWith((async () => {
    try {
      const cached = await caches.match(request, {cacheName: CACHE});
      if (cached) return cached;
    } catch (_) { /* Fall back to the browser's normal HTTP cache. */ }
    let pending = inFlight.get(request.url);
    if (!pending) {
      pending = fetch(request);
      inFlight.set(request.url, pending);
      pending.finally(() => inFlight.delete(request.url)).catch(() => {});
    }
    const response = (await pending).clone();
    if (response.ok && response.headers.get("Content-Type")?.startsWith("image/")) {
      event.waitUntil(remember(request, response.clone()));
    }
    return response;
  })());
});
