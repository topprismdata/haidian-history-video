# ARCH09 中央孔试印包 SLICE_NOTES

G2 门产物: 全石流形+壁厚+分批+装配图 (report verdict: PASS)

## 口径
- 模型比例 1:50 (scale=0.02); 打印件毫米 = 模型米 x 20。
- 床 220x220mm; 贪心货架装箱(manifest.batches), 超床件独占一批 (oversize=true)。
- 配合缝双值: 每石 clearance_print_mm/clearance_model_mm 见 manifest.stones (FIT 自动分档: 最小维 <0.3m TIGHT / <1.0m NORMAL / 否则 LOOSE)。

## 缝的打印当量(模型 mm -> 打印件 mm)
- 券环放射缝 JOINT_GAP 12.5 -> 0.25; 后端 4.0 -> 0.08。
- 砧石真缝 GAP_W 10.0 -> 0.20; 面石-背衬隐缝 BACKING_GAP 2.0 -> 0.04。
- 装配制造间隙 FIT(TIGHT/NORMAL/LOOSE)= 0.15/0.30/0.50 (打印件
  直接尺寸, 非 1:50 换算; 1:50 下历史缝仅 0.04-0.25mm, 打不出,
  故配合靠 clearance 不靠历史缝)。

## 构成
| 族 | 数量 | 体积 cm3(打印件) |
|---|---|---|
| impost-step | 24 | 5.68 |
| ring-wedge | 17 | 548.74 |
| slab | 5 | 495.09 |
| wedge-std | 188 | 496.55 |

- 石数: 234 (roles: {"BACK": 94, "CORE": 5, "IMPOST": 24, "RING": 17, "SPANDREL": 94})
- 总体积: 1546.1 cm3; 0.4mm 喷嘴 FDM 经验估时 ~128.8 h (12cm3/h)。
- 超床件 2 块(独占批): ARCH09.EAST.RING.C00.B01, ARCH09.EAST.RING.C00.B17

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
6. 背衬(毛石)与面石存在实体干涉(G2 抽样实测 4 对, 全桥估计 ~4% BACK 石; g2_report.json gap_check.assembly_fit 全量可查): 毛石按 面石内缘现场修配, 不影响面石/券环精件。

## 复现
```
blender -b --python 3d/p1a_slice.py -- --g2
```
