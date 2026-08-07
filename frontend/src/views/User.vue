<template>
  <div class="user-page">
    <div v-if="loading" class="state"><span class="spinner"></span>加载中...</div>
    <template v-else>
      <div class="user-header">
        <img v-if="userInfo.face" :src="proxyImage(userInfo.face)" class="user-avatar">
        <div v-else class="user-avatar-placeholder">{{ userInfo.name?.charAt(0) }}</div>
        <div class="user-info">
          <h2>{{ userInfo.name }}</h2>
          <p class="user-sign">{{ userInfo.sign || '这个人很懒，什么都没有写' }}</p>
          <span class="follower">👥 {{ formatNum(userInfo.follower) }} 粉丝</span>
        </div>
      </div>

      <h3 class="section-title">
        📹 全部视频 <span class="total-badge">{{ total }}</span>
        <button class="source-toggle" @click="toggleSource" :title="source === 'wbi' ? '当前: WBI签名接口（备选）' : '当前: 普通接口'">
          {{ source === 'wbi' ? '🔐 WBI' : '📡 默认' }}
        </button>
      </h3>

      <div v-if="error" class="state error">{{ error }}</div>

      <div v-else-if="videos.length === 0 && !loading" class="state empty">该UP主暂无视频</div>
      <div v-else class="video-grid">
        <VideoCard
          v-for="v in videos" :key="v.bvid"
          :video="v"
          show-collect
          @click="goPlay"
          @collect="addToCollection"
        />
      </div>

      <div v-if="totalPages > 1 && !error" class="pagination">
        <button :disabled="page <= 1" @click="changePage(page-1)">‹ 上一页</button>
        <span class="page-info">{{ page }} / {{ totalPages }}</span>
        <button :disabled="page >= totalPages" @click="changePage(page+1)">下一页 ›</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { api, proxyImage } from '../api.js'
import VideoCard from '../components/VideoCard.vue'

const props = defineProps({ mid: String })
const router = useRouter()
const showToast = inject('showToast')

const userInfo = ref({})
const videos = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 30
const loading = ref(true)
const error = ref('')
const source = ref(localStorage.getItem('upvideo_source') || 'default')

const totalPages = computed(() => Math.ceil(total.value / pageSize))

function formatNum(n) { if (!n) return '0'; if (n >= 10000) return (n / 10000).toFixed(1) + '万'; return String(n) }

function goPlay(video) { router.push(`/play/${video.bvid}`) }

async function addToCollection(video) {
  try {
    await api.addCollection({
      bvid: video.bvid, title: video.title, author: video.author,
      author_mid: video.author_mid, pic: video.pic,
      duration: video.duration, description: video.description,
      play_count: video.play_count, pubdate: video.pubdate,
    })
    showToast('已收藏 ⭐')
  } catch (e) { showToast(e.message) }
}

async function loadData() {
  loading.value = true; error.value = ''
  try {
    const mid = parseInt(props.mid)
    // 串行请求，避免同时打 B站触发风控
    const uRes = await api.userInfo(mid)
    const vRes = await api.userVideos(mid, page.value, source.value)
    userInfo.value = uRes; videos.value = vRes.videos; total.value = vRes.total
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

function changePage(p) { page.value = p; loadData(); window.scrollTo({ top: 0, behavior: 'smooth' }) }

function toggleSource() {
  source.value = source.value === 'wbi' ? 'default' : 'wbi'
  localStorage.setItem('upvideo_source', source.value)
  page.value = 1
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.user-page { max-width: 1200px; }

.user-header {
  display: flex; gap: 24px; align-items: center;
  background: #fff; padding: 28px; border-radius: 18px;
  margin-bottom: 24px;
  border: 1px solid #F1F5F9;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.user-avatar, .user-avatar-placeholder {
  width: 88px; height: 88px; border-radius: 50%;
  object-fit: cover; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.user-avatar-placeholder {
  background: linear-gradient(135deg, #FF6B35, #FF8F5E);
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 32px; font-weight: 700;
}
.user-info { flex: 1; }
.user-info h2 { font-size: 24px; font-weight: 700; margin-bottom: 6px; color: #2C3E50; }
.user-sign { font-size: 14px; color: #64748B; margin-bottom: 10px; line-height: 1.5; }
.follower { font-size: 13px; color: #FF6B35; background: #FFF3E0; padding: 4px 14px; border-radius: 20px; font-weight: 600; }

.section-title { font-size: 17px; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.total-badge {
  font-size: 12px; color: #94A3B8; background: #F1F5F9;
  padding: 2px 10px; border-radius: 12px; font-weight: 500;
}
.source-toggle {
  margin-left: auto; font-size: 11px; padding: 3px 12px;
  border: 1px solid #E2E8F0; background: #fff; border-radius: 14px;
  cursor: pointer; color: #64748B; font-family: inherit;
  transition: all .15s; white-space: nowrap;
}
.source-toggle:hover { border-color: #45B7D1; color: #45B7D1; background: #F0FAFF; }

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.pagination {
  display: flex; align-items: center; justify-content: center;
  gap: 16px; margin-top: 28px;
}
.pagination button {
  padding: 10px 22px; border: 1px solid #E2E8F0;
  background: #fff; border-radius: 10px; cursor: pointer;
  font-size: 14px; font-weight: 500; color: #64748B; font-family: inherit;
  transition: all .15s;
}
.pagination button:hover:not(:disabled) { border-color: #FF6B35; color: #FF6B35; }
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.page-info { font-size: 14px; font-weight: 500; color: #64748B; }

.state { text-align: center; padding: 60px 20px; color: #94A3B8; display: flex; align-items: center; justify-content: center; gap: 8px; }
.state.error { color: #EF4444; }
.state.empty { padding: 80px 20px; font-size: 15px; }
.spinner {
  width: 22px; height: 22px; border: 3px solid #E2E8F0;
  border-top-color: #FF6B35; border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
