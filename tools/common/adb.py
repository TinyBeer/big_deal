#!/usr/bin/env python3
"""共用：adb 输入与控件树工具。

把各游戏 auto 脚本里重复的 adb tap / keyevent / uiautomator dump 收敛到这里。
业务判定（返回哪些文案、何时点返回）仍留在各脚本。
"""
import re
import subprocess
import xml.etree.ElementTree as ET

UI_XML = "/sdcard/window.xml"


def adb_prefix(serial=None):
    return ["adb"] + (["-s", serial] if serial else [])


def tap(x, y, serial=None, touch=False, check=False):
    cmd = adb_prefix(serial) + ["shell", "input"]
    if touch:
        cmd.append("touchscreen")
    cmd += ["tap", str(int(round(x))), str(int(round(y)))]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=check)


def tap_touch(x, y, serial=None, check=False):
    return tap(x, y, serial=serial, touch=True, check=check)


def key_back(serial=None, check=False):
    cmd = adb_prefix(serial) + ["shell", "input", "keyevent", "4"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=check)


def dump_ui(serial=None):
    adb = adb_prefix(serial)
    subprocess.run(adb + ["shell", "uiautomator", "dump", UI_XML],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    data = subprocess.run(adb + ["exec-out", "cat", UI_XML],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        return None


def find_text_node(root, keywords):
    if root is None:
        return None
    for node in root.iter("node"):
        text = node.get("text", "")
        if any(k in text for k in keywords):
            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
            if m:
                x1, y1, x2, y2 = [int(v) for v in m.groups()]
                if x2 > x1 and y2 > y1:
                    return ((x1 + x2) // 2, (y1 + y2) // 2), text
    return None


def find_text(serial, keywords):
    return find_text_node(dump_ui(serial), keywords)


def detect_device():
    out = subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.strip().endswith("\tdevice"):
            return line.split()[0]
    return None
