import type { Tag } from '@/types/tag';

const TAGS_URL = 'http://127.0.0.1:8652/tag/all';

export async function loadTags(): Promise<Tag[]> {
  const response = await fetch(TAGS_URL);

  if (!response.ok) {
    throw new Error(`Не удалось загрузить теги: ${response.status}`);
  }

  return response.json() as Promise<Tag[]>;
}
