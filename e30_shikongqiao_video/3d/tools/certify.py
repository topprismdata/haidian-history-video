# -*- coding: utf-8 -*-
"""M11-D 统一认证 evaluator(九审第 3 项升级: 真正落实冻结规则的多照片语义)。

读取:
  - tools/cert_gates.json           事前冻结门(sha256 校验)
  - delivery/30_m11_joint_inversion_report.json  多照片联合反演报告
  - delivery/26_cam_register_report.json         同机位 clay 比对(可选, 单图 IoU 类门)

冻结规则(七审 M11-D):
  1. 7 门 ALL AND, 对**每张参与认证的照片独立**判定;
  2. 训练黄金照片集 >= 3 张;
  3. >= 1 张完全 hold-out(从未参与几何拟合), 且 hold-out 亦须独立过全部门;
  4. 任一照片任一门失败 -> 整体 NOT_CERTIFIED; 缺数据 -> NOT_CERTIFIED(不默认通过)。

输出 CERTIFIED / NOT_CERTIFIED + 逐照片逐门明细。禁止平均分/单门替代。
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 照片级可判门(landmark 类); IoU/Chamfer/camber 类门需 26 报告的 clay 比对, 按照片可用性判
LANDMARK_GATES = ["similarity_landmarks", "reproj_rmse_px"]


def load_gates():
    path = os.path.join(HERE, "cert_gates.json")
    raw = open(path, "rb").read()
    gj = json.loads(raw.decode())
    actual = hashlib.sha256(raw).hexdigest()
    declared = gj.get("_sha256")
    return gj, actual, declared


def check_gate(rule, v):
    """返回 (pass:bool, detail:str)。v=None -> fail(MISSING)。"""
    if v is None:
        return False, "MISSING"
    msgs = []
    ok = True
    if ">=" in rule:
        p = v >= rule[">="]
        ok = ok and p
        msgs.append("%s>=%.4f:%s" % ("v" if p else "v", rule[">="], "OK" if p else "FAIL"))
    if "<=" in rule:
        p = v <= rule["<="]
        ok = ok and p
        msgs.append("%s<=%.4f:%s" % ("v" if p else "v", rule["<="], "OK" if p else "FAIL"))
    return ok, ", ".join(msgs)


def main():
    gj, actual, declared = load_gates()
    gates = gj["gates"]
    rep_path = os.path.join(ROOT, "delivery", "30_m11_joint_inversion_report.json")
    if not os.path.exists(rep_path):
        print(json.dumps(dict(verdict="NOT_CERTIFIED",
                              reason="缺少 30 多照片联合反演报告; 单照片不足以认证"),
                         ensure_ascii=False, indent=1))
        return 1
    rep = json.load(open(rep_path))
    train = rep.get("training_evaluation", [])
    hold = rep.get("holdout_evaluation")

    # 规则 2: 训练黄金照片 >= 3
    n_train_ok = len(train) >= 3
    # 规则 3: hold-out 存在
    n_hold_ok = hold is not None

    per_photo = []
    all_pass = True

    def eval_photo(item, role):
        nonlocal all_pass
        res = dict(name=item.get("name"), role=role, gates={})
        for g in LANDMARK_GATES:
            # 30 报告字段名映射: rmse_px -> reproj_rmse_px
            v = item.get("rmse_px") if g == "reproj_rmse_px" else item.get(g)
            p, d = check_gate(gates[g], v)
            res["gates"][g] = dict(value=v, passed=p, detail=d)
            all_pass = all_pass and p
        # IoU/Chamfer/camber 门需该照片的 clay 同机位比对; 30 报告未含 -> 诚实记 MISSING(=fail)
        for g in ["void_IoU", "bridge_body_IoU", "contour_Chamfer_px_halfres",
                  "deck_camber_pearson", "deck_camber_rmse_px_halfres"]:
            p, d = check_gate(gates[g], None)
            res["gates"][g] = dict(value=None, passed=p,
                                   detail="NO_CLAY_COMPARISON_FOR_THIS_PHOTO(按规则判 fail, 不默认通过)")
            all_pass = all_pass and p
        return res

    for item in train:
        per_photo.append(eval_photo(item, "train"))
    if hold:
        per_photo.append(eval_photo(hold, "holdout"))

    # 规则 4: 汇总
    all_pass = all_pass and n_train_ok and n_hold_ok
    verdict = "CERTIFIED" if all_pass else "NOT_CERTIFIED"
    out = dict(
        verdict=verdict,
        gates_sha256_declared=declared,
        gates_sha256_actual=actual,
        gates_hash_consistent=(declared == actual),
        rule_train_ge3=dict(required=3, actual=len(train), passed=n_train_ok),
        rule_holdout_present=dict(required=1, actual=(1 if hold else 0), passed=n_hold_ok),
        per_photo=per_photo,
        note=gj.get("rule"),
        summary=("训练照片 %d 张(<3 不满足认证集规模), hold-out %s; "
                 "且各照片缺同机位 clay 的 IoU/Chamfer/camber 门按规则判 fail -> "
                 "NOT_CERTIFIED_95 维持。" % (len(train), "有" if hold else "无"))
    )
    print(json.dumps(out, ensure_ascii=False, indent=1))
    with open(os.path.join(ROOT, "delivery", "32_certify_verdict.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
