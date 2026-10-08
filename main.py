import ctypes, math
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Callback
from kivy.graphics.opengl import *

from terrain import TerrainGenerator, CHUNK_SIZE, Y_MAX
from renderer import build_mesh


VS = """
attribute vec3 p;
attribute vec3 c;
uniform mat4 m;
varying vec3 v;
void main() {
    gl_Position = m * vec4(p, 1.0);
    v = c;
}
"""

FS = """
precision mediump float;
varying vec3 v;
void main() {
    gl_FragColor = vec4(v, 1.0);
}
"""


def f32(d): return (ctypes.c_float * len(d))(*d)
def u32(d): return (ctypes.c_uint * len(d))(*d)


def persp(fov, asp, n, f):
    t = 1.0 / math.tan(math.radians(fov) / 2)
    return [t/asp,0,0,0, 0,t,0,0, 0,0,(f+n)/(n-f),-1, 0,0,2*f*n/(n-f),0]


def mul(a, b):
    r = [0.0] * 16
    for i in range(4):
        for j in range(4):
            s = 0.0
            for k in range(4):
                s += a[k*4+j] * b[i*4+k]
            r[i*4+j] = s
    return r


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return [c,0,-s,0, 0,1,0,0, s,0,c,0, 0,0,0,1]


def trans(x, y, z):
    return [1,0,0,0, 0,1,0,0, 0,0,1,0, x,y,z,1]


class Sandbox(Widget):
    def __init__(s, **kw):
        super().__init__(**kw)
        s.prog = None
        s.vbo = None
        s.ebo = None
        s.u_mvp = None
        s.n_idx = 0
        s.ok = False
        s.angle = 0.0
        with s.canvas:
            Callback(s._init)
            Callback(s._draw)
        Clock.schedule_interval(s._upd, 1/60.0)

    def _init(s, *a, **k):
        if s.ok: return
        try:
            print("[gl] generating terrain...")
            gen = TerrainGenerator(seed=12345)
            blocks = gen.generate_chunk(0, 0)
            verts, idx = build_mesh(blocks)
            s.n_idx = len(idx)
            print("[gl] mesh: %d verts, %d indices" % (len(verts)//6, len(idx)))

            vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vs, VS.encode())
            glCompileShader(vs)
            fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fs, FS.encode())
            glCompileShader(fs)
            p = glCreateProgram()
            glAttachShader(p, vs); glAttachShader(p, fs)
            glBindAttribLocation(p, 0, b"p")
            glBindAttribLocation(p, 1, b"c")
            glLinkProgram(p)
            s.prog = p
            s.u_mvp = glGetUniformLocation(p, b"m")

            v = glGenBuffers(1)[0]; s.vbo = v
            glBindBuffer(GL_ARRAY_BUFFER, v)
            glBufferData(GL_ARRAY_BUFFER, len(verts)*4, bytes(f32(verts)), GL_STATIC_DRAW)
            e = glGenBuffers(1)[0]; s.ebo = e
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, e)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(idx)*4, bytes(u32(idx)), GL_STATIC_DRAW)
            glEnable(GL_DEPTH_TEST)
            s.ok = True
            print("[gl] init ok")
        except Exception as ex:
            import traceback
            print("[gl] init fail: %s" % ex)
            traceback.print_exc()

    def _upd(s, dt):
        s.angle += dt * 0.4
        s.canvas.ask_update()

    def _draw(s, *a, **k):
        if not s.ok: return
        try:
            glClearColor(0.45, 0.65, 0.90, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glUseProgram(s.prog)

            w, h = Window.size
            proj = persp(60.0, w / max(h, 1), 0.1, 500.0)
            # 视角绕原点转，chunk 先平移到原点（中心 8,32,8）
            view = mul(trans(0, -32, -70), rot_y(s.angle))
            model = trans(-8, 0, -8)
            mvp = mul(proj, mul(view, model))

            glUniformMatrix4fv(s.u_mvp, 1, GL_FALSE, bytes(f32(mvp)))

            glBindBuffer(GL_ARRAY_BUFFER, s.vbo)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, s.ebo)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, None)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, 12)
            glEnableVertexAttribArray(1)
            glDrawElements(GL_TRIANGLES, s.n_idx, GL_UNSIGNED_INT, None)
        except Exception as ex:
            import traceback
            print("[gl] draw fail: %s" % ex)
            traceback.print_exc()


class SandboxApp(App):
    def build(s):
        Window.clearcolor = (0.45, 0.65, 0.90, 1.0)
        return Sandbox()


if __name__ == "__main__":
    SandboxApp().run()
