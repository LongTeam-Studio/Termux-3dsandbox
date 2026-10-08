import numpy as np


BLOCK_COLORS = {
    1: (0.35, 0.75, 0.35),   # 草 - 绿
    2: (0.55, 0.40, 0.25),   # 泥土 - 棕
    3: (0.55, 0.55, 0.60),   # 石头 - 灰
}

# 6 个面: (法向, 4 个角顶点偏移) 逆时针
FACES = [
    (( 0, 0, 1), [(0,0,1),(1,0,1),(1,1,1),(0,1,1)]),  # +Z
    (( 0, 0,-1), [(1,0,0),(0,0,0),(0,1,0),(1,1,0)]),  # -Z
    ((-1, 0, 0), [(0,0,0),(0,0,1),(0,1,1),(0,1,0)]),  # -X
    (( 1, 0, 0), [(1,0,1),(1,0,0),(1,1,0),(1,1,1)]),  # +X
    (( 0, 1, 0), [(0,1,1),(1,1,1),(1,1,0),(0,1,0)]),  # +Y
    (( 0,-1, 0), [(0,0,0),(1,0,0),(1,0,1),(0,0,1)]),  # -Y
]


def build_mesh(blocks):
    """blocks: (SX, SY, SZ) int8 数组
    返回 (verts_float32, indices_uint32)"""
    SX, SY, SZ = blocks.shape
    solid = (blocks != 0)
    padded = np.pad(solid, 1, mode='constant', constant_values=False)

    verts = []
    idx = []
    vc = 0

    for (nx, ny, nz), face in FACES:
        neighbor = padded[1+nx:1+nx+SX, 1+ny:1+ny+SY, 1+nz:1+nz+SZ]
        visible = solid & (~neighbor)
        xs, ys, zs = np.where(visible)
        for i in range(len(xs)):
            x, y, z = int(xs[i]), int(ys[i]), int(zs[i])
            bid = int(blocks[x, y, z])
            r, g, b = BLOCK_COLORS.get(bid, (1.0, 0.0, 1.0))
            for dx, dy, dz in face:
                verts.extend([x + dx, y + dy, z + dz, r, g, b])
            idx.extend([vc, vc+1, vc+2, vc, vc+2, vc+3])
            vc += 4

    return verts, idx
