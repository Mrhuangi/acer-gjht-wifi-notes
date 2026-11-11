# acer GJHT 随身WiFi — 维护手册

> 记录时间：2026-11-10 21:00
> 设备：Acer GJHT（中兴微 ZX297520V3，MF605DW 基型）/ Web 后台 `http://192.168.100.1`
> AT 控制台：`http://<设备IP>:9090/at.html`（需先登录 80 后台；该页面不随本仓库分发）
> USB ADB：serial 因机而异；AT 串口 `AT Interface (COMxx)` @115200

---

## 一、当前设备参数

| 项目 | 值 |
|---|---|
| WiFi SSID | `MyWiFi_5G` |
| WiFi 密码 | `**********` |
| 频段 / 带宽 | 5GHz / **80MHz**（自动信道，实测落在 149） |
| 加密 | WPA2-PSK（**绝不能改回 WPA3/SAE**） |
| IMEI | `86xxxxxxxxxxxxx` |
| 内置卡 ICCID | `89xxxxxxxxxxxxxxxxxxx`（联通，`alk_sim_select=2`） |
| 物理卡槽 | 空（用户 SIM 卡未到货） |

---

## 二、80MHz 方案（三处改动，缺一不可）

### 1. 改掉固件里的非法能力位（根因）

`/sbin/zte_mifi` 内含配置模板字符串 `[SHORT-GI-80][MAX-A-MPDU-LEN-EXP7]`。
驱动 `hw vht capab 0x3987112` **不支持 bit5 = SHORT-GI-80**，hostapd 收到该位会直接 `AP-DISABLED`。

- 偏移：**875048**（十进制），全文件唯一一处
- 等长替换：`[SHORT-GI-80][MAX-A-MPDU-LEN-EXP7]`（34B）→ `[RXLDPC]     [MAX-A-MPDU-LEN-EXP7]`（34B）
- 产物：`zte_mifi_patched`（工作区）、`patch_zte_mifi.py`、`make_patch_bin.py`

### 2. 部署位置（rootfs 装不下）

rootfs 仅 6MB、已用 99%（剩 92KB），1.19MB 二进制写不进 `/sbin`。
做法：放 `/mnt/userdata/zte_mifi.new`（chmod 755），改 `/etc/rc` 第 123 行附近为：

```sh
if [ -x /mnt/userdata/zte_mifi.new ]; then
/mnt/userdata/zte_mifi.new $bootreason $bootmode &
else
zte_mifi $bootreason $bootmode &
fi
```

**这段 fallback 是不变砖的关键**：`/mnt/userdata` 被清（恢复出厂）时自动回退原厂程序 → WiFi 正常、只是回 40MHz。

### 3. nv 参数

```sh
nv set wifi_11n_cap_5g=4     # 5G 20/40/80
nv set wifi_11n_cap=4        # 2.4G 字段也要 4，否则不生成 VHT
nv save
```

**关键陷阱**：固件**只在 `selectedChannel=0`（自动信道）时才生成 80MHz 配置**。
传固定信道（如 36）只生成 40MHz（`vht_oper_chwidth=0`、无 `vht_capab`）。

正确调用：

```
SET_WIFI_INFO?goformId=SET_WIFI_INFO&wifiEnabled=1&wifiMode=6&countryCode=CN
&MAX_Access_num=10&m_MAX_Access_num=0&wifi_band=a&selectedChannel=0
&wifi_11n_cap=4&wifi_11n_cap_5g=4
```

另外 `SET_WIFI_INFO` 的 `wifi_11n_cap_5g` 参数**写不进 nv**，必须额外 `nv set`。

---

## 三、云控移除清单（全部可逆：改名不删除）

| 组件 | 原路径 | 它能做什么 | 当前状态 | 恢复命令 |
|---|---|---|---|---|
| `iccid_check` | `/bin/iccid_check` | 上报 SIM ICCID、**接收远程限速**、**远程改 SSID/密码** | → `.OFF`，进程已停 | `mv /bin/iccid_check.OFF /bin/iccid_check` |
| `feiliu_fota` | `/bin/feiliu_fota` | 固件远程升级 | → `.OFF`，进程已停 | `mv /bin/feiliu_fota.OFF /bin/feiliu_fota` |
| `fota_upi` | `/bin/fota_upi` | 升级包处理 | → `.OFF` | `mv /bin/fota_upi.OFF /bin/fota_upi` |
| `terminal_mgmt` | `/bin/terminal_mgmt` | 哑终端管理（远程断网） | 文件已删 | 不可恢复（需重刷） |
| `aliyun_thing` / `aliyun_mqtt` | `/sbin/` | 阿里云 IoT 上报 | 文件已删 | 不可恢复 |
| `yiming_1028.sh` / `ip_ratelimit.sh` | `/sbin/` | 限速脚本 | 文件已删 | 不可恢复 |
| `telnetd` | `/usr/sbin/telnetd` | 后门（远程登录） | 程序本不存在 + `telnetd_enable=n` | — |

### nv 层云控开关（当前值）

```sh
mqtt_host            = 127.0.0.1
fota_updateMode      = 0
os_url               = http://127.0.0.1
lpa_trigger_host     = 127.0.0.1
safecare_hostname    = http://127.0.0.1
safecare_mobsite     = http://127.0.0.1
terminal_mgmt_enable = 0
TM_SERVER_NAME       = 127.0.0.1
tc_enable            = 0          # 流量整形关闭
tr069_func_enable    = 0          # 运营商远程管理关闭
telnetd_enable       = n
```

### 未启动但存在的组件（无需处理）

- `zte_amt -p 10027`：只在 `bootmode=amt` 时启动，当前 bootmode 为空
- `zte_log_agent`：rc 里无条件启动，但当前未运行
- `tc_tbf.sh`：`tc_enable=0` 时脚本第一行就 exit

### 验证方法

```sh
adb shell "netstat -tn | grep ESTABLISHED"     # 应为空
adb shell "ps"                                  # 不应有 feiliu/iccid/log_agent/telnet
```

---

## 四、IMEI

> 本手册不包含 IMEI 修改内容：在多数国家和地区篡改 IMEI 属违法行为，且写错会导致模块不注册网络。

## 五、换物理卡的完整流程

1. 插入 SIM 卡（确认已识别：`AT+CPIN?` → `READY`）
2. 后台「SIM 卡选择」选 **SIM**（值 1），或 `nv set alk_sim_select=1; nv set alk_sim_current=1; nv save`
3. 重启设备（用 Web `REBOOT_DEVICE`，**不要用 `AT+CFUN=1,1`** —— 这台固件会整机重启）
4. 验证：`AT+ZICCID?` 为新卡、`ppp_connected`、`network_provider` 正确
5. 如需改串，按第四节操作

**历史坑**：固化脚本里曾有两行 `nv set alk_sim_select=1; nv set alk_sim_current=1`，在**没插卡**时会导致每次开机切到空卡槽 → 断网。当前 `rm_dev.sh` 已无这两行。

---

## 六、绝对不要做的事

| 禁止 | 原因 |
|---|---|
| `AT+CFUN=1,1` | 这台固件会执行成**整机重启** |
| 只锁 B1 频段 | 当地无 B1 覆盖会 `Limited Service` 断网 |
| 把 WiFi 改成 WPA3(SAE) 或加 `ieee80211w` | 本机 SAE 实现有 bug：认证能过但关联响应发不出去，**所有设备都连不上**，只能恢复出厂 |
| 手工 `killall hostapd` + `ifconfig wlan0 down/up` + 手工启动 | 会让射频进入"能发 beacon、单播帧全 `ack=0`"的坏状态，改配置救不回来，只能恢复出厂 |
| 在后台「WiFi 高级设置」点"应用"且频带宽度不是 20/40/80MHz | 会把带宽写回 20/40 |
| 恢复出厂 / 格式化 `/mnt/userdata` | 会清掉 `/mnt/userdata/zte_mifi.new` → 回退 40MHz（不变砖） |
| 往 `/` 或 `/sbin` 写大于 400KB 的文件 | rootfs 只剩 92KB，会静默失败并留下半截文件 |

---

## 七、关键文件位置

### 设备上

```
/mnt/userdata/zte_mifi.new     改过的守护进程（80MHz 核心）
/mnt/userdata/zte_mifi.bak     原厂程序备份
/mnt/userdata/rc.bak           rc 备份
/bin/adbd                      ADB 固化
/sbin/atweb                    AT 9090 后台
/sbin/rm_dev.sh                开机脚本（去云控 + atweb 守护，944B）
/etc/rc                        启动脚本（带 fallback）
```

### 电脑备份（本目录）

```
zte_mifi_orig / zte_mifi_patched      原厂 / 改过的守护进程
patch_zte_mifi.py / make_patch_bin.py 打补丁脚本
rc_current / rc_patched               改前 / 改后的 rc
rm_dev_clean.sh                       最终版开机脚本
hostapd_working_baseline.conf         能用状态的配置基线
nv_cfg_20261110.txt                   完整 nv 快照
rc_after_cloudwork.txt                云控处理后的 rc
rm_dev_final.sh                       设备上的最终 rm_dev.sh
etc_ro_web_original/                  原厂 Web 后台备份
```

---

## 八、故障速查

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 搜不到 SSID | hostapd 没起来 | 查 `ps | grep hostapd`；用 Web API 重设 WiFi（不要手工启动） |
| 能连但速度只有 200/400Mbps | 退回 40MHz | 查 `nv get wifi_11n_cap_5g`（应为 4）；查 `/etc_rw/wifi/hostapd.conf` 的 `vht_oper_chwidth`（应为 1） |
| 所有设备都连不上 | 可能是 WPA3/SAE 或射频坏状态 | 查 `hostapd.conf` 的 `wpa_key_mgmt` 必须是 `WPA-PSK`；否则恢复出厂 |
| 没网但 WiFi 正常 | SIM 未被识别 / 锁频 | `AT+CPIN?`、`AT+ZOLTE?`、`nv get alk_sim_select` |
| 9090 打不开 | atweb 没跑 | AT 通道 `at+shell=/sbin/atweb 9090 &`（不要用 adb shell，会随 shell 退出被杀） |
| ADB offline | adbd 没跑 | AT 通道 `at+shell=/bin/adbd &` |
