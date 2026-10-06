# -*- coding: utf-8 -*-
"""M19: stones_p8.json z 锚点随桥面重标定重推(数据变换, x 布局不动)。
分段线性: <0.85(水线带)恒等; [0.85, old_spz]->[0.85, new_spz];
[old_spz, old_last]->[new_spz, new_last](new_last = old_last 与旧帽的层距保持)。"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "stones", "stones_p8.json")

OLD_SPZ = 1.98          # 旧中央起拱线(7.75-1.00-0.56*8.50)
NEW_SPZ = 1.14          # 新(7.30-1.40-0.56*8.50)
OLD_BAY_CAP, NEW_BAY_CAP = 7.75 - 0.10, 7.30 - 0.10      # 湾内旧/新桥面帽
OLD_PIER_CAP = 7.75 - 0.10 - (7.75 - (7.75 - 7.378e-4 * 5.815 ** 2))  # 墩8 旧帽(≈7.625)
NEW_PIER_CAP = 7.30 - 0.10 - (7.30 - (7.30 - 9.0667e-4 * 5.815 ** 2))  # 墩8 新帽(≈7.169)


def xmap(z, old_spz, new_spz, old_last, new_last):
    if z <= 0.85:
        return z
    if z <= old_spz:
        return 0.85 + (z - 0.85) * (new_spz - 0.85) / (old_spz - 0.85)
    return new_spz + (z - old_spz) * (new_last - new_spz) / (old_last - old_spz)


s = json.load(open(P))
meta = s.setdefault("_meta", {})
meta["m19_rebase"] = {
    "note": "z 锚点随 M19 桥面重标定(7.75/3.60->7.30/2.20, SPANDREL 1.0->1.4/0.5)重推; "
            "x 布局(照片驱动)逐字不动; 旧 z0 见 m19_old_z0",
    "old_spz": OLD_SPZ, "new_spz": NEW_SPZ,
}
courses = s.get("courses") or []
if courses:
    olds = [float(c["z0"]) for c in courses]
    meta["m19_rebase"]["m19_old_z0_courses"] = olds
    old_last = max(olds)
    old_cap = OLD_BAY_CAP
    new_cap = NEW_BAY_CAP
    new_last = new_cap - (old_cap - old_last)
    for c, z0 in zip(courses, olds):
        c["z0"] = round(xmap(z0, OLD_SPZ, NEW_SPZ, old_last, new_last), 3)
pier = s.get("pier") or {}
if isinstance(pier.get("courses"), list):
    olds = [float(v) for v in pier["courses"]]
    meta["m19_rebase"]["m19_old_z0_pier"] = olds
    old_last = max(olds)
    new_last = NEW_PIER_CAP - (OLD_PIER_CAP - old_last)
    pier["courses"] = [round(xmap(z, OLD_SPZ, NEW_SPZ, old_last, new_last), 3)
                       for z in olds]
json.dump(s, open(P, "w"), ensure_ascii=False, indent=1)
print("BAY z0:", [c["z0"] for c in courses])
print("PIER z0:", pier.get("courses"))
