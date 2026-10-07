# e30_shikongqiao_video/tests/test_p2_full.py
# -*- coding: utf-8 -*-
"""P2-T8 真账全链 + 五组负控 + 出口工件 + narration lint(P2 出口)。

判据(brief Task 8 Step1/Step2 全量; 预估数已被实测取代——如实钉实测,
禁为凑 brief 预估改数):
- 真账全链: 5935 石全序(入日程石恰一次), 事件 4118/stages 408 如实钉,
  frontier 轨迹合法, run_g3 三门 ok=True(复用 run_g3 单源, 不复制判据;
  acceptance/robustness 双 17/17 + gate_imbalance 0/192 +
  viol_uniform_hmax 条件性在册);
- 五负控注入逐组红(每组断言"注入→对应门点名" + 基线"不注入不误报"):
  ①悬空石(删支撑边) → g3 gate_dag DAG_UNSUPPORTED 点名该石
  ②提前 CLEAR(本孔 CLEAR/DECENTER seq 对调) → sequencer check_sequence
    R4_CLEAR_ORDER 点名孔(events 生命周期 CLEAR_WITHOUT_START 同捕)
  ③跳孔落架(dstart 越过邻孔合龙) → g3 gate_dag DAG_R6_JUMP_DECENTER
    (sequencer check_frontier R6_JUMP_DECENTER 两实现互证)
  ④R3 单边领先(邻 bank 一石对调) → check_sequence R3_IMBALANCE 点名孔
  ⑤λ 档篡改(跨孔 WEDGE 时点对调) → g3 gate_dag DAG_R6_ADJ_DECENTERING;
    H 篡改可见性: 单孔 H 区间翻倍 → ④门 dH/ratio 读数严格变化
    (篡改不被静默吞掉, T7 探针③同法)
- 3d/out/event_ledger.json: 交付闸 validate_event_ledger(
  require_evidence=True)==[] + 幂等两连跑 cmp 逐字节相同 + 盘上件==重生成件
- 3d/out/g3_report.json: 三节齐 + 条件性字段(viol_uniform_hmax) +
  meta.generation(生成命令+HEAD 头注) + content_sha256_excl_timing 摘要
  自洽(报告含耗时, 文件字节两次生成必不同 —— 摘要钉"除计时外逐字段")
- 3d/out/narration_beats.md: 逐 stage→规则号(R0-R7; 卸架序=R4/R6 非 R5)
  →G0 编号→素材要点; 四叙事铁律在对应 beats 行显式标注; 全文过自身
  narration_lint 零红(lint 能守 beats)
- narration_lint: 禁词表(样筏/线道子/对合龙口/管主剑/收分铁/铁搭头/
  "乾隆旨仿")逐词必红带位置; 现代工程词入古人台词(「」『』“”引语)必红;
  叙述用现代词未挂 [现代分析] 必红; 无 G0 号且无标签断言行必红;
  合规样例零误伤; 禁词表被清空 → NO_WORDS_TABLE(空表不构绿, skip≠pass,
  qa_l2 I4 同纪律)。
blender-free; 真账 untracked 输入(ledger_full/excluded_ids)不在盘 → skip。
"""
import copy
import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))

import events as E
import ledger as L
import centering as CEN
import sequencer as SQ
import g3_check as G3
import narration as NR

_HERE = os.path.dirname(os.path.abspath(__file__))
_3D = os.path.abspath(os.path.join(_HERE, "..", "3d"))
_OUT = os.path.join(_3D, "out")
_LEDGER = os.path.join(_OUT, "ledger_full.json")
_EXCL = os.path.join(_OUT, "print", "excluded_ids.json")
_SEQOUT = os.path.join(_OUT, "sequence.json")
_EVOUT = os.path.join(_OUT, "event_ledger.json")
_G3OUT = os.path.join(_OUT, "g3_report.json")
_BEATSOUT = os.path.join(_OUT, "narration_beats.md")

# 实测钉(2026-10-07 真账, P2-T7b 波序; brief 预估 ~6000+/200-600 已被取代)
N_EVENTS = 4118
N_STAGES = 408


# ---------------------------------------------------------------------------
# 真账全链夹具(模块级一次; dm 扫描 ~25s 为大头)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def chain():
    if not (os.path.exists(_LEDGER) and os.path.exists(_EXCL)):
        pytest.skip("真账 untracked 输入(ledger_full/excluded_ids)不在盘上")
    led = L.load_ledger(_LEDGER)
    zones = sorted(set(s["id"].split(".")[0] for s in led["stones"]))
    centerings = [CEN.build_centering_for_arch(SQ._arch_idx(z)) for z in zones
                  if z.startswith("ARCH")]
    dm_detail = SQ._double_model_ratios(led)
    dm = set(dm_detail)
    res = SQ.build_sequence(led, centerings, dm_ids=dm)
    errs = SQ.check_sequence(res, led, centerings, dm_ids=dm)
    assert errs == [], errs[:8]
    led2 = SQ.apply_support_edges(led, res)
    with open(_EXCL, encoding="utf-8") as f:
        excl = set(json.load(f)["buckets"]["in_void"])
    # 三门单源: rbo_ids=[] 跳过 W1 全桶体素扫描(~26s, test_p2_g3_thrust
    # 真账侧已覆盖 W1; 本夹具只产三节与条件性字段)
    report = G3.run_g3(res["events"], led2, in_void=excl, rbo_ids=[])
    return {"led": led, "led2": led2, "res": res, "report": report,
            "excl": excl, "dm": dm, "dm_detail": dm_detail,
            "centerings": centerings, "zones": zones}


def _swap_seq(e1, e2):
    e1["seq"], e2["seq"] = e2["seq"], e1["seq"]


def _sorted_events(events):
    evs = copy.deepcopy(events)
    evs.sort(key=lambda e: e["seq"])
    return evs


# ---------------------------------------------------------------------------
# Step1a: 真账全链数字如实钉 + frontier 轨迹合法
# ---------------------------------------------------------------------------

def test_real_chain_full_order_and_counts(chain):
    res, led = chain["res"], chain["led"]
    meta = res["meta"]
    assert meta["n_stones_ledger"] == 5935
    assert meta["n_stones_in_void"] == 2004
    assert meta["n_dm_excluded"] == 29
    # 全序: 入日程石恰一次(5935 = 入日程 + in_void 幻影)
    hits = {}
    for e in res["events"]:
        sid = e.get("stone_id")
        if sid and e["etype"] in E.MASONRY_TYPES:
            hits[sid] = hits.get(sid, 0) + 1
    assert sum(hits.values()) == meta["n_stones"] == 3931
    assert all(n == 1 for n in hits.values())
    assert len(res["events"]) == N_EVENTS
    assert len(res["sequence"]) == N_STAGES
    seqs = [e["seq"] for e in res["events"]]
    assert seqs == list(range(1, N_EVENTS + 1))


def test_real_frontier_trace_legal(chain):
    res = chain["res"]
    zones = [z for z in chain["zones"] if z.startswith("ARCH")]
    assert len(zones) == 17
    assert SQ.check_frontier(res["events"], zones) == []
    trace = res["frontier_trace"]
    # 每孔状态严格前进(按孔分组回放), at_seq 单调
    rank = {s: i for i, s in enumerate(SQ.FRONTIER_STATES)}
    by_hole = {}
    for t in trace:
        by_hole.setdefault(t["hole"], []).append(t)
    assert len(by_hole) == 17
    for zh, ts in by_hole.items():
        rs = [rank[t["state"]] for t in ts]
        assert rs == sorted(rs) and len(set(rs)) == len(rs), (zh, ts)
    # 末态: 全部孔 FILLED(无肩背胞可填的孔到 CLEARED 为止)
    last = {zh: ts[-1]["state"] for zh, ts in by_hole.items()}
    assert all(s in ("CLEARED", "FILLED") for s in last.values()), last


# ---------------------------------------------------------------------------
# Step1b: 三门 ok=True(复用 run_g3 单源)
# ---------------------------------------------------------------------------

def test_three_gates_ok_via_run_g3(chain):
    rep = chain["report"]
    assert rep["gate_dag"]["ok"] is True
    assert rep["gate_dag"]["violations"] == []
    assert rep["gate_dag"]["n_snapshots"] == N_EVENTS
    stress = rep["gate_stress"]
    assert stress["ok"] is True
    holes = stress["holes"]
    assert len(holes) == 17
    assert sum(1 for h in holes.values() if h["acceptance"]["feasible"]) == 17
    assert sum(1 for h in holes.values() if h["robustness"]["feasible"]) == 17
    imb = rep["gate_imbalance"]
    assert imb["ok"] is True
    assert imb["n_evals"] == 192
    assert imb["violations"] == []
    # T7b 条件性字段: 一致 Hmax 读数下的违例组合数在册(非零即"换读数
    # 即翻红"的量化), 真账波序实测 =1
    assert imb["viol_uniform_hmax"] == 1


# ---------------------------------------------------------------------------
# Step1c: 五组负控(每组: 注入→对应门点名 + 基线不注入不误报)
# ---------------------------------------------------------------------------

def test_neg1_floating_stone_dag_unsupported(chain):
    """悬空石(删支撑边) → g3 gate_dag DAG_UNSUPPORTED 点名该石。"""
    led2, res, excl = chain["led2"], chain["res"], chain["excl"]
    tam = copy.deepcopy(led2)
    sid = next(s["id"] for s in tam["stones"]
               if G3.stone_role(s["id"]) == "RING"
               and s["id"].startswith("ARCH09."))
    next(s for s in tam["stones"] if s["id"] == sid)["support_edges"] = []
    viols, _ = G3.check_dag_all(res["events"], tam, in_void=excl)
    assert any(v.startswith("DAG_UNSUPPORTED") and sid in v for v in viols), \
        viols[:6]
    assert any(v.startswith("DAG_NO_ACTIVE_SUPPORT") and sid in v
               for v in viols)
    # 基线: 不注入不误报(同引擎同账零违例)
    base, _ = G3.check_dag_all(res["events"], led2, in_void=excl)
    assert base == []


def test_neg2_early_clear_r4_clear_order(chain):
    """提前 CLEAR(本孔 CLEAR 与 DECENTER seq 对调) → check_sequence
    R4_CLEAR_ORDER 点名孔(events 生命周期 CLEAR_WITHOUT_START 同捕)。"""
    led, res, dm, centerings = (chain["led"], chain["res"], chain["dm"],
                                chain["centerings"])
    tam = copy.deepcopy(res)
    zh = "ARCH05"
    d = next(e for e in tam["events"] if e["hole"] == zh
             and e["etype"] == "DECENTER_START")
    c = next(e for e in tam["events"] if e["hole"] == zh
             and e["etype"] == "CENTERING_CLEAR")
    _swap_seq(d, c)
    tam["events"] = sorted(tam["events"], key=lambda e: e["seq"])
    errs = SQ.check_sequence(tam, led, centerings, dm_ids=dm)
    assert any(m.startswith("R4_CLEAR_ORDER") and zh in m for m in errs), \
        sorted({m.split()[0] for m in errs})
    assert any("CLEAR_WITHOUT_START" in m for m in errs)      # 事件账同捕
    # 基线: 不注入不误报(夹具构造时已零错, 此处显式重证)
    assert SQ.check_sequence(res, led, centerings, dm_ids=dm) == []


def test_neg3_jump_decenter_r6_jump(chain):
    """跳孔落架(ARCH02 dstart 越过 ARCH01 合龙) → g3 gate_dag
    DAG_R6_JUMP_DECENTER; sequencer check_frontier 两实现互证。"""
    led2, res, excl = chain["led2"], chain["res"], chain["excl"]
    evs = copy.deepcopy(res["events"])
    d02 = next(e for e in evs if e["hole"] == "ARCH02"
               and e["etype"] == "DECENTER_START")
    c01 = next(e for e in evs if e["hole"] == "ARCH01"
               and e["etype"] == "CLOSE_RING")
    _swap_seq(d02, c01)
    evs = _sorted_events(evs)
    viols, _ = G3.check_dag_all(evs, led2, in_void=excl)
    assert any(v.startswith("DAG_R6_JUMP_DECENTER") and "ARCH02" in v
               and "ARCH01" in v for v in viols), viols[:6]
    zones = [z for z in chain["zones"] if z.startswith("ARCH")]
    fr = SQ.check_frontier(evs, zones)
    assert any(m.startswith("R6_JUMP_DECENTER") for m in fr), fr[:6]
    # 基线: 不注入不误报
    base, _ = G3.check_dag_all(res["events"], led2, in_void=excl)
    assert base == []


def test_neg4_r3_imbalance_one_side_lead(chain):
    """R3 单边领先(ARCH09 券石邻 bank 一石对调) → check_sequence
    R3_IMBALANCE 点名孔。"""
    led, res, dm, centerings = (chain["led"], chain["res"], chain["dm"],
                                chain["centerings"])
    tam = copy.deepcopy(res)
    prs = sorted((e for e in tam["events"] if e["hole"] == "ARCH09"
                  and e["etype"] == "PLACE_STONE"
                  and e["stone_id"].split(".")[2] == "RING"),
                 key=lambda e: e["seq"])
    assert len(prs) >= 4
    _swap_seq(prs[1], prs[2])          # 右 bank1 ↔ 左 bank2 → 前缀单边
    tam["events"] = sorted(tam["events"], key=lambda e: e["seq"])
    errs = SQ.check_sequence(tam, led, centerings, dm_ids=dm)
    assert any(m.startswith("R3_IMBALANCE") and "ARCH09" in m for m in errs), \
        sorted({m.split()[0] for m in errs})


def test_neg5a_lambda_rung_tamper_r6_adj(chain):
    """λ 档篡改(ARCH08 首档 WEDGE 与 ARCH09 末档 WEDGE 时点对调) →
    g3 gate_dag DAG_R6_ADJ_DECENTERING(相邻孔同落架失档 > 一档)。"""
    led2, res, excl = chain["led2"], chain["res"], chain["excl"]
    evs = copy.deepcopy(res["events"])
    wa = next(e for e in evs if e["hole"] == "ARCH08"
              and e["etype"] == "WEDGE_RELEASE" and e["load_lambda"] == 0.25)
    wb = next(e for e in evs if e["hole"] == "ARCH09"
              and e["etype"] == "WEDGE_RELEASE" and e["load_lambda"] == 1.0)
    _swap_seq(wa, wb)                  # λ 值随事件走, 只篡改时点
    evs = _sorted_events(evs)
    viols, _ = G3.check_dag_all(evs, led2, in_void=excl)
    assert any(v.startswith("DAG_R6_ADJ_DECENTERING") for v in viols), \
        viols[:6]
    # 基线: 不注入不误报
    base, _ = G3.check_dag_all(res["events"], led2, in_void=excl)
    assert base == []


def test_neg5b_h_env_tamper_visible_in_readings(chain):
    """H 篡改可见性: 单孔(ARCH02)H 区间翻倍直喂 imbalance_gate →
    其两侧墩(P intoxic01/02) dH/ratio 读数严格变化 —— ④门消费 H,
    篡改可观测不被静默吞(T7 探针③同法); 真 H 基线 0/192 不变。"""
    led2, res, excl, rep = (chain["led2"], chain["res"], chain["excl"],
                            chain["report"])
    H_env = {zh: h["acceptance"]["H"]
             for zh, h in rep["gate_stress"]["holes"].items()
             if h["acceptance"].get("feasible")}
    base = G3.imbalance_gate(res["events"], H_env, ledger=led2,
                             in_void=excl)
    assert base["ok"] is True and base["n_evals"] == 192
    H2 = dict(H_env)
    lo, hi = H2["ARCH02"]
    H2["ARCH02"] = (2.0 * lo, 2.0 * hi)
    tam = G3.imbalance_gate(res["events"], H2, ledger=led2, in_void=excl)
    changed = 0
    for b, t in zip(base["events"], tam["events"]):
        assert (b["pier_id"], b["seq"]) == (t["pier_id"], t["seq"])
        if b["dH"] != t["dH"]:
            changed += 1
            if t["pier_id"] in ("PIER01", "PIER02"):
                assert t["dH"] != b["dH"] and t["ratio"] != b["ratio"]
    assert changed > 0, "H 区间翻倍在④门读数中不可见(篡改被静默吞)"


# ---------------------------------------------------------------------------
# Step1d: 出口工件 event_ledger.json / g3_report.json
# ---------------------------------------------------------------------------

def test_event_ledger_artifact_valid_and_idempotent(chain, tmp_path):
    """3d/out/event_ledger.json: 交付闸 require_evidence==[] + 幂等两连
    跑 cmp 逐字节相同 + 盘上件==重生成件。"""
    res, led2, excl = chain["res"], chain["led2"], chain["excl"]
    assert os.path.exists(_EVOUT), \
        "3d/out/event_ledger.json 不在盘上 —— 先跑 python3 3d/sequencer.py"
    sched_ids = [s["id"] for s in led2["stones"]
                 if s["id"] not in chain["excl"]]
    cen_ids = [c["id"] for c in chain["centerings"]]
    # 交付闸(与 sequencer.main 同一校验单源)
    doc = SQ.event_ledger_doc(res)
    assert E.validate_event_ledger(doc, cen_ids, sched_ids,
                                   require_evidence=True) == []
    with open(_EVOUT, "rb") as f:
        disk = f.read()
    # 幂等两连跑 cmp(独立两次序列化, 逐字节相同)
    b1 = SQ.dump_event_ledger(doc)
    b2 = SQ.dump_event_ledger(SQ.event_ledger_doc(res))
    assert b1 == b2
    assert disk == b1, "盘上 event_ledger.json != 重生成字节(重出后再测)"
    with open(os.path.join(str(tmp_path), "ev1.json"), "wb") as f:
        f.write(b1)
    assert json.loads(disk)["schema"] == SQ.EVENT_LEDGER_SCHEMA
    assert json.loads(disk)["meta"]["n_events"] == N_EVENTS


def test_g3_report_artifact_three_sections_and_digest():
    """3d/out/g3_report.json: 三节齐 + 条件性字段 + meta.generation
    (生成命令+HEAD 头注) + content_sha256_excl_timing 摘要自洽。"""
    assert os.path.exists(_G3OUT), \
        "3d/out/g3_report.json 不在盘上 —— 先跑 python3 3d/g3_check.py"
    with open(_G3OUT, encoding="utf-8") as f:
        rep = json.load(f)
    for sec in ("gate_dag", "gate_stress", "gate_imbalance"):
        assert sec in rep and rep[sec]["ok"] is True, sec
    assert rep["gate_imbalance"]["viol_uniform_hmax"] == 1
    assert rep["meta"]["n_events"] == N_EVENTS
    gen = rep["meta"]["generation"]
    assert "g3_check.py" in gen["command"]
    assert len(gen["git_head"]) == 40 and gen["git_head"] != "unknown", gen
    # 摘要自洽: 除 elapsed_s 计时与 generation 块外逐字段可重算
    body = G3._strip_elapsed(rep)
    body["meta"].pop("generation", None)
    blob = json.dumps(body, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    assert digest == gen["content_sha256_excl_timing"]


# ---------------------------------------------------------------------------
# Step2: narration beats + 禁词 lint
# ---------------------------------------------------------------------------

def test_narration_beats_artifact_matches_generator_and_selfclean(chain):
    """3d/out/narration_beats.md: 盘上件==重生成件(纯函数, 读
    sequence.json+g3_report.json 计数字段, 与耗时无关); 全文过自身
    narration_lint 零红; 四叙事铁律在对应 beats 行显式标注。"""
    with open(_SEQOUT, encoding="utf-8") as f:
        seqdoc = json.load(f)
    with open(_G3OUT, encoding="utf-8") as f:
        rep = json.load(f)
    text = NR.build_beats_text(seqdoc, rep)
    assert os.path.exists(_BEATSOUT), \
        "3d/out/narration_beats.md 不在盘上 —— 先跑 python3 3d/narration.py"
    with open(_BEATSOUT, encoding="utf-8") as f:
        disk = f.read()
    assert disk == text, "盘上 narration_beats.md != 重生成文本"
    assert NR.narration_lint(text) == [], \
        "beats 文本未过自身 lint(铁律/标注行不可裸奔)"
    lines = text.splitlines()
    # 四叙事铁律显式标注在对应行: ①合龙行 ②锁固肩行 ③④落架波行
    close = [ln for ln in lines if ".CLOSE_RING" in ln]
    shoulder = [ln for ln in lines if ".SHOULDER." in ln]
    dstart = [ln for ln in lines if "DECENTER.DSTART.WAVE" in ln]
    wedge = [ln for ln in lines if "DECENTER.WEDGE." in ln]
    assert close and all("铁律①" in ln for ln in close), close[:2]
    assert shoulder and all("铁律②" in ln for ln in shoulder)
    assert dstart and all("铁律③" in ln for ln in dstart)
    assert wedge and all("铁律④" in ln for ln in wedge)
    # 规则号勘误钉: 卸架波行规则=R4/R6, 不是 R5
    assert all("R4/R6" in ln and "R5" not in ln.split("规则=")[1].split("|")[0]
               for ln in dstart + wedge)


def test_lint_banned_words_red_with_position():
    """负控①: 禁词表逐词必红, 点名词+位置; 无一漏网。"""
    assert len(NR.BANNED_WORDS) >= 7
    for w in NR.BANNED_WORDS:
        text = "第 3 行提到 %s 这一说法。\n末行" % w
        finds = NR.narration_lint(text)
        hits = [f for f in finds if f.kind == "BANNED_WORD" and f.word == w]
        assert len(hits) == 1, (w, finds)
        assert hits[0].line == 1 and hits[0].col == text.find(w) + 1


def test_lint_compliant_sample_clean():
    """负控②: 合规样例(挂 G0 号/标签的正常句)零误伤。"""
    text = "\n".join([
        "# 旁白样稿(合规样例)",
        "合龙前拱圈不能自持, 撤侧墙与石灰土后五边折线自行坍塌(B14)。",
        "券脸石名目见则例石作制度(C:A2); 錾道密度有验收量化(C:A4)。",
        "始建 1750, 乾隆十五年三月丙辰命名谕旨(A1)。",
        "θ 镜像配对两侧交替, 前缀平衡度≤ε [现代分析][工程参数·敏感性]。",
        "卸架序无史料锚, 本门图式下的临界定非不可行证明 [工程推断·非史料]。",
        "生成命令: python3 3d/narration.py",
        "数据源: 3d/out/sequence.json + 3d/out/g3_report.json",
        "“修蝀凌波”匾额为乾隆御笔, 官名「长桥」同源, 书证见 G0 汇编 A 线"
        " [文献记载]。",
    ])
    assert NR.narration_lint(text) == []


def test_lint_no_words_table_not_green(monkeypatch):
    """禁词表被清空 → NO_WORDS_TABLE(空表不构绿; skip≠pass, qa_l2 I4)。"""
    monkeypatch.setattr(NR, "BANNED_WORDS", ())
    finds = NR.narration_lint("任意行(C:A2)。")
    assert any(f.kind == "NO_WORDS_TABLE" for f in finds), finds
    assert not NR.narration_ok(finds)


def test_lint_modern_term_rules():
    """现代工程词: 入古人台词(引语)必红; 叙述未挂 [现代分析] 必红;
    挂标签放行; [工程推断] 不豁免现代力学词。"""
    q = "匠人云：「此段压力线偏北三分，不妨事。」(C:B14)。"
    finds = NR.narration_lint(q)
    assert any(f.kind == "MODERN_TERM_IN_QUOTE" and f.word == "压力线"
               for f in finds), finds
    # 即使整行挂了标签, 引语内的现代词仍红(古人不说现代力学词, B1)
    finds2 = NR.narration_lint("匠人云：「倾覆裕度不足。」 [现代分析]")
    assert any(f.kind == "MODERN_TERM_IN_QUOTE" for f in finds2)
    u = "拱圈内力可用中三分校核。"
    finds3 = NR.narration_lint(u)
    assert any(f.kind == "MODERN_TERM_UNTAGGED" and f.word == "中三分"
               for f in finds3), finds3
    ok = "拱圈内力可用中三分校核 [现代分析]。"
    assert NR.narration_lint(ok) == []
    eng = "此为结构协同的工程推断, 涉压力线读数 [工程推断]。"
    assert any(f.kind == "MODERN_TERM_UNTAGGED" for f in NR.narration_lint(eng))


def test_lint_unsourced_claim_red():
    """无 G0 号且无标签的断言行必红; 结构行(标题/代码栅栏/元数据)豁免。"""
    bad = "龙门石最后安砌, 全桥合龙即告功成。"
    finds = NR.narration_lint(bad)
    assert any(f.kind == "UNSOURCED_CLAIM" and f.line == 1 for f in finds)
    fixed = "龙门石最后安砌(C:A2 龙门石名目)。"
    assert NR.narration_lint(fixed) == []
    doc = "\n".join([
        "# 标题行豁免",
        "```",
        "代码栅栏内豁免: 样筏也不在此核",
        "```",
        "生成命令: python3 3d/narration.py",
        "缺口行必红(见上断言)。",
    ])
    finds2 = NR.narration_lint(doc)
    kinds = [f.kind for f in finds2]
    assert kinds == ["UNSOURCED_CLAIM"] and finds2[0].line == 6, finds2


def test_lint_word_table_pinned():
    """禁词表/现代词表非空且含 brief 点名词(防空表/漏词回归)。"""
    for w in ("样筏", "线道子", "对合龙口", "管主剑", "收分铁", "铁搭头",
              "乾隆旨仿"):
        assert w in NR.BANNED_WORDS, w
    for w in ("压力线", "倾覆裕度", "中三分"):
        assert w in NR.MODERN_TERMS, w
