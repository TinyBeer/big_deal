#!/usr/bin/env python3
"""本关固定顺序自动点击（可重复多轮）：
冰红茶 → 矿泉水 → 冰红茶 → 啤酒 → 矿泉水 → 啤酒 → 瓜子 → 花生 → 八宝粥 → 退出按钮。

每轮都从开局状态检测开始（按固定顺序循环处理弹窗/主界面/广告页），进入关卡后直接跑
点击序列、中途不再检测界面；点完退出按钮等 2 秒再开始下一轮。
每次点击前重新抓图识别目标位置（位置会变）；退出按钮位置固定，直接点固定坐标、不做识别。
每次点击后等 1 秒，点完八宝粥后等 2 秒；全部结束后发一条简短的手机状态栏通知。

用法见 tools/snacks/quick.sh（--rounds N 指定执行轮数，默认 1）。
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
import snacks_vision as sv  # noqa: E402
from common.adb import detect_device, dump_ui, key_back, tap  # noqa: E402
from common.notify import add_notify_args, notify_phone, send_notify  # noqa: E402
from common.screen import grab  # noqa: E402

SEQUENCE = ["冰红茶", "矿泉水", "冰红茶", "啤酒", "矿泉水", "啤酒",
            "瓜子", "花生", "八宝粥", "退出按钮"]
EXIT_FIXED = (999, 172)      # 右上角退出按钮，基准分辨率下的固定中心点
GIFT_CLOSE_WAIT = 2.0        # 点 No thanks 后给足转场时间，太短会还没切到主界面就去检测
SHOP_CLOSE_WAIT = 1.0        # 关积分商店红叉后等 1s
START_GAME_WAIT = 2.5        # 点开始游戏后等 2.5s
START_GAME_SAMPLES = 6       # 按钮有缩放动画，连抓多帧取最高分，避免采到低分帧漏检
START_GAME_SAMPLE_GAP = 0.15  # 采样间隔（秒），6 帧约覆盖 0.9s 一个动画周期
ENTRY_TAB_WAIT = 6.0         # 点入口页「真香摆摊日记」页签后等 6s
EXIT_WAIT = 2.0              # 点退出按钮后等 2s，给下一轮转场留足时间
TOOL_NAME = "零食顺序点击"


def find_target(img, name, threshold, last_clicked=None):
    """重新识别当前画面，找指定名字的商品；同名多个时优先选远离上一次点击的块。

    只参考「上一次」点击位置，不按全部历史屏蔽坐标——商品移位后新出现的块
    可能正好落在旧位置，不能因此漏点。只有一个候选时直接点，不做距离过滤。
    """
    result = sv.analyze(img, threshold=threshold, use_unknown=False)
    cands = [it for it in result["items"] if it["name"] == name]
    if not cands:
        return None
    if last_clicked is not None and len(cands) > 1:
        lx, ly = last_clicked
        cands.sort(key=lambda it: (
            (it["center"][0] - lx) ** 2 + (it["center"][1] - ly) ** 2,
            it["score"] if it["score"] is not None else 0.0), reverse=True)
    else:
        cands.sort(key=lambda it: (it["score"] if it["score"] is not None else 0.0),
                   reverse=True)
    return cands[0]


def find_entry(serial, img=None):
    """两个入口模板（入口页页签 / 任务页卡片）任一命中即返回点击位置。"""
    if img is None:
        img = grab(serial, check=True)
    h, w = img.shape[:2]
    return sv.detect_entry_tab(img, w / sv.BASE_W, h / sv.BASE_H)


def click_entry(hit, serial):
    """点击命中的入口并等 6 秒，让游戏加载到积分商店。"""
    tap(hit["center"][0], hit["center"][1], serial=serial, touch=True)
    print("检测到入口「真香摆摊日记」（模板 %s，匹配 %.4f），已点中心，等待 %.1fs" %
          (hit.get("template", "-"), hit.get("score", 0.0), ENTRY_TAB_WAIT),
          flush=True)
    time.sleep(ENTRY_TAB_WAIT)


def click_entry_if_needed(serial, img=None):
    """开局状态机里用到：有入口就点，没有就交给其它状态处理。"""
    hit = find_entry(serial, img)
    if hit is None:
        return False
    click_entry(hit, serial)
    return True


def back_from_ad_if_needed(serial, img=None):
    """看广告页面直接按返回键。

    判据按顺序：近纯白加载页 → 右上角固定退出按钮消失 → WebView 控件树。
    游戏关卡右上角始终有退出按钮；它没了就说明已经不在关卡（广告页），
    这条比白屏/WebView 更可靠，广告内容加载完后也能识别。
    """
    if img is None:
        img = grab(serial, check=True)
    h, w = img.shape[:2]
    sx, sy = w / sv.BASE_W, h / sv.BASE_H
    if sv.ad_white_ratio(img) > 0.85:
        key_back(serial)
        print("检测到看广告页面（白屏），已返回", flush=True)
        time.sleep(1.0)
        return True
    if sv.detect_exit(img, sx, sy) is None:
        key_back(serial)
        print("检测到看广告页面（无退出按钮），已返回", flush=True)
        time.sleep(1.0)
        return True
    root = dump_ui(serial)
    if root is not None and any(
            "WebView" in (n.get("class") or "") for n in root.iter("node")):
        key_back(serial)
        print("检测到看广告页面（WebView），已返回", flush=True)
        time.sleep(1.0)
        return True
    return False


def dismiss_gift_if_needed(serial, img=None):
    """助力礼包弹窗出现时点「No thanks」，等足转场时间后再交给下一轮检测。"""
    if img is None:
        img = grab(serial, check=True)
    h, w = img.shape[:2]
    hit = sv.detect_gift_no_thanks(img, w / sv.BASE_W, h / sv.BASE_H)
    if hit is None:
        return False
    tap(hit["center"][0], hit["center"][1], serial=serial, touch=True)
    print("检测到助力礼包，已点 No thanks，等待 %.1fs" % GIFT_CLOSE_WAIT, flush=True)
    time.sleep(GIFT_CLOSE_WAIT)
    return True


def close_shop_if_needed(serial, img=None):
    """积分兑换商店弹窗出现时，点右上角红叉关闭；没有则不做任何操作。"""
    if img is None:
        img = grab(serial, check=True)
    h, w = img.shape[:2]
    hit = sv.detect_shop_close(img, w / sv.BASE_W, h / sv.BASE_H)
    if hit is None:
        return False
    tap(hit["center"][0], hit["center"][1], serial=serial, touch=True)
    print("检测到积分商店，已点叉号关闭，等待 %.1fs" % SHOP_CLOSE_WAIT, flush=True)
    time.sleep(SHOP_CLOSE_WAIT)
    return True


def start_game_if_needed(serial, img=None):
    """游戏主界面出现时，多帧检测「开始游戏」，命中就点并等 2.5 秒。"""
    if img is not None:
        frames = [img]
    else:
        frames = []
        for _ in range(START_GAME_SAMPLES):
            frames.append(grab(serial, check=True))
            time.sleep(START_GAME_SAMPLE_GAP)
    h, w = frames[0].shape[:2]
    hit = sv.detect_start_game(frames, w / sv.BASE_W, h / sv.BASE_H)
    if hit is None:
        return False
    tap(hit["center"][0], hit["center"][1], serial=serial, touch=True)
    print("检测到游戏主界面，已点开始游戏，等待 %.1fs" % START_GAME_WAIT, flush=True)
    time.sleep(START_GAME_WAIT)
    return True


def handle_interrupts(serial, max_rounds=6):
    """反复处理开场状态，每轮顺序：入口页签 → 积分商店 → 开始游戏 → 助力礼包 → 广告页。

    入口页「真香摆摊日记」页签先点掉并等 6s，再走用户确认的顺序：
    关商店红叉 → 点开始游戏 → 关新弹的助力礼包 → 处理可能出现的广告页。
    一轮里发生过操作就再按同顺序走一轮；直到某一轮五项都没命中，
    才认为已进入关卡，立刻返回去点零食饮料，不再检测界面。
    """
    for _ in range(max_rounds):
        changed = click_entry_if_needed(serial)
        if close_shop_if_needed(serial):
            changed = True
        if start_game_if_needed(serial):
            changed = True
        if dismiss_gift_if_needed(serial, grab(serial, check=True)):
            changed = True
        if back_from_ad_if_needed(serial):
            changed = True
        if not changed:
            return False
    return True


def main():
    ap = argparse.ArgumentParser(description="本关固定顺序自动点击")
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--threshold", type=float, default=0.75, help="商品模板匹配阈值")
    ap.add_argument("--rounds", type=int, default=1, help="完整流程执行轮数（默认 1）")
    ap.add_argument("--retry", type=int, default=4, help="单个目标找不到时的重试次数")
    ap.add_argument("--dry-run", action="store_true", help="只打印顺序，不点击")
    add_notify_args(ap, "snacks", tool_name=TOOL_NAME,
                    default_message="顺序点击完成")
    args = ap.parse_args()

    rounds = max(1, args.rounds)
    if args.dry_run:
        print("每轮依次点击：" + " → ".join(SEQUENCE))
        print("共 %d 轮（--rounds %d）" % (rounds, rounds))
        return 0

    serial = args.device or detect_device()
    if not serial:
        print("未找到 adb 设备", file=sys.stderr)
        return 1

    # 开局必须有入口（两个模板任一命中）；没匹配到就直接退出，不继续后续流程
    entry = find_entry(serial)
    if entry is None:
        print("当前页面没有游戏入口（入口页页签 / 任务页卡片都没匹配到），退出",
              file=sys.stderr, flush=True)
        return 1
    click_entry(entry, serial)

    current = 0
    try:
        for current in range(1, rounds + 1):
            print("===== 第 %d/%d 轮 =====" % (current, rounds), flush=True)
            # 每轮都从开局状态检测开始；clicked 每轮重置，位置重新识别。
            clicked = []
            handle_interrupts(serial)
            for step, name in enumerate(SEQUENCE, 1):
                if name == "退出按钮":
                    tap(EXIT_FIXED[0], EXIT_FIXED[1], serial=serial, touch=True)
                    clicked.append(EXIT_FIXED)
                    print("%d/%d 退出按钮（固定位置），等待 %.1fs" %
                          (step, len(SEQUENCE), EXIT_WAIT), flush=True)
                    time.sleep(EXIT_WAIT)
                    continue

                pos = None
                for _ in range(max(1, args.retry)):
                    img = grab(serial, check=True)
                    hit = find_target(img, name, args.threshold,
                                      clicked[-1] if clicked else None)
                    if hit is not None:
                        pos = tuple(hit["center"])
                        break
                    time.sleep(0.5)
                if pos is None:
                    raise RuntimeError("未找到目标：%s" % name)

                tap(pos[0], pos[1], serial=serial, touch=True)
                clicked.append(pos)
                print("%d/%d %s" % (step, len(SEQUENCE), name), flush=True)
                time.sleep(2.0 if name == "八宝粥" else 1.0)
    except Exception as e:
        msg = "顺序点击失败（第 %d 轮）：%s" % (current, e)
        print(msg, file=sys.stderr, flush=True)
        if args.notify:
            notify_phone(msg, serial, script_path=args.notify_script,
                         tool_name=TOOL_NAME, tool_slug="snacks")
        return 1

    if args.notify:
        send_notify("顺序点击完成（%d 轮）" % rounds, args, TOOL_NAME,
                    tool_slug="snacks", serial=serial)
    print("完成：%d 轮 × %d 步已执行" % (rounds, len(SEQUENCE)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
