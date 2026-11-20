import { API_URL } from '@/api/base'

let dataVersionPromise: Promise<string | null> | null = null

export function ensureDataVersion(): Promise<string | null> {
  if (!dataVersionPromise) {
    dataVersionPromise = fetch(`${API_URL}/data/version`, {
      cache: 'no-store',
    })
      .then((response) => (response.ok ? response.text() : null))
      .then((version) => version?.trim() || null)
      .catch(() => null)
  }

  return dataVersionPromise
}

export async function withDataVersion(url: string): Promise<string> {
  const version = await ensureDataVersion()
  if (!version) return url

  const versioned = new URL(url, window.location.origin)
  versioned.searchParams.set('v', version)
  return versioned.toString()
}
