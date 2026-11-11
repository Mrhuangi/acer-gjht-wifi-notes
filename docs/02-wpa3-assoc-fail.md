# 「能搜到热点，但所有设备都连不上」的排查记录

> 设备：Acer GJHT（中兴微 ZX297520V3，固件 MF605DW 基型）

## 现象

- 手机、电脑都能在列表里看到 SSID，信号正常
- 点击连接后一直转圈，最后显示"无法连接"
- 换 2.4G / 5G、换带宽（20/40/80）、换设备（iPhone、Windows）**全部一样**

## 日志证据

hostapd 日志固定出现：

```
authentication reply: STA=xx:xx:xx:xx:xx:xx auth_alg=3 ... dbg=sae-send-commit
SAE: State Accepted -> Committed
nl80211: Frame TX status event A1=xx:xx:xx:xx:xx:xx stype=1 cookie=... ack=0
mgmt::assoc_resp cb
nl80211: sta_remove -> DEL_STATION wlan0 xx:xx:xx:xx:xx:xx
```

关键点：

1. `auth_alg=3` → 客户端走的是 **SAE（WPA3）**
2. SAE 认证阶段**成功**（commit/confirm 都走完）
3. `assoc resp ... ack=0` → AP 发出的**关联响应客户端没有确认**

## 判断

SAE 能过、单播关联响应发不出去 → 不是信号、不是带宽、不是客户端不支持，
而是**该固件的 SAE 实现有问题**（WPA3 过渡模式 `wpa_key_mgmt=SAE WPA-PSK` + `ieee80211w=1`）。

## 验证方法（不改配置的对照实验）

恢复出厂设置后再连一次：

| 项 | 故障时 | 恢复出厂后 |
|---|---|---|
| `wpa_key_mgmt` | `SAE WPA-PSK` | **`WPA-PSK`** |
| `ieee80211w` | `1` | 无 |
| 结果 | 全部设备连不上 | 立刻能连 |

同一份出厂配置里 `force_40mhz=1`、`wps_state=2`、`ht_capab=[HT40+][HT40-]` 都在，照样能连
→ 说明这些都不是原因，**唯一变量是 `wpa_key_mgmt`**。

## 结论

把加密改成**纯 WPA2-PSK**：

```
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
ieee80211w=0        # 不要 PMF
```

## 附带经验

- 排查时的一次性误判：日志里 `HT: Forty MHz Intolerant is set by STA` 曾被我当成主因，
  实际那只影响带宽协商，不影响能否关联。
- 手工 `killall hostapd` + `ifconfig wlan0 down/up` 反复重启，会让射频进入
  "能发 beacon、单播帧全部 ack=0" 的坏状态，**改配置救不回来，只能恢复出厂**。
  改 WiFi 参数请走设备自带的 Web API。
- 判断"配置有没有生效"不能只看配置文件，要看 hostapd 日志里的 `AP-ENABLED` 与 `Set freq`。
