# Task 2: M0 本体研究——核实存疑清单并回填 facts

> 本文件由计划自动抽取，是该任务的**唯一需求来源**，其中数值必须逐字照用。

### Task 2: M0 本体研究——核实存疑清单并回填 facts

**Files:**
- Modify: `e30_shikongqiao_video/3d/facts.py`（等级/数值/RESEARCH_DONE）
- Create: `e30_shikongqiao_video/3d/refs/FACTS.md`

**Interfaces:**
- Consumes: Task 1 的 facts.py 结构
- Produces: `RESEARCH_DONE=True`；全部等级 ∈ {测绘,文献,实拍,工作值}；FACTS.md 人读版

- [ ] **Step 1: 逐项检索核实（web 搜索，按此查询序列，记录命中 URL 与原文数字）**

必查项与建议查询：
1. 桥长/桥宽：`颐和园十七孔桥 长 宽 官方`、`site:summerpalace-china.com 十七孔桥`、`北京市公园管理中心 十七孔桥`
2. 孔跨：`十七孔桥 跨径 中孔 测绘`、`十七孔桥 净跨 米`、`颐和园 十七孔桥 桥墩 测绘`
3. 起拱线/矢高：`十七孔桥 半圆券 矢高`、`颐和园石桥 测绘图`
4. 纵坡/桥面标高：`十七孔桥 桥面 坡度 中间高`
5. 墩厚：`十七孔桥 桥墩 分水尖 厚度`
- 优先级：测绘档案（天津大学梁雪《颐和园测绘笔记》第18节、孔庆普《中国古桥结构考察》——G1 提供线索，须追原件）> 官方机构专题页 > 学术论文 > 百科（只作线索）
- 学术线索（用户 2026-10-04 追加检索所得，均为**待核原文**的线索）：严雨等《清漪园桥景及十七孔桥空间形态》（北京建筑大学设计学院）；夔中羽等颐和园布局遥感考证（测绘科学研究院，"龟颈"意象）；金光穿洞天文-建筑考证（北京市政府网 2023-12-01 转载：桥身"西北—东南走向"）；修缮与病害文献（风化/冻融/石狮裂纹，《古建园林技术》等刊）
- 期刊入口：《建筑学报》《古建园林技术》《风景园林》《建筑史学刊》《文物》；检索式 `颐和园+十七孔桥+考证`、`清漪园+桥景+建筑学报`、`皇家园林+石拱桥+测绘+保护`、`样式雷+昆明湖+布局+测绘`
- **已查实（二手文献多源一致，入 FACTS.md 史料节，非几何事实）**：清乾隆年间（约1750）建；形制蓝本卢沟桥+宝带桥；544 只石狮；长约150m、宽8m（与6.56并存的通俗口径）
- **新冲突 C4**：`BRIDGE_AXIS_AZ` 现状 112°(ESE) vs 官方转载"西北—东南"(135°)，差约23°。影响 M5 冬日日照，**不影响 M2 本体几何**；登记入冲突表待裁
- **已锁定 [官方]（勿重复劳动）**：150m / 上宽6.56 / 下宽14.6 / 高7 / 17孔（北京市公园管理中心专题页，中新网2025-12、visitbeijing、北京日报多源一致）
- **搜不到的项：等级落 `[工作值]`，出处写"无文献, 沿用现脚本值"**
- 禁止把网页里 GPT 生成的旅游文案当文献

- [ ] **Step 2: 回填 facts.py（数值变则改值，等级/出处必改；RESEARCH_DONE=True）**

示例（以检索结果为准，禁止照抄此示例的数字）：

```python
RESEARCH_DONE = True
BRIDGE_LEN = 150.0        # [文献] 颐和园官网《十七孔桥》页: "全长150米" (URL)
DECK_UP_W = 8.0           # [文献] 同上: "桥宽8米" —— 若核实确为8, 同步改收分相关判据期望
```

同时更新 SOURCES 对应行。**注意**：若 DECK_UP_W 等变化导致 build_scene2 下游构件（栏板等非本体件）错位，本计划不管（M3 处理），本体判据必须反映新值。

- [ ] **Step 3: 写 FACTS.md（人读表：名 | 值 | 等级 | 出处/URL | 备注）**

- [ ] **Step 4: 跑测试确认 PASS（含 test_no_pending_after_research）**

Run: `cd /Volumes/macstudio/video-projects && python3 -m pytest e30_shikongqiao_video/tests/test_facts.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd /Volumes/macstudio/video-projects
git add e30_shikongqiao_video/3d/facts.py e30_shikongqiao_video/3d/refs/FACTS.md
git commit -m "feat(e30): M0 本体研究回填 facts——存疑清单逐项定级"
```

---

