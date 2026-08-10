<template>
  <div class="player-page">
    <div class="left">
    <div class="player-wrap">
      <Teleport :to="teleportTarget" :disabled="!teleportTarget">
        <iframe
          :src="embedUrl"
          frameborder="0"
          allowfullscreen
          allow="autoplay; fullscreen"
          scrolling="no"
        ></iframe>
      </Teleport>
      <!-- 当 iframe 被传送到小窗时，占位保持页面布局 -->
      <div v-if="teleportTarget" class="teleport-placeholder">
        <span>📺 已切换至小窗播放</span>
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
          <a :href="`https://www.bilibili.com/video/${detail.bvid}`" target="_blank" class="btn btn-outline">在B站打开</a>
        </div>

        <div v-if="hasCollection && isLastEpisode" class="end-panel">
          <span class="end-tip">✅ 这是合集的最后一集</span>
        </div>
      </div>

      <div v-else-if="loading" class="state"><span class="spinner"></span>加载中...</div>
    </div>

    <aside class="right">
      <!-- 合集/选集列表（视频属于合集或多P时显示） -->
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
import { ref, computed, onMounted, onActivated, onDeactivated, inject, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api, proxyImage } from '../api.js'

const props = defineProps({ bvid: String })
const router = useRouter()
const route = useRoute()
const showToast = inject('showToast')
const openMiniPlayer = inject('openMiniPlayer')
const closeMiniPlayer = inject('closeMiniPlayer')
const miniPlayerState = inject('miniPlayerState')

defineOptions({ name: 'Player' })

// Teleport 目标：小窗激活时把 iframe 移植到迷你播放器，保留播放状态和声音
const teleportTarget = computed(() => {
  if (miniPlayerState?.value?.visible && miniPlayerState.value.bvid === props.bvid) {
    return '#mini-player-teleport'
  }
  return null  // null = 渲染在原位
})

const detail = ref(null)
const loading = ref(true)
const myCollection = ref([])
const isCollected = ref(false)
const collection = ref(null)
const currentPage = ref(1)  // 当前多P视频的分页号

// 判断是否为多P视频选集（season_id === 0 表示多P）
const isMultiP = computed(() => collection.value?.season_id === 0)

// 是否存在合集/选集
const hasCollection = computed(() => !!collection.value?.videos?.length)

// 下一集（合集/选集中的下一项）
const nextEpisode = computed(() => {
  if (!hasCollection.value) return null

  if (isMultiP.value) {
    const nextPage = currentPage.value + 1
    const next = collection.value.videos.find(v => v.page === nextPage)
    if (next) return { type: 'page', page: nextPage, bvid: props.bvid, title: next.title }
    return null
  }

  // 合集视频：找到当前视频位置，返回下一项
  const idx = collection.value.videos.findIndex(v => v.bvid === props.bvid)
  if (idx < 0 || idx >= collection.value.videos.length - 1) return null
  const n = collection.value.videos[idx + 1]
  return { type: 'bvid', bvid: n.bvid, title: n.title }
})

// 是否已是最后一集
const isLastEpisode = computed(() => hasCollection.value && nextEpisode.value === null)

const embedUrl = computed(() => {
  if (!props.bvid) return ''
  const pageParam = currentPage.value > 1 ? `&p=${currentPage.value}` : ''
  return `https://www.bilibili.com/blackboard/html5mobileplayer.html?bvid=${props.bvid}${pageParam}&danmaku=0&playsinline=1`
})

function formatNum(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return String(n)
}

function goAuthor(mid) { if (mid) router.push(`/user/${mid}`) }

// 切换合集/选集视频
function switchCollectionItem(v) {
  if (isMultiP.value && v.page) {
    currentPage.value = v.page
    if (closeMiniPlayer) closeMiniPlayer()
  } else if (v.bvid && v.bvid !== props.bvid) {
    router.push(`/play/${v.bvid}`)
  }
}

// 播放下一集
function playNext() {
  const next = nextEpisode.value
  if (!next) {
    showToast('✅ 已是最后一集')
    return
  }
  showToast(`▶ 下一集: ${next.title}`)
  if (closeMiniPlayer) closeMiniPlayer()

  if (next.type === 'page') {
    currentPage.value = next.page
  } else {
    router.push(`/play/${next.bvid}`)
  }
}

async function addToCollection(video) {
  try {
    await api.addCollection({
      bvid: video.bvid, title: video.title, author: video.author,
      author_mid: video.author_mid, pic: video.pic,
      duration: video.duration, description: video.description,
      play_count: video.play_count, pubdate: video.pubdate,
    })
    isCollected.value = true; showToast('已收藏 ⭐'); loadMyCollection()
  } catch (e) { showToast(e.message) }
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
  } catch (e) { showToast(e.message) }
  finally { loading.value = false }
}

async function loadMyCollection() {
  try {
    const res = await api.listCollection({ page_size: 20 })
    myCollection.value = res.items.filter(v => v.bvid !== props.bvid)
  } catch (e) {}
}

onMounted(() => {
  loadDetail(); loadMyCollection()
})

// 离开播放页（被 keep-alive 隐藏）时自动进入迷你播放器
onDeactivated(() => {
  if (detail.value && props.bvid && openMiniPlayer) {
    openMiniPlayer(props.bvid, detail.value.title)
  }
})

// 回到播放页时关闭迷你播放器，iframe 回到全屏
onActivated(() => {
  if (closeMiniPlayer) closeMiniPlayer()
})

// 切换视频（点击侧边栏其他视频或路由切换 BVID）时关闭小窗，新视频全屏播放
watch(() => props.bvid, (newBvid, oldBvid) => {
  if (newBvid && newBvid !== oldBvid) {
    currentPage.value = 1
    if (closeMiniPlayer) closeMiniPlayer()
    const inCollection = collection.value?.videos?.some(v => v.bvid === newBvid)
    loadDetail(inCollection)
    loadMyCollection()
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

.player-wrap {
  position: relative; width: 100%; padding-top: 56.25%;
  background: #000; border-radius: 14px; overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}
.player-wrap iframe { position: absolute; inset: 0; width: 100%; height: 100%; }

.teleport-placeholder {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: #1a1a2e; color: rgba(255,255,255,0.6);
  font-size: 14px; border-radius: 14px;
}

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

/* 最后一集提示 */
.end-panel {
  margin-top: 16px; padding: 14px 18px;
  background: linear-gradient(135deg, #F0FDF4, #DCFCE7);
  border: 1px solid #BBF7D0; border-radius: 12px;
  text-align: center;
}
.end-tip { font-size: 13px; color: #16A34A; font-weight: 600; }

/* 侧边栏 */
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

/* 合集列表 */
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
