import numpy as np

CHUNK_SIZE = 16
Y_MAX = 64

BLOCK_AIR   = 0
BLOCK_GRASS = 1
BLOCK_DIRT  = 2
BLOCK_STONE = 3


class PerlinNoise:
    def __init__(self, seed):
        rng = np.random.default_rng(seed & 0xFFFFFFFF)
        p = rng.permutation(256).astype(np.int32)
        self.p = np.concatenate([p, p])

    @staticmethod
    def _fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    @staticmethod
    def _lerp(t, a, b):
        return a + t * (b - a)

    @staticmethod
    def _grad(h, x, y):
        h = h & 15
        u = np.where(h < 8, x, y)
        v = np.where(h < 4, y, np.where((h == 12) | (h == 14), x, 0.0))
        return np.where((h & 1) == 0, u, -u) + np.where((h & 2) == 0, v, -v)

    def noise2d(self, X, Y, freq=1.0):
        X = X * freq
        Y = Y * freq
        xi = np.floor(X).astype(np.int32) & 255
        yi = np.floor(Y).astype(np.int32) & 255
        xf = X - np.floor(X)
        yf = Y - np.floor(Y)
        u = self._fade(xf)
        v = self._fade(yf)
        a  = self.p[xi] + yi
        aa = self.p[a]
        ab = self.p[a + 1]
        b  = self.p[(xi + 1) & 255] + yi
        ba = self.p[b]
        bb = self.p[b + 1]
        x1 = self._lerp(u, self._grad(aa, xf, yf), self._grad(ba, xf - 1, yf))
        x2 = self._lerp(u, self._grad(ab, xf, yf - 1), self._grad(bb, xf - 1, yf - 1))
        return self._lerp(v, x1, x2)

    def octave2d(self, X, Y, octaves=4, persistence=0.5, freq=1.0):
        val = np.zeros_like(X, dtype=np.float64)
        amp = 1.0
        max_amp = 0.0
        f = freq
        for _ in range(octaves):
            val = val + self.noise2d(X, Y, f) * amp
            max_amp += amp
            amp *= persistence
            f *= 2.0
        return val / max_amp


class TerrainGenerator:
    def __init__(self, seed):
        self.seed = seed & 0xFFFFFFFF
        self.n1 = PerlinNoise(self.seed * 2 + 1)
        self.n2 = PerlinNoise(self.seed * 3 + 2)
        self.n3 = PerlinNoise(self.seed * 5 + 3)
        self.base_height = Y_MAX // 2
        self.amplitude = 20

    def generate_chunk(self, chunk_x, chunk_z):
        cx = np.arange(chunk_x * CHUNK_SIZE, (chunk_x + 1) * CHUNK_SIZE, dtype=np.float64)
        cz = np.arange(chunk_z * CHUNK_SIZE, (chunk_z + 1) * CHUNK_SIZE, dtype=np.float64)
        X, Z = np.meshgrid(cx, cz, indexing='ij')

        base   = self.n1.octave2d(X, np.zeros_like(X),  octaves=6, persistence=0.5, freq=0.01)
        detail = self.n2.octave2d(X, np.full_like(X, 100.0), octaves=8, persistence=0.7, freq=0.02)
        h = base * 0.7 + detail * 0.3
        heights = self.base_height + h * self.amplitude

        mountain = np.abs(self.n3.noise2d(X * 0.005, np.zeros_like(X), 1.0))
        heights = np.where(mountain > 0.8, heights + mountain * 30, heights)
        heights = np.clip(heights, 20, Y_MAX - 30).astype(np.int32)

        ys  = np.arange(Y_MAX).reshape(1, Y_MAX, 1)
        h3  = heights[:, None, :]
        blocks = np.zeros((CHUNK_SIZE, Y_MAX, CHUNK_SIZE), dtype=np.int8)
        blocks = np.where(ys <  h3 - 4, BLOCK_STONE, blocks)
        blocks = np.where((ys >= h3 - 4) & (ys < h3 - 1), BLOCK_DIRT,  blocks)
        blocks = np.where(ys == h3 - 1, BLOCK_GRASS, blocks)
        return blocks
