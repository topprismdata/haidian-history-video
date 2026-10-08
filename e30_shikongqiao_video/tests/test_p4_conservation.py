# -*- coding: utf-8 -*-
"""P4-T3 三方守恒双实现 validator 测试(计划 Task 3 Step 1, 先红).

四支钉 + import 隔离三层探针(P3-T3/P2-T5 同款纪律):
  1. 石级三方恒等(逐 id 集合): section_kept ⊎ deferred ⊎ excluded ==
     ledger 5935, 两两不交; 分段原料数 2747/3188 同钉(稳定不变量);
  2. 单元级口径钉: 1 单元 = 1 账面石(print_scope 存活, 无合并),
     1123+990=2113 == 重算 print_units == 盘上 g2_report counts;
     1974 vs 2113 口径考古结论钉进 pack_verify docstring 与本测
     (1974=P1-T8 原始轮 04f2e54, 排除 3961; T8b 体量宇宙处置后
     ring_band 305→182/thin_merge 84→68 回打印域 139 石 → 2113/排除
     3822; P1 收官 T9 即 2113。1974 不作判据)。
  3. 负控: deferred 抽一 id 塞 section → 红(偷挪); 删一 unit 三处都不
     出现 → 红(丢失)。
  4. import 隔离: pack_verify 不 import section_pack/export_print 装箱码
     (源码层/subprocess 层/探针阴性对照三层)。
只读 3d/out 真账工件(ledger_full 为 G2 门 blender 产物, 缺失即响亮,
与 test_p4_section 同约定); blender-free; Python 3.9.6。
"""
import copy
import inspect
import json
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_3D = os.path.join(REPO, "3d")
if _3D not in sys.path:
    sys.path.insert(0, _3D)

import pack_verify as PV  # noqa: E402

PRINT_DIR = os.path.join(_3D, "out", "print")
MANIFEST_PATH = os.path.join(PRINT_DIR, "section5", "manifest.json")
DEFERRED_PATH = os.path.join(PRINT_DIR, "deferred_holes.json")
EXCLUDED_PATH = os.path.join(PRINT_DIR, "excluded_ids.json")
G2REPORT_PATH = os.path.join(PRINT_DIR, "g2_report.json")
LEDGER_PATH = os.path.join(_3D, "out", "ledger_full.json")

# 真账实测钉(现行 G2/T8b+ 口径, 2026-10-07 P1 收官态)
UNIVERSE = 5935          # 全桥账面石
SEC_UNITS = 1047         # 段(ARCH07-11)打印单元 == 段 manifest.stones(1123→1047 拱线族返工清债)
SEC_RAW = 2747           # 段账面石(含排除)
DEF_UNITS = 990          # 留续 12 孔打印单元
DEF_RAW = 3188           # 留续账面石(含排除)
# [拱线族返工 2026-10-08] 3822→3898 新实测(excluded_ids.json 重出直读): in_void 2028(+24 全在 b>a 三孔)/void_cut 1580(+12)/ring_band 222(+40)/thin 68(不变)
EXCLUDED = 3898          # 排除石(in_void 2028/void_cut 1580/ring_band 222/thin 68)
UNITS_CURRENT = 2037     # 现行全桥打印单元 = 1047+990(2113→2037 拱线族返工清债)
# P1-T8 原始轮历史口径(04f2e54, 已被 T8b 更替, 只作考古对账)
UNITS_T8_ORIG = 1974
UNITS_T8B = 2113                  # T8b 口径(拱线族返工前一代, 考古对账)
EXCL_T8_ORIG = 3961
EXCL_T8B = 3822                    # T8b 排除总数(同上考古)


@pytest.fixture(scope="session")
def conservation_pack():
    """真账四方 + 独立重算(~95s 一次性) + verify_pack 报告。"""
    with open(LEDGER_PATH) as fh:
        led = json.load(fh)
    with open(MANIFEST_PATH) as fh:
        sec = json.load(fh)
    with open(DEFERRED_PATH) as fh:
        df = json.load(fh)
    with open(EXCLUDED_PATH) as fh:
        ex = json.load(fh)
    view = PV.recompute_view(led)
    rep = PV.verify_pack(sec, df, ex, led, recomputed=view)
    return led, sec, df, ex, view, rep


# ── 1. 石级三方恒等(逐 id 集合等式, 稳定不变量) ──

def test_stone_level_three_way_exact(conservation_pack):
    led, sec, df, ex, view, rep = conservation_pack
    universe = {s["id"] for s in led["stones"]}
    sec_ids = {s["id"] for s in sec["stones"]}
    df_ids = set(df["unit_ids"])
    ex_ids = {i for ids in ex["buckets"].values() for i in ids}
    # 逐 id 集合等式: 两两不交 + 并集==全账
    assert not (sec_ids & df_ids), "段∩留续非空"
    assert not (sec_ids & ex_ids), "段∩排除非空"
    assert not (df_ids & ex_ids), "留续∩排除非空"
    assert sec_ids | df_ids | ex_ids == universe, "三方并 != 全账"
    assert len(universe) == UNIVERSE
    assert len(sec_ids) == SEC_UNITS and len(df_ids) == DEF_UNITS
    assert len(ex_ids) == EXCLUDED
    # 分段原料守恒(含排除的石级账, 按同口径分段核对)
    zone = lambda i: i.split(".")[0]                    # noqa: E731
    sec_zone = {zone(i) for i in sec_ids}
    raw_sec = {s["id"] for s in led["stones"] if zone(s["id"]) in sec_zone}
    raw_def = {s["id"] for s in led["stones"]
               if zone(s["id"]) not in sec_zone}
    assert len(raw_sec) == SEC_RAW and len(raw_def) == DEF_RAW
    assert len(raw_def) + len(raw_sec) == UNIVERSE
    assert sec_ids <= raw_sec and df_ids <= raw_def
    # 分段内未出件石恰为排除账成员(逐 id)
    assert raw_sec - sec_ids <= ex_ids
    assert raw_def - df_ids <= ex_ids
    # validator 主裁定: ok 且石级三方数字如实并列
    assert rep["ok"] is True, rep["violations"]
    assert rep["三方"]["section"] == SEC_UNITS
    assert rep["三方"]["deferred"] == DEF_UNITS
    assert rep["三方"]["excluded"] == EXCLUDED
    assert rep["total"] == UNIVERSE
    # 独立重算路径与盘上两清单互证(双实现同口径)
    assert view["scope"] == sec_ids | df_ids
    for b, ids in ex["buckets"].items():
        assert view["buckets"].get(b, set()) == set(ids), b


# ── 2. 单元级口径钉(考古结论入测) ──

def test_unit_level_caliber_documented(conservation_pack):
    led, sec, df, ex, view, rep = conservation_pack
    # 单元定义: 1 单元 = 1 账面石过 print_scope, 无合并 →
    # 重算 scope 数 == 段+留续单元和; 石=单元 1:1
    assert len(view["scope"]) == SEC_UNITS + DEF_UNITS == UNITS_CURRENT
    assert len(view["scope"]) + sum(len(v) for v in
                                    view["buckets"].values()) == UNIVERSE
    # 盘上 G2 报告(现行权威)同口径: print_units==print_stones==check_stone.n
    g2 = json.load(open(G2REPORT_PATH))
    c = g2["meta"]["counts"]
    assert c["stones"] == UNIVERSE
    assert c["print_units"] == UNITS_CURRENT == c["print_stones"]
    assert g2["check_stone"]["n"] == UNITS_CURRENT
    # 口径考古钉: 1974 vs 2113 的解释写进 pack_verify 模块文档(不许丢)
    src = inspect.getsource(PV)
    for token in ("1974", "3961", "2113", "04f2e54", "T8b",
                  "ring_band_overlap", "thin_merge"):
        assert token in src, "口径考古缺 token: %s" % token
    # 两代口径各自守恒(证明是口径差不是丢账): 1974+3961 == 2037+3898 == 5935(原 2113+3822, 拱线族返工清债)
    assert UNITS_T8_ORIG + EXCL_T8_ORIG == UNIVERSE
    assert UNITS_CURRENT + EXCLUDED == UNIVERSE
    # 差 139 归因: ring_band 305→182(123 石) + thin_merge 84→68(16 石)
    # [拱线族返工清债 2026-10-08] 三代账: T8b(2113/3822) → ArchRoundFix
    # (2037/3898): 单元 −76 = 排除 +76(in_void +24 / void_cut +12 /
    # ring_band +40; 全部源于 b>a 三孔净空边界上移, 见 test_p2_sequencer)。
    # 逐桶现值: in_void 2028 / void_cut 1580 / ring_band 222 / thin 68。
    assert UNITS_T8B - UNITS_CURRENT == 24 + 12 + 40 == 76
    assert EXCLUDED - 3822 == 76
    # 不变量声明字符串: 声明石级恒等 + 现行单元口径 + 1974 历史口径
    inv = rep["不变量"]
    assert "石级" in inv and "2037" in inv and "1974" in inv
    assert "口径" in inv


# ── 3. 负控(篡改副本, 真账只读) ──

def test_neg_steal(conservation_pack, tmp_path):
    led, sec, df, ex, view, rep = conservation_pack
    tam = copy.deepcopy(df)
    victim = tam["unit_ids"].pop(0)
    sec2 = copy.deepcopy(sec)
    sec2["stones"].append({"id": victim})               # 偷挪: 塞进段清单
    rep2 = PV.verify_pack(sec2, tam, ex, led, recomputed=view)
    assert rep2["ok"] is False
    codes = {v["code"] for v in rep2["violations"]}
    assert "section_zone_mismatch" in codes, codes      # 段孔不含该 id 之孔
    assert "recompute_party_mismatch" in codes, codes   # 重算分段对不上
    assert victim not in set(tam["unit_ids"])


def test_neg_drop(conservation_pack):
    led, sec, df, ex, view, rep = conservation_pack
    tam = copy.deepcopy(df)
    victim = tam["unit_ids"].pop(0)
    tam["units_total"] = len(tam["unit_ids"])
    rep2 = PV.verify_pack(sec, tam, ex, led, recomputed=view)
    assert rep2["ok"] is False
    codes = {v["code"] for v in rep2["violations"]}
    assert "universe_missing" in codes, codes           # 三处都不出现
    assert "recompute_party_mismatch" in codes, codes


# ── 4. import 隔离三层探针(P3-T3/P2-T5 同款纪律) ──

def test_import_isolation_probe():
    # 层1 源码(AST import 面, 免疫 docstring 行文): 不 import section_pack,
    # 不直接 import export_print(后者只许经 p1a_slice 的判据几何传递依赖)。
    import ast
    tree = ast.parse(inspect.getsource(PV))
    tops = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            tops.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            tops.add(node.module.split(".")[0])
    assert "section_pack" not in tops, tops
    assert "export_print" not in tops, tops
    # 层2 subprocess 新解释器: import pack_verify 不得连带 section_pack;
    # export_print 只允许作为 p1a_slice(printcheck 判据几何)的传递依赖,
    # pack_verify 模块命名空间不得直接持有它(不碰装箱码)。
    env = dict(os.environ, PYTHONPATH=_3D)
    prog = (
        "import sys, pack_verify as pv; "
        "assert 'section_pack' not in sys.modules, 'section_pack 泄漏'; "
        "ep = sys.modules.get('export_print'); "
        "assert ep is None or not any("
        "    v is ep for v in vars(pv).values()), "
        "    'pack_verify 直接持有 export_print'; "
        "sys.exit(0)"
    )
    r = subprocess.run([sys.executable, "-c", prog], env=env,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, "隔离探针红: %s %s" % (r.stdout, r.stderr)
    # 层3 探针阴性对照: 同环境直接 import section_pack 必在 sys.modules
    # (证明层2 的断言环境本身能装下模块, 非恒真)。
    prog2 = ("import sys, section_pack; "
             "sys.exit(0 if 'section_pack' in sys.modules else 3)")
    r2 = subprocess.run([sys.executable, "-c", prog2], env=env,
                        capture_output=True, text=True, timeout=120)
    assert r2.returncode == 0, "探针阴性对照失效: %s %s" % (r2.stdout, r2.stderr)


# ── 5. CLI 面(--json / 篡改退出码, 注入重算避免二次 95s) ──

def test_cli_json_ok_and_tampered(conservation_pack, tmp_path, capsys):
    led, sec, df, ex, view, rep = conservation_pack
    rc = PV.main(["--json"], recomputed=view)
    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(out)["ok"] is True
    tam = copy.deepcopy(df)
    tam["unit_ids"].pop(0)
    p = tmp_path / "deferred_tampered.json"
    p.write_text(json.dumps(tam, ensure_ascii=False), encoding="utf-8")
    rc2 = PV.main(["--json", "--deferred", str(p)], recomputed=view)
    out2 = capsys.readouterr().out
    assert rc2 == 1
    assert json.loads(out2)["ok"] is False
