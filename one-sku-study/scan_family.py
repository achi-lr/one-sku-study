"""scan_family.py —— 扩展命名族爆破（Pro / Ultra）

覆盖的命名族：
    g1.<tier>.<period>_eft          免费试用
    g1.<tier>.<period>              裸周期
    g1.<tier>.<period>.acq          web/acq 变体
    g1.<tier>.<period>.wb           web 变体
    g1.<tier>.<period>_trial        试用
    g1.<tier>.<period>_free         免费
    g1.<tier>.<period>_intro        首期优惠
    g1.<tier>.<period>_promo        促销
    g1.<tier>.eft_<period>          倒序
    g1.<tier>.trial_<period>        倒序
    g1.<tier>.<period>_eft.acq      组合

用法：
    python scan_family.py                     # 全量
    python scan_family.py --serial 127.0.0.1:7555
    python scan_family.py --tiers 2tb.ai,20tb  # 只扫指定档位
"""
import argparse
import json
import sys
import time

import pro0

PRO_TIERS = ["2tb.ai", "play.2tb.ai", "2tb.ai.subs_variant", "5tb.ai", "ai.pro"]
ULTRA_TIERS = ["20tb", "20tb.ai", "20tb.ai.subs_variant", "20tb.v2",
               "30tb", "30tb.ai", "30tb.ai.subs_variant", "30tb.v2",
               "ai.ultra", "ai.ultra.subs_variant", "ultra", "ultra.subs_variant",
               "play.20tb", "play.30tb", "play.ai.ultra", "play.ai.pro"]

PERIODS = ["1month", "2months", "3months", "4months", "6months", "9months",
           "12months", "15months", "18months", "24months",
           "1mo", "3mo", "6mo", "12mo", "1year",
           "30days", "90days", "180days", "365days", "540days", "730days"]

FAMILIES = ["{p}_eft", "{p}", "{p}.acq", "{p}.wb",
            "{p}_trial", "{p}_free", "{p}_intro", "{p}_promo",
            "eft_{p}", "trial_{p}", "{p}_eft.acq"]


def gen(tiers):
    out, seen = [], set()
    for t in tiers:
        for p in PERIODS:
            for f in FAMILIES:
                k = f"g1.{t}." + f.format(p=p)
                if k not in seen:
                    seen.add(k)
                    out.append(k)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial", default="")
    ap.add_argument("--tiers", default="")
    ap.add_argument("--batch", type=int, default=20)
    a = ap.parse_args()

    if a.tiers:
        tiers = [t.strip() for t in a.tiers.split(",") if t.strip()]
    else:
        tiers = PRO_TIERS + ULTRA_TIERS

    pro0.ADB = pro0.find_adb()
    if a.serial:
        pro0.SERIAL = a.serial
    else:
        pro0.pick_device()
    pro0.ensure_root()
    pro0.ensure_frida_server()
    pro0.ensure_module_apk()
    pro0.ensure_vending()
    try:
        pro0.sh("forward", "tcp:27042", "tcp:27042", timeout=15)
    except Exception:
        pass

    # 计费通道自检：先查一个已知 SKU
    pid = pro0.launch_app()
    if not pid:
        sys.exit("Google One 没起来")

    import frida
    dev = frida.get_device_manager().add_remote_device("127.0.0.1:27042")
    sess = dev.attach(pid)

    def qb(skus):
        js = pro0.build_js("auto", True, False)
        js = js.replace(
            'var PRODUCTS=["g1.play.20tb","g1.play.ai.pro","g1.30tb"];',
            "var PRODUCTS=%s;" % json.dumps(skus),
        )
        out, st = [], {"done": False, "pd": 0.0, "code": None}
        def om(m, d):
            p = m.get("payload") or {}
            ev = p.get("ev")
            if ev == "offer":
                out.append(p)
            if ev == "pd":
                st["pd"] = time.time()
                st["code"] = p.get("code")
            if ev in ("list_only", "no_trial"):
                st["done"] = True
        sc = sess.create_script(js)
        sc.on("message", om)
        sc.load()
        t0 = time.time()
        for _ in range(60):
            if st["done"]:
                break
            if st["pd"] and time.time() - st["pd"] > 0.8:
                break
            if time.time() - t0 > 6:
                break
            time.sleep(0.15)
        try:
            sc.unload()
        except Exception:
            pass
        return out, st.get("code")

    # 自检
    chk, code = qb(["g1.2tb.ai.12months_eft", "g1.2tb.ai.subs_variant"])
    if code not in (None, 0, "0"):
        print(f"⚠️ 计费通道异常（pd code={code}）——账号可能需要重新验证")
    if not chk:
        print("⚠️ 自检没查到任何 offer，结果可能无效")

    cands = gen(tiers)
    print(f"候选 {len(cands)} 个，每批 {a.batch}", flush=True)

    hits = []
    for i in range(0, len(cands), a.batch):
        try:
            got, _ = qb(cands[i:i + a.batch])
            hits.extend(got)
        except Exception:
            pass
        n = i // a.batch + 1
        if n % 25 == 0:
            print(f"  ...{n}/{(len(cands)+a.batch-1)//a.batch} 批，命中 {len(hits)}", flush=True)

    print(f"\n=== 命中 {len(hits)} 条 ===")
    d = {}
    for o in hits:
        d[(o["product"], str(o.get("id")), o.get("micros"))] = o
    for (sku, oid, mc), o in sorted(d.items(), key=lambda x: (x[0][0], int(x[0][2] or 0))):
        tag = "FREE" if int(mc or 0) == 0 else f"${int(mc or 0)/1e6:g}"
        print(f"  {sku:44s} {oid:20s} {tag:>8s}  {o.get('period')}  {o.get('title','')[:24]}")
        if int(mc or 0) == 0:
            print(f"      token={o.get('token')}")

    with open("scan_family_result.json", "w", encoding="utf-8") as f:
        json.dump(hits, f, ensure_ascii=False, indent=1)
    print("\n明细已写入 scan_family_result.json")
    try:
        sess.detach()
    except Exception:
        pass


if __name__ == "__main__":
    main()
