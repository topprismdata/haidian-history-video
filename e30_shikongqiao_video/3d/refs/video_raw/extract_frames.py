# 视频证据帧图谱: 1fps 采样 -> 清晰度(Laplacian 方差) -> pHash 去重 -> 每片 contact sheet
# 用法: python3 extract_frames.py <video>... (输出到 ../video_frames/<name>/)
import sys, os, subprocess, json
import cv2, numpy as np

def phash(img, h=16):
    g = cv2.cvtColor(cv2.resize(img, (h, h)), cv2.COLOR_BGR2GRAY)
    return (g > g.mean()).flatten()

def sharp(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(g, cv2.CV_64F).var()

def run(vpath):
    name = os.path.splitext(os.path.basename(vpath))[0]
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video_frames", name)
    os.makedirs(outdir, exist_ok=True)
    cap = cv2.VideoCapture(vpath)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    step = int(round(fps))            # 1fps
    kept, i, frame_idx = [], 0, 0
    while True:
        ok = cap.grab()
        if not ok: break
        if i % step == 0:
            ok2, fr = cap.retrieve()
            if ok2:
                s = sharp(fr)
                small = cv2.resize(fr, (320, 180))
                kept.append((frame_idx, s, small.copy(), fr.copy() if s > 60 else None))
        i += 1; frame_idx = i
    cap.release()
    # 贪心: 按清晰度降序, pHash 距离>18% 才收
    kept.sort(key=lambda x: -x[1])
    sel, hashes = [], []
    for fidx, s, small, full in kept:
        h = phash(small)
        if all(np.mean(h != hh) > 0.18 for hh in hashes):
            hashes.append(h)
            if full is not None:
                fn = os.path.join(outdir, "f%06d_s%.0f.jpg" % (fidx, s))
                cv2.imwrite(fn, full, [cv2.IMWRITE_JPEG_QUALITY, 92])
            sel.append({"frame": fidx, "sharp": round(s, 1)})
            if len(sel) >= 120: break
    sel.sort(key=lambda x: x["frame"])
    json.dump(sel, open(os.path.join(outdir, "index.json"), "w"))
    # contact sheet 6x6
    files = sorted(f for f in os.listdir(outdir) if f.endswith(".jpg"))
    if files:
        tiles = []
        for f in files[:36]:
            im = cv2.imread(os.path.join(outdir, f))
            im = cv2.resize(im, (320, 180))
            cv2.putText(im, f.split("_")[0], (5, 20), 0, 0.5, (0, 255, 255), 1)
            tiles.append(im)
        rows = [np.hstack(tiles[r*6:(r+1)*6]) for r in range(0, (len(tiles)+5)//6)]
        if rows and rows[-1].shape[1] < 320*6:
            pad = 320*6 - rows[-1].shape[1]
            rows[-1] = np.pad(rows[-1], ((0,0),(0,pad),(0,0)))
        cv2.imwrite(os.path.join(outdir, "sheet.jpg"), np.vstack(rows))
    print("DONE %s kept=%d" % (name, len(sel)))

if __name__ == "__main__":
    for v in sys.argv[1:]:
        run(v)
