import type { BackupCounts, Preferences } from '@/types'
import { api } from './client'

export const exportBackupApi = () => api<unknown>('/backup')

export const previewBackupApi = (backup: unknown) => api<{ token: string; counts: BackupCounts }>('/backup/preview', 'POST', backup)

export const commitBackupApi = (token: string, backup: unknown) =>
  api<{ counts: BackupCounts; preferences: Preferences }>('/backup', 'PUT', { token, backup })
