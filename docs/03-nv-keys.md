# nv 键速查（Acer GJHT / ZX297520V3）

> 示例值均为占位符。读取：`nv get <key>`；写入：`nv set <key>=<value>` + `nv save`。
> **不要照抄别人的值**，先 `nv get` 看自己设备的当前值。

## WiFi

| 键 | 含义 | 示例 |
|---|---|---|
| `SSID1` / `SSID1_5g` | 2.4G / 5G 的 SSID | `MyWiFi_5G` |
| `HideSSID` / `HideSSID_5g` | 是否隐藏 SSID（1=隐藏） | `0` |
| `WPAPSK1_encode` / `_5g` | 密码的 Base64 明文 | `KioqKioqKio=`（`********`） |
| `m_WPAPSK1_encode` / `_5g` | 多 SSID 用的密码副本 | 同上 |
| `WPAPSK1_aes` / `_aes_5g` | 内部 PSK 哈希（带盐，**不要手改**） | — |
| `MAX_Access_num` | 最大接入数 | `5` |
| `wifi_band` | `a`=5GHz，`b`=2.4GHz | `a` |
| `wifi_11n_cap` / `_5g` | 频宽等级（0=20, 1=20/40, 4=20/40/80） | `4` |
| `wifi_cur_state` | WiFi 总开关 | `1` |

**密码一致性**：`hostapd.conf` 里的 `wpa_pass_encode` 与 `WPAPSK1_encode` 必须一致，
否则下次固件重建配置时会突然换密码。

## SIM

| 键 | 含义 |
|---|---|
| `alk_sim_select` | 卡槽选择：`1`=物理卡，`2/3/4`=内置 eSIM |
| `alk_iccid1/2/3` | 各通道的 ICCID |

切换卡槽**必须重启**才生效，热切换（`AT+ZCARDSWITCH`）返回 OK 但通常不生效。

## 电量

| 键 | 含义 |
|---|---|
| `mmi_battery_voltage_line` | 电压→电量的断点表，21 个值，`+` 分隔 |
| `mmi_temp_voltage_line` | 温度的电压映射 |

⚠️ 这条曲线**不要手工改**：实测改写后 `battery_pers` / `battery_vol_percent` 会变为空值，
写入原值也无法恢复。电量以设备 LED 为准。

## 维护提示

- `nv save` 是必须的，否则重启丢失。
- 整份配置在 `/etc_rw/nv/main/cfg`（`\0` 分隔），可 `adb pull` 出来做对比，但**不要直接写回**。
- 某些键会被开机脚本覆盖（例如脚本里有 `nv set xxx=1`），改之前先 `grep` 一遍开机脚本。
