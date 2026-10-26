const YOUTUBE_ID_PATTERN = /^[A-Za-z0-9_-]{11}$/;

export function getYouTubeVideoId(
  url: string | null | undefined
): string | null {
  const value = url?.trim();
  if (!value) return null;

  let parsed: URL;
  try {
    parsed = new URL(
      /^[a-z][a-z0-9+.-]*:\/\//i.test(value) ? value : `https://${value}`
    );
  } catch {
    return null;
  }

  const host = parsed.hostname.toLowerCase().replace(/^www\./, '');
  let videoId: string | null = null;

  if (host === 'youtu.be') {
    videoId = parsed.pathname.split('/').filter(Boolean)[0] ?? null;
  } else if (host === 'youtube.com' || host.endsWith('.youtube.com')) {
    const path = parsed.pathname.replace(/\/+$/, '');

    if (path === '/watch') {
      videoId = parsed.searchParams.get('v');
    } else {
      const match = path.match(/^\/(?:shorts|embed|live)\/([^/]+)/);
      videoId = match?.[1] ?? null;
    }
  }

  return videoId && YOUTUBE_ID_PATTERN.test(videoId) ? videoId : null;
}

export function getYouTubeThumbnailUrl(
  url: string | null | undefined
): string | null {
  const videoId = getYouTubeVideoId(url);
  return videoId
    ? `https://i.ytimg.com/vi/${videoId}/mqdefault.jpg`
    : null;
}
