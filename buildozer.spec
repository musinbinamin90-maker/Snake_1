[app]
title = My Kivy Game
package.name = mykivygame
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# Вот самая главная строчка, которую мы исправляли:
requirements = python3,kivy==2.3.0,libffi,opensslrm -rf .buildozer

orientation = portrait
osx.kivy_version = 2.3.0
fullscreen = 1
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.api = 31
android.minapi = 24
android.ndk_api = 24

[buildozer]
log_level = 2
warn_on_root = 1