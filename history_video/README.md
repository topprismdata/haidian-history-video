# 肖家河·龙背村历史视频 — 制作说明

## 成片
- `/tmp/chemistry-video/out/xiaojiahe-history.mp4` — 1920×1080, 30fps, ~305s (5:05), h264+aac
- 结构：8 页（片头 → 史前汉代 → 曹魏金元 → 白浮堰考古 → 名称考 → 八旗营房 → 1897地图 → 总结）

## 管线（参照 chemistry-video 模式）
1. **ChatGPT（browser relay, 新会话）**：投喂《肖家河与龙背村历史长编》全文 → 其确认并纠错 3 处（1400—1475=15世纪非14世纪；《日下旧闻考》只证"萧家河"写法；正黄旗@肖家河北/镶黄旗@树村西）→ 按 solubility pack 模式设计 8 页课程 + 生成全部视觉资产 → 打包 `xiaojiahe_history_pack.zip`（86 文件：spec/ + reference_pages/ + assets/ 81 PNG）
2. **CosyVoice2（本地，speed=1.15）**：8 段中文配音 292.6s（4.7字/秒），音色 zero_shot_prompt
3. **Remotion**：`src/history/` — HistoryCourse（Series 链页 + 实测音频锚点挂 `<Audio>`），每页资产 + DOM 文字 + 三级证据标签 + 底部字幕（subtitles.ts 按分句时长比例同步）
4. 页时长 = 实测音频 + 1.6s 尾垫；P8 时间轴为 DOM 重建（原 PNG 资产是坏裁切）

## 复渲
```bash
cd /tmp/chemistry-video
npx remotion render src/index.tsx HistoryCourse out/xiaojiahe-history.mp4 --concurrency=4 --overwrite
# 重新生成配音（改文案后）：
cd /tmp/history_video && /tmp/chemistry-video/.cosyvoice-venv/bin/python gen_tts.py && python3 build_history_data.py
```

## 文件索引
- 配音文案：`/tmp/history_video/narration/*.txt`（TTS 版）；`pack/xiaojiahe_history_pack/spec/course_script.md`（字幕版）
- 资产包：`/tmp/history_video/pack/`（同 `~/Downloads/xiaojiahe_history_pack.zip`）
- Remotion 页面：`/tmp/chemistry-video/src/history/pages/Page01-08.tsx` + `ui.tsx` + `data/`
- ChatGPT 会话：`https://chatgpt.com/c/6aba59e1-9b3c-83e8-b6b4-0337f75765cd`
