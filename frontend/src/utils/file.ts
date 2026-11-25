export function downloadJson(filename: string, data: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export async function readJsonFile(file: File, maxBytes = 15 * 1024 * 1024): Promise<unknown> {
  if (file.size > maxBytes) {
    throw new Error(`备份文件不能超过 ${Math.round(maxBytes / (1024 * 1024))} MiB`)
  }
  try {
    return JSON.parse(await file.text())
  } catch {
    throw new Error('无法解析为有效的 JSON 文件')
  }
}
