#!/usr/bin/env python3
"""共用：adb 截图。

各 vision 模块原先各写一份 grab，这里统一；check=True 时保持
原 ants/dogs/spool 的“空数据或解码失败即抛错”行为。
"""
import subprocess

import cv2
import numpy as np

from common.adb import adb_prefix


def grab(serial=None, check=False):
    cmd = adb_prefix(serial) + ["exec-out", "screencap", "-p"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE if check else subprocess.DEVNULL)
    if check and proc.returncode != 0:
        raise RuntimeError("adb screencap 失败: %s" %
                           proc.stderr.decode("utf-8", "replace").strip())
    data = proc.stdout
    if not data:
        if check:
            raise RuntimeError("adb screencap 返回空数据，请检查设备连接")
        return None
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None and check:
        raise RuntimeError("截图解码失败")
    return img
