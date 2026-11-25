export interface ApiAuthBridge {
  getCsrf: () => string | undefined
  onUnauthorized: (csrf: string) => void
}

let authBridge: ApiAuthBridge | null = null

export function configureApiAuth(bridge: ApiAuthBridge) {
  authBridge = bridge
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
  }
}

export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const csrf = authBridge?.getCsrf()
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (method !== 'GET' && csrf) headers['X-CSRF-Token'] = csrf

  let response: Response
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: 'no-store',
    })
  } catch {
    throw new ApiError('无法连接本机服务，请稍后重试', 0)
  }

  if (!response.ok) {
    const result = await response.json().catch(() => ({}))
    if (response.status === 401 && csrf) authBridge?.onUnauthorized(csrf)
    throw new ApiError(typeof result.detail === 'string' ? result.detail : '请求未完成，请重试', response.status)
  }
  return response.json()
}
