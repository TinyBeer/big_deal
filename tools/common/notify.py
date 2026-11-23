#!/usr/bin/env python3
"""共用：手机状态栏通知（通过 adb 让 AutoJS6 执行 notice 脚本）。

背景：各游戏辅助工具（sand/ring/spool/dogs/ants/parking/slots）都需要在
自动运行结束后发一条手机状态栏通知。原实现在每个 auto 脚本里各复制一份，
这里统一收敛，顺带修掉部分工具缺少 `mkdir -p /sdcard/Scripts` 的隐患。

用法（各工具 auto 脚本）：
    from common.notify import add_notify_args, send_notify, notify_phone

    add_notify_args(ap, "沙画收集")                 # 注册 --notify 等参数
    ...
    if args.notify and not args.dry_run:
        send_notify(message, args, "沙画收集")       # message="auto" 时直接用统计文案

如需在异常中断时发通知，可直接用 notify_phone：
    notify_phone("异常中断", args.device, tool_name="狗狗三消")

通知脚本由 AutoJS6 的 RunIntentActivity 执行，notice() 生成常驻通知，
需要 AutoJS6 的 POST_NOTIFICATIONS 权限。
"""
import json
import os
import subprocess
import tempfile

RUN_INTENT_ACTIVITY = "org.autojs.autojs6/org.autojs.autojs.external.open.RunIntentActivity"
SCRIPTS_DIR = "/sdcard/Scripts"


def default_script_path(tool_slug):
    """按工具短名生成手机端脚本路径，如 sand -> /sdcard/Scripts/sand_notify.js。"""
    return "%s/%s_notify.js" % (SCRIPTS_DIR, tool_slug)


def add_notify_args(parser, tool_slug, tool_name=None, default_message="auto"):
    """给 argparse 注册统一的通知参数。

    tool_slug : 工具短名（sand/ring/...），用于派生默认脚本路径
    tool_name : 通知标题，默认取 tool_slug
    default_message : --notify-message 的默认值，默认 "auto"（运行时自动统计）；
                      spool 等希望固定文案的工具可传入具体文案
    """
    parser.add_argument("--notify", dest="notify", action="store_true", default=True,
                        help="结束后发送手机状态栏通知（默认开启）")
    parser.add_argument("--no-notify", dest="notify", action="store_false",
                        help="不发送通知")
    parser.add_argument("--notify-message", default=default_message,
                        help="通知内容；auto 表示自动生成统计文案")
    parser.add_argument("--notify-script", default=default_script_path(tool_slug),
                        help="写到手机上供 AutoJS6 运行的临时脚本路径")


def notify_phone(message, serial=None, script_path=None, tool_name="", tool_slug=""):
    """发一条手机状态栏通知。返回是否成功。

    message    : 通知正文
    serial     : adb 设备序列号
    script_path: 手机端脚本路径，缺省按 tool_slug 派生
    tool_name  : 通知标题（中文工具名）
    tool_slug  : 工具短名，用于缺省脚本路径与临时文件前缀
    """
    if script_path is None:
        script_path = default_script_path(tool_slug or "tool")
    adb = ["adb"] + (["-s", serial] if serial else [])
    js = "notice(%s, %s);\n" % (
        json.dumps(tool_name or tool_slug or "工具", ensure_ascii=False),
        json.dumps(message, ensure_ascii=False))
    fd, tmp = tempfile.mkstemp(prefix=(tool_slug or "tool") + "_notify_", suffix=".js")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(js)
        subprocess.run(adb + ["shell", "mkdir", "-p", SCRIPTS_DIR],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(adb + ["push", tmp, script_path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(adb + ["shell", "am", "start", "-n", RUN_INTENT_ACTIVITY,
                              "-d", "file://" + script_path, "-t", "text/javascript"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("提醒: 已发送通知: %s" % message, flush=True)
        return True
    except (OSError, subprocess.CalledProcessError) as e:
        print("提醒: 发送失败: %s" % e, flush=True)
        return False
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def send_notify(auto_message, args, tool_name, tool_slug=None, serial=None):
    """按 args 决定消息内容并发送。

    若 args.notify_message 为 "auto"（缺省），用调用方传入的统计文案
    auto_message；否则用自定义文案。tool_slug 缺省从 args.notify_script
    的文件名推断，或由调用方显式传入。
    """
    if not getattr(args, "notify", False):
        return False
    custom = getattr(args, "notify_message", "auto")
    message = auto_message if custom == "auto" else custom
    slug = tool_slug or _infer_slug(getattr(args, "notify_script", ""), tool_name)
    return notify_phone(message,
                        serial if serial is not None else getattr(args, "device", None),
                        script_path=getattr(args, "notify_script", None),
                        tool_name=tool_name, tool_slug=slug)


def _infer_slug(script_path, tool_name):
    """从 /sdcard/Scripts/<slug>_notify.js 推断短名；失败则用工具名。"""
    base = os.path.basename(script_path or "")
    if base.endswith("_notify.js") and len(base) > len("_notify.js"):
        return base[:-len("_notify.js")]
    return tool_name
