"""scan_wide.py —— 扩大维度的 SKU 爆破（只关注 Pro / Ultra 5x / Ultra 20x）

维度：
  tier     Pro   : 2tb.ai  5tb.ai  ai.pro  play.2tb.ai  2tb.ai.subs_variant
           Ultra : 20tb  20tb.v2  30tb  30tb.v2  ai.ultra  ultra
                   play.20tb  play.30tb  play.ai.ultra  play.ai.pro
  period   : 1month 2months 3months 6months 9months 12months 18months 24months
  ip       : 40 50 55 60 65 70 75 80 83 85 88 90 92 95 97 98 99
  suffix   : ""  .acq  .wb  .sep

用法：
    python scan_wide.py                 # 全量（约 4500 个候选）
    python scan_wide.py --ultra-only    # 只扫 Ultra（约 2800 个）
    python scan_wide.py --pro-only      # 只扫 Pro（约 1700 个）
"""
import argparse
import json
import sys
import time

import pro0

PRO_TIERS = ["2tb.ai", "5tb.ai", "ai.pro", "play.2tb.ai", "2tb.ai.subs_variant"]
ULTRA_TIERS = [
    "20tb", "20tb.v2", "30tb", "30tb.v2", "ai.ultra", "ultra",
    "play.20tb", "play.30tb", "play.ai.ultra", "play.ai.pro",
]
PERIODS = ["1month", "2months", "3months", "6months", "9months", "12months", "18months", "24months"]
IPS = ["40", "50", "60", "70", "75", "80", "85", "90", "95", "98", "99"]
SUFFIXES = ["", ".acq", ".sep", ".wb"]

BATCH = 20


def gen(tiers):
    out = []
    for t in tiers:
        for p in PERIODS:
            for ip in IPS:
                for suf in SUFFIXES:
                    out.append(f"g1.{t}.{p}_ip_{ip}p{suf}")
    return out


def query_batch(sess, skus):
    js = pro0.build_js("auto", True, False)
    js = js.replace(
        'var PRODUCTS=["g1.play.20tb","g1.play.ai.pro","g1.30tb"];',
        'var PRODUCTS=%s;' % json.dumps(skus),
    )
    offers = []
    state = {"done": False, "pd": 0.0}

    def on_msg(msg, data):
        p = msg.get("payload") or {}
        ev = p.get("ev")
        if ev == "offer":
            offers.append(p)
        if ev == "pd":
            state["pd"] = time.time()
        if ev in ("list_only", "no_trial"):
            state["done"] = True

    sc = sess.create_script(js)
    sc.on("message", on_msg)
    sc.load()
    t_start = time.time()
    for _ in range(60):
        if state["done"]:
            break
        # 收到 pd 后最多再等 0.8 秒收集 offer
        if state["pd"] and time.time() - state["pd"] > 0.8:
            break
        if time.time() - t_start > 6:
            break
        time.sleep(0.15)
    try:
        sc.unload()
    except Exception:
        pass
    return offers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ultra-only", action="store_true")
    ap.add_argument("--pro-only", action="store_true")
    ap.add_argument("--serial", default="")
    a = ap.parse_args()

    if a.ultra_only:
        tiers = ULTRA_TIERS
    elif a.pro_only:
        tiers = PRO_TIERS
    else:
        tiers = PRO_TIERS + ULTRA_TIERS

    pro0.ADB = pro0.find_adb()
    pro0.pick_device()
    if a.serial:
        pro0.SERIAL = a.serial
    pro0.ensure_root()
    pro0.ensure_frida_server()
    pro0.ensure_module_apk()
    pro0.ensure_vending()
    try:
        pro0.sh("forward", "tcp:27042", "tcp:27042", timeout=15)
    except Exception:
        pass
    pid = pro0.launch_app()
    if not pid:
        sys.exit("Google One 没起来")
    print(f"Google One pid={pid}", flush=True)

    import frida
    dev = frida.get_device_manager().add_remote_device("127.0.0.1:27042")
    sess = dev.attach(pid)

    cands = gen(tiers)
    total = len(cands)
    print(f"候选 SKU: {total} 个，每批 {BATCH}", flush=True)

    hits = []
    t0 = time.time()
    for i in range(0, total, BATCH):
        batch = cands[i:i + BATCH]
        try:
            got = query_batch(sess, batch)
            hits.extend(got)
        except Exception as e:
            print(f"  批次 {i//BATCH+1} 出错: {e}", flush=True)
        n = i // BATCH + 1
        if n % 10 == 0:
            el = time.time() - t0
            print(f"  ...{n} 批 / {(total+BATCH-1)//BATCH} 批，已用 {el:.0f}s，命中 {len(hits)} 条", flush=True)

    try:
        sess.detach()
    except Exception:
        pass

    print("\n" + "=" * 80)
    print("命中明细：")
    print("=" * 80)
    by = {}
    for o in hits:
        by.setdefault(o["product"], []).append(o)
    for sku in sorted(by):
        rs = by[sku]
        print(f"\n{sku}   [{(rs[0].get('title') or '')[:34]}]")
        for r in sorted(rs, key=lambda x: int(x.get("micros") or 0)):
            price = int(r["micros"]) / 1_000_000
            tag = "FREE" if price == 0 else f"${price:g}"
            print(f"    {tag:>7s}  offer={str(r.get('id')):24s} {r.get('period')}")
            print(f"             token={r.get('token')}")

    with open("scan_wide_result.json", "w", encoding="utf-8") as f:
        json.dump(hits, f, ensure_ascii=False, indent=1)
    print(f"\n明细已写入 scan_wide_result.json（{len(hits)} 条）")


if __name__ == "__main__":
    main()
