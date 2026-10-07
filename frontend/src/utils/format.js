/** 通用格式化小工具 */
import dayjs from 'dayjs'

/** 把时间格式化成「2026-10-07 15:30」 */
export function formatTime(value) {
  if (!value) return ''
  return dayjs(value).format('YYYY-MM-DD HH:mm')
}

/** 把字节数格式化成「1.3 MB」 */
export function formatSize(bytes) {
  if (!bytes && bytes !== 0) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
