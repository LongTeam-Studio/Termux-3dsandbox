# 3DSandbox

Android 3D 沙盒实验项目 — 使用 Kivy + OpenGL ES 通过 Buildozer 打包成 APK。

## 特性

- Kivy 原生 GLES 上下文，直接调用 OpenGL ES 2.0 API
- 手写 MVP 矩阵与着色器（不依赖 Kivy 高层 Mesh/Rotate）
- GitHub Actions 自动构建 + Release

## 下载

从 [Releases](https://github.com/LongTeam-Studio/Termux-3dsandbox/releases) 页面下载最新的 `sandbox3d-*.apk`，直接安装。

## 本地构建

需要 Linux 环境（Termux 无法完整构建 Android SDK）：

    pip install buildozer cython
    buildozer android debug

## 项目结构

    .
    ├── main.py               # 主程序（Kivy + GLES）
    ├── buildozer.spec        # p4a 打包配置
    └── .github/workflows/
        └── build-apk.yml     # CI 自动构建

## 依赖

- Python 3
- Kivy 2.x
- OpenGL ES 2.0+

## License

MIT
