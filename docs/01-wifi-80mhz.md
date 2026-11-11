# 5GHz 80MHz 生效的三个必要条件

> 设备：Acer GJHT（中兴微 ZX297520V3）+ hostapd。以下为实测结论，不涉及修改任何二进制。

## 条件一：nv 频宽字段

```
wifi_11n_cap_5g = 4       # 5GHz: 20/40/80MHz 自适应（0=20, 1=20/40, 4=20/40/80）
wifi_11n_cap    = 4       # 实测这个 2.4G 字段也会影响是否生成 VHT 配置
wifi_band       = a       # 5GHz
```

写入后必须 `nv save`。

## 条件二：信道必须是「自动」

这是最容易踩的坑：

| selectedChannel | 固件生成的配置 | 实际带宽 |
|---|---|---|
| `0`（自动） | `vht_oper_chwidth=1` + `vht_capab=...` | **80MHz** |
| `36` / `149`（固定） | 只有 40MHz 配置 | 40MHz |

所以「为了稳定而固定信道」会直接丢掉 80MHz。二者不可兼得。

## 条件三：不能把驱动不支持的能力位写进配置

固件可能生成带 `[SHORT-GI-80]` 的 `vht_capab`。启动 hostapd 时若日志出现：

```
Driver does not support configured VHT capability [VHT_CAP_SHORT_GI_80]
wlan0: AP-DISABLED
CTRL-EVENT-TERMINATING
```

说明**驱动不支持这个可选加速位**（≠ 不支持 80MHz）。处理思路：让生成出来的配置里不含该位。

因为固件每次开机都会重新生成 `hostapd.conf`，一次性手工修改会在下次重启后失效。可靠做法是**在开机脚本里做后处理**：检测 `vht_capab` 是否含该位 → 去掉 → 再拉起 AP。规则建议只在 `wifi_11n_cap_5g=4` 时生效，避免干预用户主动选择的 20/40MHz。

## 验收标准

```
# hostapd 日志
nl80211: Set freq 5180 (ht_enabled=1, vht_enabled=1, he_enabled=1,
                        bandwidth=80 MHz, cf1=5210 MHz, cf2=0 MHz)
wlan0: AP-ENABLED

# 客户端
2×2 设备链接速率 > 400 Mbps（40MHz 2×2 理论上限就是 400）
实测 600/600 Mbps 即 80MHz 成立
```

## 注意

- 测 80MHz 前请先确保加密方式是**纯 WPA2-PSK**，否则会被关联失败掩盖（见 `02-wpa3-assoc-fail.md`）。
- 自动信道可能落到 DFS 频段（52–64）。检测到雷达时 AP 会短暂让出信道，属正常行为。
- 2.4G 不要设 VHT，只保留 20/40。
