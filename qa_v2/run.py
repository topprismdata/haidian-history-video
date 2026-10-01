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
from qa_v2.checks_content import check_l4a, check_l4b, check_l4c, load_names
from qa_v2.checks_data import check_l1, check_l2
from qa_v2.checks_render import (
    check_l3, check_l5, check_l6, assert_negative_control,
)
from qa_v2.data import Episode, Page, load_episode
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
}


def _frame_for(
    ep_name: str,
    page: Page,
    use_ocr: bool,
    ep: Optional[Episode] = None,
) -> Tuple[pathlib.Path, Optional[OcrResult]]:
    """抽该页终态帧。--ocr 时顺带跑 OCR 并缓存。"""
    out = FRAME_DIR / ep_name
    out.mkdir(parents=True, exist_ok=True)
    png = out / ("p%02d.png" % page.number)
    if not png.exists():
        if ep is None:
            ep = load_episode(ep_name)
        render_frame(
            COMPOSITION_OVERRIDES[ep_name],
            ep.final_frame(page.number),
            png,
        )
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
            if missed:
                findings.append(Finding(
                    "L3", page.number, None, "fail", "NEGATIVE_CONTROL_FAIL",
                    "负控制失败：%d 个槽位平移后仍判有文本，判据恒真"
                    % missed))
    if use_ocr:
        findings += check_l4c(ep, ocr_by_page)
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
