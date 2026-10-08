# 中央五孔段 施工卡 (section5 · construction cards)

数据源: 3d/out/sequence.json (P2 交付: 407 stage/4094 事件) x 3d/out/print/section5/manifest.json (1047 打印单元/31 批)
对照账: 3d/out/ledger_full.json
生成命令: blender -b --python 3d/section_pack.py -- --assembly
回放: python3 3d/section_pack.py --assembly --cards-only (只出本卡+分号位表, 不渲染)
口径: 装配次序 = sequence 原序过滤的段单元事件子序列 (1047/1047 单元全覆盖, 恰一次, 不重排); 批次 = 220x220 打印床分批
口径: 每孔装配图 = out/print/section5/assembly/ARCHxx.png (assembly_ortho 模式, P1A 同款); 段总图 = 同目录 section_overview.png (墩位缺口/M5(a) 底座端槽示意, 图注 [设计选择]); 床位权威 = 分号位表 assembly/ARCHxx.csv

## 批次总表 (今日打印 — 每行=一床)

| batch | 孔 | 单元数 | 床位占用 mm | 分号位表 |
|---|---|---|---|---|
| 0 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 15 | 210.9x209.1 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 1 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 12 | 195.2x207.4 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 2 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 11 | 177.0x208.1 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 3 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 11 | 164.2x219.6 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 4 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 9 | 155.2x177.3 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 5 | ARCH08+ARCH09 | 3 | 154.1x208.6 | assembly/ARCH08.csv+assembly/ARCH09.csv |
| 6 | ARCH08+ARCH09+ARCH10 | 4 | 153.6x219.0 | assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv |
| 7 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 7 | 151.4x218.0 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 8 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 9 | 149.7x173.4 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 9 | ARCH07+ARCH09+ARCH11 | 3 | 146.6x198.8 | assembly/ARCH07.csv+assembly/ARCH09.csv+assembly/ARCH11.csv |
| 10 | ARCH09+ARCH10 | 3 | 144.0x208.6 | assembly/ARCH09.csv+assembly/ARCH10.csv |
| 11 | ARCH08+ARCH10 | 3 | 143.4x202.5 | assembly/ARCH08.csv+assembly/ARCH10.csv |
| 12 | ARCH08+ARCH10+ARCH11 | 3 | 141.4x199.2 | assembly/ARCH08.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 13 | ARCH07+ARCH11 | 3 | 139.9x192.4 | assembly/ARCH07.csv+assembly/ARCH11.csv |
| 14 | ARCH07+ARCH10+ARCH11 | 3 | 135.8x195.8 | assembly/ARCH07.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 15 | ARCH08+ARCH09 | 3 | 134.9x208.6 | assembly/ARCH08.csv+assembly/ARCH09.csv |
| 16 | ARCH08+ARCH09+ARCH10 | 3 | 134.6x205.6 | assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv |
| 17 | ARCH07+ARCH10+ARCH11 | 3 | 133.9x196.4 | assembly/ARCH07.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 18 | ARCH07+ARCH08+ARCH11 | 7 | 184.9x211.5 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH11.csv |
| 19 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 42 | 205.9x218.4 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 20 | ARCH08+ARCH09+ARCH10 | 50 | 202.9x214.7 | assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv |
| 21 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 56 | 200.8x215.2 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 22 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 52 | 198.8x211.3 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 23 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 50 | 214.4x207.3 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 24 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 69 | 218.8x210.7 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 25 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 73 | 211.6x213.7 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 26 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 72 | 206.7x196.2 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 27 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 90 | 219.6x212.0 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 28 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 99 | 218.4x215.0 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 29 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 148 | 218.5x218.2 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 30 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 131 | 219.7x170.9 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |

## 装配次序 (今日粘接 — sequence 子序列, 69 stage/1047 行; 行序=粘接序)

序声明: 本节每行均为装配次序断言 [工程推断·非史料](无工序史料锚, P2 关账口径; sequence 事件原序, 不重排)。

### S124 ARCH07.IMPOST.C02 (events 672-679)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 672 | ARCH07.EAST.IMPOST.C02.B01 | 29 | 62.12,157.35 | [工程推断·非史料] |
| 673 | ARCH07.EAST.IMPOST.C02.B02 | 30 | 20.70,17.16 | [工程推断·非史料] |
| 674 | ARCH07.EAST.IMPOST.C02.B03 | 29 | 186.30,166.16 | [工程推断·非史料] |
| 675 | ARCH07.EAST.IMPOST.C02.B04 | 29 | 0.00,174.96 | [工程推断·非史料] |
| 676 | ARCH07.WEST.IMPOST.C02.B01 | 29 | 124.22,157.35 | [工程推断·非史料] |
| 677 | ARCH07.WEST.IMPOST.C02.B02 | 30 | 82.80,17.16 | [工程推断·非史料] |
| 678 | ARCH07.WEST.IMPOST.C02.B03 | 29 | 62.10,174.96 | [工程推断·非史料] |
| 679 | ARCH07.WEST.IMPOST.C02.B04 | 29 | 82.80,174.96 | [工程推断·非史料] |

### S125 ARCH07.IMPOST.C01 (events 680-687)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 680 | ARCH07.EAST.IMPOST.C01.B01 | 30 | 0.00,17.16 | [工程推断·非史料] |
| 681 | ARCH07.EAST.IMPOST.C01.B02 | 30 | 128.05,146.28 | [工程推断·非史料] |
| 682 | ARCH07.EAST.IMPOST.C01.B03 | 29 | 41.42,157.35 | [工程推断·非史料] |
| 683 | ARCH07.EAST.IMPOST.C01.B04 | 30 | 0.00,162.88 | [工程推断·非史料] |
| 684 | ARCH07.WEST.IMPOST.C01.B01 | 30 | 62.10,17.16 | [工程推断·非史料] |
| 685 | ARCH07.WEST.IMPOST.C01.B02 | 30 | 142.96,146.28 | [工程推断·非史料] |
| 686 | ARCH07.WEST.IMPOST.C01.B03 | 29 | 103.52,157.35 | [工程推断·非史料] |
| 687 | ARCH07.WEST.IMPOST.C01.B04 | 30 | 13.95,162.88 | [工程推断·非史料] |

### S126 ARCH07.IMPOST.C00 (events 688-695)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 688 | ARCH07.EAST.IMPOST.C00.B01 | 29 | 20.72,157.35 | [工程推断·非史料] |
| 689 | ARCH07.EAST.IMPOST.C00.B02 | 30 | 186.30,8.58 | [工程推断·非史料] |
| 690 | ARCH07.EAST.IMPOST.C00.B03 | 29 | 144.90,166.16 | [工程推断·非史料] |
| 691 | ARCH07.EAST.IMPOST.C00.B04 | 29 | 165.60,166.16 | [工程推断·非史料] |
| 692 | ARCH07.WEST.IMPOST.C00.B01 | 29 | 82.82,157.35 | [工程推断·非史料] |
| 693 | ARCH07.WEST.IMPOST.C00.B02 | 30 | 41.40,17.16 | [工程推断·非史料] |
| 694 | ARCH07.WEST.IMPOST.C00.B03 | 29 | 20.70,174.96 | [工程推断·非史料] |
| 695 | ARCH07.WEST.IMPOST.C00.B04 | 29 | 41.40,174.96 | [工程推断·非史料] |

### S128 ARCH07.RING.bank01 (events 697-698)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 697 | ARCH07.EAST.RING.C00.B02 | 1 | 0.00,15.89 | [工程推断·非史料] |
| 698 | ARCH07.EAST.RING.C00.B12 | 1 | 0.00,32.46 | [工程推断·非史料] |

### S129 ARCH07.RING.bank02 (events 699-700)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 699 | ARCH07.EAST.RING.C00.B03 | 1 | 0.00,188.00 | [工程推断·非史料] |
| 700 | ARCH07.EAST.RING.C00.B11 | 2 | 0.00,0.00 | [工程推断·非史料] |

### S130 ARCH07.RING.bank03 (events 701-702)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 701 | ARCH07.EAST.RING.C00.B04 | 3 | 0.00,0.00 | [工程推断·非史料] |
| 702 | ARCH07.EAST.RING.C00.B10 | 3 | 0.00,20.61 | [工程推断·非史料] |

### S131 ARCH07.RING.bank04 (events 703-704)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 703 | ARCH07.EAST.RING.C00.B01 | 0 | 0.00,79.51 | [工程推断·非史料] |
| 704 | ARCH07.EAST.RING.C00.B13 | 0 | 0.00,92.28 | [工程推断·非史料] |

### S132 ARCH07.RING.bank05 (events 705-706)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 705 | ARCH07.EAST.RING.C00.B05 | 3 | 0.00,198.27 | [工程推断·非史料] |
| 706 | ARCH07.EAST.RING.C00.B09 | 4 | 0.00,0.00 | [工程推断·非史料] |

### S133 ARCH07.RING.bank06 (events 707-708)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 707 | ARCH07.EAST.RING.C00.B06 | 8 | 0.00,15.96 | [工程推断·非史料] |
| 708 | ARCH07.EAST.RING.C00.B08 | 8 | 0.00,36.41 | [工程推断·非史料] |

### S134 ARCH07.RING.bank07 (events 709-709)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 709 | ARCH07.EAST.RING.C00.B07 | 8 | 0.00,133.37 | [工程推断·非史料] |

### S148 ARCH07.SHOULDER.C12 (events 807-815)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 807 | ARCH07.EAST.BACK.C12.B02 | 24 | 164.10,79.69 | [工程推断·非史料] |
| 808 | ARCH07.EAST.BACK.C12.B04 | 28 | 97.19,0.00 | [工程推断·非史料] |
| 809 | ARCH07.EAST.SPANDREL.C12.B02 | 24 | 136.75,79.69 | [工程推断·非史料] |
| 810 | ARCH07.EAST.SPANDREL.C12.B04 | 25 | 130.15,155.14 | [工程推断·非史料] |
| 811 | ARCH07.WEST.BACK.C12.B02 | 24 | 0.00,105.69 | [工程推断·非史料] |
| 812 | ARCH07.WEST.BACK.C12.B04 | 28 | 121.45,0.00 | [工程推断·非史料] |
| 813 | ARCH07.WEST.SPANDREL.C12.B02 | 24 | 191.45,79.69 | [工程推断·非史料] |
| 815 | ARCH07.WEST.SPANDREL.C12.B04 | 25 | 182.11,155.14 | [工程推断·非史料] |

### S149 ARCH07.SHOULDER.C14 (events 816-816)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 816 | ARCH07.EAST.CORE.C14.B01 | 13 | 0.00,64.14 | [工程推断·非史料] |

### S151 ARCH08.IMPOST.C02 (events 820-827)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 820 | ARCH08.EAST.IMPOST.C02.B01 | 29 | 186.30,174.96 | [工程推断·非史料] |
| 821 | ARCH08.EAST.IMPOST.C02.B02 | 29 | 0.00,183.64 | [工程推断·非史料] |
| 822 | ARCH08.EAST.IMPOST.C02.B03 | 29 | 20.70,183.64 | [工程推断·非史料] |
| 823 | ARCH08.EAST.IMPOST.C02.B04 | 29 | 186.30,209.55 | [工程推断·非史料] |
| 824 | ARCH08.WEST.IMPOST.C02.B01 | 29 | 124.20,183.64 | [工程推断·非史料] |
| 825 | ARCH08.WEST.IMPOST.C02.B02 | 29 | 144.90,183.64 | [工程推断·非史料] |
| 826 | ARCH08.WEST.IMPOST.C02.B03 | 29 | 165.60,183.64 | [工程推断·非史料] |
| 827 | ARCH08.WEST.IMPOST.C02.B04 | 30 | 41.40,0.00 | [工程推断·非史料] |

### S152 ARCH08.IMPOST.C01 (events 828-835)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 828 | ARCH08.EAST.IMPOST.C01.B01 | 29 | 165.60,174.96 | [工程推断·非史料] |
| 829 | ARCH08.EAST.IMPOST.C01.B02 | 30 | 27.91,162.88 | [工程推断·非史料] |
| 830 | ARCH08.EAST.IMPOST.C01.B03 | 29 | 165.60,209.55 | [工程推断·非史料] |
| 831 | ARCH08.EAST.IMPOST.C01.B04 | 30 | 79.95,162.88 | [工程推断·非史料] |
| 832 | ARCH08.WEST.IMPOST.C01.B01 | 29 | 103.50,183.64 | [工程推断·非史料] |
| 833 | ARCH08.WEST.IMPOST.C01.B02 | 30 | 40.92,162.88 | [工程推断·非史料] |
| 834 | ARCH08.WEST.IMPOST.C01.B03 | 30 | 20.70,0.00 | [工程推断·非史料] |
| 835 | ARCH08.WEST.IMPOST.C01.B04 | 30 | 92.02,162.88 | [工程推断·非史料] |

### S153 ARCH08.IMPOST.C00 (events 836-843)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 836 | ARCH08.EAST.IMPOST.C00.B01 | 29 | 103.50,174.96 | [工程推断·非史料] |
| 837 | ARCH08.EAST.IMPOST.C00.B02 | 29 | 124.20,174.96 | [工程推断·非史料] |
| 838 | ARCH08.EAST.IMPOST.C00.B03 | 29 | 144.90,174.96 | [工程推断·非史料] |
| 839 | ARCH08.EAST.IMPOST.C00.B04 | 29 | 144.90,209.55 | [工程推断·非史料] |
| 840 | ARCH08.WEST.IMPOST.C00.B01 | 29 | 41.40,183.64 | [工程推断·非史料] |
| 841 | ARCH08.WEST.IMPOST.C00.B02 | 29 | 62.10,183.64 | [工程推断·非史料] |
| 842 | ARCH08.WEST.IMPOST.C00.B03 | 29 | 82.80,183.64 | [工程推断·非史料] |
| 843 | ARCH08.WEST.IMPOST.C00.B04 | 30 | 0.00,0.00 | [工程推断·非史料] |

### S155 ARCH08.RING.bank01 (events 845-846)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 845 | ARCH08.EAST.RING.C00.B01 | 0 | 0.00,26.89 | [工程推断·非史料] |
| 846 | ARCH08.EAST.RING.C00.B15 | 0 | 0.00,40.05 | [工程推断·非史料] |

### S156 ARCH08.RING.bank02 (events 847-848)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 847 | ARCH08.EAST.RING.C00.B02 | 0 | 0.00,161.45 | [工程推断·非史料] |
| 848 | ARCH08.EAST.RING.C00.B14 | 0 | 0.00,177.34 | [工程推断·非史料] |

### S157 ARCH08.RING.bank03 (events 849-850)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 849 | ARCH08.EAST.RING.C00.B03 | 1 | 0.00,116.11 | [工程推断·非史料] |
| 850 | ARCH08.EAST.RING.C00.B13 | 1 | 0.00,134.08 | [工程推断·非史料] |

### S158 ARCH08.RING.bank04 (events 851-852)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 851 | ARCH08.EAST.RING.C00.B04 | 2 | 0.00,94.07 | [工程推断·非史料] |
| 852 | ARCH08.EAST.RING.C00.B12 | 2 | 0.00,113.36 | [工程推断·非史料] |

### S159 ARCH08.RING.bank05 (events 853-854)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 853 | ARCH08.EAST.RING.C00.B05 | 3 | 0.00,82.42 | [工程推断·非史料] |
| 854 | ARCH08.EAST.RING.C00.B11 | 3 | 0.00,102.22 | [工程推断·非史料] |

### S160 ARCH08.RING.bank06 (events 855-856)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 855 | ARCH08.EAST.RING.C00.B06 | 4 | 0.00,99.46 | [工程推断·非史料] |
| 856 | ARCH08.EAST.RING.C00.B10 | 4 | 0.00,118.92 | [工程推断·非史料] |

### S161 ARCH08.RING.bank07 (events 857-858)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 857 | ARCH08.EAST.RING.C00.B07 | 7 | 0.00,144.75 | [工程推断·非史料] |
| 858 | ARCH08.EAST.RING.C00.B09 | 7 | 0.00,163.07 | [工程推断·非史料] |

### S162 ARCH08.RING.bank08 (events 859-859)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 859 | ARCH08.EAST.RING.C00.B08 | 8 | 0.00,97.76 | [工程推断·非史料] |

### S177 ARCH08.SHOULDER.C14 (events 982-982)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 982 | ARCH08.EAST.CORE.C14.B01 | 11 | 0.00,67.51 | [工程推断·非史料] |

### S178 ARCH08.SHOULDER.C13 (events 983-994)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 983 | ARCH08.EAST.BACK.C13.B04 | 29 | 44.23,20.38 | [工程推断·非史料] |
| 985 | ARCH08.EAST.BACK.C13.B06 | 26 | 154.79,74.40 | [工程推断·非史料] |
| 986 | ARCH08.EAST.SPANDREL.C13.B04 | 20 | 152.19,0.00 | [工程推断·非史料] |
| 988 | ARCH08.EAST.SPANDREL.C13.B06 | 20 | 0.00,22.06 | [工程推断·非史料] |
| 989 | ARCH08.WEST.BACK.C13.B04 | 29 | 66.29,20.38 | [工程推断·非史料] |
| 991 | ARCH08.WEST.BACK.C13.B06 | 26 | 103.21,74.40 | [工程推断·非史料] |
| 992 | ARCH08.WEST.SPANDREL.C13.B04 | 20 | 101.46,0.00 | [工程推断·非史料] |
| 994 | ARCH08.WEST.SPANDREL.C13.B06 | 20 | 101.44,22.06 | [工程推断·非史料] |

### S180 ARCH09.IMPOST.C02 (events 998-1005)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 998 | ARCH09.EAST.IMPOST.C02.B01 | 29 | 41.40,192.31 | [工程推断·非史料] |
| 999 | ARCH09.EAST.IMPOST.C02.B02 | 30 | 124.20,0.00 | [工程推断·非史料] |
| 1000 | ARCH09.EAST.IMPOST.C02.B03 | 29 | 62.10,192.31 | [工程推断·非史料] |
| 1001 | ARCH09.EAST.IMPOST.C02.B04 | 30 | 144.90,0.00 | [工程推断·非史料] |
| 1002 | ARCH09.WEST.IMPOST.C02.B01 | 29 | 144.90,192.31 | [工程推断·非史料] |
| 1003 | ARCH09.WEST.IMPOST.C02.B02 | 30 | 20.70,8.58 | [工程推断·非史料] |
| 1004 | ARCH09.WEST.IMPOST.C02.B03 | 29 | 165.60,192.31 | [工程推断·非史料] |
| 1005 | ARCH09.WEST.IMPOST.C02.B04 | 30 | 41.40,8.58 | [工程推断·非史料] |

### S181 ARCH09.IMPOST.C01 (events 1006-1013)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1006 | ARCH09.EAST.IMPOST.C01.B01 | 29 | 20.70,192.31 | [工程推断·非史料] |
| 1007 | ARCH09.EAST.IMPOST.C01.B02 | 30 | 151.43,162.88 | [工程推断·非史料] |
| 1008 | ARCH09.EAST.IMPOST.C01.B03 | 30 | 103.50,0.00 | [工程推断·非史料] |
| 1009 | ARCH09.EAST.IMPOST.C01.B04 | 30 | 128.23,162.88 | [工程推断·非史料] |
| 1010 | ARCH09.WEST.IMPOST.C01.B01 | 29 | 124.20,192.31 | [工程推断·非史料] |
| 1011 | ARCH09.WEST.IMPOST.C01.B02 | 30 | 163.03,162.88 | [工程推断·非史料] |
| 1012 | ARCH09.WEST.IMPOST.C01.B03 | 30 | 0.00,8.58 | [工程推断·非史料] |
| 1013 | ARCH09.WEST.IMPOST.C01.B04 | 30 | 139.83,162.88 | [工程推断·非史料] |

### S182 ARCH09.IMPOST.C00 (events 1014-1021)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1014 | ARCH09.EAST.IMPOST.C00.B01 | 29 | 186.30,183.64 | [工程推断·非史料] |
| 1015 | ARCH09.EAST.IMPOST.C00.B02 | 30 | 62.10,0.00 | [工程推断·非史料] |
| 1016 | ARCH09.EAST.IMPOST.C00.B03 | 29 | 0.00,192.31 | [工程推断·非史料] |
| 1017 | ARCH09.EAST.IMPOST.C00.B04 | 30 | 82.80,0.00 | [工程推断·非史料] |
| 1018 | ARCH09.WEST.IMPOST.C00.B01 | 29 | 82.80,192.31 | [工程推断·非史料] |
| 1019 | ARCH09.WEST.IMPOST.C00.B02 | 30 | 165.60,0.00 | [工程推断·非史料] |
| 1020 | ARCH09.WEST.IMPOST.C00.B03 | 29 | 103.50,192.31 | [工程推断·非史料] |
| 1021 | ARCH09.WEST.IMPOST.C00.B04 | 30 | 186.30,0.00 | [工程推断·非史料] |

### S184 ARCH09.RING.bank01 (events 1023-1024)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1023 | ARCH09.EAST.RING.C00.B01 | 0 | 0.00,0.00 | [工程推断·非史料] |
| 1024 | ARCH09.EAST.RING.C00.B17 | 0 | 0.00,13.44 | [工程推断·非史料] |

### S185 ARCH09.RING.bank02 (events 1025-1026)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1025 | ARCH09.EAST.RING.C00.B02 | 0 | 0.00,130.59 | [工程推断·非史料] |
| 1026 | ARCH09.EAST.RING.C00.B16 | 0 | 0.00,146.02 | [工程推断·非史料] |

### S186 ARCH09.RING.bank03 (events 1027-1028)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1027 | ARCH09.EAST.RING.C00.B03 | 1 | 0.00,82.18 | [工程推断·非史料] |
| 1028 | ARCH09.EAST.RING.C00.B15 | 1 | 0.00,99.14 | [工程推断·非史料] |

### S187 ARCH09.RING.bank04 (events 1029-1030)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1029 | ARCH09.EAST.RING.C00.B04 | 2 | 0.00,58.11 | [工程推断·非史料] |
| 1030 | ARCH09.EAST.RING.C00.B14 | 2 | 0.00,76.09 | [工程推断·非史料] |

### S188 ARCH09.RING.bank05 (events 1031-1032)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1031 | ARCH09.EAST.RING.C00.B05 | 2 | 0.00,171.23 | [工程推断·非史料] |
| 1032 | ARCH09.EAST.RING.C00.B13 | 2 | 0.00,189.67 | [工程推断·非史料] |

### S189 ARCH09.RING.bank06 (events 1033-1034)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1033 | ARCH09.EAST.RING.C00.B06 | 3 | 0.00,161.60 | [工程推断·非史料] |
| 1034 | ARCH09.EAST.RING.C00.B12 | 3 | 0.00,179.94 | [工程推断·非史料] |

### S190 ARCH09.RING.bank07 (events 1035-1036)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1035 | ARCH09.EAST.RING.C00.B07 | 4 | 0.00,64.11 | [工程推断·非史料] |
| 1036 | ARCH09.EAST.RING.C00.B11 | 4 | 0.00,81.79 | [工程推断·非史料] |

### S191 ARCH09.RING.bank08 (events 1037-1038)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1037 | ARCH09.EAST.RING.C00.B08 | 6 | 0.00,202.54 | [工程推断·非史料] |
| 1038 | ARCH09.EAST.RING.C00.B10 | 7 | 0.00,0.00 | [工程推断·非史料] |

### S192 ARCH09.RING.bank09 (events 1039-1039)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1039 | ARCH09.EAST.RING.C00.B09 | 8 | 0.00,0.00 | [工程推断·非史料] |

### S203 ARCH09.SHOULDER.C14 (events 1144-1144)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1144 | ARCH09.EAST.CORE.C14.B01 | 9 | 0.00,128.29 | [工程推断·非史料] |

### S204 ARCH09.SHOULDER.C13 (events 1145-1152)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1146 | ARCH09.EAST.BACK.C13.B04 | 24 | 116.34,0.00 | [工程推断·非史料] |
| 1148 | ARCH09.EAST.SPANDREL.C13.B04 | 21 | 100.22,43.68 | [工程推断·非史料] |
| 1150 | ARCH09.WEST.BACK.C13.B04 | 24 | 144.40,0.00 | [工程推断·非史料] |
| 1152 | ARCH09.WEST.SPANDREL.C13.B04 | 21 | 150.33,43.68 | [工程推断·非史料] |

### S206 ARCH10.IMPOST.C02 (events 1156-1163)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1156 | ARCH10.EAST.IMPOST.C02.B01 | 29 | 20.70,200.89 | [工程推断·非史料] |
| 1157 | ARCH10.EAST.IMPOST.C02.B02 | 30 | 103.50,8.58 | [工程推断·非史料] |
| 1158 | ARCH10.EAST.IMPOST.C02.B03 | 29 | 41.40,200.89 | [工程推断·非史料] |
| 1159 | ARCH10.EAST.IMPOST.C02.B04 | 29 | 165.62,157.35 | [工程推断·非史料] |
| 1160 | ARCH10.WEST.IMPOST.C02.B01 | 29 | 103.50,200.89 | [工程推断·非史料] |
| 1161 | ARCH10.WEST.IMPOST.C02.B02 | 30 | 165.60,8.58 | [工程推断·非史料] |
| 1162 | ARCH10.WEST.IMPOST.C02.B03 | 29 | 124.20,200.89 | [工程推断·非史料] |
| 1163 | ARCH10.WEST.IMPOST.C02.B04 | 29 | 0.00,166.16 | [工程推断·非史料] |

### S207 ARCH10.IMPOST.C01 (events 1164-1171)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1164 | ARCH10.EAST.IMPOST.C01.B01 | 30 | 82.80,8.58 | [工程推断·非史料] |
| 1165 | ARCH10.EAST.IMPOST.C01.B02 | 30 | 104.09,162.88 | [工程推断·非史料] |
| 1166 | ARCH10.EAST.IMPOST.C01.B03 | 30 | 103.50,17.16 | [工程推断·非史料] |
| 1167 | ARCH10.EAST.IMPOST.C01.B04 | 30 | 53.93,162.88 | [工程推断·非史料] |
| 1168 | ARCH10.WEST.IMPOST.C01.B01 | 30 | 144.90,8.58 | [工程推断·非史料] |
| 1169 | ARCH10.WEST.IMPOST.C01.B02 | 30 | 116.16,162.88 | [工程推断·非史料] |
| 1170 | ARCH10.WEST.IMPOST.C01.B03 | 30 | 124.20,17.16 | [工程推断·非史料] |
| 1171 | ARCH10.WEST.IMPOST.C01.B04 | 30 | 66.94,162.88 | [工程推断·非史料] |

### S208 ARCH10.IMPOST.C00 (events 1172-1179)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1172 | ARCH10.EAST.IMPOST.C00.B01 | 29 | 186.30,192.31 | [工程推断·非史料] |
| 1173 | ARCH10.EAST.IMPOST.C00.B02 | 30 | 62.10,8.58 | [工程推断·非史料] |
| 1174 | ARCH10.EAST.IMPOST.C00.B03 | 29 | 0.00,200.89 | [工程推断·非史料] |
| 1175 | ARCH10.EAST.IMPOST.C00.B04 | 29 | 144.92,157.35 | [工程推断·非史料] |
| 1176 | ARCH10.WEST.IMPOST.C00.B01 | 29 | 62.10,200.89 | [工程推断·非史料] |
| 1177 | ARCH10.WEST.IMPOST.C00.B02 | 30 | 124.20,8.58 | [工程推断·非史料] |
| 1178 | ARCH10.WEST.IMPOST.C00.B03 | 29 | 82.80,200.89 | [工程推断·非史料] |
| 1179 | ARCH10.WEST.IMPOST.C00.B04 | 29 | 186.32,157.35 | [工程推断·非史料] |

### S210 ARCH10.RING.bank01 (events 1181-1182)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1181 | ARCH10.EAST.RING.C00.B01 | 0 | 0.00,53.20 | [工程推断·非史料] |
| 1182 | ARCH10.EAST.RING.C00.B15 | 0 | 0.00,66.36 | [工程推断·非史料] |

### S211 ARCH10.RING.bank02 (events 1183-1184)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1183 | ARCH10.EAST.RING.C00.B02 | 0 | 0.00,193.24 | [工程推断·非史料] |
| 1184 | ARCH10.EAST.RING.C00.B14 | 1 | 0.00,0.00 | [工程推断·非史料] |

### S212 ARCH10.RING.bank03 (events 1185-1186)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1185 | ARCH10.EAST.RING.C00.B03 | 1 | 0.00,152.05 | [工程推断·非史料] |
| 1186 | ARCH10.EAST.RING.C00.B13 | 1 | 0.00,170.02 | [工程推断·非史料] |

### S213 ARCH10.RING.bank04 (events 1187-1188)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1187 | ARCH10.EAST.RING.C00.B04 | 2 | 0.00,132.65 | [工程推断·非史料] |
| 1188 | ARCH10.EAST.RING.C00.B12 | 2 | 0.00,151.94 | [工程推断·非史料] |

### S214 ARCH10.RING.bank05 (events 1189-1190)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1189 | ARCH10.EAST.RING.C00.B05 | 3 | 0.00,122.01 | [工程推断·非史料] |
| 1190 | ARCH10.EAST.RING.C00.B11 | 3 | 0.00,141.81 | [工程推断·非史料] |

### S215 ARCH10.RING.bank06 (events 1191-1192)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1191 | ARCH10.EAST.RING.C00.B06 | 4 | 0.00,138.39 | [工程推断·非史料] |
| 1192 | ARCH10.EAST.RING.C00.B10 | 4 | 0.00,157.85 | [工程推断·非史料] |

### S216 ARCH10.RING.bank07 (events 1193-1194)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1193 | ARCH10.EAST.RING.C00.B07 | 7 | 0.00,181.38 | [工程推断·非史料] |
| 1194 | ARCH10.EAST.RING.C00.B09 | 7 | 0.00,199.70 | [工程推断·非史料] |

### S217 ARCH10.RING.bank08 (events 1195-1195)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1195 | ARCH10.EAST.RING.C00.B08 | 8 | 0.00,115.56 | [工程推断·非史料] |

### S232 ARCH10.SHOULDER.C14 (events 1318-1318)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1318 | ARCH10.EAST.CORE.C14.B01 | 11 | 0.00,135.03 | [工程推断·非史料] |

### S233 ARCH10.SHOULDER.C13 (events 1319-1330)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1319 | ARCH10.EAST.BACK.C13.B02 | 26 | 180.59,74.40 | [工程推断·非史料] |
| 1321 | ARCH10.EAST.BACK.C13.B04 | 29 | 88.35,20.38 | [工程推断·非史料] |
| 1322 | ARCH10.EAST.SPANDREL.C13.B02 | 20 | 50.72,22.06 | [工程推断·非史料] |
| 1324 | ARCH10.EAST.SPANDREL.C13.B04 | 20 | 50.73,0.00 | [工程推断·非史料] |
| 1325 | ARCH10.WEST.BACK.C13.B02 | 26 | 129.00,74.40 | [工程推断·非史料] |
| 1327 | ARCH10.WEST.BACK.C13.B04 | 29 | 110.41,20.38 | [工程推断·非史料] |
| 1328 | ARCH10.WEST.SPANDREL.C13.B02 | 20 | 152.16,22.06 | [工程推断·非史料] |
| 1330 | ARCH10.WEST.SPANDREL.C13.B04 | 20 | 0.00,0.00 | [工程推断·非史料] |

### S235 ARCH11.IMPOST.C02 (events 1334-1341)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1334 | ARCH11.EAST.IMPOST.C02.B01 | 29 | 0.00,209.55 | [工程推断·非史料] |
| 1335 | ARCH11.EAST.IMPOST.C02.B02 | 29 | 20.70,209.55 | [工程推断·非史料] |
| 1336 | ARCH11.EAST.IMPOST.C02.B03 | 30 | 165.60,17.16 | [工程推断·非史料] |
| 1337 | ARCH11.EAST.IMPOST.C02.B04 | 29 | 62.10,166.16 | [工程推断·非史料] |
| 1338 | ARCH11.WEST.IMPOST.C02.B01 | 29 | 103.50,209.55 | [工程推断·非史料] |
| 1339 | ARCH11.WEST.IMPOST.C02.B02 | 29 | 124.20,209.55 | [工程推断·非史料] |
| 1340 | ARCH11.WEST.IMPOST.C02.B03 | 30 | 0.00,25.95 | [工程推断·非史料] |
| 1341 | ARCH11.WEST.IMPOST.C02.B04 | 29 | 124.20,166.16 | [工程推断·非史料] |

### S236 ARCH11.IMPOST.C01 (events 1342-1349)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1342 | ARCH11.EAST.IMPOST.C01.B01 | 29 | 186.30,200.89 | [工程推断·非史料] |
| 1343 | ARCH11.EAST.IMPOST.C01.B02 | 30 | 187.67,146.28 | [工程推断·非史料] |
| 1344 | ARCH11.EAST.IMPOST.C01.B03 | 29 | 41.40,166.16 | [工程推断·非史料] |
| 1345 | ARCH11.EAST.IMPOST.C01.B04 | 30 | 157.86,146.28 | [工程推断·非史料] |
| 1346 | ARCH11.WEST.IMPOST.C01.B01 | 29 | 82.80,209.55 | [工程推断·非史料] |
| 1347 | ARCH11.WEST.IMPOST.C01.B02 | 30 | 201.63,146.28 | [工程推断·非史料] |
| 1348 | ARCH11.WEST.IMPOST.C01.B03 | 29 | 103.50,166.16 | [工程推断·非史料] |
| 1349 | ARCH11.WEST.IMPOST.C01.B04 | 30 | 172.77,146.28 | [工程推断·非史料] |

### S237 ARCH11.IMPOST.C00 (events 1350-1357)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1350 | ARCH11.EAST.IMPOST.C00.B01 | 29 | 144.90,200.89 | [工程推断·非史料] |
| 1351 | ARCH11.EAST.IMPOST.C00.B02 | 29 | 165.60,200.89 | [工程推断·非史料] |
| 1352 | ARCH11.EAST.IMPOST.C00.B03 | 30 | 144.90,17.16 | [工程推断·非史料] |
| 1353 | ARCH11.EAST.IMPOST.C00.B04 | 29 | 20.70,166.16 | [工程推断·非史料] |
| 1354 | ARCH11.WEST.IMPOST.C00.B01 | 29 | 41.40,209.55 | [工程推断·非史料] |
| 1355 | ARCH11.WEST.IMPOST.C00.B02 | 29 | 62.10,209.55 | [工程推断·非史料] |
| 1356 | ARCH11.WEST.IMPOST.C00.B03 | 30 | 186.30,17.16 | [工程推断·非史料] |
| 1357 | ARCH11.WEST.IMPOST.C00.B04 | 29 | 82.80,166.16 | [工程推断·非史料] |

### S239 ARCH11.RING.bank01 (events 1359-1360)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1359 | ARCH11.EAST.RING.C00.B02 | 1 | 0.00,49.03 | [工程推断·非史料] |
| 1360 | ARCH11.EAST.RING.C00.B12 | 1 | 0.00,65.61 | [工程推断·非史料] |

### S240 ARCH11.RING.bank02 (events 1361-1362)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1361 | ARCH11.EAST.RING.C00.B03 | 2 | 0.00,19.37 | [工程推断·非史料] |
| 1362 | ARCH11.EAST.RING.C00.B11 | 2 | 0.00,38.74 | [工程推断·非史料] |

### S241 ARCH11.RING.bank03 (events 1363-1364)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1363 | ARCH11.EAST.RING.C00.B04 | 3 | 0.00,41.21 | [工程推断·非史料] |
| 1364 | ARCH11.EAST.RING.C00.B10 | 3 | 0.00,61.82 | [工程推断·非史料] |

### S242 ARCH11.RING.bank04 (events 1365-1366)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1365 | ARCH11.EAST.RING.C00.B01 | 0 | 0.00,105.05 | [工程推断·非史料] |
| 1366 | ARCH11.EAST.RING.C00.B13 | 0 | 0.00,117.82 | [工程推断·非史料] |

### S243 ARCH11.RING.bank05 (events 1367-1368)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1367 | ARCH11.EAST.RING.C00.B05 | 4 | 0.00,21.37 | [工程推断·非史料] |
| 1368 | ARCH11.EAST.RING.C00.B09 | 4 | 0.00,42.74 | [工程推断·非史料] |

### S244 ARCH11.RING.bank06 (events 1369-1370)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1369 | ARCH11.EAST.RING.C00.B06 | 8 | 0.00,56.86 | [工程推断·非史料] |
| 1370 | ARCH11.EAST.RING.C00.B08 | 8 | 0.00,77.31 | [工程推断·非史料] |

### S245 ARCH11.RING.bank07 (events 1371-1371)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1371 | ARCH11.EAST.RING.C00.B07 | 8 | 0.00,153.36 | [工程推断·非史料] |

### S259 ARCH11.SHOULDER.C12 (events 1469-1477)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1469 | ARCH11.EAST.BACK.C12.B02 | 28 | 145.71,0.00 | [工程推断·非史料] |
| 1470 | ARCH11.EAST.BACK.C12.B04 | 24 | 54.71,79.69 | [工程推断·非史料] |
| 1471 | ARCH11.EAST.SPANDREL.C12.B02 | 25 | 156.13,155.14 | [工程推断·非史料] |
| 1472 | ARCH11.EAST.SPANDREL.C12.B04 | 24 | 27.36,79.69 | [工程推断·非史料] |
| 1473 | ARCH11.WEST.BACK.C12.B02 | 28 | 169.97,0.00 | [工程推断·非史料] |
| 1474 | ARCH11.WEST.BACK.C12.B04 | 24 | 109.41,79.69 | [工程推断·非史料] |
| 1475 | ARCH11.WEST.SPANDREL.C12.B02 | 25 | 0.00,180.36 | [工程推断·非史料] |
| 1477 | ARCH11.WEST.SPANDREL.C12.B04 | 24 | 82.06,79.69 | [工程推断·非史料] |

### S260 ARCH11.SHOULDER.C14 (events 1478-1478)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1478 | ARCH11.EAST.CORE.C14.B01 | 13 | 0.00,128.29 | [工程推断·非史料] |

### S397 ARCH07.FILL (events 2656-2848)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 2692 | ARCH07.EAST.BACK.C08.B00 | 28 | 181.66,163.09 | [工程推断·非史料] |
| 2693 | ARCH07.EAST.BACK.C08.B05 | 24 | 132.95,192.82 | [工程推断·非史料] |
| 2694 | ARCH07.EAST.SPANDREL.C08.B00 | 24 | 0.00,0.00 | [工程推断·非史料] |
| 2695 | ARCH07.EAST.SPANDREL.C08.B05 | 18 | 131.98,131.96 | [工程推断·非史料] |
| 2696 | ARCH07.WEST.BACK.C08.B00 | 28 | 22.66,177.21 | [工程推断·非史料] |
| 2697 | ARCH07.WEST.BACK.C08.B05 | 24 | 159.47,192.82 | [工程推断·非史料] |
| 2698 | ARCH07.WEST.SPANDREL.C08.B00 | 24 | 29.09,0.00 | [工程推断·非史料] |
| 2699 | ARCH07.WEST.SPANDREL.C08.B05 | 18 | 0.00,196.40 | [工程推断·非史料] |
| 2703 | ARCH07.EAST.BACK.C09.B00 | 28 | 72.67,23.63 | [工程推断·非史料] |
| 2705 | ARCH07.EAST.BACK.C09.B05 | 27 | 170.54,195.93 | [工程推断·非史料] |
| 2706 | ARCH07.EAST.BACK.C09.B06 | 29 | 153.34,42.43 | [工程推断·非史料] |
| 2707 | ARCH07.EAST.SPANDREL.C09.B00 | 19 | 0.00,24.30 | [工程推断·非史料] |
| 2708 | ARCH07.EAST.SPANDREL.C09.B05 | 24 | 111.28,53.99 | [工程推断·非史料] |
| 2709 | ARCH07.EAST.SPANDREL.C09.B06 | 19 | 0.00,82.74 | [工程推断·非史料] |
| 2710 | ARCH07.WEST.BACK.C09.B00 | 28 | 96.83,23.63 | [工程推断·非史料] |
| 2712 | ARCH07.WEST.BACK.C09.B05 | 27 | 121.89,195.93 | [工程推断·非史料] |
| 2713 | ARCH07.WEST.BACK.C09.B06 | 29 | 109.74,42.43 | [工程推断·非史料] |
| 2714 | ARCH07.WEST.SPANDREL.C09.B00 | 19 | 51.46,24.30 | [工程推断·非史料] |
| 2715 | ARCH07.WEST.SPANDREL.C09.B05 | 24 | 166.00,53.99 | [工程推断·非史料] |
| 2716 | ARCH07.WEST.SPANDREL.C09.B06 | 19 | 102.80,63.34 | [工程推断·非史料] |
| 2717 | ARCH07.EAST.CORE.C13.B00 | 9 | 0.00,64.14 | [工程推断·非史料] |
| 2719 | ARCH07.EAST.CORE.C13.B02 | 7 | 0.00,80.61 | [工程推断·非史料] |
| 2720 | ARCH07.EAST.BACK.C10.B00 | 30 | 143.47,46.31 | [工程推断·非史料] |
| 2721 | ARCH07.EAST.BACK.C10.B01 | 30 | 61.53,46.31 | [工程推断·非史料] |
| 2722 | ARCH07.EAST.BACK.C10.B02 | 30 | 151.02,128.12 | [工程推断·非史料] |
| 2724 | ARCH07.EAST.BACK.C10.B06 | 28 | 93.57,86.83 | [工程推断·非史料] |
| 2725 | ARCH07.EAST.BACK.C10.B07 | 30 | 185.49,25.95 | [工程推断·非史料] |
| 2726 | ARCH07.EAST.BACK.C10.B08 | 27 | 100.88,88.45 | [工程推断·非史料] |
| 2727 | ARCH07.EAST.SPANDREL.C10.B00 | 27 | 101.62,24.14 | [工程推断·非史料] |
| 2728 | ARCH07.EAST.SPANDREL.C10.B01 | 22 | 98.74,116.94 | [工程推断·非史料] |
| 2729 | ARCH07.EAST.SPANDREL.C10.B02 | 27 | 152.37,24.14 | [工程推断·非史料] |
| 2730 | ARCH07.EAST.SPANDREL.C10.B06 | 27 | 50.73,38.40 | [工程推断·非史料] |
| 2731 | ARCH07.EAST.SPANDREL.C10.B07 | 22 | 0.00,140.72 | [工程推断·非史料] |
| 2732 | ARCH07.EAST.SPANDREL.C10.B08 | 27 | 0.00,52.65 | [工程推断·非史料] |
| 2733 | ARCH07.WEST.BACK.C10.B00 | 30 | 163.86,46.31 | [工程推断·非史料] |
| 2734 | ARCH07.WEST.BACK.C10.B01 | 30 | 82.02,46.31 | [工程推断·非史料] |
| 2735 | ARCH07.WEST.BACK.C10.B02 | 30 | 187.78,128.12 | [工程推断·非史料] |
| 2737 | ARCH07.WEST.BACK.C10.B06 | 28 | 46.96,86.83 | [工程推断·非史料] |
| 2738 | ARCH07.WEST.BACK.C10.B07 | 30 | 0.00,46.31 | [工程推断·非史料] |
| 2739 | ARCH07.WEST.BACK.C10.B08 | 27 | 151.23,88.45 | [工程推断·非史料] |
| 2740 | ARCH07.WEST.SPANDREL.C10.B00 | 27 | 50.87,24.14 | [工程推断·非史料] |
| 2741 | ARCH07.WEST.SPANDREL.C10.B01 | 22 | 0.00,116.94 | [工程推断·非史料] |
| 2742 | ARCH07.WEST.SPANDREL.C10.B02 | 27 | 0.00,38.40 | [工程推断·非史料] |
| 2743 | ARCH07.WEST.SPANDREL.C10.B06 | 27 | 101.40,38.40 | [工程推断·非史料] |
| 2744 | ARCH07.WEST.SPANDREL.C10.B07 | 22 | 49.33,140.72 | [工程推断·非史料] |
| 2745 | ARCH07.WEST.SPANDREL.C10.B08 | 27 | 152.06,38.40 | [工程推断·非史料] |
| 2746 | ARCH07.EAST.BACK.C11.B00 | 30 | 79.58,102.08 | [工程推断·非史料] |
| 2747 | ARCH07.EAST.BACK.C11.B01 | 26 | 102.58,152.18 | [工程推断·非史料] |
| 2748 | ARCH07.EAST.BACK.C11.B05 | 27 | 97.61,174.60 | [工程推断·非史料] |
| 2749 | ARCH07.EAST.SPANDREL.C11.B00 | 21 | 0.00,144.84 | [工程推断·非史料] |
| 2750 | ARCH07.EAST.SPANDREL.C11.B01 | 26 | 0.00,74.40 | [工程推断·非史料] |
| 2751 | ARCH07.EAST.SPANDREL.C11.B05 | 26 | 0.00,94.78 | [工程推断·非史料] |
| 2752 | ARCH07.WEST.BACK.C11.B00 | 30 | 99.36,102.08 | [工程推断·非史料] |
| 2753 | ARCH07.WEST.BACK.C11.B01 | 26 | 51.31,152.18 | [工程推断·非史料] |
| 2754 | ARCH07.WEST.BACK.C11.B05 | 27 | 122.01,174.60 | [工程推断·非史料] |
| 2755 | ARCH07.WEST.SPANDREL.C11.B00 | 21 | 49.81,144.84 | [工程推断·非史料] |
| 2756 | ARCH07.WEST.SPANDREL.C11.B01 | 26 | 25.80,74.40 | [工程推断·非史料] |
| 2757 | ARCH07.WEST.SPANDREL.C11.B05 | 26 | 51.51,94.78 | [工程推断·非史料] |
| 2758 | ARCH07.EAST.BACK.C12.B00 | 27 | 0.00,88.45 | [工程推断·非史料] |
| 2759 | ARCH07.EAST.BACK.C12.B01 | 27 | 195.21,174.60 | [工程推断·非史料] |
| 2761 | ARCH07.EAST.BACK.C12.B05 | 29 | 21.27,104.65 | [工程推断·非史料] |
| 2762 | ARCH07.EAST.BACK.C12.B06 | 24 | 53.90,148.20 | [工程推断·非史料] |
| 2763 | ARCH07.EAST.SPANDREL.C12.B00 | 25 | 26.06,155.14 | [工程推断·非史料] |
| 2764 | ARCH07.EAST.SPANDREL.C12.B01 | 21 | 0.00,71.74 | [工程推断·非史料] |
| 2766 | ARCH07.EAST.SPANDREL.C12.B05 | 21 | 0.00,81.00 | [工程推断·非史料] |
| 2767 | ARCH07.EAST.SPANDREL.C12.B06 | 24 | 26.96,148.20 | [工程推断·非史料] |
| 2768 | ARCH07.WEST.BACK.C12.B00 | 27 | 25.22,88.45 | [工程推断·非史料] |
| 2769 | ARCH07.WEST.BACK.C12.B01 | 27 | 0.00,195.93 | [工程推断·非史料] |
| 2771 | ARCH07.WEST.BACK.C12.B05 | 29 | 42.51,104.65 | [工程推断·非史料] |
| 2772 | ARCH07.WEST.BACK.C12.B06 | 24 | 107.78,148.20 | [工程推断·非史料] |
| 2773 | ARCH07.WEST.SPANDREL.C12.B00 | 25 | 52.08,155.14 | [工程推断·非史料] |
| 2774 | ARCH07.WEST.SPANDREL.C12.B01 | 21 | 100.03,71.74 | [工程推断·非史料] |
| 2775 | ARCH07.WEST.SPANDREL.C12.B05 | 21 | 49.97,81.00 | [工程推断·非史料] |
| 2776 | ARCH07.WEST.SPANDREL.C12.B06 | 24 | 80.84,148.20 | [工程推断·非史料] |
| 2777 | ARCH07.EAST.CORE.C14.B00 | 14 | 0.00,64.14 | [工程推断·非史料] |
| 2778 | ARCH07.EAST.CORE.C14.B02 | 13 | 0.00,0.00 | [工程推断·非史料] |
| 2779 | ARCH07.EAST.BACK.C13.B00 | 27 | 50.65,52.65 | [工程推断·非史料] |
| 2780 | ARCH07.EAST.BACK.C13.B01 | 29 | 148.61,104.65 | [工程推断·非史料] |
| 2781 | ARCH07.EAST.BACK.C13.B02 | 28 | 183.69,128.78 | [工程推断·非史料] |
| 2782 | ARCH07.EAST.BACK.C13.B03 | 24 | 0.00,26.99 | [工程推断·非史料] |
| 2783 | ARCH07.EAST.BACK.C13.B04 | 30 | 103.17,25.95 | [工程推断·非史料] |
| 2784 | ARCH07.EAST.BACK.C13.B05 | 30 | 20.39,64.63 | [工程推断·非史料] |
| 2785 | ARCH07.EAST.BACK.C13.B06 | 23 | 152.00,128.18 | [工程推断·非史料] |
| 2786 | ARCH07.EAST.BACK.C13.B07 | 28 | 71.07,65.67 | [工程推断·非史料] |
| 2787 | ARCH07.EAST.SPANDREL.C13.B00 | 19 | 102.70,82.74 | [工程推断·非史料] |
| 2788 | ARCH07.EAST.SPANDREL.C13.B01 | 24 | 135.50,105.69 | [工程推断·非史料] |
| 2789 | ARCH07.EAST.SPANDREL.C13.B02 | 19 | 102.67,91.62 | [工程推断·非史料] |
| 2790 | ARCH07.EAST.SPANDREL.C13.B03 | 24 | 172.46,0.00 | [工程推断·非史料] |
| 2791 | ARCH07.EAST.SPANDREL.C13.B04 | 19 | 0.00,127.94 | [工程推断·非史料] |
| 2792 | ARCH07.EAST.SPANDREL.C13.B05 | 24 | 134.91,127.82 | [工程推断·非史料] |
| 2793 | ARCH07.EAST.SPANDREL.C13.B06 | 19 | 101.95,127.94 | [工程推断·非史料] |
| 2794 | ARCH07.EAST.SPANDREL.C13.B07 | 24 | 26.94,174.17 | [工程推断·非史料] |
| 2795 | ARCH07.WEST.BACK.C13.B00 | 27 | 101.27,52.65 | [工程推断·非史料] |
| 2796 | ARCH07.WEST.BACK.C13.B01 | 29 | 169.77,104.65 | [工程推断·非史料] |
| 2797 | ARCH07.WEST.BACK.C13.B02 | 28 | 137.86,128.78 | [工程推断·非史料] |
| 2798 | ARCH07.WEST.BACK.C13.B03 | 24 | 56.12,26.99 | [工程推断·非史料] |
| 2799 | ARCH07.WEST.BACK.C13.B04 | 30 | 123.75,25.95 | [工程推断·非史料] |
| 2800 | ARCH07.WEST.BACK.C13.B05 | 30 | 40.77,64.63 | [工程推断·非史料] |
| 2801 | ARCH07.WEST.BACK.C13.B06 | 23 | 181.48,128.18 | [工程推断·非史料] |
| 2802 | ARCH07.WEST.BACK.C13.B07 | 28 | 23.78,65.67 | [工程推断·非史料] |
| 2803 | ARCH07.WEST.SPANDREL.C13.B00 | 19 | 0.00,91.62 | [工程推断·非史料] |
| 2804 | ARCH07.WEST.SPANDREL.C13.B01 | 24 | 189.55,105.69 | [工程推断·非史料] |
| 2805 | ARCH07.WEST.SPANDREL.C13.B02 | 19 | 0.00,107.36 | [工程推断·非史料] |
| 2806 | ARCH07.WEST.SPANDREL.C13.B03 | 24 | 28.06,26.99 | [工程推断·非史料] |
| 2807 | ARCH07.WEST.SPANDREL.C13.B04 | 19 | 102.02,107.36 | [工程推断·非史料] |
| 2808 | ARCH07.WEST.SPANDREL.C13.B05 | 24 | 161.87,127.82 | [工程推断·非史料] |
| 2809 | ARCH07.WEST.SPANDREL.C13.B06 | 19 | 152.89,127.94 | [工程推断·非史料] |
| 2810 | ARCH07.WEST.SPANDREL.C13.B07 | 24 | 80.80,174.17 | [工程推断·非史料] |
| 2811 | ARCH07.EAST.BACK.C14.B00 | 30 | 174.22,118.42 | [工程推断·非史料] |
| 2812 | ARCH07.EAST.BACK.C14.B01 | 28 | 89.36,195.22 | [工程推断·非史料] |
| 2813 | ARCH07.EAST.BACK.C14.B02 | 30 | 20.70,25.95 | [工程推断·非史料] |
| 2814 | ARCH07.EAST.BACK.C14.B03 | 27 | 98.44,153.56 | [工程推断·非史料] |
| 2815 | ARCH07.EAST.BACK.C14.B04 | 26 | 25.82,48.95 | [工程推断·非史料] |
| 2816 | ARCH07.EAST.BACK.C14.B05 | 29 | 83.58,140.45 | [工程推断·非史料] |
| 2817 | ARCH07.EAST.BACK.C14.B06 | 27 | 0.00,153.56 | [工程推断·非史料] |
| 2818 | ARCH07.EAST.BACK.C14.B07 | 28 | 95.83,43.18 | [工程推断·非史料] |
| 2819 | ARCH07.EAST.BACK.C14.B08 | 30 | 198.13,102.08 | [工程推断·非史料] |
| 2820 | ARCH07.EAST.SPANDREL.C14.B00 | 27 | 24.40,174.60 | [工程推断·非史料] |
| 2821 | ARCH07.EAST.SPANDREL.C14.B01 | 22 | 0.00,189.00 | [工程推断·非史料] |
| 2822 | ARCH07.EAST.SPANDREL.C14.B02 | 27 | 50.02,113.12 | [工程推断·非史料] |
| 2823 | ARCH07.EAST.SPANDREL.C14.B03 | 22 | 0.00,170.62 | [工程推断·非史料] |
| 2824 | ARCH07.EAST.SPANDREL.C14.B04 | 26 | 0.00,48.95 | [工程推断·非史料] |
| 2825 | ARCH07.EAST.SPANDREL.C14.B05 | 22 | 99.21,53.62 | [工程推断·非史料] |
| 2826 | ARCH07.EAST.SPANDREL.C14.B06 | 26 | 153.85,152.18 | [工程推断·非史料] |
| 2827 | ARCH07.EAST.SPANDREL.C14.B07 | 22 | 0.00,70.52 | [工程推断·非史料] |
| 2828 | ARCH07.EAST.SPANDREL.C14.B08 | 26 | 51.19,173.22 | [工程推断·非史料] |
| 2829 | ARCH07.WEST.BACK.C14.B00 | 30 | 193.51,118.42 | [工程推断·非史料] |
| 2830 | ARCH07.WEST.BACK.C14.B01 | 28 | 111.68,195.22 | [工程推断·非史料] |
| 2831 | ARCH07.WEST.BACK.C14.B02 | 30 | 41.32,25.95 | [工程推断·非史料] |
| 2832 | ARCH07.WEST.BACK.C14.B03 | 27 | 123.02,153.56 | [工程推断·非史料] |
| 2833 | ARCH07.WEST.BACK.C14.B04 | 26 | 77.46,48.95 | [工程推断·非史料] |
| 2834 | ARCH07.WEST.BACK.C14.B05 | 29 | 41.81,140.45 | [工程推断·非史料] |
| 2835 | ARCH07.WEST.BACK.C14.B06 | 27 | 24.63,153.56 | [工程推断·非史料] |
| 2836 | ARCH07.WEST.BACK.C14.B07 | 28 | 119.61,43.18 | [工程推断·非史料] |
| 2837 | ARCH07.WEST.BACK.C14.B08 | 30 | 0.00,118.42 | [工程推断·非史料] |
| 2838 | ARCH07.WEST.SPANDREL.C14.B00 | 27 | 0.00,174.60 | [工程推断·非史料] |
| 2839 | ARCH07.WEST.SPANDREL.C14.B01 | 22 | 48.70,189.00 | [工程推断·非史料] |
| 2840 | ARCH07.WEST.SPANDREL.C14.B02 | 27 | 75.03,113.12 | [工程推断·非史料] |
| 2841 | ARCH07.WEST.SPANDREL.C14.B03 | 22 | 49.17,170.62 | [工程推断·非史料] |
| 2842 | ARCH07.WEST.SPANDREL.C14.B04 | 26 | 51.64,48.95 | [工程推断·非史料] |
| 2843 | ARCH07.WEST.SPANDREL.C14.B05 | 22 | 0.00,53.62 | [工程推断·非史料] |
| 2844 | ARCH07.WEST.SPANDREL.C14.B06 | 26 | 179.45,152.18 | [工程推断·非史料] |
| 2845 | ARCH07.WEST.SPANDREL.C14.B07 | 22 | 49.59,70.52 | [工程推断·非史料] |
| 2846 | ARCH07.WEST.SPANDREL.C14.B08 | 26 | 76.77,173.22 | [工程推断·非史料] |
| 2847 | ARCH07.EAST.CORE.C15.B01 | 18 | 0.00,67.51 | [工程推断·非史料] |
| 2848 | ARCH07.EAST.CORE.C15.B02 | 17 | 0.00,64.44 | [工程推断·非史料] |

### S398 ARCH08.FILL (events 2849-3066)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 2884 | ARCH08.EAST.BACK.C09.B00 | 28 | 48.59,0.00 | [工程推断·非史料] |
| 2885 | ARCH08.EAST.BACK.C09.B06 | 24 | 27.03,127.82 | [工程推断·非史料] |
| 2886 | ARCH08.EAST.SPANDREL.C09.B00 | 19 | 0.00,0.00 | [工程推断·非史料] |
| 2887 | ARCH08.EAST.SPANDREL.C09.B06 | 19 | 0.00,48.46 | [工程推断·非史料] |
| 2888 | ARCH08.WEST.BACK.C09.B00 | 28 | 72.89,0.00 | [工程推断·非史料] |
| 2889 | ARCH08.WEST.BACK.C09.B06 | 24 | 54.00,127.82 | [工程推断·非史料] |
| 2890 | ARCH08.WEST.SPANDREL.C09.B00 | 19 | 51.47,0.00 | [工程推断·非史料] |
| 2891 | ARCH08.WEST.SPANDREL.C09.B06 | 19 | 51.41,48.46 | [工程推断·非史料] |
| 2892 | ARCH08.EAST.BACK.C10.B00 | 29 | 64.70,63.17 | [工程推断·非史料] |
| 2893 | ARCH08.EAST.BACK.C10.B01 | 28 | 161.57,107.81 | [工程推断·非史料] |
| 2896 | ARCH08.EAST.BACK.C10.B07 | 30 | 20.10,83.76 | [工程推断·非史料] |
| 2897 | ARCH08.EAST.BACK.C10.B08 | 29 | 104.47,140.45 | [工程推断·非史料] |
| 2898 | ARCH08.EAST.BACK.C10.B09 | 28 | 69.35,107.81 | [工程推断·非史料] |
| 2899 | ARCH08.EAST.SPANDREL.C10.B00 | 26 | 103.02,94.78 | [工程推断·非史料] |
| 2900 | ARCH08.EAST.SPANDREL.C10.B01 | 21 | 0.00,183.52 | [工程推断·非史料] |
| 2901 | ARCH08.EAST.SPANDREL.C10.B07 | 21 | 0.00,193.22 | [工程推断·非史料] |
| 2902 | ARCH08.EAST.SPANDREL.C10.B08 | 26 | 102.92,119.18 | [工程推断·非史料] |
| 2903 | ARCH08.EAST.SPANDREL.C10.B09 | 21 | 0.00,211.54 | [工程推断·非史料] |
| 2904 | ARCH08.WEST.BACK.C10.B00 | 29 | 86.23,63.17 | [工程推断·非史料] |
| 2905 | ARCH08.WEST.BACK.C10.B01 | 28 | 184.62,107.81 | [工程推断·非史料] |
| 2908 | ARCH08.WEST.BACK.C10.B07 | 30 | 40.09,83.76 | [工程推断·非史料] |
| 2909 | ARCH08.WEST.BACK.C10.B08 | 29 | 125.26,140.45 | [工程推断·非史料] |
| 2910 | ARCH08.WEST.BACK.C10.B09 | 28 | 115.46,107.81 | [工程推断·非史料] |
| 2911 | ARCH08.WEST.SPANDREL.C10.B00 | 26 | 128.76,94.78 | [工程推断·非史料] |
| 2912 | ARCH08.WEST.SPANDREL.C10.B01 | 21 | 49.73,183.52 | [工程推断·非史料] |
| 2913 | ARCH08.WEST.SPANDREL.C10.B07 | 21 | 49.71,193.22 | [工程推断·非史料] |
| 2914 | ARCH08.WEST.SPANDREL.C10.B08 | 26 | 128.62,119.18 | [工程推断·非史料] |
| 2915 | ARCH08.WEST.SPANDREL.C10.B09 | 21 | 99.41,211.54 | [工程推断·非史料] |
| 2916 | ARCH08.EAST.CORE.C13.B00 | 6 | 0.00,135.03 | [工程推断·非史料] |
| 2918 | ARCH08.EAST.CORE.C13.B02 | 5 | 0.00,141.07 | [工程推断·非史料] |
| 2919 | ARCH08.EAST.BACK.C11.B00 | 28 | 158.53,177.21 | [工程推断·非史料] |
| 2920 | ARCH08.EAST.BACK.C11.B01 | 29 | 193.66,63.17 | [工程推断·非史料] |
| 2921 | ARCH08.EAST.BACK.C11.B05 | 23 | 129.22,102.48 | [工程推断·非史料] |
| 2922 | ARCH08.EAST.SPANDREL.C11.B00 | 21 | 99.47,161.18 | [工程推断·非史料] |
| 2923 | ARCH08.EAST.SPANDREL.C11.B01 | 26 | 0.00,119.18 | [工程推断·非史料] |
| 2924 | ARCH08.EAST.SPANDREL.C11.B05 | 23 | 98.82,102.48 | [工程推断·非史料] |
| 2925 | ARCH08.WEST.BACK.C11.B00 | 28 | 180.87,177.21 | [工程推断·非史料] |
| 2926 | ARCH08.WEST.BACK.C11.B01 | 29 | 150.81,63.17 | [工程推断·非史料] |
| 2927 | ARCH08.WEST.BACK.C11.B05 | 23 | 0.00,128.18 | [工程推断·非史料] |
| 2928 | ARCH08.WEST.SPANDREL.C11.B00 | 21 | 0.00,161.18 | [工程推断·非史料] |
| 2929 | ARCH08.WEST.SPANDREL.C11.B01 | 26 | 51.46,119.18 | [工程推断·非史料] |
| 2930 | ARCH08.WEST.SPANDREL.C11.B05 | 23 | 159.62,102.48 | [工程推断·非史料] |
| 2931 | ARCH08.EAST.BACK.C12.B00 | 23 | 0.00,51.81 | [工程推断·非史料] |
| 2932 | ARCH08.EAST.BACK.C12.B01 | 30 | 58.37,118.42 | [工程推断·非史料] |
| 2934 | ARCH08.EAST.BACK.C12.B05 | 29 | 147.27,122.55 | [工程推断·非史料] |
| 2935 | ARCH08.EAST.BACK.C12.B06 | 23 | 67.44,77.15 | [工程推断·非史料] |
| 2936 | ARCH08.EAST.SPANDREL.C12.B00 | 23 | 179.94,25.90 | [工程推断·非史料] |
| 2937 | ARCH08.EAST.SPANDREL.C12.B01 | 22 | 0.00,134.74 | [工程推断·非史料] |
| 2939 | ARCH08.EAST.SPANDREL.C12.B05 | 22 | 0.00,159.04 | [工程推断·非史料] |
| 2940 | ARCH08.EAST.SPANDREL.C12.B06 | 23 | 34.50,77.15 | [工程推断·非史料] |
| 2941 | ARCH08.WEST.BACK.C12.B00 | 23 | 69.00,51.81 | [工程推断·非史料] |
| 2942 | ARCH08.WEST.BACK.C12.B01 | 30 | 19.73,118.42 | [工程推断·非史料] |
| 2944 | ARCH08.WEST.BACK.C12.B05 | 29 | 168.19,122.55 | [工程推断·非史料] |
| 2945 | ARCH08.WEST.BACK.C12.B06 | 23 | 133.32,77.15 | [工程推断·非史料] |
| 2946 | ARCH08.WEST.SPANDREL.C12.B00 | 23 | 34.50,51.81 | [工程推断·非史料] |
| 2947 | ARCH08.WEST.SPANDREL.C12.B01 | 22 | 49.34,134.74 | [工程推断·非史料] |
| 2948 | ARCH08.WEST.SPANDREL.C12.B05 | 22 | 98.65,159.04 | [工程推断·非史料] |
| 2949 | ARCH08.WEST.SPANDREL.C12.B06 | 23 | 100.38,77.15 | [工程推断·非史料] |
| 2950 | ARCH08.EAST.CORE.C14.B00 | 12 | 0.00,67.51 | [工程推断·非史料] |
| 2951 | ARCH08.EAST.CORE.C14.B02 | 11 | 0.00,0.00 | [工程推断·非史料] |
| 2952 | ARCH08.EAST.BACK.C13.B00 | 26 | 103.35,25.79 | [工程推断·非史料] |
| 2953 | ARCH08.EAST.BACK.C13.B01 | 27 | 151.88,52.65 | [工程推断·非史料] |
| 2954 | ARCH08.EAST.BACK.C13.B02 | 26 | 154.20,133.86 | [工程推断·非史料] |
| 2955 | ARCH08.EAST.BACK.C13.B03 | 29 | 149.55,83.91 | [工程推断·非史料] |
| 2956 | ARCH08.EAST.BACK.C13.B07 | 23 | 0.00,180.60 | [工程推断·非史料] |
| 2957 | ARCH08.EAST.BACK.C13.B08 | 30 | 179.87,83.76 | [工程推断·非史料] |
| 2958 | ARCH08.EAST.SPANDREL.C13.B00 | 19 | 101.89,157.42 | [工程推断·非史料] |
| 2959 | ARCH08.EAST.SPANDREL.C13.B01 | 24 | 134.67,174.17 | [工程推断·非史料] |
| 2960 | ARCH08.EAST.SPANDREL.C13.B02 | 19 | 101.51,186.90 | [工程推断·非史料] |
| 2961 | ARCH08.EAST.SPANDREL.C13.B03 | 24 | 27.35,105.69 | [工程推断·非史料] |
| 2962 | ARCH08.EAST.SPANDREL.C13.B07 | 23 | 176.88,153.89 | [工程推断·非史料] |
| 2963 | ARCH08.EAST.SPANDREL.C13.B08 | 20 | 101.41,42.44 | [工程推断·非史料] |
| 2964 | ARCH08.WEST.BACK.C13.B00 | 26 | 129.17,25.79 | [工程推断·非史料] |
| 2965 | ARCH08.WEST.BACK.C13.B01 | 27 | 177.19,52.65 | [工程推断·非史料] |
| 2966 | ARCH08.WEST.BACK.C13.B02 | 26 | 179.85,133.86 | [工程推断·非史料] |
| 2967 | ARCH08.WEST.BACK.C13.B03 | 29 | 170.82,83.91 | [工程推断·非史料] |
| 2968 | ARCH08.WEST.BACK.C13.B07 | 23 | 58.96,180.60 | [工程推断·非史料] |
| 2969 | ARCH08.WEST.BACK.C13.B08 | 30 | 199.79,83.76 | [工程推断·非史料] |
| 2970 | ARCH08.WEST.SPANDREL.C13.B00 | 19 | 152.64,157.42 | [工程推断·非史料] |
| 2971 | ARCH08.WEST.SPANDREL.C13.B01 | 24 | 161.42,174.17 | [工程推断·非史料] |
| 2972 | ARCH08.WEST.SPANDREL.C13.B02 | 19 | 152.26,186.90 | [工程推断·非史料] |
| 2973 | ARCH08.WEST.SPANDREL.C13.B03 | 24 | 54.39,105.69 | [工程推断·非史料] |
| 2974 | ARCH08.WEST.SPANDREL.C13.B07 | 23 | 29.48,180.60 | [工程推断·非史料] |
| 2975 | ARCH08.WEST.SPANDREL.C13.B08 | 20 | 0.00,42.44 | [工程推断·非史料] |
| 2976 | ARCH08.EAST.BACK.C14.B00 | 30 | 100.04,83.76 | [工程推断·非史料] |
| 2977 | ARCH08.EAST.BACK.C14.B01 | 30 | 142.34,64.63 | [工程推断·非史料] |
| 2978 | ARCH08.EAST.BACK.C14.B02 | 29 | 132.47,20.38 | [工程推断·非史料] |
| 2979 | ARCH08.EAST.BACK.C14.B03 | 29 | 155.75,0.00 | [工程推断·非史料] |
| 2980 | ARCH08.EAST.BACK.C14.B04 | 28 | 46.09,128.78 | [工程推断·非史料] |
| 2981 | ARCH08.EAST.BACK.C14.B05 | 27 | 51.04,0.00 | [工程推断·非史料] |
| 2982 | ARCH08.EAST.BACK.C14.B06 | 30 | 55.04,146.28 | [工程推断·非史料] |
| 2983 | ARCH08.EAST.BACK.C14.B07 | 29 | 196.94,42.43 | [工程推断·非史料] |
| 2984 | ARCH08.EAST.BACK.C14.B08 | 28 | 118.37,65.67 | [工程推断·非史料] |
| 2985 | ARCH08.EAST.BACK.C14.B09 | 28 | 0.00,163.09 | [工程推断·非史料] |
| 2986 | ARCH08.EAST.BACK.C14.B10 | 25 | 130.97,117.38 | [工程推断·非史料] |
| 2987 | ARCH08.EAST.SPANDREL.C14.B00 | 24 | 79.85,192.82 | [工程推断·非史料] |
| 2988 | ARCH08.EAST.SPANDREL.C14.B01 | 20 | 0.00,111.22 | [工程推断·非史料] |
| 2989 | ARCH08.EAST.SPANDREL.C14.B02 | 25 | 26.28,48.40 | [工程推断·非史料] |
| 2990 | ARCH08.EAST.SPANDREL.C14.B03 | 20 | 0.00,124.24 | [工程推断·非史料] |
| 2991 | ARCH08.EAST.SPANDREL.C14.B04 | 25 | 131.24,48.40 | [工程推断·非史料] |
| 2992 | ARCH08.EAST.SPANDREL.C14.B05 | 20 | 0.00,134.62 | [工程推断·非史料] |
| 2993 | ARCH08.EAST.SPANDREL.C14.B06 | 25 | 26.23,70.42 | [工程推断·非史料] |
| 2994 | ARCH08.EAST.SPANDREL.C14.B07 | 20 | 0.00,160.14 | [工程推断·非史料] |
| 2995 | ARCH08.EAST.SPANDREL.C14.B08 | 25 | 183.52,70.42 | [工程推断·非史料] |
| 2996 | ARCH08.EAST.SPANDREL.C14.B09 | 20 | 0.00,180.88 | [工程推断·非史料] |
| 2997 | ARCH08.EAST.SPANDREL.C14.B10 | 25 | 79.53,0.00 | [工程推断·非史料] |
| 2998 | ARCH08.WEST.BACK.C14.B00 | 30 | 120.00,83.76 | [工程推断·非史料] |
| 2999 | ARCH08.WEST.BACK.C14.B01 | 30 | 162.44,64.63 | [工程推断·非史料] |
| 3000 | ARCH08.WEST.BACK.C14.B02 | 29 | 154.49,20.38 | [工程推断·非史料] |
| 3001 | ARCH08.WEST.BACK.C14.B03 | 29 | 177.86,0.00 | [工程推断·非史料] |
| 3002 | ARCH08.WEST.BACK.C14.B04 | 28 | 69.03,128.78 | [工程推断·非史料] |
| 3003 | ARCH08.WEST.BACK.C14.B05 | 27 | 76.56,0.00 | [工程推断·非史料] |
| 3004 | ARCH08.WEST.BACK.C14.B06 | 30 | 73.29,146.28 | [工程推断·非史料] |
| 3005 | ARCH08.WEST.BACK.C14.B07 | 29 | 21.57,63.17 | [工程推断·非史料] |
| 3006 | ARCH08.WEST.BACK.C14.B08 | 28 | 141.85,65.67 | [工程推断·非史料] |
| 3007 | ARCH08.WEST.BACK.C14.B09 | 28 | 22.74,163.09 | [工程推断·非史料] |
| 3008 | ARCH08.WEST.BACK.C14.B10 | 25 | 157.10,117.38 | [工程推断·非史料] |
| 3009 | ARCH08.WEST.SPANDREL.C14.B00 | 24 | 26.75,192.82 | [工程推断·非史料] |
| 3010 | ARCH08.WEST.SPANDREL.C14.B01 | 20 | 50.25,111.22 | [工程推断·非史料] |
| 3011 | ARCH08.WEST.SPANDREL.C14.B02 | 25 | 52.52,48.40 | [工程推断·非史料] |
| 3012 | ARCH08.WEST.SPANDREL.C14.B03 | 20 | 50.23,124.24 | [工程推断·非史料] |
| 3013 | ARCH08.WEST.SPANDREL.C14.B04 | 25 | 183.70,48.40 | [工程推断·非史料] |
| 3014 | ARCH08.WEST.SPANDREL.C14.B05 | 20 | 50.23,134.62 | [工程推断·非史料] |
| 3015 | ARCH08.WEST.SPANDREL.C14.B06 | 25 | 52.45,70.42 | [工程推断·非史料] |
| 3016 | ARCH08.WEST.SPANDREL.C14.B07 | 20 | 100.43,160.14 | [工程推断·非史料] |
| 3017 | ARCH08.WEST.SPANDREL.C14.B08 | 25 | 131.11,70.42 | [工程推断·非史料] |
| 3018 | ARCH08.WEST.SPANDREL.C14.B09 | 20 | 50.21,180.88 | [工程推断·非史料] |
| 3019 | ARCH08.WEST.SPANDREL.C14.B10 | 25 | 26.52,0.00 | [工程推断·非史料] |
| 3020 | ARCH08.EAST.CORE.C15.B00 | 18 | 0.00,0.00 | [工程推断·非史料] |
| 3021 | ARCH08.EAST.CORE.C15.B01 | 16 | 0.00,70.53 | [工程推断·非史料] |
| 3022 | ARCH08.EAST.CORE.C15.B02 | 15 | 0.00,0.00 | [工程推断·非史料] |
| 3023 | ARCH08.EAST.BACK.C15.B00 | 28 | 90.94,163.09 | [工程推断·非史料] |
| 3024 | ARCH08.EAST.BACK.C15.B02 | 28 | 178.64,195.22 | [工程推断·非史料] |
| 3025 | ARCH08.EAST.BACK.C15.B05 | 26 | 25.84,0.00 | [工程推断·非史料] |
| 3026 | ARCH08.EAST.SPANDREL.C15.B00 | 22 | 0.00,178.04 | [工程推断·非史料] |
| 3027 | ARCH08.EAST.SPANDREL.C15.B02 | 22 | 0.00,126.64 | [工程推断·非史料] |
| 3028 | ARCH08.EAST.SPANDREL.C15.B05 | 26 | 0.00,0.00 | [工程推断·非史料] |
| 3029 | ARCH08.WEST.BACK.C15.B00 | 28 | 136.30,163.09 | [工程推断·非史料] |
| 3030 | ARCH08.WEST.BACK.C15.B02 | 29 | 0.00,0.00 | [工程推断·非史料] |
| 3031 | ARCH08.WEST.BACK.C15.B05 | 26 | 77.52,0.00 | [工程推断·非史料] |
| 3032 | ARCH08.WEST.SPANDREL.C15.B00 | 22 | 98.31,178.04 | [工程推断·非史料] |
| 3033 | ARCH08.WEST.SPANDREL.C15.B02 | 22 | 49.36,126.64 | [工程推断·非史料] |
| 3034 | ARCH08.WEST.SPANDREL.C15.B05 | 26 | 51.68,0.00 | [工程推断·非史料] |
| 3035 | ARCH08.EAST.BACK.C15.B01 | 29 | 21.42,83.91 | [工程推断·非史料] |
| 3036 | ARCH08.EAST.BACK.C15.B04 | 28 | 67.97,177.21 | [工程推断·非史料] |
| 3037 | ARCH08.EAST.BACK.C15.B06 | 28 | 0.00,43.18 | [工程推断·非史料] |
| 3038 | ARCH08.EAST.BACK.C15.B07 | 27 | 0.00,132.52 | [工程推断·非史料] |
| 3039 | ARCH08.EAST.BACK.C15.B08 | 28 | 194.23,0.00 | [工程推断·非史料] |
| 3040 | ARCH08.EAST.BACK.C15.B09 | 28 | 140.17,86.83 | [工程推断·非史料] |
| 3041 | ARCH08.EAST.BACK.C15.B10 | 29 | 21.15,122.55 | [工程推断·非史料] |
| 3042 | ARCH08.EAST.SPANDREL.C15.B01 | 27 | 50.61,70.55 | [工程推断·非史料] |
| 3043 | ARCH08.EAST.SPANDREL.C15.B04 | 22 | 0.00,94.30 | [工程推断·非史料] |
| 3044 | ARCH08.EAST.SPANDREL.C15.B06 | 21 | 0.00,104.16 | [工程推断·非史料] |
| 3045 | ARCH08.EAST.SPANDREL.C15.B07 | 25 | 129.71,180.36 | [工程推断·非史料] |
| 3046 | ARCH08.EAST.SPANDREL.C15.B08 | 21 | 99.68,115.96 | [工程推断·非史料] |
| 3047 | ARCH08.EAST.SPANDREL.C15.B09 | 26 | 0.00,25.79 | [工程推断·非史料] |
| 3048 | ARCH08.EAST.SPANDREL.C15.B10 | 21 | 0.00,131.66 | [工程推断·非史料] |
| 3049 | ARCH08.WEST.BACK.C15.B01 | 29 | 64.20,83.91 | [工程推断·非史料] |
| 3050 | ARCH08.WEST.BACK.C15.B04 | 28 | 90.61,177.21 | [工程推断·非史料] |
| 3051 | ARCH08.WEST.BACK.C15.B06 | 28 | 169.31,23.63 | [工程推断·非史料] |
| 3052 | ARCH08.WEST.BACK.C15.B07 | 27 | 24.84,132.52 | [工程推断·非史料] |
| 3053 | ARCH08.WEST.BACK.C15.B08 | 28 | 0.00,23.63 | [工程推断·非史料] |
| 3054 | ARCH08.WEST.BACK.C15.B09 | 28 | 163.33,86.83 | [工程推断·非史料] |
| 3055 | ARCH08.WEST.BACK.C15.B10 | 29 | 42.18,122.55 | [工程推断·非史料] |
| 3056 | ARCH08.WEST.SPANDREL.C15.B01 | 27 | 75.88,70.55 | [工程推断·非史料] |
| 3057 | ARCH08.WEST.SPANDREL.C15.B04 | 22 | 49.58,94.30 | [工程推断·非史料] |
| 3058 | ARCH08.WEST.SPANDREL.C15.B06 | 21 | 49.85,104.16 | [工程推断·非史料] |
| 3059 | ARCH08.WEST.SPANDREL.C15.B07 | 25 | 155.56,180.36 | [工程推断·非史料] |
| 3060 | ARCH08.WEST.SPANDREL.C15.B08 | 21 | 0.00,115.96 | [工程推断·非史料] |
| 3061 | ARCH08.WEST.SPANDREL.C15.B09 | 26 | 25.84,25.79 | [工程推断·非史料] |
| 3062 | ARCH08.WEST.SPANDREL.C15.B10 | 21 | 49.83,131.66 | [工程推断·非史料] |
| 3063 | ARCH08.EAST.BACK.C15.B03 | 28 | 68.63,144.52 | [工程推断·非史料] |
| 3064 | ARCH08.EAST.SPANDREL.C15.B03 | 27 | 153.12,0.00 | [工程推断·非史料] |
| 3065 | ARCH08.WEST.BACK.C15.B03 | 28 | 91.48,144.52 | [工程推断·非史料] |
| 3066 | ARCH08.WEST.SPANDREL.C15.B03 | 27 | 178.56,0.00 | [工程推断·非史料] |

### S399 ARCH09.FILL (events 3067-3282)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 3102 | ARCH09.EAST.BACK.C09.B00 | 27 | 25.01,113.12 | [工程推断·非史料] |
| 3104 | ARCH09.EAST.SPANDREL.C09.B00 | 19 | 0.00,63.34 | [工程推断·非史料] |
| 3106 | ARCH09.WEST.BACK.C09.B00 | 27 | 0.00,113.12 | [工程推断·非史料] |
| 3108 | ARCH09.WEST.SPANDREL.C09.B00 | 19 | 51.40,63.34 | [工程推断·非史料] |
| 3110 | ARCH09.EAST.BACK.C10.B00 | 29 | 0.00,157.35 | [工程推断·非史料] |
| 3111 | ARCH09.EAST.BACK.C10.B01 | 27 | 73.14,195.93 | [工程推断·非史料] |
| 3112 | ARCH09.EAST.BACK.C10.B02 | 27 | 124.19,132.52 | [工程推断·非史料] |
| 3113 | ARCH09.EAST.BACK.C10.B08 | 30 | 97.01,118.42 | [工程推断·非史料] |
| 3114 | ARCH09.EAST.BACK.C10.B09 | 28 | 48.17,43.18 | [工程推断·非史料] |
| 3115 | ARCH09.EAST.SPANDREL.C10.B00 | 26 | 0.00,133.86 | [工程推断·非史料] |
| 3116 | ARCH09.EAST.SPANDREL.C10.B01 | 22 | 99.40,0.00 | [工程推断·非史料] |
| 3117 | ARCH09.EAST.SPANDREL.C10.B02 | 26 | 128.50,133.86 | [工程推断·非史料] |
| 3118 | ARCH09.EAST.SPANDREL.C10.B08 | 26 | 51.40,133.86 | [工程推断·非史料] |
| 3119 | ARCH09.EAST.SPANDREL.C10.B09 | 22 | 0.00,0.00 | [工程推断·非史料] |
| 3120 | ARCH09.WEST.BACK.C10.B00 | 29 | 187.64,140.45 | [工程推断·非史料] |
| 3121 | ARCH09.WEST.BACK.C10.B01 | 27 | 97.52,195.93 | [工程推断·非史料] |
| 3122 | ARCH09.WEST.BACK.C10.B02 | 27 | 99.36,132.52 | [工程推断·非史料] |
| 3123 | ARCH09.WEST.BACK.C10.B08 | 30 | 116.33,118.42 | [工程推断·非史料] |
| 3124 | ARCH09.WEST.BACK.C10.B09 | 28 | 72.00,43.18 | [工程推断·非史料] |
| 3125 | ARCH09.WEST.SPANDREL.C10.B00 | 26 | 25.70,133.86 | [工程推断·非史料] |
| 3126 | ARCH09.WEST.SPANDREL.C10.B01 | 22 | 149.10,0.00 | [工程推断·非史料] |
| 3127 | ARCH09.WEST.SPANDREL.C10.B02 | 26 | 102.80,133.86 | [工程推断·非史料] |
| 3128 | ARCH09.WEST.SPANDREL.C10.B08 | 26 | 77.10,133.86 | [工程推断·非史料] |
| 3129 | ARCH09.WEST.SPANDREL.C10.B09 | 22 | 49.70,0.00 | [工程推断·非史料] |
| 3130 | ARCH09.EAST.CORE.C13.B00 | 5 | 0.00,0.00 | [工程推断·非史料] |
| 3132 | ARCH09.EAST.CORE.C13.B02 | 5 | 0.00,70.53 | [工程推断·非史料] |
| 3133 | ARCH09.EAST.BACK.C11.B00 | 23 | 110.10,25.90 | [工程推断·非史料] |
| 3135 | ARCH09.EAST.BACK.C11.B04 | 30 | 0.00,128.12 | [工程推断·非史料] |
| 3136 | ARCH09.EAST.BACK.C11.B05 | 24 | 27.82,53.99 | [工程推断·非史料] |
| 3137 | ARCH09.EAST.SPANDREL.C11.B00 | 22 | 49.70,18.70 | [工程推断·非史料] |
| 3138 | ARCH09.EAST.SPANDREL.C11.B04 | 22 | 99.40,18.70 | [工程推断·非史料] |
| 3139 | ARCH09.EAST.SPANDREL.C11.B05 | 24 | 0.00,53.99 | [工程推断·非史料] |
| 3140 | ARCH09.WEST.BACK.C11.B00 | 23 | 145.02,25.90 | [工程推断·非史料] |
| 3142 | ARCH09.WEST.BACK.C11.B04 | 30 | 19.06,128.12 | [工程推断·非史料] |
| 3143 | ARCH09.WEST.BACK.C11.B05 | 24 | 83.46,53.99 | [工程推断·非史料] |
| 3144 | ARCH09.WEST.SPANDREL.C11.B00 | 22 | 0.00,18.70 | [工程推断·非史料] |
| 3145 | ARCH09.WEST.SPANDREL.C11.B04 | 22 | 149.10,18.70 | [工程推断·非史料] |
| 3146 | ARCH09.WEST.SPANDREL.C11.B05 | 24 | 55.64,53.99 | [工程推断·非史料] |
| 3147 | ARCH09.EAST.BACK.C12.B00 | 23 | 37.46,0.00 | [工程推断·非史料] |
| 3148 | ARCH09.EAST.BACK.C12.B01 | 29 | 127.43,104.65 | [工程推断·非史料] |
| 3150 | ARCH09.EAST.BACK.C12.B05 | 30 | 101.91,64.63 | [工程推断·非史料] |
| 3151 | ARCH09.EAST.BACK.C12.B06 | 23 | 0.00,25.90 | [工程推断·非史料] |
| 3152 | ARCH09.EAST.SPANDREL.C12.B00 | 23 | 0.00,0.00 | [工程推断·非史料] |
| 3153 | ARCH09.EAST.SPANDREL.C12.B01 | 21 | 99.80,92.58 | [工程推断·非史料] |
| 3155 | ARCH09.EAST.SPANDREL.C12.B05 | 21 | 0.00,92.58 | [工程推断·非史料] |
| 3156 | ARCH09.EAST.SPANDREL.C12.B06 | 23 | 149.84,0.00 | [工程推断·非史料] |
| 3157 | ARCH09.WEST.BACK.C12.B00 | 23 | 112.38,0.00 | [工程推断·非史料] |
| 3158 | ARCH09.WEST.BACK.C12.B01 | 29 | 106.25,104.65 | [工程推断·非史料] |
| 3160 | ARCH09.WEST.BACK.C12.B05 | 30 | 122.12,64.63 | [工程推断·非史料] |
| 3161 | ARCH09.WEST.BACK.C12.B06 | 23 | 73.40,25.90 | [工程推断·非史料] |
| 3162 | ARCH09.WEST.SPANDREL.C12.B00 | 23 | 74.92,0.00 | [工程推断·非史料] |
| 3163 | ARCH09.WEST.SPANDREL.C12.B01 | 21 | 149.70,92.58 | [工程推断·非史料] |
| 3164 | ARCH09.WEST.SPANDREL.C12.B05 | 21 | 49.90,92.58 | [工程推断·非史料] |
| 3165 | ARCH09.WEST.SPANDREL.C12.B06 | 23 | 36.70,25.90 | [工程推断·非史料] |
| 3166 | ARCH09.EAST.CORE.C14.B00 | 10 | 0.00,0.00 | [工程推断·非史料] |
| 3167 | ARCH09.EAST.CORE.C14.B02 | 10 | 0.00,70.53 | [工程推断·非史料] |
| 3168 | ARCH09.EAST.BACK.C13.B00 | 30 | 76.03,128.12 | [工程推断·非史料] |
| 3169 | ARCH09.EAST.BACK.C13.B01 | 23 | 88.44,153.89 | [工程推断·非史料] |
| 3170 | ARCH09.EAST.BACK.C13.B02 | 29 | 66.90,0.00 | [工程推断·非史料] |
| 3171 | ARCH09.EAST.BACK.C13.B05 | 29 | 111.45,0.00 | [工程推断·非史料] |
| 3172 | ARCH09.EAST.BACK.C13.B06 | 28 | 190.95,43.18 | [工程推断·非史料] |
| 3173 | ARCH09.EAST.BACK.C13.B07 | 25 | 25.98,180.36 | [工程推断·非史料] |
| 3174 | ARCH09.EAST.SPANDREL.C13.B00 | 21 | 0.00,25.52 | [工程推断·非史料] |
| 3175 | ARCH09.EAST.SPANDREL.C13.B01 | 23 | 58.96,153.89 | [工程推断·非史料] |
| 3176 | ARCH09.EAST.SPANDREL.C13.B02 | 21 | 0.00,43.68 | [工程推断·非史料] |
| 3177 | ARCH09.EAST.SPANDREL.C13.B05 | 25 | 78.35,139.40 | [工程推断·非史料] |
| 3178 | ARCH09.EAST.SPANDREL.C13.B06 | 21 | 100.22,25.52 | [工程推断·非史料] |
| 3179 | ARCH09.EAST.SPANDREL.C13.B07 | 25 | 52.24,139.40 | [工程推断·非史料] |
| 3180 | ARCH09.WEST.BACK.C13.B00 | 30 | 94.82,128.12 | [工程推断·非史料] |
| 3181 | ARCH09.WEST.BACK.C13.B01 | 23 | 147.40,153.89 | [工程推断·非史料] |
| 3182 | ARCH09.WEST.BACK.C13.B02 | 29 | 89.17,0.00 | [工程推断·非史料] |
| 3183 | ARCH09.WEST.BACK.C13.B05 | 29 | 133.60,0.00 | [工程推断·非史料] |
| 3184 | ARCH09.WEST.BACK.C13.B06 | 28 | 0.00,65.67 | [工程推断·非史料] |
| 3185 | ARCH09.WEST.BACK.C13.B07 | 25 | 51.93,180.36 | [工程推断·非史料] |
| 3186 | ARCH09.WEST.SPANDREL.C13.B00 | 21 | 50.11,25.52 | [工程推断·非史料] |
| 3187 | ARCH09.WEST.SPANDREL.C13.B01 | 23 | 117.92,153.89 | [工程推断·非史料] |
| 3188 | ARCH09.WEST.SPANDREL.C13.B02 | 21 | 50.11,43.68 | [工程推断·非史料] |
| 3189 | ARCH09.WEST.SPANDREL.C13.B05 | 25 | 104.46,139.40 | [工程推断·非史料] |
| 3190 | ARCH09.WEST.SPANDREL.C13.B06 | 21 | 150.33,25.52 | [工程推断·非史料] |
| 3191 | ARCH09.WEST.SPANDREL.C13.B07 | 25 | 26.13,139.40 | [工程推断·非史料] |
| 3192 | ARCH09.EAST.BACK.C14.B00 | 30 | 113.62,128.12 | [工程推断·非史料] |
| 3193 | ARCH09.EAST.BACK.C14.B01 | 30 | 36.71,146.28 | [工程推断·非史料] |
| 3194 | ARCH09.EAST.BACK.C14.B02 | 28 | 0.00,86.83 | [工程推断·非史料] |
| 3195 | ARCH09.EAST.BACK.C14.B03 | 29 | 106.99,83.91 | [工程推断·非史料] |
| 3196 | ARCH09.EAST.BACK.C14.B04 | 28 | 160.02,144.52 | [工程推断·非史料] |
| 3197 | ARCH09.EAST.BACK.C14.B05 | 27 | 0.00,0.00 | [工程推断·非史料] |
| 3198 | ARCH09.EAST.BACK.C14.B06 | 29 | 105.26,122.55 | [工程推断·非史料] |
| 3199 | ARCH09.EAST.BACK.C14.B07 | 25 | 77.89,180.36 | [工程推断·非史料] |
| 3200 | ARCH09.EAST.BACK.C14.B08 | 29 | 22.02,42.43 | [工程推断·非史料] |
| 3201 | ARCH09.EAST.BACK.C14.B09 | 27 | 150.04,113.12 | [工程推断·非史料] |
| 3202 | ARCH09.EAST.BACK.C14.B10 | 30 | 39.83,102.08 | [工程推断·非史料] |
| 3203 | ARCH09.EAST.SPANDREL.C14.B00 | 25 | 104.80,93.90 | [工程推断·非史料] |
| 3204 | ARCH09.EAST.SPANDREL.C14.B01 | 20 | 0.00,191.32 | [工程推断·非史料] |
| 3205 | ARCH09.EAST.SPANDREL.C14.B02 | 25 | 131.00,93.90 | [工程推断·非史料] |
| 3206 | ARCH09.EAST.SPANDREL.C14.B03 | 21 | 0.00,0.00 | [工程推断·非史料] |
| 3207 | ARCH09.EAST.SPANDREL.C14.B04 | 25 | 78.58,117.38 | [工程推断·非史料] |
| 3208 | ARCH09.EAST.SPANDREL.C14.B05 | 21 | 150.58,0.00 | [工程推断·非史料] |
| 3209 | ARCH09.EAST.SPANDREL.C14.B06 | 25 | 26.19,117.38 | [工程推断·非史料] |
| 3210 | ARCH09.EAST.SPANDREL.C14.B07 | 20 | 0.00,204.34 | [工程推断·非史料] |
| 3211 | ARCH09.EAST.SPANDREL.C14.B08 | 25 | 183.39,93.90 | [工程推断·非史料] |
| 3212 | ARCH09.EAST.SPANDREL.C14.B09 | 20 | 150.59,191.32 | [工程推断·非史料] |
| 3213 | ARCH09.EAST.SPANDREL.C14.B10 | 25 | 26.21,93.90 | [工程推断·非史料] |
| 3214 | ARCH09.WEST.BACK.C14.B00 | 30 | 132.32,128.12 | [工程推断·非史料] |
| 3215 | ARCH09.WEST.BACK.C14.B01 | 30 | 18.38,146.28 | [工程推断·非史料] |
| 3216 | ARCH09.WEST.BACK.C14.B02 | 28 | 23.48,86.83 | [工程推断·非史料] |
| 3217 | ARCH09.WEST.BACK.C14.B03 | 29 | 128.27,83.91 | [工程推断·非史料] |
| 3218 | ARCH09.WEST.BACK.C14.B04 | 28 | 182.80,144.52 | [工程推断·非史料] |
| 3219 | ARCH09.WEST.BACK.C14.B05 | 27 | 25.52,0.00 | [工程推断·非史料] |
| 3220 | ARCH09.WEST.BACK.C14.B06 | 29 | 126.26,122.55 | [工程推断·非史料] |
| 3221 | ARCH09.WEST.BACK.C14.B07 | 25 | 103.80,180.36 | [工程推断·非史料] |
| 3222 | ARCH09.WEST.BACK.C14.B08 | 29 | 44.04,42.43 | [工程推断·非史料] |
| 3223 | ARCH09.WEST.BACK.C14.B09 | 27 | 174.92,113.12 | [工程推断·非史料] |
| 3224 | ARCH09.WEST.BACK.C14.B10 | 30 | 59.71,102.08 | [工程推断·非史料] |
| 3225 | ARCH09.WEST.SPANDREL.C14.B00 | 25 | 78.60,93.90 | [工程推断·非史料] |
| 3226 | ARCH09.WEST.SPANDREL.C14.B01 | 20 | 50.20,191.32 | [工程推断·非史料] |
| 3227 | ARCH09.WEST.SPANDREL.C14.B02 | 25 | 157.19,93.90 | [工程推断·非史料] |
| 3228 | ARCH09.WEST.SPANDREL.C14.B03 | 21 | 50.19,0.00 | [工程推断·非史料] |
| 3229 | ARCH09.WEST.SPANDREL.C14.B04 | 25 | 104.77,117.38 | [工程推断·非史料] |
| 3230 | ARCH09.WEST.SPANDREL.C14.B05 | 21 | 100.39,0.00 | [工程推断·非史料] |
| 3231 | ARCH09.WEST.SPANDREL.C14.B06 | 25 | 52.39,117.38 | [工程推断·非史料] |
| 3232 | ARCH09.WEST.SPANDREL.C14.B07 | 20 | 50.19,204.34 | [工程推断·非史料] |
| 3233 | ARCH09.WEST.SPANDREL.C14.B08 | 25 | 0.00,117.38 | [工程推断·非史料] |
| 3234 | ARCH09.WEST.SPANDREL.C14.B09 | 20 | 100.39,191.32 | [工程推断·非史料] |
| 3235 | ARCH09.WEST.SPANDREL.C14.B10 | 25 | 52.41,93.90 | [工程推断·非史料] |
| 3236 | ARCH09.EAST.CORE.C15.B00 | 15 | 0.00,138.05 | [工程推断·非史料] |
| 3237 | ARCH09.EAST.CORE.C15.B01 | 15 | 0.00,67.51 | [工程推断·非史料] |
| 3238 | ARCH09.EAST.CORE.C15.B02 | 16 | 0.00,0.00 | [工程推断·非史料] |
| 3239 | ARCH09.EAST.BACK.C15.B00 | 27 | 151.68,70.55 | [工程推断·非史料] |
| 3240 | ARCH09.EAST.BACK.C15.B04 | 25 | 0.00,48.40 | [工程推断·非史料] |
| 3241 | ARCH09.EAST.BACK.C15.B05 | 26 | 153.52,173.22 | [工程推断·非史料] |
| 3242 | ARCH09.EAST.BACK.C15.B08 | 29 | 66.06,42.43 | [工程推断·非史料] |
| 3243 | ARCH09.EAST.BACK.C15.B09 | 30 | 38.12,128.12 | [工程推断·非史料] |
| 3244 | ARCH09.EAST.BACK.C15.B10 | 28 | 23.16,107.81 | [工程推断·非史料] |
| 3245 | ARCH09.EAST.SPANDREL.C15.B00 | 20 | 50.26,93.82 | [工程推断·非史料] |
| 3246 | ARCH09.EAST.SPANDREL.C15.B04 | 20 | 0.00,56.08 | [工程推断·非史料] |
| 3247 | ARCH09.EAST.SPANDREL.C15.B05 | 25 | 132.54,0.00 | [工程推断·非史料] |
| 3248 | ARCH09.EAST.SPANDREL.C15.B08 | 20 | 100.68,78.42 | [工程推断·非史料] |
| 3249 | ARCH09.EAST.SPANDREL.C15.B09 | 25 | 131.61,25.54 | [工程推断·非史料] |
| 3250 | ARCH09.EAST.SPANDREL.C15.B10 | 20 | 100.51,93.82 | [工程推断·非史料] |
| 3251 | ARCH09.WEST.BACK.C15.B00 | 27 | 176.93,70.55 | [工程推断·非史料] |
| 3252 | ARCH09.WEST.BACK.C15.B04 | 25 | 184.18,25.54 | [工程推断·非史料] |
| 3253 | ARCH09.WEST.BACK.C15.B05 | 26 | 179.06,173.22 | [工程推断·非史料] |
| 3254 | ARCH09.WEST.BACK.C15.B08 | 29 | 87.90,42.43 | [工程推断·非史料] |
| 3255 | ARCH09.WEST.BACK.C15.B09 | 30 | 57.07,128.12 | [工程推断·非史料] |
| 3256 | ARCH09.WEST.BACK.C15.B10 | 28 | 46.26,107.81 | [工程推断·非史料] |
| 3257 | ARCH09.WEST.SPANDREL.C15.B00 | 20 | 0.00,93.82 | [工程推断·非史料] |
| 3258 | ARCH09.WEST.SPANDREL.C15.B04 | 20 | 50.36,56.08 | [工程推断·非史料] |
| 3259 | ARCH09.WEST.SPANDREL.C15.B05 | 25 | 158.90,0.00 | [工程推断·非史料] |
| 3260 | ARCH09.WEST.SPANDREL.C15.B08 | 20 | 150.98,78.42 | [工程推断·非史料] |
| 3261 | ARCH09.WEST.SPANDREL.C15.B09 | 25 | 157.89,25.54 | [工程推断·非史料] |
| 3262 | ARCH09.WEST.SPANDREL.C15.B10 | 20 | 150.76,93.82 | [工程推断·非史料] |
| 3263 | ARCH09.EAST.BACK.C15.B01 | 28 | 22.91,144.52 | [工程推断·非史料] |
| 3264 | ARCH09.EAST.BACK.C15.B02 | 25 | 182.73,139.40 | [工程推断·非史料] |
| 3265 | ARCH09.EAST.BACK.C15.B03 | 27 | 147.61,153.56 | [工程推断·非史料] |
| 3266 | ARCH09.EAST.BACK.C15.B06 | 28 | 0.00,195.22 | [工程推断·非史料] |
| 3267 | ARCH09.EAST.BACK.C15.B07 | 25 | 130.57,139.40 | [工程推断·非史料] |
| 3268 | ARCH09.EAST.SPANDREL.C15.B01 | 25 | 79.00,25.54 | [工程推断·非史料] |
| 3269 | ARCH09.EAST.SPANDREL.C15.B02 | 20 | 0.00,78.42 | [工程推断·非史料] |
| 3270 | ARCH09.EAST.SPANDREL.C15.B03 | 25 | 185.26,0.00 | [工程推断·非史料] |
| 3271 | ARCH09.EAST.SPANDREL.C15.B06 | 20 | 151.06,56.08 | [工程推断·非史料] |
| 3272 | ARCH09.EAST.SPANDREL.C15.B07 | 25 | 26.35,25.54 | [工程推断·非史料] |
| 3273 | ARCH09.WEST.BACK.C15.B01 | 28 | 45.77,144.52 | [工程推断·非史料] |
| 3274 | ARCH09.WEST.BACK.C15.B02 | 25 | 0.00,155.14 | [工程推断·非史料] |
| 3275 | ARCH09.WEST.BACK.C15.B03 | 27 | 172.04,153.56 | [工程推断·非史料] |
| 3276 | ARCH09.WEST.BACK.C15.B06 | 28 | 22.34,195.22 | [工程推断·非史料] |
| 3277 | ARCH09.WEST.BACK.C15.B07 | 25 | 156.65,139.40 | [工程推断·非史料] |
| 3278 | ARCH09.WEST.SPANDREL.C15.B01 | 25 | 105.30,25.54 | [工程推断·非史料] |
| 3279 | ARCH09.WEST.SPANDREL.C15.B02 | 20 | 50.34,78.42 | [工程推断·非史料] |
| 3280 | ARCH09.WEST.SPANDREL.C15.B03 | 25 | 0.00,25.54 | [工程推断·非史料] |
| 3281 | ARCH09.WEST.SPANDREL.C15.B06 | 20 | 100.72,56.08 | [工程推断·非史料] |
| 3282 | ARCH09.WEST.SPANDREL.C15.B07 | 25 | 52.67,25.54 | [工程推断·非史料] |

### S400 ARCH10.FILL (events 3283-3500)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 3318 | ARCH10.EAST.BACK.C09.B00 | 24 | 80.97,127.82 | [工程推断·非史料] |
| 3319 | ARCH10.EAST.BACK.C09.B06 | 28 | 0.00,0.00 | [工程推断·非史料] |
| 3320 | ARCH10.EAST.SPANDREL.C09.B00 | 19 | 102.82,48.46 | [工程推断·非史料] |
| 3321 | ARCH10.EAST.SPANDREL.C09.B06 | 19 | 102.93,0.00 | [工程推断·非史料] |
| 3322 | ARCH10.WEST.BACK.C09.B00 | 24 | 107.94,127.82 | [工程推断·非史料] |
| 3323 | ARCH10.WEST.BACK.C09.B06 | 28 | 24.30,0.00 | [工程推断·非史料] |
| 3324 | ARCH10.WEST.SPANDREL.C09.B00 | 19 | 154.24,48.46 | [工程推断·非史料] |
| 3325 | ARCH10.WEST.SPANDREL.C09.B06 | 19 | 154.40,0.00 | [工程推断·非史料] |
| 3326 | ARCH10.EAST.BACK.C10.B00 | 28 | 92.41,107.81 | [工程推断·非史料] |
| 3327 | ARCH10.EAST.BACK.C10.B01 | 29 | 146.05,140.45 | [工程推断·非史料] |
| 3328 | ARCH10.EAST.BACK.C10.B02 | 30 | 60.07,83.76 | [工程推断·非史料] |
| 3331 | ARCH10.EAST.BACK.C10.B08 | 28 | 0.00,128.78 | [工程推断·非史料] |
| 3332 | ARCH10.EAST.BACK.C10.B09 | 29 | 107.75,63.17 | [工程推断·非史料] |
| 3333 | ARCH10.EAST.SPANDREL.C10.B00 | 21 | 49.71,211.54 | [工程推断·非史料] |
| 3334 | ARCH10.EAST.SPANDREL.C10.B01 | 26 | 154.33,119.18 | [工程推断·非史料] |
| 3335 | ARCH10.EAST.SPANDREL.C10.B02 | 21 | 99.42,193.22 | [工程推断·非史料] |
| 3336 | ARCH10.EAST.SPANDREL.C10.B08 | 21 | 99.47,183.52 | [工程推断·非史料] |
| 3337 | ARCH10.EAST.SPANDREL.C10.B09 | 26 | 154.50,94.78 | [工程推断·非史料] |
| 3338 | ARCH10.WEST.BACK.C10.B00 | 28 | 138.52,107.81 | [工程推断·非史料] |
| 3339 | ARCH10.WEST.BACK.C10.B01 | 29 | 166.85,140.45 | [工程推断·非史料] |
| 3340 | ARCH10.WEST.BACK.C10.B02 | 30 | 80.06,83.76 | [工程推断·非史料] |
| 3343 | ARCH10.WEST.BACK.C10.B08 | 28 | 23.05,128.78 | [工程推断·非史料] |
| 3344 | ARCH10.WEST.BACK.C10.B09 | 29 | 129.28,63.17 | [工程推断·非史料] |
| 3345 | ARCH10.WEST.SPANDREL.C10.B00 | 21 | 149.12,211.54 | [工程推断·非史料] |
| 3346 | ARCH10.WEST.SPANDREL.C10.B01 | 26 | 180.04,119.18 | [工程推断·非史料] |
| 3347 | ARCH10.WEST.SPANDREL.C10.B02 | 21 | 149.12,193.22 | [工程推断·非史料] |
| 3348 | ARCH10.WEST.SPANDREL.C10.B08 | 21 | 149.20,183.52 | [工程推断·非史料] |
| 3349 | ARCH10.WEST.SPANDREL.C10.B09 | 26 | 180.23,94.78 | [工程推断·非史料] |
| 3350 | ARCH10.EAST.CORE.C13.B00 | 6 | 0.00,0.00 | [工程推断·非史料] |
| 3352 | ARCH10.EAST.CORE.C13.B02 | 6 | 0.00,67.51 | [工程推断·非史料] |
| 3353 | ARCH10.EAST.BACK.C11.B00 | 23 | 60.80,128.18 | [工程推断·非史料] |
| 3354 | ARCH10.EAST.BACK.C11.B04 | 29 | 0.00,83.91 | [工程推断·非史料] |
| 3355 | ARCH10.EAST.BACK.C11.B05 | 28 | 44.68,195.22 | [工程推断·非史料] |
| 3356 | ARCH10.EAST.SPANDREL.C11.B00 | 23 | 30.40,128.18 | [工程推断·非史料] |
| 3357 | ARCH10.EAST.SPANDREL.C11.B04 | 26 | 25.73,119.18 | [工程推断·非史料] |
| 3358 | ARCH10.EAST.SPANDREL.C11.B05 | 21 | 149.20,161.18 | [工程推断·非史料] |
| 3359 | ARCH10.WEST.BACK.C11.B00 | 23 | 121.60,128.18 | [工程推断·非史料] |
| 3360 | ARCH10.WEST.BACK.C11.B04 | 29 | 172.23,63.17 | [工程推断·非史料] |
| 3361 | ARCH10.WEST.BACK.C11.B05 | 28 | 67.02,195.22 | [工程推断·非史料] |
| 3362 | ARCH10.WEST.SPANDREL.C11.B00 | 23 | 91.20,128.18 | [工程推断·非史料] |
| 3363 | ARCH10.WEST.SPANDREL.C11.B04 | 26 | 77.19,119.18 | [工程推断·非史料] |
| 3364 | ARCH10.WEST.SPANDREL.C11.B05 | 21 | 49.73,161.18 | [工程推断·非史料] |
| 3365 | ARCH10.EAST.BACK.C12.B00 | 23 | 0.00,102.48 | [工程推断·非史料] |
| 3366 | ARCH10.EAST.BACK.C12.B01 | 29 | 189.11,122.55 | [工程推断·非史料] |
| 3368 | ARCH10.EAST.BACK.C12.B05 | 30 | 77.69,118.42 | [工程推断·非史料] |
| 3369 | ARCH10.EAST.BACK.C12.B06 | 23 | 138.00,51.81 | [工程推断·非史料] |
| 3370 | ARCH10.EAST.SPANDREL.C12.B00 | 23 | 166.26,77.15 | [工程推断·非史料] |
| 3371 | ARCH10.EAST.SPANDREL.C12.B01 | 22 | 49.33,159.04 | [工程推断·非史料] |
| 3373 | ARCH10.EAST.SPANDREL.C12.B05 | 22 | 98.68,134.74 | [工程推断·非史料] |
| 3374 | ARCH10.EAST.SPANDREL.C12.B06 | 23 | 103.50,51.81 | [工程推断·非史料] |
| 3375 | ARCH10.WEST.BACK.C12.B00 | 23 | 65.88,102.48 | [工程推断·非史料] |
| 3376 | ARCH10.WEST.BACK.C12.B01 | 29 | 0.00,140.45 | [工程推断·非史料] |
| 3378 | ARCH10.WEST.BACK.C12.B05 | 30 | 39.05,118.42 | [工程推断·非史料] |
| 3379 | ARCH10.WEST.BACK.C12.B06 | 23 | 0.00,77.15 | [工程推断·非史料] |
| 3380 | ARCH10.WEST.SPANDREL.C12.B00 | 23 | 32.94,102.48 | [工程推断·非史料] |
| 3381 | ARCH10.WEST.SPANDREL.C12.B01 | 22 | 147.98,159.04 | [工程推断·非史料] |
| 3382 | ARCH10.WEST.SPANDREL.C12.B05 | 22 | 148.02,134.74 | [工程推断·非史料] |
| 3383 | ARCH10.WEST.SPANDREL.C12.B06 | 23 | 172.50,51.81 | [工程推断·非史料] |
| 3384 | ARCH10.EAST.CORE.C14.B00 | 10 | 0.00,141.07 | [工程推断·非史料] |
| 3385 | ARCH10.EAST.CORE.C14.B02 | 12 | 0.00,0.00 | [工程推断·非史料] |
| 3386 | ARCH10.EAST.BACK.C13.B00 | 30 | 0.00,102.08 | [工程推断·非史料] |
| 3387 | ARCH10.EAST.BACK.C13.B01 | 23 | 117.92,180.60 | [工程推断·非史料] |
| 3388 | ARCH10.EAST.BACK.C13.B05 | 29 | 192.08,83.91 | [工程推断·非史料] |
| 3389 | ARCH10.EAST.BACK.C13.B06 | 26 | 0.00,152.18 | [工程推断·非史料] |
| 3390 | ARCH10.EAST.BACK.C13.B07 | 27 | 0.00,70.55 | [工程推断·非史料] |
| 3391 | ARCH10.EAST.BACK.C13.B08 | 26 | 155.00,25.79 | [工程推断·非史料] |
| 3392 | ARCH10.EAST.SPANDREL.C13.B00 | 20 | 152.12,42.44 | [工程推断·非史料] |
| 3393 | ARCH10.EAST.SPANDREL.C13.B01 | 23 | 88.44,180.60 | [工程推断·非史料] |
| 3394 | ARCH10.EAST.SPANDREL.C13.B05 | 24 | 81.43,105.69 | [工程推断·非史料] |
| 3395 | ARCH10.EAST.SPANDREL.C13.B06 | 19 | 0.00,202.64 | [工程推断·非史料] |
| 3396 | ARCH10.EAST.SPANDREL.C13.B07 | 24 | 188.17,174.17 | [工程推断·非史料] |
| 3397 | ARCH10.EAST.SPANDREL.C13.B08 | 19 | 0.00,186.90 | [工程推断·非史料] |
| 3398 | ARCH10.WEST.BACK.C13.B00 | 30 | 19.91,102.08 | [工程推断·非史料] |
| 3399 | ARCH10.WEST.BACK.C13.B01 | 23 | 176.88,180.60 | [工程推断·非史料] |
| 3400 | ARCH10.WEST.BACK.C13.B05 | 29 | 0.00,104.65 | [工程推断·非史料] |
| 3401 | ARCH10.WEST.BACK.C13.B06 | 26 | 25.65,152.18 | [工程推断·非史料] |
| 3402 | ARCH10.WEST.BACK.C13.B07 | 27 | 25.30,70.55 | [工程推断·非史料] |
| 3403 | ARCH10.WEST.BACK.C13.B08 | 26 | 180.82,25.79 | [工程推断·非史料] |
| 3404 | ARCH10.WEST.SPANDREL.C13.B00 | 20 | 50.71,42.44 | [工程推断·非史料] |
| 3405 | ARCH10.WEST.SPANDREL.C13.B01 | 23 | 147.40,180.60 | [工程推断·非史料] |
| 3406 | ARCH10.WEST.SPANDREL.C13.B05 | 24 | 108.46,105.69 | [工程推断·非史料] |
| 3407 | ARCH10.WEST.SPANDREL.C13.B06 | 19 | 50.74,202.64 | [工程推断·非史料] |
| 3408 | ARCH10.WEST.SPANDREL.C13.B07 | 24 | 0.00,192.82 | [工程推断·非史料] |
| 3409 | ARCH10.WEST.SPANDREL.C13.B08 | 19 | 50.76,186.90 | [工程推断·非史料] |
| 3410 | ARCH10.EAST.BACK.C14.B00 | 25 | 183.23,117.38 | [工程推断·非史料] |
| 3411 | ARCH10.EAST.BACK.C14.B01 | 28 | 45.47,163.09 | [工程推断·非史料] |
| 3412 | ARCH10.EAST.BACK.C14.B02 | 28 | 165.33,65.67 | [工程推断·非史料] |
| 3413 | ARCH10.EAST.BACK.C14.B03 | 29 | 0.00,63.17 | [工程推断·非史料] |
| 3414 | ARCH10.EAST.BACK.C14.B04 | 30 | 91.55,146.28 | [工程推断·非史料] |
| 3415 | ARCH10.EAST.BACK.C14.B05 | 27 | 102.08,0.00 | [工程推断·非史料] |
| 3416 | ARCH10.EAST.BACK.C14.B06 | 28 | 91.98,128.78 | [工程推断·非史料] |
| 3417 | ARCH10.EAST.BACK.C14.B07 | 29 | 0.00,20.38 | [工程推断·非史料] |
| 3418 | ARCH10.EAST.BACK.C14.B08 | 29 | 176.51,20.38 | [工程推断·非史料] |
| 3419 | ARCH10.EAST.BACK.C14.B09 | 30 | 182.54,64.63 | [工程推断·非史料] |
| 3420 | ARCH10.EAST.BACK.C14.B10 | 30 | 139.96,83.76 | [工程推断·非史料] |
| 3421 | ARCH10.EAST.SPANDREL.C14.B00 | 25 | 106.03,0.00 | [工程推断·非史料] |
| 3422 | ARCH10.EAST.SPANDREL.C14.B01 | 20 | 100.41,180.88 | [工程推断·非史料] |
| 3423 | ARCH10.EAST.SPANDREL.C14.B02 | 25 | 0.00,93.90 | [工程推断·非史料] |
| 3424 | ARCH10.EAST.SPANDREL.C14.B03 | 20 | 50.21,160.14 | [工程推断·非史料] |
| 3425 | ARCH10.EAST.SPANDREL.C14.B04 | 25 | 78.67,70.42 | [工程推断·非史料] |
| 3426 | ARCH10.EAST.SPANDREL.C14.B05 | 20 | 100.45,134.62 | [工程推断·非史料] |
| 3427 | ARCH10.EAST.SPANDREL.C14.B06 | 25 | 157.47,48.40 | [工程推断·非史料] |
| 3428 | ARCH10.EAST.SPANDREL.C14.B07 | 20 | 100.47,124.24 | [工程推断·非史料] |
| 3429 | ARCH10.EAST.SPANDREL.C14.B08 | 25 | 78.76,48.40 | [工程推断·非史料] |
| 3430 | ARCH10.EAST.SPANDREL.C14.B09 | 20 | 100.49,111.22 | [工程推断·非史料] |
| 3431 | ARCH10.EAST.SPANDREL.C14.B10 | 24 | 106.40,192.82 | [工程推断·非史料] |
| 3432 | ARCH10.WEST.BACK.C14.B00 | 25 | 0.00,139.40 | [工程推断·非史料] |
| 3433 | ARCH10.WEST.BACK.C14.B01 | 28 | 68.21,163.09 | [工程推断·非史料] |
| 3434 | ARCH10.WEST.BACK.C14.B02 | 28 | 188.81,65.67 | [工程推断·非史料] |
| 3435 | ARCH10.WEST.BACK.C14.B03 | 29 | 43.13,63.17 | [工程推断·非史料] |
| 3436 | ARCH10.WEST.BACK.C14.B04 | 30 | 109.80,146.28 | [工程推断·非史料] |
| 3437 | ARCH10.WEST.BACK.C14.B05 | 27 | 127.60,0.00 | [工程推断·非史料] |
| 3438 | ARCH10.WEST.BACK.C14.B06 | 28 | 114.92,128.78 | [工程推断·非史料] |
| 3439 | ARCH10.WEST.BACK.C14.B07 | 29 | 22.11,20.38 | [工程推断·非史料] |
| 3440 | ARCH10.WEST.BACK.C14.B08 | 29 | 0.00,42.43 | [工程推断·非史料] |
| 3441 | ARCH10.WEST.BACK.C14.B09 | 30 | 0.00,83.76 | [工程推断·非史料] |
| 3442 | ARCH10.WEST.BACK.C14.B10 | 30 | 159.92,83.76 | [工程推断·非史料] |
| 3443 | ARCH10.WEST.SPANDREL.C14.B00 | 25 | 53.03,0.00 | [工程推断·非史料] |
| 3444 | ARCH10.WEST.SPANDREL.C14.B01 | 20 | 150.62,180.88 | [工程推断·非史料] |
| 3445 | ARCH10.WEST.SPANDREL.C14.B02 | 25 | 157.31,70.42 | [工程推断·非史料] |
| 3446 | ARCH10.WEST.SPANDREL.C14.B03 | 20 | 150.64,160.14 | [工程推断·非史料] |
| 3447 | ARCH10.WEST.SPANDREL.C14.B04 | 25 | 104.89,70.42 | [工程推断·非史料] |
| 3448 | ARCH10.WEST.SPANDREL.C14.B05 | 20 | 150.68,134.62 | [工程推断·非史料] |
| 3449 | ARCH10.WEST.SPANDREL.C14.B06 | 25 | 0.00,70.42 | [工程推断·非史料] |
| 3450 | ARCH10.WEST.SPANDREL.C14.B07 | 20 | 150.70,124.24 | [工程推断·非史料] |
| 3451 | ARCH10.WEST.SPANDREL.C14.B08 | 25 | 105.00,48.40 | [工程推断·非史料] |
| 3452 | ARCH10.WEST.SPANDREL.C14.B09 | 20 | 150.74,111.22 | [工程推断·非史料] |
| 3453 | ARCH10.WEST.SPANDREL.C14.B10 | 24 | 53.30,192.82 | [工程推断·非史料] |
| 3454 | ARCH10.EAST.CORE.C15.B00 | 14 | 0.00,128.29 | [工程推断·非史料] |
| 3455 | ARCH10.EAST.CORE.C15.B01 | 16 | 0.00,138.05 | [工程推断·非史料] |
| 3456 | ARCH10.EAST.CORE.C15.B02 | 17 | 0.00,128.89 | [工程推断·非史料] |
| 3457 | ARCH10.EAST.BACK.C15.B05 | 26 | 129.20,0.00 | [工程推断·非史料] |
| 3458 | ARCH10.EAST.BACK.C15.B08 | 29 | 22.30,0.00 | [工程推断·非史料] |
| 3459 | ARCH10.EAST.BACK.C15.B10 | 28 | 113.62,163.09 | [工程推断·非史料] |
| 3460 | ARCH10.EAST.SPANDREL.C15.B05 | 26 | 103.36,0.00 | [工程推断·非史料] |
| 3461 | ARCH10.EAST.SPANDREL.C15.B08 | 22 | 98.72,126.64 | [工程推断·非史料] |
| 3462 | ARCH10.EAST.SPANDREL.C15.B10 | 22 | 49.16,178.04 | [工程推断·非史料] |
| 3463 | ARCH10.WEST.BACK.C15.B05 | 26 | 180.88,0.00 | [工程推断·非史料] |
| 3464 | ARCH10.WEST.BACK.C15.B08 | 29 | 44.60,0.00 | [工程推断·非史料] |
| 3465 | ARCH10.WEST.BACK.C15.B10 | 28 | 158.98,163.09 | [工程推断·非史料] |
| 3466 | ARCH10.WEST.SPANDREL.C15.B05 | 26 | 155.04,0.00 | [工程推断·非史料] |
| 3467 | ARCH10.WEST.SPANDREL.C15.B08 | 22 | 148.08,126.64 | [工程推断·非史料] |
| 3468 | ARCH10.WEST.SPANDREL.C15.B10 | 22 | 147.47,178.04 | [工程推断·非史料] |
| 3469 | ARCH10.EAST.BACK.C15.B00 | 29 | 63.21,122.55 | [工程推断·非史料] |
| 3470 | ARCH10.EAST.BACK.C15.B01 | 28 | 186.49,86.83 | [工程推断·非史料] |
| 3471 | ARCH10.EAST.BACK.C15.B02 | 28 | 24.22,23.63 | [工程推断·非史料] |
| 3472 | ARCH10.EAST.BACK.C15.B03 | 27 | 49.68,132.52 | [工程推断·非史料] |
| 3473 | ARCH10.EAST.BACK.C15.B04 | 28 | 24.08,43.18 | [工程推断·非史料] |
| 3474 | ARCH10.EAST.BACK.C15.B06 | 28 | 113.25,177.21 | [工程推断·非史料] |
| 3475 | ARCH10.EAST.BACK.C15.B09 | 29 | 42.81,83.91 | [工程推断·非史料] |
| 3476 | ARCH10.EAST.SPANDREL.C15.B00 | 21 | 99.67,131.66 | [工程推断·非史料] |
| 3477 | ARCH10.EAST.SPANDREL.C15.B01 | 26 | 51.67,25.79 | [工程推断·非史料] |
| 3478 | ARCH10.EAST.SPANDREL.C15.B02 | 21 | 149.52,115.96 | [工程推断·非史料] |
| 3479 | ARCH10.EAST.SPANDREL.C15.B03 | 25 | 181.40,180.36 | [工程推断·非史料] |
| 3480 | ARCH10.EAST.SPANDREL.C15.B04 | 21 | 99.69,104.16 | [工程推断·非史料] |
| 3481 | ARCH10.EAST.SPANDREL.C15.B06 | 22 | 99.16,94.30 | [工程推断·非史料] |
| 3482 | ARCH10.EAST.SPANDREL.C15.B09 | 27 | 101.14,70.55 | [工程推断·非史料] |
| 3483 | ARCH10.WEST.BACK.C15.B00 | 29 | 84.23,122.55 | [工程推断·非史料] |
| 3484 | ARCH10.WEST.BACK.C15.B01 | 28 | 0.00,107.81 | [工程推断·非史料] |
| 3485 | ARCH10.WEST.BACK.C15.B02 | 28 | 48.45,23.63 | [工程推断·非史料] |
| 3486 | ARCH10.WEST.BACK.C15.B03 | 27 | 74.52,132.52 | [工程推断·非史料] |
| 3487 | ARCH10.WEST.BACK.C15.B04 | 28 | 193.40,23.63 | [工程推断·非史料] |
| 3488 | ARCH10.WEST.BACK.C15.B06 | 28 | 135.89,177.21 | [工程推断·非史料] |
| 3489 | ARCH10.WEST.BACK.C15.B09 | 29 | 85.59,83.91 | [工程推断·非史料] |
| 3490 | ARCH10.WEST.SPANDREL.C15.B00 | 21 | 149.50,131.66 | [工程推断·非史料] |
| 3491 | ARCH10.WEST.SPANDREL.C15.B01 | 26 | 77.51,25.79 | [工程推断·非史料] |
| 3492 | ARCH10.WEST.SPANDREL.C15.B02 | 21 | 49.84,115.96 | [工程推断·非史料] |
| 3493 | ARCH10.WEST.SPANDREL.C15.B03 | 25 | 0.00,204.62 | [工程推断·非史料] |
| 3494 | ARCH10.WEST.SPANDREL.C15.B04 | 21 | 149.54,104.16 | [工程推断·非史料] |
| 3495 | ARCH10.WEST.SPANDREL.C15.B06 | 22 | 148.74,94.30 | [工程推断·非史料] |
| 3496 | ARCH10.WEST.SPANDREL.C15.B09 | 27 | 126.41,70.55 | [工程推断·非史料] |
| 3497 | ARCH10.EAST.BACK.C15.B07 | 28 | 114.32,144.52 | [工程推断·非史料] |
| 3498 | ARCH10.EAST.SPANDREL.C15.B07 | 27 | 0.00,24.14 | [工程推断·非史料] |
| 3499 | ARCH10.WEST.BACK.C15.B07 | 28 | 137.17,144.52 | [工程推断·非史料] |
| 3500 | ARCH10.WEST.SPANDREL.C15.B07 | 27 | 25.44,24.14 | [工程推断·非史料] |

### S401 ARCH11.FILL (events 3501-3693)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 3537 | ARCH11.EAST.BACK.C08.B00 | 24 | 185.99,192.82 | [工程推断·非史料] |
| 3538 | ARCH11.EAST.BACK.C08.B05 | 28 | 0.00,177.21 | [工程推断·非史料] |
| 3539 | ARCH11.EAST.SPANDREL.C08.B00 | 18 | 52.94,196.40 | [工程推断·非史料] |
| 3540 | ARCH11.EAST.SPANDREL.C08.B05 | 24 | 58.17,0.00 | [工程推断·非史料] |
| 3541 | ARCH11.WEST.BACK.C08.B00 | 25 | 0.00,0.00 | [工程推断·非史料] |
| 3542 | ARCH11.WEST.BACK.C08.B05 | 28 | 45.31,177.21 | [工程推断·非史料] |
| 3543 | ARCH11.WEST.SPANDREL.C08.B00 | 18 | 105.87,196.40 | [工程推断·非史料] |
| 3544 | ARCH11.WEST.SPANDREL.C08.B05 | 24 | 87.26,0.00 | [工程推断·非史料] |
| 3548 | ARCH11.EAST.BACK.C09.B00 | 29 | 175.14,42.43 | [工程推断·非史料] |
| 3549 | ARCH11.EAST.BACK.C09.B01 | 27 | 194.86,195.93 | [工程推断·非史料] |
| 3551 | ARCH11.EAST.BACK.C09.B06 | 28 | 120.99,23.63 | [工程推断·非史料] |
| 3552 | ARCH11.EAST.SPANDREL.C09.B00 | 19 | 51.35,82.74 | [工程推断·非史料] |
| 3553 | ARCH11.EAST.SPANDREL.C09.B01 | 24 | 138.64,53.99 | [工程推断·非史料] |
| 3554 | ARCH11.EAST.SPANDREL.C09.B06 | 19 | 102.91,24.30 | [工程推断·非史料] |
| 3555 | ARCH11.WEST.BACK.C09.B00 | 29 | 131.54,42.43 | [工程推断·非史料] |
| 3556 | ARCH11.WEST.BACK.C09.B01 | 27 | 146.21,195.93 | [工程推断·非史料] |
| 3558 | ARCH11.WEST.BACK.C09.B06 | 28 | 145.15,23.63 | [工程推断·非史料] |
| 3559 | ARCH11.WEST.SPANDREL.C09.B00 | 19 | 154.15,63.34 | [工程推断·非史料] |
| 3560 | ARCH11.WEST.SPANDREL.C09.B01 | 24 | 0.00,79.69 | [工程推断·非史料] |
| 3561 | ARCH11.WEST.SPANDREL.C09.B06 | 19 | 154.37,24.30 | [工程推断·非史料] |
| 3562 | ARCH11.EAST.CORE.C13.B00 | 7 | 0.00,16.47 | [工程推断·非史料] |
| 3564 | ARCH11.EAST.CORE.C13.B02 | 9 | 0.00,0.00 | [工程推断·非史料] |
| 3565 | ARCH11.EAST.BACK.C10.B00 | 27 | 126.05,88.45 | [工程推断·非史料] |
| 3566 | ARCH11.EAST.BACK.C10.B01 | 30 | 20.51,46.31 | [工程推断·非史料] |
| 3567 | ARCH11.EAST.BACK.C10.B02 | 28 | 116.87,86.83 | [工程推断·非史料] |
| 3569 | ARCH11.EAST.BACK.C10.B06 | 30 | 169.40,128.12 | [工程推断·非史料] |
| 3570 | ARCH11.EAST.BACK.C10.B07 | 30 | 102.50,46.31 | [工程推断·非史料] |
| 3571 | ARCH11.EAST.BACK.C10.B08 | 30 | 184.26,46.31 | [工程推断·非史料] |
| 3572 | ARCH11.EAST.SPANDREL.C10.B00 | 27 | 25.33,52.65 | [工程推断·非史料] |
| 3573 | ARCH11.EAST.SPANDREL.C10.B01 | 22 | 98.66,140.72 | [工程推断·非史料] |
| 3574 | ARCH11.EAST.SPANDREL.C10.B02 | 27 | 76.06,38.40 | [工程推断·非史料] |
| 3575 | ARCH11.EAST.SPANDREL.C10.B06 | 27 | 177.73,24.14 | [工程推断·非史料] |
| 3576 | ARCH11.EAST.SPANDREL.C10.B07 | 22 | 148.11,116.94 | [工程推断·非史料] |
| 3577 | ARCH11.EAST.SPANDREL.C10.B08 | 27 | 126.99,24.14 | [工程推断·非史料] |
| 3578 | ARCH11.WEST.BACK.C10.B00 | 27 | 176.40,88.45 | [工程推断·非史料] |
| 3579 | ARCH11.WEST.BACK.C10.B01 | 30 | 41.02,46.31 | [工程推断·非史料] |
| 3580 | ARCH11.WEST.BACK.C10.B02 | 28 | 70.26,86.83 | [工程推断·非史料] |
| 3582 | ARCH11.WEST.BACK.C10.B06 | 30 | 0.00,146.28 | [工程推断·非史料] |
| 3583 | ARCH11.WEST.BACK.C10.B07 | 30 | 122.99,46.31 | [工程推断·非史料] |
| 3584 | ARCH11.WEST.BACK.C10.B08 | 30 | 0.00,64.63 | [工程推断·非史料] |
| 3585 | ARCH11.WEST.SPANDREL.C10.B00 | 27 | 177.39,38.40 | [工程推断·非史料] |
| 3586 | ARCH11.WEST.SPANDREL.C10.B01 | 22 | 147.99,140.72 | [工程推断·非史料] |
| 3587 | ARCH11.WEST.SPANDREL.C10.B02 | 27 | 126.73,38.40 | [工程推断·非史料] |
| 3588 | ARCH11.WEST.SPANDREL.C10.B06 | 27 | 25.37,38.40 | [工程推断·非史料] |
| 3589 | ARCH11.WEST.SPANDREL.C10.B07 | 22 | 49.37,116.94 | [工程推断·非史料] |
| 3590 | ARCH11.WEST.SPANDREL.C10.B08 | 27 | 76.25,24.14 | [工程推断·非史料] |
| 3591 | ARCH11.EAST.BACK.C11.B00 | 27 | 146.41,174.60 | [工程推断·非史料] |
| 3592 | ARCH11.EAST.BACK.C11.B04 | 26 | 128.22,152.18 | [工程推断·非史料] |
| 3593 | ARCH11.EAST.BACK.C11.B05 | 30 | 119.13,102.08 | [工程推断·非史料] |
| 3594 | ARCH11.EAST.SPANDREL.C11.B00 | 26 | 25.76,94.78 | [工程推断·非史料] |
| 3595 | ARCH11.EAST.SPANDREL.C11.B04 | 26 | 51.60,74.40 | [工程推断·非史料] |
| 3596 | ARCH11.EAST.SPANDREL.C11.B05 | 21 | 99.62,144.84 | [工程推断·非史料] |
| 3597 | ARCH11.WEST.BACK.C11.B00 | 27 | 170.81,174.60 | [工程推断·非史料] |
| 3598 | ARCH11.WEST.BACK.C11.B04 | 26 | 76.95,152.18 | [工程推断·非史料] |
| 3599 | ARCH11.WEST.BACK.C11.B05 | 30 | 138.90,102.08 | [工程推断·非史料] |
| 3600 | ARCH11.WEST.SPANDREL.C11.B00 | 26 | 77.27,94.78 | [工程推断·非史料] |
| 3601 | ARCH11.WEST.SPANDREL.C11.B04 | 26 | 77.41,74.40 | [工程推断·非史料] |
| 3602 | ARCH11.WEST.SPANDREL.C11.B05 | 21 | 149.43,144.84 | [工程推断·非史料] |
| 3603 | ARCH11.EAST.BACK.C12.B00 | 24 | 161.66,148.20 | [工程推断·非史料] |
| 3604 | ARCH11.EAST.BACK.C12.B01 | 29 | 63.76,104.65 | [工程推断·非史料] |
| 3606 | ARCH11.EAST.BACK.C12.B05 | 27 | 24.38,195.93 | [工程推断·非史料] |
| 3607 | ARCH11.EAST.BACK.C12.B06 | 27 | 50.44,88.45 | [工程推断·非史料] |
| 3608 | ARCH11.EAST.SPANDREL.C12.B00 | 24 | 134.72,148.20 | [工程推断·非史料] |
| 3609 | ARCH11.EAST.SPANDREL.C12.B01 | 21 | 99.95,81.00 | [工程推断·非史料] |
| 3611 | ARCH11.EAST.SPANDREL.C12.B05 | 21 | 50.01,71.74 | [工程推断·非史料] |
| 3612 | ARCH11.EAST.SPANDREL.C12.B06 | 25 | 78.10,155.14 | [工程推断·非史料] |
| 3613 | ARCH11.WEST.BACK.C12.B00 | 24 | 0.00,174.17 | [工程推断·非史料] |
| 3614 | ARCH11.WEST.BACK.C12.B01 | 29 | 85.00,104.65 | [工程推断·非史料] |
| 3616 | ARCH11.WEST.BACK.C12.B05 | 27 | 48.76,195.93 | [工程推断·非史料] |
| 3617 | ARCH11.WEST.BACK.C12.B06 | 27 | 75.66,88.45 | [工程推断·非史料] |
| 3618 | ARCH11.WEST.SPANDREL.C12.B00 | 24 | 188.60,148.20 | [工程推断·非史料] |
| 3619 | ARCH11.WEST.SPANDREL.C12.B01 | 21 | 149.92,81.00 | [工程推断·非史料] |
| 3620 | ARCH11.WEST.SPANDREL.C12.B05 | 21 | 150.04,71.74 | [工程推断·非史料] |
| 3621 | ARCH11.WEST.SPANDREL.C12.B06 | 25 | 104.13,155.14 | [工程推断·非史料] |
| 3622 | ARCH11.EAST.CORE.C14.B00 | 12 | 0.00,135.03 | [工程推断·非史料] |
| 3623 | ARCH11.EAST.CORE.C14.B02 | 14 | 0.00,0.00 | [工程推断·非史料] |
| 3624 | ARCH11.EAST.BACK.C13.B00 | 28 | 94.72,65.67 | [工程推断·非史料] |
| 3625 | ARCH11.EAST.BACK.C13.B01 | 23 | 0.00,153.89 | [工程推断·非史料] |
| 3626 | ARCH11.EAST.BACK.C13.B02 | 30 | 61.15,64.63 | [工程推断·非史料] |
| 3627 | ARCH11.EAST.BACK.C13.B03 | 30 | 144.33,25.95 | [工程推断·非史料] |
| 3628 | ARCH11.EAST.BACK.C13.B04 | 24 | 112.24,26.99 | [工程推断·非史料] |
| 3629 | ARCH11.EAST.BACK.C13.B05 | 28 | 0.00,144.52 | [工程推断·非史料] |
| 3630 | ARCH11.EAST.BACK.C13.B06 | 29 | 190.92,104.65 | [工程推断·非史料] |
| 3631 | ARCH11.EAST.BACK.C13.B07 | 27 | 75.96,52.65 | [工程推断·非史料] |
| 3632 | ARCH11.EAST.SPANDREL.C13.B00 | 24 | 53.87,174.17 | [工程推断·非史料] |
| 3633 | ARCH11.EAST.SPANDREL.C13.B01 | 19 | 0.00,157.42 | [工程推断·非史料] |
| 3634 | ARCH11.EAST.SPANDREL.C13.B02 | 24 | 188.83,127.82 | [工程推断·非史料] |
| 3635 | ARCH11.EAST.SPANDREL.C13.B03 | 19 | 50.97,127.94 | [工程推断·非史料] |
| 3636 | ARCH11.EAST.SPANDREL.C13.B04 | 24 | 84.18,26.99 | [工程推断·非史料] |
| 3637 | ARCH11.EAST.SPANDREL.C13.B05 | 19 | 153.68,91.62 | [工程推断·非史料] |
| 3638 | ARCH11.EAST.SPANDREL.C13.B06 | 24 | 162.53,105.69 | [工程推断·非史料] |
| 3639 | ARCH11.EAST.SPANDREL.C13.B07 | 19 | 154.04,82.74 | [工程推断·非史料] |
| 3640 | ARCH11.WEST.BACK.C13.B00 | 28 | 47.42,65.67 | [工程推断·非史料] |
| 3641 | ARCH11.WEST.BACK.C13.B01 | 23 | 29.48,153.89 | [工程推断·非史料] |
| 3642 | ARCH11.WEST.BACK.C13.B02 | 30 | 81.53,64.63 | [工程推断·非史料] |
| 3643 | ARCH11.WEST.BACK.C13.B03 | 30 | 164.91,25.95 | [工程推断·非史料] |
| 3644 | ARCH11.WEST.BACK.C13.B04 | 24 | 168.36,26.99 | [工程推断·非史料] |
| 3645 | ARCH11.WEST.BACK.C13.B05 | 28 | 160.78,128.78 | [工程推断·非史料] |
| 3646 | ARCH11.WEST.BACK.C13.B06 | 29 | 0.00,122.55 | [工程推断·非史料] |
| 3647 | ARCH11.WEST.BACK.C13.B07 | 27 | 126.58,52.65 | [工程推断·非史料] |
| 3648 | ARCH11.WEST.SPANDREL.C13.B00 | 24 | 107.74,174.17 | [工程推断·非史料] |
| 3649 | ARCH11.WEST.SPANDREL.C13.B01 | 19 | 50.94,157.42 | [工程推断·非史料] |
| 3650 | ARCH11.WEST.SPANDREL.C13.B02 | 24 | 0.00,148.20 | [工程推断·非史料] |
| 3651 | ARCH11.WEST.SPANDREL.C13.B03 | 19 | 153.00,107.36 | [工程推断·非史料] |
| 3652 | ARCH11.WEST.SPANDREL.C13.B04 | 24 | 140.30,26.99 | [工程推断·非史料] |
| 3653 | ARCH11.WEST.SPANDREL.C13.B05 | 19 | 51.01,107.36 | [工程推断·非史料] |
| 3654 | ARCH11.WEST.SPANDREL.C13.B06 | 24 | 0.00,127.82 | [工程推断·非史料] |
| 3655 | ARCH11.WEST.SPANDREL.C13.B07 | 19 | 51.34,91.62 | [工程推断·非史料] |
| 3656 | ARCH11.EAST.BACK.C14.B05 | 27 | 49.26,153.56 | [工程推断·非史料] |
| 3657 | ARCH11.EAST.BACK.C14.B07 | 28 | 134.00,195.22 | [工程推断·非史料] |
| 3658 | ARCH11.EAST.BACK.C14.B08 | 30 | 135.64,118.42 | [工程推断·非史料] |
| 3659 | ARCH11.EAST.SPANDREL.C14.B05 | 22 | 98.33,170.62 | [工程推断·非史料] |
| 3660 | ARCH11.EAST.SPANDREL.C14.B07 | 22 | 97.41,189.00 | [工程推断·非史料] |
| 3661 | ARCH11.EAST.SPANDREL.C14.B08 | 27 | 48.80,174.60 | [工程推断·非史料] |
| 3662 | ARCH11.WEST.BACK.C14.B05 | 27 | 73.85,153.56 | [工程推断·非史料] |
| 3663 | ARCH11.WEST.BACK.C14.B07 | 28 | 156.32,195.22 | [工程推断·非史料] |
| 3664 | ARCH11.WEST.BACK.C14.B08 | 30 | 154.93,118.42 | [工程推断·非史料] |
| 3665 | ARCH11.WEST.SPANDREL.C14.B05 | 22 | 147.50,170.62 | [工程推断·非史料] |
| 3666 | ARCH11.WEST.SPANDREL.C14.B07 | 22 | 146.11,189.00 | [工程推断·非史料] |
| 3667 | ARCH11.WEST.SPANDREL.C14.B08 | 27 | 73.20,174.60 | [工程推断·非史料] |
| 3668 | ARCH11.EAST.BACK.C14.B00 | 30 | 158.67,102.08 | [工程推断·非史料] |
| 3669 | ARCH11.EAST.BACK.C14.B01 | 28 | 143.39,43.18 | [工程推断·非史料] |
| 3670 | ARCH11.EAST.BACK.C14.B02 | 27 | 173.65,132.52 | [工程推断·非史料] |
| 3671 | ARCH11.EAST.BACK.C14.B03 | 29 | 20.92,140.45 | [工程推断·非史料] |
| 3672 | ARCH11.EAST.SPANDREL.C14.B00 | 26 | 102.36,173.22 | [工程推断·非史料] |
| 3673 | ARCH11.EAST.SPANDREL.C14.B01 | 22 | 99.18,70.52 | [工程推断·非史料] |
| 3674 | ARCH11.EAST.SPANDREL.C14.B02 | 26 | 0.00,173.22 | [工程推断·非史料] |
| 3675 | ARCH11.EAST.SPANDREL.C14.B03 | 22 | 148.81,53.62 | [工程推断·非史料] |
| 3676 | ARCH11.WEST.BACK.C14.B00 | 30 | 178.40,102.08 | [工程推断·非史料] |
| 3677 | ARCH11.WEST.BACK.C14.B01 | 28 | 167.17,43.18 | [工程推断·非史料] |
| 3678 | ARCH11.WEST.BACK.C14.B02 | 27 | 149.02,132.52 | [工程推断·非史料] |
| 3679 | ARCH11.WEST.BACK.C14.B03 | 29 | 62.70,140.45 | [工程推断·非史料] |
| 3680 | ARCH11.WEST.SPANDREL.C14.B00 | 26 | 127.94,173.22 | [工程推断·非史料] |
| 3681 | ARCH11.WEST.SPANDREL.C14.B01 | 22 | 148.76,70.52 | [工程推断·非史料] |
| 3682 | ARCH11.WEST.SPANDREL.C14.B02 | 26 | 25.60,173.22 | [工程推断·非史料] |
| 3683 | ARCH11.WEST.SPANDREL.C14.B03 | 22 | 49.60,53.62 | [工程推断·非史料] |
| 3684 | ARCH11.EAST.BACK.C14.B04 | 26 | 129.10,48.95 | [工程推断·非史料] |
| 3685 | ARCH11.EAST.BACK.C14.B06 | 30 | 61.93,25.95 | [工程推断·非史料] |
| 3686 | ARCH11.EAST.SPANDREL.C14.B04 | 26 | 103.28,48.95 | [工程推断·非史料] |
| 3687 | ARCH11.EAST.SPANDREL.C14.B06 | 27 | 100.03,113.12 | [工程推断·非史料] |
| 3688 | ARCH11.WEST.BACK.C14.B04 | 26 | 180.74,48.95 | [工程推断·非史料] |
| 3689 | ARCH11.WEST.BACK.C14.B06 | 30 | 82.55,25.95 | [工程推断·非史料] |
| 3690 | ARCH11.WEST.SPANDREL.C14.B04 | 26 | 154.92,48.95 | [工程推断·非史料] |
| 3691 | ARCH11.WEST.SPANDREL.C14.B06 | 27 | 125.04,113.12 | [工程推断·非史料] |
| 3692 | ARCH11.EAST.CORE.C15.B00 | 17 | 0.00,0.00 | [工程推断·非史料] |
| 3693 | ARCH11.EAST.CORE.C15.B01 | 18 | 0.00,131.96 | [工程推断·非史料] |

