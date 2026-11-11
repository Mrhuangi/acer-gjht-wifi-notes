#!/bin/sh

rm /dev/loop*
rm /dev/ram*
rm /dev/cpu*
rm /dev/kmsg
rm /dev/full
rm /dev/mem
rm /dev/network*
rm /dev/rfkill
rm /dev/ttyp*
rm /dev/ptyp*
rm /dev/tty
nv set mqtt_host=127.0.0.1
nv set fota_updateMode=0
nv set os_url=http://127.0.0.1
nv set lpa_trigger_host=127.0.0.1
nv set safecare_hostname=http://127.0.0.1
nv set safecare_mobsite=http://127.0.0.1
rm -rf /bin/iccid_check
rm -rf /bin/terminal_mgmt
rm -rf /sbin/aliyun_thing
rm -rf /sbin/aliyun_mqtt
nv set tc_enable=0
nv set HideSSID=0
nv set HideSSID_5g=0
nv set old_limitspeed=1024000
nv set dhcpDNS=114.114.114.114
nv set band_select_enable=1
nv set dns_manual_func_enable=1
nv set tr069_func_enable=0
nv set ussd_enable=1
nv set terminal_mgmt_enable=0
nv set nofast_port=
nv set TM_SERVER_NAME=127.0.0.1
rm -rf /sbin/yiming_1028.sh
rm -rf /sbin/ip_ratelimit.sh
rm -rf /sbin/tc_tbf.sh
nv save

# atweb (AT 9090) watchdog: only start when not already running
( sleep 25
  while :; do
    if ! ps | grep -q "[a]tweb 9090"; then
      /sbin/atweb 9090
    fi
    sleep 10
  done
) &
