# E26《十方普觉寺》管线与判据层对抗审核报告

- 审核人：E26AdversaryPipeline（独立对抗审核，未采信其他审核 agent 结论）
- 日期：2026-10-04
- 分工范围：3 类判据恒真检测、`qa_v2/` 全部模块（重点 normalize.py 本轮改动、checks_render.py 负控制）、`remotion-template/src/shifangpujue/` 槽位几何与文案、`assets/hist_shifangpujue/` 10 项资产防伪、成片 `/tmp/chemistry-video/out/shifangpujue.mp4` 逐页终态帧目视（8/8 页实际抽帧：页起点＋纯音频时长−0.2s）
- ⚠️ 路径说明：任务指定的 `e26-adversarial-evidence.md` 已被史实审核 agent（E26AdversaryEvidence）先写入，为避免互踩，本报告写至 **`.superpowers/sdd/e26-adversarial-pipeline.md`**。
- 方法声明：全部"恒真"指控均有可复现探针（本节引用的输出均为实际运行结果）；判据有效性用**内存变异**验证（pydantic 对象就地改，未落盘、未留任何测试文件）；帧证据在 `/tmp/e26frames/`（p1..p8.png 及 4 张局部放大图，可供复查）。

---

## 一、问题清单（按严重度）

### 🔴 C1 交付成片 ≠ QA 验证的渲染：P4 以旧版布局出厂，"双档 fail 0"不描述交付物

- **位置**：`/tmp/chemistry-video/out/shifangpujue.mp4`（mtime 09:23）vs `remotion-template/src/shifangpujue/data/slots.json`（09:30）、`pages/Page04.tsx`（09:28）、`data/pages.config.ts`（09:25）vs QA 帧 `/tmp/qa_frames/shifangpujue/p04.png`（09:31）
- **问题**：mp4 渲染于 09:23；之后 09:25–09:30 对 P4 做了「SVG 文字改纯图形＋槽位重定位」修复（Page04.tsx 注释自述的 E26 教训）；QA 帧在 09:30–09:32 用**修复后源码**重渲后跑出 fail 0。交付视频从未重渲。
- **证据（像素级）**：以 x=70..190 竖带测白色垫板行——交付帧 P4 tag 垫板下沿 ≈ y844，QA 帧 = 812，slots.json `p4_tag_verdict` = 762+50=812。交付帧里 `p4_axis_era_left` 槽（y900–936）**完全空白**（ink=0），而「寺·唐」半埋在 tag 垫板下（y≈804–836，「寺·唐」二字透底可见）、「贞观年间」悬在轴线上方 y≈868–884——即**出厂视频的 P4 轴标签不在任何槽位里、首行被白卡压住**。局部放大：`/tmp/e26frames/p4_left_zoom.png`。
- **建议**：①从当前源码重渲 mp4 并重跑双档 QA 后再算交付；②给 qa_v2 增加**成品新鲜度闸门**：out mp4 的 mtime 必须 ≥ 全部输入（run.py 已有 `_source_freshness` 机制，只用于帧缓存，没有管成品）；③本次事故的根因是"修完源码没回炉成片"，应写进 series_registry 教训（E15"整批未写盘"的同族：**验证对象与交付对象不同源**）。

### 🔴 C2 资产防伪红线：PIL 示意图以「实景/实拍/书影/拓影」名义上屏；伪造《元史》书影内容自相矛盾

- **位置**：`remotion-template/src/shifangpujue/pages/Page01.tsx:36`、`Page02.tsx:13`、`Page03.tsx`（caption）、`Page04.tsx`（caption）、`Page06.tsx:13`、`Page07.tsx:13`；`pages.config.ts:43`（p1_photo_gate 文案「卧佛寺山门实拍」）；资产本体 `assets/hist_shifangpujue/*.png`
- **问题与证据（逐项目视）**：
  1. `shifangpujue_garden_view.png`：扁平矢量卡通（普通坡顶房＋玻璃金字塔＋圆头树），**图内烤死的字条就写着「卧佛寺与国家植物园共存实景」**。P1 caption「卧佛寺山门实景」、P7 caption「共存实景」、config 文案「实拍」。sources.csv 老实标注「制作组绘制，非实物照片」——诚实没有活到屏幕上。
  2. `shifangpujue_wofoe_photo.png` / `_face.png`：微笑卡通行走佛简笔画，caption「元代释迦牟尼涅槃铜卧佛 · 长约五米 · VEC-3」「铜卧佛面部特写 · 元代所铸 · VEC-3」，无任何「示意」字样。
  3. `yuanshi_folio.png`（P2 上屏，caption「古籍书影 · … · VEC-1」）：**伪造的《元史》卷二十八书页**，版心内含「北京现存最大最古铜卧佛」——现代旅游口号式最高级断语被塞进 1370 年的正史书影；《元史》不可能出现「北京现存最大最古」。同页还写「长五尺」，与正片口播/屏显「长约五米」**自相矛盾（差 3 倍）**。这是伪造书证＋内容打架，比"仿旧"严重一级。
  4. `shie_yaodian_tuoying.png`（P6 上屏，caption「寺额「十方普觉寺」拓影 · 雍正十二年御赐 · VEC-1」）：现代字体排印的深底金字匾，既非拓片样式也非实物，却以「拓影＋御赐年份」的实物证词名义上屏。
  5. 代码级根因：ui.tsx 的 VEC-1/VEC-3 是 E21 证据分级体系（「正史刊本书影 · VEC-1」＝赭红一手档案），被复用到"制作组绘制示意"上，**分级语义被反转**；且观众无法解码 VEC-3。
- **对照**：P5/P8 的 MEC 资产做了正确示范（caption「制作组示意」＋图内「非测绘拓扑」角标）。
- **建议**：①P1–P6 四类 VEC caption 一律加「示意 · 非实物」上屏字样（或换掉整句，如「卧佛寺山门实景」→「山门示意 · 非实景照片」）；②yuanshi_folio 要么重做成真实排印的《元史》原文（卷二十八英宗纪实文），要么整图撤下——带现代断语的伪书影不可修复；③sources.csv 的诚实标注应成为渲染 caption 的**单一事实源**（从 csv 注记生成 caption，别手写两份）。

### 🔴 C3 内审标记泄漏上屏：「🔴」emoji 渲染进证据芯片；内部集号「E25」给观众看

- **位置**：`pages.config.ts` p3_tag_fact（「🔴 佛系元代所铸 · 非唐物」）、p7_tag_caveat（「🔴 本集为第五批，与 E25 第一批口径不同」）；渲染层 `EvidenceTag`（ui.tsx）原样包 `[...]` 输出
- **证据**：交付帧局部放大 `/tmp/e26frames/p3_tag_zoom4.png`、p7.png——屏幕上实际渲染出「[🔴 佛系元代所铸 · 非唐物]」「[🔴 本集为第五批，与 E25 第一批口径不同]」，红色圆形 emoji 清晰可见；「E25」是制作内部集号，观众无从理解。
- **建议**：pages.config.ts 两处去掉「🔴 」前缀；p7_tag_caveat 改为观众语言（如「本集为第五批国保 · 非第一批」）；可加一条廉价判据：屏显 text 禁 `[\u{1F534}]` 等标记字符（`test_no_ideographic_zero` 同款写法即可）。

### 🔴 C4 P1 SVG 覆盖层：底部标签整体出画、寿安山标记被芯片遮半；覆盖层文字是全部判据的盲区

- **位置**：`remotion-template/src/shifangpujue/pages/Page01.tsx:8`（svg top:700，高 460 → 画布 y 到 1160）与 `:24`（`<text y={424}>` → 画布 y≈1124 > 1080）
- **问题与证据**：交付帧 p1.png 底部——「寿安山南麓 · 今国家植物园」标签**完全在画面外**，绿色虚线框下半被画幅裁掉；红色寺标记被 [首例纵向层累…] 芯片白垫压住一半；「香山」标注与第二块芯片相碰。放大图：`/tmp/e26frames/p1_overlay_zoom.png`。
- **判据盲区**：覆盖层文字不在 slots.json，L3/L5/L6 与负控制全部不看它（Page04.tsx 注释已自认这类风险并只修了 P4）；L1 也不查 overlay。qa 全绿与此 defect 无矛盾。
- **建议**：①svg 高度收到 ≤380 或把 y=424 标签移进画布（≤1050）；②给 overlay 文字立规矩：要么进槽位体系，要么页组件自测（断言所有 `<text>` 的画布 y+h ≤ 1080——一个 10 行的 AST/正则检查就能挡住）；③C4 与 C1 修复后 P1 需重渲。

### 🟡 Y1 `qa_v2/normalize.py:38-40` `_DURATION_CTX_BEFORE` 是恒真正则——E26 修复的"时长语境"逻辑整体是死代码

- **证据**：正则最后一个备选是**空串**（`…|约莫|)`），等价于 `[数词]{0,3}$`，对任何输入都在串尾零宽命中。实测：`search("")=True`、`search("hello world")=True`、`search("完全无关的文本")=True`。于是 `_is_reign_year_not_duration`（:45-64）退化为「prefix 末字符 ∈ {·,・、}」单一判据，:55 的时长语境分支永远 return False（保留）。
- **系统性偏向（任务问点）**：**一概保留**。年号与时长共存时，除 ·/・、前缀外全部按"时长"保留——口播侧数字只多不少，⊆ 判据被单侧削弱。E26 本集语料恰好无损害（唯一的「不到四十年」本来就该保留，·/、简写由强信号处理），但任何未来文本中「康熙三年，六年」这类**真·并列简写年号**会把 6、9 漏进口播数字集（实测 `extract_numbers('康熙三年，六年，九年重修')=[6,9]`）。
- **建议**：删掉尾部 `|`（修复恒真），并跑一遍全库 L4-c 回归确认无新 fail；顺手清理 `不足`×2、`余`×2 重复项。

### 🟡 Y2 `、`强信号（normalize.py:52）会吞枚举数字——反例已实测

- **证据**：`extract_numbers('正统八年重修，工期三年、五年两期') = [3, 2]`——「、五年」被当简写年号**剥掉，5 凭空消失**；`'雍正十二年，分两期：三年、五年' = [2, 3]` 同样吃 5。任务怀疑点「一、五年」「二、三年」型序号成立：只要句中含任一整年号（has_reign=True），、后枚举数全被吞。
- **建议**：强信号加前置条件——、前缀仅在**前一匹配也是年号简写**时成立（链式省略），或要求、紧邻前文出现过 `年号+年` 模式；至少给「吞数」路径加 warn 计数。

### 🟡 Y3 `tests/test_shifangpujue_pages.py::test_runtime_data_synced` 恒真——3 个被检文件全是符号链接

- **证据**：`/tmp/chemistry-video/src/shifangpujue/data/` 下 `slots.json`、`pages.config.ts`、`pageMap.ts` 均 symlink → macstudio 正本（ls -la 实证）。测试对这三个文件做字节比对＝**自己比自己**，永真。而真正的副本 `durations.json`、`narration.ts`、`subtitles.ts`（09:12 拷贝）和 `pages/*.tsx`（实拷贝，**Page04.tsx 在 09:23–09:28 间漂移过，见 C1**）都不在检查清单里。
- **建议**：①比对前断言 `not os.path.samefile(src,dst)`（symlink 直接 fail）；②清单补 `durations.json`、`narration.ts`、`subtitles.ts`、`pages/Page0*.tsx`。

### 🟡 Y4 L6 tag 判据全量 warn——14/14 触发 `TAG_SLOT_ALL_WHITE`，tag 渲染实际上无人看管

- **证据**：当前源码 QA 帧实测（checks_render.check_l6）：P1×2、P2×3、P3×2、P4×2、P5×2、P6×2、P8×1 全 warn（white_ratio 0.43–0.78，上限 0.40）。根因：SlotPage 的 tag mat `inset:0` 整槽铺浅卡（SlotPage.tsx tag 分支），白像素占比永远由 mat 决定。后果：①warn 通道被系统性噪声塞满（本次成片 QA 输出 warn 14 全是它）；②C3 的 emoji、C4 的埋字都从这条盲道漏过；③tag「有无白字」的真实问题（深底白字）没有任何判据在看。
- **建议**：L6 改为**只测芯片本体的暗底白字**：先用暗色连通域找 chip 矩形再测白字占比，或把 WHITE_MAX_RATIO 提到按 mat 设计校准的 >0.85（检测「mat 也没渲出来」的空槽），两种都比现在的恒 warn 强。

### 🟡 Y5 负控制实际只覆盖 38% 的槽（23/61），untestable 计数被弱搜索撑大

- **证据**：8 页逐一跑 `assert_negative_control`（缓存 OCR）：not_caught 全 0，untestable = 4/6/4/7/4/6/3/5。逐槽分解显示连 `p1_title(860×68)`、`p7_title(860×68)` 这种小槽都"找不到空白落点"——`_find_negative_control_rect` 的 20 个固定候选＋±500/100 步进网格在 1920×1080 上找不齐空位。not_caught=0 只对 23 个被测槽成立。
- **建议**：网格回退加一步**全图栅格扫描**（对 860×68 这种槽必然找得到）；run.py 的 NEGATIVE_CONTROL_SKIPPED info 里带上槽位清单，否则 38% 的覆盖没人看见。

### 🟡 Y6 `MIN=10` 豁免在交付数据上已漏掉一个「未念屏显数」（不是假想）

- **位置**：`tests/test_shifangpujue_audio.py:92`、`tests/test_shifangpujue_pages.py:27`；实例 `pages.config.ts:82`（p4_right「长约五米」）vs `narration/all.json` p04（数字集 {1,2,600}，无 5）
- **证据**：P4 屏显有 5、P4 口播无 5（「五米」只在 P3 念）——docstring 承诺「屏显上的每一个数字都必须在该页口播里念出来」，实现豁免 <10 后此承诺今天就破着。变异实验：把两处「五米」改成「九米」，两个子集判据依旧全绿（错误屏显数完全逃过）。
- **建议**：不全量放开 <10，加**单位锚定**小数检查：`(数词|数字){1,4}(米|尺|丈|尊|座|根)` 出现于屏显时必须逐页在口播找到同单位同值；一行正则即可，E24 的「误抓普通词」顾虑不适用。

### 🟡 Y7 V-NC02 禁词表形同虚设（6 种同义写法全部逃逸），正向判据过弱

- **位置**：`tests/test_shifangpujue_audio.py:139`（唐代铜卧佛/唐代遗存/唐时铸/唐代所铸）、`tests/test_shifangpujue_pages.py:158`（后三个）；正向仅 `assert "元" in p3`（pages:156）/`"元代" in blob`（audio）
- **证据**：实测逃逸词——「唐代**的**铜卧佛」（加个「的」即绕过精确子串）、「唐铸」「唐代的佛」「自唐以来」「铸于唐代」「唐代铸造」全部放行；正向判据「元 in p3」连「公元」都能满足。
- **建议**：改成正向强断言：P3 屏显与 p03 口播必须含「元代（所）铸/元至治」，且（唐代 AND 铸）不得在同一句共现（窗口 ≤12 字），比枚举禁词稳。

### 🟡 Y8 禁「笼统改名」三份禁词表互不一致且全部可绕过

- **位置**：`tests/haidian_kg/test_shifangpujue_entry.py:82`、`tests/test_shifangpujue_audio.py:126`、`tests/test_shifangpujue_pages.py:147`
- **证据**：三份列表各不相同（pages 版漏「历经数次改名/历经多次易名」，audio/KB 版漏「数次改名」）；实测「几易其名」「数度更名」「多次更名」「五度更名」「屡易其名」在三家全部放行。
- **建议**：抽成 qa_v2.normalize 的共享常量（单一事实源），或干脆删掉这三条禁词表——正向判据（六名号逐一出现＋一一年号对应）已是主防线，禁词表只是安慰剂。

### 🔵 B1 `tests/haidian_kg/test_shifangpujue_entry.py:168` 字面重言式

`assert "1-75" in ad.rationale or "1-75" not in ad.rationale` —— 对任何字符串恒真（实测对变异数据 PASSED）。测试名承诺的事什么都没做。删掉或改成真断言（如「本寺相关 DIVISION/STATE 不得含 1-75，rationale 提及时必须带『非本寺体系』」）。

### 🔵 B2 文件头/共享件跨集残留

`tests/test_shifangpujue_pages.py:2` 自称「E24《十方普觉寺·阳台山麓的千年清水院》」（E24 是大觉寺，阳台山/清水院均误）；`SlotPage.tsx:1` 自称「E25《十方普觉寺·把塔的落成年错当成寺的始建年》…public/weigongcun/」（E25 是五塔寺，weigongcun 是 E21）；`ui.tsx` TAG_COLORS 里 **0 条 E26 标签**（E21 魏公村全表），E26 全部 tag 落到 inkSoft 兜底色，「证据分级色」语义全丢；`test_redline_no_fabricated_mansion_photo` docstring 讲辽塔/白玉兰（E24），禁词却是 E26 物——半新半旧。注：BANNED_ARABIC_YEARS 我核过**不是**残留——1321/1443/1482/1734/2001/627/649 恰是本集年份集，仅 "1321" 重复一次。

### 🔵 B3 `tests/test_shifangpujue_audio.py:72` 名实不符

名 `test_single_page_not_exceeding_audio_length`，docstring「15s 承载（约 12 字/秒 → 180 字）」，实际 `<= 200` 且根本不读音频。改成按 durations.json 实测时长×语速算上限，或改名。

### 🔵 B4 「2026」硬编码年时间炸弹

`haidian_kg/calibration/shifangpujue.py`（十方普觉寺 span end=2026）＋ `test_shifangpujue_entry.py:63`（`>= 2026`）：2027-01-01 起必 fail，之后每年都要人肉 bumps。「延续至今」应建为开区间（end=None 或哨兵 9999），测试断言 open-ended。

### 🔵 B5 `_REIGN_NAMES`（normalize.py:26）缺 至治/贞观

「至治元年」因「元」非数词而无损，但「至治三年」会漏出 3（应剥全句）；唐代号全缺。补齐成本一行。另 `_DURATION_TAIL` 的「来/许」语境误纳（如「，五年来历…」会保留 5）当前无实害，Y1 修复后随其一并复核。

### 🔵 B6 杂项

①10 项资产中 3 项未上片（sanshanyuan_shuoan_roi_4000、beijing_1915_shuoan_roi、shi_ji_bei_tuoying——后者干支「甲寅」我核过是对的，但没用上）；②audio 版屏显数字过滤不豁免 quote 槽而 pages 版豁免（本集无 quote 槽，潜伏）；③L3 存在性用全置信、负控制过滤 <0.80——方向安全但不严格对称；④P6 屏显+口播「东西南北与四维上下**六方/六个方向**」与其自身枚举（4+4+2=10 向）自相矛盾——属史实层，归口史实审核，此处仅记录数字自洽判据对此类语义矛盾天然失明。

---

## 二、核过但认为没问题的项（覆盖面声明）

1. **G5 引用完整性真有效**：五类悬空引用（division.source_id / fact.division_id / proposition.derived_from / state.entity_id / reference.appellation_id）内存变异**全部被抓住**，报错信息含具体 id——E25 那类 bug（src_guobao_1st 悬空）在今天会被拦截。变异均未落盘。
2. **KB 35 项中 34 项实测有效**：g1 六名链（恰 6、顺序、时段 627→2026 无倒置）、g2 分层（实体标签「元代所铸」且无「唐」、DISPROVEN 带反驳 id、gap 显式）、g3 批次互不污染（E25 侧不引编号也验了）、g4 DISPROVEN/UNSUBSTANTIATED 纪律、g6/g7 rationale 长度下限——语义都问对了。
3. **归一化正例**：「雍正十二年，不到四十年重修」→[40]（E26 修复目标行为正确）；「共二十四年，计三年」→[24,3]（共/计不误剥）；「二十年来」「三十许年」按时长保留正确；「成化九年、十七年」→[]（并列简写整链剥离正确）；「不到四十年」尾缀 来/许 判定正确。
4. **数字账全部对得上**（屏↔播双向）：1321（至治元年）/627–649/1443/1482/1734/2001-06-25/5-205；「四百多年」=1734−1321=413 ✓；「六百余载」=694 ✓；「不到四十年」=39 ✓；P7 用「二零零一」（U+96F6）非 U+3007 ✓。
5. **frames.py OCR 疫苗在位**：`use_doc_orientation_classify/use_doc_unwarping/use_textline_orientation` 全 False（frames.py:70-72），符合 E13 复盘铁律。
6. **数据同源性（真实副本）**：durations.json/narration.ts/subtitles.ts 字节一致；8 个 wav 实测时长与 durations.json 全部吻合（±0.01s）；pageMap `PAGE_DURATIONS_SEC` = 音频+1.6 精确；累计 275.04s ≈ ffprobe 275.029 ✓——页边界链（E8 教训①）本次没有复发。
7. **无字幕条是全系列设计**（E25 等姊妹集同样只存 subtitles.ts 供 ASR 校验、不渲染）——「字幕遮挡」本集 N/A。
8. **backing 无漏配**：53/53 非 photo 文字项全配（静态测试＋8 帧目视未见 sub 压插画不可读，E8 教训③未复发）。
9. **P5/P8 资产干净**：时间轴/叠合图诚实标注「制作组示意 · 非测绘拓扑」，**无编造碑刻/引文文字**，图内六名与年份同口播一致（任务点：mec3 时间轴无伪造文字——证实）。
10. **P2 三位纪年可读性**：「六二七年至六四九年」26px 全字形汉字、无 U+3007，帧上清晰——未违反自家红线（红线禁的是小字号＋圆圈零）。
11. **L1/L2**（引用完整性、越界、交叠、过小槽）语义健全，无恒真迹象。
12. **测试可跑性**：75/75 通过（35+20+20），全库无 import 破损。

---

## 三、判据健康度专项结论

| 判据组 | 恒真 | 问错问题 | 结论 |
|---|---|---|---|
| KB 35 项 | **1**（g3_1961 字面重言） | 0 | 其余 34 项变异/语义双验有效 |
| 页面 20 项 | **1**（runtime_data_synced 符号链接自比） | 1（six-names 用 slot_id 子串而非 kind 判 photo——p5_timeline/p8_composite 两个 photo 槽 caption 被算进「屏显」集合，当前无实害，属潜伏假通过通道） | 18 项有效 |
| 旁白 20 项 | 0 | 1（MIN=10 豁免使「每数必念」名不副实，交付数据已有 1 例漏网：P4 五米） | 19 项有效 |
| qa_v2 L6 | 事实性恒 warn（14/14） | 在测 mat 不在测 tag | 需重设计 |
| qa_v2 负控制 | 无恒真（not_caught=0 可信） | 覆盖仅 38%，untestable 虚高 | 覆盖率要修 |

**总判**：判据层「全绿」里埋着 2 个恒真 + 1 个全量 warn + 1 个 38% 覆盖——但**没有一个是本集史实出错的直接原因**；本集真正的交付事故在管线层（C1 新旧渲染不同源）与资产层（C2 伪实物命名）。这印证负控制纪律的原始命题：判据全绿 ≠ 交付物正确，两端各要一道闸。

---

## 四、临时动过的东西（均已恢复/无残留）

- **仓库文件：零改动**。所有变异（G5 五类悬空引用、禁词绕过、MIN=10 变异、5→9 屏显数）均为内存对象探针或字符串替换后即时 parse，进程结束即消失；未创建任何测试文件；未动兄弟正在改的 `tests/test_normalize.py`。
- /tmp 侧证据：`/tmp/e26frames/`（8 终态帧＋4 放大图）、`/tmp/audit_*.png/jpg`（资产副本）——仅供复查，可随时删。
- git：无任何 commit/stage；`git status` 与开工时一致（仅兄弟的 `M tests/test_normalize.py` 与 `?? scripts/extract_wenquan_assets.py`）。

---

## 五、状态附记（写报告后 10 分钟内复核）

报告写毕时发现工作树出现了**非本 agent 的并发修改**（`shifangpujue.py`、`pages.config.ts`、`all.json`、`research.md`、`test_shifangpujue_entry.py`、两个测试文件，8 files changed）——应为 Main 正在落修复。已对改动后工作树复测三项锚点发现：🔴 emoji 仍在 pages.config.ts（3 处）、「实景」caption 仍在 Page01/07、g3_1961 重言式仍在（行号 168→197 漂移）。本报告全部结论以**审核时点状态**（commit 87ce346 + 09:2x 工作树 + 09:23 成片）为准；行号引用若与当前树不符，以符号文本检索为准。
