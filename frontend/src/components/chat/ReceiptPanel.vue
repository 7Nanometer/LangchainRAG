<script setup>
/**
 * 答案回执（签名动作）—— 每条回答下方的一张"强制披露"面板
 *
 * 折叠态：一条发丝线上的摘要（来源段数 · 相关度 · 耗时 · 时间）
 * 展开态：逐项披露 —— 来源明细（文件 · 相关度 · 原文）、检索漏斗、生成指标
 *
 * 动效（本应用唯一的"出场"）：一条墨线从左"打印"到位，行项依次落定。
 */
import { computed, nextTick, ref } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'
import { formatTime } from '@/utils/format'

const props = defineProps({
  message: { type: Object, required: true },
  streaming: { type: Boolean, default: false },
})

const expanded = ref(false)
const expandedItems = ref(new Set())
const highlight = ref(null)
const bodyRef = ref(null)

const citations = computed(() => props.message.citations || [])
const count = computed(() => citations.value.length)
const fallback = computed(() => !!props.message.is_fallback)
const fromCache = computed(() => !!props.message.from_cache)
const retrieval = computed(() => props.message.retrieval || null)

const topScore = computed(() => {
  const list = citations.value.map((c) => c.score || 0)
  return list.length ? Math.max(...list) : 0
})
const latencyText = computed(() => {
  const ms = props.message.latency_ms
  return ms ? `${(ms / 1000).toFixed(1)} 秒` : ''
})
const idText = computed(() =>
  typeof props.message.id === 'number' ? `№${props.message.id}` : '—',
)
const timeShort = computed(() => formatTime(props.message.created_at).slice(-5))
const timeFull = computed(() => formatTime(props.message.created_at) || '—')

/** 相关度分档 → 评分块颜色（绿→红，只用于数据） */
function scoreClass(score) {
  const s = score || 0
  if (s >= 0.7) return 's1'
  if (s >= 0.64) return 's2'
  if (s >= 0.58) return 's3'
  if (s >= 0.52) return 's4'
  return 's5'
}
function pct(score) {
  return `${((score || 0) * 100).toFixed(0)}%`
}

function toggleItem(index) {
  const s = new Set(expandedItems.value)
  if (s.has(index)) s.delete(index)
  else s.add(index)
  expandedItems.value = s
}

/** 供回答正文里的 [n] 角标调用：展开并定位到该条来源 */
async function openAt(index) {
  expanded.value = true
  highlight.value = index
  const s = new Set(expandedItems.value)
  s.add(index)
  expandedItems.value = s
  await nextTick()
  const row = bodyRef.value?.querySelector(`[data-cite="${index}"]`)
  row?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  setTimeout(() => {
    if (highlight.value === index) highlight.value = null
  }, 1600)
}

defineExpose({ openAt })
</script>

<template>
  <div class="receipt" :class="{ 'is-streaming': streaming }">
    <span class="receipt-rule" aria-hidden="true" />

    <!-- 摘要条（发丝线上的对账行） -->
    <button class="receipt-strip" type="button" @click="expanded = !expanded">
      <span class="r-mark" :class="{ typing: streaming }" />
      <span class="r-label">回执</span>
      <span class="r-id num">{{ idText }}</span>

      <template v-if="streaming && !count">
        <span class="r-dim">正在检索资料…</span>
      </template>
      <template v-else>
        <span v-if="fallback" class="r-stamp"><i class="r-stamp-block" />未命中 · 兜底回答</span>
        <template v-else>
          <span class="r-dim num">{{ count }} 段来源</span>
          <span v-if="topScore" class="r-dim">
            相关度 <span class="num">{{ pct(topScore) }}</span>
          </span>
        </template>
        <span v-if="fromCache" class="r-cache">复用</span>
        <span v-if="streaming" class="r-dim typing-text">生成中<span class="tick">…</span></span>
        <span v-else-if="latencyText" class="r-dim num">{{ latencyText }}</span>
        <span class="r-time num">{{ timeShort }}</span>
      </template>

      <el-icon class="r-arrow" :class="{ open: expanded }" :size="12"><ArrowDown /></el-icon>
    </button>

    <!-- 展开：逐项披露 -->
    <div v-if="expanded" ref="bodyRef" class="receipt-body">
      <template v-if="count">
        <div
          v-for="(c, i) in citations"
          :key="c.index"
          class="r-source row-settle"
          :style="{ animationDelay: Math.min(i, 8) * 45 + 'ms' }"
        >
          <div
            class="r-source-head"
            :class="{ highlight: highlight === c.index }"
            :data-cite="c.index"
            role="button"
            tabindex="0"
            @click="toggleItem(c.index)"
            @keydown.enter.prevent="toggleItem(c.index)"
            @keydown.space.prevent="toggleItem(c.index)"
          >
            <span class="r-idx num">[{{ c.index }}]</span>
            <span class="r-file">{{ c.filename }}</span>
            <span class="r-score">
              <i class="score-block" :class="scoreClass(c.score)" />
              <span class="num">{{ pct(c.score) }}</span>
            </span>
            <el-icon class="r-arrow" :class="{ open: expandedItems.has(c.index) }" :size="11">
              <ArrowDown />
            </el-icon>
          </div>
          <div v-show="expandedItems.has(c.index)" class="r-content">{{ c.content }}</div>
        </div>
      </template>
      <div v-else-if="streaming" class="r-meta">检索结果将在回答开始前锁定…</div>

      <!-- 检索漏斗（构造可见）：四格披露行 -->
      <div v-if="retrieval" class="r-funnel row-settle">
        <div class="rf-cell">
          <span class="rf-label">向量命中</span>
          <span class="rf-num num">{{ retrieval.vector_hits }} 段</span>
        </div>
        <div class="rf-cell">
          <span class="rf-label">关键词命中</span>
          <span class="rf-num num">{{ retrieval.bm25_hits }} 段</span>
        </div>
        <div class="rf-cell">
          <span class="rf-label">融合</span>
          <span class="rf-num num">{{ retrieval.fused }} 段</span>
        </div>
        <div class="rf-cell">
          <span class="rf-label">采纳</span>
          <span class="rf-num num">{{ retrieval.adopted }} 段</span>
        </div>
      </div>
      <div v-if="retrieval" class="r-meta num">
        相关度阈值 {{ retrieval.threshold
        }}<template v-if="retrieval.ms != null"> · 检索耗时 {{ (retrieval.ms / 1000).toFixed(1) }} 秒</template>
      </div>

      <!-- 指标行 -->
      <div class="r-meta row-settle" :style="{ animationDelay: '60ms' }">
        <template v-if="streaming">生成中，指标完成后落定</template>
        <template v-else>
          <span class="num">{{ timeFull }}</span>
          <span v-if="latencyText" class="num"> · 生成耗时 {{ latencyText }}</span>
          <span> · {{ fallback ? '兜底回答（知识库未命中）' : fromCache ? '语义缓存复用' : '实时生成' }}</span>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.receipt {
  position: relative;
  margin-top: 12px;
}

/* 签名动效：墨线从左"打印"到位 */
.receipt-rule {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--ink);
  transform-origin: left center;
  transform: scaleX(0);
}
.receipt .receipt-rule {
  animation: rule-print var(--dur-3) var(--ease) both;
}

.receipt-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  border: none;
  border-top: 1px solid var(--rule);
  background: transparent;
  padding: 7px 8px 7px 0;
  margin: 0;
  font-family: inherit;
  font-size: var(--fs-12);
  color: var(--ink-2);
  cursor: pointer;
  text-align: left;
  transition: background var(--dur-1) var(--ease);
}
.receipt-strip:hover {
  background: var(--tint);
}
.r-mark {
  width: 3px;
  height: 12px;
  background: var(--ink);
  flex-shrink: 0;
}
.r-mark.typing {
  animation: pulse-ink 1.1s ease-in-out infinite;
}
.r-label {
  font-weight: 700;
  color: var(--ink);
  letter-spacing: 0.02em;
}
.r-id {
  color: var(--ink-3);
}
.r-dim {
  color: var(--ink-2);
}
.r-stamp {
  color: var(--stamp);
  font-weight: 600;
}
.r-stamp-block {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: var(--stamp);
  border-radius: 1px;
  margin-right: 5px;
}
.r-funnel {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border-top: 1px solid var(--rule-2);
  margin-top: 8px;
}
.rf-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 7px 10px 6px 10px;
  border-right: 1px solid var(--rule-2);
}
.rf-cell:first-child {
  padding-left: 6px;
}
.rf-cell:last-child {
  border-right: none;
}
.rf-label {
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--ink-3);
}
.rf-num {
  font-size: 12.5px;
  color: var(--ink);
}
.r-cache {
  border: 1px solid var(--rule);
  border-radius: var(--r-2);
  padding: 0 5px;
  color: var(--ink-3);
  font-size: var(--fs-11);
}
.r-time {
  margin-left: auto;
  color: var(--ink-3);
}
.typing-text .tick {
  animation: caret-blink 1s steps(1) infinite;
}
.r-arrow {
  color: var(--ink-3);
  transition: transform var(--dur-2) var(--ease);
}
.r-arrow.open {
  transform: rotate(180deg);
}

.receipt-body {
  border-top: 1px solid var(--rule-2);
  background: var(--paper-2);
  padding: 4px 12px 10px;
}

.r-source-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 6px;
  border-bottom: 1px solid var(--rule-2);
  font-size: var(--fs-12);
  cursor: pointer;
  border-radius: var(--r-2);
  transition: background var(--dur-1) var(--ease);
}
.r-source-head:hover {
  background: var(--tint);
}
.r-source-head.highlight {
  background: var(--tint-2);
}
.r-source:last-of-type .r-source-head {
  border-bottom: none;
}
.r-idx {
  color: var(--ink);
  font-weight: 700;
  flex-shrink: 0;
}
.r-file {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--ink);
}
.r-score {
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--ink-2);
  flex-shrink: 0;
}
.r-content {
  padding: 8px 10px 10px 26px;
  font-size: var(--fs-12);
  line-height: 1.75;
  color: var(--ink-2);
  white-space: pre-wrap;
  word-break: break-word;
  border-bottom: 1px solid var(--rule-2);
}
.r-meta {
  padding-top: 8px;
  font-size: var(--fs-11);
  color: var(--ink-3);
  letter-spacing: 0.01em;
}
</style>
