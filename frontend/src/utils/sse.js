/**
 * SSE 流式请求工具 —— 实现"答案一个字一个字蹦出来"
 *
 * 原理：用 fetch 发请求，服务器的响应像"水龙头"一样持续流出数据；
 * 这里不断地把流出来的字节拼成完整事件，分发给对应的处理函数。
 *
 * 关键细节：网络可能把一个事件切成两半（半个字在这段、半个字在下段），
 * 所以必须用 buffer 缓存"没收到完整事件"的残留数据。
 */
import { useUserStore } from '@/stores/user'

/**
 * 发起流式问答
 * @param {Object} payload  {question, conversation_id}
 * @param {Object} handlers {onMeta, onCitations, onDelta, onDone, onError}
 * @param {AbortSignal} signal 用于"停止生成"
 */
export async function streamChat(payload, handlers, signal) {
  const userStore = useUserStore()

  const resp = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(userStore.token ? { Authorization: `Bearer ${userStore.token}` } : {}),
    },
    body: JSON.stringify(payload),
    signal,
  })

  // HTTP 层错误（如没配 API Key、限流、未登录）：读取统一格式的中文错误
  if (!resp.ok) {
    let message = '请求失败，请稍后再试'
    try {
      const data = await resp.json()
      message = data.message || message
    } catch {
      /* 保持默认提示 */
    }
    handlers.onError?.(message)
    return
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    // stream: true 处理"一个汉字被切成两半"的多字节边界问题
    buffer += decoder.decode(value, { stream: true })
    buffer = buffer.replace(/\r/g, '') // 兼容可能的 \r\n（也处理被切断的 \r 残片）

    let sep
    while ((sep = buffer.indexOf('\n\n')) >= 0) {
      const rawEvent = buffer.slice(0, sep)
      buffer = buffer.slice(sep + 2)
      dispatchEvent(rawEvent, handlers)
    }
  }
}

/** 解析并分发单个 SSE 事件块 */
function dispatchEvent(rawEvent, handlers) {
  let event = ''
  let dataStr = ''
  for (const line of rawEvent.split('\n')) {
    if (line.startsWith('event: ')) event = line.slice(7).trim()
    else if (line.startsWith('data: ')) dataStr = line.slice(6)
    // 以 : 开头的行是心跳注释，直接忽略
  }
  if (!event || !dataStr) return

  let data
  try {
    data = JSON.parse(dataStr)
  } catch {
    return
  }

  switch (event) {
    case 'meta':
      handlers.onMeta?.(data)
      break
    case 'citations':
      handlers.onCitations?.(data)
      break
    case 'delta':
      handlers.onDelta?.(data.text)
      break
    case 'done':
      handlers.onDone?.(data)
      break
    case 'error':
      handlers.onError?.(data.message)
      break
  }
}
