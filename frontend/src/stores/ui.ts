import { reactive, ref } from 'vue'

export const toast = reactive({ message: '', error: false, version: 0 })

export const notify = (message: string, error = false) =>
  Object.assign(toast, { message, error, version: toast.version + 1 })

export const activeDialogs = ref(0)
