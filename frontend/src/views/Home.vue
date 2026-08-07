<template>
  <div class="home">
    <!-- ==== 未搜索时：展示推荐内容 ==== -->
    <template v-if="!hasSearched">
      <!-- 精选UP主 -->
      <section class="section">
        <div class="section-header">
          <h2>🌟 精选教育UP主</h2>
          <span class="section-sub">优质内容，适合小学到初中</span>
        </div>
        <div class="uper-grid">
          <div
            v-for="u in curatedUpers"
            :key="u.mid"
            class="uper-card"
            @click="goAuthor(u)"
          >
            <div class="uper-icon">{{ u.icon }}</div>
            <div class="uper-info">
              <h3 class="uper-name">{{ u.name }}</h3>
              <span class="uper-category">{{ u.category }}</span>
              <p class="uper-desc">{{ u.desc }}</p>
              <div class="uper-tags">
                <span v-for="t in u.tags" :key="t" class="uper-tag">{{ t }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 分类快捷搜索 -->
      <section class="section">
        <div class="section-header">
          <h2>🔎 按分类探索</h2>
          <span class="section-sub">点击感兴趣的领域开始发现</span>
        </div>
        <div class="category-grid">
          <button
            v-for="cat in searchCategories"
            :key="cat.label"
            class="category-card"
            @click="searchTag(cat.query)"
          >
            <span class="cat-icon">{{ cat.label.slice(0, 2) }}</span>
            <span class="cat-label">{{ cat.label.slice(3) }}</span>
          </button>
        </div>
      </section>

      <!-- 底部引导 -->
      <div class="search-hero">
        <div class="search-hero-icon">🔍</div>
        <h3>或者直接搜索你感兴趣的内容</h3>
        <p>点击顶部搜索框，输入UP主名字或关键词</p>
      </div>
    </template>

    <!-- ==== 搜索结果显示 ==== -->
    <div v-else>
      <div class="result-header">
        <div>
          <h2>"{{ query }}" 的搜索结果</h2>
          <span class="result-count">共 {{ total }} 个视频（已过滤低质内容）</span>
        </div>
        <button class="btn-back" @click="clearSearch">返回推荐</button>
      </div>

      <div v-if="loading" class="loading-state">
        <span class="spinner"></span>
        搜索中...
      </div>
      <div v-else-if="error" class="error-state">{{ error }}</div>
      <div v-else-if="videos.length === 0" class="empty-state">
        <div class="empty-icon">🔍</div>
        <p>没有找到相关视频</p>
        <span class="sub">试试换个关键词</span>
      </div>
      <div v-else class="video-grid">
        <VideoCard
          v-for="v in videos" :key="v.bvid"
          :video="v"
          show-collect
          @click="goPlay"
          @collect="addToCollection"
          @author="goAuthor"
        />
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <button :disabled="page <= 1" @click="changePage(page-1)">‹ 上一页</button>
        <span class="page-info">{{ page }} / {{ totalPages }}</span>
        <button :disabled="page >= totalPages" @click="changePage(page+1)">下一页 ›</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api.js'
import { curatedUpers, searchCategories } from '../curated.js'
import VideoCard from '../components/VideoCard.vue'

const route = useRoute()
const router = useRouter()
const showToast = inject('showToast')

const query = ref('')
const videos = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const error = ref('')
const hasSearched = ref(false)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

let searchDebounce = null

function searchTag(tag) {
  router.push({ path: '/', query: { q: tag } })
}

function goPlay(video) {
  router.push(`/play/${video.bvid}`)
}

function goAuthor(author) {
  if (author.mid || author.author_mid) {
    router.push(`/user/${author.mid || author.author_mid}`)
  }
}

function clearSearch() {
  hasSearched.value = false
  videos.value = []
  router.push({ path: '/' })
}

async function addToCollection(video) {
  try {
    await api.addCollection({
      bvid: video.bvid,
      title: video.title,
      author: video.author,
      author_mid: video.author_mid,
      pic: video.pic,
      duration: video.duration,
      description: video.description,
      play_count: video.play_count,
      pubdate: video.pubdate,
    })
    showToast('已添加到收藏 ⭐')
  } catch (e) {
    showToast(e.message)
  }
}

async function doSearch() {
  if (!query.value.trim()) return
  loading.value = true
  error.value = ''
  hasSearched.value = true
  try {
    const res = await api.search(query.value, page.value)
    videos.value = res.videos
    total.value = res.total
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function changePage(p) {
  page.value = p
  doSearch()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(() => route.query.q, (q) => {
  clearTimeout(searchDebounce)
  if (q) {
    query.value = q
    page.value = 1
    searchDebounce = setTimeout(doSearch, 500)
  } else {
    hasSearched.value = false
    videos.value = []
  }
}, { immediate: true })
</script>

<style scoped>
/* ====== 区块 ====== */
.section { margin-bottom: 40px; }
.section-header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 20px; }
.section-header h2 { font-size: 20px; font-weight: 700; color: #2C3E50; }
.section-sub { font-size: 13px; color: #94A3B8; }

/* ====== 精选UP主卡片 ====== */
.uper-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.uper-card {
  background: #fff; border-radius: 16px; padding: 22px;
  cursor: pointer;
  display: flex; gap: 16px; align-items: flex-start;
  transition: all .25s;
  border: 1px solid #F1F5F9;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.uper-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
  border-color: #FFE0B2;
}
.uper-icon {
  font-size: 40px; width: 56px; height: 56px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
  border-radius: 14px; flex-shrink: 0;
}
.uper-info { flex: 1; min-width: 0; }
.uper-name {
  font-size: 16px; font-weight: 700; color: #2C3E50;
  margin-bottom: 4px;
}
.uper-category {
  display: inline-block; font-size: 11px; font-weight: 600;
  color: #FF6B35; background: #FFF3E0;
  padding: 2px 10px; border-radius: 10px; margin-bottom: 8px;
}
.uper-desc {
  font-size: 13px; color: #64748B; line-height: 1.5;
  margin-bottom: 10px;
}
.uper-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.uper-tag {
  font-size: 11px; color: #45B7D1; background: #E0F7FA;
  padding: 2px 8px; border-radius: 8px; font-weight: 500;
}

/* ====== 分类卡片 ====== */
.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}
.category-card {
  background: #fff; border: 1px solid #F1F5F9;
  border-radius: 14px; padding: 18px 16px;
  cursor: pointer; text-align: center;
  transition: all .2s;
  font-family: inherit;
  box-shadow: 0 2px 6px rgba(0,0,0,0.03);
}
.category-card:hover {
  border-color: #FF6B35;
  background: linear-gradient(135deg, #FFF8F3, #FFF);
  box-shadow: 0 6px 20px rgba(255,107,53,0.1);
  transform: translateY(-2px);
}
.cat-icon { font-size: 28px; display: block; margin-bottom: 8px; }
.cat-label { font-size: 14px; font-weight: 600; color: #2C3E50; }

/* ====== 搜索引导 ====== */
.search-hero {
  text-align: center; padding: 60px 20px 40px;
  color: #94A3B8;
}
.search-hero-icon { font-size: 40px; margin-bottom: 12px; }
.search-hero h3 { font-size: 17px; color: #64748B; margin-bottom: 6px; }
.search-hero p { font-size: 14px; }

/* ====== 搜索结果 ====== */
.result-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 20px; flex-wrap: wrap; gap: 10px;
}
.result-header h2 { font-size: 20px; font-weight: 700; }
.result-count { font-size: 13px; color: #94A3B8; display: block; margin-top: 2px; }
.btn-back {
  padding: 8px 18px; border: 1px solid #E2E8F0;
  background: #fff; border-radius: 10px; color: #64748B;
  font-size: 13px; cursor: pointer; font-weight: 500; font-family: inherit;
  transition: all .15s;
}
.btn-back:hover { border-color: #FF6B35; color: #FF6B35; }

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 18px;
}

.loading-state, .error-state, .empty-state {
  text-align: center; padding: 60px 20px; color: #94A3B8;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.error-state { color: #EF4444; }
.empty-icon { font-size: 48px; }
.sub { font-size: 13px; color: #CBD5E1; }

.spinner {
  width: 24px; height: 24px; border: 3px solid #E2E8F0;
  border-top-color: #FF6B35; border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.pagination {
  display: flex; align-items: center; justify-content: center;
  gap: 16px; margin-top: 32px;
}
.pagination button {
  padding: 10px 22px; border: 1px solid #E2E8F0;
  background: #fff; border-radius: 10px; cursor: pointer;
  font-size: 14px; font-weight: 500; color: #64748B;
  transition: all .15s; font-family: inherit;
}
.pagination button:hover:not(:disabled) { border-color: #FF6B35; color: #FF6B35; }
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.page-info { font-size: 14px; color: #64748B; font-weight: 500; }
</style>
