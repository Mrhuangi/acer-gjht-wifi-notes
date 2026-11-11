# 设备只读审计：后台进程与对外连接

目的：搞清楚这台设备**在跑什么、连了哪里**。全部命令只读，不改任何配置。

## 1. 看进程

```sh
adb shell ps
```

关注这几类：

| 类别 | 典型进程 |
|---|---|
| 必需 | `init`、`zte_mifi`（主守护）、`hostapd`、`goahead`（Web）、`dnsmasq`/`udhcpd`、`adbd` |
| 可选 | `atweb`（AT over HTTP）、`radvd`/`dhcp6s`/`zte_ndp`（IPv6） |
| 需确认 | 名字含 `fota`、`ota`、`mqtt`、`agent`、`report`、`mgmt`、`limit` 的 |

## 2. 看对外连接

```sh
adb shell netstat -tn | grep ESTABLISHED
```

正常情况下应该**只有局域网内的连接**（你的电脑/手机到设备 80 端口）。
出现陌生的公网 IP + 443/1883/8883 端口，说明有进程在主动上报。

## 3. 看开机启动项

```sh
adb shell grep -n '&$' /etc/rc
```

逐条对照：每条后台启动都应该能说出用途。

## 4. 看配置文件里的服务器地址

```sh
adb shell nv get mqtt_host
adb shell nv get os_url
adb shell nv get fota_updateMode
```

如果这些值指向公网域名，说明设备出厂带远程管理通道。

## 5. 审计时容易踩的坑

| 坑 | 说明 |
|---|---|
| **rootfs 开机是只读** | 脚本里的 `rm -rf /bin/xxx` 会静默失败，文件其实还在。要删必须先 `mount -o remount,rw /` |
| 文件名不是证据 | 名字看起来无害的程序，也可能同时在限速、改 SSID；用 `strings` 看它内部的 HTTP 参数名，才知道真实功能 |
| 进程不在 ≠ 功能不在 | 有些程序只在特定 `bootmode` 下启动 |
| 改完要验证 | `netstat` 为空 + `ps` 里没有 + 重启后再看一遍，三者都过才算生效 |

## 6. 记录建议

审计结果建议存成表格（组件 / 用途 / 是否运行 / 如何确认），
不要只留"已处理"三个字，否则下次排查又要重来。
