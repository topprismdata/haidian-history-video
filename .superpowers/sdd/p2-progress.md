# P2 build-sequencer SDD Ledger
计划: docs/superpowers/plans/2026-10-07-p2-build-sequencer.md | BASE: 6c02edb
- Task 1: complete (93d4a4a→f370d4f, 26测, 306全绿; 复审通过: I1-I5+S全闭环, 85条P1回归绿, G2工件重放双口径, 17错误码零互捕)
  - T5待议残留: 瞬时窗t==0迁CURVE_ORDER红边界(a==b==0改[[0,0]]或拒迁); to-only边全区间0语义与from==to救法不对称(真工件0条)
- Task 2: fixed (45cff94→da89080+5743ec8, 348绿, core逐位×3, geom_math单源17孔Δ=0跨源钉, D1拱腹工作面/D2停车线回退STALE/D4 1-based集合钉/D5 raise/D6 y维) (e32753a补丁轮: M11族字面钉真闭环+AST堵import-from+§7历史修正, 351绿) → **T2 complete**
- M20b(新债务票): RING_T分叉真缺陷=端孔环厚0.54>拱肩0.50券石穿桥面4-11cm; 等价式fail⟺RING_T>spandrel(i); 需正射重测端孔冠部(拱肩vs环带谁动)→ring_t(i)或SPANDREL_E重标定→voussoir重冻+G2重生成; 在T5曲线落账前完成避免返工
- Task 3: complete (1abb57d→b23a9f1, 54测, 331全绿; 复审PASS: 独立变异8/8恰杀, H1真账fail-closed实测)
  - T4硬约束(复审M4裁决): 交付校验必须 validate_event_ledger(..., require_evidence=True)+专门测试钉死; T4后翻转默认True+废占位符
  - T4/T5接线: M7覆盖类7项归T4生成侧+T5 frontier; HOLD挂石引用时T5补zone交叉; M6真账曲线待T5落账后known_event_seqs交叉才有牙
- 主控brief错误记录: T2工作面extrados说(结构不成立)+端孔柱高歧义+T1插值算术错 → 审查链对主控同样有效
- Task 4: complete (93a9be1→0e3fe56, 392绿; 复审PASS零阻塞: Σ≥1独立复扫7.9M点0违例, 五变异恰红, 原账sha不变, 工件可复现cmp逐位)
  - W1裁决: 28块≥99%被环石实体吞没的rbo石=P1双建模债显形, 记T5交接+P3视觉隐藏处置, 不扩幻影定义(in_void语义已100%执行, 扩=全链返工)
  - W2: 报告§6.6补superseded注(T5代理顺手)
- Task 5: complete (0e3fe56→T5, 392+17=409绿; g3_check snapshot状态机+①Σ≥1/活跃/RING三闸/幻影闸/R6独立重建, 不import sequencer闭包钉死; 真账4070事件2.63s(<10s闸)零违例, holes_timeline≡frontier_trace逐孔, in_void≡excluded_ids 2052逐位; 五负控+3b/5b恰红(③Σ=0.75/0.5/0.25/0逐档); W1复现25块@0.99 vs 主控口径28@0.985(敏感带0.986-0.989三块), 以落盘清单为准待主控裁决; W2已注40.9%)
- Task 5: implemented (9813051, 409绿) — 审查WARNING: 交叉验证真独立(子进程探针+非复制0.113相似度), 增量对拍20seed零失配, 幻影双保险; 待处置W1持荷非同构(裁:对齐"全部hold完成")/W2尾部knot盲区(裁:排空)/W3报告勘误10543→6199/S1合龙边界钉/W4死码; **W1阈值改判28@0.985保守口径(推翻我先前25@0.99, 代价不对称论证)**; 修复与T6发现并单(同文件, 等T6落盘)
- Task 5: 修复落地 f83bffd(W1持荷同构含增量态更深分歧/W2尾knot/S1边界钉/W4死码/W3勘误, 3变异全杀)
- Task 6: d8d564b 停车线→裁决落地 2202548(R5a径向带闸+DM28剔除+结构带截面假设 C:A5+Heyman, acceptance 6孔→1孔) 423绿工件两连跑逐字节同
- **疑点**: ARCH07(102石)不可行 vs 镜像ARCH11(106石,荷载更多)可行, 裸环逐位同[9.96,11.83] — 对称桥不对称失败=数据伪影强信号; Arch07Diag 只读诊断中(反事实换荷载集二分定位), 诊断前不派 T6 审查
