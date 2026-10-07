/** 会话与消息接口 */
import request from './request'

export const listConversations = () => request.get('/conversations')
export const createConversation = (data = {}) => request.post('/conversations', data)
export const renameConversation = (id, title) => request.patch(`/conversations/${id}`, { title })
export const deleteConversation = (id) => request.delete(`/conversations/${id}`)
export const getMessages = (id) => request.get(`/conversations/${id}/messages`)
export const exportConversation = (id) =>
  request.get(`/conversations/${id}/export`, { responseType: 'blob' })
export const sendFeedback = (messageId, feedback) =>
  request.put(`/messages/${messageId}/feedback`, { feedback })
