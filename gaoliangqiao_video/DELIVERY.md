# E8《高梁桥》交付说明

> 海淀历史地名系列 第 8 集 · 交付日 2026-09-30

## 交付物

| 文件 | 说明 |
|---|---|
| `gaoliangqiao_final.mp4` | **成片**。1920×1080 / 30fps / H.264+AAC / 174.76s / 24.3MB |
| `research.md` | 研究档案 v2（18.0KB），GPT 复查闸门 PASS WITH EDITS，16 条硬错误已修正 |
| `design.md` | 八页设计稿（40.9KB），含逐页画面描述、口播稿、槽位几何 |
| `boards/page_01..08.png` | 八张空白板面，1672×941（**内不含任何汉字**） |
| `audio_qwen/p01..08_000.wav` | 八段旁白，合计 161.9s |
| `src/slots_2_7_8.json` | 从 ChatGPT 抽回的 25 个槽位（含 P8 手工补回的 usage） |

## 成片规格核验

```
codec_name=h264 / width=1920 / height=1080 / r_frame_rate=30/1
codec_name=aac  / duration=174.762667 / size=24313693
```

`silencedetect=noise=-35dB:d=1.2` 无输出 → 八段旁白连续覆盖全片，无断轨。

## 八页页码核验

8 个独立验收代理逐页确认，**页码与页序全部正确**：

| 页 | 标题 | 页码 | 关键内容 | 结论 |
|---|---|---|---|---|
| P1 | 一个字，错了二十多年 | 01 | 梁/粱字形对比、错字碑、纠错时间线 | PASS |
| P2 | 一条河，身份换过三次 | 02 | 永定河故道→高梁水→长河/转河 | PASS |
| P3 | 1198 年河上已经有闸了 | 03 | 金承安三年《金史》"勿毁高梁河闸" | PASS |
| P4 | 1292：郭守敬 重构一套水利系统 | 04 | 瓮山泊→积水潭→1293 通惠河 | PASS |
| P5 | 979：古高梁河畔的一场大败 | 05 | 太平兴国四年＝辽景宗乾亨元年、乘驴车南逃 | PASS |
| P6 | 明清："京师最胜地" | 06 | 袁宏道《游高梁桥记》、资安/广润牌坊 | PASS |
| P7 | 一条河，被城市改写 | 07 | 1905/1970s/2002/2003 | PASS |
| P8 | 一座桥 两座城区，两套名字记录 | 08 | 界桥、2013 第七批国保、2024 地名名录 | PASS |

## 修复清单（v1 → v4）

成片经过 4 版，每版修一处真缺陷：

### v2 — 页边界累积漂移（最严重）

`pages.config.ts` 的 `bounds` 起点每页比实际音频起点晚 **0.4s**，逐页累积到 P7 达 **+9.6s（288 帧）**。

**症状极具误导性**：抽 P7 的帧看到的是 **P8 的内容**，于是 8 个验收代理里 5 个报"槽位空字"，看起来像渲染失败，实际是**看错了页**。

**根因链**：`PAGE_DURATIONS_SEC`（音频 + 1.6s 留白）→ `pageOffsetFrames` → `bounds`。留白是**页尾**的，不该计入下页起点。

**修法**：`bounds` 起点 = 前序各页**纯音频时长**累加。

| 页 | 修正前 bounds | 修正后 | 偏差 |
|---|---|---|---|
| P1 | 0 | 0 | 0 |
| P7 | 3897 | 3609 | −288 |
| P8 | 4562 | 4226 | −336 |

### v3 — P7「1905」不可读

`railway_1905` 是 P7 四个年份项中**唯一**没用 `backing: true` 且用 `SOFT` 淡色的，字压在铁路工人插画的碎石与人物轮廓上，终态帧实测"1905"几乎不可辨。改为 `INK` + `backing: true` 后确认清晰可读。

### v4 — 其余三处底板 + 一处内容缺口

| 槽位 | 问题 | 修法 |
|---|---|---|
| `stage_independent` | sub「东汉后独立水系」无底板，压在插画树木上 | 加 `backing: true` |
| `torch_note` / `military_analysis` | 同病（P5） | 加 `backing: true` |
| `toponymy_2024` | sub 无底板，叠在卡片边缘 | 加 `backing: true` |
| `heritage_2013` | **缺「第七批」批次表述**，成片只写"列入国保" | 补全为"第七批全国重点文物保护单位" |

**共性**：六处缺陷里四处是"漏配 `backing: true`"。该字段是人工逐项写的，**漏配无任何编译或运行错误**，只在成片里表现为"某个 sub 压在插画上看不清"。

## 误报记录

多个验收代理报"标题首字被裁切"。放大裁切交叉验证后确认是**我给的裁剪窗口 `(80,50)-(1010,185)` 切到了标题框**，标题「一条河，被城市改写，又重新露出水面」首字「一」完整可见。这类"我的测量工具切到了"与"真裁切"必须分开判定。

## 复现命令

```bash
# 1) 板面：ChatGPT 产出 page_XX.png，复制为渲染端要求的 page_XX_layout.png
cd /tmp/chemistry-video/public/gaoliangqiao/
cp /Volumes/macstudio/video-projects/gaoliangqiao_video/boards/page_0{1..8}.png \
   page_0{1..8}_layout.png

# 2) 旁白（Qwen3 克隆音色）
bash /Volumes/macstudio/video-projects/gaoliangqiao_video/gen_tts_gaoliangqiao.sh

# 3) 渲染
cd /tmp/chemistry-video
npx remotion compositions src/index.tsx | grep -i gaoliangqiao
npx remotion render src/index.tsx GaoLiangQiaoCourse \
   out/gaoliangqiao_final.mp4 --concurrency=4
```

## 验收帧抽取时刻（E8 最终 v4）

`Enter` 按 `idx` 把 items 铺满 `anchor = 音频结束 − 0.5s`，所以**中点帧必然缺字**——那是设计，不是缺陷。

```python
终态帧 = 页起点(含留白) + 该页纯音频时长 − 0.2s
页起点_n = Σ_{i<n}(纯音频_i + 1.6)
```

| 页 | 终态帧 | 页 | 终态帧 |
|---|---|---|---|
| P1 | 19.2s | P5 | 105.7s |
| P2 | 41.8s | P6 | 128.1s |
| P3 | 61.5s | P7 | 150.3s |
| P4 | 84.1s | P8 | 172.9s |

## 交付前静态扫描（省两次渲染的关键）

```python
import re
s = open('data/pages.config.ts', encoding='utf-8').read()
blocks = re.findall(r'\{\s*slotId:\s*"([^"]+)"(.*?)\n      \}', s, re.S)
bad = [sid for sid, body in blocks if 'sub:' in body and 'backing:' not in body]
print('带 sub 但无 backing:', bad)
```

槽位矩形两两相交检测：

```python
# 见 remotion-slot-page-pipeline 托管技能
# 阈值 12%，豁免"匾额+题款""轴标签+年份"等刻意堆叠对
```
