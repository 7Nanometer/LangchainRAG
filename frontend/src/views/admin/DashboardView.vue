<script setup>
/**
 * 数据看板（仅管理员）
 * 统计卡片 + 提问趋势图 + 被引用资料排行 + 未命中问题清单 + 系统状态
 */
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { Refresh } from '@element-plus/icons-vue'
import {
  getStatsOverview,
  getStatsTrend,
  getSystemStatus,
  getTopDocuments,
  getUnanswered,
} from '@/api/admin'
import { formatTime } from '@/utils/format'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()
const loading = ref(true)
const overview = ref({})
const topDocs = ref([])
const unanswered = ref([])
const system = ref({})
const trendRef = ref()
let chart = null
let trendData = []

async function load() {
  loading.value = true
  try {
    const [o, t, d, u, s] = await Promise.all([
      getStatsOverview(),
      getStatsTrend(14),
      getTopDocuments(),
      getUnanswered(),
      getSystemStatus(),
    ])
    overview.value = o
    trendData = t
    topDocs.value = d
    unanswered.value = u
    system.value = s
    renderChart()
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!trendRef.value) return
  if (chart) chart.dispose()
  chart = echarts.init(trendRef.value, themeStore.isDark ? 'dark' : null)
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { left: 44, right: 20, top: 30, bottom: 32 },
    xAxis: {
      type: 'category',
      data: trendData.map((x) => x.date.slice(5)),
      axisLine: { lineStyle: { color: 'rgba(128,128,128,0.3)' } },
    },
    yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { opacity: 0.25 } } },
    series: [
      {
        name: '提问数',
        type: 'line',
        smooth: true,
        symbolSize: 7,
        data: trendData.map((x) => x.count),
        areaStyle: { opacity: 0.15 },
      },
    ],
  })
}

function onResize() {
  chart?.resize()
}

// 深浅主题切换时重新绘制图表
watch(
  () => themeStore.isDark,
  () => renderChart(),
)

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})

function percent(v) {
  return `${((v || 0) * 100).toFixed(1)}%`
}
function latencyText(ms) {
  return ms ? `${(ms / 1000).toFixed(2)} 秒` : '—'
}
function uptimeText(seconds) {
  if (!seconds) return '—'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h} 小时 ${m} 分钟` : `${m} 分钟`
}
function modelText(status) {
  const names = { unloaded: '未加载', loading: '加载中', ready: '已就绪', failed: '加载失败' }
  const device = status?.device === 'cuda' ? '显卡' : status?.device === 'cpu' ? 'CPU' : ''
  return `${names[status?.state] || '未知'}${device ? `（${device}）` : ''}`
}
</script>

<template>
  <div v-loading="loading">
    <div class="page-head">
      <h2 class="page-title">数据看板</h2>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-num">{{ overview.user_count ?? '—' }}</div>
        <div class="stat-label">注册用户</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ overview.conversation_count ?? '—' }}</div>
        <div class="stat-label">累计会话</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ overview.questions_today ?? '—' }}</div>
        <div class="stat-label">今日提问（近7天 {{ overview.questions_week ?? 0 }}）</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ overview.message_count ?? '—' }}</div>
        <div class="stat-label">消息总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ percent(overview.cache_hit_rate) }}</div>
        <div class="stat-label">缓存命中率（省时省钱）</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ latencyText(overview.avg_latency_ms) }}</div>
        <div class="stat-label">平均回答耗时</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">
          👍 {{ overview.likes ?? 0 }} ／ 👎 {{ overview.dislikes ?? 0 }}
        </div>
        <div class="stat-label">用户评价</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ percent(overview.fallback_rate) }}</div>
        <div class="stat-label">未命中率（{{ overview.document_count ?? 0 }} 份资料 / {{ overview.chunk_count ?? 0 }} 片段）</div>
      </div>
    </div>

    <!-- 趋势图 -->
    <div class="panel">
      <div class="panel-title">近 14 天提问量</div>
      <div ref="trendRef" class="trend-chart" />
    </div>

    <div class="two-col">
      <!-- 被引用排行 -->
      <div class="panel">
        <div class="panel-title">被引用最多的资料</div>
        <el-empty v-if="!topDocs.length" description="暂无数据" :image-size="60" />
        <div v-else class="rank-list">
          <div v-for="(d, i) in topDocs" :key="d.filename" class="rank-item">
            <span class="rank-no" :class="{ top: i < 3 }">{{ i + 1 }}</span>
            <span class="rank-name" :title="d.filename">{{ d.filename }}</span>
            <span class="rank-count">{{ d.count }} 次</span>
          </div>
        </div>
      </div>

      <!-- 未命中清单 -->
      <div class="panel">
        <div class="panel-title">未命中问题（可据此补充资料）</div>
        <el-empty v-if="!unanswered.length" description="暂无未命中问题" :image-size="60" />
        <div v-else class="unanswered-list">
          <div v-for="(u, i) in unanswered" :key="i" class="unanswered-item">
            <div class="unanswered-q">{{ u.question }}</div>
            <div class="unanswered-time">{{ formatTime(u.time) }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 系统状态 -->
    <div class="panel">
      <div class="panel-title">系统状态</div>
      <div class="sys-grid">
        <div class="sys-item">
          <span class="sys-label">向量模型</span>
          <span class="sys-value">{{ modelText(system.embedding_model) }}</span>
        </div>
        <div class="sys-item">
          <span class="sys-label">精排模型</span>
          <span class="sys-value">{{ modelText(system.reranker_model) }}</span>
        </div>
        <div class="sys-item">
          <span class="sys-label">知识片段总数</span>
          <span class="sys-value">{{ system.vector_count ?? '—' }}</span>
        </div>
        <div class="sys-item">
          <span class="sys-label">待处理文档</span>
          <span class="sys-value">{{ system.queue_size ?? 0 }} 个</span>
        </div>
        <div class="sys-item">
          <span class="sys-label">本次运行时长</span>
          <span class="sys-value">{{ uptimeText(system.uptime_seconds) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.page-title {
  margin: 0;
  font-size: 18px;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  background: var(--panel-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 14px 16px;
}
.stat-num {
  font-size: 20px;
  font-weight: 700;
}
.stat-label {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-second);
}
.panel {
  background: var(--panel-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}
.trend-chart {
  height: 240px;
}
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
@media (max-width: 900px) {
  .two-col {
    grid-template-columns: 1fr;
  }
}
.rank-list,
.unanswered-list {
  max-height: 260px;
  overflow-y: auto;
}
.rank-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 0;
  border-bottom: 1px dashed var(--border-color);
  font-size: 13px;
}
.rank-item:last-child {
  border-bottom: none;
}
.rank-no {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  background: rgba(128, 128, 128, 0.12);
  color: var(--text-second);
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.rank-no.top {
  background: var(--brand);
  color: #fff;
}
.rank-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rank-count {
  color: var(--text-second);
  font-size: 12px;
  flex-shrink: 0;
}
.unanswered-item {
  padding: 8px 0;
  border-bottom: 1px dashed var(--border-color);
}
.unanswered-item:last-child {
  border-bottom: none;
}
.unanswered-q {
  font-size: 13px;
}
.unanswered-time {
  font-size: 11.5px;
  color: var(--text-second);
  margin-top: 2px;
}
.sys-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}
.sys-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 6px 10px;
  background: rgba(128, 128, 128, 0.06);
  border-radius: 8px;
}
.sys-label {
  color: var(--text-second);
}
</style>
