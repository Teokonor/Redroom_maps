export type Video = {
  num: number;
  title: string;
  url: string | null;
  reserve_url: string | null;
  image_file: string | null;
  description: string | null;
  mentioned: number[] | null;
  ideas_released: number[] | null;
  ideas_planned: string[] | null;
  quality: string;
  published: string;
};

export type VideoSelection = {
  main: Video[];
  indirectly: Video[];
};
