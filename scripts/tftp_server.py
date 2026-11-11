#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""极简 TFTP 服务器（仅标准库，无第三方依赖）。

用途：给没有 tftp 客户端/服务端的设备传文件（很多嵌入式设备只带 busybox tftp）。

用法：
    python tftp_server.py --root ./files              # 只读：从目录取文件
    python tftp_server.py --root ./files --allow-write # 允许设备上传到 <root>/upload

注意：
  * UDP 69 端口在 Linux/macOS 需要 root；Windows 需管理员权限。
  * 只会访问 --root 目录内的文件，拒绝路径穿越。
"""
import argparse
import os
import socket
import struct
import sys
import time

OP_RRQ = 1
OP_WRQ = 2
OP_DATA = 3
OP_ACK = 4
OP_ERROR = 5

BLOCK = 512


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def safe_join(root, name):
    """把请求的文件名限制在 root 内，防路径穿越。"""
    name = name.replace("\\", "/").lstrip("/")
    p = os.path.normpath(os.path.join(root, name))
    if not os.path.abspath(p).startswith(os.path.abspath(root)):
        return None
    return p


def send_error(sock, addr, code, msg):
    sock.sendto(struct.pack("!HH", OP_ERROR, code) + msg.encode() + b"\0", addr)


def handle_rrq(root, addr, fname):
    path = safe_join(root, fname)
    if not path or not os.path.isfile(path):
        log("RRQ %s -> 404" % fname)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        send_error(s, addr, 1, "file not found")
        s.close()
        return

    data = open(path, "rb").read()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    log("RRQ %s -> %d bytes" % (fname, len(data)))

    block = 1
    off = 0
    retry = 0
    while retry < 5:
        chunk = data[off:off + BLOCK]
        s.sendto(struct.pack("!HH", OP_DATA, block) + chunk, addr)
        try:
            pkt, _ = s.recvfrom(1024)
            op, blk = struct.unpack("!HH", pkt[:4])
            if op == OP_ACK and blk == block:
                off += BLOCK
                block = (block + 1) & 0xFFFF
                retry = 0
                if len(chunk) < BLOCK:
                    log("RRQ %s done (%d blocks)" % (fname, block - 1))
                    break
            else:
                retry += 1
        except socket.timeout:
            retry += 1
    s.close()


def handle_wrq(root, addr, fname, allow_write):
    if not allow_write:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        send_error(s, addr, 2, "write denied")
        s.close()
        log("WRQ %s -> denied" % fname)
        return

    updir = os.path.join(root, "upload")
    os.makedirs(updir, exist_ok=True)
    path = safe_join(updir, os.path.basename(fname))
    if not path:
        return

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(10)
    s.sendto(struct.pack("!HH", OP_ACK, 0), addr)

    total = 0
    block = 1
    with open(path, "wb") as f:
        while True:
            try:
                pkt, _ = s.recvfrom(2048)
            except socket.timeout:
                log("WRQ %s timeout after %d bytes" % (fname, total))
                break
            op, blk = struct.unpack("!HH", pkt[:4])
            if op != OP_DATA:
                break
            if blk == block:
                f.write(pkt[4:])
                total += len(pkt) - 4
                s.sendto(struct.pack("!HH", OP_ACK, block), addr)
                if len(pkt) - 4 < BLOCK:
                    log("WRQ %s done (%d bytes)" % (fname, total))
                    break
                block = (block + 1) & 0xFFFF
            else:
                s.sendto(struct.pack("!HH", OP_ACK, blk), addr)
    s.close()


def main():
    ap = argparse.ArgumentParser(description="minimal TFTP server")
    ap.add_argument("--root", default=".", help="共享目录（默认当前目录）")
    ap.add_argument("--port", type=int, default=69, help="UDP 端口（默认 69）")
    ap.add_argument("--bind", default="0.0.0.0", help="监听地址")
    ap.add_argument("--allow-write", action="store_true", help="允许设备上传到 <root>/upload")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        sys.exit("root 不是目录: %s" % root)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((args.bind, args.port))
    except PermissionError:
        sys.exit("端口 %d 需要管理员/root 权限" % args.port)

    log("TFTP 就绪  %s:%d  root=%s  写入=%s"
        % (args.bind, args.port, root, "允许" if args.allow_write else "禁止"))

    while True:
        try:
            pkt, addr = sock.recvfrom(2048)
        except KeyboardInterrupt:
            break
        if len(pkt) < 4:
            continue
        op = struct.unpack("!H", pkt[:2])[0]
        name = pkt[2:].split(b"\0", 1)[0].decode("latin1", "replace")
        if op == OP_RRQ:
            handle_rrq(root, addr, name)
        elif op == OP_WRQ:
            handle_wrq(root, addr, name, args.allow_write)

    sock.close()


if __name__ == "__main__":
    main()
