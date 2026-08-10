<template>
  <div class="video-card" @click="$emit('click', video)">
    <div class="cover-wrap">
      <img v-if="video.pic && !hasError" :src="proxyImage(video.pic)" :alt="video.title" loading="lazy" @error="hasError=true">
      <div v-else class="cover-placeholder">
        <span class="ph-icon">🎬</span>
      </div>
      <span v-if="video.duration" class="duration">{{ video.duration }}</span>
      <div class="cover-actions">
        <button v-if="showDelete" class="act-btn delete-btn" @click.stop="$emit('delete', video.bvid)" title="删除">×</button>
        <button v-if="showCollect" class="act-btn collect-btn" @click.stop="$emit('collect', video)" title="收藏">⭐</button>
      </div>
    </div>
    <div class="info">
      <h4 class="title" :title="video.title">{{ video.title }}</h4>
      <div class="meta">
        <span class="author" @click.stop="$emit('author', video)">{{ video.author }}</span>
        <span class="dot-sep">·</span>
        <span v-if="video.play_count" class="play">▶ {{ formatNum(video.play_count) }}</span>
      </div>
      <div v-if="video.note" class="note">{{ video.note }}</div>
      <div v-if="showStatus && video.status" class="status-row">
        <span class="status-tag" :class="'status-'+video.status" @click.stop="$emit('cycleStatus', video)">
          {{ statusLabel(video.status) }}
        </span>
        <span v-if="video.watch_progress > 0 && video.watch_progress < 100" class="progress-text">
          {{ video.watch_progress }}%
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { proxyImage } from '../api.js'

const props = defineProps({
  video: Object,
  showDelete: Boolean,
  showCollect: Boolean,
  showStatus: Boolean,
})
defineEmits(['click', 'delete', 'collect', 'author', 'cycleStatus'])
const hasError = ref(false)
function formatNum(n) {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return String(n)
}
function statusLabel(s) {
  const map = { todo: '待学习', in_progress: '学习中', done: '已完成' }
  return map[s] || s
}
</script>

<style scoped>
.video-card {
  background: #fff;
  border-radius: 14px;
  overflow: hidden;
  cursor: pointer;
  transition: all .25s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid #F1F5F9;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.video-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.1);
  border-color: #FFE0B2;
}
.cover-wrap {
  position: relative;
  width: 100%;
  padding-top: 56.25%;
  background: #F1F5F9;
  overflow: hidden;
}
.cover-wrap img, .cover-placeholder {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
}
.cover-wrap img { object-fit: cover; transition: transform .3s; }
.video-card:hover .cover-wrap img { transform: scale(1.05); }
.cover-placeholder {
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #F1F5F9, #E2E8F0);
}
.ph-icon { font-size: 42px; opacity: 0.5; }

.duration {
  position: absolute; bottom: 8px; right: 8px;
  background: rgba(0,0,0,0.75); color: #fff;
  font-size: 11px; font-weight: 600; padding: 2px 7px;
  border-radius: 5px; letter-spacing: 0.3px;
}

.cover-actions { position: absolute; top: 8px; right: 8px; display: flex; gap: 4px; opacity: 0; transition: opacity .2s; }
.video-card:hover .cover-actions { opacity: 1; }
.act-btn {
  width: 30px; height: 30px; border-radius: 50%;
  border: none; color: #fff; font-size: 14px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all .15s; backdrop-filter: blur(4px);
}
.delete-btn { background: rgba(0,0,0,0.5); }
.delete-btn:hover { background: #EF4444; transform: scale(1.1); }
.collect-btn {
  background: rgba(255,107,53,0.75); font-size: 12px;
  right: 38px;
}
.collect-btn:hover { background: #FF6B35; transform: scale(1.1); }

/* info */
.info { padding: 12px 14px 14px; }
.title {
  font-size: 14px; font-weight: 600; line-height: 1.45;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; min-height: 40px; margin-bottom: 8px; color: #2C3E50;
}
.meta {
  font-size: 12px; color: #94A3B8;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
}
.author {
  color: #FF6B35; cursor: pointer; font-weight: 600;
  padding: 1px 6px; border-radius: 4px; background: #FFF3E0;
  transition: background .15s;
}
.author:hover { background: #FFE0B2; }
.dot-sep { color: #CBD5E1; }
.note { margin-top: 6px; font-size: 12px; color: #94A3B8; font-style: italic; }

/* 学习状态 */
.status-row {
  margin-top: 8px; display: flex; align-items: center; gap: 8px;
}
.status-tag {
  padding: 3px 10px; border-radius: 8px; font-size: 11px;
  font-weight: 600; cursor: pointer; transition: all .15s;
}
.status-todo { background: #F1F5F9; color: #64748B; }
.status-todo:hover { background: #E2E8F0; }
.status-in_progress { background: #EDE9FE; color: #8B5CF6; }
.status-in_progress:hover { background: #DDD6FE; }
.status-done { background: #D1FAE5; color: #10B981; }
.status-done:hover { background: #A7F3D0; }
.progress-text { font-size: 11px; color: #8B5CF6; font-weight: 600; }
</style>
