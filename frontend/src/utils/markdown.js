/**
 * Markdown 渲染工具 —— 把 AI 回答（含 **加粗**、列表等）变成网页排版
 *
 * 安全说明：关闭了原始 HTML 渲染（html: false），
 * 防止恶意内容混进回答里被执行（提示词注入防护）。
 */
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html: false,     // 安全：不渲染原始 HTML
  linkify: true,   // 自动识别链接
  breaks: true,    // 单个换行也当作换行（AI 回答常见格式）
})

/**
 * 渲染回答文本。
 * 额外处理：把引用编号 [1]、[2] 变成醒目的蓝色角标。
 */
export function renderMarkdown(text) {
  if (!text) return ''
  let html = md.render(text)
  // 把 [数字] 引用标记替换成角标样式（LLM 按提示词要求输出这种格式）
  html = html.replace(/\[(\d{1,2})\]/g, '<sup class="cite-ref">$1</sup>')
  return html
}
