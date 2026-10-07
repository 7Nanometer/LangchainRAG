/** 文件下载小工具 */

/** 下载文本内容为文件 */
export function downloadText(filename, text) {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  downloadBlob(blob, filename)
}

/** 下载二进制内容（比如后端返回的 Markdown 文件流） */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
