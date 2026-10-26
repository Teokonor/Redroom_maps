import type { Video, VideoSelection } from '@/types/video';

const API_URL = 'http://127.0.0.1:8652';

async function requestJson<T>(url: string): Promise<T> {
  const response = await fetch(url);

  if (!response.ok) {
    let detail = '';
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? '';
    } catch {
      // The response may not contain JSON; fall back to the status code.
    }

    throw new Error(detail || `Не удалось загрузить видео: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function requestVideoSelection(url: string): Promise<VideoSelection> {
  return requestJson<VideoSelection>(url);
}

export function loadAllVideos(): Promise<Video[]> {
  return requestJson<Video[]>(`${API_URL}/video`);
}

export function loadTagVideos(tagId: string): Promise<Video[]> {
  const params = new URLSearchParams({ tag: tagId });

  return requestJson<Video[]>(`${API_URL}/video?${params.toString()}`);
}

export function loadCountryVideos(
  countryId: string,
  begin: number,
  end: number
): Promise<VideoSelection> {
  const params = new URLSearchParams({
    begin: String(begin),
    end: String(end),
  });

  return requestVideoSelection(
    `${API_URL}/video/${encodeURIComponent(countryId)}?${params.toString()}`
  );
}

export function loadCountryHistoryVideos(
  countryId: string
): Promise<VideoSelection> {
  return requestVideoSelection(
    `${API_URL}/video/${encodeURIComponent(countryId)}/all`
  );
}
