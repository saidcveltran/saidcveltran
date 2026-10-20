#!/usr/bin/env python3
"""Downscale the logo variants used in the README header (standard library only).

usage: python -I tools/make_logo.py <src.png> <dst.png> <size> [recolor-near-black-hex]
"""
import struct
import sys
import zlib


def read_png(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, chunks = 8, []
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        chunks.append((data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]))
        pos += 12 + n
    d = dict(chunks)
    w, h, depth, ct, _, _, inter = struct.unpack(">IIBBBBB", d[b"IHDR"])
    assert depth == 8 and inter == 0, (depth, inter)
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    raw = zlib.decompress(b"".join(c for t, c in chunks if t == b"IDAT"))
    stride = w * bpp
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        ft = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if ft == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif ft == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif ft == 3:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif ft == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(line))
        prev = line
    return w, h, ct, d.get(b"PLTE"), rows


def to_rgb(ct, pal, rows):
    out = []
    for r in rows:
        if ct == 3:
            o = bytearray()
            for v in r:
                o += pal[v * 3:v * 3 + 3]
            out.append(bytes(o))
        elif ct == 2:
            out.append(r)
        elif ct == 6:
            o = bytearray()
            for x in range(0, len(r), 4):
                a = r[x + 3]
                for k in range(3):
                    o.append((r[x + k] * a + 255 * (255 - a)) // 255)
            out.append(bytes(o))
        elif ct == 0:
            out.append(bytes(v for v in r for _ in range(3)))
        else:
            raise SystemExit("unsupported colour type")
    return out


def downscale(rows, w, h, n):
    xs = [(i * w // n, max((i + 1) * w // n, i * w // n + 1)) for i in range(n)]
    ys = [(i * h // n, max((i + 1) * h // n, i * h // n + 1)) for i in range(n)]
    out = []
    for y0, y1 in ys:
        acc = [[0] * n for _ in range(3)]
        for y in range(y0, y1):
            r = rows[y]
            for k in range(3):
                ch = r[k::3]
                a = acc[k]
                for i, (x0, x1) in enumerate(xs):
                    a[i] += sum(ch[x0:x1])
        cnt = (y1 - y0) * (xs[0][1] - xs[0][0])
        line = bytearray()
        for i in range(n):
            c = (xs[i][1] - xs[i][0]) * (y1 - y0)
            for k in range(3):
                line.append(min(255, (acc[k][i] + c // 2) // c))
        out.append(bytes(line))
    return out


def write_png(path, rows, n):
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    best = None
    for mode in ("sub", "up"):
        buf = bytearray()
        prev = bytes(n * 3)
        for r in rows:
            if mode == "sub":
                f = bytes([r[i] - (r[i - 3] if i >= 3 else 0) & 255 for i in range(len(r))])
                buf += b"\x01" + f
            else:
                buf += b"\x02" + bytes((r[i] - prev[i]) & 255 for i in range(len(r)))
            prev = r
        z = zlib.compress(bytes(buf), 9)
        if best is None or len(z) < len(best):
            best = z
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", best) + chunk(b"IEND", b""))
    open(path, "wb").write(png)
    return len(png)


def main():
    src, dst, size = sys.argv[1], sys.argv[2], int(sys.argv[3])
    w, h, ct, pal, rows = read_png(src)
    if len(sys.argv) > 4:
        hexv = sys.argv[4].lstrip("#")
        bg = bytes(int(hexv[i:i + 2], 16) for i in (0, 2, 4))
        assert ct == 3, "recolour needs a palette PNG"
        pal = bytearray(pal)
        for i in range(0, len(pal), 3):
            if max(pal[i:i + 3]) <= 20:
                pal[i:i + 3] = bg
    rgb = to_rgb(ct, pal, rows)
    print(src, w, h, "->", size, "bytes", write_png(dst, downscale(rgb, w, h, size), size))


if __name__ == "__main__":
    main()
