# e30_shikongqiao_video/3d/narration.py
# -*- coding: utf-8 -*-
"""P2-T8 旁白素材表(narration beats) + 禁词 lint(P2 出口交接 P3)。

两件事:
1. build_beats_text(seqdoc, report) -> str: 读 sequence.json(stage 分组)
   + g3_report.json(三门读数), 产出逐 stage 旁白素材表:
   每 stage → 规则号(R0-R7; **卸架序=R4/R6, 不是 R5** —— T7 裁决勘误)
   → G0 证据编号 → 素材要点; 四叙事铁律在对应 beats 行显式标注:
     ① 唯一硬结论=裸环合龙即自承(robustness 17/17)     → CLOSE_RING 行
     ② acceptance 17/17 是模型族结论(两假设+失效边界)   → SHOULDER 行
     ③ 卸架序 [工程推断·非史料]+串行临界定非不可行证明  → DSTART.WAVE 行
     ④ 对称同步卸架=安全族                              → WEDGE 行
   纯函数: 只消费计数字段, 与 elapsed_s 计时无关(可字节复现)。
2. narration_lint(text) -> List[Finding]: 旁白文本三道闸(qa_l2 I4 纪律:
   判据没跑不算通过 —— 禁词表被清空时返 NO_WORDS_TABLE, 不构绿):
     BANNED_WORD           伪史料/时代错位禁词(样筏/线道子/对合龙口/
                           管主剑/收分铁/铁搭头/"乾隆旨仿")逐词点名+位置
     MODERN_TERM_IN_QUOTE  现代工程词入古人台词(「」『』“”引语)——
                           B1: 古人无压力线概念, 引语内一票红(标签不豁免)
     MODERN_TERM_UNTAGGED  现代工程词入叙述未挂 [现代分析](挂标签放行;
                           [工程推断] 不豁免现代力学词)
     UNSOURCED_CLAIM       断言行无 G0 证据号且无允许标签
   文本行约定: 一行一断言单位; 豁免=空行/`#` 标题/```代码栅栏/行首元数据
   前缀(生成命令:/数据源:/对照账:/回放:) —— 元数据是溯源信息非史实断言。

证据编号体系与旁白红线单源: refs/construction_history.md(G0 门收口文档;
禁"样筏/线道子/对合龙口"三伪词、"管主剑/收分铁/铁搭头"杜撰铁活名、
"乾隆旨仿卢沟桥"无清代出处 A7、古人不得说现代力学词 B1)。

CLI: `python3 3d/narration.py` 读 3d/out/{sequence,g3_report}.json →
lint 自检零红才落盘 3d/out/narration_beats.md(beats 必须能过自己的 lint)。
blender-free; Python 3.9。
"""
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_OUT_DIR = os.path.join(_HERE, "out")

# ---------------------------------------------------------------------------
# 词表(测试钉非空 + brief 点名词在表; 清空 → NO_WORDS_TABLE 不构绿)
# ---------------------------------------------------------------------------

# 伪史料/时代错位禁词(refs/construction_history.md 旁白红线 + B 线术语正字)
BANNED_WORDS = ("样筏", "线道子", "对合龙口", "管主剑", "收分铁", "铁搭头",
                "乾隆旨仿")

# 现代工程/力学词(B1: 古人无压力线概念; brief 点名 压力线/倾覆裕度/中三分)
MODERN_TERMS = ("压力线", "倾覆裕度", "中三分", "三分点", "推力线",
                "极限分析", "安全系数", "稳定系数", "弯矩", "剪力", "偏心距")

ANALYSIS_TAG = "现代分析"          # 现代力学词叙述放行的唯一标签
_TAG_EXACT = ("现代分析", "工程参数·敏感性", "工作值", "推断",
              "通例迁移·卢沟桥", "存疑待考", "文献记载", "图像推导",
              "后世分析", "民间传说")
_METADATA_PREFIXES = ("生成命令:", "数据源:", "对照账:", "回放:")
_G0_RE = re.compile(r"(?<![A-Za-z0-9.])(?:C:)?[AB]\d+(?![0-9A-Za-z])")
_TAG_RE = re.compile(r"\[([^\[\]]{1,24})\]")
_QUOTE_RE = re.compile(u"[「『\u201c][^」』\u201d]*[」』\u201d]")


class Finding(object):
    """单条 lint 发现。kind ∈ {BANNED_WORD, MODERN_TERM_IN_QUOTE,
    MODERN_TERM_UNTAGGED, UNSOURCED_CLAIM, NO_WORDS_TABLE};
    line/col 1 起, line=0 表示与具体行无关(空表)。"""

    def __init__(self, kind, line, col, word, message):
        # type: (str, int, int, Optional[str], str) -> None
        self.kind = kind
        self.line = line
        self.col = col
        self.word = word
        self.message = message

    def __str__(self):
        # type: () -> str
        loc = "line %d" % self.line
        if self.col:
            loc += " col %d" % self.col
        w = " word=%r" % self.word if self.word else ""
        return "[%s] %s%s %s" % (self.kind, loc, w, self.message)

    __repr__ = __str__


def _tags(line):
    # type: (str) -> List[str]
    return _TAG_RE.findall(line)


def _tag_ok(tag):
    # type: (str) -> bool
    return tag in _TAG_EXACT or tag.startswith("工程推断")


def _has_allowed_tag(line):
    # type: (str) -> bool
    return any(_tag_ok(t) for t in _tags(line))


def narration_lint(text):
    # type: (str) -> List[Finding]
    """三道闸逐行核(约定见模块 docstring); 返回发现表, 空=绿。"""
    findings = []  # type: List[Finding]
    if not BANNED_WORDS:
        findings.append(Finding(
            "NO_WORDS_TABLE", 0, 0, None,
            "禁词表为空 —— 判据未执行不构绿(skip≠pass, qa_l2 I4 同纪律)"))
    in_fence = False
    for idx, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line or line.startswith("#"):
            continue
        # 闸1: 禁词逐词点名+位置
        for w in BANNED_WORDS:
            col = line.find(w)
            if col >= 0:
                findings.append(Finding(
                    "BANNED_WORD", idx, col + 1, w,
                    "伪史料/时代错位禁词(refs/construction_history.md 旁白红线)"))
        # 闸2: 现代工程词 —— 引语内一票红(标签不豁免); 叙述须挂 [现代分析]
        spans = _QUOTE_RE.findall(line)
        outside = _QUOTE_RE.sub(u"", line)
        has_analysis = ANALYSIS_TAG in _tags(line)
        for w in MODERN_TERMS:
            if any(w in sp for sp in spans):
                findings.append(Finding(
                    "MODERN_TERM_IN_QUOTE", idx, line.find(w) + 1, w,
                    "现代工程词入古人台词 —— B1: 古人无压力线概念, 标签不豁免"))
            if w in outside and not has_analysis:
                findings.append(Finding(
                    "MODERN_TERM_UNTAGGED", idx, line.find(w) + 1, w,
                    "现代工程词入叙述须挂 [%s]" % ANALYSIS_TAG))
        # 闸3: 断言行必须挂 G0 证据号或允许标签(元数据前缀豁免)
        if not (_G0_RE.search(line) or _has_allowed_tag(line)
                or line.startswith(_METADATA_PREFIXES)):
            findings.append(Finding(
                "UNSOURCED_CLAIM", idx, 1, None,
                "断言行无 G0 证据号且无允许标签(每条必须挂编号或显式标签)"))
    return findings


def narration_ok(findings):
    # type: (List[Finding]) -> bool
    """零发现才算绿(NO_WORDS_TABLE 使空表判据天然不绿)。"""
    return not findings


# ---------------------------------------------------------------------------
# beats: stage → 规则号 + 素材(每条自带 G0 编号或标签, 过自身 lint)
# ---------------------------------------------------------------------------

_MAT = {
    "R1": ("撞券石先行、墩肩分层自下而上(C:A2 撞券石名目; 层序为工程判断"
           " [工程推断·则例石作制度 C:A1])"),
    "R2": ("立架支拆券胎为官式计价在册术语(C:A3); 合龙前拱圈不能自持——"
           "撤侧墙与石灰土后五边折线自行坍塌(B14 孔庆普拆除实证), 必先架后券"),
    "R3": ("券石 θ 镜像配对两侧交替, 偶数位前缀平衡度≤ε=0.15 [现代分析]"
           "[工程参数·敏感性]; 券脸石/内券石/龙门石名目(C:A2)"),
    "CLOSE": "合龙石楔入, 拱圈自此闭合成环(B14/C:A2)",
    "R5A": "锁固带石与券脸石餬灰胶结、协同受压(C:A5 餬灰璺一手记述)",
    "R4": ("合龙后持荷窗 ≥3 拍方准落架 [工程参数·敏感性](B15 糯米灰浆早强"
           "通例只作背景注, 非史料常数)"),
    "DSTART": "全桥 17 孔同波起落架(依 G3④门全桥同波裁决) [现代分析]",
    "WEDGE": ("卸楔 λ 档 {0.25, 0.5, 0.75, 1.0} 全阶逐档、全孔同档同步"
              " [工程参数·敏感性]"),
    "CLEAR": "全部孔 λ 满档后统一拆架(落架次序无史料锚 [工程推断·非史料])",
    "R5B": ("肩背胞填筑, 拱上荷载渐次压实(C:A1 则例石作制度; B14 拆除实证"
            "券体依赖周围砌体共同工作)"),
    "R7P": "桥面铺装先于栏杆望柱安设(C:A1; 面上最后的官式次序 [工程推断])",
    "R7R": "栏杆/望柱继铺装安设(C:A1) [工程推断]",
    "R7C": "雕刻收尾(C:A1) [工程推断]",
}

# 四叙事铁律(行级标注; 与 T6/T7b 裁决口径逐字一致)
_IRON_1 = ("【铁律①】唯一硬结论=裸环合龙即自承(robustness 17/17 孔可行)"
           " [现代分析]")
_IRON_2 = ("【铁律②】acceptance 17/17 属模型族结论——依赖餬灰胶结协同+"
           "冠缝共享支点两假设, 失效边界见 p2-task-6-report §7.2/§9"
           " [现代分析]")
_IRON_3 = ("【铁律③】卸架序是 [工程推断·非史料]——C:A3 明言则例无工序"
           "教科书; 串行序是本门图式下的临界定(6/192 组合违例, util 1.009,"
           " 见 p2-task-7-report §9.2), 非不可行证明 [现代分析]")
_IRON_4 = ("【铁律④】对称同步卸架=安全族(全桥同波 0/192 组合违例, 最小"
           "推力读数) [现代分析]")


def stage_rule(name):
    # type: (str) -> Tuple[str, str]
    """stage 名 → (规则号, 素材)。卸架三波=R4/R6(T7 勘误: 非 R5)。
    未登记 stage 名 raise(fail-closed, 新 stage 必须显式登记)。"""
    if ".IMPOST." in name:
        return "R1", _MAT["R1"]
    if name.endswith(".CENTER_ERECT"):
        return "R2", _MAT["R2"]
    if ".RING.bank" in name:
        return "R3", _MAT["R3"]
    if name.endswith(".CLOSE_RING"):
        return "R2", _MAT["CLOSE"]
    if ".SHOULDER." in name:
        return "R5a", _MAT["R5A"]
    if name.endswith(".HOLD"):
        return "R4", _MAT["R4"]
    if name == "DECENTER.DSTART.WAVE":
        return "R4/R6", _MAT["DSTART"]
    if name.startswith("DECENTER.WEDGE."):
        return "R4/R6", _MAT["WEDGE"]
    if name == "DECENTER.CLEAR.WAVE":
        return "R4/R6", _MAT["CLEAR"]
    if name.endswith(".FILL"):
        return "R5b", _MAT["R5B"]
    if name.endswith(".R7.GLOBAL"):
        if name.startswith("PAVING"):
            return "R7", _MAT["R7P"]
        if name.startswith("RAIL_POST"):
            return "R7", _MAT["R7R"]
        return "R7", _MAT["R7C"]
    raise ValueError("narration: 未登记 stage 名 %r —— 新 stage 形制必须"
                     "显式登记规则号与素材(fail-closed)" % name)


def _iron_annotation(name):
    # type: (str) -> str
    if name.endswith(".CLOSE_RING"):
        return _IRON_1
    if ".SHOULDER." in name:
        return _IRON_2
    if name == "DECENTER.DSTART.WAVE":
        return _IRON_3
    if name.startswith("DECENTER.WEDGE."):
        return _IRON_4
    return ""


def _stage_n_stones(seqdoc, st):
    # type: (Dict[str, Any], Dict[str, Any]) -> int
    lo, hi = st["event_range"]
    n = 0
    for e in seqdoc["events"]:
        if lo <= e["seq"] <= hi and e["etype"] in ("PLACE_STONE", "ADD_FILL"):
            n += 1
    return n


def build_beats_text(seqdoc, report):
    # type: (Dict[str, Any], Dict[str, Any]) -> str
    """逐 stage 旁白素材表(纯函数; 只读计数字段, 与计时无关)。"""
    stages = seqdoc["sequence"]
    n_ev = len(seqdoc["events"])
    n_st = len(stages)
    holes = report["gate_stress"]["holes"]
    n_acc = sum(1 for h in holes.values() if h["acceptance"]["feasible"])
    n_rob = sum(1 for h in holes.values() if h["robustness"]["feasible"])
    imb = report["gate_imbalance"]
    dag = report["gate_dag"]
    lines = [
        "# E30 十七孔桥 P2 建造序列·旁白素材表(narration beats)",
        "",
        "生成命令: python3 3d/narration.py(读 3d/out/sequence.json + "
        "3d/out/g3_report.json; P3 逐 stage 取材, 引用即锁本表)",
        "数据源: sequence.json events=%d stages=%d; G3 三门全 ok(读数见下节)"
        % (n_ev, n_st),
        "",
        "## 四叙事铁律(全片口径; 对应 stage 行内有行级标注)",
        "1. 唯一硬结论=裸环合龙即自承: robustness(裸环 case) %d/%d 孔可行"
        " [现代分析]" % (n_rob, len(holes)),
        "2. acceptance %d/%d 是模型族结论: 依赖「餬灰胶结协同+冠缝共享支点」"
        "两假设, 失效边界见 p2-task-6-report §7.2/§9 [现代分析]"
        % (n_acc, len(holes)),
        "3. 卸架序是 [工程推断·非史料]: C:A3 明言则例无工序教科书; 串行序是"
        "本门图式下的临界定(6/192 组合违例, util 1.009, p2-task-7-report "
        "§9.2), 非不可行证明 [现代分析]",
        "4. 对称同步卸架=安全族: 全桥同波逐档 %d/%d 组合违例(最小推力读数)"
        " [现代分析]" % (len(imb["violations"]), imb["n_evals"]),
        "",
        "## G3 三门读数(引用即锁本报告)",
        "- gate_dag(①支撑活跃): %d 事件全 snapshot %d 违例 [现代分析]"
        % (dag["n_snapshots"], len(dag["violations"])),
        "- gate_stress(③压力线): acceptance %d/%d 孔可行; robustness(裸环)"
        " %d/%d 孔可行 [现代分析]" % (n_acc, len(holes), n_rob, len(holes)),
        "- gate_imbalance(④墩不平衡·最小推力读数): %d 事件-墩组合 %d 违例; "
        "viol_uniform_hmax=%d(一致 Hmax 读数下违例组合数, 条件性在册——"
        "不违例≠可行证明) [现代分析]"
        % (imb["n_evals"], len(imb["violations"]),
           imb["viol_uniform_hmax"]),
        "",
        "## 逐 stage beats(规则号 R0-R7; 卸架序=R4/R6 非 R5 —— T7 勘误)",
    ]
    for st in stages:
        rule, mat = stage_rule(st["stage"])
        lo, hi = st["event_range"]
        iron = _iron_annotation(st["stage"])
        tail = ("; " + iron) if iron else ""
        lines.append(
            "- %s %s | 规则=%s | G0=%s | 事件 %d-%d · 石 %d | 素材: %s%s"
            % (st["id"], st["stage"], rule, st.get("evidence") or "无",
               lo, hi, _stage_n_stones(seqdoc, st), mat, tail))
    lines.append("")
    lines.append("对照账: 本表 stage 分组/事件区间与 sequence.json 逐位同源; "
                 "三门读数与 g3_report.json 同源; narration_lint(本表)==[]")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    # type: () -> int
    with open(os.path.join(_OUT_DIR, "sequence.json"), encoding="utf-8") as f:
        seqdoc = json.load(f)
    with open(os.path.join(_OUT_DIR, "g3_report.json"),
              encoding="utf-8") as f:
        report = json.load(f)
    text = build_beats_text(seqdoc, report)
    finds = narration_lint(text)
    if finds:
        for fd in finds[:20]:
            print("LINT", fd)
        print("narration_lint: %d 条 —— beats 未过自身 lint, 拒绝落盘"
              % len(finds))
        return 1
    out = os.path.join(_OUT_DIR, "narration_beats.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print("OK beats stages=%d lines=%d lint=0 -> %s"
          % (len(seqdoc["sequence"]), text.count("\n") + 1, out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
