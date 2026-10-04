# 本体变更记录

> 规则（facts.py docstring / spec §7）: M2.5 用户批准后 facts 本体节锁死；此后改锁死条目必须先在本文件登记，再改，再重跑本体判据（L1+L2 正检+负控，判据全绿才算完成）。


## 2026-10-04 环境构件桥轴旋转补正（T6 反馈）

- **问题**：T6 出图时发现 `abutment_ground` 旋转 0°，而本体与其余 8 个构件均为 −112°（`BRIDGE_AXIS_AZ`）。引道块孤悬水中并遮挡正交侧立面。T6 出图时用 `hide_render` 规避——那是绕过不是修复。
- **根因**：`build_scene2.py` 的批量旋转用内联元组枚举构件名，`abutment_ground` 漏在名单外。它与本体同父级 `m_body`，本就该一起转。
- **改动**：`build_scene2.py` 旋转名单补入 `abutment_ground`，并把枚举提为具名清单加注释说明为什么它在册。
- **是否触及冻结本体**：**否**。`abutment_ground` 属环境构件（`pier_plinth`/`deck_cornice` 同类），不在 M2.5 冻结的本体三对象内。
- **重跑判据（全绿才算完成）**：
  - 核心三对象几何 SHA **完全不变**：`bridge_body` nv=4409 sha=`6194d02d5557cc91`（与修复前一致）、`voussoir` sha=`da5441c7628a3215`、`impost` sha=`3db908a3a628646f`
  - L1 `fail=0`
  - L2 正检 `ok=True fail=[] exit=0`
  - L2 负控 `拱腹法线偏离朝心超容差 10/494 面 exit=1`（仍能抓）
  - 旋转核对：9 个桥体构件全部 −112.00°；`water` 0°（水平面，正确）
  - `pytest` 47 passed（改 manifest 哈希后）
- **冷重建硬门**：不受影响（几何哈希未变），T8 的对照结论继续有效。

## 2026-10-04 M2.5 冻结前基线

- commit: <待填——冻结包 commit 哈希，用户批准后回填>
- 状态: 待用户目验（冻结包为**候选**，未锁定；见 `3d/refs/freeze_manifest.md`）
- 冻结状态候选: `CONDITIONAL_RECONSTRUCTION_FREEZE`（依赖 12 条工作值 + 1 条图像推导，清单见 manifest §9）
