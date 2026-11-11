import struct, zlib, sys, os, re

EXE = sys.argv[1] if len(sys.argv) > 1 else "input.exe"
OUT = sys.argv[2] if len(sys.argv) > 2 else "extracted"
os.makedirs(OUT, exist_ok=True)

MAGIC = b'MEI\014\013\012\013\016'

data = open(EXE, 'rb').read()
pos = data.rfind(MAGIC)
print(f"cookie magic at: {pos:#x}, file size: {len(data):#x}")
if pos < 0:
    sys.exit("no cookie")

# cookie: magic(8) + pkgLen(4) + toc(4) + tocLen(4) + pyvers(4) [+ pylibname(64) in v2.3+]
cookie = data[pos:pos+88]
magic, pkgLen, tocPos, tocLen, pyvers = struct.unpack('!8sIIII', cookie[:24])
print(f"pkgLen={pkgLen:#x} tocPos={tocPos:#x} tocLen={tocLen:#x} pyvers={pyvers}")

# package starts at cookie_pos - pkgLen + 8 (pkgLen counts from magic start... actually: pos of magic is start of package area end)
pkgStart = pos + 8 + 24 + 64 - pkgLen  # trailing cookie size after package
# simpler: archive starts at pos - pkgLen + len(cookie_total)
cookieTotal = 8 + 4*4 + 64
pkgStart = pos - pkgLen + cookieTotal
print(f"pkgStart={pkgStart:#x}")

toc = data[pkgStart+tocPos : pkgStart+tocPos+tocLen]
i = 0
entries = []
while i < len(toc):
    (entryLen,) = struct.unpack('!i', toc[i:i+4])
    entryPos, cmprsd, uncmprsd, cmprsFlag, typeCmprs = struct.unpack('!IIIBc', toc[i+4:i+18])
    name = toc[i+18:i+entryLen].rstrip(b'\0').decode('utf-8', 'replace')
    entries.append((entryPos, cmprsd, uncmprsd, cmprsFlag, typeCmprs, name))
    i += entryLen

print(f"TOC entries: {len(entries)}")
for entryPos, cmprsd, uncmprsd, cmprsFlag, typeCmprs, name in entries:
    raw = data[pkgStart+entryPos : pkgStart+entryPos+cmprsd]
    try:
        payload = zlib.decompress(raw) if cmprsFlag == 1 else raw
    except Exception as e:
        payload = b''
    if not name:
        continue
    safe = re.sub(r'[^A-Za-z0-9_.\-]', '_', name)[:120]
    fn = os.path.join(OUT, safe)
    t = typeCmprs.decode('latin1')
    try:
        if payload:
            ext = {'s': '.txt', 'm': '.pyc', 'M': '.pyc', 'b': '', 'x': '', 'z': '.pyz', 'Z': '.pyz'}.get(t, '.bin')
            if not name:
                continue
            fn = re.sub(r'[^A-Za-z0-9_.\-]', '_', name)[:140]
            fp = os.path.join(OUT, fn)
            open(fp, 'wb').write(payload)
        print(f"[{t}] {name} ({len(payload)}B)")
    except Exception as e:
        print(f"  write fail {name}: {e}")

# Also extract PYZ contents if present
for entryPos, cmprsd, uncmprsd, cmprsFlag, typeCmprs, name in entries:
    t = typeCmprs.decode('latin1')
    if t not in ('z', 'Z'):
        continue
    raw = data[pkgStart+entryPos : pkgStart+entryPos+cmprsd]
    try:
        pyz = zlib.decompress(raw) if cmprsFlag == 1 else raw
    except Exception:
        continue
    print(f"PYZ archive found: {name} ({len(pyz)}B)")
    # PYZ magic + toc
    if pyz[:4] == b'PYZ\0':
        (tocPos2, tocLen2) = struct.unpack('!II', pyz[8:16])
        toc2 = pyz[tocPos2:tocPos2+tocLen2]
        j = 0
        idx = 0
        while j < len(toc2):
            (entryLen2,) = struct.unpack('!I', toc2[j:j+4])
            if entryLen2 == 0: break
            cmprsd2, uncmprsd2, cmprsFlag2, typeCmprs2 = struct.unpack('!IIBc', toc2[j+4:j+14])
            name2 = toc2[j+14:j+entryLen2].rstrip(b'\0').decode('utf-8','replace')
            j += entryLen2
            idx += 1
        print(f"  PYZ modules: {idx}")
print("DONE")
