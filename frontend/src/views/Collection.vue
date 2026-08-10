<template>
  <div class="collection-page">
    <div class="page-header">
      <h2>⭐ 我的收藏</h2>
      <div class="header-actions" v-if="activeTab === 'local'">
        <span class="count">{{ total }} 个视频</span>
        <button class="btn-ghost" @click="exportData">📤 导出</button>
        <button class="btn-ghost" @click="triggerImport">📥 导入</button>
        <input type="file" ref="importFile" accept=".json" style="display:none" @change="importData">
      </div>
      <div class="header-actions" v-else-if="activeTab === 'bili' && currentFolder">
        <button class="btn-ghost" @click="currentFolder = null">← 返回收藏夹列表</button>
        <span class="count">{{ currentFolder.title }}</span>
      </div>
    </div>

    <div class="tabs">
      <span class="tab" :class="{active: activeTab === 'local'}" @click="activeTab = 'local'">本地收藏</span>
      <span class="tab" :class="{active: activeTab === 'bili'}" @click="switchToBili">B站收藏夹</span>
    </div>

    <!-- ====== 本地收藏 ====== -->
    <template v-if="activeTab === 'local'">
      <div class="filter-bar">
        <div class="author-filter">
          <span class="filter-chip" :class="{active: !currentAuthor}" @click="filterAuthor(null)">全部</span>
          <span v-for="a in authors" :key="a.name" class="filter-chip" :class="{active: currentAuthor === a.name}" @click="filterAuthor(a.name)">{{ a.name }} <em>{{ a.count }}</em></span>
        </div>
        <input v-model="keyword" placeholder="搜索收藏..." class="filter-input" @input="onSearch">
      </div>

      <div v-if="loading" class="state"><span class="spinner"></span>加载中...</div>
      <div v-else-if="items.length === 0" class="state empty">
        <div class="st-icon">📭</div>
        <p>还没有收藏任何视频</p>
        <span class="st-sub">去首页搜索并添加你喜欢的视频吧</span>
      </div>
      <div v-else class="video-grid">
        <VideoCard
          v-for="v in items" :key="v.bvid" :video="v"
          show-delete show-status
          @click="goPlay"
          @delete="removeItem"
          @author="goAuthor"
          @cycleStatus="cycleStatus"
        />
      </div>
    </template>

    <!-- ====== B站收藏夹 ====== -->
    <template v-if="activeTab === 'bili'">
      <div v-if="!biliUser" class="state empty">
        <div class="st-icon">🔒</div>
        <p>请先登录B站</p>
        <span class="st-sub">登录后即可查看你在B站上的收藏夹</span>
      </div>

      <div v-else-if="!currentFolder">
        <div v-if="biliLoading" class="state"><span class="spinner"></span>加载中...</div>
        <div v-else-if="folders.length === 0" class="state empty">
          <div class="st-icon">📭</div>
          <p>没有找到B站收藏夹</p>
        </div>
        <div v-else class="folder-grid">
          <div v-for="f in folders" :key="f.id" class="folder-card" @click="openFolder(f)">
            <div class="folder-cover">
              <img v-if="f.cover" :src="proxyImage(f.cover)" loading="lazy">
              <span v-else class="folder-ph">📁</span>
            </div>
            <div class="folder-info">
              <h4>{{ f.title }}</h4>
              <span class="folder-count">{{ f.media_count }} 个视频</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else>
        <div v-if="biliLoading" class="state"><span class="spinner"></span>加载中...</div>
        <div v-else-if="folderVideos.length === 0" class="state empty">
          <div class="st-icon">📭</div>
          <p>该收藏夹为空</p>
        </div>
        <div v-else class="video-grid">
          <VideoCard
            v-for="v in folderVideos" :key="v.bvid" :video="v"
            show-collect
            @click="goPlay"
            @collect="addToLocal"
            @author="goAuthor"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, inject, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, proxyImage } from '../api.js'
import VideoCard from '../components/VideoCard.vue'

const router = useRouter()
const showToast = inject('showToast')
const biliUser = inject('biliUser')
const dataVersion = inject('dataVersion')

const activeTab = ref('local')
const items = ref([])
const authors = ref([])
const total = ref(0)
const loading = ref(false)
const currentAuthor = ref(null)
const keyword = ref('')
const importFile = ref(null)
let searchTimer

const folders = ref([])
const currentFolder = ref(null)
const folderVideos = ref([])
const biliLoading = ref(false)

function goPlay(video) { router.push(`/play/${video.bvid}`) }
function goAuthor(video) {
  if (video.author_mid) router.push(`/user/${video.author_mid}`)
}

const STATUS_CYCLE = { todo: 'in_progress', in_progress: 'done', done: 'todo' }
async function cycleStatus(video) {
  const newStatus = STATUS_CYCLE[video.status] || 'todo'
  try {
    await api.updateCollection(video.bvid, { status: newStatus })
    video.status = newStatus
    showToast(`已标记为: ${newStatus === 'todo' ? '待学习' : newStatus === 'in_progress' ? '学习中' : '已完成'}`)
  } catch (e) {
    showToast(e.message)
  }
}

function filterAuthor(name) { currentAuthor.value = name; loadData() }
function onSearch() { clearTimeout(searchTimer); searchTimer = setTimeout(loadData, 300) }

async function loadData() {
  loading.value = true
  try {
    const params = { page_size: 100 }
    if (currentAuthor.value) params.author = currentAuthor.value
    if (keyword.value) params.keyword = keyword.value
    const res = await api.listCollection(params)
    items.value = res.items; total.value = res.total
  } catch (e) { showToast(e.message) }
  finally { loading.value = false }
}

async function loadAuthors() {
  try { authors.value = await api.getAuthors() } catch (e) {}
}

async function removeItem(bvid) {
  if (!confirm('确定删除吗？')) return
  try { await api.deleteCollection(bvid); showToast('已删除'); loadData(); loadAuthors() }
  catch (e) { showToast(e.message) }
}

async function exportData() {
  try {
    const data = await api.exportCollection()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `bilistudio-${new Date().toISOString().slice(0,10)}.json`
    a.click(); showToast('导出成功')
  } catch (e) { showToast(e.message) }
}

function triggerImport() { importFile.value.click() }

async function importData(e) {
  const file = e.target.files[0]; if (!file) return
  const reader = new FileReader()
  reader.onload = async () => {
    try {
      const data = JSON.parse(reader.result)
      if (!Array.isArray(data)) throw new Error('格式错误')
      const res = await api.importCollection(data)
      showToast(`成功导入 ${res.imported} 个视频`)
      loadData(); loadAuthors()
    } catch (err) { showToast('导入失败: ' + err.message) }
  }
  reader.readAsText(file); e.target.value = ''
}

async function switchToBili() { activeTab.value = 'bili'; if (biliUser.value) await loadFolders() }

async function loadFolders() {
  biliLoading.value = true
  try { const res = await api.favorites(); folders.value = res.folders || [] }
  catch (e) { showToast(e.message) }
  finally { biliLoading.value = false }
}

async function openFolder(folder) {
  currentFolder.value = folder; biliLoading.value = true
  try { const res = await api.favoriteContent(folder.id); folderVideos.value = res.videos || [] }
  catch (e) { showToast(e.message) }
  finally { biliLoading.value = false }
}

async function addToLocal(video) {
  try { await api.addCollection({ bvid: video.bvid, title: video.title, author: video.author, author_mid: video.author_mid, pic: video.pic }); showToast('已添加到本地收藏') }
  catch (e) { showToast(e.message) }
}

onMounted(() => { loadData(); loadAuthors() })
watch(dataVersion, () => { loadData(); loadAuthors() })
</script>

<style scoped>
.page-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; flex-wrap: wrap; gap: 10px;
}
.page-header h2 { font-size: 22px; font-weight: 700; }
.header-actions { display: flex; gap: 8px; align-items: center; }
.count { font-size: 13px; color: #94A3B8; font-weight: 500; }
.btn-ghost {
  padding: 6px 14px; border-radius: 8px; border: 1px solid #E2E8F0;
  background: #fff; font-size: 13px; cursor: pointer; color: #64748B;
  font-weight: 500; font-family: inherit; transition: all .15s;
}
.btn-ghost:hover { border-color: #FF6B35; color: #FF6B35; }

/* 标签页 */
.tabs { display: flex; gap: 4px; margin-bottom: 20px; border-bottom: 2px solid #F1F5F9; }
.tab {
  padding: 10px 20px; font-size: 14px; color: #94A3B8;
  cursor: pointer; border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: all .15s; font-weight: 500;
}
.tab:hover { color: #FF6B35; }
.tab.active { color: #FF6B35; border-bottom-color: #FF6B35; font-weight: 700; }

/* 筛选栏 */
.filter-bar {
  display: flex; gap: 12px; margin-bottom: 20px;
  flex-wrap: wrap; align-items: center;
  background: #fff; padding: 12px 16px; border-radius: 12px;
  border: 1px solid #F1F5F9;
}
.author-filter { display: flex; gap: 6px; flex-wrap: wrap; flex: 1; }
.filter-chip {
  padding: 5px 12px; border-radius: 18px; font-size: 13px;
  background: #F8FAFC; color: #64748B;
  cursor: pointer; border: 1px solid #E2E8F0; transition: all .15s;
  font-weight: 500;
}
.filter-chip em { font-style: normal; color: #CBD5E1; margin-left: 2px; }
.filter-chip:hover { border-color: #FF6B35; color: #FF6B35; }
.filter-chip.active {
  background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
  border-color: #FF6B35; color: #FF6B35; font-weight: 600;
}
.filter-input {
  padding: 8px 14px; border: 1px solid #E2E8F0;
  border-radius: 10px; font-size: 14px; outline: none;
  width: 200px; background: #F8FAFC; font-family: inherit;
  transition: all .2s;
}
.filter-input:focus { border-color: #FF6B35; background: #fff; box-shadow: 0 0 0 3px rgba(255,107,53,0.08); }

/* 视频网格 */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

/* 收藏夹网格 */
.folder-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.folder-card {
  background: #fff; border-radius: 14px; overflow: hidden;
  border: 1px solid #F1F5F9; cursor: pointer;
  transition: all .2s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.03);
}
.folder-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 28px rgba(0,0,0,0.08);
  border-color: #FFE0B2;
}
.folder-cover {
  width: 100%; aspect-ratio: 16/10;
  background: #F1F5F9;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden;
}
.folder-cover img { width: 100%; height: 100%; object-fit: cover; }
.folder-ph { font-size: 40px; opacity: 0.5; }
.folder-info { padding: 12px 14px; }
.folder-info h4 { font-size: 14px; font-weight: 600; color: #2C3E50; margin: 0 0 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.folder-count { font-size: 12px; color: #94A3B8; }

/* 状态 */
.state {
  text-align: center; padding: 60px 20px; color: #94A3B8;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.state.empty { padding: 80px 20px; }
.st-icon { font-size: 48px; }
.st-sub { font-size: 13px; color: #CBD5E1; }
.spinner {
  width: 24px; height: 24px; border: 3px solid #E2E8F0;
  border-top-color: #FF6B35; border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
