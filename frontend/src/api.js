// Vite forwards /api requests to the local FastAPI server.
export async function request(path, options) {
  let response
  try {
    response = await fetch(`/api${path}`, options)
  } catch {
    throw new Error('We couldn’t connect. Please check your connection and try again.')
  }

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = data?.detail
    const message = typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map(item => item.msg).filter(Boolean).join(' ')
        : ''
    throw new Error(message || (response.status >= 500
      ? 'Something interrupted your request. Please try again in a moment.'
      : 'We couldn’t complete your request. Please try again.'))
  }
  if (!data) throw new Error('We received an unexpected response. Please try again.')
  return data
}
