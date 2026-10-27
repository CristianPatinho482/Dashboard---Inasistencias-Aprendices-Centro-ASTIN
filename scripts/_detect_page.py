# -*- coding: utf-8 -*-
from PIL import Image

path = r"C:\Users\capatino\AppData\Local\Temp\opencode\fit_page.png"
im = Image.open(path).convert("RGB")
w, h = im.size
px = im.load()

minx, miny, maxx, maxy = w, h, 0, 0
count = 0
for y in range(120, h - 120):
    for x in range(20, 1350):
        r, g, b = px[x, y]
        if abs(r - 246) <= 2 and abs(g - 246) <= 2 and abs(b - 246) <= 2:
            minx = min(minx, x)
            maxx = max(maxx, x)
            miny = min(miny, y)
            maxy = max(maxy, y)
            count += 1

print("bg bbox", (minx, miny, maxx, maxy), "count", count)
