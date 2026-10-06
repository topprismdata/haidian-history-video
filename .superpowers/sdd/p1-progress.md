# P1 stone-ledger SDD Ledger
计划: docs/superpowers/plans/2026-10-06-p1-stone-ledger.md | 分支: main | BASE: 9327c8f

- Task 1: complete (commits 9327c8f..50e3662, 审查Spec✅/质量Approved, 修复轮I2/I3/I4/M1/M3/M4落地, 15测试+回归82绿)
  - 遗留跟进: I1 allow_clearance 挂 T6; 审查N4(zone/role词元映射)由T3/T4证实
- Task 2: complete (commits 0d9329d..395d254, 审查Spec✅/质量需修→修复轮C1(d权威深度)/C2(收分方向反号)/I1(恒真测试删除重写带符号)/m2(slab测试), 86测试绿; U2原点语义移交T7)
- Task 3: complete (commits dee62a6..6974723, 审查Spec✅两偏离裁对, 修复轮course_h从spec层距推导插穿47/107→0, 94测试绿; **T4契约: 层高必须复用_course_heights**)
- Task 5: 审查BLOCK→修复轮完成(d11b07f, 35测试, 11条全落地含结构化issues+旋转AABB) → 复审中
- Task 4: 审查BLOCK→修复轮完成(3780306, 10条全落地+突变自证M2/M10被抓, 真实p8 0穿透缝=2.0mm) → 复审中
- 主控待决策(S2): 雕件(lions2深互渗体块)进printcheck前是否CSG union——T6落笔前定
- T4W8流程违规记录: 实现者跳过隔离树直提主树(未踩踏, 例外放行一次, 后续dispatch已加强)
