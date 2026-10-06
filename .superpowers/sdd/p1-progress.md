# P1 stone-ledger SDD Ledger
计划: docs/superpowers/plans/2026-10-06-p1-stone-ledger.md | 分支: main | BASE: 9327c8f

- Task 1: complete (commits 9327c8f..50e3662, 审查Spec✅/质量Approved, 修复轮I2/I3/I4/M1/M3/M4落地, 15测试+回归82绿)
  - 遗留跟进: I1 allow_clearance 挂 T6; 审查N4(zone/role词元映射)由T3/T4证实
- Task 2: complete (commits 0d9329d..395d254, 审查Spec✅/质量需修→修复轮C1(d权威深度)/C2(收分方向反号)/I1(恒真测试删除重写带符号)/m2(slab测试), 86测试绿; U2原点语义移交T7)
- Task 3: complete (commits dee62a6..6974723, 审查Spec✅两偏离裁对, 修复轮course_h从spec层距推导插穿47/107→0, 94测试绿; **T4契约: 层高必须复用_course_heights**)
- Task 5: complete (2ca3434..aad7779, 复审FAIL→收口M1/M2/M3红转绿, 42测/全量147; 平面阈1e-5导出安全+绕向自适应+gap NaN闸门)
- Task 4: complete (d095eee..3780306, 复审APPROVE: 242带端全=2.000mm独立实证, mm级负控)
  - T8接线清单(复审非阻塞项): ①退让读params['proud']非模块常量 ②带跨hw钳位折点需带内加密(p8现不触发) ③backing_stones单面契约docstring ④x梯度dz分支真实数据冒烟
- 主控待决策(S2): 雕件(lions2深互渗体块)进printcheck前是否CSG union——T6落笔前定
- T4W8流程违规记录: 实现者跳过隔离树直提主树(未踩踏, 例外放行一次, 后续dispatch已加强)
- Task 6: implemented (93a3dfa, 24测/171绿) — 审查Spec✅/Approved(0 Crit); 独立探针: inset半空间检验证不撑大桥/两量分离字节级/flip-M3自洽/超床独批不塞爆
  - W3主控裁决已落地(6bc6783): FIT打印毫米+coupon 1:1(缝2×fit可实测, NORMAL打印当量0.600mm留证)+回读双验+W1/S1-S5, 173绿 → Task 6 complete
  - P4备忘(S4/S6): manifest created_utc不可复现→回归哈希时置可选; y向inset面不对称在T7/T8全桥gap_check贴边时回看
- Task 7: implemented (1b5f9df, 188测+312, proxy逐字节回归独立证实, IoU0.9326非挪门柱[审查反向实验含coursing物理上限0.656]) — 审查质量FAIL单点H1(cap_to_deck slab误用wedge中心锚: 29越顶/9bbox坏/8静默弃) → complete (17b37dd修复, 复审PASS无一虚报: 越顶29→0/IoU0.9393/弃2救2raw对照/S4反驳成立)
- Task 8: implemented (04f2e54, G2 PASS 5935石/1974打印单元fail=0/守恒排除3961带id, 试印包234石1546cm3≈129h, 212测) — 审查中
- Task 9(处方更正, T8审查实证): 真因=cap_to_deck截顶未重算transform[1](y面), 非backing退让公式; 旧处方"补taper/2"会把610对好石变空腔已拦。并入T8b单修复轮
- Task 8: 审查BLOCK — C1吞没石漏进打印集(23块撞RING/17cm3死料)+C2包含型赦免+W1全量id+W2豁免无界+报告两处不实陈述+体积口径声明 → T8b修复轮派发中
  - T8接线清单(累积): ①core_cells x界必填已强制 ②退让读params['proud'] ③hw钳位折点带内加密 ④x梯度dz真实冒烟 ⑤clip石导出走烘焙网格(T7已raise化) ⑥ABUT分区空(桥台砌体未入账) ⑦layout无-112°方位属表现层 ⑧雕件白名单外(P4)

## T8b 期间审查方追加裁决(P1T8Review→P1T8bFix, 主控认可)
- 处置按体积吞没率pre-inset判, 面积ratio只记账; case_A(≥0.99)出集/case_B(部分撞)必须解析裁剪不得丢弃/case_C需主控显式签署降级
- 闸门收紧: final_scope_check.n_colliding==0须独立3D复测禁从桶推导; 三条负控(关case_A必红/咬角盒落B不落A/post-inset判处置被钉死)
- 顺序 B2→B3→B4; 两侧"23"按id对账
- 主控预备: 若fixer报case_C, 优先要求补裁剪而非签署降级(用户目标=可装配)
