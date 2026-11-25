import type { Preferences } from '@/types'
import { api } from './client'

export const savePreferencesApi = (payload: Preferences) => api<Preferences>('/preferences', 'PUT', payload)
