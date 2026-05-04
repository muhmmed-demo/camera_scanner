[app]

# عنوان وهوية التطبيق
title = Camera Scanner
package.name = camerascanner
package.domain = com.security.camerascanner
source.dir = .
source.include_exts = py,kv,png,jpg,atlas

# الإصدار
version = 1.0

# المكتبات المطلوبة
requirements = python3,kivy==2.3.0,kivymd==1.2.0,wsdiscovery,ifaddr

# أيقونة التطبيق (اختيارية، سنضع أيقونة افتراضية)
# icon.filename = %(source.dir)s/icon.png

# الواجهة
orientation = portrait
fullscreen = 0

# --- إعدادات أندرويد ---
android.permissions = INTERNET, ACCESS_WIFI_STATE, ACCESS_NETWORK_STATE, CHANGE_WIFI_MULTICAST_STATE
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a, armeabi-v7a

# السماح ببناء Debug APK
android.debug = True
android.logcat_filters = *:S python:D

# إعدادات Gradle
android.gradle_dependencies = 
android.add_jars = 

# --- إعدادات iOS (غير مستخدمة حالياً) ---
[buildozer]
log_level = 2
warn_on_root = 1
