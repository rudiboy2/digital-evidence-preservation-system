/**
 * API Service - Centralised HTTP client for all backend communication.
 * Automatically injects JWT tokens and handles token refresh.
 */
const BASE_URL = 'http://localhost:8000/api/v1'

class ApiService {
  constructor() {
    this.baseUrl = BASE_URL
  }

  /** Return headers with Authorization if a token is present. */
  _headers(extra = {}) {
    const token = localStorage.getItem('access_token')
    const headers = { 'Content-Type': 'application/json', ...extra }
    if (token) headers['Authorization'] = `Bearer ${token}`
    return headers
  }

  /** Core fetch wrapper with automatic 401 handling. */
  async _fetch(path, options = {}) {
    const url = `${this.baseUrl}${path}`
    let response = await fetch(url, {
      ...options,
      headers: this._headers(options.headers),
    })

    // Try to refresh token on 401
    if (response.status === 401) {
      const refreshed = await this._tryRefresh()
      if (refreshed) {
        response = await fetch(url, {
          ...options,
          headers: this._headers(options.headers),
        })
      } else {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/'
        return
      }
    }

    if (!response.ok) {
      let detail = `HTTP ${response.status}`
      try {
        const err = await response.json()
        detail = err.detail || err.message || detail
      } catch {}
      throw new Error(detail)
    }

    // 204 No Content
    if (response.status === 204) return null

    return response.json()
  }

  async _tryRefresh() {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) return false
    try {
      const resp = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (!resp.ok) return false
      const data = await resp.json()
      localStorage.setItem('access_token',  data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      return true
    } catch {
      return false
    }
  }

  // -----------------------------------------------------------------------
  // Public API
  // -----------------------------------------------------------------------

  get(path) {
    return this._fetch(path, { method: 'GET' })
  }

  post(path, body = {}, options = {}) {
    const isFormData = body instanceof FormData || body instanceof URLSearchParams
    return this._fetch(path, {
      method: 'POST',
      headers: isFormData ? {} : {},  // Let browser set Content-Type for FormData
      body: isFormData ? body : JSON.stringify(body),
      ...options,
    })
  }

  patch(path, body = {}) {
    return this._fetch(path, {
      method: 'PATCH',
      body: JSON.stringify(body),
    })
  }

  delete(path) {
    return this._fetch(path, { method: 'DELETE' })
  }

  /** File upload — Content-Type is set by browser (multipart/form-data with boundary). */
  uploadFile(path, formData) {
    const token = localStorage.getItem('access_token')
    const headers = {}
    if (token) headers['Authorization'] = `Bearer ${token}`
    return this._fetch(path, {
      method: 'POST',
      headers,
      body: formData,
    })
  }
}

export const api = new ApiService()
