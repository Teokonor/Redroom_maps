import { API_URL } from '@/api/base'

let versionPromise: Promise<string | null> | null = null

function ensureMapVersion(): Promise<string | null> {
  if (!versionPromise) {
    versionPromise = fetch(`${API_URL}/map/version`, {
      cache: 'no-store',
    })
      .then((response) => (response.ok ? response.text() : null))
      .then((version) => version?.trim() || null)
      .catch(() => null)
  }

  return versionPromise
}

export async function fetchMapResource(path: string): Promise<Response> {
  const version = await ensureMapVersion()
  const url = new URL(`${API_URL}${path}`, window.location.origin)

  if (version) {
    url.searchParams.set('v', version)
  }

  return fetch(url.toString())
}
