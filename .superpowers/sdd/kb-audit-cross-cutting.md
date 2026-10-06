# 跨集横切审计报告（KBAuditCrossCutting）

审计日期：2026-10-04。范围：`haidian_kg/calibration/`（22 内容模块，163 条 ADOPTIONS / 166 条 PROPOSITIONS）、`haidian_kg/extractor.py`（74 toponym / 73 attestation / 7 hypothesis）、`haidian_kg/data/`（entities.json + haidian_kg.ttl）、27 份已交付集 `research.md`（E1–E28，E29 研究档 v1.0 已在库）。
铁律遵守：只审不改；全部结论带 `文件:行号` 或外部 URL；核不出的明说核不出。

---

## 1. DISPROVEN 采信纪律（任务①）

**结论：全库 31 条 DISPROVEN 无一缺 `refuting_fact_ids`。** `ontology/epistemic.py:272-284` 的 `_disproven_needs_evidence` model_validator 在构造层硬阻断，且我绕开构造器做了旁路扫描（raw grep + 全模块导入后逐条复核），未发现任何 bypass（无 `construct()`/`parse_obj`）。31 条 DISPROVEN 的 refuting ids 全部真实存在于模块 FACTS（0 条悬空）。166 条 PROPOSITION 的 `derived_from_fact_ids`、7 条 hypothesis 的 supported/disproven ids 也全部存在。

语义纪律抽查（合法 DISPROVEN vs 应为 UNSUBSTANTIATED）：
- 合法（有文献说"不是X"）：dajuesi `prop_e24_jinzhangzong_founder`（辽碑 1068 直接证伪）、guajiatun 杨六郎两条（宋史地理）、shifangpujue `prop_e26_wofoe_is_yuan_not_tang`（雍正御制碑「后人范铜为之」）等——均真证伪。
- 边界把握正确的一例：wutasi `prop_e25_qianlong_bihuang_rename`（乾隆避讳说）——「时序不通」但无一手书证可反驳，按 E25 纪律立 **UNSUBSTANTIATED 而非 DISPROVEN**（wutasi_video/research.md:17 红线明文），与 skill://detector-needs-negative-control 的 absence-of-evidence 纪律一致。**这不是问题，是正面样板。**

## 2. 但发现：采信层的修复**没有传播到运行时数据层**（🔴 最重发现）

`data/entities.json`（10-03 11:08）与 `data/haidian_kg.ttl`（10-04 10:17 由 builder.py 从 entities.json 重建）相比 extractor.py **系统性过期**：

| 项 | extractor.py（真源） | data/ 导出层（运行时，query.py → ttl → entities.json） |
|---|---|---|
| `attest_wenquan_dijing`（伪引文，E28 证伪） | DISPROVEN（extractor.py:1192-1204，2026-10-04 注记） | **仍 VERIFIED**（entities.json /place_attestations/40；haidian_kg.ttl:958-962 `hhto:epistemicStatus "VERIFIED"`） |
| `attest_baijiatuan_caoxueqin`（过度断言降级） | CONTESTED（extractor.py:1175-1181） | **仍 VERIFIED** |
| E26 十方普觉寺七地名（top_sifangpujue/wofosi/doushuai/shuanshansi/zhaoxiaoshi/hongqingsi/yongansi） | 已建（extractor.py:626-632） | **全部缺失**（export toponyms 67 vs extractor 74） |
| E27 两条书证（attest_baijiatuan_founding / _yixianqin） | 已建 | **缺失**（export attestations 69 vs 73） |

后果：E28 research 自己列明其 KB 底本是 `haidian_kg/data/entities.json`（wenquan_video/research.md:222）——**修复根本没有到达它声称已修复的那一层**。运行时（query.py 问答、qa_gate、production_exports）读到的仍是「伪引文=已确证」。E26 的"五次易名"链条在运行时图谱里不存在。
建议：从 `HaidianCorpusExtractor.extract_all()` 重新导出 entities.json 并重建 TTL（builder.py 即接 entities.json），并在 CI 加「extractor↔export 一致性断言」（id 集合 + epistemic_status 双向 diff）。

## 3. 跨集事实矛盾清单（任务②，每条附 A/B 原文）

**G1 🔴 era7 vs E14 + 外部：恩佑/恩慕寺山门保护级别错级（国保→实为市保）**
- A `haidian_kg/corpus/era7_qing.md:11`：「《康熙起居注》详载圣祖常年园居理政，**今仅存恩佑寺、恩慕寺山门两处国保**」
- B `changchunyuan_video/research.md:64`：「**『畅春园遗址 2021 列市保』❌（两座山门分别列保）**」；同文件 :93 将 2021 市保拆挂到两山门实体
- 外部：海淀区政府官网「两座山门……现均为**北京市文物保护单位**」https://zyk.bjhd.gov.cn/kjhd/hdww/wwcl/202208/t20220801_4546013_hd.shtml
- 判断：A 错。山门是市级文保，非国保。era7 行文未随 E14 冻结口径回写。

**G2 🔴 extractor 层 vs E26 订正：寿安山寺朝代错置在 KB 里复活**
- A `haidian_kg/extractor.py:108-110`（注释）：「4. **明·正统八年重修，改称寿安山寺** 5. 明·成化十八年再改永安寺」
- B `shifangpujue_video/research.md:12-14`（V-NC02，2026-10-04 审核订正）：「元延祐七年（1320）敕建**寿安山寺**……明正统八年（1443）敕赐**寿安禅林**」——并明文「初稿误将寿安山寺配到明正统八年……系**跨朝代名号错置**」
- 判断：E26 已订正「寿安山寺=元、寿安禅林=明」，extractor 注释仍是订正前旧链，且 KB 完全缺「寿安禅林」这个名号（七地名里没有它）。同一错误在 research（已修）/extractor 注释（未修）/export（不存在）三层状态各不相同。

**G3 🟡 E8 内部/跨集：通惠河「开凿」年份口径（1292 vs 1293）**
- A `gaoliangqiao_video/research.md:80`：「**郭守敬 1293 年开凿通惠河**……」；同文件 :199 表：「通惠河开凿 | **1293 年**，郭守敬」
- B 同文件 :76：「元至元二十九年（**1292 年**）……命都水监郭守敬引白浮泉……」；`changhe_video/research.md:96`（《元史》卷64 直核）：「**首事於至元二十九年之春，告成於三十年之秋**，賜名曰通惠」；`guoshoujing_video/research.md:32`：「郭守敬**至元二十九年（1292）工程**」
- 判断：《元史》原文开工 1292 / 告成赐名 1293。E8 两处把「告成年」写成「开凿年」，E29 已把 1292 定为口径。建议 E8 表行改「1292 开工、1293 告成赐名」（E16 §4-4 的双徽文案即此式）。

**G4 🟡 E17 虚指 E8 内容：「于谦/夺门」在高梁桥集不存在**
- A `fenshi_video/research.md:26`：「**不整段讲景帝政治史（E8 高梁河之战已讲于谦/夺门背景的部分）**」
- B `gaoliangqiao_video/research.md` 全文 grep `于谦|夺门|景泰|景帝` = **0 命中**。E8 的「高梁河之战」是 979 年宋辽之战，与于谦（1449 北京保卫战）、夺门（1457）无关。
- 判断：E17 的跨集引用悬空——若按此句执行，叙述者会以为背景已在 E8 交代而跳过，观众接不上。建议 E17 改为自含一句背景或改指正确集。

**G5 🟡 E28 内部：黑龙潭及龙王庙「第六批」年份 2003 vs 2006**
- A `wenquan_video/research.md:141`：「**2003 年**作为京杭大运河北京段组成部分列第六批国保（6-810）」
- B 同文件 :17：「黑龙潭及龙王庙＝大运河国保子项（第六批 **6-810，2006**……）」；第六批公布日 2006-05-25（国发〔2006〕19号，E15/E24/E26 三集同引）
- 判断：141 行「2003」是错年。另注：6-810 是「京杭大运河」整条目号、7-1973-3-009 是第七批「大运河」整条目号，非黑龙潭专属号——E28 :17 的表述（"子项"）是对的，上屏时不要把 6-810 写成黑龙潭编号。

**G6 🔵 E11 内部回声：17 行复述 E1 的「村北」表述，79 行自己纠正**
- `shucun_video/research.md:17`：「肖家河讲正黄旗营房**在村北**」；同文件 :79：「v1 说肖家河"正黄旗营房在村北"——官书原文作"蕭家河"……"北"是方位词，**不是"村北"这一称谓**」。17 行的 E1 概括沿用了被 79 行废弃的说法。

**核过无矛盾的跨集口径（采样）**：永乐大钟 1607 迁万寿寺/天启置地/1743 迁觉生寺（E9=E15=E19 三集逐字一致）；万寿寺 1577-1578、乾隆 1751/1761 两修（E9/E12/E15/E16 四集同源）；慈寿寺 1576 始工/1578 落成（E19 四源，外部维基/visitbeijing 同口径）；畅春园 1684 始建+「澄心园改畅春园」DISPROVEN（E14=calibration sanshiwuyuan.py 一致）；外火器营 1688/1691/1770/1773 年份链（E10=suburbs.py 逐字一致）；圆明园八旗护军营 1724（E7=banners.py 一致）；广源闸 1289/1292 双徽证据分级（E16 定式，E8 不冲突）；杨六郎：六郎庄「驻兵纪念说」FOLK_LEGEND（pingyuan.py prop_llz_yangliulang）与挂甲屯「挂甲说」DISPROVEN（guajiatun.py）是两个不同命题、状态各自成立；E9 卷次「卷100→卷77」回写**已完成**（dazhongsi.py:105-109，E15 头部「遗留任务」为陈旧记载）。

## 4. id 体系（任务③）

**健康面**：74 个 toponym 无重复 id、`predecessor_toponym_id` 无断链、无环；校准层 107 个 entity id 无跨模块重复；166/163 proposition↔adoption 除下述 3 条外一一对应；0 条 `inference_method` 占位符；subject/entity/source 引用 0 悬空（含对 extractor 注册表的复核——首轮报出的 `top_sifangpujue` 缺失经查是我方首轮未并 extractor 注册表，复核后不存在）。

**P1 🔴 十方普觉寺簇 predecessor 方向整体倒挂**（extractor.py:626-632）：schema 语义是「直接承袭的**前序**地名」（ontology/schema.py:53），builder 以 `evolvedFrom` 落图（builder.py:84）。现在 兜率寺(唐)/寿安山寺(元)/昭孝寺(元)/洪庆寺(元)/永安寺(明)/卧佛寺(俗) 六个节点的 pred 全部指向 **雍正十二年（1734）才有的** top_sifangpujue——元唐明的名字「承袭」了清朝的名字，时间方向反转。对照正确样板：top_wutasi(vulgar) pred=top_zhenjuesi(明 1473) 方向就对。应把链条改为 兜率寺→寿安山寺→昭孝寺→洪庆寺→寿安禅林（缺，需新增）→永安寺→十方普觉寺→卧佛寺。

**P2 🟡 3 条 PROPOSITION 无 ADOPTION**（schema 层要求逐条采信）：`banners/prop_jry_structure_split`、`xishan/prop_xs_wenquan_split`、`xishan/prop_xs_fhl_split`——三条都是 GPT审3-x 新增的实体分立命题，补了命题没补采信。statement/inference_method 本身质量高，只欠 adoption 记录。

**P3 🟡 UNSUBSTANTIATED 的 confidence 语义双轨**：同一 status 下 8 条用「命题为真的置信」（0.05–0.30），5 条用「禁令置信」（0.85–0.95）：dajuesi `prop_e24_magnolia_age` 0.95、shifangpujue `prop_e26_offer_temple_as_history` 0.90、taizhouwu `prop_excavated_yuan_wharf` 0.95、wutasi `prop_e25_suming_year_unknown` 0.90、wutasi `prop_e25_qianlong_bihuang_rename` 0.85。下游若按 confidence 排序会把「玉兰辽代所植」排到多数 VERIFIED 命题（最低 0.70，urban/prop_zgc_kecheng）之前。建议统一为「命题为真的置信」并把 5 条降到 ≤0.30，禁令语义已在 rationale 里表达，无需双载。另：6 条 VERIFIED confidence=1.0（guajiatun×3、taizhouwu×3），建议封顶 0.99 留认知余地。

**P4 🟡 `unit_shengshui_court` 把存疑考释建成定论且寺名存疑**（extractor.py:300-306）：description「金世宗**大安寺**、章宗圣水院，为香山最早之皇家敕建行宫水院」+ `valid_start_year=1186` 精确系年。而 corpus/era4_liao_jin.md:47 同一考释标「**通行考释作今香山寺**——存疑」。外部通说：金大定二十六年（1186）世宗赐名「**大永安寺**」（见维基/多家：金代香山寺即大永安寺，非「大安寺」）——单元描述里的寺名疑少一「永」字，且存疑考释在单元层被写成无保留事实。建议：description 加「通行考释」限定，寺名回查《金史》。

**P5 🔵 `top_sifangpujue` id 拼音脱 h**：standard_form「十方普觉寺」拼音 `shí fāng pǔ jué sì`，id 却是 **sifang**（ extractor.py:626，全库一致使用）。id 合法但任何人按拼音猜 `top_shifangpujue` 都会落空。已在 export 缺失（§2）修复时一并斟酌（改名成本 vs 现状一致性，二选一即可）。

**P6 🔵 30/166 条 PROPOSITION `alternative_explanations` 为空**：字段契约写明「禁止只写一种解释」（ontology/epistemic.py:233-235）。全清单：banners×4、dajuesi×1、gaoliang×1、guajiatun×3、sanshiwuyuan×1、settlements×4、suburbs×7、taizhouwu×2、urban×2、wutasi×1、yuanmingyuan×3（各 id 见附表）。多为词源/建置类单一解释；不逐条断言有实错，但批量违反字段契约，建议逐条补「无他说/存X说」的显式记载。

## 5. 全库国保批次表（任务④，独立完成，与 KBAuditQingModern 结果可互证）

| 单位 | 出处集 | 库内表述 | 批次/公布日 | 编号 | 独立外核 |
|---|---|---|---|---|---|
| 真觉寺金刚宝座（五塔寺塔） | E25 | 第一批，1961-03-04；**首批无编号，禁引「1-75」** | 1 (1961) | — | ✓ 制度判断正确（编号体系 1982 第二批起施行） |
| 十方普觉寺（卧佛寺） | E26 | 第五批 2001-06-25，5-205（「引用式，非名单原文」） | 5 (2001) | 5-205 | ✓ 与名单行「205｜11｜十方普觉寺｜清」自洽 |
| 大慧寺 | E21 | 「今全国重点文物保护单位」（未写批次） | 5 (2001) | 5-204 | ✓ 维基文库第五批通知/新京报 |
| 觉生寺（大钟寺） | E9 | 第四批 1996-12-27，4-166 | 4 (1996) | 4-166 | ✓ |
| 万寿寺 | E15 | 第六批 2006-05-25，序号307·Ⅲ-10·时代栏「清」 | 6 (2006) | Ⅲ-10 | ✓ 与 6-0307-3-010 换算自洽 |
| 大觉寺 | E24 | 第六批 2006-05-25（国发〔2006〕19号） | 6 (2006) | Ⅲ-6 | ✓（北京日报/文物局页） |
| 健锐营演武厅 | banners.py | 第六批（国发〔2006〕19号），「编号Ⅲ-9」 | 6 (2006) | Ⅲ-9 | ✓（外部 3-9 / 6-0306-3-009） |
| 未名湖燕园建筑 | E20 | 第五批 2001-06-25，5-475，近现代 | 5 (2001) | 5-475 | ⚠️ E20 自标「名录原文页待核」 |
| 景泰陵 | E17 | 第五批 2001-06-25（1979 市保先行） | 5 (2001) | 未引编号 | 批次正确；未核编号 |
| 慈寿寺塔 | E19/era6 | 第七批 2013，7-0711-3-009（编号711），时代「明」 | 7 (2013) | 7-0711-3-009 | ✓ |
| 高粱闸/广源闸（大运河子项） | E8/E16 | 第七批 2013「大运河」北京市 11 处组成之一；禁裸写 UNESCO、禁「独立国保」、名称米字底 | 7 (2013) | 7-1973-3-009（大运河整条目） | ✓ 全库最严谨的口径 |
| 黑龙潭及龙王庙 | E28 | 大运河子项 6-810（2006）→并入 7-1973（2013）；另 1984 第三批市保；**但 :141 误写「2003 年」** | 6→7 | 6-810 / 7-1973-3-009 | 批次对；年份见 G5 |
| 辛亥滦州起义纪念园 | E28 | 第六批 2006-05-25，6-886（自标「须与原件复核」） | 6 (2006) | 6-886 | 未独立复核（E28 已自挂待核） |
| 恩佑寺/恩慕寺山门 | era7_qing.md:11 | 「两处**国保**」 | — | — | 🔴 **错级**：外部+ E14 均为北京市文保（G1） |
| 龙背村白浮堰 | era5_yuan.md:3 | 以「**全国重点文物**实物勘测报告」为核心依据 | ? | ? | 🔵 **核不出**：外部只能证昌平白浮泉遗址（九龙池、都龙王庙）1990 市保→2013 随大运河国保；海淀龙背村段堰体是否属第七批「大运河」11 处组成，无法从可得来源确认。需回查北京市文物局 11 处清单后才能定 era5 措辞 |
| 白家疃 | E27 | 境内无国保，禁任何「X-YYY」编号（V-NC07） | — | — | ✓ 纪律正确 |

编号体系结论：全库**没有**给第一批国保编号的实质违规——「1-75」仅作为负控制命题的否定对象出现（shifangpujue.py:358 DISPROVEN 带反驳证据；wutasi.py:23 红线）。真实的两处问题就是 G1（错级）和 G5（错年）。

## 6. 系统性模式（最重要）

1. **「修正传播链」在导出层断裂（本轮唯一致命模式）**：本轮 61 条 VERIFIED 的整改、E26/E27 的词条，都只落在 `extractor.py`/calibration（开发者可见层），运行时 `entities.json→TTL→query.py` 冻结在 10-03 之前状态。伪引文在「真源」DISPROVEN、在「运行时」VERIFIED——同一个史实在库内两层说法相反，这正是横切审计要抓的矛盾，只是发生在层间而非集间。*修法*：导出脚本化 + 双向一致性断言（当前 builder 只进不出，extractor 无人导出）。
2. **订正不同步到注释/建模层**：E26 的「跨朝代名号错置」在 research 里 2026-10-04 当天订正，extractor 注释链仍是订正前文本（G2），且 predecessor 建模方向整体倒挂（P1）——一份错误可以同时活在注释、toponym 链、导出层三个位置，各自状态不同。每次研究档订正需要一张「要同步哪些层」的清单（研究档→calibration→extractor→export→corpus）。
3. **confidence 字段语义双轨**（P3）：UNSUBSTANTIATED 下 0.05 与 0.95 并存且含义相反，属「判据问错了问题」的近亲——字段在测「我们对处置的把握」还是「命题为真的概率」，两种用法都在库里。
4. **corpus 时代文件不进集级订正的回写清单**：E14 冻结了「山门=市保」，回写任务只列了 calibration 条目，没覆盖 era7 行文（G1）；E28 证伪了 era4 香水院条，era4 已修（正面案例，说明回写做得到），era7 漏网——模式是回写清单按「动过的数据结构」列，不按「哪里还有旧说法」列。建议每集交付前对 corpus 全文跑一次该集红线词的正则回扫（如「国保」「香水院」+地名）。
5. **正面资产（必须保持）**：跨集数字冻结链（1607/1743/1576/1577/1688/1691/1770/1289/1292）在九个相关集里零冲突，靠的是「冻结口径+出处集显式引用」机制；DISPROVEN 硬阻断、负控制命题、「1-75」陷阱防御均到位。本轮横切没有发现任何**已交付成片之间**的史实矛盾——矛盾全部集中在 KB 内部各层之间。

## 附：P6 空替代解释 30 条 id 清单
banners: prop_camp_count, prop_huojunxiao, prop_zhenghong_anhe, prop_shucun_etimology / dajuesi: prop_e24_three_rebuilds / gaoliang: prop_zhuozhou_not_bridge / guajiatun: prop_efucheng_site_guajiatun, prop_wuyingxiong_princess_marriage, prop_yangyanzhao_hebei_defense / sanshiwuyuan: prop_ccy_qinghua_guzhi / settlements: prop_xsq_flag, prop_dyz_no_imperial_gift, prop_qishierfu_legend, prop_qlq_gangnian / suburbs: prop_dagongmen_zhengdian, prop_shanmianhu_chunxia, prop_shanmianhu_counts, prop_huoqiying_not_fire, prop_neiwai_ying, prop_jingqi_waisanying, prop_zongji_vs_diming / taizhouwu: prop_daizhou_establishment, prop_daizhou_epitaph_qingshuidian, prop_heilongtan_rain_praying / urban: prop_tly_neijian_yuannei, prop_zgc_kecheng / wutasi: prop_e25_stele_only_proves_pagoda / yuanmingyuan: prop_1860_not_extinction, prop_sansanyuan_aggregate, prop_minguo_park_unproven

## 核过但无问题的项
- DISPROVEN 硬阻断与反驳证据完整性（31/31）；hypothesis 证据 id（7/7）；calibration 107 entity id 无重复；74 toponym 无断链无环；`fact_id`/`source_id`/`subject_id` 引用 0 悬空；`inference_method` 无占位符；PROPOSITION↔ADOPTION 除 P2 三条外一一对应；corpus/era4 香水院证伪已回写；era6 慈寿寺塔编号与 E19 一致；E9 卷次回写已完成；E18 与 E23 对杨六郎传说的双命题建模（FOLK_LEGEND vs DISPROVEN）语义各自成立；E25「避讳改名」UNSUBSTANTIATED 处置为全库纪律样板。
- 备注：任务简报举例的 `dingguosi/xiaojingqu/zhangjiatun` 目录在仓库不存在，实际 27 集 research.md 全部覆盖于上表（E1/E2 共用 anheqiao_video；E1 肖家河独立 research 档未在库内找到，其结论经由 E11:17,79 间接可见）。
