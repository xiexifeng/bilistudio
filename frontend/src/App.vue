<template>
  <div class="app">
    <!-- 顶栏 -->
    <header class="topbar">
      <div class="logo" @click="$router.push('/')">
        <span class="logo-icon">📚</span>
        <span class="logo-text">BiliStudio</span>
        <span class="logo-badge">少儿版</span>
      </div>

      <div class="search-box">
        <svg class="search-icon-svg" viewBox="0 0 24 24" width="18" height="18"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" fill="currentColor"/></svg>
        <input v-model="searchQuery" placeholder="搜索教育视频、科普知识..." @input="onSearchInput" @keyup.enter="doSearchNow">
        <button class="search-btn" @click="doSearchNow">搜索</button>
      </div>

      <nav class="nav">
        <router-link to="/">🏠 发现</router-link>
        <router-link to="/collection">⭐ 收藏</router-link>
        <router-link to="/courses">📖 课程</router-link>
        <router-link to="/stats">📊 统计</router-link>
      </nav>

      <div class="actions">
        <!-- 用户切换器 -->
        <div class="user-switcher" @click.stop="showUsers = !showUsers">
          <span class="user-dot" :style="{background: currentUser?.color || '#FF6B35'}"></span>
          <span class="user-name">{{ currentUser?.name || '用户' }}</span>
          <span class="user-arrow">▾</span>
        </div>

        <div v-if="showUsers" class="user-dropdown" @click.stop>
          <div class="dropdown-title">切换用户</div>
          <div v-for="u in allUsers" :key="u.id" class="user-item" :class="{active: u.id === currentUserId}" @click="switchUser(u)">
            <span class="ui-dot" :style="{background: u.color}"></span>
            <span class="ui-name">{{ u.name }}</span>
            <span v-if="u.id === currentUserId" class="ui-badge">当前</span>
            <div class="ui-actions">
              <button class="ui-btn" @click.stop="startRename(u)" title="改名">✎</button>
              <button v-if="u.id !== 1 && allUsers.length > 1" class="ui-btn danger" @click.stop="confirmDeleteUser(u)" title="删除">✕</button>
            </div>
          </div>
          <div class="dropdown-footer">
            <button class="btn btn-sm" @click="doCreateUser">+ 新建用户</button>
          </div>
        </div>

        <button v-if="!biliUser" class="btn btn-login" @click="startLogin">登录B站</button>
        <div v-else class="user-box">
          <img v-if="biliUser.face" :src="proxyImage(biliUser.face)" class="avatar" />
          <span class="username">{{ biliUser.name }}</span>
          <button class="btn btn-ghost" @click="doLogout">退出</button>
        </div>
      </div>
    </header>

    <!-- 路由视图 -->
    <main class="main">
      <router-view v-slot="{ Component }">
        <keep-alive :include="['Player']">
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>

    <!-- 登录弹窗 -->
    <div v-if="showLogin" class="modal-overlay" @click="showLogin=false">
      <div class="modal" @click.stop>
        <div class="modal-icon">📱</div>
        <h3>B站扫码登录</h3>
        <p class="hint">打开B站App扫描二维码</p>

        <div class="qr-area">
          <img v-if="qrDataUrl" :src="qrDataUrl" class="qr-img" alt="B站登录二维码">
          <div v-if="qrLoading" class="qr-loading">
            <span class="spinner"></span>
            加载中...
          </div>

          <div v-if="qrStatus" class="qr-status" :class="qrStatus">
            <span v-if="qrStatus==='pending'"><span class="dot pending"></span>等待扫码...</span>
            <span v-else-if="qrStatus==='scanned'"><span class="dot success"></span>已扫码，请确认</span>
            <span v-else-if="qrStatus==='expired'"><span class="dot expired"></span>二维码已过期</span>
            <span v-else-if="qrStatus==='error'"><span class="dot error"></span>{{ qrMessage }}</span>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn btn-ghost" @click="cancelLogin">取消</button>
          <button v-if="qrStatus==='expired'" class="btn btn-primary" @click="startLogin">重新获取</button>
        </div>
        <p class="login-hint">仅本地使用，数据不会泄露</p>
      </div>
    </div>

    <!-- 重命名弹窗 -->
    <div v-if="renameUser" class="modal-overlay" @click="renameUser=null">
      <div class="modal" @click.stop>
        <h3>修改用户名</h3>
        <input v-model="renameValue" class="rename-input" @keyup.enter="doRename" placeholder="输入新名字..." autofocus>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="renameUser=null">取消</button>
          <button class="btn btn-primary" @click="doRename">确认</button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div class="toast" :class="{show: toastMsg}">{{ toastMsg }}</div>
  </div>
</template>

<script setup>
import { ref, provide, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { api, proxyImage, getUserId } from './api.js'
import QRCode from 'qrcode'

const router = useRouter()
const biliUser = ref(null)
const showLogin = ref(false)
const searchQuery = ref('')
const toastMsg = ref('')
let toastTimer
let searchTimer = null

// ====== 用户管理 ======
const showUsers = ref(false)
const allUsers = ref([])
const currentUserId = ref(getUserId())
const currentUser = computed(() => allUsers.value.find(u => u.id === currentUserId.value) || { id: currentUserId.value, name: '用户', color: '#FF6B35' })
const renameUser = ref(null)
const renameValue = ref('')
// 数据版本号：用户切换或数据变更时+1，子组件 watch 它来刷新数据
const dataVersion = ref(0)

document.addEventListener('click', (e) => {
  // 下拉菜单内部不关闭
  if (!e.target.closest('.user-dropdown') && !e.target.closest('.user-switcher')) {
    showUsers.value = false
  }
})

async function loadUsers() {
  try {
    const users = await api.listUsers()
    allUsers.value = users
    if (!users.find(u => u.id === currentUserId.value)) {
      currentUserId.value = users[0]?.id || 1
      localStorage.setItem('bilistudio_user_id', String(currentUserId.value))
    }
    api.markUserActive(currentUserId.value).catch(() => {})
  } catch (e) {
    // 离线兜底：尝试从 localStorage 恢复用户列表（注意 api.js 使用 bilistudio_cache_ 前缀）
    const cached = localStorage.getItem('bilistudio_cache_users_data')
    if (cached) {
      try {
        const parsed = JSON.parse(cached)
        if (Array.isArray(parsed) && parsed.length > 0) {
          allUsers.value = parsed
          return
        }
      } catch (_) {}
    }
    // 彻底离线且无缓存：只保留一个占位，不创建新用户
    if (allUsers.value.length === 0) {
      allUsers.value = [{ id: currentUserId.value, name: '离线用户', color: '#ccc', offline: true }]
    }
  }
}

function switchUser(user) {
  localStorage.setItem('bilistudio_user_id', String(user.id))
  router.go(0)
}

async function doCreateUser() {
  try {
    const user = await api.createUser()
    showToast(`已创建用户: ${user.name}`)
    localStorage.setItem('bilistudio_user_id', String(user.id))
    router.go(0)
  } catch (e) {
    showToast('创建失败: ' + e.message)
  }
}

function startRename(user) {
  renameUser.value = user
  renameValue.value = user.name
}

async function doRename() {
  if (!renameUser.value || !renameValue.value.trim()) return
  try {
    await api.renameUser(renameUser.value.id, renameValue.value.trim())
    showToast('改名成功')
    renameUser.value = null
    await loadUsers()
  } catch (e) {
    showToast('改名失败: ' + e.message)
  }
}

async function confirmDeleteUser(user) {
  if (!confirm(`确定删除用户「${user.name}」吗？该用户的所有收藏和数据将被清除。`)) return
  try {
    await api.deleteUser(user.id)
    showToast(`已删除用户: ${user.name}`)
    await loadUsers()
    if (currentUserId.value === user.id) {
      localStorage.setItem('bilistudio_user_id', '1')
      router.go(0)
    }
  } catch (e) {
    showToast('删除失败: ' + e.message)
  }
}

provide('currentUserId', currentUserId)
provide('dataVersion', dataVersion)

const qrLoading = ref(false)
const qrDataUrl = ref('')
const qrStatus = ref('')
const qrMessage = ref('')
let qrcodeKey = ''
let pollTimer = null

onMounted(async () => {
  await loadUsers()
  await checkLoginStatus()
})

async function checkLoginStatus() {
  try {
    const res = await api.checkLogin()
    if (res.logged_in && res.user) {
      biliUser.value = res.user
    }
  } catch (e) {}
}

function doSearchNow() {
  if (!searchQuery.value.trim()) return
  router.push({ path: '/', query: { q: searchQuery.value } })
}

function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(doSearchNow, 600)
}

async function startLogin() {
  showLogin.value = true
  qrLoading.value = true
  qrStatus.value = ''
  qrMessage.value = ''
  qrDataUrl.value = ''

  try {
    const res = await api.getQRCode()
    qrcodeKey = res.qrcode_key
    qrDataUrl.value = await QRCode.toDataURL(res.url, {
      width: 200,
      margin: 2,
      color: { dark: '#2C3E50', light: '#fff' },
    })
    qrLoading.value = false
    startPolling()
  } catch (e) {
    qrLoading.value = false
    qrStatus.value = 'error'
    qrMessage.value = e.message
  }
}

function startPolling() {
  clearInterval(pollTimer)
  qrStatus.value = 'pending'
  pollTimer = setInterval(async () => {
    try {
      const res = await api.pollQRCode(qrcodeKey)
      if (res.status === 'success') {
        clearInterval(pollTimer)
        qrStatus.value = 'success'
        biliUser.value = res.user
        showLogin.value = false
        showToast(`👋 欢迎，${res.user.name}`)
      } else if (res.status === 'expired') {
        clearInterval(pollTimer)
        qrStatus.value = 'expired'
      } else {
        qrStatus.value = res.status
        qrMessage.value = res.message || ''
      }
    } catch (e) {
      clearInterval(pollTimer)
      qrStatus.value = 'error'
      qrMessage.value = e.message
    }
  }, 2000)
}

function cancelLogin() {
  clearInterval(pollTimer)
  showLogin.value = false
  qrStatus.value = ''
  qrDataUrl.value = ''
}

async function doLogout() {
  try { await api.logout() } catch (e) {}
  biliUser.value = null
  showToast('已退出B站登录')
}

function showToast(msg) {
  toastMsg.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => toastMsg.value = '', 2000)
}

provide('showToast', showToast)
provide('biliUser', biliUser)
</script>

<style>
/* ====== 全局重置 ====== */
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #F0F4F8;
  color: #2C3E50;
  -webkit-font-smoothing: antialiased;
}
</style>

<style scoped>
.app { min-height: 100vh; display: flex; flex-direction: column; background: linear-gradient(180deg, #EEF2F7 0%, #F0F4F8 100%); }

/* ====== 顶栏 ====== */
.topbar {
  position: sticky; top: 0; z-index: 100;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0,0,0,0.06);
  padding: 0 28px; height: 60px;
  display: flex; align-items: center; gap: 20px;
}
.logo { display: flex; align-items: center; gap: 8px; cursor: pointer; user-select: none; flex-shrink: 0; }
.logo-icon { font-size: 26px; }
.logo-text { font-size: 20px; font-weight: 700; color: #FF6B35; letter-spacing: -0.3px; }
.logo-badge {
  font-size: 11px; font-weight: 600; color: #FF6B35;
  background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
  padding: 2px 8px; border-radius: 10px;
}

.search-box {
  flex: 1; max-width: 480px; display: flex; position: relative;
  background: #F0F4F8; border-radius: 24px;
  border: 2px solid transparent; transition: all .25s;
}
.search-box:focus-within {
  background: #fff; border-color: #FF6B35;
  box-shadow: 0 0 0 4px rgba(255,107,53,0.1);
}
.search-icon-svg {
  position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
  color: #94A3B8; pointer-events: none;
}
.search-box input {
  width: 100%; height: 42px; padding: 0 80px 0 42px;
  border: none; background: transparent;
  font-size: 14px; outline: none; color: #2C3E50;
}
.search-box input::placeholder { color: #94A3B8; }
.search-btn {
  position: absolute; right: 4px; top: 50%; transform: translateY(-50%);
  background: linear-gradient(135deg, #FF6B35, #FF8F5E);
  color: #fff; border: none; height: 34px; padding: 0 18px;
  border-radius: 20px; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all .2s;
}
.search-btn:hover { box-shadow: 0 2px 8px rgba(255,107,53,0.35); transform: translateY(-50%) scale(1.03); }

.nav { display: flex; gap: 4px; font-size: 14px; flex-shrink: 0; }
.nav a {
  color: #64748B; text-decoration: none; padding: 8px 14px;
  border-radius: 10px; font-weight: 500; transition: all .15s;
}
.nav a:hover { color: #FF6B35; background: rgba(255,107,53,0.06); }
.nav a.router-link-active { color: #FF6B35; background: rgba(255,107,53,0.1); font-weight: 600; }

.actions { margin-left: auto; display: flex; align-items: center; flex-shrink: 0; gap: 10px; }
.btn {
  padding: 8px 18px; border-radius: 10px; border: none;
  font-size: 14px; cursor: pointer; font-weight: 600;
  transition: all .2s; font-family: inherit;
}

/* ====== 用户切换器 ====== */
.user-switcher {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 10px; border-radius: 20px;
  cursor: pointer; border: 1px solid #E2E8F0;
  background: #F8FAFC; transition: all .15s;
  position: relative; user-select: none;
}
.user-switcher:hover { border-color: #FF6B35; background: #fff; }
.user-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}
.user-name { font-size: 13px; color: #2C3E50; font-weight: 600; }
.user-arrow { font-size: 10px; color: #94A3B8; }

.user-dropdown {
  position: absolute; top: 68px; right: 28px;
  background: #fff; border-radius: 14px;
  box-shadow: 0 16px 48px rgba(0,0,0,0.14);
  border: 1px solid #F1F5F9; width: 260px;
  padding: 8px 0; z-index: 160;
  animation: dropIn 0.2s ease-out;
}
@keyframes dropIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
.dropdown-title {
  font-size: 12px; color: #94A3B8; font-weight: 600;
  padding: 6px 16px 10px; letter-spacing: 0.5px;
}
.user-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 16px; cursor: pointer; transition: background .12s;
}
.user-item:hover { background: #F8FAFC; }
.user-item.active { background: #FFF3E0; }
.ui-dot {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; color: #fff; font-weight: 700; flex-shrink: 0;
}
.ui-name { font-size: 14px; color: #2C3E50; font-weight: 500; flex: 1; }
.ui-badge {
  font-size: 10px; color: #FF6B35; background: #FFF3E0;
  padding: 1px 6px; border-radius: 8px; font-weight: 600;
}
.ui-actions { display: flex; gap: 2px; opacity: 0; transition: opacity .15s; }
.user-item:hover .ui-actions { opacity: 1; }
.ui-btn {
  width: 24px; height: 24px; border-radius: 6px; border: none;
  background: #F1F5F9; color: #64748B; font-size: 12px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.ui-btn:hover { background: #E2E8F0; }
.ui-btn.danger:hover { background: #FEE2E2; color: #EF4444; }

.dropdown-footer {
  padding: 10px 16px; border-top: 1px solid #F1F5F9;
  margin-top: 4px;
}
.btn-sm {
  width: 100%; padding: 8px; border-radius: 10px;
  border: 1px dashed #E2E8F0; background: #F8FAFC;
  color: #FF6B35; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all .15s; font-family: inherit;
}
.btn-sm:hover { background: #FFF3E0; border-color: #FF6B35; }

.rename-input {
  width: 100%; padding: 10px 14px; border: 2px solid #E2E8F0;
  border-radius: 10px; font-size: 16px; outline: none;
  margin: 12px 0; font-family: inherit; text-align: center;
  transition: border-color .2s;
}
.rename-input:focus { border-color: #FF6B35; }
.btn-login {
  background: linear-gradient(135deg, #45B7D1, #5CC9E0);
  color: #fff; box-shadow: 0 2px 8px rgba(69,183,209,0.25);
}
.btn-login:hover { box-shadow: 0 4px 14px rgba(69,183,209,0.4); transform: translateY(-1px); }
.btn-primary {
  background: linear-gradient(135deg, #FF6B35, #FF8F5E);
  color: #fff; box-shadow: 0 2px 8px rgba(255,107,53,0.25);
}
.btn-primary:hover { box-shadow: 0 4px 14px rgba(255,107,53,0.4); }
.btn-ghost { background: none; color: #94A3B8; padding: 4px 8px; }
.btn-ghost:hover { color: #64748B; }

.user-box { display: flex; align-items: center; gap: 10px; }
.avatar {
  width: 34px; height: 34px; border-radius: 50%;
  border: 2px solid #FF6B35; object-fit: cover;
}
.username { font-size: 14px; color: #2C3E50; font-weight: 600; }

.main { flex: 1; max-width: 1320px; width: 100%; margin: 0 auto; padding: 24px 28px; }

/* ====== Modal ====== */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.35);
  z-index: 200; display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(4px);
}
.modal {
  background: #fff; border-radius: 20px; padding: 32px 36px;
  width: 380px; max-width: 92vw; text-align: center;
  box-shadow: 0 20px 60px rgba(0,0,0,0.12);
}
.modal-icon { font-size: 40px; margin-bottom: 8px; }
.modal h3 { font-size: 18px; margin-bottom: 4px; color: #2C3E50; }
.modal .hint { font-size: 13px; color: #94A3B8; margin-bottom: 20px; }

.qr-area {
  display: flex; flex-direction: column; align-items: center;
  min-height: 220px; justify-content: center;
}
.qr-img { width: 200px; height: 200px; border: 1px solid #E2E8F0; border-radius: 12px; }
.qr-loading { color: #94A3B8; font-size: 14px; display: flex; align-items: center; gap: 8px; }
.spinner {
  width: 18px; height: 18px; border: 2px solid #E2E8F0;
  border-top-color: #FF6B35; border-radius: 50%;
  animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.qr-status { margin-top: 14px; font-size: 13px; padding: 6px 16px; border-radius: 20px; display: flex; align-items: center; gap: 8px; }
.dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot.pending { background: #F59E0B; animation: pulse 1.5s infinite; }
.dot.success { background: #10B981; }
.dot.expired { background: #94A3B8; }
.dot.error { background: #EF4444; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

.qr-status.pending { color: #92400E; background: #FEF3C7; }
.qr-status.scanned { color: #065F46; background: #D1FAE5; }
.qr-status.expired { color: #64748B; background: #F1F5F9; }
.qr-status.error { color: #991B1B; background: #FEE2E2; }
.qr-status.success { color: #065F46; background: #D1FAE5; }

.modal-actions { display: flex; gap: 10px; justify-content: center; margin-top: 16px; }
.login-hint { font-size: 11px; color: #CBD5E1; margin-top: 16px; }

.toast {
  position: fixed; top: 80px; left: 50%; transform: translateX(-50%);
  background: #2C3E50; color: #fff; padding: 12px 28px;
  border-radius: 10px; font-size: 14px; z-index: 300;
  opacity: 0; transition: opacity .25s; pointer-events: none;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}
.toast.show { opacity: 1; }

</style>
