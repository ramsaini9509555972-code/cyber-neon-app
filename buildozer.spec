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

# (list) Inclusions (do not remove)
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude from the build
#source.exclude_dirs = tests, bin, venv

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*/*.py

# (str) Application versioning (method 1)
version = 1.0

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,numpy,scipy,pillow,pyjnius,android,speech_recognition,gtts,pygame,plyer

# (str) Supported orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (list) Permissions
android.permissions = INTERNET,RECORD_AUDIO,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
#android.sdk = 20

# (str) Android NDK version to use
#android.ndk = 23b

# (int) Android NDK API to use. This is the minimum API your C extensions will support.
#android.ndk_api = 21

# (bool) Use --private data storage (True) or --dir public storage (False)
#android.private_storage = True

# (str) Android app theme, default is ok for Kivy-based app
# android.theme = "@android:style/Theme.NoTitleBar"

# (bool) Copy library instead of making a libpymodules.so
#android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a,armeabi-v7a

# (bool) Enable AndroidX support
android.enable_androidx = True

# (bool) Enable the use of the Android API levels in buildozer.spec
android.api = 33
android.minapi = 21
android.ndk = 25b

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
#android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) XML file for custom backup scheme, see the documentation
# android.backup_schemes = @xml/backup_schemes

# (str) List of Java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jars that you do not need, since extra jars can slow
# down the build process. Allows wildcards matching with *.
#android.add_libs_armeabi_v7a = libs/armeabi-v7a/*.jar
#android.add_libs_arm64_v8a = libs/arm64-v8a/*.jar
#android.add_libs_x86 = libs/x86/*.jar
#android.add_libs_x86_64 = libs/x86_64/*.jar

# (bool) Automatically add Java classes from all jars in the libs directory
#android.add_libs_armeabi_v7a = libs/armeabi-v7a/*.jar
#android.add_libs_arm64_v8a = libs/arm64-v8a/*.jar

# (list) Pattern to whitelist for the whole project
#android.whitelist = lib-dynload/termios.so

# (str) Path to a custom whitelist file
#android.whitelist_src =

# (str) Path to a custom blacklist file
#android.blacklist_src =

# (list) List of Java files to add to the android project (can be Java or a
# directory containing the files)
#android.add_src =

# (list) List of Java files to remove from the android project
#android.remove_src =

# (list) List of Java files to add to the android app
#android.add_services =

# (list) List of Java files to remove from the android app
#android.remove_services =

# (bool) Copy library instead of making a libpymodules.so
#android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
#android.archs = arm64-v8a

# (int) overrides automatic versionCode generation in buildozer.spec
#android.version_code = 1

# (list) pattern matched against the release version
#android.release_artifact = apk

# (str) Filename of OUYA Console icon. It must be a 732x412 png image.
#android.ouya.icon.filename = %(source.dir)s/data/ouya_icon.png

# (str) XML file for custom backup scheme
#android.backup_schemes = @xml/backup_schemes

# (bool) Copy library instead of making a libpymodules.so
#android.copy_libs = 1

# (str) The presplash title in text. Android translates Android title into many
# languages (string) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Supported orientation (landscape, sensorLandscape, portrait or sensorPortrait)
#android.orientation = sensorPortrait

# (bool) Indicate if the application should be fullscreen or not
#android.fullscreen = True

# (str) Supported orientation (landscape, portrait or all)
#android.orientation = sensorPortrait

# (list) Permissions
android.permissions = INTERNET,RECORD_AUDIO,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning on buildozer run
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab)
# bin_dir = ./bin
