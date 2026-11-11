#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把固件里的 VHT 能力模板改成驱动支持的写法（等长替换，不改变文件大小）。

背景：某些 ZX297520V3 固件生成的 hostapd 配置里带 `[SHORT-GI-80]`，
而射频驱动并不支持该可选位，导致 hostapd 启动即 AP-DISABLED。
把生成模板里的这一位换成驱动支持的位即可（等长，避免破坏二进制布局）。

用法：
    python patch_vht_cap.py zte_mifi_orig zte_mifi_patched

注意：
  * 只对你自己设备的固件使用；
  * 替换后请校验文件大小不变、目标串数量为 0；
  * 部署前务必保留原厂文件的备份。
"""
import sys

OLD = b"[SHORT-GI-80][MAX-A-MPDU-LEN-EXP7]"
# 与 OLD 等长（34 字节）：去掉 SHORT-GI-80，补 RXLDPC 与空格
NEW = b"[RXLDPC]     [MAX-A-MPDU-LEN-EXP7]"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]

    d = open(src, "rb").read()
    print("file size        :", len(d))
    print("SHORT-GI-80 all  :", d.count(b"[SHORT-GI-80]"))
    print("target pattern   :", d.count(OLD))
    print("old/new byte len :", len(OLD), len(NEW))
    if len(OLD) != len(NEW):
        sys.exit("ABORT: 替换串长度不一致")
    if d.count(OLD) == 0:
        sys.exit("ABORT: 未找到目标模板串，固件版本可能不同")

    d2 = d.replace(OLD, NEW)
    print("same total size  :", len(d2) == len(d))
    print("after: pattern   :", d2.count(OLD))
    print("after: SHORT-GI80:", d2.count(b"[SHORT-GI-80]"))

    open(dst, "wb").write(d2)
    print("written ->", dst)


if __name__ == "__main__":
    main()
