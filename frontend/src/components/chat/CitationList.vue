<script setup>
/** 引用卡片列表：展示本次回答引用了哪些知识库片段（可展开看原文） */
import { ref } from 'vue'
import { Collection } from '@element-plus/icons-vue'

defineProps({
  citations: { type: Array, default: () => [] },
})

const expanded = ref(false)          // 整个列表是否展开
const expandedItems = ref(new Set()) // 单个片段是否展开全文

function toggleItem(index) {
  const s = new Set(expandedItems.value)
  if (s.has(index)) s.delete(index)
  else s.add(index)
  expandedItems.value = s
}
</script>

<template>
  <div v-if="citations.length" class="citation-box">
    <div class="citation-head" @click="expanded = !expanded">
      <el-icon><Collection /></el-icon>
      <span>引用了 {{ citations.length }} 段知识库资料</span>
      <span class="arrow" :class="{ open: expanded }">▾</span>
    </div>

    <div v-show="expanded" class="citation-body">
      <div v-for="c in citations" :key="c.index" class="citation-item">
        <div class="citation-meta">
          <span class="cite-index">[{{ c.index }}]</span>
          <span class="cite-file">{{ c.filename }}</span>
          <span v-if="c.score" class="cite-score">相关度 {{ (c.score * 100).toFixed(0) }}%</span>
        </div>
        <div class="citation-text" :class="{ clamp: !expandedItems.has(c.index) }">
          {{ c.content }}
        </div>
        <el-button
          v-if="c.content.length > 120"
          text
          size="small"
          type="primary"
          @click="toggleItem(c.index)"
        >
          {{ expandedItems.has(c.index) ? '收起' : '展开全文' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.citation-box {
  margin-top: 10px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}
.citation-head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-second);
  cursor: pointer;
  user-select: none;
  background: rgba(128, 128, 128, 0.05);
}
.citation-head:hover {
  color: var(--brand);
}
.arrow {
  margin-left: auto;
  transition: transform 0.2s;
  font-size: 12px;
}
.arrow.open {
  transform: rotate(180deg);
}
.citation-body {
  padding: 6px 12px 12px;
}
.citation-item {
  padding: 10px 0;
  border-bottom: 1px dashed var(--border-color);
}
.citation-item:last-child {
  border-bottom: none;
  padding-bottom: 2px;
}
.citation-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  margin-bottom: 6px;
}
.cite-index {
  color: var(--brand);
  font-weight: 600;
}
.cite-file {
  color: var(--text-main);
}
.cite-score {
  margin-left: auto;
  color: var(--text-second);
  font-size: 11.5px;
}
.citation-text {
  font-size: 13px;
  color: var(--text-second);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.citation-text.clamp {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
