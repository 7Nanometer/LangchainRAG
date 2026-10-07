/**
 * 聊天状态管理 —— 前端聊天的"大脑"
 *
 * 负责：会话列表、当前会话消息、流式生成中的状态（打字机文本 + 引用）、
 * 发送/停止、改名/删除、点赞点踩。
 */
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import * as convApi from '@/api/conversations'
import { streamChat } from '@/utils/sse'

export const useChatStore = defineStore('chat', {
  state: () => ({
    conversations: [],      // 会话列表
    currentId: null,        // 当前会话 id（null = 新对话）
    messages: [],           // 当前会话已加载的消息
    loadingMessages: false,

    // ---- 流式生成状态 ----
    streaming: false,       // 正在生成中
    streamText: '',         // 已生成的文本（逐字追加）
    streamCitations: [],    // 本次引用的资料片段
    streamFallback: false,  // 本次是否为兜底回答
    streamFromCache: false, // 本次是否命中缓存（秒回）
    abortCtrl: null,        // 用于停止生成
  }),

  getters: {
    isEmpty: (state) => state.messages.length === 0 && !state.streaming,
  },

  actions: {
    // ---------------- 会话 ----------------
    async loadConversations() {
      this.conversations = await convApi.listConversations()
    },

    async openConversation(id) {
      if (this.streaming) this.stop(true)
      this.currentId = id
      this.resetStream()
      this.loadingMessages = true
      try {
        this.messages = await convApi.getMessages(id)
      } catch {
        this.messages = []
      } finally {
        this.loadingMessages = false
      }
    },

    newChat() {
      if (this.streaming) this.stop(true)
      this.currentId = null
      this.messages = []
      this.resetStream()
    },

    async rename(id, title) {
      await convApi.renameConversation(id, title)
      await this.loadConversations()
      ElMessage.success('已重命名')
    },

    async remove(id) {
      await convApi.deleteConversation(id)
      if (this.currentId === id) this.newChat()
      await this.loadConversations()
      ElMessage.success('会话已删除')
    },

    async feedback(messageId, value) {
      // 再点一次相同评价 = 取消
      const msg = this.messages.find((m) => m.id === messageId)
      const next = msg?.feedback === value ? null : value
      await convApi.sendFeedback(messageId, next)
      if (msg) msg.feedback = next
    },

    // ---------------- 问答 ----------------
    async send(question) {
      const q = (question || '').trim()
      if (!q || this.streaming) return

      // 先把用户消息显示出来（不等服务器返回，体验更顺）
      this.messages.push({
        id: `local-${Date.now()}`,
        role: 'user',
        content: q,
        citations: [],
        feedback: null,
        created_at: new Date().toISOString(),
      })

      this.streaming = true
      this.streamText = ''
      this.streamCitations = []
      this.streamFallback = false
      this.streamFromCache = false
      this.abortCtrl = new AbortController()

      try {
        await streamChat(
          { question: q, conversation_id: this.currentId },
          {
            onMeta: (meta) => {
              // 新会话：服务器已建好会话，记住 id（视图会同步地址栏）
              if (this.currentId == null) this.currentId = meta.conversation_id
              this.streamFallback = meta.is_fallback
              this.streamFromCache = !!meta.from_cache
            },
            onCitations: (citations) => {
              this.streamCitations = citations
            },
            onDelta: (text) => {
              this.streamText += text
            },
            onDone: async (done) => {
              // 生成完成：把"生成中"转成正式消息
              this.messages.push({
                id: done.message_id,
                role: 'assistant',
                content: this.streamText,
                citations: this.streamCitations,
                feedback: null,
                is_fallback: this.streamFallback,
                from_cache: this.streamFromCache,
                latency_ms: done.latency_ms,
                created_at: new Date().toISOString(),
              })
              this.resetStream()
              // 刷新会话列表（标题/排序可能变化）
              this.loadConversations().catch(() => {})
            },
            onError: (message) => {
              ElMessage.error(message)
              // 若已有部分内容，保留显示；否则不留空消息
              if (this.streamText) {
                this.messages.push({
                  id: `err-${Date.now()}`,
                  role: 'assistant',
                  content: `${this.streamText}\n\n> ⚠️ （回答生成中断）`,
                  citations: this.streamCitations,
                  feedback: null,
                  created_at: new Date().toISOString(),
                })
              }
              this.resetStream()
            },
          },
          this.abortCtrl.signal,
        )
      } catch (err) {
        // 用户点"停止"触发的 abort 属于正常操作，不提示错误
        if (err?.name !== 'AbortError') {
          console.error(err)
          ElMessage.error('网络异常，请检查系统是否在运行')
        }
      } finally {
        if (this.streaming) this.streaming = false
      }
    },

    /** 停止生成（silent=true 用于切换会话时的静默停止） */
    stop(silent = false) {
      this.abortCtrl?.abort()
      // 把已生成的部分保留为一条消息
      if (this.streamText) {
        this.messages.push({
          id: `stopped-${Date.now()}`,
          role: 'assistant',
          content: `${this.streamText}\n\n> ✋ （已停止生成）`,
          citations: this.streamCitations,
          feedback: null,
          created_at: new Date().toISOString(),
        })
      }
      this.resetStream()
      if (!silent) ElMessage.info('已停止生成')
    },

    resetStream() {
      this.streaming = false
      this.streamText = ''
      this.streamCitations = []
      this.streamFallback = false
      this.streamFromCache = false
      this.abortCtrl = null
    },
  },
})
