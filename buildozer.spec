[app]

# (str) Title of your application
title = Cyber Voice AI Pro

# (str) Package name
package.name = cybervoiceai

# (str) Package domain (needed for android/ios packaging)
package.domain = org.cybervoiceai

# (source.dir) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
requirements = python3,kivy,numpy,scipy,pillow,pyjnius,android,speech_recognition,gtts,pygame,plyer

# (str) Supported orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,RECORD_AUDIO,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a,armeabi-v7a

# (bool) Enable AndroidX support
android.enable_androidx = True

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (int) overrides automatic versionCode generation in buildozer.spec
android.version_code = 1

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning on buildozer run
warn_on_root = 1
