import ctypes, math
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Callback
from kivy.graphics.opengl import *

VS = "attribute vec3 p; attribute vec3 c; uniform mat4 m; varying vec3 v; void main(){ gl_Position=m*vec4(p,1.0); v=c; }"
FS = "precision mediump float; varying vec3 v; void main(){ gl_FragColor=vec4(v,1.0); }"

V = [-0.5,-0.5,0.5,1,0,0,  0.5,-0.5,0.5,1,0,0,  0.5,0.5,0.5,1,0,0, -0.5,0.5,0.5,1,0,0,
      0.5,-0.5,-0.5,0,1,0, -0.5,-0.5,-0.5,0,1,0, -0.5,0.5,-0.5,0,1,0,  0.5,0.5,-0.5,0,1,0,
     -0.5,-0.5,-0.5,0,0,1, -0.5,-0.5,0.5,0,0,1, -0.5,0.5,0.5,0,0,1, -0.5,0.5,-0.5,0,0,1,
      0.5,-0.5,0.5,1,1,0,  0.5,-0.5,-0.5,1,1,0,  0.5,0.5,-0.5,1,1,0,  0.5,0.5,0.5,1,1,0,
     -0.5,0.5,0.5,0,1,1,   0.5,0.5,0.5,0,1,1,   0.5,0.5,-0.5,0,1,1, -0.5,0.5,-0.5,0,1,1,
     -0.5,-0.5,-0.5,1,0,1, 0.5,-0.5,-0.5,1,0,1, 0.5,-0.5,0.5,1,0,1, -0.5,-0.5,0.5,1,0,1]
I = [0,1,2,0,2,3, 4,5,6,4,6,7, 8,9,10,8,10,11, 12,13,14,12,14,15,
     16,17,18,16,18,19, 20,21,22,20,22,23]

def f32(d): return (ctypes.c_float*len(d))(*d)
def u32(d): return (ctypes.c_uint*len(d))(*d)

def persp(fov,asp,n,f):
    t = 1.0/math.tan(math.radians(fov)/2)
    return [t/asp,0,0,0, 0,t,0,0, 0,0,(f+n)/(n-f),-1, 0,0,2*f*n/(n-f),0]

def mm(a,b):
    r = [0]*16
    for i in range(4):
        for j in range(4):
            r[i*4+j] = sum(a[k*4+j]*b[i*4+k] for k in range(4))
    return r

def ry(a):
    c,s = math.cos(a),math.sin(a)
    return [c,0,-s,0, 0,1,0,0, s,0,c,0, 0,0,0,1]

def rx(a):
    c,s = math.cos(a),math.sin(a)
    return [1,0,0,0, 0,c,s,0, 0,-s,c,0, 0,0,0,1]

def tr(x,y,z):
    return [1,0,0,0, 0,1,0,0, 0,0,1,0, x,y,z,1]

class Cube(Widget):
    def __init__(s, **kw):
        super().__init__(**kw)
        s.p=None; s.v=None; s.e=None; s.u=None
        s.ax=0.0; s.ay=0.0; s.ok=False
        with s.canvas:
            Callback(s._init)
            Callback(s._draw)
        Clock.schedule_interval(s._upd, 1/60.0)

    def _init(s, *a, **k):
        if s.ok: return
        try:
            vs = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vs, VS.encode())
            glCompileShader(vs)
            fs = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fs, FS.encode())
            glCompileShader(fs)
            p = glCreateProgram()
            glAttachShader(p, vs)
            glAttachShader(p, fs)
            glBindAttribLocation(p, 0, b"p")
            glBindAttribLocation(p, 1, b"c")
            glLinkProgram(p)
            s.p = p
            s.u = glGetUniformLocation(p, b"m")
            v = glGenBuffers(1); s.v = v
            glBindBuffer(GL_ARRAY_BUFFER, v)
            s._vd=f32(V); glBufferData(GL_ARRAY_BUFFER, len(V)*4, ctypes.addressof(s._vd), GL_STATIC_DRAW)
            e = glGenBuffers(1); s.e = e
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, e)
            s._ed=u32(I); glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(I)*4, ctypes.addressof(s._ed), GL_STATIC_DRAW)
            glEnable(GL_DEPTH_TEST)
            s.ok = True
            print("[gl] init ok, prog=%s u=%s" % (p, s.u))
        except Exception as ex:
            print("[gl] init fail: %s" % ex); import traceback; traceback.print_exc()

    def _upd(s, dt):
        s.ax += dt*0.7
        s.ay += dt*1.2
        s.canvas.ask_update()

    def _draw(s, *a, **k):
        if not s.ok: return
        try:
            glClearColor(0.1, 0.1, 0.15, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glUseProgram(s.p)
            w, h = Window.size
            proj = persp(60.0, w/max(h,1), 0.1, 100.0)
            view = tr(0,0,-3)
            model = mm(ry(s.ay), rx(s.ax))
            mvp = mm(proj, mm(view, model))
            glUniformMatrix4fv(s.u, 1, GL_FALSE, f32(mvp))
            glBindBuffer(GL_ARRAY_BUFFER, s.v)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, s.e)
            glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,24,0)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,24,12)
            glEnableVertexAttribArray(1)
            glDrawElements(GL_TRIANGLES, len(I), GL_UNSIGNED_INT, 0)
        except Exception as ex:
            print("[gl] draw fail: %s" % ex)

class S(App):
    def build(s):
        Window.clearcolor = (0.1, 0.1, 0.15, 1.0)
        return Cube()

if __name__ == "__main__":
    S().run()
