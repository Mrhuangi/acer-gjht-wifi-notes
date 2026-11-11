<#
.SYNOPSIS
    只读体检脚本：检查 ZX297520V3 便携路由的运行状态。

.DESCRIPTION
    仅做读取与展示，不修改设备任何配置。
    HTTP 部分使用 curl.exe（该设备返回 HTTP/1.0 且响应头不规范，
    Invoke-WebRequest 可能直接报错）。

.PARAMETER DeviceIp
    设备地址，默认 192.168.100.1

.PARAMETER Password
    Web 后台密码。给出才会查询后台 API（部分接口需要登录态）。

.PARAMETER AdbPath
    adb.exe 路径。给出才会检查进程 / nv / 存储。

.EXAMPLE
    .\health_check.ps1 -DeviceIp 192.168.100.1 -Password admin -AdbPath .\adb.exe
#>
[CmdletBinding()]
param(
    [string]$DeviceIp = "192.168.100.1",
    [string]$Password = "",
    [string]$AdbPath = ""
)

$ErrorActionPreference = "Continue"
$ok = 0; $warn = 0; $fail = 0

function HttpGet($url, $referer) {
    $args = @("--noproxy", "*", "-s", "-m", "8")
    if ($referer) { $args += @("-H", "Referer: $referer") }
    $args += $url
    return (& curl.exe @args) -join ""
}

Write-Host "===== 设备体检 $DeviceIp  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') =====" -ForegroundColor Cyan

# 1) 连通性
$ping = Test-Connection -ComputerName $DeviceIp -Count 2 -Quiet -ErrorAction SilentlyContinue
if ($ping) { Write-Host "  OK  网络可达              ping 通" -ForegroundColor Green; $ok++ }
else { Write-Host " FAIL 网络可达              不通" -ForegroundColor Red; $fail++ }

# 2) Web 入口
$code80 = (& curl.exe --noproxy "*" -s -o NUL -m 8 -w "%{http_code}" "http://$DeviceIp/index.html")
if ($code80 -eq "200") { Write-Host "  OK  80 后台               HTTP 200" -ForegroundColor Green; $ok++ }
else { Write-Host " WARN 80 后台               HTTP $code80" -ForegroundColor Yellow; $warn++ }

$code90 = (& curl.exe --noproxy "*" -s -o NUL -m 8 -w "%{http_code}" "http://${DeviceIp}:9090/at.html")
if ($code90 -eq "200") { Write-Host "  OK  9090 AT 控制台        HTTP 200" -ForegroundColor Green; $ok++ }
else { Write-Host " WARN 9090 AT 控制台        HTTP $code90（未启用可忽略）" -ForegroundColor Yellow; $warn++ }

# 3) 后台 API（需密码）
if ($Password) {
    # 该固件的 LOGIN 接口要求密码用 Base64 传输
    $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Password))
    & curl.exe --noproxy "*" -s -m 8 -X POST "http://$DeviceIp/reqproc/proc_post" -d "goformId=LOGIN&password=$b64" | Out-Null
    $stat = HttpGet "http://$DeviceIp/reqproc/proc_get?cmd=ppp_status,network_type,SSID1,wifi_11n_cap_5g&multi_data=1"
    if ($stat) {
        Write-Host "       状态                  $stat"
        if ($stat -match '"ppp_status":"ppp_connected"') { Write-Host "  OK  蜂窝已连接            ppp_connected" -ForegroundColor Green; $ok++ }
        else { Write-Host " WARN 蜂窝连接             未连接" -ForegroundColor Yellow; $warn++ }
        if ($stat -match '"wifi_11n_cap_5g":"4"') { Write-Host "  OK  WiFi 频宽             80MHz 档位" -ForegroundColor Green; $ok++ }
        else { Write-Host "  ..  WiFi 频宽             非 80MHz 档位（可能是你主动选的）" }
    }
}

# 4) ADB 相关
if ($AdbPath -and (Test-Path $AdbPath)) {
    $devs = (& $AdbPath devices 2>$null) -join "`n"
    if ($devs -match "\sdevice$" -or $devs -match "\sdevice\s") {
        Write-Host "  OK  ADB                  已连接" -ForegroundColor Green; $ok++

        $procs = (& $AdbPath shell "ps" 2>$null) -join "`n"
        foreach ($p in @("zte_mifi", "hostapd", "goahead", "adbd")) {
            if ($procs -match [regex]::Escape($p)) { Write-Host "  OK  进程 $p" -ForegroundColor Green; $ok++ }
            else { Write-Host " FAIL 进程 $p              未运行" -ForegroundColor Red; $fail++ }
        }

        $mem = (& $AdbPath shell "grep MemFree /proc/meminfo") -join ""
        Write-Host "       内存                  $mem"

        $disk = (& $AdbPath shell "df / /mnt/userdata" 2>$null) -join "`n"
        Write-Host "       存储"
        ($disk -split "`n") | ForEach-Object { if ($_.Trim()) { Write-Host ("         " + $_.Trim()) } }

        $up = (& $AdbPath shell "cat /proc/uptime") -join ""
        Write-Host "       运行时长              $up"

        $est = (& $AdbPath shell "netstat -tn | grep ESTABLISHED") -join ""
        if ([string]::IsNullOrWhiteSpace($est)) { Write-Host "  OK  对外连接              无" -ForegroundColor Green; $ok++ }
        else { Write-Host " WARN 对外连接              有活动连接，请人工确认：`n$est" -ForegroundColor Yellow; $warn++ }
    }
    else {
        Write-Host " WARN ADB                  未连接（可能未插 USB 或未开调试）" -ForegroundColor Yellow; $warn++
    }
}
else {
    Write-Host "  ..  ADB                  未提供 -AdbPath，跳过进程/nv 检查"
}

Write-Host ""
Write-Host ("===== 完成：OK {0} / WARN {1} / FAIL {2} =====" -f $ok, $warn, $fail) -ForegroundColor Cyan
if ($fail -gt 0) { exit 1 } else { exit 0 }
