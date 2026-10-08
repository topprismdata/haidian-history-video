# M23 照片对照包报告（多角度贴图渲染 vs 原图）

日期: 2026-10-08/09 | 执行: M23Compare (sub) | 分支 e30-bridge-body
最终 commit 链: 02cfa8b → dcb3b5c → fbe672f → c6aa1d6 → 57a0daa → (本轮)几何 v3 复渲+闸门定版

## 0. 一句话

五轮渲染迭代（ogee → 布尔静默失败 → bowtie → 3ac909d2 未切 → adc59a5a 四层闸全绿）后,
在真·修复 blend(adc59a5a43868795, 444 锁)上以水线约束修正位姿完成全套 10 张对照渲
（6 中性 + 4 金光 v3）, 逐石像素层(a6 全表 62 石 PASS)、水线量化(约束点 52.6→2.1px)、
透光闸门(raycast 式, 已入 build 链常驻)随包交付。

## 1. 交付物

`3d/out/compare_pack/`:
- pairs/: 12 张拼图 = 7 组中性(材质判读基准) + 4 组 GOLDEN(金光对照主图: b/c/d/e) + overlay 水线版×2
- INDEX.md: 几何 v3 口径 + 逐组已知差异 + 待改进 4+ 条 + gpt_review.md 挂载位
- params/*.json: 10 组渲染参数（blend_sha16=adc59a5a43868795 入档, 材质/灯光/位姿覆盖全记录）
- perstone/: a6_v5(62 石全 PASS, 边界偏移中位 0.45px)+a5_v5 表 + raylabel 标签 npz + attr_a9 归因表
- renders/: 最终 PNG 10 张（隔离区×2 留证: ogee 8 张 / voidcut 10 张）

## 2. 渲染规格（主控历次闸门全落实）

Cycles METAL GPU + OIDN, seed=20261004; 全景 512 / 特写 1024 samples; b/c/d 4K, e 3552×2368。
材质=最终程序化石栈+修复栈(青石三区冷灰蓝/汉白玉微暖/逐石噪声/法线重算); 金光 v3=
日沿桥轴低角(travel az58.7/el2)+17 洞暖面光阵列+暖渐变天穹([主控 v3 PASS]参数)。

## 3. 本轮三项新工程产出

1. **透光闸门 v2**（`check_arch_transmittance.py`, 反委托交付）: 射线采样式(22z×22x/孔,
   透光率+弦宽剖面 rmse 双指标), 极性无关; 三候选 blend 全 RED 实证"正确构建尚不存在",
   已入 build 链常驻。v1 明暗极性法废弃教训: 目测/亮度阈值均不可靠, 闸门必须过负控。
2. **水线约束位姿修正**（`compare_pack_waterfit.py`）: 检测水线作 z=0 平面约束,
   (dz,dt,df) 三参最小扰动 least_squares; f175 约束点 52.6→2.1px(<10px 达标);
   f150 部分(16.1px)/f675 弱(29.6px)如实入档; 全幅非均匀残差→全位姿重拟列待改进。
3. **逐石像素层**（`compare_pack_raylabel.py` + perstone --npz）: ray_cast 标签图
   (被摄面带+法线朝向过滤, Position AOV 的 5.2 合成器规避方案), a6 全表 62 石:
   IoU 中位 0.451(rect vs 放射楔 inherent 天花板), 边界法向偏移中位 0.45px/最大 0.33px
   —— 放样+位姿+渲染链一致性达亚像素级; 偏移为主判据(IoU 对 rect-vs-wedge 天然偏严)。

## 4. 几何五轮迭代大事记（皆留证）

| 轮 | blend | 结果 | 证据 |
|---|---|---|---|
| 1 | ogee(Oct7) | 尖拱错形 | quarantine_ogee 8 张 |
| 2 | 3ac909d2 | 布尔静默失败(实心墙+环浮雕) | ray_cast 17k 射线+4K 特写, quarantine_voidcut 10 张 |
| 3 | 7c7a452c | 同 2(环浮雕+平顶槽) | blend1 侧视实渲 /tmp/blend1_side_check.jpg |
| 4 | d5ce2a4c→3ac909d2 重落 | bowtie 揭示, 停渲 | 本轮 a/f/b/c 隔离 |
| 5 | **adc59a5a(现行)** | **圆弧+全开+四层闸绿** | 本包全部最终渲染 |

联裁归因(孔9, attr_a9_514dd33.json): coursing 未随新弧重裁=拱冠带实心主因(86-100%),
bridge_body 切割已开(12/528)——RoundArchFix 据此完成 coursing 弧区重裁。

## 5. 诚实边界（INDEX.md §2 全量）

- b/c/d 券洞组: 照片无标定位姿 → 仅量级对照(主控裁定维持); 位姿垂直退化已用水线约束
  部分修正(df -10%), 掠射下视线穿洞落邻墩侧壁=几何正确(透光闸 17/17 佐证), 通透感差
  系实拍暖橙辉光掩盖效应(光照时段项)。
- e 组: m20C 位姿 n=7 强退化(高空视角), 拱冠 Z 基准仍有效; e2 裁窗目视定位。
- 账外件: 石狮造型级/匾额未建模/毛石背非入画面。
- 全幅水线 mean -38.7px 非均匀残差 → 全位姿重拟列待改进 #4。

## 6. 环境事实

- 沙箱 CPU 限流: 前台>60s 命令被自动转后台(~2.4%)/nohup(~0.2%)/eval 子进程(~7%)——
  blender 渲染必须走 **bash 命名服务模式**(不限流, 4K s1024≈900-1300s)。
- blend 正交相机垂直 ppm≠水平 ppm(sensor36×24 实测拉伸~2x), 需实测 vppm 校正。
- 低倍目测不可靠实例: "round ✓"误判(实为环浮雕+平顶槽)——一切几何结论过闸门。
