import sys, os, subprocess, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
LIB = '/home/claude/coogi-ad-assets/brand/library-2026-11/'
BR = '/home/claude/coogi-ad-assets/brand/'
GF = '/usr/share/fonts/truetype/google-fonts/ofl/'
ANTON = GF + 'anton/Anton-Regular.ttf'
CARDO = GF + 'cardo/Cardo-Regular.ttf'
CARDO_I = GF + 'cardo/Cardo-Italic.ttf'
INTER_B = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
INTER_M = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'
K = (13, 13, 13); Y = (255, 204, 0); R = (214, 40, 40); B = (22, 104, 220); G = (0, 138, 78)
WH = (255, 255, 255); CREAM = (244, 239, 230)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(p): p = clamp(p); return 1 - (1 - p) ** 3
def eio(p): p = clamp(p); return p * p * (3 - 2 * p)

_fc = {}
def font(path, size):
    k = (path, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

_tc = {}
def text(s, path, size, fill, tracking=0):
    k = (s, path, size, fill, tracking)
    if k in _tc: return _tc[k]
    f = font(path, size)
    if tracking:
        ws = [f.getlength(c) for c in s]; tw = int(sum(ws) + tracking * (len(s) - 1)) + 8
    else:
        tw = int(f.getlength(s)) + 8
    asc, desc = f.getmetrics()
    im = Image.new('RGBA', (tw + 20, asc + desc + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if tracking:
        x = 10
        for c, w in zip(s, ws): d.text((x, 10), c, font=f, fill=fill); x += w + tracking
    else:
        d.text((10, 10), s, font=f, fill=fill)
    im = im.crop(im.getbbox()); _tc[k] = im
    return im

def fit(s, path, maxw, maxsize, fill, tracking=0):
    size = maxsize
    while size > 20:
        im = text(s, path, size, fill, tracking)
        if im.width <= maxw: return im
        size = int(size * 0.96)
    return im

def paste(dst, im, cx, y, alpha=1.0, scale=1.0, anchor='top'):
    if alpha <= 0.003: return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 1.0:
        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
    x = int(cx - im.width / 2)
    yy = int(y - im.height / 2) if anchor == 'mid' else int(y)
    dst.paste(im, (x, yy), im)

_pc = {}
def photo(name, w, h, cx=0.5, top=0.15, bot=0.92, over=1.12):
    """Cover-crop a library photo (logo strip and dots cropped off) to w x h * over."""
    k = (name, w, h, cx, top, bot, over)
    if k in _pc: return _pc[k]
    im = Image.open(LIB + name).convert('RGB')
    iw, ih = im.size
    y0, y1 = int(ih * top), int(ih * bot)
    ch = y1 - y0; cw = ch * w / h
    if cw > iw: cw = iw; ch = cw * h / w; y0 = int(y0 + ((y1 - y0) - ch) / 2)
    x0 = clamp(cx * iw - cw / 2, 0, iw - cw)
    im = im.crop((int(x0), y0, int(x0 + cw), int(y0 + ch))).resize((int(w * over), int(h * over)), Image.LANCZOS)
    _pc[k] = im
    return im

def zoomed(base, w, h, z, over=1.12):
    bw, bh = base.size
    z = clamp(z, 1.0, over)
    vw, vh = bw / z, bh / z
    x0, y0 = (bw - vw) / 2, (bh - vh) / 2
    return base.resize((w, h), Image.BILINEAR, box=(x0, y0, x0 + vw, y0 + vh))

_lg = {}
def logo(kind, width):
    k = (kind, width)
    if k not in _lg:
        im = Image.open(BR + f'logo_{kind}.png').convert('RGBA'); im = im.crop(im.getbbox())
        _lg[k] = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    return _lg[k]

def solid(c): return Image.new('RGB', (W, H), c)
_gr = {}
def gradient(y0, y1, maxa):
    k = (y0, y1, maxa)
    if k not in _gr:
        g = Image.new('L', (1, H), 0)
        for y in range(H): g.putpixel((0, y), int(maxa * eio((y - y0) / (y1 - y0))))
        im = Image.new('RGBA', (W, H), (0, 0, 0, 255)); im.putalpha(g.resize((W, H)))
        _gr[k] = im
    return _gr[k]

# ---------------------------------------------------------------- 1. HYPE
H_FLASH = ['blue-hoodie-set-night.jpg', 'womens-longsleeve-orange.jpg', 'camo-hoodie.jpg',
           'tonal-navy-crewneck.jpg', 'womens-cardigan-pink-bag-car.jpg', 'black-zip-set-chair.jpg']
H_SC = [('blue-green-crewneck-vinyl.jpg', 'BLACK', 'FRIDAY', Y, K),
        ('blue-hoodie-set-night.jpg', '25% OFF', 'SITEWIDE', Y, K),
        ('womens-longsleeve-blue.jpg', 'UP TO 45% OFF', 'SALE SECTION ITEMS', R, WH),
        ('tonal-green-crewneck.jpg', '2X', 'REWARD POINTS', B, WH),
        ('black-zip-set-couch.jpg', 'FREE', 'MYSTERY GIFT · EVERY ORDER', G, WH)]
H_T0, H_D = 1.2, 1.3
H_END = H_T0 + H_D * len(H_SC)
H_LINES = ['25% OFF SITEWIDE', 'UP TO 45% OFF SALE ITEMS', '2X REWARD POINTS', 'FREE MYSTERY GIFT']
def hype(t):
    if t < H_T0:
        i = int(t / 0.2); p = (t - i * 0.2) / 0.2
        f = zoomed(photo(H_FLASH[i], W, H), W, H, 1.0 + 0.08 * p)
        paste(f, logo('white', 520), W / 2, 880, 1.0)
        return f
    if t < H_END:
        i = int((t - H_T0) / H_D); lt = t - H_T0 - i * H_D
        name, big, sub, col, tcol = H_SC[i]
        f = zoomed(photo(name, W, H), W, H, 1.0 + 0.1 * lt / H_D)
        f = Image.blend(f, solid(K), 0.5)
        p = eo(lt / 0.18)
        bigim = fit(big, ANTON, 940, 520, WH if col != Y else Y)
        paste(f, bigim, W / 2, 830, clamp(lt / 0.08), 1.6 - 0.6 * p, 'mid')
        if lt > 0.22:
            q = eo((lt - 0.22) / 0.2)
            s = fit(sub, ANTON, 820, 92, tcol)
            bw, bh = s.width + 70, 140
            y = 830 + bigim.height / 2 + 50
            bar = Image.new('RGBA', (int(bw * q) or 1, bh), col + (255,))
            f.paste(bar, (int(W / 2 - bw / 2), int(y)))
            if q > 0.6: paste(f, s, W / 2, y + bh / 2, clamp((q - 0.6) / 0.3), 1.0, 'mid')
        if lt < 0.07: f = Image.blend(f, solid(WH), 0.55 * (1 - lt / 0.07))
        return f
    lt = t - H_END
    f = solid(Y)
    paste(f, logo('dark', 330), W / 2, 280)
    paste(f, fit('BLACK FRIDAY', ANTON, 900, 260, K), W / 2, 450, clamp(lt / 0.15), 1.25 - 0.25 * eo(lt / 0.2))
    d = ImageDraw.Draw(f)
    for i, s in enumerate(H_LINES):
        q = eo((lt - 0.25 - 0.13 * i) / 0.25)
        if q <= 0: continue
        y = 730 + i * 150
        d.rectangle((90, y, 90 + int(900 * q), y + 128), fill=K)
        if q > 0.5: paste(f, fit(s, ANTON, 820, 84, Y), W / 2, y + 64, clamp((q - 0.5) / 0.4), 1.0, 'mid')
    q = clamp((lt - 1.0) / 0.3)
    paste(f, text('NO CODE NEEDED  ·  COOGI.COM', INTER_B, 40, K, 3), W / 2, 1380, q)
    if lt < 0.07: f = Image.blend(f, solid(WH), 0.6 * (1 - lt / 0.07))
    return f
HYPE_DUR = H_END + 2.6

# ---------------------------------------------------------------- 2. EDITORIAL
E_SC = [('womens-longsleeve-blue.jpg', 'THE EVENT', 'Black Friday', 'four offers, no code needed', 0.5),
        ('blue-green-crewneck-vinyl.jpg', 'N° 01', '25% Off', 'sitewide', 0.5),
        ('womens-cardigan-pink-bag-car.jpg', 'N° 02', 'Up to 45% Off', 'sale section items', 0.45),
        ('tonal-navy-crewneck.jpg', 'N° 03', '2X Points', 'double rewards on every order', 0.5),
        ('womens-knit-tee.jpg', 'N° 04', 'Mystery Gift', 'free with every order', 0.5)]
E_D, E_X = 2.2, 0.6
E_END = E_D * len(E_SC)
def ed_scene(i, lt):
    name, lab, head, sub, cx = E_SC[i]
    f = zoomed(photo(name, W, H, cx), W, H, 1.0 + 0.09 * lt / (E_D + E_X)).convert('RGBA')
    f.alpha_composite(gradient(820, 1500, 215))
    f = f.convert('RGB')
    a = eio((lt - 0.25) / 0.6); dy = 26 * (1 - eo((lt - 0.25) / 0.7))
    paste(f, text(lab, INTER_M, 30, WH, 9), W / 2, 1150 + dy, a * 0.9)
    ImageDraw.Draw(f).line((W / 2 - 45 * a, 1208, W / 2 + 45 * a, 1208), fill=WH, width=2)
    paste(f, fit(head, CARDO, 920, 150, WH), W / 2, 1245 + dy, a)
    a2 = eio((lt - 0.55) / 0.6)
    paste(f, fit(sub, CARDO_I, 900, 62, WH), W / 2, 1415, a2)
    return f
E_LINES = [('01', '25% off sitewide'), ('02', 'Up to 45% off sale section items'),
           ('03', '2X reward points'), ('04', 'Free mystery gift with every order')]
def ed_end(lt):
    f = solid(CREAM); d = ImageDraw.Draw(f)
    paste(f, logo('dark', 300), W / 2, 290, eio(lt / 0.5))
    paste(f, text('Black Friday', CARDO, 150, K), W / 2, 470, eio((lt - 0.1) / 0.6))
    for i, (n, s) in enumerate(E_LINES):
        a = eio((lt - 0.45 - 0.18 * i) / 0.55)
        y = 740 + i * 150
        d.line((150, y - 28, 150 + 780 * a, y - 28), fill=(170, 160, 145), width=2)
        paste(f, text('N° ' + n, INTER_M, 24, (120, 110, 95), 6), W / 2, y, a)
        paste(f, fit(s, CARDO, 780, 58, K), W / 2, y + 42, a)
    a = eio((lt - 1.4) / 0.5)
    paste(f, text('NO CODE NEEDED   ·   COOGI.COM', INTER_M, 30, K, 7), W / 2, 1390, a)
    return f
def editorial(t):
    if t >= E_END + E_X: return ed_end(t - E_END)
    i = min(int(t / E_D), len(E_SC) - 1); lt = t - i * E_D
    if t >= E_END: return Image.blend(ed_scene(len(E_SC) - 1, t - (len(E_SC) - 1) * E_D), ed_end(t - E_END), eio((t - E_END) / E_X))
    f = ed_scene(i, lt)
    if i > 0 and lt < E_X: f = Image.blend(ed_scene(i - 1, lt + E_D), f, eio(lt / E_X))
    return f
EDIT_DUR = E_END + 3.4

# ---------------------------------------------------------------- 3. COLOR BLOCK
C_SC = [(Y, K, '25% OFF', 'SITEWIDE', 'red-knit-jacket.jpg', dict(top=0.0, bot=1.0)),
        (R, WH, 'UP TO 45% OFF', 'SALE SECTION ITEMS', 'womens-longsleeve-orange.jpg', dict(top=0.2, bot=0.85)),
        (B, WH, '2X', 'REWARD POINTS', 'camo-hoodie.jpg', dict(top=0.16, bot=0.8)),
        (G, WH, 'FREE', 'MYSTERY GIFT · EVERY ORDER', 'blue-hoodie-set-night.jpg', dict(top=0.16, bot=0.8))]
C_D = 1.7
C_END = C_D * len(C_SC)
CW_, CH_ = 760, 700
_mask = Image.new('L', (CW_, CH_), 0); ImageDraw.Draw(_mask).rounded_rectangle((0, 0, CW_ - 1, CH_ - 1), 30, fill=255)
C_BARS = [(Y, K, '25% OFF SITEWIDE'), (R, WH, 'UP TO 45% OFF SALE ITEMS'), (B, WH, '2X REWARD POINTS'), (G, WH, 'FREE MYSTERY GIFT')]
def cb_scene(i, lt, f):
    col, tc, big, sub, name, kw = C_SC[i]
    wipe = eo(lt / 0.28)
    ImageDraw.Draw(f).rectangle((0, int(H * (1 - wipe)), W, H), fill=col)
    a = clamp((lt - 0.12) / 0.12)
    x = (1 - eo((lt - 0.1) / 0.3)) * -260
    paste(f, text('BLACK FRIDAY', INTER_B, 34, tc, 10), W / 2 + x, 262, a)
    bigim = fit(big, ANTON, 900, 380, tc)
    paste(f, bigim, W / 2 + x, 325, a)
    paste(f, fit(sub, ANTON, 900, 84, tc), W / 2 - x, 325 + bigim.height + 28, a)
    p = eo((lt - 0.22) / 0.4)
    if p > 0:
        card = zoomed(photo(name, CW_, CH_, **kw), CW_, CH_, 1.0 + 0.08 * lt / C_D)
        f.paste(card, ((W - CW_) // 2, int(790 + 500 * (1 - p))), _mask)
def cb_end(lt, f):
    wipe = eo(lt / 0.28)
    d = ImageDraw.Draw(f); d.rectangle((0, int(H * (1 - wipe)), W, H), fill=K)
    paste(f, logo('white', 280), W / 2, 250, clamp((lt - 0.15) / 0.2))
    paste(f, fit('BLACK FRIDAY', ANTON, 900, 240, WH), W / 2, 395, clamp((lt - 0.15) / 0.15), 1.2 - 0.2 * eo((lt - 0.15) / 0.2))
    for i, (col, tc, s) in enumerate(C_BARS):
        p = eo((lt - 0.4 - 0.14 * i) / 0.35)
        if p <= 0: continue
        y = 650 + i * 172; off = int((1 - p) * 1100) * (-1 if i % 2 == 0 else 1)
        d.rectangle((90 + off, y, 990 + off, y + 156), fill=col)
        paste(f, fit(s, ANTON, 820, 96, tc), W / 2 + off, y + 78, 1.0, 1.0, 'mid')
    paste(f, text('NO CODE NEEDED  ·  COOGI.COM', INTER_B, 38, WH, 3), W / 2, 1390, clamp((lt - 1.2) / 0.3))
def colorblock(t):
    if t < C_END:
        i = int(t / C_D); lt = t - i * C_D
        f = solid(K)
        if i > 0: cb_scene(i - 1, C_D + lt, f)
        cb_scene(i, lt, f)
        return f
    f = solid(K); cb_scene(len(C_SC) - 1, C_D + t - C_END, f); cb_end(t - C_END, f)
    return f
CB_DUR = C_END + 3.6

STYLES = {'hype': (hype, HYPE_DUR), 'editorial': (editorial, EDIT_DUR), 'colorblock': (colorblock, CB_DUR)}

if __name__ == '__main__':
    name, mode = sys.argv[1], sys.argv[2]
    fn, dur = STYLES[name]
    if mode == 'test':
        ts = [float(x) for x in sys.argv[3:]]
        sheet = Image.new('RGB', (len(ts) * 360, 640))
        for i, t in enumerate(ts): sheet.paste(fn(t).resize((360, 640), Image.LANCZOS), (i * 360, 0))
        sheet.save(f'/tmp/test_{name}.jpg', quality=88); print(dur)
    else:
        out = sys.argv[3]; tmp = out.replace('.mp4', '.part.mp4')
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-shortest',
                              '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '96k',
                              '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
        for n in range(int(dur * FPS)): p.stdin.write(fn(n / FPS).tobytes())
        p.stdin.close()
        if p.wait() == 0: os.rename(tmp, out); print('ok', out, dur)
        else: sys.exit(1)
