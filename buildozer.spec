[app]
title = 3DSandbox
package.name = sandbox3d
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,glsl,ttf
version = 0.1.18

android.api = 31
android.minapi = 28
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.build_tools = 33.0.2
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

p4a.bootstrap = sdl2
p4a.branch = v2024.01.21
requirements = python3,kivy,numpy

fullscreen = 1
orientation = landscape
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 0

