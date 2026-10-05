# Source of Truth：真相链、冻结门、MCP 边界

## 1. 真相链（从高到低）

```
研究档案 research.md（证据分级 + 冲突 C 表）
   → facts.py（已裁决事实，带来源等级）
   → assumptions.py（假设层，永不冻结，不参与来源）
   → parameters / build_*.py（生成器）
   → .blend / renders（构建产物，可删可重建）
```

**只有前四层可被引用为"依据"。** 后两层是输出，引用输出当依据 = 循环论证。

## 2. 冻结门

- `refs/freeze_manifest.md` 记录锁死文件哈希；`test_freeze_manifest.py` 在 CI 硬门。
- 改锁死文件的唯一合法路径：`refs/body_changelog.md` 写**改动依据**（哪条来源/哪次实测）
  → 重跑本体判据 → 更新 manifest 哈希 → commit。
- 为什么：复原项目的立身证据是"从零重建、哈希逐位一致"。任何绕过冻结门的手改
  都会让这条证据失效，且失效是静默的。

## 3. 渲染确定性（回归可比的前提）

- `cycles.seed` 固定整数；`use_animated_seed = False`（官方依据：animated seed 每帧改 seed，
  静帧必须关，否则同机位同帧号像素也变）。
- denoise 的 Prefilter/Quality 固定；device 固定（GPU/METAL 或 CPU，不混）。
- 体积雾出现水平硬边：**先查相机 `clip_end`**。默认 1000m 时，出射距离超 1000m 的天空射线
  体积栈为空 → 雾效在仰角 atan(盒顶高/1000) 处变成二元开关（实测 6.9° 硬边，Δ=7.68 灰阶）。
  修法是把 clip_end 拉到雾盒对角之外，雾参数零改动。

## 4. MCP 边界

允许（交互检查层）：
- 列对象/查 modifier/量当前场景尺寸
- 截 viewport 看局部
- 临时移灯/移相机试效果（**不保存**）

禁止（不得成为真相）：
- 在 MCP 会话里改几何/材质后直接存 .blend 当交付
- 用 MCP 执行未经 review 的生成代码绕过冻结门
- 把 MCP 量到的数写进 facts.py 而不注明是"交互测量"（交互测量等级 ≤ 图像推导）

不装的额外理由：官方 MCP 无防护执行 LLM 代码，建议在无敏感数据环境运行；
生产机有真实登录态与全部项目数据。headless 路线天然规避。

## 5. 交互测量的正确归宿

MCP/viewport 量到的数若要用，走：登记为 [图像推导] 或 [工作值] + 注明测量方式，
再设法用 measure 层判据或文献升级等级。**不得直接写成 [官方] 或 [测绘]。**
