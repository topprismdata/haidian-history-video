# E26《十方普觉寺》对抗审核 · 修复处置账本

- 建立日期：2026-10-04（依 `.superpowers/sdd/three-stage-review-workflow.md` 收尾件要求补写）。
- 对照报告：
  - `.superpowers/sdd/e26-adversarial-evidence.md`（证据层，E26AdversaryEvidence）
  - `.superpowers/sdd/e26-adversarial-pipeline.md`（管线与判据层，E26AdversaryPipeline）
- 信息来源：`git log --oneline -8`（主处置 commit **0e2638d** `fix(e26): 对抗审核 7 项处置`，2026-10-04 10:36）＋两份报告原文＋**对当前工作树逐条回查验证**（每条处置都核了现行文件，非仅抄 commit message）。
- 处置取值：**已修**（含 commit 与现行文件证据）/ **部分采纳**（主体已修、余项顺延并注明）/ **顺延**（本集未改，写明理由）/ **驳回**（附反证）。
- 注：两份报告编号各自独立（都有 Y*/B*），本账本以「证据Y1」「管线Y1」区分；两报告重叠项已互相标注。

---

## 一、证据层（e26-adversarial-evidence.md）逐条处置

| 编号 | 等级 | 条目 | 处置 | 证据 |
|---|---|---|---|---|
| R1 | 🔴 | 名号链跨朝代错置（寿安山寺≠明正统八年） | **已修** | 0e2638d。名号链六个→七个、易名五次→六次；research.md:12/14 订正注、narration 重录 TTS（p03「延祐七年…敕建的寺名叫寿安山寺」实测）、屏显 p5/p8 同步、calibration Appellation 增「寿安禅林」(1443)、extractor toponym 增 top_shouanchanlin；测试 SIX_NAMES→SEVEN_NAMES＋新增 test_g1_shouanshan_is_yuan_not_ming / test_g1_shouanchanlin_is_ming / test_g1_six_names_collapses_to_five_is_fatal（负控制） |
| R2 | 🔴 | 「十方＝六个方向」算术错误 | **已修** | 0e2638d。narration p06 实测「十方, 是十个方位: 东西南北四方, 加东南、西南、东北、西北四维, 再加上和下」；「本为僧众居住之所的称呼」已删；新增 test_shi_fang_is_ten_not_six（pages＋audio 双档） |
| R3 | 🔴 | 8 条 verbatim_quote 错挂国保名单（自撰伪引文） | **已修** | 0e2638d。facts 由 8 条降为 4 条可核（名单原行、元史冶铜条、雍正御碑条、寺址条）；QUARANTINE Q-003 留档；新增 test_g5_no_selfauthored_quotes / test_g5_facts_count_is_small_and_honest 回归 |
| 证据Y1 | 🟡 | 元代扩建系年两说未处理 | **已修** | research.md:45-47 采「延祐七年下诏、至治元年铸佛」分年表述并记两说；narration p03 实测分年口播；屏显 p8_eras「元·延祐/至治（敕建＋三称）」 |
| 证据Y2 | 🟡 | 《观无量寿佛经》误作兜率出处 | **已修** | 错误经名整句撤除：narration p02 改「出自佛经里对未来弥勒的描述」（不落具体经名即不出错）；research.md 已无「观无量寿」字样（全文检索 0 命中） |
| 证据Y3 | 🟡 | p02「名字在前，佛像后来才换」与雍正碑檀木卧佛传统相抵 | **顺延** | narration p02 实测仍含「名字在前, 佛像后来才换」。未删句。理由：前句「兜率是弥勒内院…并不是同一尊佛」的区分本身被审核认可为站得住；末句的错（初建供奉无书证）未在双档 fail 中暴露，修正顺延。审核对檀木层的裁定已由 KB 侧吸收（见 §三②） |
| 证据Y4 | 🟡 | 「两个御赐名号」无法自洽 | **部分采纳** | 随 R1 由「六个」改「七个」（narration p06、p6_note/p6_tag_bestow 实测已更新）；但「有两个是皇帝敕赐或御赐的」句保留、未点名、未删。理由：修正名号链后该句未再被判据抓住；御赐清单重审（昭孝赐额是否计入）顺延 |
| 证据Y5 | 🟡 | KB 闸门重言式 `assert "1-75" in … or "1-75" not in …` | **顺延** | 现行 tests/haidian_kg/test_shifangpujue_entry.py:197 该行**原样保留**（现带注释「rationale 提及 1-75 是合法的」）；0e2638d 对本函数仅改了 fact id（fact_e26_guobao5_5_205→listentry），未加新断言。≡ 管线B1。理由：判据层清理整体顺延（见管线Y3-Y8 同批） |
| 证据Y6 | 🟡 | 页面测试文件头/防伪判据 E24 残留 | **顺延** | 现行 tests/test_shifangpujue_pages.py:2 docstring 仍为「E24《十方普觉寺·阳台山麓的千年清水院》」；test_redline_no_fabricated_mansion_photo 的 E24 禁词表未换。0e2638d 对该文件仅改 SIX→SEVEN 与 R2 判据。≡ 管线B2 的一部分。理由：判据层清理整体顺延 |
| 证据B1 | 🔵 | 「元代宗室」错误＋代表作无来源标注 | **已修** | research.md 全文检索「宗室」0 命中（随 R1 重写消除） |
| 证据B2 | 🔵 | 「普觉寺为梵汉合称」文句不通 | **已修** | research.md 检索「梵汉合称」0 命中；narration p06 改「普觉, 意思是普遍地令众生觉悟」 |
| 证据B3 | 🔵 | p07「戏称为为什么音译的英文词」拗口 | **顺延** | narration p07 实测原句未改。理由：纯文案润色，无史实负荷，顺延 |
| 证据B4 | 🔵 | 屏显「零」与口播「〇」用字不一致 | **已修** | 0e2638d。口播改「二零零一年六月二十五日」（与屏显同用 U+96F6），audio 测试断言同步 `assert "二零零一年六月二十五日" in n`，两侧字符串恢复同源 |
| 证据B5 | 🔵 | BANNED_ARABIC_YEARS 混入 "1473" 无注＋"1321" 重复 | **顺延** | 现行 tests/test_shifangpujue_pages.py:213 仍为 `("1473", "1321", …, "1321")`。理由：审核本人亦判「不是残留、黑名单法天然漏新年份，真闸门是四位裸数字兜底」——维持现状 |
| 证据B6 | 🔵 | Appellation 时段零长/分界无书证 | **顺延** | 时段已随 R1 全链重排（寿安山寺1320、寿安禅林1443 等），但「零长时段/分界无书证」未逐条复审。理由：审核自评「建模本身不传播到成片，列为备忘」 |
| §三-① | 专项 | DISPROVEN 反驳证据空心（错挂书源） | **已修** | 雍正御碑「其一则后人范铜为之」已立为独立 fact（calibration/shifangpujue.py:127-136 实测，含檀木/铜佛两尊分层注释）并计入 R3 修复的 4 facts |
| §三-② | 专项 | 「寺内卧佛是唐代遗物」整体打证伪过宽 | **已修** | calibration:127-136 实测注明「檀木者『相传贞观中造』（传说层，雍正八年大修移走），铜者『后人范铜为之』。二者不可混为一谈」；只有「现存铜卧佛是唐物」保持 DISPROVEN |
| 未决 | — | 「寺额至今悬于殿前」未能独立证实 | **顺延** | 屏显 p6_tag_source 实测仍为「御赐名号 · 寺额至今悬于殿前」。该项在报告中列为「未决（不作为问题）」，未入修复清单；现状断言补证顺延 |

---

## 二、管线与判据层（e26-adversarial-pipeline.md）逐条处置

| 编号 | 等级 | 条目 | 处置 | 证据 |
|---|---|---|---|---|
| C1 | 🔴 | 交付 mp4 ≠ QA 验证的渲染（P4 旧版出厂） | **已修** | 0e2638d。qa_v2 新增 `check_delivery_freshness` 闸门（run.py +35；成片 mtime 须 ≥ 全部输入）；装好即抓到 DELIVERY_STALE（差 3344 秒），从当前源码重渲并复验通过，双档 fail 0。子项顺延：审核建议「根因写进 series_registry 教训」未落地——`git log -- anheqiao_video/series_registry.md` 末次变更仍为 e2ac4c7（E25），未见本轮补写 |
| C2 | 🔴 | PIL 示意图以「实景/实拍/书影/拓影」名义上屏；伪造《元史》书影 | **已修** | 0e2638d。7 处 caption 实测全部改为「制作组绘制示意 · 非实物照片」「转引排印 · 非原刊扫描」「排印示意 · 非实物拓片」等（Page01/02/03/04/06/07/08.tsx diff）；yuanshi_folio 资产重做（git stat Bin 71319→49341）、shie_yaodian_tuoying/garden_view 同步重制；VEC-1/VEC-3 分级语义从 caption 层移除。残留（顺延）：pages.config.ts:42/130 两个 photo 槽的 `text` 字段仍含「实拍/实景」字样——渲染 caption 已由 Page tsx 的 PhotoSpec 承担，该字段若仅作内部登记则无碍，未单独清理；「caption 从 sources.csv 生成」的单一事实源改造未做 |
| C3 | 🔴 | 「🔴」emoji 与内部集号「E25」泄漏上屏 | **已修** | 0e2638d。pages.config.ts 现存唯一「🔴」在第 6 行**代码注释**（屏显纪律备忘），两条 tag 文案已去 emoji；p7 口径改观众语言。建议的「屏显禁 emoji 判据」未加（顺延，随判据层批次） |
| C4 | 🔴 | P1 SVG 覆盖层底部标签出画、被芯片遮挡；覆盖层文字是判据盲区 | **部分采纳** | 已修部分：图内烤死「实景」字条随 C2 资产重制消除、caption 同步（commit 将此记为「C4 随 C2 一并处置」）。**顺延部分（审核 C4 的核心）**：Page01.tsx 实测 svg 仍 `top:700, height:460`（画布底 y=1160>1080）、`<text y={424}>`（画布 y≈1124）——**几何出画未修**；「overlay 文字进槽位体系或页组件自测」的判据亦未建。理由：0e2638d 对 pages/ 的改动全部为 caption 行，无几何改动；重渲后双档 fail 0 恰因 L3/L5/L6 不看 overlay（审核指出的盲区原样存在） |
| 管线Y1 | 🟡 | `_DURATION_CTX_BEFORE` 恒真正则（死代码） | **已修** | 0e2638d（qa_v2/normalize.py +36、tests/test_normalize.py +36）。现行 normalize.py:36-42 起带订正注释；并修复审核后新暴露的 Y1b（时长语境窗口 `s[start-12:start]` 停在待判数字之前、永不命中→改窗口含待判数字）。commit 原文：「E26 那个『四十年』的修复实由『·/、』路径兜住，与这条规则无关」 |
| 管线Y2 | 🟡 | 「、」强信号吞枚举数字 | **顺延（已记录为已知取舍）** | commit 原文：「Y2 (已记录为已知取舍) 『、』是强年号信号，也会吞枚举数字…当前判据偏向保留(宁可多留不可多删), 方向安全」。未加前置条件、未加 warn 计数 |
| 管线Y3 | 🟡 | `test_runtime_data_synced` 恒真（3 文件是符号链接自比） | **顺延** | 现行 tests/test_shifangpujue_pages.py 无 `samefile/islink` 断言，检查清单未补 durations.json/narration.ts/subtitles.ts/Page0*.tsx |
| 管线Y4 | 🟡 | L6 tag 判据全量 warn（14/14 TAG_SLOT_ALL_WHITE） | **顺延** | 现行 qa_v2/checks_render.py:263 仍 `WHITE_MAX_RATIO: 0.40`，无「暗色连通域找 chip 再测白字」改造，也无 >0.85 空槽检测 |
| 管线Y5 | 🟡 | 负控制仅覆盖 38%（23/61），untestable 虚高 | **顺延** | 现行 checks_render.py:88 `_find_negative_control_rect` 仍是 20 候选＋步进网格，无全图栅格扫描回退；run.py 的 NEGATIVE_CONTROL_SKIPPED info 未带槽位清单 |
| 管线Y6 | 🟡 | MIN=10 豁免漏「未念屏显数」（P4 五米实锤） | **顺延** | 现行两测试仍 `MIN=10 / MIN_YEAR=10`（audio:92、pages:27）；「单位锚定小数检查」（数词+米/尺/丈…逐页对同值）未实现。P4 屏显 5 / 口播无 5 的实例原样存在 |
| 管线Y7 | 🟡 | V-NC02 禁词表 6 种同义写法全部逃逸 | **顺延（部分采纳）** | **Main 处置：本集未改**。现行 audio:139-141 四词禁词表与 pages:158 后三词原样；正向判据为主防线（audio「元代/元朝/元至治元年」必须出现）。理由：正向强断言（「元代（所）铸」必须出现＋唐/铸同句共现窗口检测）属判据层通用改造，顺延至 qa_v2 批次；本集主防线（正向）已在位 |
| 管线Y8 | 🟡 | 三份「笼统改名」禁词表互不一致且全可绕过 | **顺延** | 实测三表仍各不相同：entry:111（历经数次改名/历经多次易名/数次易名/屡次改名）、audio:126（同 entry）、pages:147（数次易名/历经多次改名/屡次改名/数次改名）；未抽成 qa_v2 共享常量，也未删表 |
| 管线B1 | 🔵 | test_g3_1961 字面重言式 | **顺延** | ≡ 证据Y5，同上：现行 :197 原样保留 |
| 管线B2 | 🔵 | 跨集残留（pages docstring 自称 E24、SlotPage.tsx 自称 E25、ui.tsx TAG_COLORS 无 E26 标签） | **顺延** | 实测：test_shifangpujue_pages.py:2 仍「E24…清水院」；shifangpujue/SlotPage.tsx:1 仍「E25《十方普觉寺·把塔的落成年错当成寺的始建年》」；ui.tsx 检索「E26」0 命中（TAG_COLORS 仍无本集条目，tag 落 inkSoft 兜底色）。BANNED_ARABIC_YEARS 经审核自证不是残留（见证据B5） |
| 管线B3 | 🔵 | audio 测试名实不符（docstring 180 字 vs 断言 200 且不读音频） | **顺延** | 现行 tests/test_shifangpujue_audio.py:73-74 原样 |
| 管线B4 | 🔵 | 「2026」硬编码年时间炸弹 | **顺延** | 现行 calibration/shifangpujue.py:251/271/288 三处 `_ts(…, 2026, …)` 仍在；未改开区间（end=None/9999） |
| 管线B5 | 🔵 | `_REIGN_NAMES` 缺 至治/贞观 | **顺延** | 现行 qa_v2/normalize.py 检索「至治|贞观」0 命中 |
| 管线B6 | 🔵 | 杂项（3 资产未上片/quote 槽豁免不对称/L3 置信不对称/「六方」矛盾） | **顺延** | ①3 项未上片资产未处置；②quote 槽豁免仍不对称（pages:220 豁免 photo+quote，audio 无 quote 豁免）；③checks_render.py:26 仍单一 `LOW_CONFIDENCE=0.80`，正/负路过滤未对称化；④「六方」矛盾本体已由 R2 修复（归口证据层） |

---

## 三、三条特定记录（任务指名）

1. **审核 Y7（禁词表绕过）→ 部分采纳，本集未改，记顺延**：正向「元 in p3」类判据为主防线的立场被采纳，禁词表枚举法放弃加固；同义逃逸问题的根治（正向强断言＋共现窗口）并入 qa_v2 判据层改造批次，不在本集修。详见上表管线Y7。
2. **「唐铸 DISPROVEN 越界」质疑 → 驳回（Main 认错，采纳审核）**：Main 最初怀疑证据报告 §三 会要求把「唐时所铸」降为 UNSUBSTANTIATED。审核以肯定性反面书证驳回：《元史·英宗纪》至治元年「冶铜五十万斤作寿安山寺佛像」＋雍正御碑「其一则后人范铜为之」属 **evidence of absence(Tang)**，非 absence of evidence，DISPROVEN 成立。0e2638d commit「驳回/不采纳」节原文记录此裁决，并把雍正碑书证补进 KB（Q-003、calibration:127-136）。同时审核另一侧意见被采纳：「寺内卧佛是唐代遗物」整体打证伪过宽——檀木卧佛「相传贞观中造」按传说层单独注明（§三②，已修）。
3. **C1 新鲜度闸门 DELIVERY_STALE 两次触发记录**：0e2638d 原文——「qa_v2 新增 check_delivery_freshness 闸门(成片 mtime 须 >= 全部输入)，装好后**立刻抓到 DELIVERY_STALE 差 3344 秒**；**重渲后复验通过**」。即第一次运行触发=抓到 09:23 旧成片（根因即 C1 指控本身）；第二次运行=回炉重渲后的通过验证。此后成片与 QA 验证对象恢复同源。

---

## 四、统计

- 证据层：编号条目 15（🔴3/🟡6/🔵6）＋ DISPROVEN 专项 2 ＋ 未决 1 = **18 条**
  - 已修 **10**（R1、R2、R3、Y1、Y2、B1、B2、B4、§三①、§三②）
  - 部分采纳 **1**（证据Y4：随 R1 更新七名，御赐清单重审顺延）
  - 顺延 **7**（Y3、Y5、Y6、B3、B5、B6、未决「寺额至今悬于殿前」）
- 管线层：编号条目 **18 条**（🔴4/🟡8/🔵6）
  - 已修 **4**（C1、C2、C3、Y1〔含 Y1b〕）
  - 部分采纳 **1**（C4：caption/图内文字已修；SVG 几何出画与 overlay 判据顺延）
  - 顺延 **13**（Y2〔已知取舍〕、Y3、Y4、Y5、Y6、Y7〔本集未改〕、Y8、B1、B2、B3、B4、B5、B6）
- **合计 36 条：已修 14 / 部分采纳 2 / 顺延 20；驳回 1（针对审核立场的裁决记录，见 §三-2，Main 被审核驳回后采纳审核）**
- 顺延条目的集中原因：判据/闸门类（Y3-Y8、B1-B6、C4 判据子项）属 qa_v2 通用层，按「本集先保交付、判据改造单独立批」处理，故整体顺延；本集史实与交付层（R/C 全部 🔴）无一带延。
- 重叠项对照：证据Y5≡管线B1；证据Y6≈管线B2；证据R3↔管线B6④（「六方」数字自洽失明的本体即 R2，已修）。
- 修复后全库 **1192 passed**，E26 双档 **fail 0**（0e2638d）。
