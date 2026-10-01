# 海淀历史地名培训视频 · 生产流水线

用外部工具（出图模型 + 克隆音色 TTS + Remotion）批量生产中文历史短视频。
已交付 9 集，单集 3–4 分钟、8 页、1920×1080 / 30fps。

**方法论与全部踩坑记录见 [`METHODOLOGY.md`](METHODOLOGY.md)——先读那份。**

---

## 快速上手

```bash
# 1. 装 TTS 工具链（venv + mlx-audio，只需一次）
./scripts/setup_tts.sh
#    然后按提示放：
#      tts/models/qwen3/Base-1.7B     模型（2.9 GB，手动下载）
#      tts/voices/ref_10s.wav         你的 10 秒参考音频
#      tts/voices/ref_10s.txt         该音频的逐字文本

# 2. 装视频合成依赖（在 Remotion 工程目录里）
npm i remotion@4.0.529 @remotion/cli@4.0.529 \
      @remotion/bundler@4.0.529 @remotion/renderer@4.0.529 \
      @remotion/media-utils@4.0.529 react@19.2.3 react-dom@19.2.3

# 3. 新开一集
mkdir -p <集名>_video/{boards,prompts,narration}
```

---

## 一集的目录

```
<集名>_video/
  research.md          史料档案（证据分级 + GPT 闸门修订记录）
  design.md            立论 + 八页结构 + 槽位坐标 + 全片红线
  slotcheck.py         槽位几何校验（三层）
  make_prompts.js      从 design.md 生成 8 份送图 prompt
  prompts/page_01..08.txt
  boards/page_01..08.png      板面图（1672×941，零汉字）
  narration/all.json          8 段旁白文本
  DELIVERY.md          交付说明（成片规格 + 逐页验收 + 修掉的缺陷）
```

---

## 九步流程

| # | 步骤 | 命令 / 动作 | 卡点 |
|---|---|---|---|
| 1 | 研究 | 写 `research.md` → GPT 复查 → **逐条独立核实** | 闸门意见 8% 概率是错的 |
| 2 | 设计 | 写 `design.md`（立论 + 八页 + 槽位 + 红线） | 必须一句话说清立论 |
| 3 | **校验** | `python3 slotcheck.py` | **零冲突才能往下走** |
| 4 | 生成 prompt | `node make_prompts.js` | 坐标自动读，不手抄 |
| 5 | 出图 | 改 `scripts/send_board_prompt.js` 的 `N`/`EP`，逐页发 | 见下 |
| 6 | 验收板面 | 视觉模型问「有无汉字」**+ 逐格核对图例编码** | 零汉字 ≠ 画对了 |
| 7 | 配音 | 写 `narration/all.json` → `./gen_tts.sh <集名>` | **必须在设计定稿后**（时长决定时间轴） |
| 8 | 装配 | `cp -r remotion-template <工程>` → 改 4 处 → `python3 build_remotion_data.py` | 见 `remotion-template/README.md` |
| 9 | 渲染验收 | `python3 scripts/qa_page.py` → `npm run render` | 终态帧口径见下方警告 |

**旁白 JSON 格式**（`gen_tts.sh` 的输入，键名建议 `p01`…`p08`）：

```json
{ "p01": "第一段旁白……", "p02": "第二段旁白……" }
```

> ⚠ **页长与页起点是两套口径**：
> 页长 = 纯音频 + 1.6s 留白；页起点 = 前序各页**纯音频**累加（**不含**留白）。
> 留白是页尾的，计入下一页起点就会逐页漂移（E8 曾累计 +288 帧）。

**第 3 步零成本，能省 1–2 轮白渲染。E8 跳过它，白渲 2 版才修完 6 处缺陷。**

## 克隆后能直接做什么

```bash
git clone <repo> && cd haidian-history-video

python3 landianchang_video/slotcheck.py      # 校验槽位（应零冲突）
node landianchang_video/make_prompts.js     # 重新生成送图 prompt
./gen_tts.sh <集名>                          # 生成配音（需先 setup_tts.sh）
```

第 8/9 步的起点是 `remotion-template/`，其 README 列了要改的 4 处。

---

## 三个最贵的坑

**1. `tab.run` 的 `args` 传参是坏的。**
`{args:[X]}` 传进去的是 `[object Object]`，连数字都中招。
零参数调用，值写死在函数体内。详见 METHODOLOGY §5.4。

**2. 终态帧口径有两套。**
`PAGE_DURATIONS_SEC`（含 1.6s 留白）vs `_meta.json` 的 `bounds`（纯音频）。
用错会渲到前一页的尾巴，症状是"槽位缺字且换任何帧号都不补齐"。

**3. 零汉字红线不够。**
E9 P4 板面尺寸全对、零汉字、槽位全留白，却因**图例编码画反**而整版作废——
缺字观众看不到，画反的图例会主动教错。

---

## 脚本

| 脚本 | 用途 |
|---|---|
| `remotion-template/` | Remotion 合成工程模板（第 8/9 步的起点） |
| `scripts/setup_tts.sh` | 一键装 TTS 工具链（Darwin/arm64） |
| `gen_tts.sh` | 生成一集 8 段旁白（断点续跑） |
| `scripts/send_board_prompt.js` | 送图（改 `N` / `EP` 两行） |
| `scripts/wait_ready.js` | 等 ChatGPT 结束响应 |
| `<集名>_video/slotcheck.py` | 槽位几何三层校验 |
| `<集名>_video/make_prompts.js` | 生成送图 prompt |

**所有路径从脚本自身位置或环境变量推导，无机器专属硬编码。**
可用环境变量：`ROOT` `TTS_HOME` `AUDIO_DIR` `BOARD_ROOT` `TTS_PYTHON` `TTS_MODEL` `TTS_REF` `TTS_REF_TEXT` `PAGE_GAP`

---

## 已交付

E1 肖家河 · E2 安河桥 · E3 青龙桥 · E4 有大庄 · E5 一亩园 ·
E6 娘娘府 · E7 西三旗 · E8 高梁桥 · E9 大钟寺

E10 蓝靛厂：研究 v2 定稿，设计稿 107 槽位零冲突，**板面 8/8 全部验收 PASS**，
配音与 Remotion 装配进行中。逐页验收记录见 `landianchang_video/SEND_LOG.md`。

---

## 硬件前提

Apple Silicon（`torch.backends.mps.is_available()`）。M1 Max / 64GB 实测。
TTS 走 MLX，CPU 跑不动。详见 METHODOLOGY §0.1。
