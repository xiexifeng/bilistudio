<template>
  <div class="player-page">
    <div class="left">
      <div class="player-wrap" :class="{ 'player-empty': !detail }">
        <div ref="playerContainer" class="dplayer-container"></div>
        <div v-if="!detail" class="player-overlay">
          <span class="spinner"></span>加载视频信息...
        </div>
        <div v-else-if="playerLoading" class="player-overlay">
          <span class="spinner"></span>获取播放地址...
        </div>
      </div>

      <div class="video-info" v-if="detail">
        <h1 class="video-title">{{ detail.title }}</h1>
        <div class="video-meta">
          <span class="author" @click="goAuthor(detail.author_mid)">👤 {{ detail.author }}</span>
          <span>▶ {{ formatNum(detail.play_count) }} 播放</span>
          <span>📅 {{ detail.pubdate }}</span>
        </div>
        <p class="video-desc" v-if="detail.description">{{ detail.description }}</p>
        <div class="video-actions">
          <button class="btn btn-primary" @click="addToCollection(detail)">
            {{ isCollected ? '✅ 已收藏' : '⭐ 收藏到本地' }}
          </button>
          <button
            v-if="nextEpisode"
            class="btn btn-next"
            @click="playNext"
            :title="`下一集：${nextEpisode.title}`"
          >
            ▶ 播放下一集
          </button>
          <button
            v-if="nextEpisode"
            class="btn btn-autoplay"
            :class="{ active: autoplayNext }"
            @click="toggleAutoplayNext"
            :title="autoplayNext ? '已开启自动连播' : '已关闭自动连播'"
          >
            <span class="autoplay-icon">{{ autoplayNext ? '🔁' : '⏸' }}</span>
            {{ autoplayNext ? '自动连播：开' : '自动连播：关' }}
          </button>
          <a :href="`https://www.bilibili.com/video/${detail.bvid}`" target="_blank" class="btn btn-outline">在B站打开</a>
        </div>

        <div v-if="hasCollection && isLastEpisode" class="end-panel">
          <span class="end-tip">✅ 这是合集的最后一集</span>
        </div>
      </div>

      <div v-else-if="loading" class="state"><span class="spinner"></span>加载中...</div>
    </div>

    <aside class="right">
      <!-- 合集/选集列表 -->
      <div v-if="collection" class="collection-block">
        <div class="collection-header">
          <h3>{{ isMultiP ? '🎬 视频选集' : '📚 合集列表' }}</h3>
          <span class="collection-count">{{ collection.title }} · {{ collection.total }}</span>
        </div>
        <div class="collection-list">
          <div
            v-for="v in collection.videos"
            :key="v.page || v.bvid"
            class="collection-item"
            :class="{ active: isMultiP ? v.page === currentPage : v.bvid === props.bvid }"
            @click="switchCollectionItem(v)"
          >
            <div class="col-thumb">
              <img v-if="v.pic" :src="proxyImage(v.pic)" loading="lazy">
              <span v-else class="col-ph">🎬</span>
              <span class="col-dur">{{ v.duration || '--:--' }}</span>
            </div>
            <div class="col-info">
              <p class="col-title" :title="v.title">{{ v.title }}</p>
              <span class="col-meta">
                <span v-if="v.section_title" class="col-section">[{{ v.section_title }}]</span>
                <span v-if="v.play_count">▶ {{ formatNum(v.play_count) }}</span>
                <span v-else-if="v.page">P{{ v.page }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <h3>⭐ 我的收藏</h3>
      <div v-if="myCollection.length === 0" class="side-empty">还没有收藏视频</div>
      <div v-else class="side-list">
        <div v-for="v in myCollection" :key="v.bvid" class="side-item" @click="$router.push('/play/' + v.bvid)">
          <div class="side-thumb">
            <img v-if="v.pic" :src="proxyImage(v.pic)" loading="lazy">
            <span v-else class="side-ph">🎬</span>
          </div>
          <div class="side-info">
            <p class="side-title" :title="v.title">{{ v.title }}</p>
            <span class="side-author">{{ v.author }}</span>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, onActivated, onDeactivated, inject, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { api, proxyImage } from '../api.js'
import DPlayer from 'dplayer'

const props = defineProps({ bvid: String })
const router = useRouter()
const showToast = inject('showToast')

defineOptions({ name: 'Player' })

// ====== 播放器 ======
const playerContainer = ref(null)
const playerLoading = ref(false)
let dp = null
let initTimer = null    // debounce 计时器
let initLock = false    // 防止并发初始化

// ====== 数据状态 ======
const detail = ref(null)
const loading = ref(true)
const myCollection = ref([])
const isCollected = ref(false)
const collection = ref(null)
const currentPage = ref(1)

// ====== 自动播放下一集开关（localStorage 持久化，默认关闭） ======
const _autoplayStored = (() => {
  try { return localStorage.getItem('bilistudio_autoplay_next') === 'true' }
  catch { return false }
})()
const autoplayNext = ref(_autoplayStored)
function toggleAutoplayNext() {
  autoplayNext.value = !autoplayNext.value
  try { localStorage.setItem('bilistudio_autoplay_next', String(autoplayNext.value)) } catch {}
}

// ====== 当前视频的 cid（多P时取对应 page 的 cid） ======
const currentCid = computed(() => {
  if (!detail.value) return null
  if (isMultiP.value && collection.value?.videos) {
    const pageItem = collection.value.videos.find(v => v.page === currentPage.value)
    return pageItem?.cid || detail.value.cid
  }
  return detail.value.cid
})

// ====== 合集/多P ======
const isMultiP = computed(() => collection.value?.season_id === 0)
const hasCollection = computed(() => !!collection.value?.videos?.length)

const nextEpisode = computed(() => {
  if (!hasCollection.value) return null
  if (isMultiP.value) {
    const nextPage = currentPage.value + 1
    const next = collection.value.videos.find(v => v.page === nextPage)
    if (next) return { type: 'page', page: nextPage, bvid: props.bvid, title: next.title }
    return null
  }
  const idx = collection.value.videos.findIndex(v => v.bvid === props.bvid)
  if (idx < 0 || idx >= collection.value.videos.length - 1) return null
  const n = collection.value.videos[idx + 1]
  return { type: 'bvid', bvid: n.bvid, title: n.title }
})

const isLastEpisode = computed(() => hasCollection.value && nextEpisode.value === null)

// ====== DPlayer 初始化（防抖：多次触发只执行最后一次） ======
function initPlayer() {
  if (!props.bvid) return
  const cid = currentCid.value
  if (!cid) return

  clearTimeout(initTimer)
  initTimer = setTimeout(() => {
    _doInitPlayer(cid)
  }, 120)
}

async function _doInitPlayer(cid) {
  if (initLock) return
  if (!playerContainer.value) return

  initLock = true

  // 销毁旧实例
  if (dp) {
    dp.destroy()
    dp = null
  }

  playerLoading.value = true

  try {
    const playData = await api.videoPlayurl(props.bvid, cid, 80)
    if (!playData?.url) {
      showToast?.('❌ 该视频暂无播放地址（可能需要登录）')
      playerLoading.value = false
      initLock = false
      return
    }

    dp = new DPlayer({
      container: playerContainer.value,
      autoplay: true,
      video: {
        url: playData.url,
        type: 'auto',
      },
      lang: 'zh-cn',
    })

    // === 自动播放下一集（仅开启开关时） ===
    dp.on('ended', () => {
      if (!autoplayNext.value) return
      const next = nextEpisode.value
      if (next) {
        showToast?.(`⏭ 自动播放下一集: ${next.title}`)
        playNext()
      }
    })

    // === PiP 关闭时：自动回到播放页 ===
    dp.video.addEventListener('leavepictureinpicture', () => {
      if (router.currentRoute.value.path !== `/play/${props.bvid}`) {
        router.push(`/play/${props.bvid}`)
      }
    })

    // 正常播放时设置浏览器标签页标题
    document.title = (detail.value?.title || '正在播放') + ' - BiliStudio'

  } catch (e) {
    console.error('DPlayer init failed:', e)
    showToast?.('❌ 播放器初始化失败: ' + (e.message || '未知错误'))
  } finally {
    playerLoading.value = false
    initLock = false
  }
}

function destroyPlayer() {
  clearTimeout(initTimer)
  if (dp) {
    dp.destroy()
    dp = null
  }
}

// ====== 工具函数 ======
function formatNum(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return String(n)
}

function goAuthor(mid) { if (mid) router.push(`/user/${mid}`) }

// ====== 合集/选集切换 ======
function switchCollectionItem(v) {
  if (isMultiP.value && v.page) {
    currentPage.value = v.page
  } else if (v.bvid && v.bvid !== props.bvid) {
    router.push(`/play/${v.bvid}`)
  }
}

function playNext() {
  const next = nextEpisode.value
  if (!next) {
    showToast?.('✅ 已是最后一集')
    return
  }
  showToast?.(`▶ 下一集: ${next.title}`)

  if (next.type === 'page') {
    currentPage.value = next.page
  } else {
    router.push(`/play/${next.bvid}`)
  }
}

// ====== 数据加载 ======
async function addToCollection(video) {
  try {
    await api.addCollection({
      bvid: video.bvid, title: video.title, author: video.author,
      author_mid: video.author_mid, pic: video.pic,
      duration: video.duration, description: video.description,
      play_count: video.play_count, pubdate: video.pubdate,
    })
    isCollected.value = true; showToast?.('已收藏 ⭐'); loadMyCollection()
  } catch (e) { showToast?.(e.message) }
}

async function loadDetail(skipCollection = false) {
  loading.value = true
  if (!skipCollection) {
    collection.value = null
    currentPage.value = 1
  }
  try {
    detail.value = await api.videoDetail(props.bvid)
    if (!skipCollection) {
      collection.value = detail.value?.collection || null
    }
    const col = await api.listCollection({ keyword: props.bvid })
    isCollected.value = col.total > 0
  } catch (e) { showToast?.(e.message) }
  finally { loading.value = false }
}

async function loadMyCollection() {
  try {
    const res = await api.listCollection({ page_size: 20 })
    myCollection.value = res.items.filter(v => v.bvid !== props.bvid)
  } catch (e) {}
}

// ====== 生命周期 ======
onMounted(() => {
  loadDetail()
  loadMyCollection()
})

onBeforeUnmount(() => {
  destroyPlayer()
  document.title = 'BiliStudio'
})

// keep-alive: 离开页面 — 浏览器原生画中画（不重新加载视频）
onDeactivated(() => {
  // 必须先设标题，PiP 窗口创建时读取 document.title
  document.title = (detail.value?.title || '正在播放') + ' - BiliStudio'
  if (dp?.video && document.pictureInPictureEnabled) {
    dp.video.requestPictureInPicture()
      .then(() => dp.play())   // 防止浏览器默认暂停
      .catch(() => {})
  }
})

// 回来时退出 PiP，恢复全屏播放
onActivated(() => {
  if (document.pictureInPictureElement) {
    document.exitPictureInPicture().catch(() => {})
  }
  document.title = (detail.value?.title || '正在播放') + ' - BiliStudio'
  if (dp) dp.play()
})

// 切换视频（路由 bvid 变化）
watch(() => props.bvid, (newBvid, oldBvid) => {
  if (newBvid && newBvid !== oldBvid) {
    currentPage.value = 1
    const inCollection = collection.value?.videos?.some(v => v.bvid === newBvid)
    loadDetail(inCollection)
    loadMyCollection()
  }
})

// 多P切换：cid 变了就重建播放器
watch(currentCid, (newCid, oldCid) => {
  if (newCid && newCid !== oldCid) {
    nextTick(() => initPlayer())
  }
})
</script>

<style scoped>
.player-page { display: flex; gap: 24px; }

.left { flex: 1; min-width: 0; }
.right {
  width: 320px; flex-shrink: 0;
  background: #fff; border-radius: 16px;
  padding: 20px; border: 1px solid #F1F5F9;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  align-self: flex-start; position: sticky; top: 80px;
  max-height: calc(100vh - 100px); overflow-y: auto;
}
.right h3 { font-size: 16px; font-weight: 700; margin-bottom: 14px; color: #2C3E50; }

/* === 播放器容器 === */
.player-wrap {
  position: relative; width: 100%;
  background: #000; border-radius: 14px; overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  min-height: 360px;  /* 宽屏下的 16:9 兜底 */
}
/* 没有播放器时撑开 16:9 */
.player-wrap.player-empty {
  aspect-ratio: 16 / 9;
}
.dplayer-container { width: 100%; }

/* DPlayer 内部会设置自己的高度，覆盖保持 16:9 */
.player-wrap :deep(.dplayer) {
  border-radius: 14px; overflow: hidden;
}

.player-overlay {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.85); color: rgba(255,255,255,0.8);
  font-size: 14px; z-index: 10; border-radius: 14px;
}

/* === 视频信息 === */
.video-info { margin-top: 20px; background: #fff; border-radius: 14px; padding: 20px 24px; border: 1px solid #F1F5F9; }
.video-title { font-size: 20px; font-weight: 700; line-height: 1.4; margin-bottom: 12px; color: #2C3E50; }
.video-meta {
  display: flex; gap: 16px; font-size: 13px; color: #94A3B8;
  margin-bottom: 14px; flex-wrap: wrap; align-items: center;
}
.video-meta .author {
  color: #FF6B35; cursor: pointer; font-weight: 600;
  padding: 3px 10px; border-radius: 6px; background: #FFF3E0;
  transition: background .15s;
}
.video-meta .author:hover { background: #FFE0B2; }
.video-desc { font-size: 14px; color: #64748B; line-height: 1.7; margin-bottom: 18px; white-space: pre-wrap; }
.video-actions { display: flex; gap: 10px; flex-wrap: wrap; }

.btn {
  padding: 10px 22px; border-radius: 10px; border: none;
  font-size: 14px; cursor: pointer; font-weight: 600; text-decoration: none;
  display: inline-flex; align-items: center; gap: 4px; font-family: inherit;
  transition: all .15s;
}
.btn-primary { background: linear-gradient(135deg, #FF6B35, #FF8F5E); color: #fff; box-shadow: 0 2px 8px rgba(255,107,53,0.25); }
.btn-primary:hover { box-shadow: 0 4px 14px rgba(255,107,53,0.4); }
.btn-outline { background: #fff; color: #FF6B35; border: 1.5px solid #FF6B35; }
.btn-outline:hover { background: #FFF3E0; }
.btn-next {
  background: linear-gradient(135deg, #4A90E2, #6BB6FF); color: #fff;
  box-shadow: 0 2px 8px rgba(74,144,226,0.25);
}
.btn-next:hover { box-shadow: 0 4px 14px rgba(74,144,226,0.4); }
.btn-autoplay {
  background: #F1F5F9; color: #64748B; border: 1.5px solid #E2E8F0;
}
.btn-autoplay:hover { border-color: #CBD5E1; }
.btn-autoplay.active {
  background: linear-gradient(135deg, #059669, #10B981); color: #fff;
  border-color: transparent;
  box-shadow: 0 2px 8px rgba(5,150,105,0.25);
}
.btn-autoplay.active:hover { box-shadow: 0 4px 14px rgba(5,150,105,0.4); }
.autoplay-icon { font-size: 16px; }

.end-panel {
  margin-top: 16px; padding: 14px 18px;
  background: linear-gradient(135deg, #F0FDF4, #DCFCE7);
  border: 1px solid #BBF7D0; border-radius: 12px;
  text-align: center;
}
.end-tip { font-size: 13px; color: #16A34A; font-weight: 600; }

/* === 侧边栏 === */
.side-list { display: flex; flex-direction: column; gap: 8px; }
.side-item {
  display: flex; gap: 10px; cursor: pointer;
  padding: 8px; border-radius: 10px; transition: all .15s;
  border: 1px solid transparent;
}
.side-item:hover { background: #F8FAFC; border-color: #F1F5F9; }
.side-thumb {
  width: 110px; height: 62px; border-radius: 8px;
  overflow: hidden; flex-shrink: 0; background: #F1F5F9;
}
.side-thumb img, .side-ph {
  width: 100%; height: 100%; object-fit: cover;
}
.side-ph {
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; background: #E2E8F0;
}
.side-info { flex: 1; min-width: 0; }
.side-title {
  font-size: 13px; line-height: 1.4; font-weight: 500;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; margin-bottom: 4px; color: #2C3E50;
}
.side-author { font-size: 12px; color: #94A3B8; }
.side-empty { font-size: 13px; color: #CBD5E1; text-align: center; padding: 30px 0; }

/* === 合集列表 === */
.collection-block {
  margin-bottom: 22px; padding-bottom: 18px;
  border-bottom: 1px dashed #E2E8F0;
}
.collection-header {
  display: flex; flex-direction: column; gap: 4px;
  margin-bottom: 12px;
}
.collection-header h3 { margin: 0; }
.collection-count {
  font-size: 12px; color: #94A3B8;
  display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical;
  overflow: hidden; font-weight: 500;
}
.collection-list {
  display: flex; flex-direction: column; gap: 8px;
  max-height: 480px; overflow-y: auto;
  padding-right: 4px;
}
.collection-list::-webkit-scrollbar { width: 4px; }
.collection-list::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 2px; }

.collection-item {
  display: flex; gap: 10px; cursor: pointer;
  padding: 8px; border-radius: 10px; transition: all .15s;
  border: 1px solid transparent;
  position: relative;
}
.collection-item:hover { background: #F8FAFC; border-color: #F1F5F9; }
.collection-item.active {
  background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
  border-color: #FF6B35;
}
.collection-item.active::before {
  content: '▶'; position: absolute; left: -2px; top: 50%;
  transform: translateY(-50%); color: #FF6B35; font-size: 10px;
}
.col-thumb {
  position: relative; width: 110px; height: 62px;
  border-radius: 8px; overflow: hidden; flex-shrink: 0;
  background: #F1F5F9;
}
.col-thumb img { width: 100%; height: 100%; object-fit: cover; }
.col-dur {
  position: absolute; right: 4px; bottom: 4px;
  background: rgba(0,0,0,0.75); color: #fff;
  font-size: 11px; padding: 1px 6px; border-radius: 4px;
  font-weight: 500;
}
.col-info { flex: 1; min-width: 0; }
.col-title {
  font-size: 13px; line-height: 1.4; font-weight: 500;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; margin-bottom: 4px; color: #2C3E50;
}
.collection-item.active .col-title { color: #FF6B35; font-weight: 600; }
.col-meta {
  font-size: 11px; color: #94A3B8;
  display: flex; align-items: center; gap: 6px;
}
.col-section {
  background: #F1F5F9; color: #64748B;
  padding: 1px 5px; border-radius: 3px; font-weight: 500;
}

.state { padding: 40px; text-align: center; color: #94A3B8; display: flex; align-items: center; justify-content: center; gap: 8px; }
.spinner {
  width: 20px; height: 20px; border: 2px solid #E2E8F0;
  border-top-color: #FF6B35; border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 900px) {
  .player-page { flex-direction: column; }
  .right { width: 100%; position: static; }
}
</style>
