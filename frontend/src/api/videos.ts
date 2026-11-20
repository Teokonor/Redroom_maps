import { API_URL } from '@/api/base';
import { withDataVersion } from '@/api/version';
import type { VideoPeriod } from '@/types/period';
import type {
  HistoryVideoSelection,
  Video,
  VideoSelection,
} from '@/types/video';

async function requestJson<T>(url: string): Promise<T> {
  const response = await fetch(await withDataVersion(url));

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

export function getVideoPreviewUrl(imageFile: string): string {
  return `${API_URL}/preview/${encodeURIComponent(imageFile)}`;
}

export function loadAllVideos(): Promise<Video[]> {
  return requestJson<Video[]>(`${API_URL}/video`);
}

export function loadVideoPeriods(videoNum: number): Promise<VideoPeriod[]> {
  return requestJson<VideoPeriod[]>(`${API_URL}/video/${videoNum}/periods`);
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

  return requestJson<VideoSelection>(
    `${API_URL}/video/${encodeURIComponent(countryId)}?${params.toString()}`
  );
}

export function loadCountryHistoryVideos(
  countryId: string
): Promise<HistoryVideoSelection> {
  return requestJson<HistoryVideoSelection>(
    `${API_URL}/video/${encodeURIComponent(countryId)}/all`
  );
}
