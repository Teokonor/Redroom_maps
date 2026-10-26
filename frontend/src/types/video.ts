export type Video = {
  num: number;
  title: string;
  url: string | null;
  reserve_url: string | null;
  image_file: string | null;
  description: string | null;
  quality: string;
  published: string;
};

export type VideoSelection = {
  main: Video[];
  indirectly: Video[];
};
