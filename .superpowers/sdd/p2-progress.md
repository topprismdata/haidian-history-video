# P2 build-sequencer SDD Ledger
计划: docs/superpowers/plans/2026-10-07-p2-build-sequencer.md | BASE: 6c02edb
- Task 1: complete (93d4a4a→f370d4f, 26测, 306全绿; 复审通过: I1-I5+S全闭环, 85条P1回归绿, G2工件重放双口径, 17错误码零互捕)
  - T5待议残留: 瞬时窗t==0迁CURVE_ORDER红边界(a==b==0改[[0,0]]或拒迁); to-only边全区间0语义与from==to救法不对称(真工件0条)
- Task 2: implemented (45cff94) — 审查BLOCK(2C+4H: id 0based静默错配17孔/springer第二公式偏1.17m/工作面应在intrados[主控brief错误]/RING_T facts0.40vs账0.54分叉/夹持静默/footprint缺y维) → D1-D7裁决修复轮在跑(geom_math单源提取+冻结重锚规程)
- Task 3: implemented (1abb57d, 29测) — 审查REQUEST_CHANGES(3H: CLOSE判据可空转/裁决零pin变异存活/引用类不分流) → 修复轮在跑
- 主控brief错误记录: T2工作面extrados说(结构不成立)+端孔柱高歧义+T1插值算术错 → 审查链对主控同样有效
