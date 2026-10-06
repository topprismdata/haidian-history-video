# 知识库四路审计 · 修复处置账本

- 建立日期：2026-10-04（依 `.superpowers/sdd/three-stage-review-workflow.md` 收尾件要求补写）。
- 对照报告（`.superpowers/sdd/`）：
  - `kb-audit-era0-era4.md`（KBAuditPreHistory，P01–P35）
  - `kb-audit-yuan-ming.md`（KBAuditYuanMing，R1–R10 / Y1–Y11 / B1–B7）
  - `kb-audit-qing-modern.md`（KBAuditQingModern，R1–R12 / Y1–Y9 / X1–X8 ＋ 国保全局核对表）
  - `kb-audit-cross-cutting.md`（KBAuditCrossCutting，§2 导出断裂 / G1–G6 / P1–P6 / 系统性模式）
- 信息来源：`git log --oneline -8` 主处置 commit——**f0e5ba6**（横切审计：隔离区＋闸门＋era5 回灌）、**344b819**（E27 字源入库 commit **捆绑落地了元明/清现代两 agent 的半成品 corpus 修复**）、**e2e2bd2**（承接配额中断 agent 收尾：era0-4 伪引文全清＋extractor＋数据重导出＋QUARANTINE Q-010..Q-024，1207 passed）、**0e2638d**（E26 修复 commit 内含横切 G7/G2/G1）——＋四份报告原文＋**对当前工作树逐条回查验证**。
- 工作树未提交项（待 Main 统一提交，本账本按「已改未提交」记）：`haidian_kg/evaluation/holdout_v1.jsonl`（P14 卷次 101→106×4 段、96→95×3 段）、`haidian_kg/CHRONOLOGY_MASTER_REPORT.md`＋`docs/superpowers/{plans,specs}/2026-10-02-*` 3 件（P34 文档层订正注）、`dajuesi_video/narration/*`＋`research.md`（P33 辽圣宗→辽道宗及 TTS 配套）。
- 处置取值：**已修**（注明 commit/Q 编号与验证位置）/ **部分采纳**（主体已修、残留项注明）/ **顺延**（写明理由）。KB 侧本轮**无驳回案例**（审核与修复方向零冲突）。

---

## 〇、执行史与 commit 归属（含配额中断事故）

1. 四路审计并行只审不改 → 产出四份报告。
2. **era0–era4 段由 FixKBPreHistory 完成**：fixed 清单要点——①era4 大觉寺辽碑「大安四年1088/碑名/碑文」三重伪改判咸雍四年（1068）《暘臺山清水院創造藏經記》＋邓从贵施财印藏经（Q-004，含**干支回验**前置检查：1088=戊辰 vs 碑末「嵗次戊申」一算即破）；②《金史》卷24 芙蓉殿整句伪＋钓鱼台「章宗」伪→卷95 实文（Q-005）；③era1–era3 一级书证伪引文五例（封蓟两句拼装＋乐记漏「未及」／汉书广阳国户口虚增＋沿革方向反／三国志官号卷次灌溉数三错／隋书临朔宫无「置宫」文／两唐书带州置年与寄治错置）（Q-006）；④焦府君墓志「查无此志」降 UNSUBSTANTIATED（Q-007）；⑤遗光寺新石器「出土物」查无著录降存疑（Q-008）；⑥「北京水利史志研究1995」查无实书、太舟坞两假说一律 CONTESTED（Q-009）；⑦数据层同步：extractor（宛平析津开泰元年1012、清水院 feat_yangtaishan 空间锚定、临朔宫伪坐标撤为[0,0]、克盉「令克侯于匽」、装饰品共141件其中石珠7枚、上宅/王府井 toponym 各建、王恭厂 Wetland 类型订正等）＋ tests/era0-4 断言同步（**错误引文曾被写成断言受回归保护，本次连测试一起改**）＋ holdout 卷次映射。corpus era2/era3 部分随 344b819 落盘，era0/1/4 与 extractor/tests 随 e2e2bd2 落盘。
3. **元明段（FixKBYuanMing）与清现代段（FixKBQingModern）两个 agent 完成大部分修复但死于配额**，半成品散落工作树：corpus era5/6/7/8 的订正块、QUARANTINE 续编条目、extractor 部分改挂。**Main 接手收尾**，标志性收尾件＝`attest_huoqiying_record`（extractor.py:1936-1955 实测）：外火器营「四千间」伪句剥离——`evidence_level=L6_DISPROVEN`＋`epistemic_status=DISPROVEN`，quote 换可核的「乾隆三十五年改移外火器营于蓝靛厂，设枪炮演武场」，notes 记 E10 冻结口径（只报分项：官廨千余/炮甲连房六千余/门楼三千一百余）与卷次存疑（卷98 未核，E16 直核相关卷为卷73）。两 agent 的 corpus 半成品随 **344b819** 一并落盘（该 commit 标题是 E27 字源，实际捆绑了元明清 corpus 修复——读 commit message 判断处置时会漏，特此注明），extractor/数据/测试收尾随 **e2e2bd2**。
4. 横切 G7/G2/G1 的数据层修复随 **0e2638d**（时间上早于 f0e5ba6，因 E26 修复与横切审计并行）。

---

## 一、era0–era4 段（P01–P35，FixKBPreHistory）

| 编号 | 条目 | 处置 | 证据 |
|---|---|---|---|
| P01 | 大觉寺辽碑年代/碑名/碑文三重错 | **已修** | Q-004。corpus/era4_liao_jin.md §1.2 整段重写（实测 ：29 碑名＋志延＋邓从贵），e2e2bd2 |
| P02 | 1088 传染链（extractor/data/tests） | **已修** | Q-004。extractor unit_qingshui_court/attest 同步；tests/test_era4_liao_jin.py 断言反转为 1068＋干支互验前置（:30,:66-68 实测）；entities.json/ttl 重导出（e2e2bd2 stat 323/301 行） |
| P03 | 《金史·地理志》宛平县条芙蓉殿伪引文 | **已修** | Q-005。「有玉泉山行宮」实文保留为 L2，芙蓉殿 UNSUBSTANTIATED |
| P04 | 钓鱼台卷次96→95＋「章宗」伪 | **已修** | Q-005。corpus §1.6＋extractor attest_diaoyutai_dijing；holdout 钓鱼台段 96→95（已改未提交） |
| P05 | 《三国志·刘靖传》伪引文＋水经注卷次＋灌溉数编造 | **已修** | Q-006。改挂《水经注》卷14 鮑丘水引《刘靖碑》，灌溉数改「岁二千顷，后改定五千九百三十顷」（extractor:101-102 订正注实测） |
| P06 | 刘弘重修系年泰始元年错 | **已修** | Q-006。改元康四年受命/五年刊石（corpus era2） |
| P07 | 《汉书》广阳国户口虚增＋沿革方向反 | **已修** | Q-006。改实文「户二万七百四十，口七万六百五十八」＋「高帝燕國→元鳳元年為廣陽郡→本始元年更為國」 |
| P08 | 《汉书·地理志上》「幽州刺史部」伪句＋卷次归属错 | **已修** | Q-006。 |
| P09 | 《隋书·炀帝纪》临朔宫伪引文 | **已修** | Q-006。改乙亥/庚午实文，「置宫」拆出推测层 |
| P10 | 带州双唐书伪引文＋焦府君墓志存疑 | **已修** | Q-006＋Q-007。两唐书改实文（贞观十九年置/神龙初放还/州陷后寄治清水店）；墓志 attest_tang_jiao_epitaph→UNSUBSTANTIATED；带州 unit `valid_start_year=645`（extractor:313 实测） |
| P11 | 《史记》合成引文＋《乐记》漏「未及」翻转 | **已修** | Q-006。两句各回实文＋加注两传世文献矛盾 |
| P12 | 燕并蓟迁都 L3 VERIFIED 过度＋《水经注》转引链伪造 | **顺延** | corpus/era1:29-33 实测：标题仍「约前7世纪」、《水经注·漯水》引《战国策》苏秦伪转引链原样。理由：本轮以伪书证清剿为主，推论层降级（「通行推定，存疑」）未做 |
| P13 | 宛平/析津县名 938→1012 错置 | **已修** | extractor:1019-1027 订正注实测「宛平、析津二县名始于开泰元年（1012）」，e2e2bd2 |
| P14 | 水院条卷次101→106＋holdout 映射错 | **已修** | corpus era4:79-80 订正注（已核卷101 全文无水院字样）；holdout_v1.jsonl 7 段 rxjwkc_juan 101→106、96→95（**已改未提交**，git diff HEAD 实测）；底本异文备忘（六院/八院）按「勿互改」处理 |
| P15 | 金中都「天德三年四月筑」失真 | **已修** | corpus era4:49-51 实测订正块（三月增广燕城） |
| P16 | 带州三层口径互搏＋1995 水利文献查无 | **已修** | Q-009。hypo_taizhouwu_dock/tang 一律 CONTESTED、disproven_by 置空、unit 改挂中性 feature（extractor:309 area「改挂中性的 feat_gaolianghe…三说并存」实测） |
| P17 | 清水院空间锚定错误（挂香山） | **已修** | feat_yangtaishan 新设，unit_qingshui_court 改挂（extractor:177,346-347 实测），e2e2bd2 |
| P18 | 遗光寺新石器「出土物」查无著录 | **已修** | Q-008。attest_yiguangsi_axe 降存疑＋feat 同步；「海淀最早实物考古信史原点」撤回 |
| P19 | 雪山遗址属地/分期年代不合通行口径 | **顺延** | corpus/era0:57 实测仍「南口镇雪山村」。理由：属考释对表（通行分期两端均不合），需专项核对后改，本轮未做 |
| P20 | 幽州都督府引文失真 | **已修** | corpus era3:34-37 实测实文＋「旧稿…于原文无此文」订正块 |
| P21 | 《隋书》涿郡「开皇初废郡」失真 | **已修** | corpus era3:21-22 实测订正块（「大業初府廢」） |
| P22 | 临朔宫伪精确坐标＋推测混级 L2 | **已修** | extractor:112-118 实测：坐标[0,0] 占位＋label「遗址未定位」＋订正注「伪精确度比未考得更有害」 |
| P23 | 克盉铭文引字失真 | **已修** | extractor:883-887 实测「令克侯于匽…用乍（作）宝尊彝」43 字订正注 |
| P24 | 「141件穿孔石珠」措辞误读 | **部分采纳** | extractor:787-788 已改「装饰品共141件（其中穿孔石珠7枚，另有…）」；**corpus era0:25 残留旧措辞「出土 141 件穿孔石珠…」未同步** |
| P25 | 东胡林「最早陶容器」缺「之一」限定 | **顺延** | corpus/era0:43 实测原样。理由：限定词级微调未排入本轮 |
| P26 | 上宅「最早定居农业/首支」绝对化 | **顺延** | extractor label 实测仍「北京最早定居农业陶器与石磨盘聚落」。理由：同 P25，绝对化降级批次顺延 |
| P27 | 「最早天然用火」绝对化 | **已修** | extractor:777 订正注实测：降「控制用火的早期重要证据」，记灰烬层再检争论 |
| P28 | 上宅/王府井 attest 挂 top_zhoukoudian 接线错误 | **已修** | extractor:652-655,795 订正注实测：各建本名 toponym |
| P29 | 王恭厂 Wetland 类型错挂＋钓鱼台 Wetland 无出处 | **已修** | extractor:68 订正注实测（P29 类型订正） |
| P30 | 高梁河/高粱水两物＋积水潭后世地名 | **已修** | corpus era2:65-66 实测订正块（加「今」字限定＋同水两名合并表述＋水经注流向为准） |
| P31 | 「全境隶属广阳国蓟县」过度 | **已修** | corpus era2:23 实测订正块（整境断言超出史载精度，改「主体」口径） |
| P32 | 「现存金代行宫园林地标」易读作遗构尚存 | **已修** | corpus era4:126 实测「因金代旧迹得名的地标，不得读作金代行宫遗构尚存」 |
| P33 | E24 旁白「辽圣宗咸雍」年号错（道宗） | **已修（已改未提交）** | dajuesi narration/all.json p02 实测「辽道宗咸雍四年」；durations/narration.ts/research.md 配套改动在工作树，待统一提交 |
| P34 | 文档/规划层残留（大安四年碑/芙蓉殿/八院考实） | **已修（已改未提交）** | CHRONOLOGY_MASTER_REPORT.md Era4 行＋3 份 docs/superpowers 文件实测已加订正注（Q-004/Q-005 挂钩），git diff HEAD 7 行 |
| P35 | 卧佛寺传说始建钉 627 硬起始年 | **顺延** | extractor unit_sifangpujue_temple 实测仍 `valid_start_year=627`。理由：与横切 G2 残留同处（见 §四），实体层「传说性始建不锁年」改造顺延 |

小结：**已修 29 / 部分采纳 1（P24）/ 顺延 5（P12、P19、P25、P26、P35）**。系统性模式落地点：伪引文机械负控制＝`tests/haidian_kg/test_fake_quote_detector.py`（f0e5ba6 建 7 项，e2e2bd2 扩充）；干支回验＝Q-004 起为入库前置检查（era4 测试已固化单例，全库通用闸顺延）。

---

## 二、元明段（era5/era6，FixKBYuanMing → 配额中断 → Main 收尾）

| 编号 | 条目 | 处置 | 证据 |
|---|---|---|---|
| R1 | 《元史·郭守敬传》引水引文跨段拼接伪句 | **已修** | Q-010。corpus era5 §1.2 整段替换为直核原文「別引北山白浮泉水…自西水門入城」＋新增禁语红线（「白家圈/石佛村/西直门」禁回填） |
| R2 | 「海店」八月→三月＋大都时序错置 | **已修** | corpus era5:19-21 实测订正块（三月五日发燕京，六日午憩海店；距金中都旧城廿里；赴开平） |
| R3 | 《元史·廉希宪传》葬地/畏吾村伪引文（E21 已判死未回灌） | **已修** | Q-001。f0e5ba6 回灌 era5 §1.3，Level 2 VERIFIED→2+3/UNSUBSTANTIATED |
| R4 | 《宛署杂记》「海甸」伪句＋1612 勺园塞进 1593 书证 | **已修** | Q-013。corpus era6 §1.1 引文换卷五街道实文（北海店），勺园移出书证，「园林之祖」降级 |
| R5 | attest_wanping_niulanzhuang 书名错挂＋引文伪造 | **已修** | Q-013/Q-020。extractor 由 FixKBQingModern 同步（QUARANTINE Q-013 回灌栏原话），source_title 改「宛署杂记卷五」 |
| R6 | 「广源闸重修碑记」查无此碑 | **已修** | Q-011。改挂《元史·河渠志》「其壩牐之名曰：廣源牐」（E16 直核），id 保留换书证实体 |
| R7 | 《明史·神宗本纪》万寿寺敕建伪句 | **已修** | Q-012。改挂张居正《敕建万寿寺碑文》（经日下旧闻考卷77 转引）三源 |
| R8 | 碧云寺正德扩建「魏彬」错误 | **已修** | corpus era6:62-63 实测订正块（御马监太监于经，嘉靖初下狱死） |
| R9 | calibration 命题层仍是 E26 订正前错误六名链 | **顺延** | 🔴 **现行 calibration/shifangpujue.py:319-330 与 :402-412 实测：`prop_e26_six_names_chain` statement/inference_method 及 ADOPTION rationale 仍为「…明正统八年·寿安山寺…六个名号」VERIFIED 0.92**——Appellation 层（已修七名）、extractor toponym 层（已建 top_shouanchanlin）、已交付成片三层均对，唯独命题/采信层漏改，与报告警告完全一致。理由：E26 修复（0e2638d）改了 Appellation/facts/测试，命题层同步在两 agent 配额中断中丢失，收尾时未扫到。**建议 Main 优先补修（本轮唯一残留的 🔴）** |
| R10 | 龙背村白浮堰「全国唯一存世」三重证伪 | **已修** | Q-015。attest_longbeicun_weir_site→L6_DISPROVEN/DISPROVEN（保留原文）；era5 §1.4bis 新增判死留档段；「白浮泉遗址（昌平龙山）」为正确国保表述 |
| Y1 | 广源闸「至元二十六年建」拍平双徽口径 | **已修** | corpus era5:54 实测「1289：《水部备考》转引称建（成书年代未核，转引层）」双徽并陈；feat 描述改口径 |
| Y2 | hypo_xisanqi_manchu DISPROVEN 缺真反驳证据 | **顺延** | extractor:2377-2379 实测：仍 `disproven_by=["attest_shuntian_xisanqi"]`＋DISPROVEN，未按建议降 CONTESTED/换真源。理由：f0e5ba6 建闸门时只判了「本轮唯一实锤划错」的登记，替换反驳书证（尹钧科文等）需重新直核，顺延 |
| Y3 | 慈寿寺「永安寿塔」＋「光□间」编码损坏 | **已修** | corpus era6:84,88 实测「永安万寿塔」＋异文注（帝京景物略作「永安壽塔」可注为异文）；乱码字符全文件 0 命中 |
| Y4 | 西顶「万历敕建广仁宫」名号时代错挂 | **已修** | corpus era6:93-95 实测订正块（明建西顶娘娘庙，清康熙四十七年改名广仁宫） |
| Y5 | 中关村条整段 VERIFIED 过度＋「中国硅谷」时代错乱 | **已修** | corpus era6:60,68-70 实测整条降级块（现代考述层/L4 命名链/硅谷句删） |
| Y6 | 1913/1915 两图捏成一张＋「取代」夸大 | **已修** | corpus era5:90-94 实测（两图拆分、1913 二万五千分之一「中关」零星出现、1915 五万分之一魏公村定名、不得混为一图）；extractor:1357 音转链 canon 同步；corpus era8:3,11-12 同口径 |
| Y7 | 《大明会典》「五行百户为所」讹文 | **已修** | Q-014。corpus era6 §1.2 换明史卷90 canonical 条文 |
| Y8 | 碧云寺卷次104→87 疑误＋耶律楚材世系越级 | **已修** | corpus era5:100-103 实测订正块（卷八十七·郊坰西七＋御制碑文直核；世系对齐 xishan CONTESTED） |
| Y9 | 成府「相传陈氏别墅」标 VERIFIED L4 | **顺延** | extractor:1700-1710 实测仍 `epistemic_status=VERIFIED`。理由：相传句降 FOLK_LEGEND/CONTESTED 属批量语义清理，顺延（与横切 P3 同批） |
| Y10 | wutasi/shifangpujue 校准模块书源层全挂 src_guobao_5th | **顺延** | 实测 calibration/wutasi.py:67（div_e25_guobao1_zhenjuesi 第一批 volume 挂第五批源，批次自相矛盾）、shifangpujue.py:73/76/81（雍正碑、元史英宗 division 仍挂 src_guobao_5th）原样；bibliography.py 既有 src_yuanshi 未启用。理由：Q-003 修了引文真伪，**归属层**（挂靠哪个 DIVISION/SOURCE）整体顺延 |
| Y11 | era5 无《授时历》条目 | **已修** | f0e5ba6 补 era5 §1.5：1276 奉命修历/1280 历成/365.2425 日，并显式标注「不与京西水系直接挂钩」 |
| B1 | 元史引文插逗号＋attested_string 配错句 | **顺延** | calibration/shifangpujue.py:97 实测 verbatim_quote 仍作「冶銅五十萬斤，作壽安山寺佛像」（带逗号；Q-003 留档亦用此形）。理由：《元史》原文无逗号、屏显引文逐字纪律要求去逗号，但该句同时是 Q-003 判死留档形——去逗号须连 QUARANTINE 原文与测试断言一起动，顺延 |
| B2 | prop_e26_in_xiangshan refuting_fact_ids 混入雍正碑铜佛条 | **顺延** | calibration:387/:456 实测条目仍在，未见订正注。理由：反驳指针语义复核（横切 P6 同族）顺延 |
| B3 | hypo_zgc_chenyuan CONTESTED 却带 disproven_by | **顺延** | 未见订正（与 Y6 地图拆分联动；Q-023 只处置了 1953 批复伪件侧）。理由：图证强度重裁需先落 1913《京西图》直核，顺延 |
| B4 | prop_xs_qishierfu_suyan 反驳指针挂错物 | **顺延** | 未见订正（处置结论本体 era6 §1.3 早已订正并经横切核过 ✓，仅检索证据指针未改挂）。理由：指针语义改造随 B2 同批 |
| B5 | 「不可动摇！」「重要空间见证」感叹号修辞 | **已修** | corpus era5 检索「不可动摇」0 命中（§1.1/§1.2 随 R1/R2 重写平实化） |
| B6 | 「御马监太监赵政」监属待核 | **顺延** | 未核《日下旧闻考》监属，条目未系年无冲突，维持待核状态 |
| B7 | 「万寿山瓮山前」时代混挂 | **已修** | corpus era5:62 实测订正注＋:187 新增红线「元代语境一律作『瓮山』」 |

小结：**已修 19 / 顺延 9（R9、Y2、Y9、Y10、B1、B2、B3、B4、B6）**。其中 **R9 为 🔴 残留**（唯一），其余顺延多为「降级批量清理/书源归属/反驳指针」类二阶修正。

---

## 三、清现代段（era7/era8-9，FixKBQingModern → 配额中断 → Main 收尾）

| 编号 | 条目 | 处置 | 证据 |
|---|---|---|---|
| R1 | 恩佑/恩慕寺山门误称「国保」 | **已修** | corpus era7:11 实测（1981 区保→2021 第九批北京市文保，分列 9-17/9-18，非畅春园遗址本体、更非国保）；calibration sanshiwuyuan.py 原本正确（库内两层矛盾消除）。横切 G1 同此 |
| R2 | 外火器营「四千余间」＋卷98 | **已修** | corpus era7 订正（分项口径，不给总数）＋extractor:574-579【R2 回灌】＋**attest_huoqiying_record DISPROVEN+L6（Main 收尾件，extractor:1936-1955 实测）** |
| R3 | 健锐营「碉楼数百座」 | **已修** | corpus era7:26 实测订正块（卷102 馆臣按「共计六十有七」，两说并存，现存数不列） |
| R4 | 《御稻米》张冠李戴（康熙≠乾隆诗） | **已修** | corpus era7:30 实测订正块（康熙《几暇格物编》条目，乾隆以御制诗咏京西稻） |
| R5 | 一亩园三处矛盾＋《御制文二集》拟托书证 | **已修** | Q-022。corpus era7:32 实测订正块（亲耕=传说层、耤田礼在先农坛 L1、建年不锁 1745/1723、拟托书证已撤）＋extractor attest_yimuyuan_qianlong DISPROVEN |
| R6 | 大有庄「御赐易名」作事实＋卷99 | **已修** | corpus era7:38 实测订正块（官书卷一百已用其名 L1；赐名降 L3 地方文史「据载」；竞争解释并存） |
| R7 | 民国地图三重失实（两图捏一张/「取代」/evt 1913 学堂叙事） | **已修** | corpus era8:3,11-12 实测（1913《京西图》二万五千分之一与 1915《实测京师四郊图》五万分之一拆分、「不得捏成一张」、渐见雅化两步走）＋Q-023（evt_zhongguan_euphemism 解除 occurred_year=1913） |
| R8 | 「等离子体学会先进技术服务部」漏「发展」 | **已修** | corpus era8:45 实测＋extractor:1785-1787 全名订正 |
| R9 | 1953 政务院文委批复查无＋石刻考纪年 1900 | **部分采纳** | 已修：Q-023（attest_zgc_1953_decision DISPROVEN＋新增 attest_zgc_1951_land 挂 1951 官方院史）＋Q-024（attest_zhongguan_eunuch_stele L6_DISPROVEN，recorded_year=1900 审计性保留）＋corpus era8:36,48 订正块＋Y7 等级标签对位。**残留（顺延）**：extractor `unit_cas_zhongguancun` 仍 `valid_start_year=1953`＋description「政务院确定之…科学城」（撤证未撤结论的实体层变体） |
| R10 | 「辅仁大学西山农林试验场」全库无源 | **已修** | corpus era8:23 实测【删条】块（全库无源、外部核不出、不得与辅仁混挂） |
| R11 | 六条同族拟托书证（觉生寺/苏州街/安和桥/北平地名通志/宛平县志沈榜/青龙桥卷99 水文） | **已修** | Q-016～Q-021 逐条：各 attest→DISPROVEN/L6 保留原文＋新增真书证（attest_jueshengsi_beiwen 碑文、attest_suzhoujie_xiaoting 啸亭杂录卷十、attest_qinglongqiao_rixia100 卷100 实文等） |
| R12 | 觉生寺第四批公布日 1996-12-27→11-20 | **已修** | calibration/dazhongsi.py:307-310 实测【R12 回灌】注（国发〔1996〕47号，维基文库原件已核） |
| Y1 | 「肖家河村北/长春园东北」方位称谓 | **顺延** | corpus era7:21 实测仍「正黄旗营房驻**肖家河**村北…正白旗营房驻长春园东北」。理由：官书原文（卷99「蕭家河北」/卷116「樹村東邊」）改写未落（E11 v2 已纠过同族表述，corpus 层漏网——横切系统性模式3 的实例） |
| Y2 | 柳浪庄环节 VERIFIED＋「清康熙年间」自加系年 | **顺延** | corpus era7:39-40 实测原链无订正标记。理由：与 Y1 同批（冻结口径回写 corpus 的漏网清单） |
| Y3 | 畅春园 1687 定年＋「焚毁」表述 | **顺延** | corpus era7:9-10 实测仍「康熙二十六年（1687）」单口径（E14 冻结为 1684 营建/1687 具驻跸条件双口径）。理由：同 Y1/Y2 批次 |
| Y4 | suburbs 引文内嵌「中顶/北顶（存，国保）」误标 | **顺延** | calibration/suburbs.py:358-368 实测：verbatim 原样保留（转录可留），但 translator_note 仍只有「五顶之首」等三条，**未加「文中『国保』与名录不符」注**。理由：下游引用传染风险未消除，补注顺延 |
| Y5 | 龙背村白浮堰（登记项，移交元层） | **已修** | ＝元明 R10/Q-015，已按「保护对象≠所在地点」处置 |
| Y6 | 「京西第一大庙会」最高级 | **已修** | corpus era7:33 实测订正块（降「著名」，并给出五顶中西顶的真实特殊性） |
| Y7 | 「工商登记一手档案」等级标签错配 | **已修** | corpus era8:48 实测订正块（1980 一节实引报纸二手，L2/L4 逐条对位） |
| Y8 | unit_wenquan_village 辽金 1150 起点未随 E28 撤证 | **顺延** | extractor:396 实测仍 `valid_start_year=1150`。理由：attestation 已 DISPROVEN（Q-002），「撤证不撤结论」的实体层同步顺延——与横切系统性模式3 建议的 qa_gate 新闸同批 |
| Y9 | 《圆明园史事编年》现代辑录混级 L2＋「副将」存疑 | **顺延** | corpus era7:22＋extractor:1488 实测原样（未改挂「清代档案，转引自现代辑录」层级）。理由：层级重挂需先核卷116「副将」词制，顺延 |
| X1 | 「五朝皇帝年均园居逾200天」混级 | **顺延** | corpus era7:13 实测仍在 L2 块内，未标「现代研究统计」 |
| X2 | 西三旗引光绪志「小旗分屯」疑现代解释回填 | **顺延** | extractor:1305,1860 实测原样（志书原文核对未做） |
| X3 | 光绪顺天府志 1885/1886 纪年口径混用 | **顺延** | extractor:1303,1681(1885)/1729(1886) 实测混用如故 |
| X4 | 「熙春园（清华园）」后世园名读进康熙史实 | **顺延** | corpus era8:21 实测原样 |
| X5 | 国函〔1988〕74号文号未直核 | **顺延** | era8 未见「文号待核」注记（R9① 的文件名已撤与 X5 是两件事） |
| X6 | 《中共中央进驻香山史料汇编》书名未检出 | **顺延** | 未见订正标记（事件本体审计已确认无误） |
| X7 | attest_guajiatun_chenyuan 引《宸垣识略卷十三》待核 | **顺延** | extractor:1542 实测原样（E23 冻结官书链为日下旧闻考卷76 按语，替换未做） |
| X8 | 正白旗营房三处措辞不统一 | **顺延** | 与 Y1 同源（corpus/extractor/官书卷116 三处），统一到卷116 原文的批次顺延 |

国保全局核对表（两报告互证）的处置说明：表中「✓」各行为审计确认无误，**无需处置**（颐和园/五塔寺/圆明园/大慧寺/未名湖/碧云寺/景泰陵/十方普觉 5-205/大觉寺/万寿寺/健锐营/慈寿寺/高粱闸广源闸大运河口径/第一批编号零违规扫描）；表中三项真问题处置为：恩佑恩慕（R1，已修）、中顶北顶（Y4，顺延，见上）、龙背村白浮堰（Y5→Q-015，已修）。

小结：**已修 14 / 部分采纳 1（R9）/ 顺延 14（Y1、Y2、Y3、Y4、Y8、Y9、X1–X8）**。顺延集中原因＝横切报告系统性模式1/3 的预言应验：**corpus 层回写清单按「动过的数据结构」列，不按「哪里还有旧说法」列**，era7 行文层（Y1/Y2/Y3/X1/X8）成为主要漏网带。

---

## 四、横切段（导出断裂 / G1–G6 / P1–P6 / 系统性建议）

| 编号 | 条目 | 处置 | 证据 |
|---|---|---|---|
| §2/G7 | 采信层修复未传播到运行时数据层（entities.json 冻结 10-03，伪引文运行时仍 VERIFIED） | **已修** | 0e2638d。`load_or_extract` 加 **mtime 比对自动重算**（extractor.py:2420-2440 实测 docstring「比对 entities.json 与 extractor.py 的 mtime，源更新即重算并回写」）＋ **`force_refresh()`**（:2442，`__main__` 入口默认走 force_refresh）；重新导出后 toponym 74→75、伪引文运行时为 DISPROVEN。**子项顺延**：审核建议的「extractor↔export 双向一致性断言进 CI」未建（tests/ 无 diff 断言测试，现仅 test_production_exports 旧档） |
| G1 | era7 恩佑/恩慕「国保」错级 | **已修** | ＝清现代 R1（corpus era7:11），0e2638d 同期发现、344b819 落盘 |
| G2 | E26 订正未同步 extractor 层（注释旧链＋「寿安禅林」缺位） | **部分采纳** | 已修：toponym 链重建（extractor:742-749 实测订正注＋top_shouanchanlin，方向 兜率寺→寿安山寺→昭孝/洪庆/寿安禅林→永安寺→十方普觉寺→卧佛寺，承袭方向全部正确）。**残留（顺延）**：unit_sifangpujue_temple（:368）description 仍为旧链「元至治元年改昭孝寺…明正统八年改寿安山寺」＋valid_start_year=627/2026 硬编码（≡era0-4 P35＋管线B4 同处） |
| G3 | E8 通惠河「1293 开凿」两处（应 1292 开工/1293 告成） | **顺延** | gaoliangqiao_video/research.md:80,:199 实测仍「1293 年开凿」。理由：已交付集 research 冻结档修订需走集级修订流程（含 QA 复跑），本轮 KB 收口未动集档 |
| G4 | E17 虚指 E8「于谦/夺门」（悬空跨集引用） | **顺延** | fenshi_video/research.md:26 实测原样。理由：同 G3（集档修订批次） |
| G5 | E28 黑龙潭「第六批 2003」错年 | **已修** | wenquan_video/research.md:141 实测「**2006-05-25（国发〔2006〕19 号）**…列第六批国保（6-810）」，e2e2bd2（该文件 2 行变更即此修） |
| G6 | E11:17 复述 E1「村北」被己身 :79 废弃 | **顺延** | shucun_video/research.md:17 实测原样。理由：同 G3/G4 批次 |
| P1 | 十方普觉寺簇 predecessor 方向整体倒挂 | **已修** | ＝commit 所记「G2 修复」：六节点倒挂重建为正序链＋补寿安禅林节点（extractor:743-749 实测方向正确；builder evolvedFrom 落图随 data 重导出生效） |
| P2 | 3 条 PROPOSITION 无 ADOPTION（jry_structure_split/xs_wenquan_split/xs_fhl_split） | **顺延** | calibration 全文检索三条 proposition_id 的 adoption 0 命中。理由：补采信记录属批量 schema 卫生，顺延 |
| P3 | UNSUBSTANTIATED confidence 语义双轨（0.05–0.30 vs 0.85–0.95）＋VERIFIED 1.0 未封顶 | **顺延** | dajuesi.py:280（0.95）/wutasi.py:309（0.85）实测原样。理由：语义统一（统一为「命题为真置信」＋5 条降 ≤0.30＋封顶 0.99）牵动全库 13 条，需单批 |
| P4 | unit_shengshui_court 存疑考释建成定论＋寺名疑漏「永」 | **已修** | extractor:371-378 实测降级订正注（八大水院=明人归纳非金代自述、今地对应无直证）；「大永安寺」实名已入 attestation（:2049-2054「大定二十六年三月，世宗幸西山，驻跸香山大永安寺」） |
| P5 | top_sifangpujue 拼音脱 h（id 合法但难猜） | **已处置（按建议二选一：保留现状）** | 审核明言「改名成本 vs 现状一致性，二选一即可」；随 G7 重导出保留 top_sifangpujue（extractor:738 实测），未改名 |
| P6 | 30/166 条 PROPOSITION alternative_explanations 为空 | **顺延** | 实测 `alternative_explanations=[]` 计数与报告一致（suburbs 7、guajiatun 3、taizhouwu 3、urban 2、settlements/banners 各 4 等）。理由：逐条补「无他说/存X说」显式记载属长尾清理 |
| 建议-1 | calibration 裁决→corpus/extractor 同步对账脚本 | **顺延** | 未建。本轮以 QUARANTINE「是否已回灌」栏＋fake_quote_detector 闸门替代部分职能 |
| 建议-2 | 每集交付前对 corpus 跑该集红线词正则回扫 | **顺延** | 未落（本轮 era7 Y1/Y2/Y3/X1 漏网即该闸缺位的直接后果） |
| 建议-3 | qa_gate 加「DISPROVEN/CONTESTED 的关联 entity/event 复查同步降级」闸 | **顺延** | 未落（清 Y8 温泉 1150、R9 残留 unit 1953 即活体案例） |
| 建议-4 | 名号 canonical 表（calibration 反哺 corpus） | **顺延** | 未建（永安万寿塔/广仁宫/魏公村音转已逐条手工修，机制未固化） |
| 建议-5 | DISPROVEN 增加「反驳命题」人工可读字段＋指针语义复核 | **顺延** | schema.py e2e2bd2 +6 行为 TEST_FOLLOWS_DATA 配套，未含此字段 |

小结：**已修 6 / 部分采纳 1（G2）/ 已处置-二选一 1（P5）/ 顺延 10（G3、G4、G6、P2、P3、P6＋建议 5 项）**。

---

## 五、Q-010/Q-011 编号撞车事故记录（任务指名）

- **经过**（依 Main 转述；发生在未提交的工作树现场，无 commit 级快照可回放）：元明段与清现代段两个修复 agent 并发追加 QUARANTINE.md 条目时，**各自从 Q-010 起编号**，两套 Q-010/Q-011 指向不同书证——编号撞车。Main 接手收尾时尝试**按时代段重排全部编号**，第一次重排失败（两 agent 的半成品条目正文与编号错位交叉，逐条搬移时正文-判死理由对应关系被打散，只能回滚）；最终按「以条目内容为准、编号就地顺延」的方案归位，即现行 Q-010《元史·郭守敬传》～Q-024 太监墓石刻考。
- **现行注册表可观察的合并痕迹**（工作树实测）：Q-001～Q-009 条目间有 `---` 分隔线与空行（f0e5ba6 原生风格），Q-010 起条目**无分隔线、格式紧凑**（两个配额中断 agent 的追加风格），且「处置规范/反面教材」章节被 Q-010 从中间插断——即重排后未做版式统一。
- **防再犯**：QUARANTINE.md「处置规范」第 5/6 条（标注是否已回灌＋进 DEAD_VERBATIM 闸门）已固化；**编号分配未加规则**，建议后续条目由 Main 单点分配或改用内容寻址 id（如 `Q-yuan-guoshoujing`），避免并发 agent 各自称号。

---

## 六、统计

| 段 | 条目数 | 已修 | 部分采纳 | 顺延 |
|---|---|---|---|---|
| era0–era4（P01–P35） | 35 | 29 | 1（P24） | 5（P12/P19/P25/P26/P35） |
| 元明（R10+Y11+B7） | 28 | 19 | 0 | 9（**R9🔴**/Y2/Y9/Y10/B1/B2/B3/B4/B6） |
| 清现代（R12+Y9+X8） | 29 | 14 | 1（R9清） | 14（Y1/Y2/Y3/Y4/Y8/Y9/X1–X8） |
| 横切（G7+G1–G6+P1–P6+建议5） | 18 | 6 | 1（G2） | 11（G3/G4/G6/P2/P3/P6＋建议5项） |
| **合计** | **110** | **68** | **3** | **39** |

- 注：横切 P5（id 保留现状）按审核「二选一」建议属已处置，计入已修栏；顺延合计 39（5+9+14+11）。
- 另有工作树未提交修复 3 件套（P14 holdout、P34 文档层、P33 dajuesi 旁白），已计入对应条目的「已修」并标注「待统一提交」。
- 驳回 **0**（四路审计结论与修复方向无冲突；f0e5ba6 唯一的「实锤划错」hypo_xisanqi_manchu 属元明 Y2，本轮为顺延非驳回）。
- 测试基线：f0e5ba6 后 1199 passed → e2e2bd2 后 **1207 passed**（era0-4 伪引文清零收口）。
- **遗留优先级建议**：①R9（元明）calibration 命题层旧六名链——唯一残留 🔴，且被 `prop_e26_six_names_chain` 的 VERIFIED 0.92 采信背书，任何以 calibration 为底本的下游挖掘都会复吸旧错；②「撤证不撤结论」三连（清 Y8 温泉 1150、R9清 残留 unit 1953、G2 残留 unit_sifangpujue 旧链）——同根模式，宜与建议-3 的 qa_gate 新闸一并修；③era7 行文层回写批（Y1/Y2/Y3/X1/X8）——corpus 红线回扫闸（建议-2）落地后一次清。
