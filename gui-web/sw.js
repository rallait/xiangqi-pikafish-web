/* 中国象棋 PWA Service Worker v2
   静态资源 cache-first，HTML 永远 network-first（拿到最新前端代码），API network-only */
const CACHE = "xq-v2";
const ASSETS = ["/manifest.json", "/sw.js", "/icon-192.png", "/icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;                 // POST 直接放行
  if (url.origin !== location.origin) return;             // 跨域不接管
  // HTML 永远拿最新（前端代码常改）
  if (url.pathname === "/" || url.pathname === "/index.html" || url.pathname === "/index-en.html") {
    e.respondWith(
      fetch(e.request).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return res;
      }).catch(() => caches.match(e.request))
    );
    return;
  }
  if (url.pathname === "/health") return;                 // 健康检查始终走网络
  // 其他静态资源 cache-first
  e.respondWith(
    caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
      }
      return res;
    }))
  );
});
