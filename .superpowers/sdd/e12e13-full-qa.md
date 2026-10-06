# E12《苏州街》/ E13《中关村》全档 QA 报告（qa_v2 全档 + 独立复核）

日期：2026-10-02　执行：FullQaRun（全档 QA 路；内容红线归 E12BackAudit / E13BackAudit 另两路）
工程：`/tmp/chemistry-video`（软链至 `/Volumes/macstudio/video-projects/chemistry-video`），本轮只审不修，未 commit。

## 一、结论速览

| 集 | 档位 | 真实运行耗时 | fail | warn | skip | info | 判定 |
|---|---|---|---|---|---|---|---|
| E12 suzhoujie | 全档 L1–L6 + `--ocr`（L3/L4a/b/c/负控制） | 合跑 84.47s（含模型加载）；热缓存收口 1.0s；独立复跑 7.8s | 0 | 0 | 0 | 0 | **通过** |
| E13 zhongguancun | 同上 | 首跑在合跑内；**清帧重渲重跑 101.97s**；热缓存收口 1.0s | 0 | 0 | 0 | 1 | **通过**（info 见 §四） |

info 1 = zhongguancun P3 负控制 3 槽无法构造空白平移矩形（`NEGATIVE_CONTROL_SKIPPED`），已按 §五独立证实属实，非判据缺陷。

**fail / warn 总数：0。故「逐条归因」对象为空**；以下以覆盖证据 + 负控制 + 新增一致性检查证明「通过」不是恒真或空转。

## 二、运行与缓存治理（本轮实踩两处陈旧产物，均已排除）

1. **OCR 缓存陈旧**：`/tmp/qa_cache/zhongguancun_*.json`（08:13）早于 `src/zhongguancun/data/slots.json`、`_meta.json`（08:19:31）→ 按纪律 `rm -f` 后再跑。suzhoujie 缓存（01:09）晚于其全部源文件（≤01:08:54），无需清。
2. **渲染帧陈旧（qa_v2 工具缺口，见 §七）**：首跑时 `/tmp/qa_frames/zhongguancun/p03.png` 为 08:12:18 渲染，早于 08:19:31 数据修改；`_frame_for` 在 png 存在时**直接复用旧帧**，L3/L5/L6 首跑判的是旧渲染。→ `rm` 全部 zgc 帧 + 缓存后重跑（bg_33，重渲 8 帧 + 重 OCR，101.97s），结论不变。
3. 08:19 的 `slots.json` 改动内容不可考（chemistry-video 不在卷根 git 追踪内）；但其影响已被排除：重渲后的新帧与交付 mp4（08:24，晚于该改动）逐页 MAD 与旧帧版本**逐位相同**（8 页到小数点后两位），即该改动对终态帧零视觉影响，且 QA 判的是改动后工程。
   - **「数据修改 → 仍用旧帧」场景的精确文件清单**（供 `_frame_for` 失效键复用；均为实测 mtime，经 `find <src> -newer <旧缓存> -name '*.json'` 检出）：
     - `/tmp/chemistry-video/src/zhongguancun/data/slots.json`（实库 `…/chemistry-video/src/zhongguancun/data/slots.json`）mtime **2026-10-02 08:19:31**
     - `/tmp/chemistry-video/src/zhongguancun/data/_meta.json`（实库同目录）mtime **2026-10-02 08:19:31**
     - 旧帧：`/tmp/qa_frames/zhongguancun/p03.png` mtime 08:12:18（早于上述两文件 7 分钟仍被复用）
   - 该集同目录其余失效键候选（suzhoujie 侧实测同构）：`narration.ts`/`pageMap.ts`/`subtitles.ts`（01:02:23）、`pages.config.ts`（01:08:54）、`pages/PageNN.tsx`（01:00:04）、`SlotPage.tsx`/`ui.tsx`/`*Course.tsx`（01:00–01:03）。建议失效键至少覆盖 `data/` 全部文件 + `pages/*.tsx` + `SlotPage.tsx`。

## 三、反向覆盖表（qa_v2 不打印覆盖计数，以下为独立复跑实测）

| 判据层 | E12 suzhoujie | E13 zhongguancun | 结果 |
|---|---|---|---|
| L1 数据一致性 | 8 页 / 48 项文案 | 8 页 / 43 项文案 | 0 发现 |
| L2 几何预检 | 8 页同上槽位 | 同左 | 0 发现 |
| L3 渲染存在性（OCR） | 48/48 槽 OCR 命中，最低置信 0.894（阈值 0.80） | 43/43 命中，最低置信 0.973 | 0 发现 |
| L4a 数字闭环 | 48 项 | 43 项 | 0 发现 |
| L4b 专名闭环 | 46 条专名表逐页比对 | 同左 | 0 发现 |
| L4c 字幕×口播交叉 | 8 页 | 8 页 | 0 发现 |
| L5 溢出（墨迹触边） | 48 槽逐帧量 bbox | 43 槽 | 0 发现 |
| L6 tag 槽（深底白字） | 6 个 `badge` 槽（p1/p2/p4/p5/p6/p7） | 6 个 `badge` 槽（p1/p2/p4/p5/p6/p8） | 0 发现 |
| 负控制 | 8 页全部可测，0 not_caught / 0 untestable | 7 页 0/0；P3 0 not_caught / **3 untestable** | 见 §五 |

注意：L6 覆盖曾一度被误判为 0——`TAG_IDS={"evidence_tag"}` 与本两集 tag 槽名 `badge` 不一致，按槽名统计会得出「L6 零覆盖」假象；实测 `check_l6` 按 `kind=="tag"` 正确评估了 6+6 个 badge。白字占比实测：E12 0.0233–0.0453，E13 0.0178–0.0225，全部落在判据区间 [0.01, 0.40] 且远离两端（非空转）。

## 四、逐条归因

- **fail：0 条，warn：0 条**（两集）——无归因对象。
- **info：2 条**（E12 首跑 0 条；E13 每跑 1 条）：
  - E13 P3 `NEGATIVE_CONTROL_SKIPPED`：3 槽（`d_left`/`d_mid`/`d_right`，P3 日期三联槽）无法构造与任何真槽及自身原矩形不相交的空白平移矩形。**独立复现**：自写 20px 步长全板面网格搜索，三槽同样找不到空白落点 → 「untestable」属实，非判据搜索空间不足。该页其余槽位负控制正常执行且通过。

## 五、负控制实测（判据不是恒真）

| # | 对象 | 操作 | 结果 |
|---|---|---|---|
| 1 | **L3 存在性**（两集全部 16 页） | 每页选 OCR 命中槽，`_find_negative_control_rect` 挪至空白落点后重跑 `check_l3` | 16/16 页翻转：`shifted_text_at=EMPTY` 且该槽报 `SLOT_RENDER_EMPTY` |
| 2 | **L4a 数字闭环**（E12 P2） | 从 OCR 结果删除一行含数字文本 `乾隆十六年（1751）·崇庆皇太后六十寿` | 翻转：`L4-a/2/NUMBER_MISMATCH` |
| 3 | **L6 tag 槽**（E12 P7 badge） | badge 矩形挪至 (1345,348)，白字占比 0.0233 → 0.0051 | 翻转：`TAG_SLOT_EMPTY`（white_ratio=0.0051 < 0.01） |
| 4 | E13 P3 untestable 声明 | 独立 20px 网格复搜 | 证实：三槽确实无空白落点 |

## 六、口播音频 × 字幕逐页一致性（qa_v2 不覆盖，本轮新增）

方法：`subtitles.ts` 逐行拼接 vs `narration/all.json` 口播原文（标点/空白归一后全等比较）；`ffprobe` 实测 `public/audio/<ep>/pN.wav` 时长 vs `narration.ts` 声明值；字幕末条结束时刻 vs 音频尾/页长。

| 检查 | E12（8 页） | E13（8 页） |
|---|---|---|
| 字幕拼接 == 口播原文（逐页） | 8/8 一致 | 8/8 一致 |
| 实测 wav − 声明音频时长 | ≤ +0.005s | ≤ 0.005s |
| 字幕末条结束时刻 vs 音频尾 | 全部 = 音频尾（Δ≈0.00s） | 同左 |
| 页长 = 音频 + 1.6s 留白 | 8/8 精确成立 | 8/8 精确成立 |
| Σround(页长×30) == TOTAL_FRAMES | 5709 ✓ | 6034 ✓ |

**结论：两集不存在「改文未重录」型字幕/音频背离；字幕恰在语音结束时刻收口，页尾 1.6s 留白全部干净。**

（自查记录：本检查第一版曾报 16/16「文本不一致 + 页长错乱」——归因为脚本两个 bug：正则把 `// p01` 注释当数字抽走、`narration_text` 返回 int 页键而脚本用 `"p%02d"` 字符串键取值取到空串。修正后转绿，非成片问题。）

## 七、交付 mp4 × 工程终态帧交叉（补充：证明「QA 通过」适用于已交付文件）

从 `out/suzhoujie.mp4`（01:16）、`out/zhongguancun.mp4`（08:24）按各页终态帧时刻抽帧，与 `/tmp/qa_frames` 工程帧逐像素比：

- E12：MAD 0.91–3.71/255，热点像素（|Δ|>40）≤0.12%；E13：MAD 0.83–3.30/255，热点 ≤0.02%。
- 最高值 E12 P7（MAD 3.71，hot 0.12%）已目视归因：热点近满幅散布（2506/207 万像素，无局部聚集），左右帧对比图逐元素一致（标题「街废名存」、副题「北起海淀镇·南至万泉庄桥」、[今貌] badge、三条底部说明全部相同）→ **H.264 压缩噪声，非缺陷**（对比图 `/tmp/e12e13_p7_compare.png`）。

即：交付 mp4 与本轮 QA 通过的工程状态是同一渲染。

> 08:19:31 数据修改 → 仍用 08:12 旧帧场景涉及的数据文件精确清单见 §二第 3 条（`src/zhongguancun/data/slots.json`、`src/zhongguancun/data/_meta.json`，mtime 08:19:31；同目录 narration/pageMap/subtitles/pages.config/pages/* 构成同构失效键集）。

## 八、本次走查发现的问题（registry / 工具层）

1. **qa_v2 工具缺口：渲染帧不随数据修改失效**。`frames.py` 注释只警告了 OCR 缓存需手动清，`run._frame_for` 对已存在 png 直接复用且无 mtime 校验——本轮实踩：zgc 数据 08:19:31 修改后，首跑仍判 08:12 的旧帧。建议：抽帧前比对 `src/<ep>` 最新 mtime，或帧文件名绑定数据哈希。**series_registry 的 QA 教训清单未记此条，建议补**。
2. **qa_v2 run 输出无覆盖计数**（每层评估了多少槽/项），「全部通过」无法从输出区分「全覆盖通过」与「零评估通过」；本轮覆盖表靠独立复跑补齐。另 `TAG_IDS` 只含 `evidence_tag`，本两集 tag 槽名是 `badge`——任何按 TAG_IDS 统计 L6 覆盖的口径都会得出「零覆盖」假象（check_l6 本体按 `kind=="tag"` 判定，不受影响）。
3. **内容 registry：无发现**——本路为全档 QA，不含内容红线走查（E12/E13 红线反向走查由 E12BackAudit / E13BackAudit 负责）。

## 附：证据文件

- 运行输出：本文各耗时/计数均为终端实测；独立复核脚本 `/tmp/e12e13_verify.py`，结构化结果 `/tmp/e12e13_verify_out.json`
- mp4 抽帧：`/tmp/e12e13_mp4frame/`；P7 对比图：`/tmp/e12e13_p7_compare.png`
- 幂等性：全档判定在「冷跑（含重渲）」「缓存热跑」「独立复跑」三种状态下结果一致
