const BASE = '' // Im Dev-Modus proxied Vite, in Produktion gleiche Origin

export interface Server {
  id: string
  display_name: string
  template: string
  status: string
  health: string | null
  container_id: string
}

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, init)
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status} ${text}`)
  }
  return res.json()
}

export async function getServers(): Promise<Server[]> {
  return fetchJSON('/api/servers')
}

export async function startServer(id: string): Promise<void> {
  await fetchJSON(`/api/servers/${id}/start`, { method: 'POST' })
}

export async function stopServer(id: string): Promise<void> {
  await fetchJSON(`/api/servers/${id}/stop`, { method: 'POST' })
}

export async function restartServer(id: string): Promise<void> {
  await fetchJSON(`/api/servers/${id}/restart`, { method: 'POST' })
}