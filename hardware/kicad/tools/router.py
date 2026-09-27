"""Grid maze-router for the Torqeedo control board (A*, 2 layers, GND plane on B.Cu)."""
import pcbnew, numpy as np, heapq, math
from scipy.ndimage import distance_transform_edt

CELL      = 0.15     # grid pitch, mm
CLEAR     = 0.25     # copper clearance, mm
VIA_D     = 0.7      # via pad diameter, mm
VIA_DRILL = 0.35
EDGE_KEEP = 0.60     # copper-to-board-edge keepout, mm
VIA_COST  = 2.5      # mm-equivalent penalty per via
BCU_MULT  = 1.6      # discourage B.Cu (it is the ground plane)

WIDTH = {'/+12V_IN': 0.8, '/+12V_PROT': 0.8, '/+5V': 0.5, '/GND': 0.5}
DEF_W = 0.25
def wof(net): return WIDTH.get(net, DEF_W)

F, B = 0, 1
LAYER = {F: pcbnew.F_Cu, B: pcbnew.B_Cu}


class Grid:
    def __init__(self, bw, bh, holes):
        self.bw, self.bh = bw, bh
        self.nx = int(bw / CELL) + 1
        self.ny = int(bh / CELL) + 1
        # obstacle primitives: (layermask, net, kind, params)  kind: 'rect'|'circ'
        self.obs = []
        self.base = np.zeros((self.ny, self.nx), bool)   # edges + holes, blocks everything
        xs = np.arange(self.nx) * CELL
        ys = np.arange(self.ny) * CELL
        X, Y = np.meshgrid(xs, ys)
        self.X, self.Y = X, Y
        self.base |= (X < EDGE_KEEP) | (X > bw - EDGE_KEEP) | (Y < EDGE_KEEP) | (Y > bh - EDGE_KEEP)
        for hx, hy in holes:
            self.base |= ((X - hx) ** 2 + (Y - hy) ** 2) < (1.6 + CLEAR + 0.4) ** 2

    def add_rect(self, net, x0, y0, x1, y1, layers):
        self.obs.append((layers, net, 'rect', (x0, y0, x1, y1)))

    def add_circ(self, net, cx, cy, r, layers):
        self.obs.append((layers, net, 'circ', (cx, cy, r)))

    def add_seg(self, net, x0, y0, x1, y1, hw, layers):
        self.obs.append((layers, net, 'seg', (x0, y0, x1, y1, hw)))

    def cell(self, x, y):
        return (min(max(int(round(x / CELL)), 0), self.nx - 1),
                min(max(int(round(y / CELL)), 0), self.ny - 1))

    def blocked_for(self, net, infl):
        """bool (2,ny,nx): cells a track of this net (inflated by `infl`) may not occupy."""
        out = np.zeros((2, self.ny, self.nx), bool)
        out[F] |= self.base
        out[B] |= self.base
        for layers, onet, kind, prm in self.obs:
            if onet == net:
                continue
            if kind == 'rect':
                x0, y0, x1, y1 = prm
                i0 = max(int((x0 - infl) / CELL), 0);      i1 = min(int((x1 + infl) / CELL) + 1, self.nx)
                j0 = max(int((y0 - infl) / CELL), 0);      j1 = min(int((y1 + infl) / CELL) + 1, self.ny)
                if i0 >= i1 or j0 >= j1:
                    continue
                for L in layers:
                    out[L, j0:j1, i0:i1] = True
            elif kind == 'seg':
                x0, y0, x1, y1, hw = prm
                R = hw + infl
                i0 = max(int((min(x0,x1)-R)/CELL), 0); i1 = min(int((max(x0,x1)+R)/CELL)+1, self.nx)
                j0 = max(int((min(y0,y1)-R)/CELL), 0); j1 = min(int((max(y0,y1)+R)/CELL)+1, self.ny)
                if i0 >= i1 or j0 >= j1:
                    continue
                px = self.X[j0:j1, i0:i1] - x0; py = self.Y[j0:j1, i0:i1] - y0
                dx, dy = x1 - x0, y1 - y0
                L2 = dx*dx + dy*dy
                t = 0.0 if L2 == 0 else np.clip((px*dx + py*dy) / L2, 0.0, 1.0)
                d2 = (px - t*dx)**2 + (py - t*dy)**2
                sub = d2 < R*R
                for L in layers:
                    out[L, j0:j1, i0:i1] |= sub
            else:
                cx, cy, r = prm
                R = r + infl
                i0 = max(int((cx - R) / CELL), 0);        i1 = min(int((cx + R) / CELL) + 1, self.nx)
                j0 = max(int((cy - R) / CELL), 0);        j1 = min(int((cy + R) / CELL) + 1, self.ny)
                if i0 >= i1 or j0 >= j1:
                    continue
                sub = ((self.X[j0:j1, i0:i1] - cx) ** 2 + (self.Y[j0:j1, i0:i1] - cy) ** 2) < R * R
                for L in layers:
                    out[L, j0:j1, i0:i1] |= sub
        return out


def astar(g, blocked, viaok, starts, targets):
    """targets: bool (2,ny,nx). returns list of (layer,ix,iy) or None."""
    ny, nx = g.ny, g.nx
    t2d = targets[F] | targets[B]
    if not t2d.any():
        return None
    h2d = distance_transform_edt(~t2d, sampling=(CELL, CELL)).astype(np.float32)

    INF = np.float32(1e18)
    gsc = np.full((2, ny, nx), INF, np.float32)
    par = np.full((2, ny, nx), -1, np.int64)
    pq = []
    for (L, i, j) in starts:
        if blocked[L, j, i]:
            continue
        gsc[L, j, i] = 0.0
        heapq.heappush(pq, (h2d[j, i], 0.0, L, i, j))
    D = [(1,0,CELL),(-1,0,CELL),(0,1,CELL),(0,-1,CELL),
         (1,1,CELL*1.41421),(1,-1,CELL*1.41421),(-1,1,CELL*1.41421),(-1,-1,CELL*1.41421)]
    while pq:
        f, cost, L, i, j = heapq.heappop(pq)
        if cost > gsc[L, j, i]:
            continue
        if targets[L, j, i]:
            path = []
            cl, ci, cj = L, i, j
            while True:
                path.append((int(cl), int(ci), int(cj)))
                p = par[cl, cj, ci]
                if p < 0:
                    break
                cl, ci, cj = p // (nx * ny), (p % (nx * ny)) % nx, (p % (nx * ny)) // nx
            return path[::-1]
        mult = 1.0 if L == F else BCU_MULT
        for dx, dy, step in D:
            ni, nj = i + dx, j + dy
            if ni < 0 or nj < 0 or ni >= nx or nj >= ny or blocked[L, nj, ni]:
                continue
            if dx and dy and (blocked[L, j, ni] or blocked[L, nj, i]):
                continue                      # no corner cutting
            nc = cost + step * mult
            if nc < gsc[L, nj, ni]:
                gsc[L, nj, ni] = nc
                par[L, nj, ni] = L * nx * ny + j * nx + i
                heapq.heappush(pq, (nc + h2d[nj, ni], nc, L, ni, nj))
        # via
        nl = 1 - L
        if viaok[j, i] and not blocked[nl, j, i]:
            nc = cost + VIA_COST
            if nc < gsc[nl, j, i]:
                gsc[nl, j, i] = nc
                par[nl, j, i] = L * nx * ny + j * nx + i
                heapq.heappush(pq, (nc + h2d[j, i], nc, nl, i, j))
    return None


def simplify(path):
    """collapse a cell path into (layer, [(i,j)...]) runs with collinear points removed"""
    runs, cur, curL = [], [], path[0][0]
    for (L, i, j) in path:
        if L != curL:
            runs.append((curL, cur)); cur = [(i, j)]; curL = L
        else:
            cur.append((i, j))
    runs.append((curL, cur))
    out = []
    for L, pts in runs:
        if len(pts) < 2:
            out.append((L, pts)); continue
        keep = [pts[0]]
        for k in range(1, len(pts) - 1):
            ax, ay = pts[k][0]-pts[k-1][0], pts[k][1]-pts[k-1][1]
            bx, by = pts[k+1][0]-pts[k][0], pts[k+1][1]-pts[k][1]
            if (ax, ay) != (bx, by):
                keep.append(pts[k])
        keep.append(pts[-1])
        out.append((L, keep))
    return out


# ---------- path straightening (pull staircases taut, keep 45-degree geometry) ----------
def seg_clear(blk, L, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    n = max(abs(dx), abs(dy))
    if n == 0:
        return True
    if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
        return False
    sx = (dx > 0) - (dx < 0); sy = (dy > 0) - (dy < 0)
    x, y = a
    for _ in range(n):
        x += sx; y += sy
        if blk[L, y, x]:
            return False
        if sx and sy and (blk[L, y-sy, x] and blk[L, y, x-sx]):
            return False
    return True


def corners(a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    if dx == 0 or dy == 0 or abs(dx) == abs(dy):
        return [None]
    sx = (dx > 0) - (dx < 0); sy = (dy > 0) - (dy < 0)
    m = min(abs(dx), abs(dy))
    out = [(a[0]+sx*m, a[1]+sy*m)]            # diagonal leg first
    out.append((b[0]-sx*m, b[1]-sy*m))        # straight leg first
    return out


def taut(blk, L, pts, window=80, passes=3):
    pts = [(int(a), int(b)) for a, b in pts]
    for _ in range(passes):
        changed = False
        i = 0
        while i < len(pts) - 2:
            hi = min(len(pts) - 1, i + window)
            for j in range(hi, i + 1, -1):
                done = False
                for c in corners(pts[i], pts[j]):
                    if c is None:
                        if seg_clear(blk, L, pts[i], pts[j]):
                            pts[i+1:j] = []; done = True; break
                    else:
                        if seg_clear(blk, L, pts[i], c) and seg_clear(blk, L, c, pts[j]):
                            pts[i+1:j] = [c]; done = True; break
                if done:
                    changed = True; break
            i += 1
        if not changed:
            break
    return pts
