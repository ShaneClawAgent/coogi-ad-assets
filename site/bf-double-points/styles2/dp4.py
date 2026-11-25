from playwright.sync_api import sync_playwright
from PIL import Image
import os
out="/home/claude/coogi-ad-assets/site/bf-double-points/styles2/"; os.makedirs(out,exist_ok=True)
NM={'a':'double-vision','b':'knit-numerals','c':'mosaic'}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    for sc,kinds in ((2,('desktop','mobile')),(3,('push',))):
        pg=b.new_page(viewport={"width":1400,"height":1000},device_scale_factor=sc)
        pg.goto("file:///home/claude/work/dp4.html"); pg.wait_for_timeout(1800)
        for s in 'abc':
            for k in kinds:
                pg.locator(f"#{s}-{k}").screenshot(path="/tmp/b.png"); Image.open("/tmp/b.png").convert("RGB").save(f"{out}coogi-2x-{NM[s]}-{k}.jpg",quality=90,optimize=True)
    b.close()
sh=Image.new("RGB",(3*(560+200+20),315+356+250+20),"#777")
for i,s in enumerate('abc'):
    x=i*780
    sh.paste(Image.open(f"{out}coogi-2x-{NM[s]}-desktop.jpg").resize((560,315)),(x,0))
    sh.paste(Image.open(f"{out}coogi-2x-{NM[s]}-mobile.jpg").resize((200,356)),(x+570,0))
    sh.paste(Image.open(f"{out}coogi-2x-{NM[s]}-push.jpg").resize((375,250)),(x,325))
sh.save("/tmp/dp4.jpg",quality=85)
