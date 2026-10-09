<script setup>
/**
 * 数据看板（仅管理员）
 * 运营数据以"披露表格"呈现 + 提问趋势 + 被引用排行 + 未命中清单 + 系统状态
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

/** 读取设计令牌（图表也用同一套墨色与发丝线） */
function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

function renderChart() {
  if (!trendRef.value) return
  if (chart) chart.dispose()
  const ink = cssVar('--ink')
  const ink2 = cssVar('--ink-2')
  const ink3 = cssVar('--ink-3')
  const rule = cssVar('--rule')
  const rule2 = cssVar('--rule-2')
  const paper = cssVar('--panel')

  chart = echarts.init(trendRef.value)
  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: paper,
      borderColor: rule,
      borderWidth: 1,
      padding: [6, 10],
      textStyle: { color: ink, fontSize: 12 },
      axisPointer: { lineStyle: { color: ink3, width: 1, type: 'dashed' } },
    },
    grid: { left: 40, right: 16, top: 24, bottom: 30 },
    xAxis: {
      type: 'category',
      data: trendData.map((x) => x.date.slice(5)),
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false },
      axisLabel: { color: ink3, fontSize: 11, fontFamily: 'inherit' },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      axisLabel: { color: ink3, fontSize: 11, fontFamily: 'inherit' },
      splitLine: { lineStyle: { color: rule2 } },
    },
    series: [
      {
        name: '提问数',
        type: 'line',
        data: trendData.map((x) => x.count),
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: ink, width: 1.6 },
        itemStyle: { color: ink },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(17,17,17,0.07)' },
              { offset: 1, color: 'rgba(17,17,17,0)' },
            ],
          },
        },
        emphasis: { itemStyle: { color: ink2 } },
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
      <div>
        <h2 class="page-title">数据看板</h2>
        <p class="page-sub">运营数据逐项披露 · 数据来自全部已落库回执</p>
      </div>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
    </div>

    <!-- 运营数据：一张"披露表格"，不是一排卡片 -->
    <section class="panel facts-panel">
      <div class="facts">
        <div class="fact">
          <span class="u-label">注册用户</span>
          <span class="fact-num num">{{ overview.user_count ?? '—' }}</span>
        </div>
        <div class="fact">
          <span class="u-label">累计会话</span>
          <span class="fact-num num">{{ overview.conversation_count ?? '—' }}</span>
        </div>
        <div class="fact">
          <span class="u-label">今日提问</span>
          <span class="fact-num num">{{ overview.questions_today ?? '—' }}</span>
          <span class="fact-note num">近 7 天 {{ overview.questions_week ?? 0 }}</span>
        </div>
        <div class="fact">
          <span class="u-label">消息总数</span>
          <span class="fact-num num">{{ overview.message_count ?? '—' }}</span>
        </div>
        <div class="fact">
          <span class="u-label">缓存命中率</span>
          <span class="fact-num num">{{ percent(overview.cache_hit_rate) }}</span>
          <span class="fact-note">秒回复用省算力</span>
        </div>
        <div class="fact">
          <span class="u-label">平均回答耗时</span>
          <span class="fact-num num">{{ latencyText(overview.avg_latency_ms) }}</span>
        </div>
        <div class="fact">
          <span class="u-label">用户评价</span>
          <span class="fact-num num">
            <span class="ok">赞 {{ overview.likes ?? 0 }}</span>
            <span class="sep">／</span>
            <span class="bad">踩 {{ overview.dislikes ?? 0 }}</span>
          </span>
        </div>
        <div class="fact">
          <span class="u-label">未命中率</span>
          <span class="fact-num num">{{ percent(overview.fallback_rate) }}</span>
          <span class="fact-note num">
            {{ overview.document_count ?? 0 }} 份资料 · {{ overview.chunk_count ?? 0 }} 段
          </span>
        </div>
      </div>
    </section>

    <!-- 趋势图 -->
    <section class="panel panel-pad">
      <h3 class="panel-title">近 14 天提问量</h3>
      <div ref="trendRef" class="trend-chart" />
    </section>

    <div class="two-col">
      <!-- 被引用排行 -->
      <section class="panel panel-pad">
        <h3 class="panel-title">被引用最多的资料</h3>
        <el-empty v-if="!topDocs.length" description="暂无数据" :image-size="52" />
        <div v-else class="rule-list">
          <div v-for="(d, i) in topDocs" :key="d.filename" class="rule-row">
            <span class="row-no num">{{ String(i + 1).padStart(2, '0') }}</span>
            <span class="row-name" :title="d.filename">{{ d.filename }}</span>
            <span class="row-count num">{{ d.count }} 次</span>
          </div>
        </div>
      </section>

      <!-- 未命中清单 -->
      <section class="panel panel-pad">
        <h3 class="panel-title">未命中问题（可据此补充资料）</h3>
        <el-empty v-if="!unanswered.length" description="暂无未命中问题" :image-size="52" />
        <div v-else class="rule-list">
          <div v-for="(u, i) in unanswered" :key="i" class="rule-row">
            <span class="row-name">{{ u.question }}</span>
            <span class="row-count num">{{ formatTime(u.time).slice(5) }}</span>
          </div>
        </div>
      </section>
    </div>

    <!-- 系统状态 -->
    <section class="panel panel-pad">
      <h3 class="panel-title">系统状态</h3>
      <div class="kv-grid">
        <div class="kv-row">
          <span class="kv-label u-label">向量模型</span>
          <span class="kv-value">{{ modelText(system.embedding_model) }}</span>
        </div>
        <div class="kv-row">
          <span class="kv-label u-label">精排模型</span>
          <span class="kv-value">{{ modelText(system.reranker_model) }}</span>
        </div>
        <div class="kv-row">
          <span class="kv-label u-label">知识片段总数</span>
          <span class="kv-value num">{{ system.vector_count ?? '—' }}</span>
        </div>
        <div class="kv-row">
          <span class="kv-label u-label">待处理文档</span>
          <span class="kv-value num">{{ system.queue_size ?? 0 }} 个</span>
        </div>
        <div class="kv-row">
          <span class="kv-label u-label">本次运行时长</span>
          <span class="kv-value num">{{ uptimeText(system.uptime_seconds) }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ---- 披露表格 ---- */
.facts-panel {
  margin-bottom: var(--sp-4);
}
.facts {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
}
.fact {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 16px 18px;
  border-right: 1px solid var(--rule-2);
  border-bottom: 1px solid var(--rule-2);
}
.fact:nth-child(4n) {
  border-right: none;
}
.fact:nth-last-child(-n + 4) {
  border-bottom: none;
}
.fact-num {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.01em;
  line-height: 1.2;
}
.fact-note {
  font-size: var(--fs-11);
  color: var(--ink-3);
}
.ok {
  color: var(--ink);
}
.bad {
  color: var(--ink);
}
.sep {
  color: var(--ink-3);
  font-weight: 400;
}

.trend-chart {
  height: 230px;
}
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-4);
  margin: var(--sp-4) 0;
}

/* ---- 发丝行列表 ---- */
.rule-list {
  max-height: 250px;
  overflow-y: auto;
}
.rule-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--rule-2);
  font-size: var(--fs-13);
}
.rule-row:last-child {
  border-bottom: none;
}
.row-no {
  color: var(--ink-3);
  font-size: var(--fs-11);
  flex-shrink: 0;
}
.row-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.row-count {
  color: var(--ink-2);
  font-size: var(--fs-12);
  flex-shrink: 0;
}

/* ---- 系统状态：披露行 ---- */
.kv-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: var(--sp-8);
}
.kv-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--rule-2);
}
.kv-value {
  font-size: var(--fs-13);
  color: var(--ink);
}

@media (max-width: 900px) {
  .facts {
    grid-template-columns: repeat(2, 1fr);
  }
  .fact:nth-child(4n) {
    border-right: 1px solid var(--rule-2);
  }
  .fact:nth-child(2n) {
    border-right: none;
  }
  .fact:nth-last-child(-n + 4) {
    border-bottom: 1px solid var(--rule-2);
  }
  .fact:nth-last-child(-n + 2) {
    border-bottom: none;
  }
  .two-col {
    grid-template-columns: 1fr;
  }
  .kv-grid {
    grid-template-columns: 1fr;
  }
}
</style>
