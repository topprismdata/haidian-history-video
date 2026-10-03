"""统一入口：跑一集的七层验收。

    python3 -m qa_v2.run shucun            # L1/L2/L5/L6（快档，~1s/页；不含 L3/L4）
    python3 -m qa_v2.run shucun --ocr      # 加 L3+L4（~2min/页，8 页约 2 分钟）
    python3 -m qa_v2.run shucun --full     # 全开
    python3 -m qa_v2.run shucun --json     # 机读输出

只有 fail 阻塞退出码（spec §10.2）：历史集的 warn 噪声不应淹没真问题。
"""
import argparse
import pathlib
import sys
from typing import List, Optional, Tuple
from qa_v2.checks_content import (check_l4a, check_l4b, check_l4c,
                                  check_l4d, load_names)
from qa_v2.checks_data import check_l1, check_l2
from qa_v2.checks_render import (
    check_l3, check_l5, check_l6, assert_negative_control,
)
from qa_v2.data import Episode, Page, load_episode
from qa_v2.frames import CACHE as OCR_CACHE_DIR
from qa_v2.frames import OcrResult, ocr_cached, render_frame
from qa_v2.report import Finding, render_json, render_text

ROOT = pathlib.Path("/tmp/chemistry-video")
FRAME_DIR = pathlib.Path("/tmp/qa_frames")

# 集名 → Composition id（Remotion 注册名是驼峰）
COMPOSITION_OVERRIDES = {
    "yimuyuan": "YimuyuanCourse",
    "niangniangfu": "NiangniangfuCourse",
    "xisanqi": "XisanqiCourse",
    "gaoliangqiao": "GaoLiangQiaoCourse",
    "dazhongsi": "DazhongsiCourse",
    "landianchang": "LandianchangCourse",
    "shucun": "ShucunCourse",
    "suzhoujie": "SuzhoujieCourse",
    "zhongguancun": "ZhongguancunCourse",
    "changchunyuan": "ChangchunyuanCourse",
    "wanshou": "WanshouCourse",
    "changhe": "ChangheCourse",
    "fenshi": "FenshiCourse",
    "liulangzhuang": "LiulangzhuangCourse",
    "cishousi": "CishousiCourse",
    "shaoyuan": "ShaoyuanCourse",
    "weigongcun": "WeigongcunCourse",
}


def _source_freshness(ep_name: str) -> float:
    """该集全部输入的最新 mtime（秒）。

    覆盖：集目录（narration/slots/pages/组件）、公共板图、共享组件与 Root。
    任一输入比缓存帧新 → 帧过期，必须重渲。
    """
    import os
    roots = [
        ROOT / "src" / ep_name,
        ROOT / "public" / ep_name,
        ROOT / "src" / "components",
        ROOT / "src" / "Root.tsx",
        ROOT / "src" / "index.tsx",
    ]
    newest = 0.0
    for r in roots:
        if r.is_file():
            newest = max(newest, r.stat().st_mtime)
        elif r.is_dir():
            for dirpath, _dirnames, filenames in os.walk(r):
                for fn in filenames:
                    p = pathlib.Path(dirpath) / fn
                    try:
                        newest = max(newest, p.stat().st_mtime)
                    except OSError:
                        pass
    return newest


def _frame_for(
    ep_name: str,
    page: Page,
    use_ocr: bool,
    ep: Optional[Episode] = None,
) -> Tuple[pathlib.Path, Optional[OcrResult]]:
    """抽该页终态帧。--ocr 时顺带跑 OCR 并缓存。

    帧失效纪律（2026-10-02 FullQaRun 实测发现的缺陷修复）：
    png 存在但早于任一输入文件的 mtime → 视为过期，重渲；
    重渲后同步删除该页 OCR 缓存（缓存键不含帧内容哈希，旧 OCR 会配错新帧）。
    """
    out = FRAME_DIR / ep_name
    out.mkdir(parents=True, exist_ok=True)
    png = out / ("p%02d.png" % page.number)
    stale = False
    if png.exists() and png.stat().st_mtime < _source_freshness(ep_name):
        stale = True
    if stale or not png.exists():
        if ep is None:
            ep = load_episode(ep_name)
        render_frame(
            COMPOSITION_OVERRIDES[ep_name],
            ep.final_frame(page.number),
            png,
        )
        if stale:
            ocr_cache = OCR_CACHE_DIR / (
                "%s_p%02d.json" % (ep_name, page.number))
            if ocr_cache.exists():
                ocr_cache.unlink()
    if use_ocr:
        return png, ocr_cached(ep_name, page.number, png)
    return png, None


def run_episode(name: str, use_ocr: bool = False, full: bool = False) -> List[Finding]:
    """跑一集的全部适用层，返回 findings。"""
    ep = load_episode(name)
    findings = []

    # L1 / L2：纯数据
    findings += check_l1(ep)
    findings += check_l2(ep)

    names = load_names()
    ocr_by_page = {}
    for page in ep.pages:
        try:
            png, ocr = _frame_for(name, page, use_ocr, ep=ep)
        except Exception as exc:                      # 抽帧/OCR 失败
            findings.append(Finding(
                "L3", page.number, None, "fail", "RENDER_FAILED",
                "抽帧或 OCR 失败：%s" % exc))
            continue

        findings += check_l5(page, png)
        findings += check_l6(page, png)

        if ocr is None:
            continue
        ocr_by_page[page.number] = ocr
        findings += check_l3(page, ocr)
        if use_ocr:
            findings += check_l4a(page, ocr)
            findings += check_l4b(page, ocr, names)
            # 负控制：证明 L3/L4 不是恒真
            missed = assert_negative_control(page, ocr)
            if missed.not_caught > 0:
                findings.append(Finding(
                    "L3", page.number, None, "fail", "NEGATIVE_CONTROL_FAIL",
                    "负控制失败：%d 个槽位平移后仍判有文本，判据恒真"
                    % missed.not_caught))
            elif missed.untestable > 0:
                findings.append(Finding(
                    "L3", page.number, None, "info", "NEGATIVE_CONTROL_SKIPPED",
                    "负控制跳过：%d 个槽位密集无法构造空白平移矩形"
                    % missed.untestable))
    if use_ocr:
        findings += check_l4c(ep, ocr_by_page)

    # L4-d 引文一致性：计数自洽纯文本，快档即跑；ocr_by_page 非空时
    # （仅 --ocr）自动升级为带上屏核验
    findings += check_l4d(ep, ocr_by_page or None)
    return findings


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="qa_v2.run", description="七层验收")
    p.add_argument("episodes", nargs="+")
    p.add_argument("--ocr", dest="use_ocr", action="store_true",
                   help="开启 L4 内容闭环（慢，约 2 分钟/集）")
    p.add_argument("--full", action="store_true",
                   help="等价于 --ocr，并额外提示运行字幕验收")
    p.add_argument("--json", dest="as_json", action="store_true",
                   help="输出 JSON")
    return p.parse_args(argv)


def exit_code(findings: List[Finding]) -> int:
    from qa_v2.report import summarize
    return 1 if summarize(findings).get("fail") else 0


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    rc = 0
    for name in args.episodes:
        if name not in COMPOSITION_OVERRIDES:
            print("未知集 %s，可选 %s" % (name, list(COMPOSITION_OVERRIDES)))
            rc = 1
            continue
        findings = run_episode(name, use_ocr=(args.use_ocr or args.full),
                              full=args.full)
        print(render_json(findings, name) if args.as_json
              else render_text(findings, name))
        if exit_code(findings):
            rc = 1
    if args.full:
        print("\n提示：字幕/音频验收请另跑 "
              "/tmp/.asr-venv/bin/python "
              "/Volumes/macstudio/video-projects/scripts/verify_subtitles_asr.py")
    return rc


if __name__ == "__main__":
    sys.exit(main())
