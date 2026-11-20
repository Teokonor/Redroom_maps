import type { VideoPeriodGroup } from '@/types/video';

export type TimelineBlock = {
  key: string;
  beginYear: number;
  endYear: number;
  videoNums: number[];
  isGap: boolean;
  singleYear: boolean;
};

export const TIMELINE_LABEL_HEIGHT = 26;
export const TIMELINE_BOTTOM_LABEL_HEIGHT = 26;
export const TIMELINE_ROW_HEIGHT = 34;
export const TIMELINE_GAP_HEIGHT = 14;

type PeriodGroup = {
  beginYear: number;
  endYear: number;
  videoNums: Set<number>;
};

function sameVideoNums(left: number[], right: number[]): boolean {
  if (left.length !== right.length) return false;
  return left.every((value, index) => value === right[index]);
}

/**
 * Строит блоки таймлайна по периодам.
 *
 * Годы начала и конца периода становятся узлами. Если период одногодичный,
 * его год обязан встретиться в узлах дважды — тогда между двумя одинаковыми
 * узлами появится отдельный блок за этот год.
 */
export function buildTimelineBlocks(
  periods: VideoPeriodGroup[]
): TimelineBlock[] {
  const grouped = new Map<string, PeriodGroup>();
  const nodeCounts = new Map<number, number>();

  for (const period of periods) {
    if (!period.video_nums.length) continue;

    let begin = period.begin_year;
    let end = period.end_year;
    if (begin > end) [begin, end] = [end, begin];

    const groupKey = `${begin}:${end}`;
    let group = grouped.get(groupKey);
    if (!group) {
      group = { beginYear: begin, endYear: end, videoNums: new Set() };
      grouped.set(groupKey, group);
    }
    for (const videoNum of period.video_nums) {
      group.videoNums.add(videoNum);
    }

    const required = begin === end ? 2 : 1;
    nodeCounts.set(begin, Math.max(nodeCounts.get(begin) ?? 0, required));
    nodeCounts.set(end, Math.max(nodeCounts.get(end) ?? 0, required));
  }

  const nodes: number[] = [];
  for (const year of [...nodeCounts.keys()].sort((a, b) => a - b)) {
    const count = nodeCounts.get(year) ?? 1;
    for (let index = 0; index < count; index += 1) nodes.push(year);
  }

  const groups = [...grouped.values()];
  const blocks: TimelineBlock[] = [];

  for (let index = 0; index < nodes.length - 1; index += 1) {
    const beginYear = nodes[index]!;
    const endYear = nodes[index + 1]!;
    const videoNums = new Set<number>();

    for (const group of groups) {
      if (group.beginYear <= beginYear && group.endYear >= endYear) {
        for (const videoNum of group.videoNums) videoNums.add(videoNum);
      }
    }

    const sortedVideoNums = [...videoNums].sort((a, b) => a - b);

    if (!sortedVideoNums.length) {
      // Пустая пара узлов — не блок, а стык соседних лет. Реальный разрыв
      // появляется только там, где между границами есть целый свободный год.
      if (endYear - beginYear > 1) {
        blocks.push({
          key: '',
          beginYear,
          endYear,
          videoNums: [],
          isGap: true,
          singleYear: false,
        });
      }
      continue;
    }

    blocks.push({
      key: '',
      beginYear,
      endYear,
      videoNums: sortedVideoNums,
      isGap: false,
      singleYear: beginYear === endYear,
    });
  }

  const merged: TimelineBlock[] = [];

  for (const block of blocks) {
    const last = merged[merged.length - 1];

    if (last?.isGap && block.isGap) {
      last.endYear = block.endYear;
      continue;
    }

    if (
      last &&
      !last.isGap &&
      !block.isGap &&
      sameVideoNums(last.videoNums, block.videoNums)
    ) {
      last.endYear = block.endYear;
      continue;
    }

    merged.push({ ...block });
  }

  return merged.map((block) => ({
    ...block,
    key: `${block.beginYear}:${block.endYear}`,
    singleYear: !block.isGap && block.beginYear === block.endYear,
  }));
}

/**
 * Блок, в который попадает выбранный год. Если такого нет — ближайший
 * более старый блок; если год древнее всего таймлайна — самый старый блок.
 */
export function findAnchorIndex(
  blocks: TimelineBlock[],
  year: number
): number {
  if (!blocks.length) return 0;

  let olderIndex = -1;

  for (let index = 0; index < blocks.length; index += 1) {
    const block = blocks[index]!;
    if (block.beginYear <= year && year <= block.endYear) return index;
    if (block.endYear < year) olderIndex = index;
  }

  return olderIndex >= 0 ? olderIndex : 0;
}

export function timelineContentHeight(block: TimelineBlock): number {
  return block.isGap
    ? TIMELINE_GAP_HEIGHT
    : block.videoNums.length * TIMELINE_ROW_HEIGHT;
}


