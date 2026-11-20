import { describe, expect, it } from 'vitest';
import type { VideoPeriodGroup } from '@/types/video';
import {
  buildTimelineBlocks,
  findAnchorIndex,
  type TimelineBlock,
} from '../videoTimeline';

function group(
  begin: number,
  end: number,
  videoNums: number[],
  isMain = true
): VideoPeriodGroup {
  return {
    begin_year: begin,
    end_year: end,
    is_main: isMain,
    video_nums: videoNums,
  };
}

function summary(blocks: TimelineBlock[]) {
  return blocks.map((block) => ({
    begin: block.beginYear,
    end: block.endYear,
    videos: block.videoNums,
    gap: block.isGap,
    single: block.singleYear,
  }));
}

describe('buildTimelineBlocks', () => {
  it('shares a boundary year without merging the videos', () => {
    const blocks = buildTimelineBlocks([group(200, 500, [1]), group(500, 800, [2])]);

    expect(summary(blocks)).toEqual([
      { begin: 200, end: 500, videos: [1], gap: false, single: false },
      { begin: 500, end: 800, videos: [2], gap: false, single: false },
    ]);
  });

  it('includes all videos that touch a single-year block', () => {
    const blocks = buildTimelineBlocks([
      group(200, 500, [1]),
      group(500, 500, [3]),
      group(500, 800, [2]),
    ]);

    expect(summary(blocks)).toEqual([
      { begin: 200, end: 500, videos: [1], gap: false, single: false },
      { begin: 500, end: 500, videos: [1, 2, 3], gap: false, single: true },
      { begin: 500, end: 800, videos: [2], gap: false, single: false },
    ]);
  });

  it('keeps a real gap and drops a one-year connector', () => {
    const withGap = buildTimelineBlocks([
      group(200, 300, [1]),
      group(500, 800, [2]),
    ]);
    const consecutive = buildTimelineBlocks([
      group(500, 500, [1]),
      group(501, 501, [2]),
    ]);

    expect(summary(withGap)).toEqual([
      { begin: 200, end: 300, videos: [1], gap: false, single: false },
      { begin: 300, end: 500, videos: [], gap: true, single: false },
      { begin: 500, end: 800, videos: [2], gap: false, single: false },
    ]);
    expect(summary(consecutive)).toEqual([
      { begin: 500, end: 500, videos: [1], gap: false, single: true },
      { begin: 501, end: 501, videos: [2], gap: false, single: true },
    ]);
  });

  it('merges adjacent blocks with identical video sets', () => {
    const blocks = buildTimelineBlocks([
      group(200, 300, [1]),
      group(300, 400, [1]),
      group(400, 500, [2]),
    ]);

    expect(summary(blocks)).toEqual([
      { begin: 200, end: 400, videos: [1], gap: false, single: false },
      { begin: 400, end: 500, videos: [2], gap: false, single: false },
    ]);
  });
});

describe('findAnchorIndex', () => {
  const blocks = buildTimelineBlocks([
    group(200, 300, [1]),
    group(500, 800, [2]),
  ]);

  it('finds the containing block or the nearest older one', () => {
    expect(findAnchorIndex(blocks, 250)).toBe(0);
    expect(findAnchorIndex(blocks, 400)).toBe(1);
    expect(findAnchorIndex(blocks, 600)).toBe(2);
    expect(findAnchorIndex(blocks, 100)).toBe(0);
    expect(findAnchorIndex(blocks, 1000)).toBe(2);
  });
});
