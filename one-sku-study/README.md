# Google One AI Pro 一键下单工具

> ## ⚠️ 免责声明
>
> **本项目仅供学习与研究 Play 计费（BillingClient）机制使用。**
>
> - 不得用于任何商业用途
> - 不得用于违反 Google 服务条款的行为
> - 使用本项目产生的任何后果（账号封禁、扣费、数据丢失等）由使用者自行承担
> - 本项目不含任何账号、卡号、支付凭证，也不收集任何用户数据
> - 所有档位由 Google 服务端下发，随时可能失效，作者不保证可用性
>
> **如有侵权或内容不当，请通过 GitHub Issues 联系，我会在收到通知后立即删除仓库。**

在 Android 模拟器里通过 Play BillingClient **主动查询任意 SKU** 并拉起收银台，
拿到 Google 页面上看不到的促销档和免费试用档。

> 当前只保留 **Google AI Pro (5 TB)** 的档位。
> Ultra / AI Plus 的促销档已在 2026-11 被 Google 全面下架，相关脚本已移除。

---

## 能拿到什么

| 档位 | SKU | 价格 |
|---|---|---|
| **Pro 免费 18 个月** | `g1.2tb.ai.18months_eft` | **¥0** |
| Pro 免费 15 个月 | `g1.2tb.ai.15months_eft` | ¥0 |
| Pro 免费 12 个月 | `g1.2tb.ai.12months_eft` | ¥0 |
| Pro 免费 6 / 4 / 3 / 2 / 1 个月 | `g1.2tb.ai.<N>months_eft` | ¥0 |
| Pro 付费年付 9 折 | `g1.2tb.ai.12months_ip_90p` | $1.99/月 × 12 |
| Pro 付费首月 | `g1.2tb.ai.1month_ip_95p.acq` | $0.99 |

**最短路径拿 24 个月**：18 个月免费 → 叠加 6 个月。

---

## 快速开始

### 1. 环境

- MuMu 模拟器（Android 12，x86_64），**开启 ROOT 和 ADB**
- Python 3.9+
- Play 商店已登录 Google 账号（**必须有付款方式**，免费试用也要验证卡）

> **看图操作** → [INSTALL.md](INSTALL.md)
>
> 图一：MuMu 开启 ROOT 权限 ｜ 图二：开启 ADB 权限 ｜ 图三：下载 Google Play 和 Google One

### 2. 装环境

双击 `一键安装环境.bat`，它会自动：

- 装 Python 依赖（`frida==16.5.9`、`colorama`）
- 下载并推送 frida-server 到模拟器
- 推送计费模块 APK
- 跑一次自检

> **frida 必须是 16.x**。17.x 移除了 Java bridge，全部功能失效。

### 3. 自检

双击 `一键安装环境.bat`，看到下面全绿就可以跑：

```
✅ 设备已连接
✅ frida-server 已启动
✅ 计费模块已就位
✅ Play 商店进程在跑
✅ frida：16.5.9
✅ 环境自检通过，可以开始跑号了
```

### 4. 下单

```
项目根目录\
  一键安装环境.bat          <- 先跑这个
  免费区\                   <- 免费试用档
    1_Pro_免费18个月.bat    <- 推荐
    2_Pro_免费15个月.bat
    3_Pro_免费12个月.bat
    4_Pro_免费6个月.bat
    5_Pro_免费4个月.bat
    6_Pro_免费3个月.bat
    7_Pro_免费2个月.bat
    8_Pro_免费1个月.bat
    9_Pro_叠加6个月_第1次.bat
    10_Pro_叠加6个月_第2次.bat
    11_Pro_叠加6个月_备用.bat
  付费区\                   <- 付费优惠档
    1_Pro_年付1.99_12个月.bat   US$23.88/年
    2_Pro_3个月1.99.bat         US$5.97
    3_Pro_1个月0.99.bat         US$0.99
```

**24 个月最短路径**：先跑 `免费区\1_Pro_免费18个月.bat`，再跑 `9_` 和 `10_` 各叠 6 个月。
---|---|
| `21_Pro_免费18个月_一步到位.bat` | **推荐**，一步 18 个月免费 |
| `3_Pro_免费叠加6个月_第2步.bat` | 在已有订阅上叠加 6 个月 |

---

## 原理

Google One 的档位在 Play 里是一组商品 ID：

```
g1.<档位>.<周期>_eft               免费试用（extended free trial）
g1.<档位>.<周期>_ip_<N>p[.acq|.wb] 付费首期优惠（N = 折扣百分比）
g1.<档位>.subs_variant             订阅变体（承载多个 offer）
```

网页端只能买 Google **主动下发**给你的那一档（请求体里带 `skuDetailsToken` + 服务端签名，改不动）。
而 Android 的 BillingClient 可以**主动查询任意 SKU**，服务端会当场签发合法凭证 —— 这是唯一能拿到低价档的入口。

### 叠加

直接下单只会「换成同档、日期不变」。叠加必须用订阅升级参数：

```java
SubscriptionUpdateParams.newBuilder()
    .setOldPurchaseToken(旧 token)
    .setReplaceProrationMode(5)   // CHARGE_FULL_PRICE
```

> 这个方法名是 `setReplaceProrationMode`，不是 `setSubscriptionReplacementMode`（不存在）。
> 订阅必须处于「活跃」状态（`auto_renew=1`）才给叠加。

---

## 踩过的坑

| 现象 | 原因 | 解决 |
|---|---|---|
| 查询全空 | Play 商店进程挂了 | 重启模拟器 |
| 查询全空（Play 在跑） | 账号卡在 `MinuteMaidActivity` 验证页 | 在模拟器里完成验证 |
| 收银台一闪就没 | 付款方式被拒 | 换卡 |
| `app_not_started` | App 启动慢 | 脚本已改轮询 25 秒 |
| frida 连不上 | 端口转发丢失 | `adb forward tcp:27042 tcp:27042` |
| `Invalid signature`（网页） | 手工 ear 缺服务端签名 | 走 Android |

---

## 免责

- 所有档位由 Google 下发，随时可能变化，脚本不保证长期有效
- 免费试用**到期前必须取消**，否则按原价续费
- 同一账号的试用资格用一次就没了
- 仅用于学习和研究 Play 计费机制
