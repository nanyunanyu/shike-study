import { ref } from 'vue'
import { savePreferencesApi } from '@/api/preferences'
import { updatePreferences } from '@/stores/session'
import { notify } from '@/stores/ui'
import type { Preferences } from '@/types'

export function usePreferencesActions() {
  const saving = ref(false)

  async function savePreferences(value: Preferences, message?: string) {
    saving.value = true
    try {
      const updated = await savePreferencesApi(value)
      updatePreferences(updated)
      if (message) notify(message)
      return updated
    } catch (e) {
      notify((e as Error).message, true)
      return null
    } finally {
      saving.value = false
    }
  }

  return { saving, savePreferences }
}
