#!/usr/bin/env python3

import json
import os
import struct
import sys

q = [[0, 0], [1, 0], [1, 1], [0, 1]]

def mix(a, b, c):
    a = ((a - b - c) ^ (c >> 13)) & 0xFFFFFFFF
    b = ((b - c - a) ^ (a << 8)) & 0xFFFFFFFF
    c = ((c - a - b) ^ (b >> 13)) & 0xFFFFFFFF
    a = ((a - b - c) ^ (c >> 12)) & 0xFFFFFFFF
    b = ((b - c - a) ^ (a << 16)) & 0xFFFFFFFF
    c = ((c - a - b) ^ (b >> 5)) & 0xFFFFFFFF
    a = ((a - b - c) ^ (c >> 3)) & 0xFFFFFFFF
    b = ((b - c - a) ^ (a << 10)) & 0xFFFFFFFF
    c = ((c - a - b) ^ (b >> 15)) & 0xFFFFFFFF
    return a, b, c


def word(d, i):
    return d[i] | (d[i + 1] << 8) | (d[i + 2] << 16) | (d[i + 3] << 24)


def string_id(text):
    d = bytes((c - 32) if 97 <= c <= 122 else c for c in text.encode("utf-8"))
    a = b = 0x9E3779B9
    c = 0
    i = 0
    while len(d) - i >= 12:
        a = (a + word(d, i)) & 0xFFFFFFFF
        b = (b + word(d, i + 4)) & 0xFFFFFFFF
        c = (c + word(d, i + 8)) & 0xFFFFFFFF
        a, b, c = mix(a, b, c)
        i += 12
    c = (c + len(d)) & 0xFFFFFFFF
    r = d[i:]
    k = len(r)
    if k >= 11: c = (c + (r[10] << 24)) & 0xFFFFFFFF
    if k >= 10: c = (c + (r[9] << 16)) & 0xFFFFFFFF
    if k >= 9: c = (c + (r[8] << 8)) & 0xFFFFFFFF
    if k >= 8: b = (b + (r[7] << 24)) & 0xFFFFFFFF
    if k >= 7: b = (b + (r[6] << 16)) & 0xFFFFFFFF
    if k >= 6: b = (b + (r[5] << 8)) & 0xFFFFFFFF
    if k >= 5: b = (b + r[4]) & 0xFFFFFFFF
    if k >= 4: a = (a + (r[3] << 24)) & 0xFFFFFFFF
    if k >= 3: a = (a + (r[2] << 16)) & 0xFFFFFFFF
    if k >= 2: a = (a + (r[1] << 8)) & 0xFFFFFFFF
    if k >= 1: a = (a + r[0]) & 0xFFFFFFFF
    return mix(a, b, c)[2]


def shortest(x):
    raw = struct.pack(">f", x)
    for p in range(1, 10):
        v = float("%.*g" % (p, x))
        if struct.pack(">f", v) == raw:
            return v
    return x


def flt(w):
    return shortest(struct.unpack(">f", struct.pack(">I", w))[0])


def decode(data):
    w = struct.unpack(">%dI" % (len(data) // 4), data)
    p = 2
    records = []
    for _ in range(w[1]):
        h, ver, n = w[p], w[p + 1], w[p + 4]
        rec = {"hash": "%08x" % h, "width": flt(w[p + 2]), "height": flt(w[p + 3])}
        if ver != 18:
            raise ValueError("unsupported record version %d" % ver)
        p += 5
        elements = []
        for _ in range(n):
            eid, k = w[p], w[p + 1]
            p += 2
            elements.append({"id": eid, "uv": [[flt(w[p + 2 * i]), flt(w[p + 2 * i + 1])] for i in range(k)]})
            p += 2 * k
        blocks = []
        nx = w[p]
        p += 1
        for _ in range(nx):
            block = {"header": list(w[p:p + 3])}
            nv = w[p + 3]
            p += 4
            block["vertices"] = []
            for _ in range(nv):
                v = w[p:p + 6]
                block["vertices"].append([flt(v[0]), flt(v[1]), "%08x" % v[2], flt(v[3]), flt(v[4]), flt(v[5])])
                p += 6
            t = w[p]
            p += 1
            block["triangles"] = [list(w[p + 3 * i:p + 3 * i + 3]) for i in range(t)]
            p += 3 * t
            block["tail"] = list(w[p:p + 2])
            p += 2
            blocks.append(block)
        if not (n == 1 and elements[0] == {"id": 0, "uv": q} and not blocks):
            rec["elements"] = elements
            if blocks:
                rec["blocks"] = blocks
        records.append(rec)
    if p != len(w):
        raise ValueError("%d words left over" % (len(w) - p))
    return records


def key_of(rec):
    if "path" in rec:
        return string_id(rec["path"])
    h = rec["hash"]
    return int(h, 16) if isinstance(h, str) else int(h)


def encode(records):
    u = lambda x: struct.pack(">I", x)
    f = lambda x: struct.pack(">f", x)
    keyed = sorted(((key_of(r), r) for r in records), key=lambda t: t[0])
    for (a, _), (b, _) in zip(keyed, keyed[1:]):
        if a == b:
            raise ValueError("duplicate hash %08x" % a)
    out = [u(0), u(len(keyed))]
    for h, r in keyed:
        elements = r.get("elements") or [{"id": 0, "uv": q}]
        out += [u(h), u(18), f(r["width"]), f(r["height"]), u(len(elements))]
        for e in elements:
            out += [u(e["id"]), u(len(e["uv"]))]
            for x, y in e["uv"]:
                out += [f(x), f(y)]
        blocks = r.get("blocks", [])
        out.append(u(len(blocks)))
        for b in blocks:
            out += [u(x) for x in b.get("header", [0, 0, 0])]
            out.append(u(len(b["vertices"])))
            for v in b["vertices"]:
                out += [f(v[0]), f(v[1]), u(int(v[2], 16)), f(v[3]), f(v[4]), f(v[5])]
            out.append(u(len(b["triangles"])))
            for t in b["triangles"]:
                out += [u(x) for x in t]
            out += [u(x) for x in b.get("tail", [0, 0])]
    return b"".join(out)


def add(records, path, width, height, elements=None, blocks=None):
    rec = {"path": path, "width": float(width), "height": float(height)}
    if elements:
        rec["elements"] = elements
    if blocks:
        rec["blocks"] = blocks
    records.append(rec)
    return rec


def read(path):
    with open(path, "rb") as f:
        return decode(f.read())


def write(path, records):
    with open(path, "wb") as f:
        f.write(encode(records))


def main():
    if len(sys.argv) < 2:
        sys.exit("no input file")
    src = sys.argv[1]
    stem, ext = os.path.splitext(src)
    if ext.lower() == ".json":
        with open(src, encoding="utf-8") as f:
            write(stem + ".ckd", json.load(f))
    else:
        with open(stem + ".json", "w", encoding="utf-8") as f:
            json.dump(read(src), f, indent=1)


if __name__ == "__main__":
    main()
