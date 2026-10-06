# M18 逐块复刻拱肩+桥墩贴面砧石(重写 build_coursing)— 报告

隔离工作树: `/tmp/e30_m18_stone/`(refs 软链)。已同步回主树 `3d/`(masonry.py,
build_scene2.py, stones/stones_p8.json, 重建的 e30_bridge.blend / masonry_stats.json),
**未 commit**(工作区 M: masonry.py / build_scene2.py / masonry_stats.json / blend / 若干渲染 PNG)。

## 1. 照片量测(refs/community_photos_details/2017-05-20_A_closer_view_of_the_17-arch_bridge.jpg)

裁剪: 原图 (1500,300)-(3700,2600) → 2200×2300。判读对象 = 画面最前方整孔
(中央跨, a=4.25, b=4.76, spz=1.99, xc=0, deck 7.75)及其右邻跨。

| 量测项 | 方法 | 结果 |
|---|---|---|
| 竖直比例 sy | 两圆心拱曲线 4 参仿射最小二乘拟合(274 边界点, 中位残差 0.76px) | 181 px/m |
| 竖直比例 sy(交叉) | 桥面顶(y740, z=7.80)→拱脚(y≈1883, z≈1.99) | 197 px/m |
| 水平比例 sx | 冠距法: 前两孔 intrados 冠点 (667,1040)/(987,947), Δ=320px / 9.385m | 34.1 px/m |
| 水平比例 sx(交叉) | 拟合 29.2 / 墩面缝隙上限 38.8 | 取 33±5 |
| **主层高** | 左拱肩 x530-585 层线 1011/1114/1216 | 102,103px → **0.55±0.05 m** |
| **冠顶环带薄层** | 拱冠环上方 2-3 道 | 35-38px → **0.19-0.21 m** |
| **块宽** | 层带内竖缝 | 59px≈1.8m, 39-40px≈1.2m, 22-24px≈0.7m → 1.0~1.8 长块为主+0.55~0.95 短块调剂 |
| 墩身缝 | 墩面竖缝上下对直(非错缝), 层高 ~91px≈0.49m | 对直成列 ✓ |
| 缝宽 | 暗线 2-3px | 8-16mm → 取 10mm(GAP_W) |
| 券环外露宽(参考) | 冠顶环带宽 55-65px | ≈0.30-0.35m(比模型 RING_T=0.54 窄; RING_T 冻结未动, 记录差异) |
| 贴拱切块 | 拱肩块下沿咬 extrados, 底沿为曲边; 起拱线处券石座承压面下有座石 | 已按此复刻 |

每孔拱参数(bridge_geom2 实取): spans=[4.5,4.9,5.4,5.9,6.4,6.9,7.4,8.0,8.5] 对称,
xc=PIER_X[i]+PIER_X[i+1] /2, spz=arch_springer_z(i)(中央 1.99, 端孔 0.958),
b=arch_rise(i)(中央 4.76, 端孔 2.07; 端孔 b<a 为单心平拱分支)。

## 2. stones_pX.json 数据格式(M20 模板 = 3d/stones/stones_p8.json)

```json
{
  "courses": [ {"z0": <层底z m>, "blocks": [<x边界序列 m, ≥2 递增>]
               | "block_centers": [<x中心序列 m>]} ],   // 拱肩+腹孔间实腹墙, 逐层
  "pier":    {"cols": [<竖缝列 x 边界>], "courses": [<z 边界序列>]}, // 该孔左侧墩(=墩i)
  "ring":    {"counts": <每孔券石块数>, "phase": <冠部角相位 rad>}   // 兜底 VOUSSOIR_TARGET
}
```
- 坐标语义: **x=桥轴系**(与 PIER_X/deck_z 同系, m; 端点应落在墩面线内),
  **z=水面起算高**(水面 z=0)。层顶=下一层 z0; 末层顶=桥面底 deck_z(x)-0.10(逐块沿
  桥面曲线裁)。贴拱切块与桥面裁切由几何自动施加, **谱只给水平排版**。
- 对称规则: 只允许写 p0..p8; **p9..16 由加载器镜像复用 p(16-i)**(x 取负反序;
  ring 原样)。谱按键粒度生效: courses/pier/ring 各自缺省时该项退程序兜底。
- blocks=边界序列; block_centers=中心序列(边界取相邻中点, 端部半均距外推)。
- 加载判据: `E30_STONES_DIR` 环境变量或 `3d/stones/stones_pX.json` 存在即走数据路
  (打印 `M18_SPEC pX`), 文件缺失/损坏/字段非法 → 打印 `M18_SPEC_BAD` 后该项程序兜底。
  stats 新增 `spec_arches`(当前生效孔列表)与 `coursing_regions`。
- ring.phase 语义: 名义半张角 θ=atan2(a,b) 度量的冠部角偏移, 换算弧长 ds=phase·L/(2θ)
  施加于内部放射缝(端点钉在起拱线, 端块保 6% 弧长); counts 奇数化(|1)。

示例 `stones_p8.json` 为手写中央孔谱(上文照片量测值): 水线层 0.15/0.85, 主层
0.85/1.42/1.98/…/6.46, 冠顶薄层 6.90/7.12/7.34, 墩8 cols=[-5.72,-5.00](三分对直),
courses 14 道, ring counts=17 phase=0。它当前在主树**真实生效**(stats.spec_arches=[8])。

## 3. 程序兜底布局(无谱孔)

- 分区: 拱肩+腹孔间实腹墙(bay: 墩面到墩面, |x|≤72) / 墩区(16 内墩, 竖缝对直:
  每墩 2 列三分, 谱可覆盖) / 端区 |x|>72(旧 M17f 均匀错缝 `_wedge` 原样, 冻结)。
- 层高: 水线第一层 0.15~0.85 加高(照片近水大块), 其上 0.50~0.63 随机
  (照片 0.55±); 层顶帽=湾内最大桥面底(曲线差由逐块裁切吸收); 墩区从墩脚带顶 1.20 起砌。
- 块宽: 1.0~1.8 长块为主(^0.8 偏大分布)+18% 概率 0.55~0.95 短块; 每层独立随机错缝;
  边界缝调整后的**有效宽**<0.30m 并入邻块(先调缝后判宽, 防墩面 300mm 露体带)。
- 贴拱切块: 洞+环带切割下沿=extrados+GAP_W 沿外法向偏置曲线(等弧长采样 ~0.1m,
  拱脚端点法向钉 (∓1,0) 防 dd=0 退化); 承压带(a+GAP..a+RING_T+GAP)切割封顶
  spz-GAP, 并自动落**券脚承压座石**[z0, spz-GAP]; 顶 course 贴桥面曲线裁
  (deck-0.10-GAP_W), 残高≤20mm 才弃。
- 全部块经 `_stone`: 前脸逐顶点 hw(x,z)+STONE_PROUD(8mm, 22° 收分跟随, M17f _wedge
  同规则推广到曲边), 背咬 0.30m; 真实几何缝 GAP_W=10mm(露本体成暗线); 前后脸块局部米 UV。

## 4. 每孔块数统计(主树重建, build_scene2 输出)

- MASONRY total 2767 = 券石 193(每孔 [7,9,9,11,11,13,13,15,17,15,13,13,11,11,9,9,7],
  =VOUSSOIR_TARGET, 谱 counts 未改) + coursing 2574
- coursing_regions: endzone=92 / pier=998 / bay=1484(前后墙合计; M17f 基线为 2068 均匀盒)。

## 5. 验收数字

| 验收项 | 结果 |
|---|---|
| build_scene2 零 Error/Traceback | ✅(隔离与主树各一遍, grep 计数 0) |
| qa_l2 | ✅ QA_L2_OK(隔离+主树) |
| _check_abutment | ✅ 32/32 PASS(隔离+主树) |
| pytest tests/bridge3d(主树) | ✅ **312 passed** |
| 水密 coursing/voussoir boundary edges | ✅ 0/0(`_m18_smoke.py`) |
| 平色消融 arch 1200px 暗带 | ✅ 拱肩带暗像素占比 0.193→**0.019**(基线→M18, 10×↓); 拱腹带 0.397→0.207; 墩水线带 0.548→0.379(`_m18_final_abl_arch.png` vs `_m18_baseline_arch.png`) |
| 露体带判据(几何) | ✅ `_m18_verify.py`: 候选域暴露 7.46m², 其中腐蚀(24mm)存活 0.72m²=0.006% 墙面, 为环冠过渡带 25-170mm 离散残条(58 簇), 渲染不可见; 全部构造缝=10mm |
| 并排 montage | ✅ /tmp/e30_m18_stone/m18_cmp_arch.png(同弦长标定), m18_cmp_hero.png, m18_cmp_side.png |
| 块宽/层高 vs 照片 ±20% | ✅ 层高程序带 0.50-0.63 vs 0.55±0.05; 块宽 0.55-1.80 vs 1.0-1.8(长块为主)分布一致; stones_p8 层高 0.53-0.56 段=0.55±0.03 |
| 冻结项 diff | ✅ bridge_geom2.py/facts.py/assumptions.py 隔离副本==主树逐字节相同(diff 空); materials.py 主树有他人并行改动(本任务未触碰); RING_T/VOUSSOIR_TARGET/BARREL_PROTRUDE/JOINT_GAP/deck_z/墩宽/端区逻辑/灯光零改动; 无 git commit |

证据文件(隔离目录): `_m18_smoke.py`(水密), `_m18_verify.py`(露体带),
`_m18_smoke.py` 输出 WATERTIGHT_OK, `_m18_baseline_arch.png`/`_m18_final_abl_arch.png`
(消融对照), `m18_cmp_*.png`(并排), `_m18_exposed_mask.png`(覆盖掩膜),
`stones/stones_p8.json`(M20 模板)。

## 6. 遗留风险

1. **环冠过渡残条(0.72m²)**: 贴拱切割线与判据排除边界在冠顶相差 ~8mm(离散化),
   个别列成 25-170mm 细条; 渲染不可见, M20 数据路逐孔替换时可随谱消除。
2. **照片环带宽 ~0.32m vs 模型 RING_T=0.54m**: 该近景实测比七审工作值更细;
   RING_T 冻结未动, 若后续解冻建议单独复核(冠顶弦向)。
3. **spec pier 顶闭合**: 数据路 pier.courses 低于桥面底时加载器自动补桥面帽
   (打印无专门标记); M20 谱建议直接给到桥面底。
4. **materials.py 主树有并行改动**(非本任务), build_scene2 仅改了 m_course
   joint=0.014→0.0005(程序缝关, 几何缝接管), uv_joints=True 保留无害; 若他人改了
   qingshi_material 签名需主控合并确认。
5. 渲染回归基线(core_hash/l2_baseline)未重冻结——按分工属主控落盘后统一重冻结。
