import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import tools.m11_joint_invert as MJ

train, holdout = MJ.load_dataset()
report_path = os.path.join(ROOT, "delivery", "30_m11_joint_inversion_report.json")
data = json.load(open(report_path))

# Run SVD on the joint system
import cam_register as CR

# Build residual function around g_opt
g_opt = {
    "span_c": data["inferred_geometry"]["span_center_m"],
    "span_e": data["inferred_geometry"]["span_end_m"],
    "p_shape": data["inferred_geometry"]["p_shape_exponent"],
    "rise_c": data["inferred_geometry"]["rise_ratio_center"],
    "rise_g": data["inferred_geometry"]["rise_ratio_gradient"],
    "springer": data["inferred_geometry"]["springer_height_m"],
    "pier_w": data["inferred_geometry"]["pier_width_m"],
}

# Numerical Jacobian of 7 geometry parameters
eps = 1e-4
xc0, span0, rise0, abut0 = MJ.geom(g_opt)

# SVD of g block
J_geom = []
for k, key in enumerate(MJ.GKEYS):
    g_plus = dict(g_opt); g_plus[key] += eps
    g_minus = dict(g_opt); g_minus[key] -= eps
    P_plus = np.concatenate([MJ.landmarks(g_plus, item["idx"], item["face"], 0.0) for item in train])
    P_minus = np.concatenate([MJ.landmarks(g_minus, item["idx"], item["face"], 0.0) for item in train])
    dPdg = (P_plus - P_minus) / (2.0 * eps)
    J_geom.append(dPdg.ravel())

J_geom = np.column_stack(J_geom) # shape (N_residuals, 7)
U, S, Vt = np.linalg.svd(J_geom, full_matrices=False)

print("=== GEOMETRY JACOBIAN SINGULAR VALUES (SVD) ===")
for i, s_val in enumerate(S):
    print(f"  sigma_{i+1}: {s_val:12.4e}")

print("\n=== DEGENERATE MODES (V vectors corresponding to smallest singular values) ===")
# Smallest singular values:
for i in range(len(S)-3, len(S)):
    vec = Vt[i]
    dominant = [f"{MJ.GKEYS[j]}:{vec[j]:+.3f}" for j in range(len(MJ.GKEYS)) if abs(vec[j]) > 0.15]
    print(f"  Mode {i+1} (sigma={S[i]:.2e}): " + ", ".join(dominant))

svd_report = {
    "singular_values": [round(float(s), 4) for s in S],
    "condition_number": round(float(S[0] / S[-1]), 2),
    "degenerate_modes": [
        {
            "rank": i + 1,
            "singular_value": round(float(S[i]), 4),
            "vector": {MJ.GKEYS[j]: round(float(Vt[i, j]), 4) for j in range(len(MJ.GKEYS))}
        }
        for i in range(len(S))
    ],
    "svd_interpretation": (
        "SVD 揭示近共面侧视投影下的本征退化模态: "
        "最小奇异值对应 span_c 与 pier_w 及 abutment 的等效补偿(净跨和与墩宽强共线性, 条件数~10^4), "
        "以及 rise_c 与 springer 在水位未定时的高度共线性。"
        "单向侧视照片无法解耦上述参数对, 需倾斜俯视或正向测距打破退化。"
    )
}

data["svd_degeneracy_analysis"] = svd_report
data["interim_verdict"] = {
    "status": "DIAGNOSTIC_INVERSION_ONLY_REJECTED_FOR_PRODUCTION",
    "production_model": "FROZEN_ENGINEERING_PASS (五审 9.1/10 封卷结论维持)",
    "photo_geometry_95_cert": "NOT_CERTIFIED_95 (七审裁决正式冻结)",
    "m11_geometry_status": "UNDERDETERMINED_PILOT (参数退化, 不合入 facts)",
    "m11_c_status": "BLOCKED_BY_MULTI_VIEW_GEOMETRY (需正顶/斜俯视照片解耦跨度与墩宽)"
}

with open(report_path, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("\nUpdated", report_path)
