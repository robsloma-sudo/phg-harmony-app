"""The monument as a letterpress pull (round 3).

Three layers, all in glyph units (cap height 100) inside one group that the page rotates and scales:
  1. impression: the forme bites the sheet. A faint darker paper ring (dilated, blurred, offset toward light-fall)
     sits under the letters; it shows only as a deboss edge on the paper around each glyph.
  2. key plate: near-black, with wood grain in the solids (fractal noise stretched along the letter's width axis)
     letting a little paper through, the way a worn wood-type face prints.
  3. chile plate: printed on top as a true overprint (mix-blend-mode: multiply), so red over black goes darker and
     only the mis-registered edges show red. The plate is skewed (a small rotation about the word's centre plus a
     slip along the letter axis): red shows on one side of the strokes at the head of the word and on the other side
     at the foot, so it can never read as a constant drop shadow.
"""

PAPER = "#EFE7D8"


def defs(uid="m", grain_freq=(0.018, 0.42), grain_alpha=(1.5, -0.92), red_grain_alpha=(1.0, -0.7)):
    fx, fy = grain_freq
    ka, kb = grain_alpha
    ra, rb = red_grain_alpha
    return f"""
<defs>
 <filter id="{uid}-grain" x="-2%" y="-2%" width="104%" height="104%" primitiveUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="{fx} {fy}" numOctaves="3" seed="11" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  {ka} 0 0 0 {kb}" result="m"/>
  <feFlood flood-color="{PAPER}" result="p"/>
  <feComposite in="p" in2="m" operator="in" result="pm"/>
  <feComposite in="pm" in2="SourceAlpha" operator="in" result="pmc"/>
  <feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="pmc"/></feMerge>
 </filter>
 <filter id="{uid}-rgrain" x="-2%" y="-2%" width="104%" height="104%" primitiveUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="{fx*1.3:.4f} {fy*0.8:.4f}" numOctaves="3" seed="29" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  {ra} 0 0 0 {rb}" result="m"/>
  <feComposite in="m" in2="SourceAlpha" operator="in" result="mc"/>
  <feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="mc"/></feMerge>
 </filter>
 <filter id="{uid}-bite" x="-3%" y="-3%" width="106%" height="106%" primitiveUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
  <feMorphology in="SourceAlpha" operator="dilate" radius="0.5" result="d"/>
  <feGaussianBlur in="d" stdDeviation="0.5" result="b"/>
  <feOffset in="b" dx="0.5" dy="0.7" result="o"/>
  <feFlood flood-color="#8A7A63" flood-opacity="0.16" result="c"/>
  <feComposite in="c" in2="o" operator="in"/>
 </filter>
</defs>"""


def layers(word_paths, word_len, uid="m", skew_deg=0.9, slip=1.6, red_on=True, grain_on=True, bite_on=True):
    """word_paths: <path> elements for the word in glyph units; returns the three plates."""
    cx = word_len / 2
    out = []
    if bite_on:
        out.append(f'<g filter="url(#{uid}-bite)" fill="#000">{word_paths}</g>')
    key_f = f' filter="url(#{uid}-grain)"' if grain_on else ""
    out.append(f'<g class="plate-key" fill-rule="evenodd"{key_f}>{word_paths}</g>')
    if red_on:
        red_f = f' filter="url(#{uid}-rgrain)"' if grain_on else ""
        out.append(f'<g class="plate-red" fill-rule="evenodd" style="mix-blend-mode:multiply"'
                   f' transform="rotate({skew_deg} {cx:.1f} 50) translate({slip} 0)"{red_f}>{word_paths}</g>')
    return "".join(out)
