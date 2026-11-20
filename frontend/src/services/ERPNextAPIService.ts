/** Thin wrapper over Frappe's whitelisted-method API. Every request carries the session cookie and CSRF token. */

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
  }
}

function serverMessage(body: any): string | null {
  // Frappe puts user-facing messages in _server_messages (a JSON list of JSON strings).
  try {
    if (body?._server_messages) {
      const messages = JSON.parse(body._server_messages) as string[]
      const text = messages
        .map((m) => JSON.parse(m)?.message as string)
        .filter(Boolean)
        .join('\n')
      if (text) return text.replace(/<[^>]+>/g, '')
    }
  } catch {
    /* fall through */
  }
  if (body?.exception) return String(body.exception).split('\n').pop() ?? null
  return null
}

/** Like `call`, but returns the whole response body (some Frappe methods answer outside `message`). */
export async function callRaw(method: string, args: Record<string, unknown> = {}): Promise<any> {
  return request(method, args)
}

export async function call<T>(method: string, args: Record<string, unknown> = {}): Promise<T> {
  const body = await request(method, args)
  return body.message as T
}

async function request(method: string, args: Record<string, unknown>): Promise<any> {
  const response = await fetch(`/api/method/${method}`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      'X-Frappe-CSRF-Token': window.csrf_token ?? '',
    },
    body: JSON.stringify(args),
  })

  let body: any = null
  try {
    body = await response.json()
  } catch {
    /* non-JSON error page */
  }

  if (response.status === 401 || response.status === 403) {
    if (response.status === 401) window.location.href = '/login?redirect-to=/project-calendar'
    throw new ApiError(serverMessage(body) ?? 'You are not permitted to do that.', response.status)
  }
  if (!response.ok) {
    throw new ApiError(serverMessage(body) ?? `Request failed (${response.status})`, response.status)
  }
  return body
}

export const api = (name: string) => `project_calendar.api.${name}`

export const deskUrl = (doctype: string, name?: string | null) => {
  const slug = doctype.toLowerCase().replace(/\s+/g, '-')
  return name ? `/desk/${slug}/${encodeURIComponent(name)}` : `/desk/${slug}`
}
