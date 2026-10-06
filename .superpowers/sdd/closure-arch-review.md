# 闭包方法 architect 内审报告(2026-10-02)

## Verdict: 需先修 critical(C1+C2),修完可与 GPT 外审意见合并执行

## Critical
- C1【违反不变式3·词表双字形】_STOPWORDS 简体侧缺 7 词:繁体侧收了 圓明園/清漪園/暢春園/靜宜園/靜明園/萬壽山/稻田廠(expansion.py:47-48),简体侧一个都没有;泛指词 八處(:50)也无简体 八处。简体档案语料入库后 畅春园/清漪园/静宜园/静明园(无种子覆盖)将以 mid/high 候选冒充新发现。修复:补词+加简体负控制断言;仿 qa_gate.py:170-182(G6 双字形覆盖检查器)对 _STOPWORDS 做繁→简自检。
- C2【违反不变式3+spec §2.2】known_names 只收 a.label 单字形:expansion.py:306 只 update a.label;Appellation.script_variants(spatiotemporal.py:268「异体字/讹字」)全库零引用。种子 label 全简体(树村/青龙桥/大有庄)而官书引文繁体,已建词条以繁体字形回归为【high 置信】新候选——樹村(坐落+村双证)、青龍橋(曰+橋)、大有莊(為+莊),占据人工消费队列最上层,每代重复污染。G6/G7 同型「单字形翻车」换了个集合复发。注意:test:52-56 断言 蕭家河/安河橋 不受影响(种子只有 萧家河北,base 形不同),修复后仍应发现;但不得新增对 樹村 的同类断言。

## Major
- M1【溯源半残】CandidateName.from_source_id 恒空(:180,208 写死 "";mine() 收 source_id 但从不写入)。expand() 挖书循环 :324 回填。
- M2【证据塌缩+计数混计】discovered[cand.name] first-wins(:332):同名候选在别的篇卷的独立书证被静默丢弃——「一名多书互证」塌缩为1条。cycles_avoided 混计三类事件(重复篇卷/命中已知名/重复候选名),render「环避让N次」不可归因。改 name→List[CandidateName],计数拆三字段。
- M3【B法语义与spec冲突】后缀扫描只取「锚点+短语尾窗」(:189-213):「內務府於青龍橋設稻田廠」→产出污染窗口「龍橋設稻田廠」;test 夹具实际产出「永定河入西山」而非干净「永定河」,断言用子串匹配恒过掩盖缺陷。修复(命中后从锚点回溯专名头)后重跑实测并留档。
- M4【契约漂移】spec 叫 SourceMiner,代码叫 ToponymMiner,别名 QuoteCorpusMiner 承重。定义 SourceMiner Protocol(3.9 可用),删别名,更新调用点。
- M5【seen_sources 隐藏假设】去重键 (source_id, division_id) 假设同篇卷 facts 全局同源,但每个 KB deep-copy 各自 facts:两词条共引同卷不同切片时,第二个 KB 的独有引文被静默跳过并计成「环避让」——是书证丢失不是环。E12+ 第一轮即踩中。键加 kb 维度或同 division 合并 facts 挖一次。
- M6【负控制缺口】①简体侧双字形负控制缺失(补测即 FAIL 实锤 C1);②跨 KB 去重无用例;③B法干净名负控制缺失;④幂等性负控制缺失。

## Minor
- m1 _is_noise 死分支 or self.known_names 无效果
- m2 rep.seeds.extend(dict and list) 真值巧合,改列表推导
- m3 QAGate/QAReport 未用导入;adversarial 存而不论;rep.rejected 恒空;docstring 提及不存在的 qa_gate_args
- m4 spec 伪代码名≠实现名,应注明
- m5 test_sources_mined==20 绝对值断言脆弱;test_suffix_scan 子串断言;test_candidates_are_traceable 恒真字段
- m6 _suffix_scan low 分支死代码
- m7 每 division 全量浅拷贝 facts,O(D×F),按 division_id 预索引
- m8 DIRECTION_SUFFIXES 裸方位词超集,注释取舍

## 五条不变式核查
1. 引擎只发现不入库 ✅
2. evidence_fact_id 溯源 ✅半残(from_source_id 恒空=M1)
3. 词表繁简双字形 ❌❌(C1+C2)
4. 九维闸门 ✅(不适用是正确的)
5. TGAZ 未验证契约未写码 ✅
