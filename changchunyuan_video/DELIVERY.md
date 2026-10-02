# E14《畅春园·消失的园》交付

- **成片**:`/tmp/chemistry-video/out/changchunyuan.mp4`(1920×1080@30,5556 帧,185.2s,18.3MB)
- **管线**:Qwen3-TTS ref_user_E(8 段 172.4s)→ SlotPage 槽位填字 → h264 crf20
- **QA v2**:快档 fail 0 / 全档(--ocr)fail 0,唯一 warn=P1/badge 圆徽记纸色白占比(非阻塞)
- **闸门链**:研究 v2(FAIL→采纳)→ 设计 v1 GPT 审校 **FAIL(23 项)**→ v2 全修 → 复审 **PASS WITH EDITS(2 项)**→ v2.1 落完
- **实现要点**:5 AI 板图+3 纸面排版页;P2 石匾伪刻字 PIL 抹平;P3/P6 顶卡裁弃改底带承载;P5 屏显纪年随口播用词(L4-c 抓出公元年与口播不一致);底带槽位抬到板面 y≤850 避开字幕条
- **反向走查**:1723/「60 年」/「第一座」/问安路链/长河串三山 均未出现;引文「京国第一名园也」「述耳食而鲜目击」逐字上屏
- 遗留:P6 左上 GPT 残卡已修;板图源文件在 `boards/`(不入库),重渲需 public/changchunyuan/
