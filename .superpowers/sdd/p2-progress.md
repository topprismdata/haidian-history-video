# P2 build-sequencer SDD Ledger
计划: docs/superpowers/plans/2026-10-07-p2-build-sequencer.md | BASE: 6c02edb
- Task 1: complete (93d4a4a→f370d4f, 26测, 306全绿; 复审通过: I1-I5+S全闭环, 85条P1回归绿, G2工件重放双口径, 17错误码零互捕)
  - T5待议残留: 瞬时窗t==0迁CURVE_ORDER红边界(a==b==0改[[0,0]]或拒迁); to-only边全区间0语义与from==to救法不对称(真工件0条)
- Task 2: fixed (45cff94→da89080+5743ec8, 348绿, core逐位×3, geom_math单源17孔Δ=0跨源钉, D1拱腹工作面/D2停车线回退STALE/D4 1-based集合钉/D5 raise/D6 y维) — 复审在跑
- M20b(新债务票): RING_T分叉真缺陷=端孔环厚0.54>拱肩0.50券石穿桥面4-11cm; 等价式fail⟺RING_T>spandrel(i); 需正射重测端孔冠部(拱肩vs环带谁动)→ring_t(i)或SPANDREL_E重标定→voussoir重冻+G2重生成; 在T5曲线落账前完成避免返工
- Task 3: complete (1abb57d→b23a9f1, 54测, 331全绿; 复审PASS: 独立变异8/8恰杀, H1真账fail-closed实测)
  - T4硬约束(复审M4裁决): 交付校验必须 validate_event_ledger(..., require_evidence=True)+专门测试钉死; T4后翻转默认True+废占位符
  - T4/T5接线: M7覆盖类7项归T4生成侧+T5 frontier; HOLD挂石引用时T5补zone交叉; M6真账曲线待T5落账后known_event_seqs交叉才有牙
- 主控brief错误记录: T2工作面extrados说(结构不成立)+端孔柱高歧义+T1插值算术错 → 审查链对主控同样有效
