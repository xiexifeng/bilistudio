// BiliStudio Service Worker — 离线支持
// 缓存策略：
//   1. 前端壳（HTML/JS/CSS）→ 安装时预缓存，先缓存后网络
//   2. API 响应（收藏/用户）→ 运行时缓存，网络优先，离线降级
//   3. 图片（封面代理）→ 运行时缓存，缓存优先

const CACHE_SHELL = 'bilistudio-shell-v2'
const CACHE_API = 'bilistudio-api-v2'
const CACHE_IMAGE = 'bilistudio-image-v2'

// 安装时预缓存的静态资源
const SHELL_FILES = [
  '/',
  '/index.html',
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_SHELL).then((cache) => {
      return cache.addAll(SHELL_FILES).catch(() => {})
    })
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k.startsWith('bilistudio-') && k !== CACHE_SHELL && k !== CACHE_API && k !== CACHE_IMAGE)
          .map((k) => caches.delete(k))
      )
    })
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url)

  // API 请求：网络优先，失败时用缓存（提供离线数据）
  if (url.pathname.startsWith('/api/collection') || url.pathname.startsWith('/api/users') || url.pathname.startsWith('/api/stats') || url.pathname.startsWith('/api/courses')) {
    event.respondWith(networkFirst(event.request, CACHE_API))
    return
  }

  // 图片代理：缓存优先（封面图片不经常变化）
  if (url.pathname.startsWith('/api/bilibili/proxy/image')) {
    event.respondWith(cacheFirst(event.request, CACHE_IMAGE))
    return
  }

  // 前端静态资源：缓存优先
  if (event.request.destination === 'script' || event.request.destination === 'style' || event.request.destination === 'font') {
    event.respondWith(cacheFirst(event.request, CACHE_SHELL))
    return
  }

  // HTML 导航请求：网络优先
  if (event.request.mode === 'navigate') {
    event.respondWith(networkFirst(event.request, CACHE_SHELL))
    return
  }
})

// 网络优先策略
async function networkFirst(request, cacheName) {
  const isSafeToCache = request.method === 'GET'
  try {
    const response = await fetch(request)
    if (response.ok && isSafeToCache) {
      const cache = await caches.open(cacheName)
      cache.put(request, response.clone())
    }
    if (response.ok || !isSafeToCache) {
      return response
    }
    // 网络返回 4xx/5xx，回退缓存
    const cached = await caches.match(request)
    if (cached) return cached
    return response
  } catch (e) {
    const cached = await caches.match(request)
    if (cached) return cached
    // 返回一个友好的离线响应
    if (request.headers.get('Accept')?.includes('application/json')) {
      return new Response(JSON.stringify({ offline: true, items: [], total: 0 }), {
        headers: { 'Content-Type': 'application/json' }
      })
    }
    throw e
  }
}

// 缓存优先策略
async function cacheFirst(request, cacheName) {
  const isSafeToCache = request.method === 'GET'
  const cached = await caches.match(request)
  if (cached) return cached
  try {
    const response = await fetch(request)
    if (response.ok && isSafeToCache) {
      const cache = await caches.open(cacheName)
      cache.put(request, response.clone())
    }
    return response
  } catch (e) {
    return new Response('', { status: 204 })
  }
}
