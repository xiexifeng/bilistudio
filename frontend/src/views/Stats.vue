<template>
  <div class="stats-page">
    <div class="page-header">
      <h2>📊 学习统计</h2>
      <span class="subtitle">当前用户: {{ currentUserName }}</span>
    </div>

    <div v-if="loading" class="state"><span class="spinner"></span>加载中...</div>
    <div v-else-if="error" class="state error">{{ error }}</div>
    <div v-else>
      <!-- 概览卡片 -->
      <div class="stats-cards">
        <div class="stat-card orange">
          <div class="sc-icon">📚</div>
          <div class="sc-value">{{ stats.total_collection }}</div>
          <div class="sc-label">总收藏</div>
        </div>
        <div class="stat-card blue">
          <div class="sc-icon">📝</div>
          <div class="sc-value">{{ stats.todo_count }}</div>
          <div class="sc-label">待学习</div>
        </div>
        <div class="stat-card purple">
          <div class="sc-icon">▶️</div>
          <div class="sc-value">{{ stats.in_progress_count }}</div>
          <div class="sc-label">学习中</div>
        </div>
        <div class="stat-card green">
          <div class="sc-icon">✅</div>
          <div class="sc-value">{{ stats.done_count }}</div>
          <div class="sc-label">已完成</div>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-section" v-if="stats.total_collection > 0">
        <div class="progress-bar-wrap">
          <div class="progress-bar">
            <div class="bar-seg done" :style="{width: donePct + '%'}"></div>
            <div class="bar-seg doing" :style="{width: doingPct + '%'}"></div>
            <div class="bar-seg todo" :style="{width: todoPct + '%'}"></div>
          </div>
        </div>
        <div class="progress-legend">
          <span><b class="c-done"></b> 已完成 {{ donePct }}%</span>
          <span><b class="c-doing"></b> 学习中 {{ doingPct }}%</span>
          <span><b class="c-todo"></b> 待学习 {{ todoPct }}%</span>
        </div>
      </div>

      <!-- 活跃度 -->
      <div class="section">
        <div class="section-header">
          <h3>📅 最近30天</h3>
        </div>
        <div class="activity-card">
          <div class="big-num">{{ stats.recent_days }}</div>
          <div class="big-label">天有收藏活动</div>
          <p class="activity-note" v-if="stats.recent_days < 3">加油！每天坚持收藏和学习，积少成多 💪</p>
          <p class="activity-note" v-else-if="stats.recent_days < 10">不错哦，保持节奏 👏</p>
          <p class="activity-note" v-else>太棒了，学习已成习惯！🌟</p>
        </div>
      </div>

      <!-- 按作者分布 -->
      <div class="section" v-if="stats.by_author.length > 0">
        <div class="section-header">
          <h3>👤 收藏最多的UP主</h3>
        </div>
        <div class="author-chart">
          <div v-for="(a, i) in stats.by_author" :key="a.author" class="author-bar-wrap">
            <div class="author-rank">{{ i + 1 }}</div>
            <div class="author-name">{{ a.author }}</div>
            <div class="author-bar-bg">
              <div class="author-bar-fill" :style="{width: barWidth(i) + '%'}"></div>
            </div>
            <div class="author-count">{{ a.count }}个</div>
          </div>
        </div>
      </div>

      <!-- 无数据提示 -->
      <div v-if="stats.total_collection === 0" class="state empty">
        <div class="st-icon">📭</div>
        <p>还没有任何学习数据</p>
        <span class="st-sub">去首页搜索并收藏感兴趣的视频吧</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject, watch } from 'vue'
import { api } from '../api.js'

const showToast = inject('showToast')
const currentUserId = inject('currentUserId')
const dataVersion = inject('dataVersion')

const stats = ref({ total_collection: 0, todo_count: 0, in_progress_count: 0, done_count: 0, by_author: [], recent_days: 0, total_users: 0 })
const loading = ref(true)
const error = ref('')

const currentUserName = computed(() => {
  // 从全局状态获取用户名（实际通过 App.vue 的 currentUser 提供）
  return ''
})

const donePct = computed(() => stats.value.total_collection > 0 ? Math.round(stats.value.done_count / stats.value.total_collection * 100) : 0)
const doingPct = computed(() => stats.value.total_collection > 0 ? Math.round(stats.value.in_progress_count / stats.value.total_collection * 100) : 0)
const todoPct = computed(() => 100 - donePct.value - doingPct.value)

function barWidth(i) {
  const max = stats.value.by_author[0]?.count || 1
  return Math.round(stats.value.by_author[i].count / max * 100)
}

async function loadStats() {
  loading.value = true
  error.value = ''
  try {
    stats.value = await api.getStats()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
watch(dataVersion, loadStats)
</script>

<style scoped>
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 700; color: #2C3E50; }
.subtitle { font-size: 13px; color: #94A3B8; }

/* 卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 14px; margin-bottom: 28px;
}
.stat-card {
  background: #fff; border-radius: 16px; padding: 20px;
  text-align: center; border: 1px solid #F1F5F9;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: transform .2s;
}
.stat-card:hover { transform: translateY(-3px); }
.sc-icon { font-size: 32px; margin-bottom: 8px; }
.sc-value { font-size: 36px; font-weight: 800; color: #2C3E50; }
.sc-label { font-size: 13px; color: #94A3B8; margin-top: 4px; font-weight: 500; }

.stat-card.orange { border-top: 3px solid #FF6B35; }
.stat-card.blue { border-top: 3px solid #45B7D1; }
.stat-card.purple { border-top: 3px solid #8B5CF6; }
.stat-card.green { border-top: 3px solid #10B981; }

/* 进度条 */
.progress-section { margin-bottom: 28px; }
.progress-bar-wrap {
  background: #fff; border-radius: 14px; padding: 20px 24px;
  border: 1px solid #F1F5F9; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.progress-bar {
  height: 12px; border-radius: 6px; overflow: hidden;
  background: #F1F5F9; display: flex;
}
.bar-seg { height: 100%; transition: width .5s ease; }
.bar-seg.done { background: linear-gradient(90deg, #10B981, #34D399); }
.bar-seg.doing { background: linear-gradient(90deg, #8B5CF6, #A78BFA); }
.bar-seg.todo { background: #E2E8F0; }

.progress-legend {
  display: flex; gap: 20px; margin-top: 10px;
  font-size: 13px; color: #64748B;
}
.progress-legend b {
  display: inline-block; width: 10px; height: 10px; border-radius: 2px;
  margin-right: 4px; vertical-align: middle;
}
.c-done { background: #10B981; }
.c-doing { background: #8B5CF6; }
.c-todo { background: #E2E8F0; }

/* 活跃度 */
.section { margin-bottom: 28px; }
.section-header { margin-bottom: 12px; }
.section-header h3 { font-size: 16px; font-weight: 700; color: #2C3E50; }

.activity-card {
  background: #fff; border-radius: 14px; padding: 28px 24px;
  text-align: center; border: 1px solid #F1F5F9;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.big-num { font-size: 48px; font-weight: 800; color: #FF6B35; }
.big-label { font-size: 14px; color: #64748B; margin: 4px 0 10px; }
.activity-note { font-size: 13px; color: #94A3B8; }

/* 作者排行 */
.author-chart { background: #fff; border-radius: 14px; padding: 16px 20px; border: 1px solid #F1F5F9; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.author-bar-wrap { display: flex; align-items: center; gap: 10px; padding: 6px 0; }
.author-rank {
  width: 24px; height: 24px; border-radius: 6px;
  background: #F1F5F9; display: flex; align-items: center;
  justify-content: center; font-size: 12px; font-weight: 700;
  color: #64748B; flex-shrink: 0;
}
.author-bar-wrap:nth-child(1) .author-rank { background: #FFE0B2; color: #FF6B35; }
.author-bar-wrap:nth-child(2) .author-rank { background: #E0E7FF; color: #6366F1; }
.author-bar-wrap:nth-child(3) .author-rank { background: #D1FAE5; color: #10B981; }
.author-name { width: 110px; font-size: 13px; font-weight: 500; color: #2C3E50; flex-shrink: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.author-bar-bg { flex: 1; height: 10px; background: #F1F5F9; border-radius: 5px; overflow: hidden; }
.author-bar-fill { height: 100%; background: linear-gradient(90deg, #FF6B35, #FF8F5E); border-radius: 5px; transition: width .5s ease; }
.author-count { width: 40px; font-size: 12px; font-weight: 700; color: #64748B; text-align: right; flex-shrink: 0; }

/* 状态 */
.state {
  text-align: center; padding: 60px 20px; color: #94A3B8;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.state.error { color: #EF4444; }
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
