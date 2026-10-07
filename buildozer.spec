[app]
title = 3DSandbox
package.name = sandbox3d
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,glsl,ttf,wav,ogg
version = 0.1.0

android.api = 31
android.minapi = 28
android.ndk = 25b
android.archs = arm64-v8a

p4a.bootstrap = sdl2
requirements = python3,pyglet,sdl2,pyjnius

fullscreen = 1
orientation = landscape
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
