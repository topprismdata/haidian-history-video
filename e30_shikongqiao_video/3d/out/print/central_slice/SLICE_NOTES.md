> **G2 门未过(verdict=FAIL), 本包作废待 T9。**红门明细见 out/print/g2_report.json(check_stone.fail_matrix / ring_dedup)。

# ARCH09 中央孔试印包 SLICE_NOTES

G2 门产物: 全石流形+壁厚+分批+装配图 (report verdict: FAIL)

## 口径
- 模型比例 1:50 (scale=0.02); 打印件毫米 = 模型米 x 20。
- 床 220x220mm; 贪心货架装箱(manifest.batches), 允许旋转: 90° 归一+45° 对角斜置(fit_diagonal 非独占批), 真放不下才 oversize 独占。
- 配合缝双值: 每石 clearance_print_mm/clearance_model_mm 见 manifest.stones (FIT 自动分档: 最小维 <0.3m TIGHT / <1.0m NORMAL / 否则 LOOSE)。

## 体积口径声明(T8b-E8, 审查点 2/5)
1. manifest 体积 = 散度定理逐面求和, 三角化按 triangulate_faces
   约定(四边形固定 0-2 对角剖分 + ≥5 边形 x-z 耳切)。_voussoir
   侧面是翘曲四边形(JOINT_GAP 前缘 12.5 / 后缘 4.0mm), 体积对剖分
   对角约定敏感: 两对角约定实测最大相对差 6.2e-3 —— 本 manifest
   的 cm3/h 数字是【耳切对角约定】口径, 换剖分器有 ~0.6% 级漂移,
   不是同一数字。
2. 估时 128.8h 是【实心体上界】(12cm3/h 经验): 未扣 infill/支撑/
   失败重打; 实际耗时的唯一权威是切片器实测。
3. CORE 体积与面石【有意重叠】(y_extent=full_wall, 牺牲芯建模语
   义) —— 各族体积不可加和成'净打印料'; 与面石同批时以面石外形
   为准抠芯。
4. 超床件以旋转后判定: 对角斜置(fit_diagonal)非独占批 0 块: 无
   真超床独占批(oversize) 2 块: ARCH09.EAST.RING.C00.B01, ARCH09.EAST.RING.C00.B17

## 缝的打印当量(模型 mm -> 打印件 mm)
- 券环放射缝 JOINT_GAP 12.5 -> 0.25; 后端 4.0 -> 0.08。
- 砧石真缝 GAP_W 10.0 -> 0.20; 面石-背衬隐缝 BACKING_GAP 2.0 -> 0.04。
- 装配制造间隙 FIT(TIGHT/NORMAL/LOOSE)= 0.15/0.30/0.50 (打印件
  直接尺寸, 非 1:50 换算; 1:50 下历史缝仅 0.04-0.25mm, 打不出,
  故配合靠 clearance 不靠历史缝)。
- 带裁片的环-墙切割缝: 切割面与 RING 相贴(表征界面)但同样吃 FIT
  余量, 打印当量 = GAP_W 0.20 + 2×clr ≈ 0.5-0.8mm —— 试印见此量
  级宽缝属口径预期, 不是模型错误(T8c 口径披露, 复审实测)。

## 构成
| 族 | 数量 | 体积 cm3(打印件) |
|---|---|---|
| impost-step | 24 | 5.68 |
| ring-wedge | 17 | 548.74 |
| slab | 5 | 495.09 |
| wedge-std | 188 | 496.55 |

- 石数: 234 (roles: {"BACK": 94, "CORE": 5, "IMPOST": 24, "RING": 17, "SPANDREL": 94})
- 总体积: 1546.1 cm3(耳切对角约定口径, 实心体上界); 0.4mm 喷嘴 FDM 经验估时 ~128.8 h。

## RING 真相弃用/修配件清单(T8b ring_dedup)
- 带 subsume(整块弃, 材料由 RING 代表): 0 块; trim(按 masonry 切割折线裁短后保留拼装): 475 块; 裁后薄片(thin_merge, 不单独印): 0 块。明细: g2_report.json ring_dedup.pairs(逐块 collide/unique 体积 pre-inset 口径)。
- trim 修配件 id: ARCH01.EAST.CORE.C07.B00, ARCH01.EAST.CORE.C08.B02, ARCH02.EAST.CORE.C09.B00, ARCH02.EAST.CORE.C09.B02, ARCH02.EAST.SPANDREL.C04.B00, ARCH02.EAST.SPANDREL.C04.B04, ARCH02.EAST.SPANDREL.C05.B00, ARCH02.EAST.SPANDREL.C05.B02, ARCH02.WEST.SPANDREL.C04.B00, ARCH02.WEST.SPANDREL.C04.B04, ARCH02.WEST.SPANDREL.C05.B00, ARCH02.WEST.SPANDREL.C05.B02

## 切片器注意
1. 底面平板朝上打印序: 每石以【最大平整面】贴床 —— RING/IMPOST 以
   前脸(y 向大面)朝下, SPANDREL 以层带下缘贴床, CORE 以顶/底大面
   贴床; 悬垂超过 45° 的券腹内弧面加支撑或摆成拱脚两端对称成对印。
2. RING 楔形件放射缝端面薄(端孔 7 块时弦宽大、楔角小), 摆放时让
   内弧朝上避免台阶纹打在券脸上。
3. history 缝 0.2mm 级在 0.4mm 喷嘴下会糊死, 不要试图打缝 —— 缝
   由装配间隙(FIT)表达; 相邻批拼装按 manifest.batch 顺序。
4. 几何已打印视图三角化(triangulate_faces: 四边形对角剖分 + 非凸   帽面耳切), STL/3MF 全三角面, 无 >3 边形; 顶点未做任何修补,
   与 families 账目逐位同源。
5. 装配图 assembly_ortho.png 为 -Y 正射侧视(账目坐标系未旋桥轴),
   RB<块>=券环块号, IM.<阶>.<段>=西墙起拱脚步, S<层>.<块>=西墙面石;
   全 id -> 文件映射见 manifest.json stones[].stl。
6. 面石-背衬隐缝设计值 2mm(T8b-A1 修复后全链恒等式核验); 若个别
   对仍示实体干涉, 见 g2_report.json gap_check.assembly_fit(全量   对+真深度), 毛石按面石内缘现场修配。

## 复现
```
blender -b --python 3d/p1a_slice.py -- --g2
```
