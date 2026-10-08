# P4-T5: 进度账状态机(print_status) + M5(a) 底座规格(BASE_SPEC)单测。
# 判据(plan T5 Step1 + 任务书): ①全合法迁移表驱动遍历(pending→printed→
# checked→glued 主链 + printed→redo→pending 重打改派); ②非法迁移 raise
# (pending→glued 等, 且失败不落盘); ③幂等: init 两连跑逐字节同(真 manifest
# 1047 单元)+advance 同态两跑逐字节同; ④query --phase 过滤正确; ⑤BASE_SPEC
# 规格数字与盘上工件重算一致(manifest/ledger_full+facts 单源, 手写数字与
# 推导差>1mm 必红 —— 禁手编数字的钉)。
# blender-free: bbox/券环走 p1a_slice.world_mesh 纯逻辑路径(与 T4 段总图同源),
# PIER_X 走 geom_math facts 累加式(桥长闭合硬门在 import 时自证)。
import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "3d"))

import geom_math as GM  # noqa: E402  (facts 单源: PIER_X 累加式)
import p1a_slice as PS  # noqa: E402
import print_status as PST  # noqa: E402
import section_pack as SEC  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO, "3d", "out", "print", "section5", "manifest.json")
BASE_SPEC = os.path.join(REPO, "3d", "out", "print", "section5", "BASE_SPEC.md")
SCALE = 0.02                     # manifest.meta.scale (1:50)
UNIT_N = 1047                    # manifest.conservation.exported 实测
BATCH_N = 31                     # manifest.conservation.batches 实测


# ---------------------------------------------------------------- 工具

def _syn_manifest():
    """小合成账: 覆盖批/材质/孔前缀, 状态机测不依赖真账规模。"""
    return {
        "meta": {"scale": SCALE},
        "stones": [
            {"id": "ARCH09.EAST.RING.C00.B00", "batch": 0, "material": "qingshi"},
            {"id": "ARCH09.EAST.RING.C00.B01", "batch": 0, "material": "qingshi"},
            {"id": "ARCH09.WEST.IMPOST.C01.B00", "batch": 1, "material": "qingshi"},
            {"id": "ARCH09.WEST.BACK.C02.B00", "batch": 2, "material": "maoshi"},
        ],
    }


def _fresh_status(_tmp=None):
    st = PST.init_status(_syn_manifest(), "synthetic-for-test")
    return st


def _set_phase(status, unit, phase):
    """测试脚手架: 直改相位构造任意中间态(绕过迁移表, 只服务判据②③)。"""
    status["units"][unit]["phase"] = phase


# ---------------------------------------------------------------- ①合法迁移

def test_status_legal_transitions():
    """全合法迁移表驱动遍历: TRANSITIONS 每条 (from,to) 逐一走通。"""
    for frm, tos in PST.TRANSITIONS.items():
        for to in tos:
            st = _fresh_status(None)
            uid = sorted(st["units"])[0]
            _set_phase(st, uid, frm)
            batch_before = st["units"][uid]["batch"]
            PST.advance_unit(st, uid, to)
            assert st["units"][uid]["phase"] == to, (frm, to)
            h = st["units"][uid]["history"]
            assert h[-1] == {"op": "advance", "from": frm, "to": to}
            assert st["units"][uid]["batch"] == batch_before
    # 主链一贯到底 + 重打改派支链(redo→pending 可携 batch 改派)
    st = _fresh_status(None)
    uid = sorted(st["units"])[0]
    for to in ("printed", "checked", "glued"):
        PST.advance_unit(st, uid, to)
    assert st["units"][uid]["phase"] == "glued"
    st2 = _fresh_status(None)
    uid2 = sorted(st2["units"])[0]
    PST.advance_unit(st2, uid2, "printed")
    PST.advance_unit(st2, uid2, "redo")
    assert st2["units"][uid2]["phase"] == "redo"
    PST.advance_unit(st2, uid2, "pending", batch=99)
    assert st2["units"][uid2]["phase"] == "pending"
    assert st2["units"][uid2]["batch"] == 99, "重打改派: redo→pending 应可改派批次"
    assert any(e.get("op") == "reassign" and e.get("batch") == 99
               for e in st2["units"][uid2]["history"])


# ---------------------------------------------------------------- ②非法迁移

def test_status_illegal_raise():
    """非法迁移 raise (IllegalTransition), 且失败 advance 不改动文件状态。"""
    bad = [("pending", "glued"), ("pending", "checked"), ("pending", "pending"),
           ("printed", "printed"), ("printed", "pending"), ("checked", "printed"),
           ("checked", "redo"), ("glued", "pending"), ("glued", "printed"),
           ("redo", "printed"), ("redo", "glued"), ("redo", "checked")]
    for frm, to in bad:
        st = _fresh_status(None)
        uid = sorted(st["units"])[0]
        _set_phase(st, uid, frm)
        with pytest.raises(PST.IllegalTransition):
            PST.advance_unit(st, uid, to)
        assert st["units"][uid]["phase"] == frm, "失败迁移不得改相位"
    # 未知阶段 / 未知单元 / 改派窗口错用
    st = _fresh_status(None)
    uid = sorted(st["units"])[0]
    with pytest.raises(ValueError):
        PST.advance_unit(st, uid, "shipped")
    with pytest.raises(ValueError):
        PST.advance_unit(st, "ARCH09.NOPE.B99", "printed")
    with pytest.raises(ValueError):
        PST.advance_unit(st, uid, "printed", batch=7)  # 改派仅限 redo→pending
    # schema 头校验
    with pytest.raises(ValueError):
        PST.validate_status({"schema": 999, "kind": "print_status", "units": {}})
    with pytest.raises(ValueError):
        PST.validate_status({"schema": 1, "kind": "other", "units": {}})


# ---------------------------------------------------------------- ③幂等落盘

def test_status_idempotent_init(tmp_path):
    """真 manifest init 两连跑逐字节同; advance 同态两路逐字节同。"""
    out1 = str(tmp_path / "s1.json")
    out2 = str(tmp_path / "s2.json")
    for out in (out1, out2):     # 两连跑(两份独立落盘, 等价于 --force 重跑)
        st = PST.init_status(json.load(open(MANIFEST)), MANIFEST)
        PST.save_status(st, out)
    b1 = open(out1, "rb").read()
    b2 = open(out2, "rb").read()
    assert b1 == b2, "init 两连跑必须逐字节同(幂等落盘)"
    doc = json.loads(b1)
    assert doc["schema"] == PST.SCHEMA_VERSION and doc["kind"] == PST.KIND
    assert len(doc["units"]) == UNIT_N
    assert all(u["phase"] == "pending" for u in doc["units"].values())
    batches = {u["batch"] for u in doc["units"].values()}
    assert max(batches) == BATCH_N - 1 and min(batches) == 0
    # advance: 同一初态两路各走两步 → 逐字节同(无时间戳路径)
    a1 = str(tmp_path / "a1.json")
    a2 = str(tmp_path / "a2.json")
    uid = sorted(json.loads(b1)["units"])[0]   # 真账单元(不猜 id 形态)
    for out in (a1, a2):
        st = json.loads(b1)
        PST.advance_unit(st, uid, "printed")
        PST.advance_unit(st, uid, "checked")
        PST.save_status(st, out)
    assert open(a1, "rb").read() == open(a2, "rb").read()


# ---------------------------------------------------------------- ④query

def test_query_filter():
    """query --phase 只返回该相位单元(排序确定), counts 全相位居零。"""
    st = PST.init_status(_syn_manifest(), "synthetic-for-test")
    PST.advance_unit(st, "ARCH09.EAST.RING.C00.B00", "printed")
    PST.advance_unit(st, "ARCH09.EAST.RING.C00.B01", "printed")
    PST.advance_unit(st, "ARCH09.EAST.RING.C00.B01", "checked")
    PST.advance_unit(st, "ARCH09.WEST.IMPOST.C01.B00", "printed")
    PST.advance_unit(st, "ARCH09.WEST.IMPOST.C01.B00", "checked")
    PST.advance_unit(st, "ARCH09.WEST.IMPOST.C01.B00", "glued")
    q = PST.query(st, phase="checked")
    assert q["units"] == ["ARCH09.EAST.RING.C00.B01"]
    q = PST.query(st)
    assert q["counts"] == {"pending": 1, "printed": 1, "checked": 1,
                           "glued": 1, "redo": 0}
    assert q["total"] == 4
    assert q["units"] == sorted(q["units"])
    assert PST.query(st, phase="redo")["units"] == []
    with pytest.raises(ValueError):
        PST.query(st, phase="nope")


# ---------------------------------------------------------------- CLI

def test_cli_roundtrip(tmp_path, capsys):
    """三命令 CLI 接线: init/advance/query 退出码与输出; 非法迁移 exit≠0。"""
    out = str(tmp_path / "cli.json")
    rc = PST.main(["init", "--manifest", MANIFEST, "--out", out])
    assert rc == 0
    uid = sorted(json.load(open(MANIFEST))["stones"],
                 key=lambda s: s["id"])[0]["id"]
    capsys.readouterr()
    rc = PST.main(["advance", "--status", out, "--unit", uid, "--to", "printed"])
    assert rc == 0
    capsys.readouterr()          # 冲掉 init/advance 行, 只留 query 的 JSON
    rc = PST.main(["query", "--status", out, "--phase", "printed"])
    assert rc == 0
    q = json.loads(capsys.readouterr().out)
    assert q["units"] == [uid]
    before = open(out, "rb").read()
    rc = PST.main(["advance", "--status", out, "--unit", uid, "--to", "glued"])
    assert rc != 0, "CLI 非法迁移必须非零退出"
    assert open(out, "rb").read() == before, "CLI 失败迁移不得落盘"


# ---------------------------------------------------------------- ⑤BASE_SPEC

def _read_base_spec():
    assert os.path.exists(BASE_SPEC), "缺 BASE_SPEC.md: %s" % BASE_SPEC
    return open(BASE_SPEC, encoding="utf-8").read()


def _section_envelope():
    """独立重算: 段世界 bbox + 每孔 RING x 区间 + 状态计数(裁片按裁后实体)。"""
    led = SEC.load_full_ledger()
    statuses, scope_ids, _ = SEC.build_print_view(led)
    sub5 = SEC.slice_section(led, scope_ids, SEC.SEGMENT)
    xs, ys, zs = [], [], []
    ring = {}
    from collections import Counter
    cnt = Counter()
    for s in sub5["stones"]:
        cnt[statuses[s["id"]][0]] += 1
        verts, _ = PS.world_mesh(s, statuses)
        xs += [v[0] for v in verts]
        ys += [v[1] for v in verts]
        zs += [v[2] for v in verts]
        if s["role_struct"] == "RING":
            r = ring.setdefault(s["id"].split(".")[0],
                                [float("inf"), float("-inf")])
            for v in verts:
                r[0] = min(r[0], v[0])
                r[1] = max(r[1], v[0])
    return {
        "n": len(sub5["stones"]),
        "bbox": (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)),
        "ring": ring,
        "statuses": cnt,
    }


def test_base_spec_numbers_from_manifest():
    """规格数字与盘上工件重算一致: bbox/PIER_X/体积/单元数全链钉。"""
    text = _read_base_spec()
    man = json.load(open(MANIFEST))
    env = _section_envelope()
    x0, x1, y0, y1, z0, z1 = env["bbox"]
    mm = lambda m_val: m_val * SCALE * 1000.0        # 1:50: m → mm

    # -- §1 段包络表: 三行 (min..max | 尺寸 m | 尺寸 mm)
    for name, lo, hi in (("段长 L", x0, x1), ("段宽 W", y0, y1),
                         ("段高 H", z0, z1)):
        row = re.search(r"\|\s*%s\s*\|\s*(-?[\d.]+)\s*\.\.\s*(-?[\d.]+)"
                        r"\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|" % name, text)
        assert row, "BASE_SPEC 缺包络行: %s" % name
        d_lo, d_hi, d_len_m, d_len_mm = (float(g) for g in row.groups())
        assert abs(d_lo - lo) < 1e-5 and abs(d_hi - hi) < 1e-5, name
        assert abs(d_len_m - (hi - lo)) < 1e-4, name
        assert abs(d_len_mm - mm(hi - lo)) < 1.0, \
            "%s: 手写 mm 与推导差 >1mm (禁手编数字)" % name
    # 状态计数注记
    for k, v in env["statuses"].items():
        assert re.search(r"%s=%d\b" % (k, v), text), "状态计数 %s=%d 未落文档" % (k, v)

    # -- §2 底座长宽高 = bbox + 边距 (推导式自洽 + 数字与重算一致)
    m_l = re.search(r"L_底座\s*=\s*([\d.]+)\s*\+\s*2\s*×\s*([\d.]+)"
                    r"\s*=\s*\*\*([\d.]+)\s*mm\*\*", text)
    m_w = re.search(r"W_底座\s*=\s*([\d.]+)\s*\+\s*2\s*×\s*([\d.]+)"
                    r"\s*=\s*\*\*([\d.]+)\s*mm\*\*", text)
    assert m_l and m_w, "BASE_SPEC 缺底座推导式"
    l_seg, l_mar, l_base = (float(g) for g in m_l.groups())
    w_seg, w_mar, w_base = (float(g) for g in m_w.groups())
    assert abs(l_seg - mm(x1 - x0)) < 1.0 and abs(w_seg - mm(y1 - y0)) < 1.0
    assert abs(l_base - (l_seg + 2 * l_mar)) < 0.02, "推导式算术不自洽 (L)"
    assert abs(w_base - (w_seg + 2 * w_mar)) < 0.02, "推导式算术不自洽 (W)"
    m_h = re.search(r"H_底座\s*=\s*\*\*([\d.]+)\s*mm\*\*", text)
    assert m_h, "BASE_SPEC 缺底座厚"
    m_datum = re.search(r"x_datum\s*=\s*x0\s*-\s*1\.2\s*=\s*(-?[\d.]+)\s*m", text)
    assert m_datum and abs(float(m_datum.group(1)) - (x0 - 1.2)) < 1e-5

    # -- §3 五孔定位槽位表: 孔心 x = geom_math facts 单源, 券环区间 = 重算
    for i in range(6, 11):
        zone = "ARCH%02d" % (i + 1)
        c_world = GM.arch_center_x(i)
        p_w, p_e = GM.PIER_X[i], GM.PIER_X[i + 1]
        row = re.search(
            r"\|\s*%s\s*\|\s*P%d=(-?[\d.]+),\s*P%d=(-?[\d.]+)\s*"
            r"\|\s*(-?[\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\.\.\s*([\d.]+)\s*\|"
            % (zone, i, i + 1), text)
        assert row, "BASE_SPEC 缺五孔行: %s" % zone
        d_pw, d_pe, d_c, d_cmm, d_r0, d_r1 = (float(g) for g in row.groups())
        assert abs(d_pw - p_w) < 5e-5 and abs(d_pe - p_e) < 5e-5, zone
        assert abs(d_c - c_world) < 5e-5, "%s 孔心 world x" % zone
        datum = x0 - 1.2
        assert abs(d_cmm - mm(c_world - datum)) < 1.0, \
            "%s 孔心 mm 与重算差 >1mm (禁手编数字)" % zone
        r0, r1 = env["ring"][zone]
        assert abs(d_r0 - mm(r0 - datum)) < 1.0, "%s 券环西缘 mm" % zone
        assert abs(d_r1 - mm(r1 - datum)) < 1.0, "%s 券环东缘 mm" % zone
    # 端切面墩位 (M5(a)): P6/P11 与段端外扩量(取幅值: 包络端在墩心外侧)
    assert abs((x0 - GM.PIER_X[6]) - (-1.179501)) < 5e-5  # 事实自检(非文档钉)
    m_ext = re.search(r"外扩\s*(-?[\d.]+)\s*m", text)
    assert m_ext and abs(abs(float(m_ext.group(1))) - abs(x0 - GM.PIER_X[6])) < 5e-4

    # -- §5 承重粗估: 体积×密度上界, 体积须回 manifest
    vol = man["conservation"]["volume_cm3_by_material"]
    tot = man["conservation"]["volume_cm3_total"]
    RHO = 1.25                                        # [估算] 树脂上界(文档同值)
    for mat in ("qingshi", "maoshi"):
        row = re.search(r"\|\s*%s\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)"
                        r"\s*\|\s*([\d.]+)\s*\|" % mat, text)
        assert row, "BASE_SPEC 缺承重行: %s" % mat
        n, v, rho, mass = (int(row.group(1)),) + tuple(
            float(row.group(i)) for i in (2, 3, 4))
        assert n == man["materials"][mat], mat
        assert abs(v - vol[mat]) < 0.01, "%s 体积须=manifest" % mat
        assert rho == RHO
        assert abs(mass - v * rho) < 0.02, "%s 质量=体积×密度上界" % mat
    m_tot = re.search(r"\|\s*合计\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)"
                      r"\s*\|\s*([\d.]+)\s*\|", text)
    assert m_tot
    assert int(m_tot.group(1)) == UNIT_N
    assert abs(float(m_tot.group(2)) - tot) < 0.01
    assert abs(float(m_tot.group(4)) - tot * RHO) < 0.02

    # -- 口径标记与计数钉
    for tag in ("[设计选择]", "[估算]", "M5(a)", "不打印",
                "1047", "31 批", "601", "446"):
        assert tag in text, "BASE_SPEC 缺口径标记/计数: %s" % tag
    # 端槽规格(设计定案常数, 防漂移钉): 宽18/深5/距端24 (=段总图 0.9m×20 同参)
    assert re.search(r"槽宽\s*18\.0\s*mm", text)
    assert re.search(r"槽深\s*5\.0\s*mm", text)
    assert re.search(r"距底座端\s*24\.0\s*mm", text)
    # 单元数/批数与 manifest 一致
    assert man["conservation"]["exported"] == UNIT_N
    assert man["conservation"]["batches"] == BATCH_N
    assert abs(mm(x1 - x0) + 2 * 24.0 - 1105.72) < 0.02   # 文档头数自检
