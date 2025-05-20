const CACHE_NAME = "flask-pwa-cache-v1";
const URLS_TO_CACHE = [
  "/",                // index.html (루트 URL)
  "/player",          // player.html (라우트 기반 접근)
  "/static/style.css", // 공통 스타일 예시
  "/static/icon-192.png",
  "/static/icon-512.png"
];

// 설치: 캐시 저장
self.addEventListener("install", event => {
  console.log("[ServiceWorker] 설치 완료");
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(URLS_TO_CACHE);
    })
  );
});

// 요청: 캐시 → 네트워크
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});

// 캐시 정리 (선택적)
self.addEventListener("activate", event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(keyList =>
      Promise.all(
        keyList.map(key => {
          if (!cacheWhitelist.includes(key)) {
            return caches.delete(key);
          }
        })
      )
    )
  );
});
