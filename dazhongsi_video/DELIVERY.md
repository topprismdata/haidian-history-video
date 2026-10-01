# E9《大钟寺》交付说明

## 成片

- 路径：`/tmp/chemistry-video/out/dazhongsi_final.mp4`
- 规格：1920×1080 / 30fps / 5756 帧 / **191.87s** / H.264 + AAC
- Remotion 工程：`/tmp/chemistry-video/src/dazhongsi/`（Composition `DazhongsiCourse`）
- 配音：8 段 Qwen3 克隆音色，纯音频合计 **179.07s**，页尾各留 1.6s

## 本集立论

一口钟的**物理迁移**与**解释的生成**不是同时发生的。

- 器物线：铸钟厂 → 汉经厂 → 万寿寺（1607）→ 觉生寺（**1743**）
- 解释线：乾隆八年的诗还只是佛教语汇（「善吼周三界·声闻具六通」）；
  到**乾隆十一年（1746）**的《大钟歌》才把钟与靖难、忠臣、忏悔绑在一起

**中间隔三年。** 本集全部版式都为这条结论服务：P7 把 1743 与 1746 画成两条独立时间线，
中间用「三年」跨度连接，并明写「这三年里，钟一直在殿上，解释还没有发生」。

## 事实红线（成片已逐页核验）

| 禁用 | 出现情况 |
|---|---|
| 「1424」 | 零出现 |
| 「至元九年」 | 零出现 |
| 「5.5 米」 | 零出现（通高一律 6.75 米） |
| 「230,184 / 230184」 | 零出现 |
| 1743 与 1746 混同 | 零出现（**P7 明确分开**） |
| 1733 开工 / 1734 赐名 混用 | 零出现（**P2 明确分开**） |
| 「皇家祈雨法器」讹传 | 零出现（P5 立论即纠正此说） |

## 逐页验收

| 页 | 标题 | 槽位 | 验收 |
|---|---|---|---|
| P1 | 一口钟，一个名字 | 6+tag | PASS |
| P2 | 寺先建，钟后来 | 7+tag | PASS（「北」字无底板，设计如此） |
| P3 | 46.5 吨，一口钟 | 11+tag | PASS |
| P4 | 一口钟，四次安放 | 12+tag | PASS（斜纹编码：左二空右二斜） |
| P5 | 不是三百年，是一百二十年 | 8+tag | PASS |
| P6 | 钟搬进寺，碑立在钟的东边 | 10+tag | PASS（1743 已补入） |
| P7 | 钟挂好了，解释还没来 | 9+tag | PASS（1743/1746 分开） |
| P8 | 同一口钟，一条街名 | 13+tag | PASS（竖排印章不溢出） |

**86 槽位全部有底板、无溢出、无遮挡、无重叠。**

## 本集修掉的真缺陷

### 1. P4 板面斜纹编码画反（插画级，整版作废重出）
证据等级带的斜纹给了「铸钟厂/汉经厂」（实为研究推断），而「万寿寺/觉生寺」（实为文献确证）却是空白。
**缺字只是观众看不到，画反的图例会主动教错。** 重出时在 prompt 里把映射写死成清单并强调「左右不要搞混」。

### 2. 终态帧口径错误（浪费三轮时间）
- `bounds` 有两套：Remotion `Series` 用的含 1.6s 留白，`_meta.json` 的是纯音频累加。P4 处差 **144 帧**。
- 照 `_meta.json` 抽帧会渲到**前一页的尾巴**，症状是"槽位缺字"且**换任何帧号都不补齐**——
  极易误判成 `pageDur`/`anchor`/数组截断/缓存/坐标错位。
- 修正：`/tmp/e9_frames.py` 为唯一权威口径；终态帧取「纯音频结束处」而非「纯音频末 − 0.5s」
  （末项进场按 anchor 铺满，取更早会漏——P6 的 `compass` 实测页内 842 帧才出现）。

### 3. `pageDur` 取了整片时长
`useVideoConfig().durationInFrames` 是整部视频帧数，不是当前 `Sequence` 页长。已改为由 `PAGE_DURATIONS_SEC` 累加。

### 4. P8 印章竖排溢出（抄 E8 时漏字段）
E8 是 `vertical: true` + 3 字「大钟桥」；E9 抄字段但换 14 字文案且漏了 `vertical`，
横向渲染撑破 300×80 槽位并压住邻槽。**抄样式字段必须连文案长度一起看。**

### 5. P6 缺 1743（本页主题年份）
探针片阶段发现——白底让"该有字却没字"一眼可见，已补 `move_year` 槽位。

### 6. 5 处槽位被字幕条压住
`Caption` 固定 `bottom:8`，占 y≈988–1072 横跨全宽，**矩形相交检测看不见它**（字幕条不是槽位）。
已把这项检查加进 `slotcheck.py` 作为第三层。

## 复现命令

```bash
cd /tmp/chemistry-video
# 逐页终态帧验收（程序化判底板覆盖）
python3 /tmp/qa_page.py            # 1..8
# 终态帧口径
python3 /tmp/e9_frames.py
# 终渲染
npx remotion render src/index.tsx DazhongsiCourse out/dazhongsi_final.mp4 --codec=h264
```

## 文件索引

- 研究档案：`/Volumes/macstudio/video-projects/dazhongsi_video/research.md`（v2，22.9KB，两轮 GPT 复查拦下 29 条硬错误）
- 设计稿：`/Volumes/macstudio/video-projects/dazhongsi_video/design.md`（86 槽位）
- 板面图：`/Volumes/macstudio/video-projects/dazhongsi_video/boards/page_01..08.png`（1672×941）
- 运行时槽位：`/tmp/chemistry-video/public/dazhongsi/page_0N_layout.png`
- 配音：`/tmp/chemistry-video/public/audio/dazhongsi/`
