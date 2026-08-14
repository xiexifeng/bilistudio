const API_BASE = '/api'

// ====== 当前用户ID（从 localStorage 读取，默认 1） ======
function getUserId() {
  return parseInt(localStorage.getItem('bilistudio_user_id') || '1', 10)
}

// ====== playurl 内存缓存：key=bvid_cid_qn，避免切回已播放视频时重复请求 API ======
const playurlCache = new Map()

// 导出清除方法（视频加载失败时调用，仅清除单个 key）
export function clearPlayurlCache(bvid, cid, qn = 80) {
  playurlCache.delete(`${bvid}_${cid}_${qn}`)
}
// 用户切换时清空全部缓存
export function clearAllPlayurlCache() {
  playurlCache.clear()
}

// ====== localStorage 缓存层：在线时自动存，离线时降级兜底 ======
const LOCAL_CACHE_PREFIX = 'bilistudio_cache_'
function _readCache(key) {
  try {
    const raw = localStorage.getItem(LOCAL_CACHE_PREFIX + key)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}
function _writeCache(key, data) {
  try { localStorage.setItem(LOCAL_CACHE_PREFIX + key, JSON.stringify(data)) } catch {}
}

// 包装器：在线成功写缓存，失败读缓存兜底
async function cachedGet(path, cacheKey) {
  try {
    const data = await request(path)
    _writeCache(cacheKey, data)
    return data
  } catch (e) {
    const cached = _readCache(cacheKey)
    if (cached) return cached
    throw e
  }
}

// ====== B站请求队列：防止并发请求触发风控 ======
let _pendingRequest = null
let _minInterval = 800  // 可调：两个 B站请求之间最小间隔（ms）

function _isBiliRequest(path) {
  return path.startsWith('/bilibili/') || path.startsWith('/auth/qrcode')
}

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  // 对 B站 API 做串行化排队
  if (_isBiliRequest(path)) {
    const prev = _pendingRequest
    let resolve
    _pendingRequest = new Promise(r => { resolve = r })
    if (prev) await prev
    // 额外延迟降低请求密度
    await new Promise(r => setTimeout(r, _minInterval))
    try {
      const result = await _doFetch(url, { ...options, headers })
      resolve()
      return result
    } catch (e) {
      resolve()
      throw e
    }
  }

  return _doFetch(url, { ...options, headers })
}

async function _doFetch(url, options) {
  const resp = await fetch(url, options)
  if (resp.status === 401) {
    throw new Error('请先登录B站')
  }
  if (resp.status === 429) {
    const err = await resp.json().catch(() => ({}))
    throw new Error('⏳ ' + (err.detail || '请求过于频繁，请稍后再试'))
  }
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err.detail || `请求失败: ${resp.status}`)
  }
  if (resp.status === 204) return null
  return resp.json()
}

export function proxyImage(url) {
  if (!url) return ''
  if (url.startsWith('data:')) return url
  if (url.startsWith('/api/')) return url
  // B站返回的 protocol-relative URL 补全为 https
  if (url.startsWith('//')) url = 'https:' + url
  return `/api/bilibili/proxy/image?url=${encodeURIComponent(url)}`
}

export const api = {
  // ====== 频率控制 ======
  getRateConfig: () => request('/config/rate'),
  updateRateConfig: (cfg) => request('/config/rate', { method: 'POST', body: JSON.stringify(cfg) }),
  setMinInterval: (ms) => { _minInterval = Math.max(200, Math.min(ms, 5000)) },

  // ===================== B站登录 =====================
  getQRCode: () => request('/auth/qrcode'),
  pollQRCode: (qrcodeKey) => request(`/auth/qrcode/status?qrcode_key=${qrcodeKey}`),
  checkLogin: () => request('/auth/status'),
  logout: () => request('/auth/logout', { method: 'POST' }),

  // ===================== B站搜索 & 视频 =====================
  search: (keyword, page = 1) => request(`/bilibili/search?keyword=${encodeURIComponent(keyword)}&page=${page}`),
  videoDetail: (bvid) => request(`/bilibili/video/${bvid}`),
  videoPlayurl: (bvid, cid, qn = 80) => {
    const key = `${bvid}_${cid}_${qn}`
    if (playurlCache.has(key)) {
      return Promise.resolve(playurlCache.get(key))
    }
    return request(`/bilibili/video/${bvid}/playurl?cid=${cid}&qn=${qn}`).then(data => {
      if (data?.url) playurlCache.set(key, data)
      return data
    })
  },
  videoCollection: (bvid) => request(`/bilibili/video/${bvid}/collection`),
  userInfo: (mid) => request(`/bilibili/user/${mid}`),
  userVideos: (mid, page = 1, source = 'default') => request(`/bilibili/user/${mid}/videos?page=${page}&source=${source}`),

  // ===================== B站个人内容（需登录） =====================
  followings: (page = 1) => request(`/bilibili/followings?page=${page}`),
  favorites: (page = 1) => request(`/bilibili/favorites?page=${page}`),
  favoriteContent: (mediaId, page = 1) => request(`/bilibili/favorites/${mediaId}?page=${page}`),
  history: (page = 1) => request(`/bilibili/history?page=${page}`),

  // ===================== 本地收藏（带用户隔离 + 离线缓存） =====================
  addCollection: (data) => {
    data.user_id = getUserId()
    return request('/collection', { method: 'POST', body: JSON.stringify(data) }).then(r => {
      // 添加成功后刷新收藏缓存
      api.listCollection().catch(() => {})
      return r
    })
  },
  listCollection: (params = {}) => {
    params.user_id = getUserId()
    const qs = new URLSearchParams(params).toString()
    return cachedGet(`/collection?${qs}`, `collection_${getUserId()}`)
  },
  updateCollection: (bvid, data) => request(`/collection/${bvid}?user_id=${getUserId()}`, {
    method: 'PUT', body: JSON.stringify(data)
  }),
  deleteCollection: (bvid) => request(`/collection/${bvid}?user_id=${getUserId()}`, { method: 'DELETE' }).then(r => {
    // 删除成功后刷新收藏缓存
    api.listCollection().catch(() => {})
    return r
  }),
  getAuthors: () => cachedGet(`/collection/authors?user_id=${getUserId()}`, `authors_${getUserId()}`),
  exportCollection: () => request(`/collection/export?user_id=${getUserId()}`),
  importCollection: (data) => request(`/collection/import?user_id=${getUserId()}`, {
    method: 'POST', body: JSON.stringify({ data })
  }),

  // ===================== 用户管理（带离线缓存） =====================
  listUsers: async () => {
    try {
      const users = await request('/users')
      _writeCache('users', users)
      return users
    } catch {
      const cached = _readCache('users')
      if (cached) return cached
      // 兜底：从 localStorage 构建最小用户列表
      return [{ id: getUserId(), name: '默认用户', color: '#FF6B35' }]
    }
  },
  createUser: (name = null) => request('/users', {
    method: 'POST', body: JSON.stringify(name ? { name } : {})
  }),
  renameUser: (userId, name) => request(`/users/${userId}/rename`, {
    method: 'PUT', body: JSON.stringify({ name })
  }),
  markUserActive: (userId) => request(`/users/${userId}/active`, { method: 'POST' }),
  deleteUser: (userId) => request(`/users/${userId}`, { method: 'DELETE' }),

  // ===================== 统计（带离线缓存） =====================
  getStats: () => cachedGet(`/stats?user_id=${getUserId()}`, `stats_${getUserId()}`),

  // ===================== 学习路线（带离线缓存） =====================
  getCourseProgress: () => cachedGet(`/courses/progress?user_id=${getUserId()}`, `courses_${getUserId()}`),
  updateStageProgress: (pathId, stageId, completed) => request('/courses/progress', {
    method: 'POST', body: JSON.stringify({ path_id: pathId, stage_id: stageId, completed })
  }),
}

export { getUserId }
