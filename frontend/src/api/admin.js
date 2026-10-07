/** 管理后台接口（知识库 / 文档） */
import request from './request'

// ---- 知识库 ----
export const listKbs = () => request.get('/admin/kb')
export const createKb = (data) => request.post('/admin/kb', data)
export const updateKb = (id, data) => request.patch(`/admin/kb/${id}`, data)
export const deleteKb = (id) => request.delete(`/admin/kb/${id}`)
export const reindexKb = (id) => request.post(`/admin/kb/${id}/reindex`)

// ---- 文档 ----
export const listDocuments = (kbId) => request.get(`/admin/kb/${kbId}/documents`)
// 上传可能较慢（多文件），单独放宽超时
export const uploadDocuments = (kbId, formData) =>
  request.post(`/admin/kb/${kbId}/documents`, formData, { timeout: 300000 })
export const deleteDocument = (id) => request.delete(`/admin/documents/${id}`)
export const reindexDocument = (id) => request.post(`/admin/documents/${id}/reindex`)
