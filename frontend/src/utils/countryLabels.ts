import * as d3 from 'd3'

export type CountryLabelOptions = {
  fontSize: number
  fontFamily: string
  /** Расстояние между строками (для одной строки — фактически высота плашки). */
  lineHeight?: number
  paddingX?: number
  paddingY?: number
}

export type CountryLabel = {
  id: string
  name: string
  /** Координата центра подписи в системе координат проекции. */
  x: number
  y: number
  /** Угол поворота в градусах, всегда в диапазоне [-90, 90). */
  angle: number
  /** Ширина текста в пикселях при базовом размере шрифта. */
  width: number
  /** Минимальный масштаб, при котором подпись помещается внутри страны. */
  minZoom: number
  /** Площадь главного полигона — для приоритета при пересечении подписей. */
  area: number
}

export type CountryLabelVisibilityOptions = {
  lineHeight: number
  paddingX?: number
  paddingY?: number
}

type Point = [number, number]
type PolygonRect = {
  angle: number
  aspect: number
}

type AngleCandidate = {
  angle: number
  x: number
  y: number
  minZoom: number
}

type Obb = {
  cx: number
  cy: number
  hw: number
  hh: number
  cos: number
  sin: number
}

/** Шаг перебора углов при уточнении наклона. */
const ANGLE_STEP = 5
/** Насколько вытянутой должна быть страна, чтобы подпись класть вдоль её оси. */
const ROTATE_ASPECT_THRESHOLD = 2
/** Насколько градусов уточняем наклон вокруг длинной оси. */
const ANGLE_REFINEMENT = 10

/**
 * Собирает кольца полигонов в экранных координатах.
 *
 * Используется контекст d3.geoPath, а не прямая проекция координат: так d3 сам
 * обрезает полигоны по антимеридиану и краям проекции. Иначе, например, Россия
 * или Фиджи дают кольцо, растянутое через всю карту.
 */
function collectRings(feature: GeoJSON.Feature, projection: d3.GeoProjection): Point[][] {
  const rings: Point[][] = []
  let current: Point[] | null = null

  const context = {
    moveTo(x: number, y: number) {
      current = [[x, y]]
      rings.push(current)
    },
    lineTo(x: number, y: number) {
      current?.push([x, y])
    },
    closePath() {
      current = null
    },
  }

  d3.geoPath(projection, context as unknown as d3.GeoContext)(
    feature as unknown as d3.GeoPermissibleObjects,
  )

  return rings.filter((ring) => ring.length >= 3)
}

function distanceToRingSq(px: number, py: number, ring: Point[]): number {
  let best = Infinity

  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [ax, ay] = ring[j]!
    const [bx, by] = ring[i]!
    const dx = bx - ax
    const dy = by - ay
    const lengthSq = dx * dx + dy * dy
    let t = lengthSq > 0 ? ((px - ax) * dx + (py - ay) * dy) / lengthSq : 0
    t = Math.max(0, Math.min(1, t))
    const qx = ax + t * dx - px
    const qy = ay + t * dy - py
    const distanceSq = qx * qx + qy * qy
    if (distanceSq < best) best = distanceSq
  }

  return best
}

/**
 * Pole of inaccessibility: точка внутри полигона, максимально удалённая от границ.
 * Нужна потому, что обычный centroid у вогнутых стран (Хорватия, Норвегия,
 * Вьетнам) часто попадает в море или в соседнюю страну.
 */
function poleOfInaccessibility(ring: Point[]): { x: number; y: number } {
  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity

  for (const [x, y] of ring) {
    if (x < minX) minX = x
    if (y < minY) minY = y
    if (x > maxX) maxX = x
    if (y > maxY) maxY = y
  }

  const width = maxX - minX
  const height = maxY - minY
  const cells = Math.min(16, Math.max(4, Math.round(Math.max(width, height) / 2)))

  let bestX = (minX + maxX) / 2
  let bestY = (minY + maxY) / 2
  let bestDistance = -1

  for (let i = 0; i <= cells; i++) {
    for (let j = 0; j <= cells; j++) {
      const x = minX + (width * i) / cells
      const y = minY + (height * j) / cells
      if (!d3.polygonContains(ring, [x, y])) continue
      const distance = distanceToRingSq(x, y, ring)
      if (distance > bestDistance) {
        bestDistance = distance
        bestX = x
        bestY = y
      }
    }
  }

  let step = Math.max(width, height) / cells
  const directions: Array<[number, number]> = [
    [-1, -1],
    [0, -1],
    [1, -1],
    [-1, 0],
    [1, 0],
    [-1, 1],
    [0, 1],
    [1, 1],
  ]

  while (step > 0.25) {
    let improved = false
    for (const [dx, dy] of directions) {
      const x = bestX + dx * step
      const y = bestY + dy * step
      if (!d3.polygonContains(ring, [x, y])) continue
      const distance = distanceToRingSq(x, y, ring)
      if (distance > bestDistance) {
        bestDistance = distance
        bestX = x
        bestY = y
        improved = true
      }
    }
    if (!improved) step /= 2
  }

  return { x: bestX, y: bestY }
}

function normalizeAngle(angle: number): number {
  let result = angle
  while (result > Math.PI / 2) result -= Math.PI
  while (result < -Math.PI / 2) result += Math.PI
  return result
}

/**
 * Минимальный по площади прямоугольник вокруг формы (rotating calipers по
 * выпуклой оболочке). Его длинная сторона задаёт «естественный» наклон подписи.
 */
function preferredRect(ring: Point[]): PolygonRect {
  const hull = d3.polygonHull(ring)
  if (!hull || hull.length < 3) return { angle: 0, aspect: 1 }

  let bestArea = Infinity
  let bestAngle = 0
  let bestWidth = 1
  let bestHeight = 1

  for (let i = 0; i < hull.length; i++) {
    const a = hull[i]!
    const b = hull[(i + 1) % hull.length]!
    const angle = Math.atan2(b[1] - a[1], b[0] - a[0])
    const cos = Math.cos(angle)
    const sin = Math.sin(angle)

    let minU = Infinity
    let maxU = -Infinity
    let minV = Infinity
    let maxV = -Infinity

    for (const [x, y] of hull) {
      const u = x * cos + y * sin
      const v = -x * sin + y * cos
      if (u < minU) minU = u
      if (u > maxU) maxU = u
      if (v < minV) minV = v
      if (v > maxV) maxV = v
    }

    const width = maxU - minU
    const height = maxV - minV
    const area = width * height
    if (area < bestArea) {
      bestArea = area
      bestAngle = angle
      bestWidth = width
      bestHeight = height
    }
  }

  let angle = bestAngle
  if (bestHeight > bestWidth) angle += Math.PI / 2

  return {
    angle: normalizeAngle(angle),
    aspect: Math.max(bestWidth, bestHeight) / Math.max(Math.min(bestWidth, bestHeight), 1e-6),
  }
}

/** Отрезок прямой (через точку p в направлении d), лежащий внутри полигона. */
function chordThrough(
  px: number,
  py: number,
  dx: number,
  dy: number,
  ring: Point[],
): { t0: number; t1: number } | null {
  const crossings: number[] = []

  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [ax, ay] = ring[j]!
    const [bx, by] = ring[i]!
    const ex = bx - ax
    const ey = by - ay
    const denominator = dx * ey - dy * ex
    if (Math.abs(denominator) < 1e-12) continue

    const qx = ax - px
    const qy = ay - py
    const t = (qx * ey - qy * ex) / denominator
    const s = (qx * dy - qy * dx) / denominator
    if (s >= -1e-9 && s <= 1 + 1e-9) crossings.push(t)
  }

  crossings.sort((a, b) => a - b)

  for (let i = 0; i + 1 < crossings.length; i++) {
    const t0 = crossings[i]!
    const t1 = crossings[i + 1]!
    if (t0 <= 1e-9 && t1 >= -1e-9) return { t0, t1 }
  }

  return null
}

/** Расстояние от точки до границы вдоль луча. */
function rayDistance(px: number, py: number, dx: number, dy: number, ring: Point[]): number {
  let best = Infinity

  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [ax, ay] = ring[j]!
    const [bx, by] = ring[i]!
    const ex = bx - ax
    const ey = by - ay
    const denominator = dx * ey - dy * ex
    if (Math.abs(denominator) < 1e-12) continue

    const qx = ax - px
    const qy = ay - py
    const t = (qx * ey - qy * ex) / denominator
    const s = (qx * dy - qy * dx) / denominator
    if (t > 1e-9 && s >= -1e-9 && s <= 1 + 1e-9 && t < best) best = t
  }

  return best
}

function createTextMeasurer(fontSize: number, fontFamily: string): (text: string) => number {
  const fallback = (text: string) => text.length * fontSize * 0.6

  if (typeof document === 'undefined') return fallback

  const context = document.createElement('canvas').getContext('2d')
  if (!context) return fallback

  context.font = `${fontSize}px ${fontFamily}`
  const cache = new Map<string, number>()

  return (text: string) => {
    const cached = cache.get(text)
    if (cached !== undefined) return cached
    const width = context.measureText(text).width
    cache.set(text, width)
    return width
  }
}

function evaluateAngle(
  anchor: { x: number; y: number },
  angle: number,
  ring: Point[],
  neededWidth: number,
  neededHeight: number,
): AngleCandidate | null {
  const cos = Math.cos(angle)
  const sin = Math.sin(angle)
  const chord = chordThrough(anchor.x, anchor.y, cos, sin, ring)
  if (!chord) return null

  // Центрируем подпись не в точке polylabel, а посередине хорды вдоль текста.
  // Для вытянутых стран это даёт заметно больше места (Италия, Норвегия, Чили).
  const offset = (chord.t0 + chord.t1) / 2
  const x = anchor.x + cos * offset
  const y = anchor.y + sin * offset
  const halfWidth = (chord.t1 - chord.t0) / 2

  const up = rayDistance(x, y, -sin, cos, ring)
  const down = rayDistance(x, y, sin, -cos, ring)
  const halfHeight = Math.min(up, down)

  if (!Number.isFinite(halfHeight) || halfWidth <= 0 || halfHeight <= 0) return null

  const minZoom = Math.max(neededWidth / (2 * halfWidth), neededHeight / (2 * halfHeight), 1)

  return { angle, x, y, minZoom }
}

export function buildCountryLabels(
  features: readonly GeoJSON.Feature[],
  projection: d3.GeoProjection,
  options: CountryLabelOptions,
): CountryLabel[] {
  const fontSize = options.fontSize
  const lineHeight = options.lineHeight ?? fontSize * 1.15
  const paddingX = options.paddingX ?? 2
  const paddingY = options.paddingY ?? 1
  const measureText = createTextMeasurer(fontSize, options.fontFamily)
  const labels: CountryLabel[] = []

  for (const feature of features) {
    const name = feature.properties?.name
    if (typeof name !== 'string' || !name.trim()) continue

    const rings = collectRings(feature, projection)
    if (!rings.length) continue

    // Для подписи достаточно самого большого куска суши: у США это материк,
    // а не Аляска или Гавайи.
    let ring = rings[0]!
    let area = Math.abs(d3.polygonArea(ring))
    for (let i = 1; i < rings.length; i++) {
      const candidate = rings[i]!
      const candidateArea = Math.abs(d3.polygonArea(candidate))
      if (candidateArea > area) {
        ring = candidate
        area = candidateArea
      }
    }

    const anchor = poleOfInaccessibility(ring)
    const rect = preferredRect(ring)
    const textWidth = measureText(name)
    const neededWidth = textWidth + paddingX * 2
    const neededHeight = lineHeight + paddingY * 2
    const isElongated = rect.aspect >= ROTATE_ASPECT_THRESHOLD

    // Компактные страны подписываем горизонтально, вытянутые — вдоль длинной
    // оси. Вокруг этой оси дополнительно ищем положение с максимальным запасом
    // места: форма может быть изогнутой, и «идеальный» угол не всегда лучший.
    const preferredAngle = isElongated ? rect.angle : 0
    const angles = [preferredAngle]
    if (isElongated) {
      const refinement = (ANGLE_REFINEMENT * Math.PI) / 180
      const step = (ANGLE_STEP * Math.PI) / 180
      for (let offset = -refinement; offset <= refinement; offset += step) {
        if (offset !== 0) angles.push(normalizeAngle(preferredAngle + offset))
      }
    }

    let chosen: AngleCandidate | null = null
    for (const angle of angles) {
      const candidate = evaluateAngle(anchor, angle, ring, neededWidth, neededHeight)
      if (candidate && (!chosen || candidate.minZoom < chosen.minZoom)) chosen = candidate
    }

    // Страховка для совсем нестандартных форм: если вдоль оси места нет,
    // пробуем найти хоть какой-то подходящий угол.
    if (!chosen) {
      for (let degrees = -90; degrees < 90; degrees += ANGLE_STEP) {
        const angle = (degrees * Math.PI) / 180
        const candidate = evaluateAngle(anchor, angle, ring, neededWidth, neededHeight)
        if (candidate && (!chosen || candidate.minZoom < chosen.minZoom)) chosen = candidate
      }
    }

    if (!chosen) continue

    const id = feature.properties?.id
    labels.push({
      id: typeof id === 'string' || typeof id === 'number' ? String(id) : name,
      name,
      x: chosen.x,
      y: chosen.y,
      angle: (chosen.angle * 180) / Math.PI,
      width: textWidth,
      minZoom: chosen.minZoom,
      area,
    })
  }

  return labels
}

function obbOverlap(a: Obb, b: Obb): boolean {
  const dx = b.cx - a.cx
  const dy = b.cy - a.cy
  const axes: Array<[number, number]> = [
    [a.cos, a.sin],
    [-a.sin, a.cos],
    [b.cos, b.sin],
    [-b.sin, b.cos],
  ]

  for (const [ux, uy] of axes) {
    const distance = Math.abs(dx * ux + dy * uy)
    const radiusA =
      a.hw * Math.abs(a.cos * ux + a.sin * uy) + a.hh * Math.abs(-a.sin * ux + a.cos * uy)
    const radiusB =
      b.hw * Math.abs(b.cos * ux + b.sin * uy) + b.hh * Math.abs(-b.sin * ux + b.cos * uy)
    if (distance > radiusA + radiusB) return false
  }

  return true
}

/**
 * Отбирает подписи, которые помещаются при текущем масштабе, и убирает
 * пересекающиеся. Более крупные страны (меньший minZoom) имеют приоритет.
 */
export function visibleCountryLabels(
  labels: readonly CountryLabel[],
  scale: number,
  options: CountryLabelVisibilityOptions,
): CountryLabel[] {
  const paddingX = options.paddingX ?? 2
  const paddingY = options.paddingY ?? 1
  const lineHeight = options.lineHeight

  const candidates = labels
    .filter((label) => label.minZoom <= scale + 1e-6)
    .sort((a, b) => a.minZoom - b.minZoom || b.area - a.area)

  const accepted: CountryLabel[] = []
  const boxes: Obb[] = []

  for (const label of candidates) {
    const radians = (label.angle * Math.PI) / 180
    const box: Obb = {
      cx: label.x * scale,
      cy: label.y * scale,
      hw: label.width / 2 + paddingX,
      hh: lineHeight / 2 + paddingY,
      cos: Math.cos(radians),
      sin: Math.sin(radians),
    }

    if (boxes.some((other) => obbOverlap(box, other))) continue

    accepted.push(label)
    boxes.push(box)
  }

  return accepted
}
