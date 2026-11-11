# Acer GJHT 随身 WiFi（ZX297520V3）维护笔记

针对 **Acer GJHT** 便携路由器（主控 中兴微 **ZX297520V3**，板卡基型 **MF605DW**）的维护记录与只读体检工具。

| 项目 | 值 |
|---|---|
| 品牌 / 产品 | Acer GJHT 随身 WiFi |
| 平台 | 中兴微 ZX297520V3 |
| 固件 | `MF605DW-MA257_BB_JJ_SL_MF_V01.01.02P42U28_06` |
| 硬件版本 | V1.1 |
| 无线 | 2.4G + 5G（802.11 a/n/ac/ax），支持 5G 80MHz |
| 蜂窝 | 4G LTE，支持内置 eSIM + 物理卡槽 |

> 同平台（ZX297520V3 / MF605DW 基型）的其他贴牌设备，多数结论可参考，但**先 `nv get` 确认自己的值**，不要照抄。

> 适用范围：**自己拥有的设备**。仓库只包含文字经验与自写脚本，**不包含任何厂商固件、二进制、Web 资源、日志转储或凭据字典**。

## 目录结构

```
.
├─ README.md
├─ .gitignore
├─ docs/
│   ├─ 01-wifi-80mhz.md          80MHz 三个必要条件 + 验收标准
│   ├─ 02-wpa3-assoc-fail.md     assoc resp ack=0 排查全过程
│   ├─ 03-nv-keys.md             nv 键速查
│   ├─ 04-at-commands.md         AT 命令速查与坑位
│   ├─ 05-audit.md               只读审计方法
│   └─ 06-maintenance-manual.md  完整维护手册（脱敏版）
├─ device/
│   ├─ rm_dev.sh                 开机脚本（去云控 + atweb 守护）
│   └─ rm_dev_physical_sim.sh    同一脚本的「物理 SIM 卡」变体
└─ scripts/
    ├─ health_check.ps1          只读体检（PowerShell）
    ├─ tftp_server.py            通用 TFTP 服务器
    ├─ patch_vht_cap.py          修 hostapd VHT 能力模板（等长替换）
    └─ unpack_pyinstaller.py     PyInstaller 单文件解包
```

## 各文件说明

| 路径 | 内容 |
|---|---|
| `docs/01-wifi-80mhz.md` | 5GHz 80MHz 生效的三个必要条件，以及驱动能力位的判断方法 |
| `docs/02-wpa3-assoc-fail.md` | 手机"能搜到但连不上"的排查路径（`assoc resp ack=0`） |
| `docs/03-nv-keys.md` | 常用 nv 键速查表（WiFi / SIM / 电量） |
| `docs/04-at-commands.md` | 常用 AT 命令速查与 4 个坑 |
| `docs/05-audit.md` | 设备对外连接 / 后台进程的只读审计方法 |
| `docs/06-maintenance-manual.md` | 完整维护手册：参数、80MHz 方案、云控清单、换卡流程、禁忌、故障速查 |
| `device/rm_dev.sh` | 开机脚本：清理云控 nv、强制开启 SSID 广播、atweb 守护循环 |
| `device/rm_dev_physical_sim.sh` | 同上，切到物理 SIM 卡槽的版本（含切卡 nv） |
| `scripts/health_check.ps1` | 只读体检脚本，输出中文报告 |
| `scripts/tftp_server.py` | 通用 TFTP 服务器（标准库，支持只读/上传、防路径穿越） |
| `scripts/patch_vht_cap.py` | 把固件生成模板里的 `[SHORT-GI-80]` 等长替换掉（参数化，校验文件大小不变） |
| `scripts/unpack_pyinstaller.py` | PyInstaller 单文件解包（提取 PYZ 与资源） |

> `device/*.sh` 是**示例脚本**，里面的 nv 键名与取值来自本机固件，**换设备请逐行核对**再用。
> 9090 的 AT 控制台页面是厂商 Web 资源，**不随本仓库分发**，需要的同学请从自己设备上取。


## 快速开始

```powershell
# 只读体检（-AdbPath 可选，给出才会查进程/nv/存储）
powershell -ExecutionPolicy Bypass -File .\scripts\health_check.ps1 `
    -DeviceIp 192.168.100.1 -Password <后台密码> -AdbPath .\adb.exe

# 通用 TFTP 服务器（默认 UDP 69，需要管理员权限）
python .\scripts\tftp_server.py --root .\files
```

体检脚本实测输出：

```
===== 设备体检 192.168.100.1 =====
  OK  网络可达              ping 通
  OK  80 后台               HTTP 200
  OK  9090 AT 控制台        HTTP 200
  OK  蜂窝已连接            ppp_connected
  OK  WiFi 频宽             80MHz 档位
  OK  ADB                  已连接
  OK  进程 zte_mifi / hostapd / goahead / adbd
       内存 / 存储 / 运行时长 …
  OK  对外连接              无
===== 完成：OK 11 / WARN 0 / FAIL 0 =====
```

## 免责声明

- 所有操作均在**自有设备**上完成，仅用于设备维护与学习。
- 仓库**不含**厂商二进制、固件、Web 前端资源、反编译产物或任何密码字典。
- 不提供、不讨论 IMEI 修改等内容（在多数国家和地区属违法行为）。
- 刷机、改分区有变砖风险，风险自负。
