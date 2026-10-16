from PIL import Image
import math

W, H = 1920, 1080

def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))

def radial(path, cx_frac, cy_frac, stops):
    """stops: list of (pos 0-1, (r,g,b)) ordered by pos."""
    img = Image.new("RGB", (W, H))
    px = img.load()
    cx, cy = W * cx_frac, H * cy_frac
    # normalise radius so the farthest corner is t=1
    corners = [(0, 0), (W, 0), (0, H), (W, H)]
    maxr = max(math.hypot(cx - x, cy - y) for x, y in corners)
    for y in range(H):
        for x in range(W):
            t = math.hypot(x - cx, y - cy) / maxr
            # find bracketing stops
            for i in range(len(stops) - 1):
                p0, c0 = stops[i]
                p1, c1 = stops[i + 1]
                if t <= p1 or i == len(stops) - 2:
                    tt = 0 if p1 == p0 else min(max((t - p0) / (p1 - p0), 0), 1)
                    px[x, y] = lerp(c0, c1, tt)
                    break
    img.save(path, "PNG")
    print("wrote", path)

TEAL_HI  = (30, 70, 78)    # #1E464E
TEAL_MID = (22, 52, 58)    # #16343A
TEAL_LO  = (14, 33, 37)    # #0E2125

# cover: glow up-left
radial("bg/bg_cover.png", 0.18, 0.12, [(0.0, TEAL_HI), (0.52, TEAL_MID), (1.0, TEAL_LO)])
# dividers / hero / closing: centred glow
radial("bg/bg_dark.png", 0.50, 0.42, [(0.0, TEAL_HI), (0.55, TEAL_MID), (1.0, TEAL_LO)])


# pptxgenjs has no image `tint`, so the white-on-dark Monash logo used on the
# title, divider and closing slides is pre-rendered here from the same source
# logo the report uses: every pixel forced to white, the original alpha kept,
# so the mark's shape and antialiasing survive the recolour.
def white_logo(src_path, out_path):
    src = Image.open(src_path).convert("RGBA")
    alpha = src.getchannel("A")
    out = Image.new("RGBA", src.size, (255, 255, 255, 0))
    out.putalpha(alpha)
    out.save(out_path, "PNG")
    print("wrote", out_path)

white_logo("../../report/figures/monash-logo.png", "bg/monash-logo-white.png")
