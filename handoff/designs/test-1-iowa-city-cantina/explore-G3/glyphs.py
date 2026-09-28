"""CANTINA drawn as structure: a condensed block letter cut like wood type (chamfered corners; round 3 removed the
V ink traps, which read as chipped corners) with the flat-topped A and spurred C of hand-painted rótulo block lettering.

Units: cap height 100, y down (0 = cap line, 100 = baseline). Each glyph returns (advance, path d).
"""
import math

GAP = 6  # inter-letter space in units (the monument's own tracking)
T_CUT, T_DEPTH = 2.4, 3.0  # ink trap: notch opening and depth


def _trap(pts, idx):
    """Replace the concave corner pts[idx] with a V ink trap cut into the solid."""
    a, p, b = pts[idx - 1], pts[idx], pts[(idx + 1) % len(pts)]
    u1 = ((p[0] - a[0]), (p[1] - a[1])); n1 = math.hypot(*u1); u1 = (u1[0] / n1, u1[1] / n1)
    u2 = ((b[0] - p[0]), (b[1] - p[1])); n2 = math.hypot(*u2); u2 = (u2[0] / n2, u2[1] / n2)
    d = (u1[0] - u2[0], u1[1] - u2[1]); nd = math.hypot(*d); d = (d[0] / nd, d[1] / nd)
    return [(p[0] - u1[0] * T_CUT, p[1] - u1[1] * T_CUT), (p[0] + d[0] * T_DEPTH, p[1] + d[1] * T_DEPTH),
            (p[0] + u2[0] * T_CUT, p[1] + u2[1] * T_CUT)]


USE_TRAPS = False


def _poly(pts, traps=()):
    out = []
    for i, p in enumerate(pts):
        out += _trap(pts, i) if (USE_TRAPS and i in traps) else [p]
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in out) + " Z"


def C():
    w, k = 56, 15
    pts = [(k, 0), (w - 6, 0), (w, 6), (w, 30), (w - 15, 30), (w - 15, 18), (27, 18), (20, 25), (20, 75), (27, 82),
           (w - 15, 82), (w - 15, 70), (w, 70), (w, 94), (w - 6, 100), (k, 100), (0, 100 - k), (0, k)]
    return w, _poly(pts, traps=(5, 10))


def A():
    w = 60
    outer = [(20, 0), (40, 0), (60, 100), (43, 100), (38.6, 78), (21.4, 78), (17, 100), (0, 100)]
    counter = [(30, 35), (35.8, 64), (24.2, 64)]
    return w, _poly(outer, traps=(4, 5)) + " " + _poly(counter)


def N():
    w = 58
    pts = [(0, 6), (6, 0), (22, 0), (41, 58), (41, 0), (52, 0), (58, 6), (58, 100), (36, 100), (17, 42), (17, 100),
           (6, 100), (0, 94)]
    return w, _poly(pts, traps=(3, 9))


def T():
    w = 54
    pts = [(6, 0), (48, 0), (54, 6), (54, 18), (36.5, 18), (36.5, 100), (17.5, 100), (17.5, 18), (0, 18), (0, 6)]
    return w, _poly(pts, traps=(4, 7))


def I():
    w = 19
    pts = [(4, 0), (15, 0), (19, 4), (19, 96), (15, 100), (4, 100), (0, 96), (0, 4)]
    return w, _poly(pts)


GLYPHS = {"C": C, "A": A, "N": N, "T": T, "I": I}


def word(text="CANTINA"):
    """Return (total length in units, path d for the whole word laid along +x)."""
    x, parts = 0.0, []
    for i, ch in enumerate(text):
        w, d = GLYPHS[ch]()
        parts.append(f'<path transform="translate({x:.2f},0)" d="{d}"/>')
        x += w + (GAP if i < len(text) - 1 else 0)
    return x, "".join(parts)
