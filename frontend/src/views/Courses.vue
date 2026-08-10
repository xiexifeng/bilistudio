<template>
  <div class="courses-page">
    <div class="page-header">
      <h2>📖 学习路线</h2>
      <span class="subtitle">选择一个路线，收藏视频后打卡完成</span>
    </div>

    <div class="paths-grid">
      <div v-for="path in paths" :key="path.id" class="path-card" :style="{borderTopColor: path.color}">
        <div class="path-header" @click="toggleExpand(path.id)">
          <div class="path-icon-bg" :style="{background: path.bg}">
            <span class="path-icon">{{ path.title.slice(0, 2) }}</span>
          </div>
          <div class="path-meta">
            <h3>{{ path.title }}</h3>
            <p>{{ path.desc }}</p>
          </div>
          <div class="path-progress-badge">
            <span class="progress-text">{{ pathProgress(path.id).done }}/{{ path.stages.length }}</span>
          </div>
          <span class="expand-icon" :class="{expanded: expanded === path.id}">▾</span>
        </div>

        <div v-if="expanded === path.id" class="stages-list">
          <div v-for="stage in path.stages" :key="stage.id" class="stage-item" :class="{done: isStageDone(path.id, stage.id)}">
            <div class="stage-check" @click="toggleStage(path.id, stage.id)">
              <span v-if="isStageDone(path.id, stage.id)" class="check-icon">✓</span>
              <span v-else class="check-empty"></span>
            </div>
            <div class="stage-info">
              <h4>{{ stage.title }}</h4>
              <p>{{ stage.desc }}</p>
            </div>
            <div class="stage-actions">
              <button class="stage-btn" @click="searchStage(stage.search)">🔍 搜索相关视频</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="section" v-if="!loading">
      <div class="tip-card">
        <h4>💡 使用技巧</h4>
        <ul>
          <li>展开路线后，点击"搜索相关视频"可以找到适合的学习内容</li>
          <li>将视频加入收藏后，在这里打卡标记完成</li>
          <li>每条路线可以按照自己的节奏学习，不一定要按顺序</li>
          <li>在<a href="#/stats">统计页面</a>可以查看整体学习进度</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api.js'
import { learningPaths } from '../curated.js'

const router = useRouter()
const paths = learningPaths
const expanded = ref(null)
const progressData = ref({})
const loading = ref(true)
const dataVersion = inject('dataVersion')

function toggleExpand(id) {
  expanded.value = expanded.value === id ? null : id
}

async function loadProgress() {
  loading.value = true
  try {
    const data = await api.getCourseProgress()
    const map = {}
    for (const p of data) {
      const stages = {}
      for (const s of p.stages) {
        stages[s.stage_id] = s.completed
      }
      map[p.path_id] = stages
    }
    progressData.value = map
  } catch (e) {
    // 静默处理，不影响浏览路线
  } finally {
    loading.value = false
  }
}

function pathProgress(pathId) {
  const path = paths.find(p => p.id === pathId)
  const done = path ? path.stages.filter(s => isStageDone(pathId, s.id)).length : 0
  return { done, total: path?.stages.length || 0 }
}

function isStageDone(pathId, stageId) {
  return progressData.value[pathId]?.[stageId] || false
}

async function toggleStage(pathId, stageId) {
  const newCompleted = !isStageDone(pathId, stageId)
  try {
    await api.updateStageProgress(pathId, stageId, newCompleted)
    if (!progressData.value[pathId]) progressData.value[pathId] = {}
    progressData.value[pathId][stageId] = newCompleted
  } catch (e) {
    // 静默处理
  }
}

function searchStage(query) {
  router.push({ path: '/', query: { q: query } })
}

onMounted(loadProgress)
watch(dataVersion, loadProgress)
</script>

<style scoped>
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 700; color: #2C3E50; }
.subtitle { font-size: 13px; color: #94A3B8; }

.paths-grid { display: flex; flex-direction: column; gap: 14px; margin-bottom: 28px; }

.path-card {
  background: #fff; border-radius: 16px;
  border: 1px solid #F1F5F9;
  border-top: 4px solid #FF6B35;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  overflow: hidden; transition: box-shadow .2s;
}
.path-card:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.08); }

.path-header {
  display: flex; align-items: center; gap: 14px;
  padding: 18px 20px; cursor: pointer; user-select: none;
  transition: background .15s;
}
.path-header:hover { background: #FAFBFC; }

.path-icon-bg {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.path-icon { font-size: 20px; }

.path-meta { flex: 1; min-width: 0; }
.path-meta h3 { font-size: 16px; font-weight: 700; color: #2C3E50; }
.path-meta p { font-size: 13px; color: #94A3B8; margin-top: 2px; }

.path-progress-badge {
  padding: 4px 12px; border-radius: 14px;
  background: #F8FAFC; border: 1px solid #E2E8F0;
}
.progress-text { font-size: 13px; font-weight: 700; color: #FF6B35; }

.expand-icon {
  font-size: 14px; color: #94A3B8; transition: transform .25s;
}
.expand-icon.expanded { transform: rotate(180deg); }

/* 关卡列表 */
.stages-list { border-top: 1px solid #F1F5F9; }
.stage-item {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 20px; border-bottom: 1px solid #F8FAFC;
  transition: background .12s;
}
.stage-item:last-child { border-bottom: none; }
.stage-item:hover { background: #FAFBFC; }

.stage-check {
  width: 28px; height: 28px; border-radius: 50%;
  cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s;
}
.check-empty {
  width: 22px; height: 22px; border-radius: 50%;
  border: 2px solid #E2E8F0; transition: all .2s;
}
.stage-check:hover .check-empty { border-color: #10B981; }
.check-icon {
  width: 28px; height: 28px; border-radius: 50%;
  background: #10B981; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700;
}

.stage-item.done .stage-info h4 { color: #94A3B8; text-decoration: line-through; }
.stage-item.done .stage-info p { color: #CBD5E1; }

.stage-info { flex: 1; min-width: 0; }
.stage-info h4 { font-size: 14px; font-weight: 600; color: #2C3E50; }
.stage-info p { font-size: 12px; color: #94A3B8; margin-top: 2px; }

.stage-actions { flex-shrink: 0; }
.stage-btn {
  padding: 6px 14px; border-radius: 8px; border: 1px solid #E2E8F0;
  background: #fff; font-size: 12px; color: #45B7D1; cursor: pointer;
  font-weight: 500; font-family: inherit; transition: all .15s;
}
.stage-btn:hover { border-color: #45B7D1; background: #E0F7FA; }

/* 技巧卡片 */
.tip-card {
  background: linear-gradient(135deg, #FFF3E0, #fff);
  border-radius: 14px; padding: 20px 24px;
  border: 1px solid #FFE0B2;
}
.tip-card h4 { font-size: 15px; color: #2C3E50; margin-bottom: 10px; }
.tip-card ul { padding-left: 18px; font-size: 13px; color: #64748B; line-height: 1.8; }
.tip-card a { color: #FF6B35; text-decoration: none; font-weight: 600; }
.tip-card a:hover { text-decoration: underline; }

.section { margin-top: 8px; }
</style>
