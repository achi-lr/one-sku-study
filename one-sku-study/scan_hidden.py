"""scan_hidden.py —— 按 SKU 命名规则批量爆破，找隐藏的促销档

命名规律（从已发现的档归纳）：
    g1.<tier>.<period>_ip_<N>p[.acq]
      tier    : 30gb 100gb 200gb helium 2tb 5tb 10tb 20tb 30tb
                2tb.ai 5tb.ai 20tb.ai 30tb.ai ai.pro ai.ultra
                play.2tb.ai play.20tb play.ai.pro play.helium
      period  : 3months（主力）/ 6months / 12months / 1month
      N       : 50 60 70 75 80 83 85 90 95 98
      suffix  : 空 / .acq

用法：
    python scan_hidden.py                # 全量（约 380 个候选，5~10 分钟）
    python scan_hidden.py --quick        # 只扫 3months + 主力档位（约 120 个）
    python scan_hidden.py --serial 127.0.0.1:16416

输出：
    有 offer 的 SKU 全部列出（含免费/付费价格 + token）
"""
import argparse
import json
import sys
import time

import pro0

TIERS = [
    "30gb", "100gb", "200gb", "helium", "2tb", "5tb", "10tb", "20tb", "30tb",
    "2tb.ai", "5tb.ai", "20tb.ai", "30tb.ai", "ai.pro", "ai.ultra",
    "play.2tb.ai", "play.20tb", "play.ai.pro", "play.helium",
]
TIERS_QUICK = ["20tb", "30tb", "ai.ultra", "ai.pro", "2tb.ai", "play.20tb", "play.ai.pro"]
IPS = ["50", "60", "70", "75", "80", "83", "85", "90", "95", "98"]
PERIODS = ["3months"]
PERIODS_FULL = ["1month", "3months", "6months", "12months"]

BATCH = 15


def gen(quick: bool):
    tiers = TIERS_QUICK if quick else TIERS
    periods = PERIODS if quick else PERIODS_FULL
    out = []
    for t in tiers:
        for p in periods:
            for ip in IPS:
                base = f"g1.{t}.{p}_ip_{ip}p"
                out.append(base)
                out.append(base + ".acq")
    return out


def query_batch(sess, skus):
    """查一批 SKU，返回 offer 列表"""
    js = pro0.build_js("auto", True, False)
    js = js.replace(
        'var PRODUCTS=["g1.play.20tb","g1.play.ai.pro","g1.30tb"];',
        'var PRODUCTS=%s;' % json.dumps(skus),
    )
    offers = []
    done = {"flag": False}

    def on_msg(msg, data):
        p = msg.get("payload") or {}
        ev = p.get("ev")
        if ev == "offer":
            offers.append(p)
        if ev in ("list_only", "no_trial"):
            done["flag"] = True

    script = sess.create_script(js)
    script.on("message", on_msg)
    script.load()
    for _ in range(40):
        if done["flag"]:
            break
        time.sleep(0.5)
    try:
        script.unload()
    except Exception:
        pass
    return offers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--serial", default="")
    a = ap.parse_args()

    pro0.ADB = pro0.find_adb()
    pro0.pick_device()
    if a.serial:
        pro0.SERIAL = a.serial
    pro0.ensure_root()
    pro0.ensure_frida_server()
    pro0.ensure_module_apk()
    pro0.ensure_vending()
    pid = pro0.launch_app()
    if not pid:
        sys.exit("Google One 没起来")
    print(f"Google One pid={pid}", flush=True)

    # 确保端口转发（frida-server 在设备侧监听 27042）
    try:
        pro0.sh("forward", "tcp:27042", "tcp:27042", timeout=15)
    except Exception:
        pass

    import frida
    dev = frida.get_device_manager().add_remote_device("127.0.0.1:27042")
    sess = dev.attach(pid)

    cands = gen(a.quick)
    print(f"候选 SKU: {len(cands)} 个，每批 {BATCH}", flush=True)

    hits = []
    for i in range(0, len(cands), BATCH):
        batch = cands[i:i + BATCH]
        try:
            got = query_batch(sess, batch)
        except Exception as e:
            print(f"  批次 {i//BATCH+1} 出错: {e}", flush=True)
            continue
        for o in got:
            hits.append(o)
        if got:
            print(f"  [{i//BATCH+1}] 命中 {len(got)} 条", flush=True)
        time.sleep(0.3)

    try:
        sess.detach()
    except Exception:
        pass

    print("\n" + "=" * 78)
    print("有 offer 的 SKU：")
    print("=" * 78)
    by_sku = {}
    for o in hits:
        by_sku.setdefault(o["product"], []).append(o)
    for sku in sorted(by_sku):
        rows = by_sku[sku]
        free = [r for r in rows if str(r.get("micros")) == "0"]
        paid = [r for r in rows if str(r.get("micros")) != "0"]
        title = rows[0].get("title") or ""
        print(f"\n{sku}   [{title}]")
        for r in free:
            print(f"    FREE  offer={r.get('id'):26s} {r.get('period')}")
            print(f"          token={r.get('token')}")
        for r in sorted(paid, key=lambda x: int(x.get("micros") or 0)):
            price = int(r["micros"]) / 1_000_000
            print(f"    ${price:>8.2f}  offer={str(r.get('id')):22s} {r.get('period')}")
            print(f"          token={r.get('token')}")

    out = "scan_hidden_result.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(hits, f, ensure_ascii=False, indent=1)
    print(f"\n明细已写入 {out}")


if __name__ == "__main__":
    main()
