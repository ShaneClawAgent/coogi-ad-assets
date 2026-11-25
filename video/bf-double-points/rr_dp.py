import subprocess,os
from playwright.sync_api import sync_playwright
FPS=30; CUTS=[0,2.5,5.0,8.125,10.0,12.5]; out="/home/claude/work/out/reel_dp"; os.makedirs(out,exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    pg=b.new_page(viewport={"width":540,"height":960},device_scale_factor=2)
    pg.goto("file:///home/claude/work/reel_dp.html"); pg.wait_for_timeout(3000)
    for i in range(5):
        f0=round(CUTS[i]*FPS); f1=round(CUTS[i+1]*FPS); tmp=f"{out}/tmp_s{i}.mp4"
        ff=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","image2pipe","-framerate",str(FPS),"-c:v","mjpeg","-i","-","-vf","format=yuv420p","-c:v","libx264","-crf","17","-preset","veryfast","-pix_fmt","yuv420p","-r",str(FPS),tmp],stdin=subprocess.PIPE)
        for f in range(f0,f1):
            pg.evaluate(f"seek({f/FPS})"); ff.stdin.write(pg.screenshot(type="jpeg",quality=92))
            if f in (148,372): pg.screenshot(path=f"/tmp/chk{f}.jpg",type="jpeg",quality=80)
        ff.stdin.close(); assert ff.wait()==0; os.rename(tmp,f"{out}/s{i}.mp4"); print("scene",i,f1-f0,flush=True)
    b.close()
open(f"{out}/list.txt","w").write("".join(f"file 's{i}.mp4'\n" for i in range(5)))
subprocess.check_call(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",f"{out}/list.txt","-c","copy",f"{out}/joined.mp4"])
dst="/home/claude/coogi-ad-assets/video/bf-double-points"; os.makedirs(dst,exist_ok=True)
subprocess.check_call(["ffmpeg","-y","-loglevel","error","-i",f"{out}/joined.mp4","-i","/tmp/hh.wav","-map","0:v","-map","1:a","-c:v","copy","-af","afade=t=out:st=12.0:d=0.5","-c:a","aac","-b:a","160k","-t","12.5","-movflags","+faststart",f"{dst}/coogi-2x-points-instagram.mp4"])
