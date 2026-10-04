import { Capacitor } from '@capacitor/core'
import { Preferences } from '@capacitor/preferences'
import { ref } from 'vue'
export const nativeClient = Capacitor.isNativePlatform()
export const backend = ref(localStorage.getItem('radar_backend') || '')
export async function initializeBackend() {
  if (nativeClient) backend.value = (await Preferences.get({ key: 'radar_backend' })).value || backend.value
}
export function normalizeBackend(value: string): string {
  const url = new URL(value.trim())
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
    throw new Error('Enter an HTTP(S) URL without credentials, query or fragment.')
  }
  if (nativeClient && ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)) {
    throw new Error('Use your computer LAN IP; localhost means this phone.')
  }
  return url.toString().replace(/\/+$/, '')
}
export async function saveBackend(value: string) {
  const normalized = normalizeBackend(value)
  if (normalized !== backend.value) {
    localStorage.removeItem('auth_logged_in')
    localStorage.removeItem('auth_username')
  }
  await Preferences.set({ key: 'radar_backend', value: normalized })
  localStorage.setItem('radar_backend', normalized)
  backend.value = normalized
}
export function apiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path
  return `${backend.value}${path.startsWith('/') ? path : '/' + path}`
}
export function websocketUrl(): string {
  const base = backend.value || window.location.origin
  return `${base.replace(/^http/, 'ws')}/ws`
}
export async function checkBackend() {
  const response = await fetch(apiUrl('/health'), { signal: AbortSignal.timeout(6000) })
  if (!response.ok || (await response.json()).status !== 'healthy') throw new Error('Cannot reach Radar backend')
}
