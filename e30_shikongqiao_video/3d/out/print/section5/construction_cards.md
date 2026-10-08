# 中央五孔段 施工卡 (section5 · construction cards)

数据源: 3d/out/sequence.json (P2 交付: 408 stage/4118 事件) x 3d/out/print/section5/manifest.json (1123 打印单元/34 批)
对照账: 3d/out/ledger_full.json
生成命令: blender -b --python 3d/section_pack.py -- --assembly
回放: python3 3d/section_pack.py --assembly --cards-only (只出本卡+分号位表, 不渲染)
口径: 装配次序 = sequence 原序过滤的段单元事件子序列 (1123/1123 单元全覆盖, 恰一次, 不重排); 批次 = 220x220 打印床分批
口径: 每孔装配图 = out/print/section5/assembly/ARCHxx.png (assembly_ortho 模式, P1A 同款); 段总图 = 同目录 section_overview.png (墩位缺口/M5(a) 底座端槽示意, 图注 [设计选择]); 床位权威 = 分号位表 assembly/ARCHxx.csv

## 批次总表 (今日打印 — 每行=一床)

| batch | 孔 | 单元数 | 床位占用 mm | 分号位表 |
|---|---|---|---|---|
| 0 | ARCH09 | 1 | 167.6x167.6 | assembly/ARCH09.csv |
| 1 | ARCH08+ARCH09+ARCH10 | 5 | 214.9x217.0 | assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv |
| 2 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 14 | 212.7x208.6 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 3 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 12 | 191.5x218.9 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 4 | ARCH08+ARCH09+ARCH10 | 11 | 175.2x216.0 | assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv |
| 5 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 10 | 164.8x203.9 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 6 | ARCH07+ARCH09+ARCH10+ARCH11 | 6 | 156.7x176.5 | assembly/ARCH07.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 7 | ARCH08+ARCH09+ARCH10 | 3 | 154.1x205.6 | assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv |
| 8 | ARCH08+ARCH09+ARCH10 | 6 | 153.4x212.1 | assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv |
| 9 | ARCH07+ARCH09+ARCH10+ARCH11 | 6 | 151.5x206.9 | assembly/ARCH07.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 10 | ARCH07+ARCH08+ARCH10+ARCH11 | 8 | 149.3x203.8 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 11 | ARCH07+ARCH09 | 3 | 146.6x205.2 | assembly/ARCH07.csv+assembly/ARCH09.csv |
| 12 | ARCH08+ARCH09+ARCH10 | 3 | 144.0x205.6 | assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv |
| 13 | ARCH08+ARCH10 | 3 | 142.6x202.5 | assembly/ARCH08.csv+assembly/ARCH10.csv |
| 14 | ARCH07+ARCH08+ARCH11 | 3 | 141.4x195.8 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH11.csv |
| 15 | ARCH07+ARCH11 | 3 | 138.0x192.4 | assembly/ARCH07.csv+assembly/ARCH11.csv |
| 16 | ARCH07+ARCH08+ARCH10 | 3 | 135.8x199.2 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH10.csv |
| 17 | ARCH09 | 3 | 134.8x211.6 | assembly/ARCH09.csv |
| 18 | ARCH08+ARCH10+ARCH11 | 3 | 134.0x199.5 | assembly/ARCH08.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 19 | ARCH07+ARCH08+ARCH10 | 3 | 133.9x199.5 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH10.csv |
| 20 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 19 | 211.3x202.9 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 21 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 32 | 205.8x194.2 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 22 | ARCH08+ARCH09+ARCH10+ARCH11 | 41 | 203.2x211.3 | assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 23 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 48 | 200.9x215.1 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 24 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 42 | 199.4x215.5 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 25 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 57 | 214.4x218.0 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 26 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 54 | 212.8x210.3 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 27 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 79 | 219.5x219.8 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 28 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 80 | 210.1x210.7 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 29 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 88 | 206.7x219.9 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 30 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 100 | 219.5x205.9 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 31 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 99 | 213.6x210.4 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 32 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 160 | 218.5x217.1 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |
| 33 | ARCH07+ARCH08+ARCH09+ARCH10+ARCH11 | 115 | 219.4x164.4 | assembly/ARCH07.csv+assembly/ARCH08.csv+assembly/ARCH09.csv+assembly/ARCH10.csv+assembly/ARCH11.csv |

## 装配次序 (今日粘接 — sequence 子序列, 71 stage/1123 行; 行序=粘接序)

序声明: 本节每行均为装配次序断言 [工程推断·非史料](无工序史料锚, P2 关账口径; sequence 事件原序, 不重排)。

### S124 ARCH07.IMPOST.C02 (events 672-679)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 672 | ARCH07.EAST.IMPOST.C02.B01 | 32 | 20.70,138.78 | [工程推断·非史料] |
| 673 | ARCH07.EAST.IMPOST.C02.B02 | 32 | 186.30,208.26 | [工程推断·非史料] |
| 674 | ARCH07.EAST.IMPOST.C02.B03 | 32 | 144.90,147.58 | [工程推断·非史料] |
| 675 | ARCH07.EAST.IMPOST.C02.B04 | 32 | 165.60,147.58 | [工程推断·非史料] |
| 676 | ARCH07.WEST.IMPOST.C02.B01 | 32 | 82.80,138.78 | [工程推断·非史料] |
| 677 | ARCH07.WEST.IMPOST.C02.B02 | 33 | 41.40,0.00 | [工程推断·非史料] |
| 678 | ARCH07.WEST.IMPOST.C02.B03 | 32 | 20.70,156.39 | [工程推断·非史料] |
| 679 | ARCH07.WEST.IMPOST.C02.B04 | 32 | 41.40,156.39 | [工程推断·非史料] |

### S125 ARCH07.IMPOST.C01 (events 680-687)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 680 | ARCH07.EAST.IMPOST.C01.B01 | 32 | 165.60,208.26 | [工程推断·非史料] |
| 681 | ARCH07.EAST.IMPOST.C01.B02 | 33 | 200.91,131.82 | [工程推断·非史料] |
| 682 | ARCH07.EAST.IMPOST.C01.B03 | 32 | 0.00,138.78 | [工程推断·非史料] |
| 683 | ARCH07.EAST.IMPOST.C01.B04 | 33 | 72.63,148.42 | [工程推断·非史料] |
| 684 | ARCH07.WEST.IMPOST.C01.B01 | 33 | 20.70,0.00 | [工程推断·非史料] |
| 685 | ARCH07.WEST.IMPOST.C01.B02 | 33 | 0.00,148.42 | [工程推断·非史料] |
| 686 | ARCH07.WEST.IMPOST.C01.B03 | 32 | 62.10,138.78 | [工程推断·非史料] |
| 687 | ARCH07.WEST.IMPOST.C01.B04 | 33 | 86.58,148.42 | [工程推断·非史料] |

### S126 ARCH07.IMPOST.C00 (events 688-695)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 688 | ARCH07.EAST.IMPOST.C00.B01 | 32 | 187.26,121.88 | [工程推断·非史料] |
| 689 | ARCH07.EAST.IMPOST.C00.B02 | 32 | 144.90,208.26 | [工程推断·非史料] |
| 690 | ARCH07.EAST.IMPOST.C00.B03 | 32 | 103.50,147.58 | [工程推断·非史料] |
| 691 | ARCH07.EAST.IMPOST.C00.B04 | 32 | 124.20,147.58 | [工程推断·非史料] |
| 692 | ARCH07.WEST.IMPOST.C00.B01 | 32 | 41.40,138.78 | [工程推断·非史料] |
| 693 | ARCH07.WEST.IMPOST.C00.B02 | 33 | 0.00,0.00 | [工程推断·非史料] |
| 694 | ARCH07.WEST.IMPOST.C00.B03 | 32 | 186.30,147.58 | [工程推断·非史料] |
| 695 | ARCH07.WEST.IMPOST.C00.B04 | 32 | 0.00,156.39 | [工程推断·非史料] |

### S128 ARCH07.RING.bank01 (events 697-698)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 697 | ARCH07.EAST.RING.C00.B02 | 2 | 0.00,175.42 | [工程推断·非史料] |
| 698 | ARCH07.EAST.RING.C00.B12 | 2 | 0.00,191.99 | [工程推断·非史料] |

### S129 ARCH07.RING.bank02 (events 699-700)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 699 | ARCH07.EAST.RING.C00.B03 | 3 | 0.00,141.38 | [工程推断·非史料] |
| 700 | ARCH07.EAST.RING.C00.B11 | 3 | 0.00,160.76 | [工程推断·非史料] |

### S130 ARCH07.RING.bank03 (events 701-702)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 701 | ARCH07.EAST.RING.C00.B04 | 5 | 0.00,20.48 | [工程推断·非史料] |
| 702 | ARCH07.EAST.RING.C00.B10 | 5 | 0.00,41.09 | [工程推断·非史料] |

### S131 ARCH07.RING.bank04 (events 703-704)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 703 | ARCH07.EAST.RING.C00.B01 | 2 | 0.00,29.15 | [工程推断·非史料] |
| 704 | ARCH07.EAST.RING.C00.B13 | 2 | 0.00,41.92 | [工程推断·非史料] |

### S132 ARCH07.RING.bank05 (events 705-706)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 705 | ARCH07.EAST.RING.C00.B05 | 6 | 0.00,20.50 | [工程推断·非史料] |
| 706 | ARCH07.EAST.RING.C00.B09 | 6 | 0.00,41.87 | [工程推断·非史料] |

### S133 ARCH07.RING.bank06 (events 707-708)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 707 | ARCH07.EAST.RING.C00.B06 | 9 | 0.00,186.46 | [工程推断·非史料] |
| 708 | ARCH07.EAST.RING.C00.B08 | 10 | 0.00,0.00 | [工程推断·非史料] |

### S134 ARCH07.RING.bank07 (events 709-709)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 709 | ARCH07.EAST.RING.C00.B07 | 10 | 0.00,99.67 | [工程推断·非史料] |

### S148 ARCH07.SHOULDER.C12 (events 807-815)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 807 | ARCH07.EAST.BACK.C12.B02 | 27 | 27.35,65.45 | [工程推断·非史料] |
| 808 | ARCH07.EAST.BACK.C12.B04 | 30 | 0.00,162.72 | [工程推断·非史料] |
| 809 | ARCH07.EAST.SPANDREL.C12.B02 | 27 | 0.00,65.45 | [工程推断·非史料] |
| 810 | ARCH07.EAST.SPANDREL.C12.B04 | 28 | 52.04,144.75 | [工程推断·非史料] |
| 811 | ARCH07.WEST.BACK.C12.B02 | 27 | 82.05,65.45 | [工程推断·非史料] |
| 812 | ARCH07.WEST.BACK.C12.B04 | 30 | 24.26,162.72 | [工程推断·非史料] |
| 813 | ARCH07.WEST.SPANDREL.C12.B02 | 27 | 54.70,65.45 | [工程推断·非史料] |
| 815 | ARCH07.WEST.SPANDREL.C12.B04 | 28 | 104.01,144.75 | [工程推断·非史料] |

### S149 ARCH07.SHOULDER.C14 (events 816-816)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 816 | ARCH07.EAST.CORE.C14.B01 | 15 | 0.00,0.00 | [工程推断·非史料] |

### S151 ARCH08.IMPOST.C02 (events 820-827)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 820 | ARCH08.EAST.IMPOST.C02.B01 | 32 | 144.90,156.39 | [工程推断·非史料] |
| 821 | ARCH08.EAST.IMPOST.C02.B02 | 32 | 165.60,156.39 | [工程推断·非史料] |
| 822 | ARCH08.EAST.IMPOST.C02.B03 | 32 | 186.30,156.39 | [工程推断·非史料] |
| 823 | ARCH08.EAST.IMPOST.C02.B04 | 32 | 144.90,191.00 | [工程推断·非史料] |
| 824 | ARCH08.WEST.IMPOST.C02.B01 | 32 | 82.80,165.07 | [工程推断·非史料] |
| 825 | ARCH08.WEST.IMPOST.C02.B02 | 32 | 103.50,165.07 | [工程推断·非史料] |
| 826 | ARCH08.WEST.IMPOST.C02.B03 | 32 | 124.20,165.07 | [工程推断·非史料] |
| 827 | ARCH08.WEST.IMPOST.C02.B04 | 32 | 0.00,199.68 | [工程推断·非史料] |

### S152 ARCH08.IMPOST.C01 (events 828-835)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 828 | ARCH08.EAST.IMPOST.C01.B01 | 32 | 124.20,156.39 | [工程推断·非史料] |
| 829 | ARCH08.EAST.IMPOST.C01.B02 | 33 | 100.54,148.42 | [工程推断·非史料] |
| 830 | ARCH08.EAST.IMPOST.C01.B03 | 32 | 124.20,191.00 | [工程推断·非史料] |
| 831 | ARCH08.EAST.IMPOST.C01.B04 | 33 | 152.58,148.42 | [工程推断·非史料] |
| 832 | ARCH08.WEST.IMPOST.C01.B01 | 32 | 62.10,165.07 | [工程推断·非史料] |
| 833 | ARCH08.WEST.IMPOST.C01.B02 | 33 | 113.55,148.42 | [工程推断·非史料] |
| 834 | ARCH08.WEST.IMPOST.C01.B03 | 32 | 186.30,191.00 | [工程推断·非史料] |
| 835 | ARCH08.WEST.IMPOST.C01.B04 | 33 | 164.65,148.42 | [工程推断·非史料] |

### S153 ARCH08.IMPOST.C00 (events 836-843)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 836 | ARCH08.EAST.IMPOST.C00.B01 | 32 | 62.10,156.39 | [工程推断·非史料] |
| 837 | ARCH08.EAST.IMPOST.C00.B02 | 32 | 82.80,156.39 | [工程推断·非史料] |
| 838 | ARCH08.EAST.IMPOST.C00.B03 | 32 | 103.50,156.39 | [工程推断·非史料] |
| 839 | ARCH08.EAST.IMPOST.C00.B04 | 32 | 103.50,191.00 | [工程推断·非史料] |
| 840 | ARCH08.WEST.IMPOST.C00.B01 | 32 | 0.00,165.07 | [工程推断·非史料] |
| 841 | ARCH08.WEST.IMPOST.C00.B02 | 32 | 20.70,165.07 | [工程推断·非史料] |
| 842 | ARCH08.WEST.IMPOST.C00.B03 | 32 | 41.40,165.07 | [工程推断·非史料] |
| 843 | ARCH08.WEST.IMPOST.C00.B04 | 32 | 165.60,191.00 | [工程推断·非史料] |

### S155 ARCH08.RING.bank01 (events 845-846)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 845 | ARCH08.EAST.RING.C00.B02 | 2 | 0.00,80.23 | [工程推断·非史料] |
| 846 | ARCH08.EAST.RING.C00.B14 | 2 | 0.00,95.66 | [工程推断·非史料] |

### S156 ARCH08.RING.bank02 (events 847-848)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 847 | ARCH08.EAST.RING.C00.B03 | 3 | 0.00,33.14 | [工程推断·非史料] |
| 848 | ARCH08.EAST.RING.C00.B13 | 3 | 0.00,51.03 | [工程推断·非史料] |

### S157 ARCH08.RING.bank03 (events 849-850)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 849 | ARCH08.EAST.RING.C00.B04 | 4 | 0.00,38.00 | [工程推断·非史料] |
| 850 | ARCH08.EAST.RING.C00.B12 | 4 | 0.00,57.20 | [工程推断·非史料] |

### S158 ARCH08.RING.bank04 (events 851-852)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 851 | ARCH08.EAST.RING.C00.B01 | 1 | 0.00,167.65 | [工程推断·非史料] |
| 852 | ARCH08.EAST.RING.C00.B15 | 1 | 0.00,179.99 | [工程推断·非史料] |

### S159 ARCH08.RING.bank05 (events 853-854)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 853 | ARCH08.EAST.RING.C00.B05 | 4 | 0.00,154.52 | [工程推断·非史料] |
| 854 | ARCH08.EAST.RING.C00.B11 | 4 | 0.00,175.00 | [工程推断·非史料] |

### S160 ARCH08.RING.bank06 (events 855-856)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 855 | ARCH08.EAST.RING.C00.B06 | 5 | 0.00,142.38 | [工程推断·非史料] |
| 856 | ARCH08.EAST.RING.C00.B10 | 5 | 0.00,162.89 | [工程推断·非史料] |

### S161 ARCH08.RING.bank07 (events 857-858)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 857 | ARCH08.EAST.RING.C00.B07 | 8 | 0.00,172.99 | [工程推断·非史料] |
| 858 | ARCH08.EAST.RING.C00.B09 | 8 | 0.00,192.56 | [工程推断·非史料] |

### S162 ARCH08.RING.bank08 (events 859-859)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 859 | ARCH08.EAST.RING.C00.B08 | 10 | 0.00,61.35 | [工程推断·非史料] |

### S173 ARCH08.SHOULDER.C09 (events 925-940)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 928 | ARCH08.EAST.BACK.C09.B05 | 28 | 0.00,85.58 | [工程推断·非史料] |
| 932 | ARCH08.EAST.SPANDREL.C09.B05 | 27 | 55.03,21.98 | [工程推断·非史料] |
| 936 | ARCH08.WEST.BACK.C09.B05 | 28 | 52.27,85.58 | [工程推断·非史料] |
| 940 | ARCH08.WEST.SPANDREL.C09.B05 | 27 | 82.44,21.98 | [工程推断·非史料] |

### S177 ARCH08.SHOULDER.C14 (events 970-970)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 970 | ARCH08.EAST.CORE.C14.B01 | 13 | 0.00,0.00 | [工程推断·非史料] |

### S178 ARCH08.SHOULDER.C13 (events 971-978)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 971 | ARCH08.EAST.BACK.C13.B04 | 31 | 44.15,188.33 | [工程推断·非史料] |
| 972 | ARCH08.EAST.BACK.C13.B05 | 32 | 62.88,101.00 | [工程推断·非史料] |
| 973 | ARCH08.EAST.SPANDREL.C13.B04 | 22 | 152.21,45.22 | [工程推断·非史料] |
| 974 | ARCH08.EAST.SPANDREL.C13.B05 | 28 | 0.00,119.53 | [工程推断·非史料] |
| 975 | ARCH08.WEST.BACK.C13.B04 | 31 | 66.21,188.33 | [工程推断·非史料] |
| 976 | ARCH08.WEST.BACK.C13.B05 | 32 | 83.82,101.00 | [工程推断·非史料] |
| 977 | ARCH08.WEST.SPANDREL.C13.B04 | 22 | 50.74,45.22 | [工程推断·非史料] |
| 978 | ARCH08.WEST.SPANDREL.C13.B05 | 28 | 26.07,119.53 | [工程推断·非史料] |

### S180 ARCH09.IMPOST.C02 (events 982-989)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 982 | ARCH09.EAST.IMPOST.C02.B01 | 32 | 0.00,173.74 | [工程推断·非史料] |
| 983 | ARCH09.EAST.IMPOST.C02.B02 | 32 | 82.80,199.68 | [工程推断·非史料] |
| 984 | ARCH09.EAST.IMPOST.C02.B03 | 32 | 20.70,173.74 | [工程推断·非史料] |
| 985 | ARCH09.EAST.IMPOST.C02.B04 | 32 | 103.50,199.68 | [工程推断·非史料] |
| 986 | ARCH09.WEST.IMPOST.C02.B01 | 32 | 103.50,173.74 | [工程推断·非史料] |
| 987 | ARCH09.WEST.IMPOST.C02.B02 | 32 | 186.30,199.68 | [工程推断·非史料] |
| 988 | ARCH09.WEST.IMPOST.C02.B03 | 32 | 124.20,173.74 | [工程推断·非史料] |
| 989 | ARCH09.WEST.IMPOST.C02.B04 | 32 | 0.00,208.26 | [工程推断·非史料] |

### S181 ARCH09.IMPOST.C01 (events 990-997)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 990 | ARCH09.EAST.IMPOST.C01.B01 | 32 | 186.30,165.07 | [工程推断·非史料] |
| 991 | ARCH09.EAST.IMPOST.C01.B02 | 33 | 11.60,156.51 | [工程推断·非史料] |
| 992 | ARCH09.EAST.IMPOST.C01.B03 | 32 | 62.10,199.68 | [工程推断·非史料] |
| 993 | ARCH09.EAST.IMPOST.C01.B04 | 33 | 200.86,148.42 | [工程推断·非史料] |
| 994 | ARCH09.WEST.IMPOST.C01.B01 | 32 | 82.80,173.74 | [工程推断·非史料] |
| 995 | ARCH09.WEST.IMPOST.C01.B02 | 33 | 23.20,156.51 | [工程推断·非史料] |
| 996 | ARCH09.WEST.IMPOST.C01.B03 | 32 | 165.60,199.68 | [工程推断·非史料] |
| 997 | ARCH09.WEST.IMPOST.C01.B04 | 33 | 0.00,156.51 | [工程推断·非史料] |

### S182 ARCH09.IMPOST.C00 (events 998-1005)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 998 | ARCH09.EAST.IMPOST.C00.B01 | 32 | 144.90,165.07 | [工程推断·非史料] |
| 999 | ARCH09.EAST.IMPOST.C00.B02 | 32 | 20.70,199.68 | [工程推断·非史料] |
| 1000 | ARCH09.EAST.IMPOST.C00.B03 | 32 | 165.60,165.07 | [工程推断·非史料] |
| 1001 | ARCH09.EAST.IMPOST.C00.B04 | 32 | 41.40,199.68 | [工程推断·非史料] |
| 1002 | ARCH09.WEST.IMPOST.C00.B01 | 32 | 41.40,173.74 | [工程推断·非史料] |
| 1003 | ARCH09.WEST.IMPOST.C00.B02 | 32 | 124.20,199.68 | [工程推断·非史料] |
| 1004 | ARCH09.WEST.IMPOST.C00.B03 | 32 | 62.10,173.74 | [工程推断·非史料] |
| 1005 | ARCH09.WEST.IMPOST.C00.B04 | 32 | 144.90,199.68 | [工程推断·非史料] |

### S184 ARCH09.RING.bank01 (events 1007-1008)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1007 | ARCH09.EAST.RING.C00.B02 | 2 | 0.00,0.00 | [工程推断·非史料] |
| 1008 | ARCH09.EAST.RING.C00.B16 | 2 | 0.00,14.58 | [工程推断·非史料] |

### S185 ARCH09.RING.bank02 (events 1009-1010)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1009 | ARCH09.EAST.RING.C00.B03 | 2 | 0.00,141.97 | [工程推断·非史料] |
| 1010 | ARCH09.EAST.RING.C00.B15 | 2 | 0.00,158.69 | [工程推断·非史料] |

### S186 ARCH09.RING.bank03 (events 1011-1012)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1011 | ARCH09.EAST.RING.C00.B04 | 3 | 0.00,104.70 | [工程推断·非史料] |
| 1012 | ARCH09.EAST.RING.C00.B14 | 3 | 0.00,123.04 | [工程推断·非史料] |

### S187 ARCH09.RING.bank04 (events 1013-1014)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1013 | ARCH09.EAST.RING.C00.B05 | 4 | 0.00,0.00 | [工程推断·非史料] |
| 1014 | ARCH09.EAST.RING.C00.B13 | 4 | 0.00,19.00 | [工程推断·非史料] |

### S188 ARCH09.RING.bank05 (events 1015-1016)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1015 | ARCH09.EAST.RING.C00.B01 | 0 | 0.00,0.00 | [工程推断·非史料] |
| 1016 | ARCH09.EAST.RING.C00.B17 | 1 | 0.00,0.00 | [工程推断·非史料] |

### S189 ARCH09.RING.bank06 (events 1017-1018)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1017 | ARCH09.EAST.RING.C00.B06 | 4 | 0.00,114.78 | [工程推断·非史料] |
| 1018 | ARCH09.EAST.RING.C00.B12 | 4 | 0.00,134.65 | [工程推断·非史料] |

### S190 ARCH09.RING.bank07 (events 1019-1020)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1019 | ARCH09.EAST.RING.C00.B07 | 5 | 0.00,102.90 | [工程推断·非史料] |
| 1020 | ARCH09.EAST.RING.C00.B11 | 5 | 0.00,122.64 | [工程推断·非史料] |

### S191 ARCH09.RING.bank08 (events 1021-1022)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1021 | ARCH09.EAST.RING.C00.B08 | 8 | 0.00,0.00 | [工程推断·非史料] |
| 1022 | ARCH09.EAST.RING.C00.B10 | 8 | 0.00,18.98 | [工程推断·非史料] |

### S192 ARCH09.RING.bank09 (events 1023-1023)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1023 | ARCH09.EAST.RING.C00.B09 | 9 | 0.00,39.13 | [工程推断·非史料] |

### S204 ARCH09.SHOULDER.C14 (events 1124-1124)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1124 | ARCH09.EAST.CORE.C14.B01 | 11 | 0.00,64.14 | [工程推断·非史料] |

### S205 ARCH09.SHOULDER.C13 (events 1125-1128)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1125 | ARCH09.EAST.BACK.C13.B03 | 32 | 20.98,101.00 | [工程推断·非史料] |
| 1126 | ARCH09.EAST.SPANDREL.C13.B03 | 28 | 78.21,119.53 | [工程推断·非史料] |
| 1127 | ARCH09.WEST.BACK.C13.B03 | 32 | 41.93,101.00 | [工程推断·非史料] |
| 1128 | ARCH09.WEST.SPANDREL.C13.B03 | 28 | 52.14,119.53 | [工程推断·非史料] |

### S207 ARCH10.IMPOST.C02 (events 1132-1139)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1132 | ARCH10.EAST.IMPOST.C02.B01 | 32 | 186.30,173.74 | [工程推断·非史料] |
| 1133 | ARCH10.EAST.IMPOST.C02.B02 | 32 | 62.10,208.26 | [工程推断·非史料] |
| 1134 | ARCH10.EAST.IMPOST.C02.B03 | 32 | 0.00,182.32 | [工程推断·非史料] |
| 1135 | ARCH10.EAST.IMPOST.C02.B04 | 32 | 124.20,138.78 | [工程推断·非史料] |
| 1136 | ARCH10.WEST.IMPOST.C02.B01 | 32 | 62.10,182.32 | [工程推断·非史料] |
| 1137 | ARCH10.WEST.IMPOST.C02.B02 | 32 | 124.20,208.26 | [工程推断·非史料] |
| 1138 | ARCH10.WEST.IMPOST.C02.B03 | 32 | 82.80,182.32 | [工程推断·非史料] |
| 1139 | ARCH10.WEST.IMPOST.C02.B04 | 32 | 165.60,138.78 | [工程推断·非史料] |

### S208 ARCH10.IMPOST.C01 (events 1140-1147)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1140 | ARCH10.EAST.IMPOST.C01.B01 | 32 | 41.40,208.26 | [工程推断·非史料] |
| 1141 | ARCH10.EAST.IMPOST.C01.B02 | 33 | 176.72,148.42 | [工程推断·非史料] |
| 1142 | ARCH10.EAST.IMPOST.C01.B03 | 33 | 62.10,0.00 | [工程推断·非史料] |
| 1143 | ARCH10.EAST.IMPOST.C01.B04 | 33 | 126.56,148.42 | [工程推断·非史料] |
| 1144 | ARCH10.WEST.IMPOST.C01.B01 | 32 | 103.50,208.26 | [工程推断·非史料] |
| 1145 | ARCH10.WEST.IMPOST.C01.B02 | 33 | 188.79,148.42 | [工程推断·非史料] |
| 1146 | ARCH10.WEST.IMPOST.C01.B03 | 33 | 82.80,0.00 | [工程推断·非史料] |
| 1147 | ARCH10.WEST.IMPOST.C01.B04 | 33 | 139.57,148.42 | [工程推断·非史料] |

### S209 ARCH10.IMPOST.C00 (events 1148-1155)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1148 | ARCH10.EAST.IMPOST.C00.B01 | 32 | 144.90,173.74 | [工程推断·非史料] |
| 1149 | ARCH10.EAST.IMPOST.C00.B02 | 32 | 20.70,208.26 | [工程推断·非史料] |
| 1150 | ARCH10.EAST.IMPOST.C00.B03 | 32 | 165.60,173.74 | [工程推断·非史料] |
| 1151 | ARCH10.EAST.IMPOST.C00.B04 | 32 | 103.50,138.78 | [工程推断·非史料] |
| 1152 | ARCH10.WEST.IMPOST.C00.B01 | 32 | 20.70,182.32 | [工程推断·非史料] |
| 1153 | ARCH10.WEST.IMPOST.C00.B02 | 32 | 82.80,208.26 | [工程推断·非史料] |
| 1154 | ARCH10.WEST.IMPOST.C00.B03 | 32 | 41.40,182.32 | [工程推断·非史料] |
| 1155 | ARCH10.WEST.IMPOST.C00.B04 | 32 | 144.90,138.78 | [工程推断·非史料] |

### S211 ARCH10.RING.bank01 (events 1157-1158)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1157 | ARCH10.EAST.RING.C00.B02 | 2 | 0.00,111.10 | [工程推断·非史料] |
| 1158 | ARCH10.EAST.RING.C00.B14 | 2 | 0.00,126.53 | [工程推断·非史料] |

### S212 ARCH10.RING.bank02 (events 1159-1160)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1159 | ARCH10.EAST.RING.C00.B03 | 3 | 0.00,68.92 | [工程推断·非史料] |
| 1160 | ARCH10.EAST.RING.C00.B13 | 3 | 0.00,86.81 | [工程推断·非史料] |

### S213 ARCH10.RING.bank03 (events 1161-1162)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1161 | ARCH10.EAST.RING.C00.B04 | 4 | 0.00,76.39 | [工程推断·非史料] |
| 1162 | ARCH10.EAST.RING.C00.B12 | 4 | 0.00,95.59 | [工程推断·非史料] |

### S214 ARCH10.RING.bank04 (events 1163-1164)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1163 | ARCH10.EAST.RING.C00.B01 | 1 | 0.00,192.34 | [工程推断·非史料] |
| 1164 | ARCH10.EAST.RING.C00.B15 | 1 | 0.00,204.68 | [工程推断·非史料] |

### S215 ARCH10.RING.bank05 (events 1165-1166)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1165 | ARCH10.EAST.RING.C00.B05 | 4 | 0.00,195.48 | [工程推断·非史料] |
| 1166 | ARCH10.EAST.RING.C00.B11 | 5 | 0.00,0.00 | [工程推断·非史料] |

### S216 ARCH10.RING.bank06 (events 1167-1168)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1167 | ARCH10.EAST.RING.C00.B06 | 5 | 0.00,183.39 | [工程推断·非史料] |
| 1168 | ARCH10.EAST.RING.C00.B10 | 6 | 0.00,0.00 | [工程推断·非史料] |

### S217 ARCH10.RING.bank07 (events 1169-1170)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1169 | ARCH10.EAST.RING.C00.B07 | 9 | 0.00,0.00 | [工程推断·非史料] |
| 1170 | ARCH10.EAST.RING.C00.B09 | 9 | 0.00,19.56 | [工程推断·非史料] |

### S218 ARCH10.RING.bank08 (events 1171-1171)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1171 | ARCH10.EAST.RING.C00.B08 | 10 | 0.00,80.51 | [工程推断·非史料] |

### S229 ARCH10.SHOULDER.C09 (events 1237-1252)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1237 | ARCH10.EAST.BACK.C09.B01 | 28 | 26.14,85.58 | [工程推断·非史料] |
| 1241 | ARCH10.EAST.SPANDREL.C09.B01 | 27 | 109.86,21.98 | [工程推断·非史料] |
| 1245 | ARCH10.WEST.BACK.C09.B01 | 28 | 78.41,85.58 | [工程推断·非史料] |
| 1249 | ARCH10.WEST.SPANDREL.C09.B01 | 27 | 137.28,21.98 | [工程推断·非史料] |

### S233 ARCH10.SHOULDER.C14 (events 1282-1282)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1282 | ARCH10.EAST.CORE.C14.B01 | 13 | 0.00,67.51 | [工程推断·非史料] |

### S234 ARCH10.SHOULDER.C13 (events 1283-1290)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1283 | ARCH10.EAST.BACK.C13.B03 | 32 | 189.57,80.12 | [工程推断·非史料] |
| 1284 | ARCH10.EAST.BACK.C13.B04 | 31 | 88.27,188.33 | [工程推断·非史料] |
| 1285 | ARCH10.EAST.SPANDREL.C13.B03 | 28 | 0.00,98.65 | [工程推断·非史料] |
| 1286 | ARCH10.EAST.SPANDREL.C13.B04 | 22 | 0.00,67.28 | [工程推断·非史料] |
| 1287 | ARCH10.WEST.BACK.C13.B03 | 32 | 0.00,101.00 | [工程推断·非史料] |
| 1288 | ARCH10.WEST.BACK.C13.B04 | 31 | 110.33,188.33 | [工程推断·非史料] |
| 1289 | ARCH10.WEST.SPANDREL.C13.B03 | 28 | 26.11,98.65 | [工程推断·非史料] |
| 1290 | ARCH10.WEST.SPANDREL.C13.B04 | 22 | 101.48,45.22 | [工程推断·非史料] |

### S236 ARCH11.IMPOST.C02 (events 1294-1301)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1294 | ARCH11.EAST.IMPOST.C02.B01 | 32 | 165.60,182.32 | [工程推断·非史料] |
| 1295 | ARCH11.EAST.IMPOST.C02.B02 | 32 | 186.30,182.32 | [工程推断·非史料] |
| 1296 | ARCH11.EAST.IMPOST.C02.B03 | 33 | 124.20,0.00 | [工程推断·非史料] |
| 1297 | ARCH11.EAST.IMPOST.C02.B04 | 32 | 20.70,147.58 | [工程推断·非史料] |
| 1298 | ARCH11.WEST.IMPOST.C02.B01 | 32 | 62.10,191.00 | [工程推断·非史料] |
| 1299 | ARCH11.WEST.IMPOST.C02.B02 | 32 | 82.80,191.00 | [工程推断·非史料] |
| 1300 | ARCH11.WEST.IMPOST.C02.B03 | 33 | 165.60,0.00 | [工程推断·非史料] |
| 1301 | ARCH11.WEST.IMPOST.C02.B04 | 32 | 82.80,147.58 | [工程推断·非史料] |

### S237 ARCH11.IMPOST.C01 (events 1302-1309)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1302 | ARCH11.EAST.IMPOST.C01.B01 | 32 | 144.90,182.32 | [工程推断·非史料] |
| 1303 | ARCH11.EAST.IMPOST.C01.B02 | 33 | 44.72,148.42 | [工程推断·非史料] |
| 1304 | ARCH11.EAST.IMPOST.C01.B03 | 32 | 0.00,147.58 | [工程推断·非史料] |
| 1305 | ARCH11.EAST.IMPOST.C01.B04 | 33 | 14.91,148.42 | [工程推断·非史料] |
| 1306 | ARCH11.WEST.IMPOST.C01.B01 | 32 | 41.40,191.00 | [工程推断·非史料] |
| 1307 | ARCH11.WEST.IMPOST.C01.B02 | 33 | 58.67,148.42 | [工程推断·非史料] |
| 1308 | ARCH11.WEST.IMPOST.C01.B03 | 32 | 62.10,147.58 | [工程推断·非史料] |
| 1309 | ARCH11.WEST.IMPOST.C01.B04 | 33 | 29.81,148.42 | [工程推断·非史料] |

### S238 ARCH11.IMPOST.C00 (events 1310-1317)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1310 | ARCH11.EAST.IMPOST.C00.B01 | 32 | 103.50,182.32 | [工程推断·非史料] |
| 1311 | ARCH11.EAST.IMPOST.C00.B02 | 32 | 124.20,182.32 | [工程推断·非史料] |
| 1312 | ARCH11.EAST.IMPOST.C00.B03 | 33 | 103.50,0.00 | [工程推断·非史料] |
| 1313 | ARCH11.EAST.IMPOST.C00.B04 | 32 | 186.30,138.78 | [工程推断·非史料] |
| 1314 | ARCH11.WEST.IMPOST.C00.B01 | 32 | 0.00,191.00 | [工程推断·非史料] |
| 1315 | ARCH11.WEST.IMPOST.C00.B02 | 32 | 20.70,191.00 | [工程推断·非史料] |
| 1316 | ARCH11.WEST.IMPOST.C00.B03 | 33 | 144.90,0.00 | [工程推断·非史料] |
| 1317 | ARCH11.WEST.IMPOST.C00.B04 | 32 | 41.40,147.58 | [工程推断·非史料] |

### S240 ARCH11.RING.bank01 (events 1319-1320)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1319 | ARCH11.EAST.RING.C00.B02 | 3 | 0.00,0.00 | [工程推断·非史料] |
| 1320 | ARCH11.EAST.RING.C00.B12 | 3 | 0.00,16.57 | [工程推断·非史料] |

### S241 ARCH11.RING.bank02 (events 1321-1322)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1321 | ARCH11.EAST.RING.C00.B03 | 3 | 0.00,180.13 | [工程推断·非史料] |
| 1322 | ARCH11.EAST.RING.C00.B11 | 3 | 0.00,199.50 | [工程推断·非史料] |

### S242 ARCH11.RING.bank03 (events 1323-1324)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1323 | ARCH11.EAST.RING.C00.B04 | 5 | 0.00,61.69 | [工程推断·非史料] |
| 1324 | ARCH11.EAST.RING.C00.B10 | 5 | 0.00,82.30 | [工程推断·非史料] |

### S243 ARCH11.RING.bank04 (events 1325-1326)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1325 | ARCH11.EAST.RING.C00.B01 | 2 | 0.00,54.69 | [工程推断·非史料] |
| 1326 | ARCH11.EAST.RING.C00.B13 | 2 | 0.00,67.46 | [工程推断·非史料] |

### S244 ARCH11.RING.bank05 (events 1327-1328)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1327 | ARCH11.EAST.RING.C00.B05 | 6 | 0.00,63.24 | [工程推断·非史料] |
| 1328 | ARCH11.EAST.RING.C00.B09 | 6 | 0.00,84.62 | [工程推断·非史料] |

### S245 ARCH11.RING.bank06 (events 1329-1330)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1329 | ARCH11.EAST.RING.C00.B06 | 10 | 0.00,20.45 | [工程推断·非史料] |
| 1330 | ARCH11.EAST.RING.C00.B08 | 10 | 0.00,40.90 | [工程推断·非史料] |

### S246 ARCH11.RING.bank07 (events 1331-1331)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1331 | ARCH11.EAST.RING.C00.B07 | 10 | 0.00,119.66 | [工程推断·非史料] |

### S260 ARCH11.SHOULDER.C12 (events 1429-1437)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1429 | ARCH11.EAST.BACK.C12.B02 | 30 | 48.52,162.72 | [工程推断·非史料] |
| 1430 | ARCH11.EAST.BACK.C12.B04 | 27 | 136.78,39.45 | [工程推断·非史料] |
| 1431 | ARCH11.EAST.SPANDREL.C12.B02 | 28 | 78.03,144.75 | [工程推断·非史料] |
| 1432 | ARCH11.EAST.SPANDREL.C12.B04 | 27 | 109.44,39.45 | [工程推断·非史料] |
| 1433 | ARCH11.WEST.BACK.C12.B02 | 30 | 72.78,162.72 | [工程推断·非史料] |
| 1434 | ARCH11.WEST.BACK.C12.B04 | 27 | 191.48,39.45 | [工程推断·非史料] |
| 1435 | ARCH11.WEST.SPANDREL.C12.B02 | 28 | 129.99,144.75 | [工程推断·非史料] |
| 1437 | ARCH11.WEST.SPANDREL.C12.B04 | 27 | 164.13,39.45 | [工程推断·非史料] |

### S261 ARCH11.SHOULDER.C14 (events 1438-1438)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 1438 | ARCH11.EAST.CORE.C14.B01 | 15 | 0.00,64.14 | [工程推断·非史料] |

### S398 ARCH07.FILL (events 2616-2808)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 2652 | ARCH07.EAST.BACK.C08.B00 | 31 | 90.72,109.50 | [工程推断·非史料] |
| 2653 | ARCH07.EAST.BACK.C08.B05 | 27 | 0.00,179.19 | [工程推断·非史料] |
| 2654 | ARCH07.EAST.SPANDREL.C08.B00 | 26 | 58.96,129.56 | [工程推断·非史料] |
| 2655 | ARCH07.EAST.SPANDREL.C08.B05 | 20 | 131.98,64.44 | [工程推断·非史料] |
| 2656 | ARCH07.WEST.BACK.C08.B00 | 31 | 136.03,109.50 | [工程推断·非史料] |
| 2657 | ARCH07.WEST.BACK.C08.B05 | 27 | 26.52,179.19 | [工程推断·非史料] |
| 2658 | ARCH07.WEST.SPANDREL.C08.B00 | 26 | 88.05,129.56 | [工程推断·非史料] |
| 2659 | ARCH07.WEST.SPANDREL.C08.B05 | 20 | 0.00,128.89 | [工程推断·非史料] |
| 2663 | ARCH07.EAST.BACK.C09.B00 | 30 | 193.93,162.72 | [工程推断·非史料] |
| 2665 | ARCH07.EAST.BACK.C09.B05 | 30 | 73.02,146.70 | [工程推断·非史料] |
| 2666 | ARCH07.EAST.BACK.C09.B06 | 32 | 153.34,0.00 | [工程推断·非史料] |
| 2667 | ARCH07.EAST.SPANDREL.C09.B00 | 21 | 51.47,0.00 | [工程推断·非史料] |
| 2668 | ARCH07.EAST.SPANDREL.C09.B05 | 27 | 0.00,39.45 | [工程推断·非史料] |
| 2669 | ARCH07.EAST.SPANDREL.C09.B06 | 21 | 154.10,85.64 | [工程推断·非史料] |
| 2670 | ARCH07.WEST.BACK.C09.B00 | 30 | 0.00,186.35 | [工程推断·非史料] |
| 2672 | ARCH07.WEST.BACK.C09.B05 | 30 | 24.37,146.70 | [工程推断·非史料] |
| 2673 | ARCH07.WEST.BACK.C09.B06 | 32 | 109.74,0.00 | [工程推断·非史料] |
| 2674 | ARCH07.WEST.SPANDREL.C09.B00 | 21 | 102.92,0.00 | [工程推断·非史料] |
| 2675 | ARCH07.WEST.SPANDREL.C09.B05 | 27 | 54.72,39.45 | [工程推断·非史料] |
| 2676 | ARCH07.WEST.SPANDREL.C09.B06 | 21 | 51.40,85.64 | [工程推断·非史料] |
| 2677 | ARCH07.EAST.CORE.C13.B00 | 11 | 0.00,0.00 | [工程推断·非史料] |
| 2679 | ARCH07.EAST.CORE.C13.B02 | 9 | 0.00,122.32 | [工程推断·非史料] |
| 2680 | ARCH07.EAST.BACK.C10.B00 | 33 | 102.45,31.03 | [工程推断·非史料] |
| 2681 | ARCH07.EAST.BACK.C10.B01 | 33 | 20.51,31.03 | [工程推断·非史料] |
| 2682 | ARCH07.EAST.BACK.C10.B02 | 33 | 151.02,113.66 | [工程推断·非史料] |
| 2684 | ARCH07.EAST.BACK.C10.B06 | 31 | 0.00,43.65 | [工程推断·非史料] |
| 2685 | ARCH07.EAST.BACK.C10.B07 | 33 | 144.17,10.68 | [工程推断·非史料] |
| 2686 | ARCH07.EAST.BACK.C10.B08 | 30 | 0.00,62.74 | [工程推断·非史料] |
| 2687 | ARCH07.EAST.SPANDREL.C10.B00 | 30 | 0.00,0.00 | [工程推断·非史料] |
| 2688 | ARCH07.EAST.SPANDREL.C10.B01 | 25 | 98.74,46.42 | [工程推断·非史料] |
| 2689 | ARCH07.EAST.SPANDREL.C10.B02 | 30 | 50.75,0.00 | [工程推断·非史料] |
| 2690 | ARCH07.EAST.SPANDREL.C10.B06 | 30 | 152.21,0.00 | [工程推断·非史料] |
| 2691 | ARCH07.EAST.SPANDREL.C10.B07 | 25 | 0.00,70.20 | [工程推断·非史料] |
| 2692 | ARCH07.EAST.SPANDREL.C10.B08 | 30 | 101.32,14.25 | [工程推断·非史料] |
| 2693 | ARCH07.WEST.BACK.C10.B00 | 33 | 122.84,31.03 | [工程推断·非史料] |
| 2694 | ARCH07.WEST.BACK.C10.B01 | 33 | 41.00,31.03 | [工程推断·非史料] |
| 2695 | ARCH07.WEST.BACK.C10.B02 | 33 | 187.78,113.66 | [工程推断·非史料] |
| 2697 | ARCH07.WEST.BACK.C10.B06 | 31 | 164.53,22.49 | [工程推断·非史料] |
| 2698 | ARCH07.WEST.BACK.C10.B07 | 33 | 164.68,10.68 | [工程推断·非史料] |
| 2699 | ARCH07.WEST.BACK.C10.B08 | 30 | 50.35,62.74 | [工程推断·非史料] |
| 2700 | ARCH07.WEST.SPANDREL.C10.B00 | 29 | 152.74,205.46 | [工程推断·非史料] |
| 2701 | ARCH07.WEST.SPANDREL.C10.B01 | 25 | 0.00,46.42 | [工程推断·非史料] |
| 2702 | ARCH07.WEST.SPANDREL.C10.B02 | 30 | 101.48,0.00 | [工程推断·非史料] |
| 2703 | ARCH07.WEST.SPANDREL.C10.B06 | 30 | 0.00,14.25 | [工程推断·非史料] |
| 2704 | ARCH07.WEST.SPANDREL.C10.B07 | 25 | 49.33,70.20 | [工程推断·非史料] |
| 2705 | ARCH07.WEST.SPANDREL.C10.B08 | 30 | 50.67,14.25 | [工程推断·非史料] |
| 2706 | ARCH07.EAST.BACK.C11.B00 | 33 | 39.76,87.62 | [工程推断·非史料] |
| 2707 | ARCH07.EAST.BACK.C11.B01 | 29 | 153.89,144.53 | [工程推断·非史料] |
| 2708 | ARCH07.EAST.BACK.C11.B05 | 30 | 0.00,125.36 | [工程推断·非史料] |
| 2709 | ARCH07.EAST.SPANDREL.C11.B00 | 24 | 99.67,15.70 | [工程推断·非史料] |
| 2710 | ARCH07.EAST.SPANDREL.C11.B01 | 29 | 51.64,51.24 | [工程推断·非史料] |
| 2711 | ARCH07.EAST.SPANDREL.C11.B05 | 29 | 51.58,76.69 | [工程推断·非史料] |
| 2712 | ARCH07.WEST.BACK.C11.B00 | 33 | 59.53,87.62 | [工程推断·非史料] |
| 2713 | ARCH07.WEST.BACK.C11.B01 | 29 | 102.62,144.53 | [工程推断·非史料] |
| 2714 | ARCH07.WEST.BACK.C11.B05 | 30 | 24.40,125.36 | [工程推断·非史料] |
| 2715 | ARCH07.WEST.SPANDREL.C11.B00 | 24 | 149.48,15.70 | [工程推断·非史料] |
| 2716 | ARCH07.WEST.SPANDREL.C11.B01 | 29 | 77.44,51.24 | [工程推断·非史料] |
| 2717 | ARCH07.WEST.SPANDREL.C11.B05 | 29 | 103.10,76.69 | [工程推断·非史料] |
| 2718 | ARCH07.EAST.BACK.C12.B00 | 30 | 101.05,38.07 | [工程推断·非史料] |
| 2719 | ARCH07.EAST.BACK.C12.B01 | 30 | 97.60,125.36 | [工程推断·非史料] |
| 2721 | ARCH07.EAST.BACK.C12.B05 | 32 | 21.27,62.22 | [工程推断·非史料] |
| 2722 | ARCH07.EAST.BACK.C12.B06 | 27 | 134.78,109.35 | [工程推断·非史料] |
| 2723 | ARCH07.EAST.SPANDREL.C12.B00 | 28 | 156.40,119.53 | [工程推断·非史料] |
| 2724 | ARCH07.EAST.SPANDREL.C12.B01 | 23 | 100.22,136.36 | [工程推断·非史料] |
| 2726 | ARCH07.EAST.SPANDREL.C12.B05 | 23 | 100.03,164.42 | [工程推断·非史料] |
| 2727 | ARCH07.EAST.SPANDREL.C12.B06 | 27 | 107.84,109.35 | [工程推断·非史料] |
| 2728 | ARCH07.WEST.BACK.C12.B00 | 30 | 126.27,38.07 | [工程推断·非史料] |
| 2729 | ARCH07.WEST.BACK.C12.B01 | 30 | 121.98,125.36 | [工程推断·非史料] |
| 2731 | ARCH07.WEST.BACK.C12.B05 | 32 | 42.51,62.22 | [工程推断·非史料] |
| 2732 | ARCH07.WEST.BACK.C12.B06 | 27 | 188.66,109.35 | [工程推断·非史料] |
| 2733 | ARCH07.WEST.SPANDREL.C12.B00 | 28 | 182.42,119.53 | [工程推断·非史料] |
| 2734 | ARCH07.WEST.SPANDREL.C12.B01 | 23 | 0.00,164.42 | [工程推断·非史料] |
| 2735 | ARCH07.WEST.SPANDREL.C12.B05 | 23 | 150.00,164.42 | [工程推断·非史料] |
| 2736 | ARCH07.WEST.SPANDREL.C12.B06 | 27 | 161.72,109.35 | [工程推断·非史料] |
| 2737 | ARCH07.EAST.CORE.C14.B00 | 16 | 0.00,0.00 | [工程推断·非史料] |
| 2738 | ARCH07.EAST.CORE.C14.B02 | 14 | 0.00,131.66 | [工程推断·非史料] |
| 2739 | ARCH07.EAST.BACK.C13.B00 | 30 | 151.97,14.25 | [工程推断·非史料] |
| 2740 | ARCH07.EAST.BACK.C13.B01 | 32 | 190.93,62.22 | [工程推断·非史料] |
| 2741 | ARCH07.EAST.BACK.C13.B02 | 31 | 91.71,74.32 | [工程推断·非史料] |
| 2742 | ARCH07.EAST.BACK.C13.B03 | 26 | 112.67,156.27 | [工程推断·非史料] |
| 2743 | ARCH07.EAST.BACK.C13.B04 | 33 | 61.85,10.68 | [工程推断·非史料] |
| 2744 | ARCH07.EAST.BACK.C13.B05 | 33 | 184.02,31.03 | [工程推断·非史料] |
| 2745 | ARCH07.EAST.BACK.C13.B06 | 26 | 0.00,76.74 | [工程推断·非史料] |
| 2746 | ARCH07.EAST.BACK.C13.B07 | 31 | 189.97,0.00 | [工程推断·非史料] |
| 2747 | ARCH07.EAST.SPANDREL.C13.B00 | 21 | 51.35,119.50 | [工程推断·非史料] |
| 2748 | ARCH07.EAST.SPANDREL.C13.B01 | 27 | 0.00,91.45 | [工程推断·非史料] |
| 2749 | ARCH07.EAST.SPANDREL.C13.B02 | 21 | 51.34,128.38 | [工程推断·非史料] |
| 2750 | ARCH07.EAST.SPANDREL.C13.B03 | 26 | 84.61,156.27 | [工程推断·非史料] |
| 2751 | ARCH07.EAST.SPANDREL.C13.B04 | 21 | 152.96,144.12 | [工程推断·非史料] |
| 2752 | ARCH07.EAST.SPANDREL.C13.B05 | 27 | 0.00,109.35 | [工程推断·非史料] |
| 2753 | ARCH07.EAST.SPANDREL.C13.B06 | 21 | 50.97,164.70 | [工程推断·非史料] |
| 2754 | ARCH07.EAST.SPANDREL.C13.B07 | 27 | 107.76,135.32 | [工程推断·非史料] |
| 2755 | ARCH07.WEST.BACK.C13.B00 | 30 | 0.00,20.17 | [工程推断·非史料] |
| 2756 | ARCH07.WEST.BACK.C13.B01 | 32 | 0.00,80.12 | [工程推断·非史料] |
| 2757 | ARCH07.WEST.BACK.C13.B02 | 31 | 45.89,74.32 | [工程推断·非史料] |
| 2758 | ARCH07.WEST.BACK.C13.B03 | 26 | 168.79,156.27 | [工程推断·非史料] |
| 2759 | ARCH07.WEST.BACK.C13.B04 | 33 | 82.43,10.68 | [工程推断·非史料] |
| 2760 | ARCH07.WEST.BACK.C13.B05 | 33 | 0.00,50.17 | [工程推断·非史料] |
| 2761 | ARCH07.WEST.BACK.C13.B06 | 26 | 29.48,76.74 | [工程推断·非史料] |
| 2762 | ARCH07.WEST.BACK.C13.B07 | 31 | 142.67,0.00 | [工程推断·非史料] |
| 2763 | ARCH07.WEST.SPANDREL.C13.B00 | 21 | 154.02,119.50 | [工程推断·非史料] |
| 2764 | ARCH07.WEST.SPANDREL.C13.B01 | 27 | 54.05,91.45 | [工程推断·非史料] |
| 2765 | ARCH07.WEST.SPANDREL.C13.B02 | 21 | 153.36,128.38 | [工程推断·非史料] |
| 2766 | ARCH07.WEST.SPANDREL.C13.B03 | 26 | 140.73,156.27 | [工程推断·非史料] |
| 2767 | ARCH07.WEST.SPANDREL.C13.B04 | 21 | 51.01,144.12 | [工程推断·非史料] |
| 2768 | ARCH07.WEST.SPANDREL.C13.B05 | 27 | 26.96,109.35 | [工程推断·非史料] |
| 2769 | ARCH07.WEST.SPANDREL.C13.B06 | 21 | 101.92,164.70 | [工程推断·非史料] |
| 2770 | ARCH07.WEST.SPANDREL.C13.B07 | 27 | 161.62,135.32 | [工程推断·非史料] |
| 2771 | ARCH07.EAST.BACK.C14.B00 | 33 | 135.17,103.96 | [工程推断·非史料] |
| 2772 | ARCH07.EAST.BACK.C14.B01 | 31 | 44.68,149.20 | [工程推断·非史料] |
| 2773 | ARCH07.EAST.BACK.C14.B02 | 33 | 186.30,0.00 | [工程推断·非史料] |
| 2774 | ARCH07.EAST.BACK.C14.B03 | 30 | 0.00,116.20 | [工程推断·非史料] |
| 2775 | ARCH07.EAST.BACK.C14.B04 | 29 | 77.47,25.79 | [工程推断·非史料] |
| 2776 | ARCH07.EAST.BACK.C14.B05 | 32 | 41.77,121.88 | [工程推断·非史料] |
| 2777 | ARCH07.EAST.BACK.C14.B06 | 30 | 98.92,95.16 | [工程推断·非史料] |
| 2778 | ARCH07.EAST.BACK.C14.B07 | 31 | 0.00,0.00 | [工程推断·非史料] |
| 2779 | ARCH07.EAST.BACK.C14.B08 | 33 | 158.30,87.62 | [工程推断·非史料] |
| 2780 | ARCH07.EAST.SPANDREL.C14.B00 | 30 | 122.43,116.20 | [工程推断·非史料] |
| 2781 | ARCH07.EAST.SPANDREL.C14.B01 | 25 | 0.00,118.48 | [工程推断·非史料] |
| 2782 | ARCH07.EAST.SPANDREL.C14.B02 | 30 | 150.72,62.74 | [工程推断·非史料] |
| 2783 | ARCH07.EAST.SPANDREL.C14.B03 | 25 | 0.00,100.10 | [工程推断·非史料] |
| 2784 | ARCH07.EAST.SPANDREL.C14.B04 | 29 | 51.65,25.79 | [工程推断·非史料] |
| 2785 | ARCH07.EAST.SPANDREL.C14.B05 | 24 | 0.00,198.56 | [工程推断·非史料] |
| 2786 | ARCH07.EAST.SPANDREL.C14.B06 | 29 | 0.00,160.27 | [工程推断·非史料] |
| 2787 | ARCH07.EAST.SPANDREL.C14.B07 | 25 | 0.00,0.00 | [工程推断·非史料] |
| 2788 | ARCH07.EAST.SPANDREL.C14.B08 | 29 | 102.38,160.27 | [工程推断·非史料] |
| 2789 | ARCH07.WEST.BACK.C14.B00 | 33 | 154.46,103.96 | [工程推断·非史料] |
| 2790 | ARCH07.WEST.BACK.C14.B01 | 31 | 67.00,149.20 | [工程推断·非史料] |
| 2791 | ARCH07.WEST.BACK.C14.B02 | 33 | 0.00,10.68 | [工程推断·非史料] |
| 2792 | ARCH07.WEST.BACK.C14.B03 | 30 | 24.59,116.20 | [工程推断·非史料] |
| 2793 | ARCH07.WEST.BACK.C14.B04 | 29 | 129.11,25.79 | [工程推断·非史料] |
| 2794 | ARCH07.WEST.BACK.C14.B05 | 32 | 0.00,121.88 | [工程推断·非史料] |
| 2795 | ARCH07.WEST.BACK.C14.B06 | 30 | 123.55,95.16 | [工程推断·非史料] |
| 2796 | ARCH07.WEST.BACK.C14.B07 | 31 | 23.78,0.00 | [工程推断·非史料] |
| 2797 | ARCH07.WEST.BACK.C14.B08 | 33 | 178.02,87.62 | [工程推断·非史料] |
| 2798 | ARCH07.WEST.SPANDREL.C14.B00 | 30 | 98.03,116.20 | [工程推断·非史料] |
| 2799 | ARCH07.WEST.SPANDREL.C14.B01 | 25 | 48.70,118.48 | [工程推断·非史料] |
| 2800 | ARCH07.WEST.SPANDREL.C14.B02 | 30 | 175.72,62.74 | [工程推断·非史料] |
| 2801 | ARCH07.WEST.SPANDREL.C14.B03 | 25 | 49.17,100.10 | [工程推断·非史料] |
| 2802 | ARCH07.WEST.SPANDREL.C14.B04 | 29 | 103.29,25.79 | [工程推断·非史料] |
| 2803 | ARCH07.WEST.SPANDREL.C14.B05 | 24 | 99.40,181.66 | [工程推断·非史料] |
| 2804 | ARCH07.WEST.SPANDREL.C14.B06 | 29 | 25.60,160.27 | [工程推断·非史料] |
| 2805 | ARCH07.WEST.SPANDREL.C14.B07 | 25 | 49.59,0.00 | [工程推断·非史料] |
| 2806 | ARCH07.WEST.SPANDREL.C14.B08 | 29 | 127.97,160.27 | [工程推断·非史料] |
| 2807 | ARCH07.EAST.CORE.C15.B01 | 20 | 0.00,0.00 | [工程推断·非史料] |
| 2808 | ARCH07.EAST.CORE.C15.B02 | 19 | 0.00,0.00 | [工程推断·非史料] |

### S399 ARCH08.FILL (events 2809-3046)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 2831 | ARCH08.EAST.BACK.C07.B00 | 28 | 0.00,169.97 | [工程推断·非史料] |
| 2833 | ARCH08.EAST.SPANDREL.C07.B00 | 20 | 0.00,175.29 | [工程推断·非史料] |
| 2835 | ARCH08.WEST.BACK.C07.B00 | 28 | 25.96,169.97 | [工程推断·非史料] |
| 2837 | ARCH08.WEST.SPANDREL.C07.B00 | 20 | 156.74,163.83 | [工程推断·非史料] |
| 2842 | ARCH08.EAST.BACK.C08.B05 | 27 | 0.00,21.98 | [工程推断·非史料] |
| 2844 | ARCH08.EAST.SPANDREL.C08.B05 | 20 | 158.81,128.89 | [工程推断·非史料] |
| 2846 | ARCH08.WEST.BACK.C08.B05 | 27 | 138.25,0.00 | [工程推断·非史料] |
| 2848 | ARCH08.WEST.SPANDREL.C08.B05 | 20 | 0.00,146.36 | [工程推断·非史料] |
| 2852 | ARCH08.EAST.BACK.C09.B00 | 27 | 83.04,0.00 | [工程推断·非史料] |
| 2853 | ARCH08.EAST.BACK.C09.B06 | 27 | 108.10,91.45 | [工程推断·非史料] |
| 2854 | ARCH08.EAST.SPANDREL.C09.B00 | 20 | 52.12,175.29 | [工程推断·非史料] |
| 2855 | ARCH08.EAST.SPANDREL.C09.B06 | 21 | 51.46,27.61 | [工程推断·非史料] |
| 2856 | ARCH08.WEST.BACK.C09.B00 | 27 | 110.64,0.00 | [工程推断·非史料] |
| 2857 | ARCH08.WEST.BACK.C09.B06 | 27 | 135.07,91.45 | [工程推断·非史料] |
| 2858 | ARCH08.WEST.SPANDREL.C09.B00 | 20 | 103.59,175.29 | [工程推断·非史料] |
| 2859 | ARCH08.WEST.SPANDREL.C09.B06 | 21 | 102.87,27.61 | [工程推断·非史料] |
| 2860 | ARCH08.EAST.BACK.C10.B00 | 32 | 64.70,20.74 | [工程推断·非史料] |
| 2861 | ARCH08.EAST.BACK.C10.B01 | 31 | 69.16,64.62 | [工程推断·非史料] |
| 2862 | ARCH08.EAST.BACK.C10.B02 | 33 | 128.05,131.82 | [工程推断·非史料] |
| 2865 | ARCH08.EAST.BACK.C10.B06 | 30 | 121.66,146.70 | [工程推断·非史料] |
| 2866 | ARCH08.EAST.BACK.C10.B07 | 33 | 181.97,50.17 | [工程推断·非史料] |
| 2867 | ARCH08.EAST.BACK.C10.B08 | 32 | 62.66,121.88 | [工程推断·非史料] |
| 2868 | ARCH08.EAST.BACK.C10.B09 | 31 | 185.44,43.65 | [工程推断·非史料] |
| 2869 | ARCH08.EAST.SPANDREL.C10.B00 | 29 | 154.61,76.69 | [工程推断·非史料] |
| 2870 | ARCH08.EAST.SPANDREL.C10.B01 | 24 | 99.47,54.38 | [工程推断·非史料] |
| 2871 | ARCH08.EAST.SPANDREL.C10.B02 | 29 | 154.39,101.09 | [工程推断·非史料] |
| 2872 | ARCH08.EAST.SPANDREL.C10.B06 | 29 | 51.46,115.77 | [工程推断·非史料] |
| 2873 | ARCH08.EAST.SPANDREL.C10.B07 | 24 | 99.47,76.72 | [工程推断·非史料] |
| 2874 | ARCH08.EAST.SPANDREL.C10.B08 | 29 | 154.30,115.77 | [工程推断·非史料] |
| 2875 | ARCH08.EAST.SPANDREL.C10.B09 | 24 | 99.42,95.04 | [工程推断·非史料] |
| 2876 | ARCH08.WEST.BACK.C10.B00 | 32 | 86.23,20.74 | [工程推断·非史料] |
| 2877 | ARCH08.WEST.BACK.C10.B01 | 31 | 92.21,64.62 | [工程推断·非史料] |
| 2878 | ARCH08.WEST.BACK.C10.B02 | 33 | 164.48,131.82 | [工程推断·非史料] |
| 2881 | ARCH08.WEST.BACK.C10.B06 | 30 | 170.23,146.70 | [工程推断·非史料] |
| 2882 | ARCH08.WEST.BACK.C10.B07 | 33 | 0.00,69.30 | [工程推断·非史料] |
| 2883 | ARCH08.WEST.BACK.C10.B08 | 32 | 83.45,121.88 | [工程推断·非史料] |
| 2884 | ARCH08.WEST.BACK.C10.B09 | 31 | 23.05,64.62 | [工程推断·非史料] |
| 2885 | ARCH08.WEST.SPANDREL.C10.B00 | 29 | 180.34,76.69 | [工程推断·非史料] |
| 2886 | ARCH08.WEST.SPANDREL.C10.B01 | 24 | 149.20,54.38 | [工程推断·非史料] |
| 2887 | ARCH08.WEST.SPANDREL.C10.B02 | 29 | 180.12,101.09 | [工程推断·非史料] |
| 2888 | ARCH08.WEST.SPANDREL.C10.B06 | 29 | 102.88,115.77 | [工程推断·非史料] |
| 2889 | ARCH08.WEST.SPANDREL.C10.B07 | 24 | 149.17,76.72 | [工程推断·非史料] |
| 2890 | ARCH08.WEST.SPANDREL.C10.B08 | 29 | 180.00,115.77 | [工程推断·非史料] |
| 2891 | ARCH08.WEST.SPANDREL.C10.B09 | 24 | 0.00,113.36 | [工程推断·非史料] |
| 2892 | ARCH08.EAST.CORE.C13.B00 | 8 | 0.00,105.48 | [工程推断·非史料] |
| 2894 | ARCH08.EAST.CORE.C13.B02 | 7 | 0.00,70.53 | [工程推断·非史料] |
| 2895 | ARCH08.EAST.BACK.C11.B00 | 31 | 112.92,127.51 | [工程推断·非史料] |
| 2896 | ARCH08.EAST.BACK.C11.B01 | 32 | 193.66,20.74 | [工程推断·非史料] |
| 2897 | ARCH08.EAST.BACK.C11.B05 | 26 | 0.00,51.03 | [工程推断·非史料] |
| 2898 | ARCH08.EAST.SPANDREL.C11.B00 | 24 | 0.00,54.38 | [工程推断·非史料] |
| 2899 | ARCH08.EAST.SPANDREL.C11.B01 | 29 | 51.47,101.09 | [工程推断·非史料] |
| 2900 | ARCH08.EAST.SPANDREL.C11.B05 | 26 | 164.70,25.32 | [工程推断·非史料] |
| 2901 | ARCH08.WEST.BACK.C11.B00 | 31 | 135.26,127.51 | [工程推断·非史料] |
| 2902 | ARCH08.WEST.BACK.C11.B01 | 32 | 150.81,20.74 | [工程推断·非史料] |
| 2903 | ARCH08.WEST.BACK.C11.B05 | 26 | 60.80,51.03 | [工程推断·非史料] |
| 2904 | ARCH08.WEST.SPANDREL.C11.B00 | 24 | 99.62,32.04 | [工程推断·非史料] |
| 2905 | ARCH08.WEST.SPANDREL.C11.B01 | 29 | 102.93,101.09 | [工程推断·非史料] |
| 2906 | ARCH08.WEST.SPANDREL.C11.B05 | 26 | 30.40,51.03 | [工程推断·非史料] |
| 2907 | ARCH08.EAST.BACK.C12.B00 | 25 | 0.00,192.61 | [工程推断·非史料] |
| 2908 | ARCH08.EAST.BACK.C12.B01 | 33 | 19.32,103.96 | [工程推断·非史料] |
| 2910 | ARCH08.EAST.BACK.C12.B05 | 32 | 104.76,101.00 | [工程推断·非史料] |
| 2911 | ARCH08.EAST.BACK.C12.B06 | 26 | 135.18,0.00 | [工程推断·非史料] |
| 2912 | ARCH08.EAST.SPANDREL.C12.B00 | 25 | 179.94,166.70 | [工程推断·非史料] |
| 2913 | ARCH08.EAST.SPANDREL.C12.B01 | 25 | 0.00,64.22 | [工程推断·非史料] |
| 2915 | ARCH08.EAST.SPANDREL.C12.B05 | 25 | 0.00,88.52 | [工程推断·非史料] |
| 2916 | ARCH08.EAST.SPANDREL.C12.B06 | 26 | 102.24,0.00 | [工程推断·非史料] |
| 2917 | ARCH08.WEST.BACK.C12.B00 | 25 | 69.00,192.61 | [工程推断·非史料] |
| 2918 | ARCH08.WEST.BACK.C12.B01 | 33 | 197.75,87.62 | [工程推断·非史料] |
| 2920 | ARCH08.WEST.BACK.C12.B05 | 32 | 125.68,101.00 | [工程推断·非史料] |
| 2921 | ARCH08.WEST.BACK.C12.B06 | 26 | 0.00,25.32 | [工程推断·非史料] |
| 2922 | ARCH08.WEST.SPANDREL.C12.B00 | 25 | 34.50,192.61 | [工程推断·非史料] |
| 2923 | ARCH08.WEST.SPANDREL.C12.B01 | 25 | 49.34,64.22 | [工程推断·非史料] |
| 2924 | ARCH08.WEST.SPANDREL.C12.B05 | 25 | 98.65,88.52 | [工程推断·非史料] |
| 2925 | ARCH08.WEST.SPANDREL.C12.B06 | 26 | 168.12,0.00 | [工程推断·非史料] |
| 2926 | ARCH08.EAST.CORE.C14.B00 | 14 | 0.00,0.00 | [工程推断·非史料] |
| 2927 | ARCH08.EAST.CORE.C14.B02 | 12 | 0.00,138.05 | [工程推断·非史料] |
| 2928 | ARCH08.EAST.BACK.C13.B00 | 29 | 155.03,0.00 | [工程推断·非史料] |
| 2929 | ARCH08.EAST.BACK.C13.B01 | 30 | 50.62,20.17 | [工程推断·非史料] |
| 2930 | ARCH08.EAST.BACK.C13.B02 | 29 | 0.00,144.53 | [工程推断·非史料] |
| 2931 | ARCH08.EAST.BACK.C13.B03 | 32 | 149.55,41.48 | [工程推断·非史料] |
| 2932 | ARCH08.EAST.BACK.C13.B06 | 29 | 0.00,76.69 | [工程推断·非史料] |
| 2933 | ARCH08.EAST.BACK.C13.B07 | 26 | 58.96,102.85 | [工程推断·非史料] |
| 2934 | ARCH08.EAST.BACK.C13.B08 | 33 | 139.79,69.30 | [工程推断·非史料] |
| 2935 | ARCH08.EAST.SPANDREL.C13.B00 | 22 | 50.94,0.00 | [工程推断·非史料] |
| 2936 | ARCH08.EAST.SPANDREL.C13.B01 | 27 | 0.00,161.29 | [工程推断·非史料] |
| 2937 | ARCH08.EAST.SPANDREL.C13.B02 | 22 | 50.76,29.48 | [工程推断·非史料] |
| 2938 | ARCH08.EAST.SPANDREL.C13.B03 | 27 | 109.40,65.45 | [工程推断·非史料] |
| 2939 | ARCH08.EAST.SPANDREL.C13.B06 | 22 | 50.73,67.28 | [工程推断·非史料] |
| 2940 | ARCH08.EAST.SPANDREL.C13.B07 | 26 | 29.48,102.85 | [工程推断·非史料] |
| 2941 | ARCH08.EAST.SPANDREL.C13.B08 | 22 | 152.13,89.34 | [工程推断·非史料] |
| 2942 | ARCH08.WEST.BACK.C13.B00 | 29 | 180.85,0.00 | [工程推断·非史料] |
| 2943 | ARCH08.WEST.BACK.C13.B01 | 30 | 75.92,20.17 | [工程推断·非史料] |
| 2944 | ARCH08.WEST.BACK.C13.B02 | 29 | 25.65,144.53 | [工程推断·非史料] |
| 2945 | ARCH08.WEST.BACK.C13.B03 | 32 | 170.82,41.48 | [工程推断·非史料] |
| 2946 | ARCH08.WEST.BACK.C13.B06 | 29 | 154.85,51.24 | [工程推断·非史料] |
| 2947 | ARCH08.WEST.BACK.C13.B07 | 26 | 117.92,102.85 | [工程推断·非史料] |
| 2948 | ARCH08.WEST.BACK.C13.B08 | 33 | 159.70,69.30 | [工程推断·非史料] |
| 2949 | ARCH08.WEST.SPANDREL.C13.B00 | 22 | 101.70,0.00 | [工程推断·非史料] |
| 2950 | ARCH08.WEST.SPANDREL.C13.B01 | 27 | 26.75,161.29 | [工程推断·非史料] |
| 2951 | ARCH08.WEST.SPANDREL.C13.B02 | 22 | 101.50,29.48 | [工程推断·非史料] |
| 2952 | ARCH08.WEST.SPANDREL.C13.B03 | 27 | 136.43,65.45 | [工程推断·非史料] |
| 2953 | ARCH08.WEST.SPANDREL.C13.B06 | 22 | 152.17,67.28 | [工程推断·非史料] |
| 2954 | ARCH08.WEST.SPANDREL.C13.B07 | 26 | 88.44,102.85 | [工程推断·非史料] |
| 2955 | ARCH08.WEST.SPANDREL.C13.B08 | 22 | 50.72,89.34 | [工程推断·非史料] |
| 2956 | ARCH08.EAST.BACK.C14.B00 | 33 | 59.95,69.30 | [工程推断·非史料] |
| 2957 | ARCH08.EAST.BACK.C14.B01 | 33 | 101.56,50.17 | [工程推断·非史料] |
| 2958 | ARCH08.EAST.BACK.C14.B02 | 31 | 132.39,188.33 | [工程推断·非史料] |
| 2959 | ARCH08.EAST.BACK.C14.B03 | 31 | 111.15,167.95 | [工程推断·非史料] |
| 2960 | ARCH08.EAST.BACK.C14.B04 | 31 | 161.35,64.62 | [工程推断·非史料] |
| 2961 | ARCH08.EAST.BACK.C14.B05 | 29 | 102.12,181.31 | [工程推断·非史料] |
| 2962 | ARCH08.EAST.BACK.C14.B06 | 33 | 55.04,131.82 | [工程推断·非史料] |
| 2963 | ARCH08.EAST.BACK.C14.B07 | 32 | 196.94,0.00 | [工程推断·非史料] |
| 2964 | ARCH08.EAST.BACK.C14.B08 | 31 | 23.65,22.49 | [工程推断·非史料] |
| 2965 | ARCH08.EAST.BACK.C14.B09 | 31 | 114.10,92.90 | [工程推断·非史料] |
| 2966 | ARCH08.EAST.BACK.C14.B10 | 28 | 104.55,85.58 | [工程推断·非史料] |
| 2967 | ARCH08.EAST.SPANDREL.C14.B00 | 27 | 160.10,161.29 | [工程推断·非史料] |
| 2968 | ARCH08.EAST.SPANDREL.C14.B01 | 22 | 50.25,171.80 | [工程推断·非史料] |
| 2969 | ARCH08.EAST.SPANDREL.C14.B02 | 28 | 105.14,0.00 | [工程推断·非史料] |
| 2970 | ARCH08.EAST.SPANDREL.C14.B03 | 22 | 50.25,187.94 | [工程推断·非史料] |
| 2971 | ARCH08.EAST.SPANDREL.C14.B04 | 28 | 0.00,22.02 | [工程推断·非史料] |
| 2972 | ARCH08.EAST.SPANDREL.C14.B05 | 23 | 0.00,0.00 | [工程推断·非史料] |
| 2973 | ARCH08.EAST.SPANDREL.C14.B06 | 28 | 104.92,22.02 | [工程推断·非史料] |
| 2974 | ARCH08.EAST.SPANDREL.C14.B07 | 23 | 0.00,25.52 | [工程推断·非史料] |
| 2975 | ARCH08.EAST.SPANDREL.C14.B08 | 28 | 52.42,38.62 | [工程推断·非史料] |
| 2976 | ARCH08.EAST.SPANDREL.C14.B09 | 23 | 0.00,46.26 | [工程推断·非史料] |
| 2977 | ARCH08.EAST.SPANDREL.C14.B10 | 27 | 159.10,179.19 | [工程推断·非史料] |
| 2978 | ARCH08.WEST.BACK.C14.B00 | 33 | 79.91,69.30 | [工程推断·非史料] |
| 2979 | ARCH08.WEST.BACK.C14.B01 | 33 | 121.66,50.17 | [工程推断·非史料] |
| 2980 | ARCH08.WEST.BACK.C14.B02 | 31 | 154.41,188.33 | [工程推断·非史料] |
| 2981 | ARCH08.WEST.BACK.C14.B03 | 31 | 133.26,167.95 | [工程推断·非史料] |
| 2982 | ARCH08.WEST.BACK.C14.B04 | 31 | 184.29,64.62 | [工程推断·非史料] |
| 2983 | ARCH08.WEST.BACK.C14.B05 | 29 | 127.64,181.31 | [工程推断·非史料] |
| 2984 | ARCH08.WEST.BACK.C14.B06 | 33 | 73.29,131.82 | [工程推断·非史料] |
| 2985 | ARCH08.WEST.BACK.C14.B07 | 32 | 21.57,20.74 | [工程推断·非史料] |
| 2986 | ARCH08.WEST.BACK.C14.B08 | 31 | 47.13,22.49 | [工程推断·非史料] |
| 2987 | ARCH08.WEST.BACK.C14.B09 | 31 | 136.84,92.90 | [工程推断·非史料] |
| 2988 | ARCH08.WEST.BACK.C14.B10 | 28 | 130.68,85.58 | [工程推断·非史料] |
| 2989 | ARCH08.WEST.SPANDREL.C14.B00 | 27 | 107.00,161.29 | [工程推断·非史料] |
| 2990 | ARCH08.WEST.SPANDREL.C14.B01 | 22 | 100.50,171.80 | [工程推断·非史料] |
| 2991 | ARCH08.WEST.SPANDREL.C14.B02 | 28 | 131.38,0.00 | [工程推断·非史料] |
| 2992 | ARCH08.WEST.SPANDREL.C14.B03 | 22 | 100.48,187.94 | [工程推断·非史料] |
| 2993 | ARCH08.WEST.SPANDREL.C14.B04 | 28 | 52.46,22.02 | [工程推断·非史料] |
| 2994 | ARCH08.WEST.SPANDREL.C14.B05 | 23 | 50.23,0.00 | [工程推断·非史料] |
| 2995 | ARCH08.WEST.SPANDREL.C14.B06 | 28 | 131.14,22.02 | [工程推断·非史料] |
| 2996 | ARCH08.WEST.SPANDREL.C14.B07 | 23 | 100.43,25.52 | [工程推断·非史料] |
| 2997 | ARCH08.WEST.SPANDREL.C14.B08 | 28 | 0.00,38.62 | [工程推断·非史料] |
| 2998 | ARCH08.WEST.SPANDREL.C14.B09 | 23 | 50.21,46.26 | [工程推断·非史料] |
| 2999 | ARCH08.WEST.SPANDREL.C14.B10 | 27 | 106.09,179.19 | [工程推断·非史料] |
| 3000 | ARCH08.EAST.CORE.C15.B00 | 19 | 0.00,131.96 | [工程推断·非史料] |
| 3001 | ARCH08.EAST.CORE.C15.B01 | 18 | 0.00,0.00 | [工程推断·非史料] |
| 3002 | ARCH08.EAST.CORE.C15.B02 | 16 | 0.00,131.66 | [工程推断·非史料] |
| 3003 | ARCH08.EAST.BACK.C15.B00 | 31 | 0.00,109.50 | [工程推断·非史料] |
| 3004 | ARCH08.EAST.BACK.C15.B02 | 31 | 133.96,149.20 | [工程推断·非史料] |
| 3005 | ARCH08.EAST.BACK.C15.B05 | 28 | 77.53,184.87 | [工程推断·非史料] |
| 3006 | ARCH08.EAST.SPANDREL.C15.B00 | 25 | 0.00,107.52 | [工程推断·非史料] |
| 3007 | ARCH08.EAST.SPANDREL.C15.B02 | 25 | 0.00,56.12 | [工程推断·非史料] |
| 3008 | ARCH08.EAST.SPANDREL.C15.B05 | 28 | 51.69,184.87 | [工程推断·非史料] |
| 3009 | ARCH08.WEST.BACK.C15.B00 | 31 | 45.36,109.50 | [工程推断·非史料] |
| 3010 | ARCH08.WEST.BACK.C15.B02 | 31 | 156.26,149.20 | [工程推断·非史料] |
| 3011 | ARCH08.WEST.BACK.C15.B05 | 28 | 129.21,184.87 | [工程推断·非史料] |
| 3012 | ARCH08.WEST.SPANDREL.C15.B00 | 25 | 98.31,107.52 | [工程推断·非史料] |
| 3013 | ARCH08.WEST.SPANDREL.C15.B02 | 25 | 49.36,56.12 | [工程推断·非史料] |
| 3014 | ARCH08.WEST.SPANDREL.C15.B05 | 28 | 103.37,184.87 | [工程推断·非史料] |
| 3015 | ARCH08.EAST.BACK.C15.B01 | 32 | 21.42,41.48 | [工程推断·非史料] |
| 3016 | ARCH08.EAST.BACK.C15.B04 | 31 | 181.34,109.50 | [工程推断·非史料] |
| 3017 | ARCH08.EAST.BACK.C15.B06 | 30 | 120.65,186.35 | [工程推断·非史料] |
| 3018 | ARCH08.EAST.BACK.C15.B07 | 30 | 99.77,82.14 | [工程推断·非史料] |
| 3019 | ARCH08.EAST.BACK.C15.B08 | 30 | 97.04,162.72 | [工程推断·非史料] |
| 3020 | ARCH08.EAST.BACK.C15.B09 | 31 | 46.61,43.65 | [工程推断·非史料] |
| 3021 | ARCH08.EAST.BACK.C15.B10 | 32 | 63.46,80.12 | [工程推断·非史料] |
| 3022 | ARCH08.EAST.SPANDREL.C15.B01 | 30 | 151.83,20.17 | [工程推断·非史料] |
| 3023 | ARCH08.EAST.SPANDREL.C15.B04 | 25 | 0.00,23.78 | [工程推断·非史料] |
| 3024 | ARCH08.EAST.SPANDREL.C15.B06 | 23 | 99.80,187.58 | [工程推断·非史料] |
| 3025 | ARCH08.EAST.SPANDREL.C15.B07 | 28 | 155.65,169.97 | [工程推断·非史料] |
| 3026 | ARCH08.EAST.SPANDREL.C15.B08 | 24 | 0.00,0.00 | [工程推断·非史料] |
| 3027 | ARCH08.EAST.SPANDREL.C15.B09 | 29 | 51.68,0.00 | [工程推断·非史料] |
| 3028 | ARCH08.EAST.SPANDREL.C15.B10 | 24 | 99.68,0.00 | [工程推断·非史料] |
| 3029 | ARCH08.WEST.BACK.C15.B01 | 32 | 64.20,41.48 | [工程推断·非史料] |
| 3030 | ARCH08.WEST.BACK.C15.B04 | 31 | 0.00,127.51 | [工程推断·非史料] |
| 3031 | ARCH08.WEST.BACK.C15.B06 | 30 | 72.48,186.35 | [工程推断·非史料] |
| 3032 | ARCH08.WEST.BACK.C15.B07 | 30 | 124.61,82.14 | [工程推断·非史料] |
| 3033 | ARCH08.WEST.BACK.C15.B08 | 30 | 121.26,162.72 | [工程推断·非史料] |
| 3034 | ARCH08.WEST.BACK.C15.B09 | 31 | 69.77,43.65 | [工程推断·非史料] |
| 3035 | ARCH08.WEST.BACK.C15.B10 | 32 | 84.48,80.12 | [工程推断·非史料] |
| 3036 | ARCH08.WEST.SPANDREL.C15.B01 | 30 | 177.10,20.17 | [工程推断·非史料] |
| 3037 | ARCH08.WEST.SPANDREL.C15.B04 | 25 | 49.58,23.78 | [工程推断·非史料] |
| 3038 | ARCH08.WEST.SPANDREL.C15.B06 | 23 | 149.65,187.58 | [工程推断·非史料] |
| 3039 | ARCH08.WEST.SPANDREL.C15.B07 | 28 | 181.50,169.97 | [工程推断·非史料] |
| 3040 | ARCH08.WEST.SPANDREL.C15.B08 | 23 | 99.69,199.38 | [工程推断·非史料] |
| 3041 | ARCH08.WEST.SPANDREL.C15.B09 | 29 | 77.52,0.00 | [工程推断·非史料] |
| 3042 | ARCH08.WEST.SPANDREL.C15.B10 | 24 | 149.52,0.00 | [工程推断·非史料] |
| 3043 | ARCH08.EAST.BACK.C15.B03 | 31 | 183.26,74.32 | [工程推断·非史料] |
| 3044 | ARCH08.EAST.SPANDREL.C15.B03 | 29 | 50.99,205.46 | [工程推断·非史料] |
| 3045 | ARCH08.WEST.BACK.C15.B03 | 31 | 0.00,92.90 | [工程推断·非史料] |
| 3046 | ARCH08.WEST.SPANDREL.C15.B03 | 29 | 76.43,205.46 | [工程推断·非史料] |

### S400 ARCH09.FILL (events 3047-3286)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 3070 | ARCH09.EAST.BACK.C07.B06 | 31 | 0.00,188.33 | [工程推断·非史料] |
| 3072 | ARCH09.EAST.SPANDREL.C07.B06 | 20 | 0.00,163.83 | [工程推断·非史料] |
| 3074 | ARCH09.WEST.BACK.C07.B06 | 31 | 22.08,188.33 | [工程推断·非史料] |
| 3076 | ARCH09.WEST.SPANDREL.C07.B06 | 20 | 157.53,146.36 | [工程推断·非史料] |
| 3079 | ARCH09.EAST.BACK.C08.B00 | 31 | 67.92,127.51 | [工程推断·非史料] |
| 3081 | ARCH09.EAST.SPANDREL.C08.B00 | 26 | 175.30,129.56 | [工程推断·非史料] |
| 3083 | ARCH09.WEST.BACK.C08.B00 | 31 | 90.42,127.51 | [工程推断·非史料] |
| 3085 | ARCH09.WEST.SPANDREL.C08.B00 | 26 | 0.00,156.27 | [工程推断·非史料] |
| 3090 | ARCH09.EAST.BACK.C09.B00 | 30 | 125.71,62.74 | [工程推断·非史料] |
| 3091 | ARCH09.EAST.BACK.C09.B01 | 32 | 169.77,62.22 | [工程推断·非史料] |
| 3092 | ARCH09.EAST.BACK.C09.B06 | 26 | 34.50,0.00 | [工程推断·非史料] |
| 3093 | ARCH09.EAST.SPANDREL.C09.B00 | 21 | 51.41,51.77 | [工程推断·非史料] |
| 3094 | ARCH09.EAST.SPANDREL.C09.B01 | 27 | 164.69,21.98 | [工程推断·非史料] |
| 3095 | ARCH09.EAST.SPANDREL.C09.B06 | 21 | 154.21,51.77 | [工程推断·非史料] |
| 3096 | ARCH09.WEST.BACK.C09.B00 | 30 | 100.70,62.74 | [工程推断·非史料] |
| 3097 | ARCH09.WEST.BACK.C09.B01 | 32 | 148.61,62.22 | [工程推断·非史料] |
| 3098 | ARCH09.WEST.BACK.C09.B06 | 26 | 68.37,0.00 | [工程推断·非史料] |
| 3099 | ARCH09.WEST.SPANDREL.C09.B00 | 21 | 102.81,51.77 | [工程推断·非史料] |
| 3100 | ARCH09.WEST.SPANDREL.C09.B01 | 27 | 192.09,21.98 | [工程推断·非史料] |
| 3101 | ARCH09.WEST.SPANDREL.C09.B06 | 21 | 0.00,85.64 | [工程推断·非史料] |
| 3102 | ARCH09.EAST.BACK.C10.B00 | 32 | 166.55,121.88 | [工程推断·非史料] |
| 3103 | ARCH09.EAST.BACK.C10.B01 | 30 | 195.13,125.36 | [工程推断·非史料] |
| 3104 | ARCH09.EAST.BACK.C10.B02 | 30 | 24.83,95.16 | [工程推断·非史料] |
| 3105 | ARCH09.EAST.BACK.C10.B03 | 33 | 173.75,103.96 | [工程推断·非史料] |
| 3106 | ARCH09.EAST.BACK.C10.B07 | 29 | 25.50,205.46 | [工程推断·非史料] |
| 3107 | ARCH09.EAST.BACK.C10.B08 | 33 | 57.97,103.96 | [工程推断·非史料] |
| 3108 | ARCH09.EAST.BACK.C10.B09 | 30 | 168.82,186.35 | [工程推断·非史料] |
| 3109 | ARCH09.EAST.SPANDREL.C10.B00 | 29 | 51.41,126.21 | [工程推断·非史料] |
| 3110 | ARCH09.EAST.SPANDREL.C10.B01 | 24 | 0.00,132.06 | [工程推断·非史料] |
| 3111 | ARCH09.EAST.SPANDREL.C10.B02 | 29 | 179.91,126.21 | [工程推断·非史料] |
| 3112 | ARCH09.EAST.SPANDREL.C10.B03 | 24 | 99.40,166.98 | [工程推断·非史料] |
| 3113 | ARCH09.EAST.SPANDREL.C10.B07 | 24 | 0.00,181.66 | [工程推断·非史料] |
| 3114 | ARCH09.EAST.SPANDREL.C10.B08 | 29 | 102.81,126.21 | [工程推断·非史料] |
| 3115 | ARCH09.EAST.SPANDREL.C10.B09 | 24 | 99.41,113.36 | [工程推断·非史料] |
| 3116 | ARCH09.WEST.BACK.C10.B00 | 32 | 145.83,121.88 | [工程推断·非史料] |
| 3117 | ARCH09.WEST.BACK.C10.B01 | 30 | 0.00,146.70 | [工程推断·非史料] |
| 3118 | ARCH09.WEST.BACK.C10.B02 | 30 | 0.00,95.16 | [工程推断·非史料] |
| 3119 | ARCH09.WEST.BACK.C10.B03 | 33 | 192.85,103.96 | [工程推断·非史料] |
| 3120 | ARCH09.WEST.BACK.C10.B07 | 29 | 0.00,205.46 | [工程推断·非史料] |
| 3121 | ARCH09.WEST.BACK.C10.B08 | 33 | 77.28,103.96 | [工程推断·非史料] |
| 3122 | ARCH09.WEST.BACK.C10.B09 | 30 | 192.65,186.35 | [工程推断·非史料] |
| 3123 | ARCH09.WEST.SPANDREL.C10.B00 | 29 | 77.11,126.21 | [工程推断·非史料] |
| 3124 | ARCH09.WEST.SPANDREL.C10.B01 | 24 | 49.70,132.06 | [工程推断·非史料] |
| 3125 | ARCH09.WEST.SPANDREL.C10.B02 | 29 | 154.21,126.21 | [工程推断·非史料] |
| 3126 | ARCH09.WEST.SPANDREL.C10.B03 | 24 | 149.10,166.98 | [工程推断·非史料] |
| 3127 | ARCH09.WEST.SPANDREL.C10.B07 | 24 | 49.70,181.66 | [工程推断·非史料] |
| 3128 | ARCH09.WEST.SPANDREL.C10.B08 | 29 | 128.51,126.21 | [工程推断·非史料] |
| 3129 | ARCH09.WEST.SPANDREL.C10.B09 | 24 | 149.11,113.36 | [工程推断·非史料] |
| 3130 | ARCH09.EAST.CORE.C13.B00 | 6 | 0.00,105.99 | [工程推断·非史料] |
| 3132 | ARCH09.EAST.CORE.C13.B02 | 7 | 0.00,0.00 | [工程推断·非史料] |
| 3133 | ARCH09.EAST.BACK.C11.B00 | 25 | 110.10,166.70 | [工程推断·非史料] |
| 3135 | ARCH09.EAST.BACK.C11.B04 | 33 | 0.00,113.66 | [工程推断·非史料] |
| 3136 | ARCH09.EAST.BACK.C11.B05 | 26 | 140.06,183.27 | [工程推断·非史料] |
| 3137 | ARCH09.EAST.SPANDREL.C11.B00 | 24 | 149.10,132.06 | [工程推断·非史料] |
| 3138 | ARCH09.EAST.SPANDREL.C11.B04 | 24 | 0.00,166.98 | [工程推断·非史料] |
| 3139 | ARCH09.EAST.SPANDREL.C11.B05 | 26 | 112.24,183.27 | [工程推断·非史料] |
| 3140 | ARCH09.WEST.BACK.C11.B00 | 25 | 145.02,166.70 | [工程推断·非史料] |
| 3142 | ARCH09.WEST.BACK.C11.B04 | 33 | 19.06,113.66 | [工程推断·非史料] |
| 3143 | ARCH09.WEST.BACK.C11.B05 | 27 | 0.00,0.00 | [工程推断·非史料] |
| 3144 | ARCH09.WEST.SPANDREL.C11.B00 | 24 | 99.40,132.06 | [工程推断·非史料] |
| 3145 | ARCH09.WEST.SPANDREL.C11.B04 | 24 | 49.70,166.98 | [工程推断·非史料] |
| 3146 | ARCH09.WEST.SPANDREL.C11.B05 | 26 | 167.88,183.27 | [工程推断·非史料] |
| 3147 | ARCH09.EAST.BACK.C12.B00 | 25 | 37.46,140.80 | [工程推断·非史料] |
| 3148 | ARCH09.EAST.BACK.C12.B01 | 32 | 127.43,62.22 | [工程推断·非史料] |
| 3150 | ARCH09.EAST.BACK.C12.B05 | 33 | 61.14,50.17 | [工程推断·非史料] |
| 3151 | ARCH09.EAST.BACK.C12.B06 | 25 | 0.00,166.70 | [工程推断·非史料] |
| 3152 | ARCH09.EAST.SPANDREL.C12.B00 | 25 | 0.00,140.80 | [工程推断·非史料] |
| 3153 | ARCH09.EAST.SPANDREL.C12.B01 | 23 | 0.00,187.58 | [工程推断·非史料] |
| 3155 | ARCH09.EAST.SPANDREL.C12.B05 | 23 | 99.95,176.00 | [工程推断·非史料] |
| 3156 | ARCH09.EAST.SPANDREL.C12.B06 | 25 | 149.84,140.80 | [工程推断·非史料] |
| 3157 | ARCH09.WEST.BACK.C12.B00 | 25 | 112.38,140.80 | [工程推断·非史料] |
| 3158 | ARCH09.WEST.BACK.C12.B01 | 32 | 106.25,62.22 | [工程推断·非史料] |
| 3160 | ARCH09.WEST.BACK.C12.B05 | 33 | 81.35,50.17 | [工程推断·非史料] |
| 3161 | ARCH09.WEST.BACK.C12.B06 | 25 | 73.40,166.70 | [工程推断·非史料] |
| 3162 | ARCH09.WEST.SPANDREL.C12.B00 | 25 | 74.92,140.80 | [工程推断·非史料] |
| 3163 | ARCH09.WEST.SPANDREL.C12.B01 | 23 | 49.90,187.58 | [工程推断·非史料] |
| 3164 | ARCH09.WEST.SPANDREL.C12.B05 | 23 | 149.85,176.00 | [工程推断·非史料] |
| 3165 | ARCH09.WEST.SPANDREL.C12.B06 | 25 | 36.70,166.70 | [工程推断·非史料] |
| 3166 | ARCH09.EAST.CORE.C14.B00 | 11 | 0.00,134.68 | [工程推断·非史料] |
| 3167 | ARCH09.EAST.CORE.C14.B02 | 12 | 0.00,0.00 | [工程推断·非史料] |
| 3168 | ARCH09.EAST.BACK.C13.B00 | 33 | 76.03,113.66 | [工程推断·非史料] |
| 3169 | ARCH09.EAST.BACK.C13.B01 | 26 | 147.40,76.74 | [工程推断·非史料] |
| 3170 | ARCH09.EAST.BACK.C13.B02 | 31 | 22.30,167.95 | [工程推断·非史料] |
| 3171 | ARCH09.EAST.BACK.C13.B04 | 26 | 28.49,156.27 | [工程推断·非史料] |
| 3172 | ARCH09.EAST.BACK.C13.B05 | 31 | 66.85,167.95 | [工程推断·非史料] |
| 3173 | ARCH09.EAST.BACK.C13.B06 | 31 | 95.12,0.00 | [工程推断·非史料] |
| 3174 | ARCH09.EAST.BACK.C13.B07 | 28 | 51.92,169.97 | [工程推断·非史料] |
| 3175 | ARCH09.EAST.SPANDREL.C13.B00 | 23 | 100.39,90.46 | [工程推断·非史料] |
| 3176 | ARCH09.EAST.SPANDREL.C13.B01 | 26 | 117.92,76.74 | [工程推断·非史料] |
| 3177 | ARCH09.EAST.SPANDREL.C13.B02 | 23 | 100.22,115.98 | [工程推断·非史料] |
| 3178 | ARCH09.EAST.SPANDREL.C13.B04 | 23 | 0.00,136.36 | [工程推断·非史料] |
| 3179 | ARCH09.EAST.SPANDREL.C13.B05 | 28 | 104.45,98.65 | [工程推断·非史料] |
| 3180 | ARCH09.EAST.SPANDREL.C13.B06 | 23 | 0.00,115.98 | [工程推断·非史料] |
| 3181 | ARCH09.EAST.SPANDREL.C13.B07 | 28 | 78.34,98.65 | [工程推断·非史料] |
| 3182 | ARCH09.WEST.BACK.C13.B00 | 33 | 94.82,113.66 | [工程推断·非史料] |
| 3183 | ARCH09.WEST.BACK.C13.B01 | 26 | 0.00,102.85 | [工程推断·非史料] |
| 3184 | ARCH09.WEST.BACK.C13.B02 | 31 | 44.58,167.95 | [工程推断·非史料] |
| 3185 | ARCH09.WEST.BACK.C13.B04 | 26 | 56.55,156.27 | [工程推断·非史料] |
| 3186 | ARCH09.WEST.BACK.C13.B05 | 31 | 89.00,167.95 | [工程推断·非史料] |
| 3187 | ARCH09.WEST.BACK.C13.B06 | 31 | 118.90,0.00 | [工程推断·非史料] |
| 3188 | ARCH09.WEST.BACK.C13.B07 | 28 | 77.87,169.97 | [工程推断·非史料] |
| 3189 | ARCH09.WEST.SPANDREL.C13.B00 | 23 | 150.50,90.46 | [工程推断·非史料] |
| 3190 | ARCH09.WEST.SPANDREL.C13.B01 | 26 | 176.88,76.74 | [工程推断·非史料] |
| 3191 | ARCH09.WEST.SPANDREL.C13.B02 | 23 | 150.33,115.98 | [工程推断·非史料] |
| 3192 | ARCH09.WEST.SPANDREL.C13.B04 | 23 | 50.11,136.36 | [工程推断·非史料] |
| 3193 | ARCH09.WEST.SPANDREL.C13.B05 | 28 | 130.56,98.65 | [工程推断·非史料] |
| 3194 | ARCH09.WEST.SPANDREL.C13.B06 | 23 | 50.11,115.98 | [工程推断·非史料] |
| 3195 | ARCH09.WEST.SPANDREL.C13.B07 | 28 | 52.22,98.65 | [工程推断·非史料] |
| 3196 | ARCH09.EAST.BACK.C14.B00 | 33 | 113.62,113.66 | [工程推断·非史料] |
| 3197 | ARCH09.EAST.BACK.C14.B01 | 33 | 36.71,131.82 | [工程推断·非史料] |
| 3198 | ARCH09.EAST.BACK.C14.B02 | 31 | 117.57,22.49 | [工程推断·非史料] |
| 3199 | ARCH09.EAST.BACK.C14.B03 | 32 | 106.99,41.48 | [工程推断·非史料] |
| 3200 | ARCH09.EAST.BACK.C14.B04 | 31 | 68.54,92.90 | [工程推断·非史料] |
| 3201 | ARCH09.EAST.BACK.C14.B05 | 29 | 51.08,181.31 | [工程推断·非史料] |
| 3202 | ARCH09.EAST.BACK.C14.B06 | 32 | 147.56,80.12 | [工程推断·非史料] |
| 3203 | ARCH09.EAST.BACK.C14.B07 | 28 | 103.83,169.97 | [工程推断·非史料] |
| 3204 | ARCH09.EAST.BACK.C14.B08 | 32 | 22.02,0.00 | [工程推断·非史料] |
| 3205 | ARCH09.EAST.BACK.C14.B09 | 30 | 50.01,82.14 | [工程推断·非史料] |
| 3206 | ARCH09.EAST.BACK.C14.B10 | 33 | 0.00,87.62 | [工程推断·非史料] |
| 3207 | ARCH09.EAST.SPANDREL.C14.B00 | 28 | 183.43,38.62 | [工程推断·非史料] |
| 3208 | ARCH09.EAST.SPANDREL.C14.B01 | 23 | 0.00,56.70 | [工程推断·非史料] |
| 3209 | ARCH09.EAST.SPANDREL.C14.B02 | 28 | 0.00,62.10 | [工程推断·非史料] |
| 3210 | ARCH09.EAST.SPANDREL.C14.B03 | 23 | 100.39,69.72 | [工程推断·非史料] |
| 3211 | ARCH09.EAST.SPANDREL.C14.B04 | 28 | 157.17,62.10 | [工程推断·非史料] |
| 3212 | ARCH09.EAST.SPANDREL.C14.B05 | 23 | 50.19,90.46 | [工程推断·非史料] |
| 3213 | ARCH09.EAST.SPANDREL.C14.B06 | 28 | 104.78,62.10 | [工程推断·非史料] |
| 3214 | ARCH09.EAST.SPANDREL.C14.B07 | 23 | 0.00,69.72 | [工程推断·非史料] |
| 3215 | ARCH09.EAST.SPANDREL.C14.B08 | 28 | 52.39,62.10 | [工程推断·非史料] |
| 3216 | ARCH09.EAST.SPANDREL.C14.B09 | 23 | 150.59,56.70 | [工程推断·非史料] |
| 3217 | ARCH09.EAST.SPANDREL.C14.B10 | 28 | 104.84,38.62 | [工程推断·非史料] |
| 3218 | ARCH09.WEST.BACK.C14.B00 | 33 | 132.32,113.66 | [工程推断·非史料] |
| 3219 | ARCH09.WEST.BACK.C14.B01 | 33 | 18.38,131.82 | [工程推断·非史料] |
| 3220 | ARCH09.WEST.BACK.C14.B02 | 31 | 141.05,22.49 | [工程推断·非史料] |
| 3221 | ARCH09.WEST.BACK.C14.B03 | 32 | 128.27,41.48 | [工程推断·非史料] |
| 3222 | ARCH09.WEST.BACK.C14.B04 | 31 | 91.32,92.90 | [工程推断·非史料] |
| 3223 | ARCH09.WEST.BACK.C14.B05 | 29 | 76.60,181.31 | [工程推断·非史料] |
| 3224 | ARCH09.WEST.BACK.C14.B06 | 32 | 168.57,80.12 | [工程推断·非史料] |
| 3225 | ARCH09.WEST.BACK.C14.B07 | 28 | 129.74,169.97 | [工程推断·非史料] |
| 3226 | ARCH09.WEST.BACK.C14.B08 | 32 | 44.04,0.00 | [工程推断·非史料] |
| 3227 | ARCH09.WEST.BACK.C14.B09 | 30 | 74.89,82.14 | [工程推断·非史料] |
| 3228 | ARCH09.WEST.BACK.C14.B10 | 33 | 19.88,87.62 | [工程推断·非史料] |
| 3229 | ARCH09.WEST.SPANDREL.C14.B00 | 28 | 157.23,38.62 | [工程推断·非史料] |
| 3230 | ARCH09.WEST.SPANDREL.C14.B01 | 23 | 50.20,56.70 | [工程推断·非史料] |
| 3231 | ARCH09.WEST.SPANDREL.C14.B02 | 28 | 26.19,62.10 | [工程推断·非史料] |
| 3232 | ARCH09.WEST.SPANDREL.C14.B03 | 23 | 150.58,69.72 | [工程推断·非史料] |
| 3233 | ARCH09.WEST.SPANDREL.C14.B04 | 28 | 183.36,62.10 | [工程推断·非史料] |
| 3234 | ARCH09.WEST.SPANDREL.C14.B05 | 23 | 0.00,90.46 | [工程推断·非史料] |
| 3235 | ARCH09.WEST.SPANDREL.C14.B06 | 28 | 130.97,62.10 | [工程推断·非史料] |
| 3236 | ARCH09.WEST.SPANDREL.C14.B07 | 23 | 50.19,69.72 | [工程推断·非史料] |
| 3237 | ARCH09.WEST.SPANDREL.C14.B08 | 28 | 78.58,62.10 | [工程推断·非史料] |
| 3238 | ARCH09.WEST.SPANDREL.C14.B09 | 23 | 100.39,56.70 | [工程推断·非史料] |
| 3239 | ARCH09.WEST.SPANDREL.C14.B10 | 28 | 131.03,38.62 | [工程推断·非史料] |
| 3240 | ARCH09.EAST.CORE.C15.B00 | 17 | 0.00,70.53 | [工程推断·非史料] |
| 3241 | ARCH09.EAST.CORE.C15.B01 | 17 | 0.00,0.00 | [工程推断·非史料] |
| 3242 | ARCH09.EAST.CORE.C15.B02 | 17 | 0.00,141.07 | [工程推断·非史料] |
| 3243 | ARCH09.EAST.BACK.C15.B00 | 30 | 50.53,38.07 | [工程推断·非史料] |
| 3244 | ARCH09.EAST.BACK.C15.B04 | 28 | 78.86,0.00 | [工程推断·非史料] |
| 3245 | ARCH09.EAST.BACK.C15.B05 | 29 | 0.00,181.31 | [工程推断·非史料] |
| 3246 | ARCH09.EAST.BACK.C15.B08 | 32 | 66.06,0.00 | [工程推断·非史料] |
| 3247 | ARCH09.EAST.BACK.C15.B09 | 33 | 38.12,113.66 | [工程推断·非史料] |
| 3248 | ARCH09.EAST.BACK.C15.B10 | 31 | 139.25,43.65 | [工程推断·非史料] |
| 3249 | ARCH09.EAST.SPANDREL.C15.B00 | 22 | 100.56,154.40 | [工程推断·非史料] |
| 3250 | ARCH09.EAST.SPANDREL.C15.B04 | 22 | 50.71,109.72 | [工程推断·非史料] |
| 3251 | ARCH09.EAST.SPANDREL.C15.B05 | 27 | 0.00,194.27 | [工程推断·非史料] |
| 3252 | ARCH09.EAST.SPANDREL.C15.B08 | 22 | 151.02,132.06 | [工程推断·非史料] |
| 3253 | ARCH09.EAST.SPANDREL.C15.B09 | 28 | 0.00,0.00 | [工程推断·非史料] |
| 3254 | ARCH09.EAST.SPANDREL.C15.B10 | 22 | 150.82,154.40 | [工程推断·非史料] |
| 3255 | ARCH09.WEST.BACK.C15.B00 | 30 | 75.79,38.07 | [工程推断·非史料] |
| 3256 | ARCH09.WEST.BACK.C15.B04 | 28 | 52.58,0.00 | [工程推断·非史料] |
| 3257 | ARCH09.WEST.BACK.C15.B05 | 29 | 25.54,181.31 | [工程推断·非史料] |
| 3258 | ARCH09.WEST.BACK.C15.B08 | 32 | 87.90,0.00 | [工程推断·非史料] |
| 3259 | ARCH09.WEST.BACK.C15.B09 | 33 | 57.07,113.66 | [工程推断·非史料] |
| 3260 | ARCH09.WEST.BACK.C15.B10 | 31 | 162.34,43.65 | [工程推断·非史料] |
| 3261 | ARCH09.WEST.SPANDREL.C15.B00 | 22 | 50.31,154.40 | [工程推断·非史料] |
| 3262 | ARCH09.WEST.SPANDREL.C15.B04 | 22 | 101.07,109.72 | [工程推断·非史料] |
| 3263 | ARCH09.WEST.SPANDREL.C15.B05 | 27 | 26.36,194.27 | [工程推断·非史料] |
| 3264 | ARCH09.WEST.SPANDREL.C15.B08 | 22 | 0.00,154.40 | [工程推断·非史料] |
| 3265 | ARCH09.WEST.SPANDREL.C15.B09 | 28 | 26.29,0.00 | [工程推断·非史料] |
| 3266 | ARCH09.WEST.SPANDREL.C15.B10 | 22 | 0.00,171.80 | [工程推断·非史料] |
| 3267 | ARCH09.EAST.BACK.C15.B01 | 31 | 137.54,74.32 | [工程推断·非史料] |
| 3268 | ARCH09.EAST.BACK.C15.B02 | 28 | 104.28,119.53 | [工程推断·非史料] |
| 3269 | ARCH09.EAST.BACK.C15.B03 | 30 | 49.18,116.20 | [工程推断·非史料] |
| 3270 | ARCH09.EAST.BACK.C15.B06 | 31 | 157.60,127.51 | [工程推断·非史料] |
| 3271 | ARCH09.EAST.BACK.C15.B07 | 28 | 156.67,98.65 | [工程推断·非史料] |
| 3272 | ARCH09.EAST.SPANDREL.C15.B01 | 27 | 158.07,194.27 | [工程推断·非史料] |
| 3273 | ARCH09.EAST.SPANDREL.C15.B02 | 22 | 50.34,132.06 | [工程推断·非史料] |
| 3274 | ARCH09.EAST.SPANDREL.C15.B03 | 27 | 52.72,194.27 | [工程推断·非史料] |
| 3275 | ARCH09.EAST.SPANDREL.C15.B06 | 22 | 0.00,132.06 | [工程推断·非史料] |
| 3276 | ARCH09.EAST.SPANDREL.C15.B07 | 27 | 105.43,194.27 | [工程推断·非史料] |
| 3277 | ARCH09.WEST.BACK.C15.B01 | 31 | 160.40,74.32 | [工程推断·非史料] |
| 3278 | ARCH09.WEST.BACK.C15.B02 | 28 | 130.34,119.53 | [工程推断·非史料] |
| 3279 | ARCH09.WEST.BACK.C15.B03 | 30 | 73.60,116.20 | [工程推断·非史料] |
| 3280 | ARCH09.WEST.BACK.C15.B06 | 31 | 179.94,127.51 | [工程推断·非史料] |
| 3281 | ARCH09.WEST.BACK.C15.B07 | 28 | 182.75,98.65 | [工程推断·非史料] |
| 3282 | ARCH09.WEST.SPANDREL.C15.B01 | 27 | 184.38,194.27 | [工程推断·非史料] |
| 3283 | ARCH09.WEST.SPANDREL.C15.B02 | 22 | 100.68,132.06 | [工程推断·非史料] |
| 3284 | ARCH09.WEST.SPANDREL.C15.B03 | 27 | 79.07,194.27 | [工程推断·非史料] |
| 3285 | ARCH09.WEST.SPANDREL.C15.B06 | 22 | 151.43,109.72 | [工程推断·非史料] |
| 3286 | ARCH09.WEST.SPANDREL.C15.B07 | 27 | 131.75,194.27 | [工程推断·非史料] |

### S401 ARCH10.FILL (events 3287-3524)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 3310 | ARCH10.EAST.BACK.C07.B06 | 28 | 155.97,144.75 | [工程推断·非史料] |
| 3312 | ARCH10.EAST.SPANDREL.C07.B06 | 20 | 104.62,163.83 | [工程推断·非史料] |
| 3314 | ARCH10.WEST.BACK.C07.B06 | 28 | 181.93,144.75 | [工程推断·非史料] |
| 3316 | ARCH10.WEST.SPANDREL.C07.B06 | 20 | 52.49,163.83 | [工程推断·非史料] |
| 3319 | ARCH10.EAST.BACK.C08.B00 | 27 | 27.51,21.98 | [工程推断·非史料] |
| 3321 | ARCH10.EAST.SPANDREL.C08.B00 | 20 | 52.51,146.36 | [工程推断·非史料] |
| 3323 | ARCH10.WEST.BACK.C08.B00 | 27 | 165.76,0.00 | [工程推断·非史料] |
| 3325 | ARCH10.WEST.SPANDREL.C08.B00 | 20 | 105.02,146.36 | [工程推断·非史料] |
| 3330 | ARCH10.EAST.BACK.C09.B00 | 27 | 162.04,91.45 | [工程推断·非史料] |
| 3331 | ARCH10.EAST.BACK.C09.B06 | 27 | 27.82,0.00 | [工程推断·非史料] |
| 3332 | ARCH10.EAST.SPANDREL.C09.B00 | 21 | 154.28,27.61 | [工程推断·非史料] |
| 3333 | ARCH10.EAST.SPANDREL.C09.B06 | 20 | 155.06,175.29 | [工程推断·非史料] |
| 3334 | ARCH10.WEST.BACK.C09.B00 | 27 | 189.01,91.45 | [工程推断·非史料] |
| 3335 | ARCH10.WEST.BACK.C09.B06 | 27 | 55.43,0.00 | [工程推断·非史料] |
| 3336 | ARCH10.WEST.SPANDREL.C09.B00 | 21 | 0.00,51.77 | [工程推断·非史料] |
| 3337 | ARCH10.WEST.SPANDREL.C09.B06 | 21 | 0.00,0.00 | [工程推断·非史料] |
| 3338 | ARCH10.EAST.BACK.C10.B00 | 31 | 0.00,64.62 | [工程推断·非史料] |
| 3339 | ARCH10.EAST.BACK.C10.B01 | 32 | 104.25,121.88 | [工程推断·非史料] |
| 3340 | ARCH10.EAST.BACK.C10.B02 | 33 | 19.98,69.30 | [工程推断·非史料] |
| 3341 | ARCH10.EAST.BACK.C10.B03 | 30 | 145.94,146.70 | [工程推断·非史料] |
| 3344 | ARCH10.EAST.BACK.C10.B07 | 33 | 146.26,131.82 | [工程推断·非史料] |
| 3345 | ARCH10.EAST.BACK.C10.B08 | 31 | 115.26,64.62 | [工程推断·非史料] |
| 3346 | ARCH10.EAST.BACK.C10.B09 | 32 | 107.75,20.74 | [工程推断·非史料] |
| 3347 | ARCH10.EAST.SPANDREL.C10.B00 | 24 | 149.12,95.04 | [工程推断·非史料] |
| 3348 | ARCH10.EAST.SPANDREL.C10.B01 | 29 | 0.00,126.21 | [工程推断·非史料] |
| 3349 | ARCH10.EAST.SPANDREL.C10.B02 | 24 | 0.00,95.04 | [工程推断·非史料] |
| 3350 | ARCH10.EAST.SPANDREL.C10.B03 | 29 | 77.17,115.77 | [工程推断·非史料] |
| 3351 | ARCH10.EAST.SPANDREL.C10.B07 | 29 | 0.00,115.77 | [工程推断·非史料] |
| 3352 | ARCH10.EAST.SPANDREL.C10.B08 | 24 | 0.00,76.72 | [工程推断·非史料] |
| 3353 | ARCH10.EAST.SPANDREL.C10.B09 | 29 | 0.00,101.09 | [工程推断·非史料] |
| 3354 | ARCH10.WEST.BACK.C10.B00 | 31 | 46.11,64.62 | [工程推断·非史料] |
| 3355 | ARCH10.WEST.BACK.C10.B01 | 32 | 125.04,121.88 | [工程推断·非史料] |
| 3356 | ARCH10.WEST.BACK.C10.B02 | 33 | 39.97,69.30 | [工程推断·非史料] |
| 3357 | ARCH10.WEST.BACK.C10.B03 | 30 | 194.51,146.70 | [工程推断·非史料] |
| 3360 | ARCH10.WEST.BACK.C10.B07 | 33 | 182.69,131.82 | [工程推断·非史料] |
| 3361 | ARCH10.WEST.BACK.C10.B08 | 31 | 138.30,64.62 | [工程推断·非史料] |
| 3362 | ARCH10.WEST.BACK.C10.B09 | 32 | 129.28,20.74 | [工程推断·非史料] |
| 3363 | ARCH10.WEST.SPANDREL.C10.B00 | 24 | 49.71,113.36 | [工程推断·非史料] |
| 3364 | ARCH10.WEST.SPANDREL.C10.B01 | 29 | 25.71,126.21 | [工程推断·非史料] |
| 3365 | ARCH10.WEST.SPANDREL.C10.B02 | 24 | 49.71,95.04 | [工程推断·非史料] |
| 3366 | ARCH10.WEST.SPANDREL.C10.B03 | 29 | 128.59,115.77 | [工程推断·非史料] |
| 3367 | ARCH10.WEST.SPANDREL.C10.B07 | 29 | 25.73,115.77 | [工程推断·非史料] |
| 3368 | ARCH10.WEST.SPANDREL.C10.B08 | 24 | 49.73,76.72 | [工程推断·非史料] |
| 3369 | ARCH10.WEST.SPANDREL.C10.B09 | 29 | 25.74,101.09 | [工程推断·非史料] |
| 3370 | ARCH10.EAST.CORE.C13.B00 | 7 | 0.00,138.05 | [工程推断·非史料] |
| 3372 | ARCH10.EAST.CORE.C13.B02 | 8 | 0.00,37.97 | [工程推断·非史料] |
| 3373 | ARCH10.EAST.BACK.C11.B00 | 26 | 121.60,51.03 | [工程推断·非史料] |
| 3374 | ARCH10.EAST.BACK.C11.B04 | 32 | 0.00,41.48 | [工程推断·非史料] |
| 3375 | ARCH10.EAST.BACK.C11.B05 | 31 | 0.00,149.20 | [工程推断·非史料] |
| 3376 | ARCH10.EAST.SPANDREL.C11.B00 | 26 | 91.20,51.03 | [工程推断·非史料] |
| 3377 | ARCH10.EAST.SPANDREL.C11.B04 | 29 | 77.20,101.09 | [工程推断·非史料] |
| 3378 | ARCH10.EAST.SPANDREL.C11.B05 | 24 | 49.73,54.38 | [工程推断·非史料] |
| 3379 | ARCH10.WEST.BACK.C11.B00 | 26 | 182.40,51.03 | [工程推断·非史料] |
| 3380 | ARCH10.WEST.BACK.C11.B04 | 32 | 172.23,20.74 | [工程推断·非史料] |
| 3381 | ARCH10.WEST.BACK.C11.B05 | 31 | 22.34,149.20 | [工程推断·非史料] |
| 3382 | ARCH10.WEST.SPANDREL.C11.B00 | 26 | 152.00,51.03 | [工程推断·非史料] |
| 3383 | ARCH10.WEST.SPANDREL.C11.B04 | 29 | 128.66,101.09 | [工程推断·非史料] |
| 3384 | ARCH10.WEST.SPANDREL.C11.B05 | 24 | 149.35,32.04 | [工程推断·非史料] |
| 3385 | ARCH10.EAST.BACK.C12.B00 | 26 | 65.88,25.32 | [工程推断·非史料] |
| 3386 | ARCH10.EAST.BACK.C12.B01 | 32 | 146.61,101.00 | [工程推断·非史料] |
| 3388 | ARCH10.EAST.BACK.C12.B05 | 33 | 38.64,103.96 | [工程推断·非史料] |
| 3389 | ARCH10.EAST.BACK.C12.B06 | 25 | 138.00,192.61 | [工程推断·非史料] |
| 3390 | ARCH10.EAST.SPANDREL.C12.B00 | 26 | 32.94,25.32 | [工程推断·非史料] |
| 3391 | ARCH10.EAST.SPANDREL.C12.B01 | 25 | 49.33,88.52 | [工程推断·非史料] |
| 3393 | ARCH10.EAST.SPANDREL.C12.B05 | 25 | 98.68,64.22 | [工程推断·非史料] |
| 3394 | ARCH10.EAST.SPANDREL.C12.B06 | 25 | 103.50,192.61 | [工程推断·非史料] |
| 3395 | ARCH10.WEST.BACK.C12.B00 | 26 | 131.76,25.32 | [工程推断·非史料] |
| 3396 | ARCH10.WEST.BACK.C12.B01 | 32 | 167.53,101.00 | [工程推断·非史料] |
| 3398 | ARCH10.WEST.BACK.C12.B05 | 33 | 0.00,103.96 | [工程推断·非史料] |
| 3399 | ARCH10.WEST.BACK.C12.B06 | 26 | 0.00,0.00 | [工程推断·非史料] |
| 3400 | ARCH10.WEST.SPANDREL.C12.B00 | 26 | 98.82,25.32 | [工程推断·非史料] |
| 3401 | ARCH10.WEST.SPANDREL.C12.B01 | 25 | 147.98,88.52 | [工程推断·非史料] |
| 3402 | ARCH10.WEST.SPANDREL.C12.B05 | 25 | 148.02,64.22 | [工程推断·非史料] |
| 3403 | ARCH10.WEST.SPANDREL.C12.B06 | 25 | 172.50,192.61 | [工程推断·非史料] |
| 3404 | ARCH10.EAST.CORE.C14.B00 | 12 | 0.00,70.53 | [工程推断·非史料] |
| 3405 | ARCH10.EAST.CORE.C14.B02 | 13 | 0.00,135.03 | [工程推断·非史料] |
| 3406 | ARCH10.EAST.BACK.C13.B00 | 33 | 179.62,69.30 | [工程推断·非史料] |
| 3407 | ARCH10.EAST.BACK.C13.B01 | 26 | 176.88,102.85 | [工程推断·非史料] |
| 3408 | ARCH10.EAST.BACK.C13.B02 | 29 | 25.79,76.69 | [工程推断·非史料] |
| 3409 | ARCH10.EAST.BACK.C13.B05 | 32 | 192.08,41.48 | [工程推断·非史料] |
| 3410 | ARCH10.EAST.BACK.C13.B06 | 29 | 51.31,144.53 | [工程推断·非史料] |
| 3411 | ARCH10.EAST.BACK.C13.B07 | 30 | 101.22,20.17 | [工程推断·非史料] |
| 3412 | ARCH10.EAST.BACK.C13.B08 | 29 | 0.00,25.79 | [工程推断·非史料] |
| 3413 | ARCH10.EAST.SPANDREL.C13.B00 | 22 | 0.00,109.72 | [工程推断·非史料] |
| 3414 | ARCH10.EAST.SPANDREL.C13.B01 | 26 | 147.40,102.85 | [工程推断·非史料] |
| 3415 | ARCH10.EAST.SPANDREL.C13.B02 | 22 | 101.45,67.28 | [工程推断·非史料] |
| 3416 | ARCH10.EAST.SPANDREL.C13.B05 | 27 | 163.47,65.45 | [工程推断·非史料] |
| 3417 | ARCH10.EAST.SPANDREL.C13.B06 | 22 | 152.24,29.48 | [工程推断·非史料] |
| 3418 | ARCH10.EAST.SPANDREL.C13.B07 | 27 | 53.50,161.29 | [工程推断·非史料] |
| 3419 | ARCH10.EAST.SPANDREL.C13.B08 | 22 | 152.46,0.00 | [工程推断·非史料] |
| 3420 | ARCH10.WEST.BACK.C13.B00 | 33 | 199.53,69.30 | [工程推断·非史料] |
| 3421 | ARCH10.WEST.BACK.C13.B01 | 26 | 29.48,129.56 | [工程推断·非史料] |
| 3422 | ARCH10.WEST.BACK.C13.B02 | 29 | 180.64,51.24 | [工程推断·非史料] |
| 3423 | ARCH10.WEST.BACK.C13.B05 | 32 | 0.00,62.22 | [工程推断·非史料] |
| 3424 | ARCH10.WEST.BACK.C13.B06 | 29 | 76.96,144.53 | [工程推断·非史料] |
| 3425 | ARCH10.WEST.BACK.C13.B07 | 30 | 126.53,20.17 | [工程推断·非史料] |
| 3426 | ARCH10.WEST.BACK.C13.B08 | 29 | 25.82,25.79 | [工程推断·非史料] |
| 3427 | ARCH10.WEST.SPANDREL.C13.B00 | 22 | 101.43,89.34 | [工程推断·非史料] |
| 3428 | ARCH10.WEST.SPANDREL.C13.B01 | 26 | 0.00,129.56 | [工程推断·非史料] |
| 3429 | ARCH10.WEST.SPANDREL.C13.B02 | 22 | 0.00,89.34 | [工程推断·非史料] |
| 3430 | ARCH10.WEST.SPANDREL.C13.B05 | 27 | 190.51,65.45 | [工程推断·非史料] |
| 3431 | ARCH10.WEST.SPANDREL.C13.B06 | 22 | 0.00,45.22 | [工程推断·非史料] |
| 3432 | ARCH10.WEST.SPANDREL.C13.B07 | 27 | 80.25,161.29 | [工程推断·非史料] |
| 3433 | ARCH10.WEST.SPANDREL.C13.B08 | 22 | 0.00,29.48 | [工程推断·非史料] |
| 3434 | ARCH10.EAST.BACK.C14.B00 | 28 | 156.80,85.58 | [工程推断·非史料] |
| 3435 | ARCH10.EAST.BACK.C14.B01 | 31 | 159.57,92.90 | [工程推断·非史料] |
| 3436 | ARCH10.EAST.BACK.C14.B02 | 31 | 70.61,22.49 | [工程推断·非史料] |
| 3437 | ARCH10.EAST.BACK.C14.B03 | 32 | 0.00,20.74 | [工程推断·非史料] |
| 3438 | ARCH10.EAST.BACK.C14.B04 | 33 | 91.55,131.82 | [工程推断·非史料] |
| 3439 | ARCH10.EAST.BACK.C14.B05 | 29 | 153.16,181.31 | [工程推断·非史料] |
| 3440 | ARCH10.EAST.BACK.C14.B06 | 31 | 0.00,74.32 | [工程推断·非史料] |
| 3441 | ARCH10.EAST.BACK.C14.B07 | 31 | 155.38,167.95 | [工程推断·非史料] |
| 3442 | ARCH10.EAST.BACK.C14.B08 | 31 | 176.43,188.33 | [工程推断·非史料] |
| 3443 | ARCH10.EAST.BACK.C14.B09 | 33 | 141.77,50.17 | [工程推断·非史料] |
| 3444 | ARCH10.EAST.BACK.C14.B10 | 33 | 99.87,69.30 | [工程推断·非史料] |
| 3445 | ARCH10.EAST.SPANDREL.C14.B00 | 27 | 185.60,179.19 | [工程推断·非史料] |
| 3446 | ARCH10.EAST.SPANDREL.C14.B01 | 23 | 100.41,46.26 | [工程推断·非史料] |
| 3447 | ARCH10.EAST.SPANDREL.C14.B02 | 28 | 78.63,38.62 | [工程推断·非史料] |
| 3448 | ARCH10.EAST.SPANDREL.C14.B03 | 23 | 50.21,25.52 | [工程推断·非史料] |
| 3449 | ARCH10.EAST.SPANDREL.C14.B04 | 28 | 157.36,22.02 | [工程推断·非史料] |
| 3450 | ARCH10.EAST.SPANDREL.C14.B05 | 23 | 100.45,0.00 | [工程推断·非史料] |
| 3451 | ARCH10.EAST.SPANDREL.C14.B06 | 28 | 26.23,22.02 | [工程推断·非史料] |
| 3452 | ARCH10.EAST.SPANDREL.C14.B07 | 22 | 150.71,187.94 | [工程推断·非史料] |
| 3453 | ARCH10.EAST.SPANDREL.C14.B08 | 28 | 157.62,0.00 | [工程推断·非史料] |
| 3454 | ARCH10.EAST.SPANDREL.C14.B09 | 22 | 150.75,171.80 | [工程推断·非史料] |
| 3455 | ARCH10.EAST.SPANDREL.C14.B10 | 27 | 186.65,161.29 | [工程推断·非史料] |
| 3456 | ARCH10.WEST.BACK.C14.B00 | 28 | 182.93,85.58 | [工程推断·非史料] |
| 3457 | ARCH10.WEST.BACK.C14.B01 | 31 | 182.31,92.90 | [工程推断·非史料] |
| 3458 | ARCH10.WEST.BACK.C14.B02 | 31 | 94.09,22.49 | [工程推断·非史料] |
| 3459 | ARCH10.WEST.BACK.C14.B03 | 32 | 43.13,20.74 | [工程推断·非史料] |
| 3460 | ARCH10.WEST.BACK.C14.B04 | 33 | 109.80,131.82 | [工程推断·非史料] |
| 3461 | ARCH10.WEST.BACK.C14.B05 | 29 | 178.68,181.31 | [工程推断·非史料] |
| 3462 | ARCH10.WEST.BACK.C14.B06 | 31 | 22.94,74.32 | [工程推断·非史料] |
| 3463 | ARCH10.WEST.BACK.C14.B07 | 31 | 177.49,167.95 | [工程推断·非史料] |
| 3464 | ARCH10.WEST.BACK.C14.B08 | 32 | 0.00,0.00 | [工程推断·非史料] |
| 3465 | ARCH10.WEST.BACK.C14.B09 | 33 | 161.87,50.17 | [工程推断·非史料] |
| 3466 | ARCH10.WEST.BACK.C14.B10 | 33 | 119.83,69.30 | [工程推断·非史料] |
| 3467 | ARCH10.WEST.SPANDREL.C14.B00 | 27 | 132.59,179.19 | [工程推断·非史料] |
| 3468 | ARCH10.WEST.SPANDREL.C14.B01 | 23 | 150.62,46.26 | [工程推断·非史料] |
| 3469 | ARCH10.WEST.SPANDREL.C14.B02 | 28 | 26.21,38.62 | [工程推断·非史料] |
| 3470 | ARCH10.WEST.SPANDREL.C14.B03 | 23 | 150.64,25.52 | [工程推断·非史料] |
| 3471 | ARCH10.WEST.SPANDREL.C14.B04 | 28 | 183.58,22.02 | [工程推断·非史料] |
| 3472 | ARCH10.WEST.SPANDREL.C14.B05 | 23 | 150.68,0.00 | [工程推断·非史料] |
| 3473 | ARCH10.WEST.SPANDREL.C14.B06 | 28 | 78.69,22.02 | [工程推断·非史料] |
| 3474 | ARCH10.WEST.SPANDREL.C14.B07 | 22 | 0.00,200.96 | [工程推断·非史料] |
| 3475 | ARCH10.WEST.SPANDREL.C14.B08 | 28 | 183.86,0.00 | [工程推断·非史料] |
| 3476 | ARCH10.WEST.SPANDREL.C14.B09 | 22 | 0.00,187.94 | [工程推断·非史料] |
| 3477 | ARCH10.WEST.SPANDREL.C14.B10 | 27 | 133.55,161.29 | [工程推断·非史料] |
| 3478 | ARCH10.EAST.CORE.C15.B00 | 16 | 0.00,64.14 | [工程推断·非史料] |
| 3479 | ARCH10.EAST.CORE.C15.B01 | 18 | 0.00,67.51 | [工程推断·非史料] |
| 3480 | ARCH10.EAST.CORE.C15.B02 | 19 | 0.00,64.44 | [工程推断·非史料] |
| 3481 | ARCH10.EAST.BACK.C15.B05 | 28 | 180.89,184.87 | [工程推断·非史料] |
| 3482 | ARCH10.EAST.BACK.C15.B08 | 31 | 178.56,149.20 | [工程推断·非史料] |
| 3483 | ARCH10.EAST.BACK.C15.B10 | 31 | 22.68,109.50 | [工程推断·非史料] |
| 3484 | ARCH10.EAST.SPANDREL.C15.B05 | 28 | 155.05,184.87 | [工程推断·非史料] |
| 3485 | ARCH10.EAST.SPANDREL.C15.B08 | 25 | 98.72,56.12 | [工程推断·非史料] |
| 3486 | ARCH10.EAST.SPANDREL.C15.B10 | 25 | 49.16,107.52 | [工程推断·非史料] |
| 3487 | ARCH10.WEST.BACK.C15.B05 | 29 | 25.84,0.00 | [工程推断·非史料] |
| 3488 | ARCH10.WEST.BACK.C15.B08 | 31 | 0.00,167.95 | [工程推断·非史料] |
| 3489 | ARCH10.WEST.BACK.C15.B10 | 31 | 68.04,109.50 | [工程推断·非史料] |
| 3490 | ARCH10.WEST.SPANDREL.C15.B05 | 29 | 0.00,0.00 | [工程推断·非史料] |
| 3491 | ARCH10.WEST.SPANDREL.C15.B08 | 25 | 148.08,56.12 | [工程推断·非史料] |
| 3492 | ARCH10.WEST.SPANDREL.C15.B10 | 25 | 147.47,107.52 | [工程推断·非史料] |
| 3493 | ARCH10.EAST.BACK.C15.B00 | 32 | 105.51,80.12 | [工程推断·非史料] |
| 3494 | ARCH10.EAST.BACK.C15.B01 | 31 | 92.93,43.65 | [工程推断·非史料] |
| 3495 | ARCH10.EAST.BACK.C15.B02 | 30 | 145.48,162.72 | [工程推断·非史料] |
| 3496 | ARCH10.EAST.BACK.C15.B03 | 30 | 149.45,82.14 | [工程推断·非史料] |
| 3497 | ARCH10.EAST.BACK.C15.B04 | 30 | 144.73,186.35 | [工程推断·非史料] |
| 3498 | ARCH10.EAST.BACK.C15.B06 | 31 | 22.64,127.51 | [工程推断·非史料] |
| 3499 | ARCH10.EAST.BACK.C15.B09 | 32 | 42.81,41.48 | [工程推断·非史料] |
| 3500 | ARCH10.EAST.SPANDREL.C15.B00 | 24 | 0.00,15.70 | [工程推断·非史料] |
| 3501 | ARCH10.EAST.SPANDREL.C15.B01 | 29 | 103.35,0.00 | [工程推断·非史料] |
| 3502 | ARCH10.EAST.SPANDREL.C15.B02 | 24 | 49.84,0.00 | [工程推断·非史料] |
| 3503 | ARCH10.EAST.SPANDREL.C15.B03 | 28 | 0.00,184.87 | [工程推断·非史料] |
| 3504 | ARCH10.EAST.SPANDREL.C15.B04 | 23 | 0.00,199.38 | [工程推断·非史料] |
| 3505 | ARCH10.EAST.SPANDREL.C15.B06 | 25 | 99.16,23.78 | [工程推断·非史料] |
| 3506 | ARCH10.EAST.SPANDREL.C15.B09 | 30 | 0.00,38.07 | [工程推断·非史料] |
| 3507 | ARCH10.WEST.BACK.C15.B00 | 32 | 126.54,80.12 | [工程推断·非史料] |
| 3508 | ARCH10.WEST.BACK.C15.B01 | 31 | 116.09,43.65 | [工程推断·非史料] |
| 3509 | ARCH10.WEST.BACK.C15.B02 | 30 | 169.71,162.72 | [工程推断·非史料] |
| 3510 | ARCH10.WEST.BACK.C15.B03 | 30 | 174.29,82.14 | [工程推断·非史料] |
| 3511 | ARCH10.WEST.BACK.C15.B04 | 30 | 96.56,186.35 | [工程推断·非史料] |
| 3512 | ARCH10.WEST.BACK.C15.B06 | 31 | 45.28,127.51 | [工程推断·非史料] |
| 3513 | ARCH10.WEST.BACK.C15.B09 | 32 | 85.59,41.48 | [工程推断·非史料] |
| 3514 | ARCH10.WEST.SPANDREL.C15.B00 | 24 | 49.83,15.70 | [工程推断·非史料] |
| 3515 | ARCH10.WEST.SPANDREL.C15.B01 | 29 | 129.19,0.00 | [工程推断·非史料] |
| 3516 | ARCH10.WEST.SPANDREL.C15.B02 | 23 | 149.53,199.38 | [工程推断·非史料] |
| 3517 | ARCH10.WEST.SPANDREL.C15.B03 | 28 | 25.84,184.87 | [工程推断·非史料] |
| 3518 | ARCH10.WEST.SPANDREL.C15.B04 | 23 | 49.85,199.38 | [工程推断·非史料] |
| 3519 | ARCH10.WEST.SPANDREL.C15.B06 | 25 | 148.74,23.78 | [工程推断·非史料] |
| 3520 | ARCH10.WEST.SPANDREL.C15.B09 | 30 | 25.27,38.07 | [工程推断·非史料] |
| 3521 | ARCH10.EAST.BACK.C15.B07 | 31 | 22.85,92.90 | [工程推断·非史料] |
| 3522 | ARCH10.EAST.SPANDREL.C15.B07 | 29 | 101.87,205.46 | [工程推断·非史料] |
| 3523 | ARCH10.WEST.BACK.C15.B07 | 31 | 45.69,92.90 | [工程推断·非史料] |
| 3524 | ARCH10.WEST.SPANDREL.C15.B07 | 29 | 127.30,205.46 | [工程推断·非史料] |

### S402 ARCH11.FILL (events 3525-3717)

| seq | 单元 | 批 | 床位(x,y) mm | 标注 |
|---|---|---|---|---|
| 3561 | ARCH11.EAST.BACK.C08.B00 | 27 | 53.04,179.19 | [工程推断·非史料] |
| 3562 | ARCH11.EAST.BACK.C08.B05 | 31 | 113.37,109.50 | [工程推断·非史料] |
| 3563 | ARCH11.EAST.SPANDREL.C08.B00 | 20 | 52.94,128.89 | [工程推断·非史料] |
| 3564 | ARCH11.EAST.SPANDREL.C08.B05 | 26 | 117.13,129.56 | [工程推断·非史料] |
| 3565 | ARCH11.WEST.BACK.C08.B00 | 27 | 79.57,179.19 | [工程推断·非史料] |
| 3566 | ARCH11.WEST.BACK.C08.B05 | 31 | 158.69,109.50 | [工程推断·非史料] |
| 3567 | ARCH11.WEST.SPANDREL.C08.B00 | 20 | 105.87,128.89 | [工程推断·非史料] |
| 3568 | ARCH11.WEST.SPANDREL.C08.B05 | 26 | 146.22,129.56 | [工程推断·非史料] |
| 3572 | ARCH11.EAST.BACK.C09.B00 | 32 | 175.14,0.00 | [工程推断·非史料] |
| 3573 | ARCH11.EAST.BACK.C09.B01 | 30 | 97.34,146.70 | [工程推断·非史料] |
| 3575 | ARCH11.EAST.BACK.C09.B06 | 30 | 24.16,186.35 | [工程推断·非史料] |
| 3576 | ARCH11.EAST.SPANDREL.C09.B00 | 21 | 0.00,119.50 | [工程推断·非史料] |
| 3577 | ARCH11.EAST.SPANDREL.C09.B01 | 27 | 27.36,39.45 | [工程推断·非史料] |
| 3578 | ARCH11.EAST.SPANDREL.C09.B06 | 21 | 154.38,0.00 | [工程推断·非史料] |
| 3579 | ARCH11.WEST.BACK.C09.B00 | 32 | 131.54,0.00 | [工程推断·非史料] |
| 3580 | ARCH11.WEST.BACK.C09.B01 | 30 | 48.70,146.70 | [工程推断·非史料] |
| 3582 | ARCH11.WEST.BACK.C09.B06 | 30 | 48.32,186.35 | [工程推断·非史料] |
| 3583 | ARCH11.WEST.SPANDREL.C09.B00 | 21 | 102.75,85.64 | [工程推断·非史料] |
| 3584 | ARCH11.WEST.SPANDREL.C09.B01 | 27 | 82.08,39.45 | [工程推断·非史料] |
| 3585 | ARCH11.WEST.SPANDREL.C09.B06 | 21 | 0.00,27.61 | [工程推断·非史料] |
| 3586 | ARCH11.EAST.CORE.C13.B00 | 9 | 0.00,58.18 | [工程推断·非史料] |
| 3588 | ARCH11.EAST.CORE.C13.B02 | 10 | 0.00,139.66 | [工程推断·非史料] |
| 3589 | ARCH11.EAST.BACK.C10.B00 | 30 | 25.17,62.74 | [工程推断·非史料] |
| 3590 | ARCH11.EAST.BACK.C10.B01 | 33 | 185.19,10.68 | [工程推断·非史料] |
| 3591 | ARCH11.EAST.BACK.C10.B02 | 31 | 23.30,43.65 | [工程推断·非史料] |
| 3593 | ARCH11.EAST.BACK.C10.B06 | 33 | 169.40,113.66 | [工程推断·非史料] |
| 3594 | ARCH11.EAST.BACK.C10.B07 | 33 | 61.48,31.03 | [工程推断·非史料] |
| 3595 | ARCH11.EAST.BACK.C10.B08 | 33 | 143.23,31.03 | [工程推断·非史料] |
| 3596 | ARCH11.EAST.SPANDREL.C10.B00 | 30 | 126.65,14.25 | [工程推断·非史料] |
| 3597 | ARCH11.EAST.SPANDREL.C10.B01 | 25 | 98.66,70.20 | [工程推断·非史料] |
| 3598 | ARCH11.EAST.SPANDREL.C10.B02 | 30 | 177.54,0.00 | [工程推断·非史料] |
| 3599 | ARCH11.EAST.SPANDREL.C10.B06 | 30 | 76.11,0.00 | [工程推断·非史料] |
| 3600 | ARCH11.EAST.SPANDREL.C10.B07 | 25 | 148.11,46.42 | [工程推断·非史料] |
| 3601 | ARCH11.EAST.SPANDREL.C10.B08 | 30 | 25.37,0.00 | [工程推断·非史料] |
| 3602 | ARCH11.WEST.BACK.C10.B00 | 30 | 75.52,62.74 | [工程推断·非史料] |
| 3603 | ARCH11.WEST.BACK.C10.B01 | 33 | 0.00,31.03 | [工程推断·非史料] |
| 3604 | ARCH11.WEST.BACK.C10.B02 | 31 | 187.83,22.49 | [工程推断·非史料] |
| 3606 | ARCH11.WEST.BACK.C10.B06 | 33 | 0.00,131.82 | [工程推断·非史料] |
| 3607 | ARCH11.WEST.BACK.C10.B07 | 33 | 81.96,31.03 | [工程推断·非史料] |
| 3608 | ARCH11.WEST.BACK.C10.B08 | 33 | 163.63,31.03 | [工程推断·非史料] |
| 3609 | ARCH11.WEST.SPANDREL.C10.B00 | 30 | 75.99,14.25 | [工程推断·非史料] |
| 3610 | ARCH11.WEST.SPANDREL.C10.B01 | 25 | 147.99,70.20 | [工程推断·非史料] |
| 3611 | ARCH11.WEST.SPANDREL.C10.B02 | 30 | 25.33,14.25 | [工程推断·非史料] |
| 3612 | ARCH11.WEST.SPANDREL.C10.B06 | 30 | 126.84,0.00 | [工程推断·非史料] |
| 3613 | ARCH11.WEST.SPANDREL.C10.B07 | 25 | 49.37,46.42 | [工程推断·非史料] |
| 3614 | ARCH11.WEST.SPANDREL.C10.B08 | 29 | 178.11,205.46 | [工程推断·非史料] |
| 3615 | ARCH11.EAST.BACK.C11.B00 | 30 | 48.80,125.36 | [工程推断·非史料] |
| 3616 | ARCH11.EAST.BACK.C11.B04 | 29 | 179.53,144.53 | [工程推断·非史料] |
| 3617 | ARCH11.EAST.BACK.C11.B05 | 33 | 79.30,87.62 | [工程推断·非史料] |
| 3618 | ARCH11.EAST.SPANDREL.C11.B00 | 29 | 77.34,76.69 | [工程推断·非史料] |
| 3619 | ARCH11.EAST.SPANDREL.C11.B04 | 29 | 103.24,51.24 | [工程推断·非史料] |
| 3620 | ARCH11.EAST.SPANDREL.C11.B05 | 24 | 0.00,32.04 | [工程推断·非史料] |
| 3621 | ARCH11.WEST.BACK.C11.B00 | 30 | 73.20,125.36 | [工程推断·非史料] |
| 3622 | ARCH11.WEST.BACK.C11.B04 | 29 | 128.25,144.53 | [工程推断·非史料] |
| 3623 | ARCH11.WEST.BACK.C11.B05 | 33 | 99.07,87.62 | [工程推断·非史料] |
| 3624 | ARCH11.WEST.SPANDREL.C11.B00 | 29 | 128.85,76.69 | [工程推断·非史料] |
| 3625 | ARCH11.WEST.SPANDREL.C11.B04 | 29 | 129.05,51.24 | [工程推断·非史料] |
| 3626 | ARCH11.WEST.SPANDREL.C11.B05 | 24 | 49.81,32.04 | [工程推断·非史料] |
| 3627 | ARCH11.EAST.BACK.C12.B00 | 27 | 26.94,135.32 | [工程推断·非史料] |
| 3628 | ARCH11.EAST.BACK.C12.B01 | 32 | 63.76,62.22 | [工程推断·非史料] |
| 3630 | ARCH11.EAST.BACK.C12.B05 | 30 | 146.36,125.36 | [工程推断·非史料] |
| 3631 | ARCH11.EAST.BACK.C12.B06 | 30 | 151.49,38.07 | [工程推断·非史料] |
| 3632 | ARCH11.EAST.SPANDREL.C12.B00 | 27 | 0.00,135.32 | [工程推断·非史料] |
| 3633 | ARCH11.EAST.SPANDREL.C12.B01 | 23 | 0.00,176.00 | [工程推断·非史料] |
| 3635 | ARCH11.EAST.SPANDREL.C12.B05 | 23 | 150.23,136.36 | [工程推断·非史料] |
| 3636 | ARCH11.EAST.SPANDREL.C12.B06 | 28 | 0.00,144.75 | [工程推断·非史料] |
| 3637 | ARCH11.WEST.BACK.C12.B00 | 27 | 80.82,135.32 | [工程推断·非史料] |
| 3638 | ARCH11.WEST.BACK.C12.B01 | 32 | 85.00,62.22 | [工程推断·非史料] |
| 3640 | ARCH11.WEST.BACK.C12.B05 | 30 | 170.74,125.36 | [工程推断·非史料] |
| 3641 | ARCH11.WEST.BACK.C12.B06 | 30 | 176.71,38.07 | [工程推断·非史料] |
| 3642 | ARCH11.WEST.SPANDREL.C12.B00 | 27 | 53.88,135.32 | [工程推断·非史料] |
| 3643 | ARCH11.WEST.SPANDREL.C12.B01 | 23 | 49.97,176.00 | [工程推断·非史料] |
| 3644 | ARCH11.WEST.SPANDREL.C12.B05 | 23 | 50.01,164.42 | [工程推断·非史料] |
| 3645 | ARCH11.WEST.SPANDREL.C12.B06 | 28 | 26.02,144.75 | [工程推断·非史料] |
| 3646 | ARCH11.EAST.CORE.C14.B00 | 14 | 0.00,67.51 | [工程推断·非史料] |
| 3647 | ARCH11.EAST.CORE.C14.B02 | 15 | 0.00,128.29 | [工程推断·非史料] |
| 3648 | ARCH11.EAST.BACK.C13.B00 | 31 | 0.00,22.49 | [工程推断·非史料] |
| 3649 | ARCH11.EAST.BACK.C13.B01 | 26 | 58.96,76.74 | [工程推断·非史料] |
| 3650 | ARCH11.EAST.BACK.C13.B02 | 33 | 20.38,50.17 | [工程推断·非史料] |
| 3651 | ARCH11.EAST.BACK.C13.B03 | 33 | 103.01,10.68 | [工程推断·非史料] |
| 3652 | ARCH11.EAST.BACK.C13.B04 | 26 | 28.06,183.27 | [工程推断·非史料] |
| 3653 | ARCH11.EAST.BACK.C13.B05 | 31 | 114.62,74.32 | [工程推断·非史料] |
| 3654 | ARCH11.EAST.BACK.C13.B06 | 32 | 21.15,80.12 | [工程推断·非史料] |
| 3655 | ARCH11.EAST.BACK.C13.B07 | 30 | 177.28,14.25 | [工程推断·非史料] |
| 3656 | ARCH11.EAST.SPANDREL.C13.B00 | 27 | 134.69,135.32 | [工程推断·非史料] |
| 3657 | ARCH11.EAST.SPANDREL.C13.B01 | 21 | 152.86,164.70 | [工程推断·非史料] |
| 3658 | ARCH11.EAST.SPANDREL.C13.B02 | 27 | 53.92,109.35 | [工程推断·非史料] |
| 3659 | ARCH11.EAST.SPANDREL.C13.B03 | 21 | 0.00,164.70 | [工程推断·非史料] |
| 3660 | ARCH11.EAST.SPANDREL.C13.B04 | 26 | 0.00,183.27 | [工程推断·非史料] |
| 3661 | ARCH11.EAST.SPANDREL.C13.B05 | 21 | 102.35,128.38 | [工程推断·非史料] |
| 3662 | ARCH11.EAST.SPANDREL.C13.B06 | 27 | 27.03,91.45 | [工程推断·非史料] |
| 3663 | ARCH11.EAST.SPANDREL.C13.B07 | 21 | 102.69,119.50 | [工程推断·非史料] |
| 3664 | ARCH11.WEST.BACK.C13.B00 | 31 | 166.32,0.00 | [工程推断·非史料] |
| 3665 | ARCH11.WEST.BACK.C13.B01 | 26 | 88.44,76.74 | [工程推断·非史料] |
| 3666 | ARCH11.WEST.BACK.C13.B02 | 33 | 40.76,50.17 | [工程推断·非史料] |
| 3667 | ARCH11.WEST.BACK.C13.B03 | 33 | 123.59,10.68 | [工程推断·非史料] |
| 3668 | ARCH11.WEST.BACK.C13.B04 | 26 | 84.18,183.27 | [工程推断·非史料] |
| 3669 | ARCH11.WEST.BACK.C13.B05 | 31 | 68.80,74.32 | [工程推断·非史料] |
| 3670 | ARCH11.WEST.BACK.C13.B06 | 32 | 42.30,80.12 | [工程推断·非史料] |
| 3671 | ARCH11.WEST.BACK.C13.B07 | 30 | 25.31,20.17 | [工程推断·非史料] |
| 3672 | ARCH11.WEST.SPANDREL.C13.B00 | 27 | 188.56,135.32 | [工程推断·非史料] |
| 3673 | ARCH11.WEST.SPANDREL.C13.B01 | 22 | 0.00,0.00 | [工程推断·非史料] |
| 3674 | ARCH11.WEST.SPANDREL.C13.B02 | 27 | 80.88,109.35 | [工程推断·非史料] |
| 3675 | ARCH11.WEST.SPANDREL.C13.B03 | 21 | 101.99,144.12 | [工程推断·非史料] |
| 3676 | ARCH11.WEST.SPANDREL.C13.B04 | 26 | 56.12,183.27 | [工程推断·非史料] |
| 3677 | ARCH11.WEST.SPANDREL.C13.B05 | 21 | 0.00,144.12 | [工程推断·非史料] |
| 3678 | ARCH11.WEST.SPANDREL.C13.B06 | 27 | 81.08,91.45 | [工程推断·非史料] |
| 3679 | ARCH11.WEST.SPANDREL.C13.B07 | 21 | 0.00,128.38 | [工程推断·非史料] |
| 3680 | ARCH11.EAST.BACK.C14.B05 | 30 | 148.18,95.16 | [工程推断·非史料] |
| 3681 | ARCH11.EAST.BACK.C14.B07 | 31 | 89.32,149.20 | [工程推断·非史料] |
| 3682 | ARCH11.EAST.BACK.C14.B08 | 33 | 96.59,103.96 | [工程推断·非史料] |
| 3683 | ARCH11.EAST.SPANDREL.C14.B05 | 25 | 98.33,100.10 | [工程推断·非史料] |
| 3684 | ARCH11.EAST.SPANDREL.C14.B07 | 25 | 97.41,118.48 | [工程推断·非史料] |
| 3685 | ARCH11.EAST.SPANDREL.C14.B08 | 30 | 146.83,116.20 | [工程推断·非史料] |
| 3686 | ARCH11.WEST.BACK.C14.B05 | 30 | 172.77,95.16 | [工程推断·非史料] |
| 3687 | ARCH11.WEST.BACK.C14.B07 | 31 | 111.64,149.20 | [工程推断·非史料] |
| 3688 | ARCH11.WEST.BACK.C14.B08 | 33 | 115.88,103.96 | [工程推断·非史料] |
| 3689 | ARCH11.WEST.SPANDREL.C14.B05 | 25 | 147.50,100.10 | [工程推断·非史料] |
| 3690 | ARCH11.WEST.SPANDREL.C14.B07 | 25 | 146.11,118.48 | [工程推断·非史料] |
| 3691 | ARCH11.WEST.SPANDREL.C14.B08 | 30 | 171.24,116.20 | [工程推断·非史料] |
| 3692 | ARCH11.EAST.BACK.C14.B00 | 33 | 118.85,87.62 | [工程推断·非史料] |
| 3693 | ARCH11.EAST.BACK.C14.B01 | 31 | 47.56,0.00 | [工程推断·非史料] |
| 3694 | ARCH11.EAST.BACK.C14.B02 | 30 | 74.29,95.16 | [工程推断·非史料] |
| 3695 | ARCH11.EAST.BACK.C14.B03 | 32 | 188.45,101.00 | [工程推断·非史料] |
| 3696 | ARCH11.EAST.SPANDREL.C14.B00 | 29 | 153.55,160.27 | [工程推断·非史料] |
| 3697 | ARCH11.EAST.SPANDREL.C14.B01 | 25 | 99.18,0.00 | [工程推断·非史料] |
| 3698 | ARCH11.EAST.SPANDREL.C14.B02 | 29 | 51.19,160.27 | [工程推断·非史料] |
| 3699 | ARCH11.EAST.SPANDREL.C14.B03 | 24 | 49.60,198.56 | [工程推断·非史料] |
| 3700 | ARCH11.WEST.BACK.C14.B00 | 33 | 138.57,87.62 | [工程推断·非史料] |
| 3701 | ARCH11.WEST.BACK.C14.B01 | 31 | 71.34,0.00 | [工程推断·非史料] |
| 3702 | ARCH11.WEST.BACK.C14.B02 | 30 | 49.66,95.16 | [工程推断·非史料] |
| 3703 | ARCH11.WEST.BACK.C14.B03 | 32 | 20.89,121.88 | [工程推断·非史料] |
| 3704 | ARCH11.WEST.SPANDREL.C14.B00 | 29 | 179.13,160.27 | [工程推断·非史料] |
| 3705 | ARCH11.WEST.SPANDREL.C14.B01 | 25 | 148.76,0.00 | [工程推断·非史料] |
| 3706 | ARCH11.WEST.SPANDREL.C14.B02 | 29 | 76.79,160.27 | [工程推断·非史料] |
| 3707 | ARCH11.WEST.SPANDREL.C14.B03 | 24 | 149.00,181.66 | [工程推断·非史料] |
| 3708 | ARCH11.EAST.BACK.C14.B04 | 29 | 180.75,25.79 | [工程推断·非史料] |
| 3709 | ARCH11.EAST.BACK.C14.B06 | 33 | 20.62,10.68 | [工程推断·非史料] |
| 3710 | ARCH11.EAST.SPANDREL.C14.B04 | 29 | 154.93,25.79 | [工程推断·非史料] |
| 3711 | ARCH11.EAST.SPANDREL.C14.B06 | 30 | 0.00,82.14 | [工程推断·非史料] |
| 3712 | ARCH11.WEST.BACK.C14.B04 | 29 | 25.82,51.24 | [工程推断·非史料] |
| 3713 | ARCH11.WEST.BACK.C14.B06 | 33 | 41.23,10.68 | [工程推断·非史料] |
| 3714 | ARCH11.WEST.SPANDREL.C14.B04 | 29 | 0.00,51.24 | [工程推断·非史料] |
| 3715 | ARCH11.WEST.SPANDREL.C14.B06 | 30 | 25.00,82.14 | [工程推断·非史料] |
| 3716 | ARCH11.EAST.CORE.C15.B00 | 18 | 0.00,135.03 | [工程推断·非史料] |
| 3717 | ARCH11.EAST.CORE.C15.B01 | 20 | 0.00,64.44 | [工程推断·非史料] |

