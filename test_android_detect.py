import subprocess
import os

def check():
    is_android = "ANDROID_ROOT" in os.environ or "ANDROID_DATA" in os.environ or os.path.exists("/system/build.prop")
    print(is_android)
check()
