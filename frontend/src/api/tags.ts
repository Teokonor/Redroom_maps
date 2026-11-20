import { API_URL } from '@/api/base';
import { withDataVersion } from '@/api/version';
import type { Tag } from '@/types/tag';

const TAGS_URL = `${API_URL}/tag/all`;

export async function loadTags(): Promise<Tag[]> {
  const response = await fetch(await withDataVersion(TAGS_URL));

  if (!response.ok) {
    throw new Error(`Не удалось загрузить теги: ${response.status}`);
  }

  return response.json() as Promise<Tag[]>;
}
