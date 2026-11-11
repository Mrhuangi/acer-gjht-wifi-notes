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
nv set old_limitspeed=1024000
nv set dhcpDNS=114.114.114.114
nv set band_select_enable=1
nv set dns_manual_func_enable=1
nv set tr069_func_enable=1
nv set ussd_enable=1
nv set terminal_mgmt_enable=0
nv set nofast_port=
nv set TM_SERVER_NAME=127.0.0.1
nv set alk_sim_select=1
nv set alk_sim_current=1
rm -rf /sbin/yiming_1028.sh
rm -rf /sbin/ip_ratelimit.sh
rm -rf /sbin/tc_tbf.sh
nv save

# atweb (AT 9090 console) self-healing loop
( sleep 25; while :; do /sbin/atweb 9090; sleep 10; done ) &

# 5GHz 80MHz self-heal: only acts when nv wifi_11n_cap_5g=4.
# Driver hw vht capab 0x3987112 lacks VHT_CAP_SHORT_GI_80, so hostapd refuses
# to start if the config carries [SHORT-GI-80]. Firmware rewrites the conf at
# runtime, so keep stripping it and re-launch hostapd whenever it is not running.
(
  sleep 35
  CONF=/etc_rw/wifi/hostapd.conf
  while :; do
    if [ "$(nv get wifi_11n_cap_5g)" = "4" ]; then
      if [ -f $CONF ] && grep -q 'SHORT-GI-80' $CONF 2>/dev/null; then
        sed -i 's/\[SHORT-GI-80\]//g' $CONF
      fi
      if ! ps | grep -q '[b]in/hostapd'; then
        killall hostapd 2>/dev/null
        sleep 3
        ifconfig wlan0 down 2>/dev/null
        sleep 1
        ifconfig wlan0 up 2>/dev/null
        sleep 2
        /bin/hostapd -d $CONF -c 2 >> /mnt/userdata/hostapd.log 2>&1 &
        sleep 12
      fi
    fi
    sleep 20
  done
) &

