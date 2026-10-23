export const years: number[] = [
  ...Array.from(
    { length: 20 },
    (_, i) => -3000 + i * 100
  ),
  ...Array.from(
    { length: 280 },
    (_, i) => -1000 + i * 10
  ),
  ...Array.from(
    { length: 201 },
    (_, i) => 1800 + i
  ),
  2010,
  2020,
  2025,
];
