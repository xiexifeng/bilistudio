const API_BASE = '/api'

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
  videoCollection: (bvid) => request(`/bilibili/video/${bvid}/collection`),
  userInfo: (mid) => request(`/bilibili/user/${mid}`),
  userVideos: (mid, page = 1, source = 'default') => request(`/bilibili/user/${mid}/videos?page=${page}&source=${source}`),

  // ===================== B站个人内容（需登录） =====================
  followings: (page = 1) => request(`/bilibili/followings?page=${page}`),
  favorites: (page = 1) => request(`/bilibili/favorites?page=${page}`),
  favoriteContent: (mediaId, page = 1) => request(`/bilibili/favorites/${mediaId}?page=${page}`),
  history: (page = 1) => request(`/bilibili/history?page=${page}`),

  // ===================== 本地收藏 =====================
  addCollection: (data) => request('/collection', { method: 'POST', body: JSON.stringify(data) }),
  listCollection: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/collection?${qs}`)
  },
  deleteCollection: (bvid) => request(`/collection/${bvid}`, { method: 'DELETE' }),
  getAuthors: () => request('/collection/authors'),
  exportCollection: () => request('/collection/export'),
  importCollection: (data) => request('/collection/import', { method: 'POST', body: JSON.stringify({ data }) }),
}
