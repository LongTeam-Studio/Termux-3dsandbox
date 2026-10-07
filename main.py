import ctypes, math
import pyglet
from pyglet import gl
from pyglet.window import key

pyglet.options.backend = "gles3"
cfg = pyglet.config.Config()
cfg.gles3.major_version = 3
cfg.gles3.minor_version = 0

VS = """#version 300 es
layout(location=0) in vec3 pos;
layout(location=1) in vec3 col;
uniform mat4 mvp;
out vec3 vcol;
void main(){ gl_Position = mvp*vec4(pos,1.0); vcol = col; }
"""

FS = """#version 300 es
precision mediump float;
in vec3 vcol;
out vec4 frag;
void main(){ frag = vec4(vcol,1.0); }
"""

V = [
 -0.5,-0.5, 0.5, 1,0,0,   0.5,-0.5, 0.5, 1,0,0,
  0.5, 0.5, 0.5, 1,0,0,  -0.5, 0.5, 0.5, 1,0,0,
  0.5,-0.5,-0.5, 0,1,0,  -0.5,-0.5,-0.5, 0,1,0,
 -0.5, 0.5,-0.5, 0,1,0,   0.5, 0.5,-0.5, 0,1,0,
 -0.5,-0.5,-0.5, 0,0,1,  -0.5,-0.5, 0.5, 0,0,1,
 -0.5, 0.5, 0.5, 0,0,1,  -0.5, 0.5,-0.5, 0,0,1,
  0.5,-0.5, 0.5, 1,1,0,   0.5,-0.5,-0.5, 1,1,0,
  0.5, 0.5,-0.5, 1,1,0,   0.5, 0.5, 0.5, 1,1,0,
 -0.5, 0.5, 0.5, 0,1,1,   0.5, 0.5, 0.5, 0,1,1,
  0.5, 0.5,-0.5, 0,1,1,  -0.5, 0.5,-0.5, 0,1,1,
 -0.5,-0.5,-0.5, 1,0,1,   0.5,-0.5,-0.5, 1,0,1,
  0.5,-0.5, 0.5, 1,0,1,  -0.5,-0.5, 0.5, 1,0,1,
]
I = [0,1,2,0,2,3, 4,5,6,4,6,7, 8,9,10,8,10,11,
     12,13,14,12,14,15, 16,17,18,16,18,19, 20,21,22,20,22,23]

def f32(d): return (ctypes.c_float*len(d))(*d)
def u32(d): return (ctypes.c_uint*len(d))(*d)

def perspective(fov, asp, n, f):
    t = 1/math.tan(math.radians(fov)/2)
    return [t/asp,0,0,0, 0,t,0,0, 0,0,(f+n)/(n-f),-1, 0,0,2*f*n/(n-f),0]

def mm(a,b):
    r=[0]*16
    for i in range(4):
        for j in range(4):
            r[i*4+j]=sum(a[k*4+j]*b[i*4+k] for k in range(4))
    return r

def roty(a):
    c,s=math.cos(a),math.sin(a)
    return [c,0,-s,0, 0,1,0,0, s,0,c,0, 0,0,0,1]

def rotx(a):
    c,s=math.cos(a),math.sin(a)
    return [1,0,0,0, 0,c,s,0, 0,-s,c,0, 0,0,0,1]

def tr(x,y,z):
    return [1,0,0,0, 0,1,0,0, 0,0,1,0, x,y,z,1]

class Aud:
    def __init__(self):
        self.ok=False; self.tr=None; self.rate=44100
        try:
            from jnius import autoclass
            AT=autoclass('android.media.AudioTrack')
            AF=autoclass('android.media.AudioFormat')
            AM=autoclass('android.media.AudioManager')
            b=AT.getMinBufferSize(self.rate, AF.CHANNEL_OUT_MONO, AF.ENCODING_PCM_16BIT)
            self.tr=AT(AM.STREAM_MUSIC, self.rate, AF.CHANNEL_OUT_MONO,
                       AF.ENCODING_PCM_16BIT, b, AT.MODE_STREAM)
            self.tr.play(); self.ok=True
            print("[audio] AudioTrack ready")
        except Exception as e:
            print("[audio] skip (desktop ok):", e)
    def beep(self, f=660, ms=150):
        if not self.ok: return
        import struct
        n=int(self.rate*ms/1000)
        buf=struct.pack(f'<{n}h',
            *(int(20000*math.sin(2*math.pi*f*i/self.rate)) for i in range(n)))
        try: self.tr.write(buf,0,len(buf))
        except: pass
    def release(self):
        if self.tr:
            try: self.tr.stop(); self.tr.release()
            except: pass

win = pyglet.window.Window(800,600,"3DSandbox",config=cfg,resizable=True)
S = {'prog':None,'vao':None,'vbo':None,'ebo':None,'mvp':None,
     'ax':0.0,'ay':0.0,'aud':None}

@win.event
def on_init():
    def cs(src, kind):
        s=gl.glCreateShader(kind); gl.glShaderSource(s,src); gl.glCompileShader(s)
        if gl.glGetShaderiv(s, gl.GL_COMPILE_STATUS)!=gl.GL_TRUE:
            raise RuntimeError(gl.glGetShaderInfoLog(s))
        return s
    vs=cs(VS, gl.GL_VERTEX_SHADER); fs=cs(FS, gl.GL_FRAGMENT_SHADER)
    p=gl.glCreateProgram()
    gl.glAttachShader(p,vs); gl.glAttachShader(p,fs); gl.glLinkProgram(p)
    gl.glDeleteShader(vs); gl.glDeleteShader(fs)
    S['prog']=p
    S['mvp']=gl.glGetUniformLocation(p,"mvp")
    vao=gl.GLuint(); gl.glGenVertexArrays(1, ctypes.byref(vao)); S['vao']=vao
    gl.glBindVertexArray(vao)
    vbo=gl.GLuint(); gl.glGenBuffers(1, ctypes.byref(vbo)); S['vbo']=vbo
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, len(V)*4, f32(V), gl.GL_STATIC_DRAW)
    ebo=gl.GLuint(); gl.glGenBuffers(1, ctypes.byref(ebo)); S['ebo']=ebo
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
    gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, len(I)*4, u32(I), gl.GL_STATIC_DRAW)
    gl.glVertexAttribPointer(0,3,gl.GL_FLOAT,gl.GL_FALSE,24,ctypes.c_void_p(0))
    gl.glEnableVertexAttribArray(0)
    gl.glVertexAttribPointer(1,3,gl.GL_FLOAT,gl.GL_FALSE,24,ctypes.c_void_p(12))
    gl.glEnableVertexAttribArray(1)
    gl.glBindVertexArray(0)
    gl.glEnable(gl.GL_DEPTH_TEST)
    S['aud']=Aud()

@win.event
def on_resize(w,h):
    gl.glViewport(0,0,w,h)

@win.event
def on_draw():
    gl.glClearColor(0.1,0.1,0.15,1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT|gl.GL_DEPTH_BUFFER_BIT)
    p=S['prog']
    if not p: return
    gl.glUseProgram(p)
    gl.glBindVertexArray(S['vao'])
    w,h=win.get_size()
    proj=perspective(60.0, w/max(h,1), 0.1, 100.0)
    view=tr(0,0,-3)
    model=mm(roty(S['ay']), rotx(S['ax']))
    mvp=mm(proj, mm(view, model))
    gl.glUniformMatrix4fv(S['mvp'],1,gl.GL_FALSE,f32(mvp))
    gl.glDrawElements(gl.GL_TRIANGLES, len(I), gl.GL_UNSIGNED_INT, ctypes.c_void_p(0))
    gl.glBindVertexArray(0)

@win.event
def on_key_press(sym, mod):
    if sym==key.SPACE and S['aud']:
        S['aud'].beep()

def upd(dt):
    S['ay']+=dt*1.2
    S['ax']+=dt*0.7

pyglet.clock.schedule_interval(upd, 1/60.0)

if __name__=="__main__":
    pyglet.app.run()
    if S['aud']: S['aud'].release()
