# -*- coding: utf-8 -*-
"""M11-D 统一认证 evaluator: 读 cert_gates.json(事前冻结) + 26 报告全部指标,
ALL-AND 输出 CERTIFIED / NOT_CERTIFIED。禁止任何单门或平均分替代。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    gj = json.load(open(os.path.join(HERE, "cert_gates.json")))
    gates = gj["gates"]
    rep = json.load(open(os.path.join(ROOT, "delivery", "26_cam_register_report.json")))
    reg = json.load(open(os.path.join(HERE, "cam_register_last.json")))
    metrics = {
        "similarity_landmarks": reg.get("similarity_landmarks"),
        "reproj_rmse_px": reg.get("reproj_rmse_px"),
        "void_IoU": rep.get("void_IoU"),
        "bridge_body_IoU": rep.get("bridge_body_IoU"),
        "contour_Chamfer_px_halfres": rep.get("contour_Chamfer_px_halfres"),
        "deck_camber_pearson": rep.get("deck_camber_pearson"),
        "deck_camber_rmse_px_halfres": rep.get("deck_camber_rmse_px_halfres"),
    }
    fails = []
    for k, rule in gates.items():
        v = metrics.get(k)
        if v is None:
            fails.append((k, "MISSING"))
            continue
        if ">=" in rule and not (v >= rule[">="]):
            fails.append((k, "v=%.4f < %.4f" % (v, rule[">="])))
        if "<=" in rule and not (v <= rule["<="]):
            fails.append((k, "v=%.4f > %.4f" % (v, rule["<="])))
    out = dict(verdict="CERTIFIED" if not fails else "NOT_CERTIFIED",
               fails=fails, metrics=metrics,
               gates_sha256=gj.get("_sha256"),
               note=gates.get("rule"))
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return out


if __name__ == "__main__":
    main()
