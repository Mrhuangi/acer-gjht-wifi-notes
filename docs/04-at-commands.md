# AT 命令速查（Acer GJHT / ZX297520V3 便携路由）

通过设备的 AT 串口（Windows 下通常是 `AT Interface (COMxx)`，115200 8N1）发送，
或走设备自带的 AT over HTTP 接口。

## 常用命令

| 命令 | 用途 | 正常返回示例 |
|---|---|---|
| `AT` | 握手 | `OK` |
| `AT+CPIN?` | SIM 是否就绪 | `+CPIN: READY`；`+CME ERROR: 10` = 未插卡/未识别 |
| `AT+CSQ` | 信号质量 | `+CSQ: 20,99`（第一个值 0–31，越大越好） |
| `AT+COPS?` | 当前运营商 | `+COPS: 0,0,"CHN-UNICOM",7` |
| `AT+CEREG?` | LTE 注册状态 | `+CEREG: 0,1`（第二个 1 = 已注册） |
| `AT+ZICCID?` | 读 ICCID | `+ZICCID: 89xxxxxxxxxxxxxxxxxxx` |
| `AT+ZLTEBAND?` | 当前锁频 | 位图，全默认值 = 未锁频 |

## 该固件的坑

| 命令 | 实际行为 |
|---|---|
| `AT+CFUN=1,1` | **整机重启**，不是只重启模组 |
| `AT+CBC` / `AT+CBAT?` | `+CME ERROR: 6003`（模组不提供电量） |
| `AT+EGMR=0,7` | 不支持（IMEI 只能从 nv 读） |
| `AT+ZCARDSWITCH=n` | 返回 `OK`，但切卡通常要重启才生效 |

## 锁频注意

`AT+ZLTEBAND` 锁单个频段是**最常见的断网原因**：当地没有该频段覆盖时会停在
`Limited Service`（`+COPS: 0`、`+CEREG: 0,0`）。

锁之前先确认当前驻留频段，或全选支持的频段。出问题用对应命令恢复默认位图。

## 从 HTTP 接口发 AT

部分固件提供：

```
GET http://<ip>:<port>/goform/goform_set_cmd_process?goformId=EXECUTE_AT_COMMAND&at_cmd=AT%2BCSQ
```

需要先登录主 Web 后台（会话态），否则 401。命令里的 `+` 要 URL 编码成 `%2B`。
