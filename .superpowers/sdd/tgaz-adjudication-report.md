# TGAZ 真实裁决报告——首轮候选 × 多源比对

- 日期: 2026-10-02
- 引擎: 闭包引擎 v3 (miner=v3 / rule_profile=rp-v3)，六模块完整闭包 G/Y/B/S/dazhongsi/bridges
- 端点: `GET https://tgaz.fudan.edu.cn/tgaz/placename?fmt=json&n=<候选名>`（简体，串行，≥0.4s 间隔）
- 契约要点（详见 tgaz-api-findings.md）: 前缀 LIKE 匹配；HTTP 200 不代表成功，须校验 body 以 `{` 开头；单次 JSON 最多返回 200 条
- 闭包规模: 种子词条 47，挖过篇卷 54，已知名命中(跳过) 41，**候选假说 68 个**（mid 62 / high 6）

## 裁决规则

1. 每个候选取其**简体查询用形**逐个调 TGAZ（引擎 `normalize_form` 只覆盖项目语料子集，个别候选补查字形转换，仅在查询侧，不改引擎）；
2. 命中 → 置信 `mid` 升 `high`（`low` 命中升 `mid`；本轮无 low 候选）；未命中 → **保留原置信，不否决**（TGAZ 前缀匹配 + 收录范围有限，零命中≠不存在）；
3. 最佳命中选取：上级属京师域加权 +3（两级标记：顺天府属州县名前缀匹配——大兴/宛平/房山/通州/昌平/涿州/蓟州/密云等 23 州县及京师/北京，府域词包含匹配——顺天/直隶/畿辅），名称与查询形全等 +2、前缀命中 +1，同分取返回序首；
4. 异常单列：同名异地多命中、命中全在异地、零命中噪声形态。

## 命中统计

| 指标 | 值 |
|---|---|
| 候选总数 | 68 |
| TGAZ 命中(≥1) | 9 |
| 零命中(保留) | 59 |
| 同名异地多命中 | 7 |
| 命中全在异地(不可采信) | 7 |
| 置信 mid→high | 8 |
| 查询失败 | 0 |

## 逐候选裁决表

| # | 候选 | 引擎置信 | 书证 | TGAZ命中 | 最佳命中 sys_id | 命中名 | 年代 | 上级 | 要素类型 | 裁决后置信 | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **永定河** | mid | 1处/shuijingzhu | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 2 | **戾陵堰** | mid | 1处/shuijingzhu | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 3 | **车箱渠** | mid | 1处/shuijingzhu | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 4 | **通惠河** | mid | 2处/yuanshi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 5 | **绮春三园** | mid | 1处/ymy_yuan | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 6 | **水礳** | mid | 1处/bqtz | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 7 | **保福寺** | high | 1处/bqtz | 0 | — | — | — | — | — | **high** | 未命中→保留不否决 |
| 8 | **萧家河** | high | 2处/bqtz、rxjwkc | 0 | — | — | — | — | — | **high** | 未命中→保留不否决 |
| 9 | **蓝靛厂** | high | 1处/bqtz | 0 | — | — | — | — | — | **high** | 未命中→保留不否决 |
| 10 | **五圣庵** | high | 1处/rxjwkc | 0 | — | — | — | — | — | **high** | 未命中→保留不否决 |
| 11 | **观音寺** | mid | 1处/rxjwkc | 12 | `hvd_128374` 观音寺 | 观音寺 | 1911 ~ 1911 | 应山县 (Yingshan Xian) | 村镇 (cun zhen) | **high** | ⚠ 命中均为异地同名（非京师域，含上级未标注者），不可直接采信；同名异地多命中 |
| 12 | **观音庵** | high | 2处/rxjwkc | 1 | `hvd_162715` 观音庵 | 观音庵 | 1911 ~ 1911 | （无） | 村镇 (cun zhen) | **high** | ⚠ 命中均为异地同名（非京师域，含上级未标注者），不可直接采信 |
| 13 | **达官村** | mid | 1处/rxjwkc | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 14 | **关帝庙** | mid | 2处/rxjwkc | 3 | `hvd_133196` 关帝庙 | 关帝庙 | 1911 ~ 1911 | 洋县 (Yang Xian) | 村镇 (cun zhen) | **high** | ⚠ 命中均为异地同名（非京师域，含上级未标注者），不可直接采信；同名异地多命中 |
| 15 | **金山** | mid | 1处/rxjwkc | 35 | `hvd_136654` 金山庄 | 金山庄 | 1911 ~ 1911 | 密云县 (Miyun Xian) | 村镇 (cun zhen) | **high** | 同名异地多命中 |
| 16 | **清河** | mid | 4处/bma_1929、hd_diqumingzhi、hd_gov_open、minglu_2 | 56 | `hvd_136231` 清河铺 | 清河铺 | 1911 ~ 1911 | 大兴县 (Daxing Xian) | 村镇 (cun zhen) | **high** | 同名异地多命中 |
| 17 | **西二旗** | mid | 1处/hd_diqumingzhi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 18 | **名覺生寺** | mid | 1处/jueshengsi_beiwen | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决；查询用形「名觉生寺」（补繁简归一） |
| 19 | **左繞山** | mid | 1处/jueshengsi_beiwen | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决；查询用形「左绕山」（补繁简归一） |
| 20 | **向藏漢經厂** | mid | 1处/dijingjingwulue | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决；查询用形「向藏汉经厂」（补繁简归一） |
| 21 | **方钟樓** | mid | 1处/changankehua | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决；查询用形「方钟楼」（补繁简归一） |
| 22 | **異他钟** | mid | 1处/changankehua | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决；查询用形「异他钟」（补繁简归一） |
| 23 | **懸大钟一口** | mid | 1处/zuozhongzhi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决；查询用形「悬大钟一口」（补繁简归一） |
| 24 | **十数仆地上** | mid | 1处/chunmengmengyulu | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 25 | **旋梯** | mid | 1处/yanjingsuishiji | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 26 | **道傍观** | mid | 1处/yuanzhonglang | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 27 | **六月十六日** | mid | 1处/rxjwkc | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 28 | **觉生寺大钟殿** | mid | 1处/dzs_history | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 29 | **华严觉海** | mid | 1处/dzs_history | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 30 | **天王殿** | mid | 1处/dzs_history | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 31 | **大雄宝殿** | mid | 1处/dzs_history | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 32 | **命勿毀高梁河** | mid | 1处/jinshi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 33 | **長源** | mid | 1处/rxjwkc | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 34 | **永澤** | mid | 1处/rxjwkc | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 35 | **資安** | mid | 1处/rxjwkc | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 36 | **广潤** | mid | 1处/rxjwkc | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 37 | **南牌坊** | mid | 1处/rxjwkc | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 38 | **北牌坊** | mid | 1处/rxjwkc | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 39 | **德胜门外安河** | mid | 1处/lidaizhiguangbiao | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 40 | **供守卫圆明园** | mid | 1处/lidaizhiguangbiao | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 41 | **《三山五园** | mid | 2处/minglu_2、sxwj | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 42 | **水渠** | mid | 3处/anheqiao_xiaoshi、hd_gov_open、minglu_2 | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 43 | **重要重修** | mid | 1处/wjbz_open | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 44 | **古桥** | mid | 1处/wjbz_open | 2 | `hvd_148278` 古桥 | 古桥 | 1911 ~ 1911 | 洧川县 (Chuan Xian) | 村镇 (cun zhen) | **high** | ⚠ 命中均为异地同名（非京师域，含上级未标注者），不可直接采信；同名异地多命中 |
| 45 | **建公路桥** | mid | 1处/wjbz_open | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 46 | **桥北归海淀** | mid | 1处/wjbz_open | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 47 | **界桥** | mid | 1处/wjbz_open | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 48 | **大运河** | mid | 1处/wjbz_open | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 49 | **桥上置闸** | mid | 1处/wjbz_open | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 50 | **该闸** | mid | 1处/wjbz_open | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 51 | **船坞** | mid | 1处/hd_gov_open | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 52 | **高梁桥是长河** | mid | 1处/hd_gov_open | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 53 | **转河** | mid | 1处/hd_gov_open | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 54 | **大河** | mid | 1处/hd_gov_open | 42 | `hvd_163674` 大河 | 大河 | 1911 ~ 1911 | （无） | 村镇 (cun zhen) | **high** | ⚠ 命中均为异地同名（非京师域，含上级未标注者），不可直接采信；同名异地多命中 |
| 55 | **白石桥** | mid | 1处/hd_gov_open | 1 | `hvd_141704` 白石桥 | 白石桥 | 1911 ~ 1911 | 玉山县 (Yushan Xian) | 村镇 (cun zhen) | **high** | ⚠ 命中均为异地同名（非京师域，含上级未标注者），不可直接采信 |
| 56 | **历史旧安河桥** | mid | 2处/bma_1929、hd_gov_open | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 57 | **新桥** | mid | 1处/hd_gov_open | 24 | `hvd_17123` 新桥 | 新桥 | 1820 ~ 1820 | 肇庆府 (Zhaoqing Fu) | 村镇 (cun zhen) | **high** | ⚠ 命中均为异地同名（非京师域，含上级未标注者），不可直接采信；同名异地多命中 |
| 58 | **建木桥** | mid | 1处/anheqiao_xiaoshi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 59 | **旧料** | mid | 1处/anheqiao_xiaoshi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 60 | **旧桥** | mid | 1处/anheqiao_xiaoshi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 61 | **控水闸** | high | 1处/anheqiao_xiaoshi | 0 | — | — | — | — | — | **high** | 未命中→保留不否决 |
| 62 | **常水输瓮山泊** | mid | 1处/anheqiao_xiaoshi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 63 | **洪水泄清河** | mid | 1处/anheqiao_xiaoshi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 64 | **不说桥** | mid | 1处/anheqiao_xiaoshi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 65 | **消失** | mid | 1处/anheqiao_xiaoshi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 66 | **公交安河桥** | mid | 1处/anheqiao_xiaoshi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 67 | **地铁安河桥** | mid | 2处/anheqiao_xiaoshi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |
| 68 | **龙背村** | mid | 1处/anheqiao_xiaoshi | 0 | — | — | — | — | — | **mid** | 未命中→保留不否决 |

## 异常与发现

### 1. 同名异地多命中（同名不同上级，须消歧后才能采信）

- **观音寺**（查询「观音寺」，12 命中）：
  - `hvd_128374` 观音寺｜1911 ~ 1911｜上级 应山县 (Yingshan Xian)｜村镇 (cun zhen)
  - `hvd_128511` 观音寺｜1911 ~ 1911｜上级 石首县 (Shishou Xian)｜村镇 (cun zhen)
  - `hvd_128596` 观音寺｜1911 ~ 1911｜上级 宜都县 (Yidu Xian)｜村镇 (cun zhen)
  - `hvd_149894` 观音寺｜1911 ~ 1911｜上级 西平县 (Xiping Xian)｜村镇 (cun zhen)
  - `hvd_164151` 观音寺｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_164537` 观音寺｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_164697` 观音寺｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_164898` 观音寺｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_166079` 观音寺｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_133204` 观音寺街｜1911 ~ 1911｜上级 略阳县 (Lueyang Xian)｜村镇 (cun zhen)
  - `hvd_128532` 观音寺市｜1911 ~ 1911｜上级 监利县 (Jianli Xian)｜村镇 (cun zhen)
  - `TBRC_G1KR30` ཐུགས་རྗེ་ཆེན་པོའི་དགོན｜1850 ~ 9999｜上级 （无）｜དགོན་པ། (dgon pa)
- **关帝庙**（查询「关帝庙」，3 命中）：
  - `hvd_133196` 关帝庙｜1911 ~ 1911｜上级 洋县 (Yang Xian)｜村镇 (cun zhen)
  - `hvd_150118` 关帝庙｜1911 ~ 1911｜上级 商城县 (Shangcheng Xian)｜村镇 (cun zhen)
  - `hvd_166265` 关帝庙｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
- **金山**（查询「金山」，35 命中）：
  - `TBRC_G1PD96095` ཅིང་ཧྲན་ཟི｜555 ~ 9999｜上级 （无）｜དགོན་པ། (dgon pa)
  - `hvd_20431` 金山｜1820 ~ 1820｜上级 曹州府 (Caozhou Fu)｜村镇 (cun zhen)
  - `hvd_167582` 金山｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_163773` 金山｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_147360` 金山｜1911 ~ 1911｜上级 五台县 (Wutai Xian)｜村镇 (cun zhen)
  - `hvd_96577` 金山郡｜607 ~ 617｜上级 隋 (Sui)｜郡 (jun)
  - `hvd_85422` 金山千户所｜1474 ~ 1644｜上级 （无）｜千户 (qian hu)
  - `hvd_96131` 金山县｜571 ~ 607｜上级 （无）｜县 (xian)
  - `hvd_70503` 金山县｜575 ~ 576｜上级 张掖郡 (Zhangye Jun)｜县 (xian)
  - `hvd_40594` 金山县｜618 ~ 624｜上级 江都郡 (Jiangdu Jun)｜县 (xian)
  - `hvd_40707` 金山县｜688 ~ 704｜上级 婺州 (Wu Zhou)｜县 (xian)
  - `hvd_40487` 金山县｜1724 ~ 1730｜上级 松江府 (Songjiang Fu)｜县 (xian)
  - `hvd_25896` 金山县｜1724 ~ 1911｜上级 （无）｜县 (xian)
  - `hvd_40488` 金山县｜1731 ~ 1758｜上级 松江府 (Songjiang Fu)｜县 (xian)
  - `hvd_40505` 金山县｜1759 ~ 1767｜上级 松江府 (Songjiang Fu)｜县 (xian)
  - `hvd_40506` 金山县｜1768 ~ 1795｜上级 松江府 (Songjiang Fu)｜县 (xian)
  - `hvd_40508` 金山县｜1796 ~ 1911｜上级 松江府 (Songjiang Fu)｜县 (xian)
  - `hvd_196516` 金山县｜1911 ~ 1911｜上级 松江府 (Songjiang Fu)｜县 (xian)
  - `hvd_163373` 金山场｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_164046` 金山场｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_163848` 金山场｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_24283` 金山城｜1820 ~ 1820｜上级 金山县 (Jinshan Xian)｜村镇 (cun zhen)
  - `hvd_139536` 金山城｜1911 ~ 1911｜上级 金山县 (Jinshan Xian)｜村镇 (cun zhen)
  - `hvd_145180` 金山沟｜1911 ~ 1911｜上级 洪洞县 (Hongdong Xian)｜村镇 (cun zhen)
  - `hvd_167344` 金山口｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_21614` 金山铺｜1820 ~ 1820｜上级 绵州 (Mian Zhou)｜村镇 (cun zhen)
  - `hvd_147251` 金山铺｜1911 ~ 1911｜上级 忻州 (Xin Zhou)｜村镇 (cun zhen)
  - `hvd_147464` 金山铺｜1911 ~ 1911｜上级 繁峙县 (Fanzhi Xian)｜村镇 (cun zhen)
  - `hvd_139623` 金山市｜1911 ~ 1911｜上级 余姚县 (Yuyao Xian)｜村镇 (cun zhen)
  - `hvd_132173` 金山寺｜1911 ~ 1911｜上级 宁羌州 (Ningqiang Zhou)｜村镇 (cun zhen)
  - `hvd_131853` 金山镇｜1911 ~ 1911｜上级 蓝田县 (Lantian Xian)｜村镇 (cun zhen)
  - `hvd_164866` 金山镇｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_136654` 金山庄｜1911 ~ 1911｜上级 密云县 (Miyun Xian)｜村镇 (cun zhen)
  - `hvd_138395` 金山总｜1911 ~ 1911｜上级 南靖县 (Nanjing Xian)｜村镇 (cun zhen)
  - `hvd_135757` 金山嘴｜1911 ~ 1911｜上级 临榆县 (Linyu Xian)｜村镇 (cun zhen)
- **清河**（查询「清河」，56 命中）：
  - `hvd_56` 清河县｜1820 ~ 1820｜上级 广平府 (Guangping Fu)｜县 (xian)
  - `hvd_87255` 清河国｜-147 ~ -137｜上级 西汉 (Xihan)｜国 (guo)
  - `hvd_87257` 清河国｜-114 ~ -82｜上级 西汉 (Xihan)｜国 (guo)
  - `hvd_112220` 清河国｜-113 ~ -67｜上级 （无）｜国 (guo)
  - `hvd_87258` 清河国｜-81 ~ -71｜上级 西汉 (Xihan)｜国 (guo)
  - `hvd_87259` 清河国｜-70 ~ -67｜上级 西汉 (Xihan)｜国 (guo)
  - `hvd_112222` 清河国｜-47 ~ -44｜上级 西汉 (Xihan)｜国 (guo)
  - `hvd_115729` 清河国｜25 ~ 438｜上级 （无）｜国 (guo)
  - `hvd_112226` 清河国｜79 ~ 147｜上级 （无）｜国 (guo)
  - `hvd_87263` 清河国｜82 ~ 147｜上级 东汉 (Donghan)｜国 (guo)
  - `hvd_87254` 清河郡｜-221 ~ -148｜上级 秦 (Qin)｜郡 (jun)
  - `hvd_112216` 清河郡｜-198 ~ -155｜上级 西汉 (Xihan)｜郡 (jun)
  - `hvd_112217` 清河郡｜-154 ~ -148｜上级 （无）｜郡 (jun)
  - `hvd_87256` 清河郡｜-136 ~ -113｜上级 西汉 (Xihan)｜郡 (jun)
  - `hvd_112219` 清河郡｜-136 ~ -114｜上级 （无）｜郡 (jun)
  - `hvd_87260` 清河郡｜-66 ~ 13｜上级 西汉 (Xihan)｜郡 (jun)
  - `hvd_112221` 清河郡｜-66 ~ -48｜上级 （无）｜郡 (jun)
  - `hvd_112223` 清河郡｜-43 ~ 8｜上级 西汉 (Xihan)｜郡 (jun)
  - `hvd_87939` 清河郡｜0 ~ 582｜上级 北周 (Bei Zhou)｜郡 (jun)
  - `hvd_87262` 清河郡｜23 ~ 81｜上级 东汉 (Donghan)｜郡 (jun)
  - `hvd_112225` 清河郡｜24 ~ 78｜上级 东汉 (Donghan)｜郡 (jun)
  - `hvd_87940` 清河郡｜607 ~ 620｜上级 隋 (Sui)｜郡 (jun)
  - `hvd_87944` 清河郡｜742 ~ 757｜上级 唐 (Tang)｜郡 (jun)
  - `hvd_44848` 清河县｜583 ~ 859｜上级 贝州 (Bei Zhou)｜县 (xian)
  - `hvd_44849` 清河县｜860 ~ 993｜上级 贝州 (Bei Zhou)｜县 (xian)
  - `hvd_85204` 清河县｜936 ~ 946｜上级 （无）｜县 (xian)
  - `hvd_44850` 清河县｜994 ~ 1911｜上级 贝州 (Bei Zhou)｜县 (xian)
  - `hvd_42767` 清河县｜1273 ~ 1323｜上级 淮安州 (Huaian Zhou)｜县 (xian)
  - `hvd_42768` 清河县｜1324 ~ 1327｜上级 淮安路 (Huaian Lu)｜县 (xian)
  - `hvd_42769` 清河县｜1328 ~ 1642｜上级 淮安路 (Huaian Lu)｜县 (xian)
  - `hvd_42770` 清河县｜1643 ~ 1644｜上级 淮安府 (Huaian Fu)｜县 (xian)
  - `hvd_42771` 清河县｜1645 ~ 1759｜上级 淮安府 (Huaian Fu)｜县 (xian)
  - `hvd_42772` 清河县｜1760 ~ 1911｜上级 淮安府 (Huaian Fu)｜县 (xian)
  - `hvd_763` 清河县｜1820 ~ 1820｜上级 淮安府 (Huai'an Fu)｜县 (xian)
  - `hvd_121004` 清河县｜1911 ~ 1911｜上级 淮安府 (Huai'an Fu)｜县 (xian)
  - `hvd_121449` 清河县｜1911 ~ 1911｜上级 广平府 (Guangping Fu)｜县 (xian)
  - `hvd_196583` 清河县｜1911 ~ 1911｜上级 广平府 (Guangping Fu)｜县 (xian)
  - `hvd_196463` 清河县｜1911 ~ 1911｜上级 淮安府 (Huai'an Fu)｜县 (xian)
  - `hvd_21122` 清河堡｜1820 ~ 1820｜上级 奉天府 (Fengtian Fu)｜村镇 (cun zhen)
  - `hvd_164093` 清河场｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_167688` 清河城｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_146860` 清河店｜1911 ~ 1911｜上级 辽州 (Liao Zhou)｜村镇 (cun zhen)
  - `hvd_148205` 清河集｜1911 ~ 1911｜上级 祥符县 (Xiangfu Xian)｜村镇 (cun zhen)
  - `hvd_149245` 清河口｜1911 ~ 1911｜上级 孟津县 (Mengjin Xian)｜村镇 (cun zhen)
  - `hvd_15478` 清河门｜1820 ~ 1820｜上级 承德府 (Chengde Fu)｜村镇 (cun zhen)
  - `hvd_21038` 清河门｜1820 ~ 1820｜上级 锦州府 (Jinzhou Fu)｜村镇 (cun zhen)
  - `hvd_153162` 清河门｜1911 ~ 1911｜上级 阜新县 (Fuxin Xian)｜村镇 (cun zhen)
  - `hvd_136231` 清河铺｜1911 ~ 1911｜上级 大兴县 (Daxing Xian)｜村镇 (cun zhen)
  - `hvd_134685` 清河头镇｜1911 ~ 1911｜上级 开州 (Kai Zhou)｜村镇 (cun zhen)
  - `hvd_18172` 清河驿｜1820 ~ 1820｜上级 陈州府 (Chenzhou Fu)｜村镇 (cun zhen)
  - `hvd_148670` 清河驿｜1911 ~ 1911｜上级 西华县 (Xihua Xian)｜村镇 (cun zhen)
  - `hvd_20204` 清河镇｜1820 ~ 1820｜上级 武定府 (Wuding Fu)｜村镇 (cun zhen)
  - `hvd_163274` 清河镇｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_142841` 清河镇｜1911 ~ 1911｜上级 惠民县 (Huimin Xian)｜村镇 (cun zhen)
  - `hvd_125117` 清河镇｜1911 ~ 1911｜上级 赣榆县 (Ganyu Xian)｜村镇 (cun zhen)
  - `hvd_167450` 清河镇（西街基）｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
- **古桥**（查询「古桥」，2 命中）：
  - `hvd_148278` 古桥｜1911 ~ 1911｜上级 洧川县 (Chuan Xian)｜村镇 (cun zhen)
  - `hvd_129341` 古桥塘店｜1911 ~ 1911｜上级 湘潭县 (Xiangtan Xian)｜村镇 (cun zhen)
- **大河**（查询「大河」，42 命中）：
  - `hvd_163674` 大河｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_159111` 大河｜1911 ~ 1911｜上级 镇雄州 (Zhenxiong Zhou)｜村镇 (cun zhen)
  - `hvd_154636` 大河｜1911 ~ 1911｜上级 修仁县 (Xiuren Xian)｜村镇 (cun zhen)
  - `hvd_153696` 大河｜1911 ~ 1911｜上级 雒容县 (Luorong Xian)｜村镇 (cun zhen)
  - `hvd_149754` 大河｜1911 ~ 1911｜上级 桐柏县 (Tongbai Xian)｜村镇 (cun zhen)
  - `hvd_145736` 大河｜1911 ~ 1911｜上级 壶关县 (Huguan Xian)｜村镇 (cun zhen)
  - `hvd_112476` 大河郡｜-111 ~ -53｜上级 西汉 (Xihan)｜郡 (jun)
  - `hvd_112478` 大河郡｜-4 ~ 1｜上级 西汉 (Xihan)｜郡 (jun)
  - `hvd_127928` 大河岸铺｜1911 ~ 1911｜上级 罗田县 (Luotian Xian)｜村镇 (cun zhen)
  - `hvd_163607` 大河坝｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_132210` 大河坝｜1911 ~ 1911｜上级 洋县 (Yang Xian)｜村镇 (cun zhen)
  - `hvd_128843` 大河坝｜1911 ~ 1911｜上级 来凤县 (Laifeng Xian)｜村镇 (cun zhen)
  - `hvd_16532` 大河堡｜1820 ~ 1820｜上级 凉州府 (Liangzhou Fu)｜村镇 (cun zhen)
  - `hvd_162550` 大河边｜1911 ~ 1911｜上级 思南府 (Sinan Fu)｜村镇 (cun zhen)
  - `hvd_160039` 大河边｜1911 ~ 1911｜上级 景东厅 (Jingdong Ting)｜村镇 (cun zhen)
  - `hvd_160014` 大河边｜1911 ~ 1911｜上级 思茅厅 (Simao Ting)｜村镇 (cun zhen)
  - `hvd_159268` 大河边｜1911 ~ 1911｜上级 楚雄县 (Chuxiong Xian)｜村镇 (cun zhen)
  - `hvd_167113` 大河边｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_134864` 大河村｜1911 ~ 1911｜上级 雄县 (Xiong Xian)｜村镇 (cun zhen)
  - `hvd_151633` 大河店｜1911 ~ 1911｜上级 徽县 (Hui Xian)｜村镇 (cun zhen)
  - `hvd_161242` 大河渡｜1911 ~ 1911｜上级 独山州 (Dushan Zhou)｜村镇 (cun zhen)
  - `hvd_151008` 大河家｜1911 ~ 1911｜上级 河州 (He Zhou)｜村镇 (cun zhen)
  - `hvd_128411` 大河口｜1911 ~ 1911｜上级 随州 (Sui Zhou)｜村镇 (cun zhen)
  - `hvd_145274` 大河口｜1911 ~ 1911｜上级 翼城县 (Yicheng Xian)｜村镇 (cun zhen)
  - `hvd_160218` 大河口｜1911 ~ 1911｜上级 云南县 (Yunnan Xian)｜村镇 (cun zhen)
  - `hvd_162930` 大河口｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_150275` 大河里｜1911 ~ 1911｜上级 翼城县 (Yicheng Xian)｜村镇 (cun zhen)
  - `hvd_162741` 大河坪｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_18591` 大河埔｜1820 ~ 1820｜上级 黄州府 (Huangzhou Fu)｜村镇 (cun zhen)
  - `hvd_128012` 大河铺｜1911 ~ 1911｜上级 黄梅县 (Huangmei Xian)｜村镇 (cun zhen)
  - `hvd_23784` 大河市｜1820 ~ 1820｜上级 常熟县 (Changshu Xian)｜村镇 (cun zhen)
  - `hvd_139037` 大河市｜1911 ~ 1911｜上级 常熟县 (Changshu Xian)｜村镇 (cun zhen)
  - `hvd_165423` 大河滩｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_161212` 大河塘｜1911 ~ 1911｜上级 都匀县 (Duyun Xian)｜村镇 (cun zhen)
  - `hvd_144663` 大河套｜1911 ~ 1911｜上级 邱县 (Qiu Xian)｜村镇 (cun zhen)
  - `hvd_18206` 大河屯｜1820 ~ 1820｜上级 南阳府 (Nanyang Fu)｜村镇 (cun zhen)
  - `hvd_149585` 大河屯｜1911 ~ 1911｜上级 唐县 (Tang Xian)｜村镇 (cun zhen)
  - `hvd_159620` 大河湾｜1911 ~ 1911｜上级 建水县 (Jianshui Xian)｜村镇 (cun zhen)
  - `hvd_153430` 大河墟｜1911 ~ 1911｜上级 灵川县 (Lingchuan Xian)｜村镇 (cun zhen)
  - `hvd_168266` 大河沿子｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_150704` 大河驿｜1911 ~ 1911｜上级 武威县 (Wuwei Xian)｜村镇 (cun zhen)
  - `hvd_162882` 大河镇｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
- **新桥**（查询「新桥」，24 命中）：
  - `hvd_17123` 新桥｜1820 ~ 1820｜上级 肇庆府 (Zhaoqing Fu)｜村镇 (cun zhen)
  - `hvd_127555` 新桥｜1911 ~ 1911｜上级 武昌县 (Wuchang Xian)｜村镇 (cun zhen)
  - `hvd_129582` 新桥｜1911 ~ 1911｜上级 常宁县 (Changning Xian)｜村镇 (cun zhen)
  - `hvd_137086` 新桥｜1911 ~ 1911｜上级 闽清县 (Minqing Xian)｜村镇 (cun zhen)
  - `hvd_137662` 新桥｜1911 ~ 1911｜上级 长汀县 (Changting Xian)｜村镇 (cun zhen)
  - `hvd_163795` 新桥｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_154203` 新桥｜1911 ~ 1911｜上级 宾州 (Bin Zhou)｜村镇 (cun zhen)
  - `hvd_140166` 新桥｜1911 ~ 1911｜上级 兰溪县 (Lanxi Xian)｜村镇 (cun zhen)
  - `hvd_164919` 新桥场｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_164121` 新桥场｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_148694` 新桥集｜1911 ~ 1911｜上级 项城县 (Xiangcheng Xian)｜村镇 (cun zhen)
  - `hvd_148623` 新桥集｜1911 ~ 1911｜上级 永城县 (Yongcheng Xian)｜村镇 (cun zhen)
  - `hvd_23546` 新桥铺｜1820 ~ 1820｜上级 昌化县 (Changhua Xian)｜村镇 (cun zhen)
  - `hvd_138802` 新桥铺｜1911 ~ 1911｜上级 昌化县 (Changhua Xian)｜村镇 (cun zhen)
  - `hvd_138561` 新桥市｜1911 ~ 1911｜上级 漳平县 (Zhangping Xian)｜村镇 (cun zhen)
  - `hvd_137645` 新桥市｜1911 ~ 1911｜上级 泰宁县 (Taining Xian)｜村镇 (cun zhen)
  - `hvd_168224` 新桥湾｜1911 ~ 1911｜上级 （无）｜村镇 (cun zhen)
  - `hvd_16054` 新桥墟｜1820 ~ 1820｜上级 延平府 (Yanping Fu)｜村镇 (cun zhen)
  - `hvd_154841` 新桥墟｜1911 ~ 1911｜上级 郁林州 (Yulin Zhilizhou)｜村镇 (cun zhen)
  - `hvd_126679` 新桥墟汛｜1911 ~ 1911｜上级 高要县 (Gaoyao Xian)｜村镇 (cun zhen)
  - `hvd_15569` 新桥镇｜1820 ~ 1820｜上级 保定府 (Baoding Fu)｜村镇 (cun zhen)
  - `hvd_139673` 新桥镇｜1911 ~ 1911｜上级 象山县 (Xiangshan Xian)｜村镇 (cun zhen)
  - `hvd_134840` 新桥镇｜1911 ~ 1911｜上级 新城县 (Xincheng Xian)｜村镇 (cun zhen)
  - `hvd_125381` 新桥镇｜1911 ~ 1911｜上级 海门厅 (Haimen Ting)｜村镇 (cun zhen)

### 2. 命中全在异地（唯一/最佳命中不在京师域，不能直接当作本项目实体）

- **观音寺** → 12 命中，最佳 `hvd_128374` 观音寺｜1911 ~ 1911｜上级 应山县 (Yingshan Xian)
- **观音庵** → 1 命中，最佳 `hvd_162715` 观音庵｜1911 ~ 1911｜上级 （无）
- **关帝庙** → 3 命中，最佳 `hvd_133196` 关帝庙｜1911 ~ 1911｜上级 洋县 (Yang Xian)
- **古桥** → 2 命中，最佳 `hvd_148278` 古桥｜1911 ~ 1911｜上级 洧川县 (Chuan Xian)
- **大河** → 42 命中，最佳 `hvd_163674` 大河｜1911 ~ 1911｜上级 （无）
- **白石桥** → 1 命中，最佳 `hvd_141704` 白石桥｜1911 ~ 1911｜上级 玉山县 (Yushan Xian)
- **新桥** → 24 命中，最佳 `hvd_17123` 新桥｜1820 ~ 1820｜上级 肇庆府 (Zhaoqing Fu)

### 3. 零命中候选的形态观察（保留不否决，仅记录形态类型）

零命中 59 个，按形态归类：

- **疑似挖掘器分割噪声**（动词短语/日期/句法残片，非自由地名）: 名覺生寺、左繞山、向藏漢經厂、方钟樓、異他钟、懸大钟一口、十数仆地上、旋梯、道傍观、六月十六日、觉生寺大钟殿、大雄宝殿、命勿毀高梁河、供守卫圆明园、《三山五园、重要重修、建公路桥、桥北归海淀、大运河、该闸、船坞、高梁桥是长河、历史旧安河桥、建木桥、旧料、旧桥、控水闸、常水输瓮山泊、洪水泄清河、不说桥、消失
- **形似真实地名但 TGAZ 未收录**（CHGIS 收政区级+1911 年聚落，不含城内寺观殿宇与 mikro-toponym）: 永定河、戾陵堰、车箱渠、通惠河、绮春三园、水礳、保福寺、萧家河、蓝靛厂、五圣庵、达官村、西二旗、华严觉海、天王殿、長源、永澤、資安、广潤、南牌坊、北牌坊、德胜门外安河、水渠、界桥、桥上置闸、转河、公交安河桥、地铁安河桥、龙背村
- **强佐证**: 连「永定河」「通惠河」这类一等历史河流在本库也是 0 命中（实测复验），坐实 TGAZ placename 库不含自然河流实体——河渠类候选零命中只能说明「超出收录范围」，不能反推实体不存在。

### 4. 查询异常实录

本轮 68 次查询全部返回合法 JSON（body 均以 `{` 开头），无失败/截断。

### 5. 书证明细（逐候选 occurrence）

- **永定河** ←「永定河」 suffix_scan @div_sjz_v14_baqiushui（《shuijingzhu》）
- **戾陵堰** ←「戾陵堰」 suffix_scan @div_sjz_v14_baqiushui（《shuijingzhu》）
- **车箱渠** ←「车箱渠」 suffix_scan @div_sjz_v14_baqiushui（《shuijingzhu》）
- **通惠河** ←「通惠河」 suffix_scan @div_yuanshi_hequ_3（《yuanshi》）
- **通惠河** ←「通惠河」 suffix_scan @div_yuanshi_hequ_gl（《yuanshi》）
- **绮春三园** ←「绮春三园」 suffix_scan @div_ymy_yuan_yange（《ymy_yuan》）
- **水礳** ←「水礳」 cue:坐落 @div_bqtz116_yingjian（《bqtz》）
- **保福寺** ←「保福寺」 cue:坐落 @div_bqtz116_yingjian（《bqtz》）
- **萧家河** ←「蕭家河」 cue:坐落 @div_bqtz116_yingjian（《bqtz》）
- **萧家河** ←「蕭家河」 suffix_scan @div_rxjwkc72_baqi（《rxjwkc》）
- **蓝靛厂** ←「藍靛廠」 cue:坐落 @div_bqtz116_yingjian（《bqtz》）
- **五圣庵** ←「五聖菴」 cue:有 @div_rxjwkc99_jiaojiong（《rxjwkc》）
- **观音寺** ←「觀音寺」 suffix_scan @div_rxjwkc99_jiaojiong（《rxjwkc》）
- **观音庵** ←「觀音菴」 cue:有 @div_rxjwkc100_xijiaojing（《rxjwkc》）
- **观音庵** ←「觀音菴」 suffix_scan @div_rxjwkc100_xijiaojing（《rxjwkc》）
- **达官村** ←「達官村」 suffix_scan @div_rxjwkc100_xijiaojing（《rxjwkc》）
- **关帝庙** ←「關帝廟」 suffix_scan @div_rxjwkc100_xijiaojing（《rxjwkc》）
- **关帝庙** ←「關帝廟」 suffix_scan @div_rxjwkc100_xijiaojing（《rxjwkc》）
- **金山** ←「金山」 suffix_scan @div_rxjwkc100_xijiaojing（《rxjwkc》）
- **清河** ←「清河」 suffix_scan @div_diquminglu_xisanqi（《hd_diqumingzhi》）
- **清河** ←「清河」 suffix_scan @div_minglu2_ahc（《minglu_2》）
- **清河** ←「清河」 suffix_scan @div_hd_anhe1965（《hd_gov_open》）
- **清河** ←「清河」 suffix_scan @div_bma_anhe（《bma_1929》）
- **西二旗** ←「西二旗」 suffix_scan @div_diquminglu_xisanqi（《hd_diqumingzhi》）
- **名覺生寺** ←「名覺生寺」 suffix_scan @div_beiwen_quanbei（《jueshengsi_beiwen》）
- **左繞山** ←「左繞山」 suffix_scan @div_beiwen_quanbei（《jueshengsi_beiwen》）
- **向藏漢經厂** ←「向藏漢經廠」 suffix_scan @div_djjwl_hjc（《dijingjingwulue》）
- **方钟樓** ←「方鐘樓」 cue:有 @div_cakh_wanshousi（《changankehua》）
- **異他钟** ←「異他鐘」 cue:有 @div_cakh_wanshousi（《changankehua》）
- **懸大钟一口** ←「懸大鐘一口」 suffix_scan @div_zzz_dazhong（《zuozhongzhi》）
- **十数仆地上** ←「十數仆地上」 cue:有 @div_cmmyl_zhuzhongchang（《chunmengmengyulu》）
- **旋梯** ←「旋梯」 cue:有 @div_yjsj_jueshengsi（《yanjingsuishiji》）
- **道傍观** ←「道傍觀」 suffix_scan @div_yhd_wanshousi（《yuanzhonglang》）
- **六月十六日** ←「六月十六日」 cue:為 @div_rxjwkc100_wanshousi（《rxjwkc》）
- **觉生寺大钟殿** ←「觉生寺大钟殿」 suffix_scan @div_dzs_yange（《dzs_history》）
- **华严觉海** ←「华严觉海」 suffix_scan @div_dzs_yange（《dzs_history》）
- **天王殿** ←「天王殿」 suffix_scan @div_dzs_yange（《dzs_history》）
- **大雄宝殿** ←「大雄宝殿」 suffix_scan @div_dzs_yange（《dzs_history》）
- **命勿毀高梁河** ←「命勿毀高梁河」 suffix_scan @div_jinshi_zhaguan（《jinshi》）
- **長源** ←「長源」 cue:曰 @div_rxjwkc_gl（《rxjwkc》）
- **永澤** ←「永澤」 cue:曰 @div_rxjwkc_gl（《rxjwkc》）
- **資安** ←「資安」 cue:曰 @div_rxjwkc_gl（《rxjwkc》）
- **广潤** ←「廣潤」 cue:曰 @div_rxjwkc_gl（《rxjwkc》）
- **南牌坊** ←「南牌坊」 suffix_scan @div_rxjwkc_gl（《rxjwkc》）
- **北牌坊** ←「北牌坊」 suffix_scan @div_rxjwkc_gl（《rxjwkc》）
- **德胜门外安河** ←「德胜门外安河」 suffix_scan @div_zhiguan_v8（《lidaizhiguangbiao》）
- **供守卫圆明园** ←「供守卫圆明园」 suffix_scan @div_zhiguan_v8（《lidaizhiguangbiao》）
- **《三山五园** ←「《三山五园」 suffix_scan @div_minglu2_ahc（《minglu_2》）
- **《三山五园** ←「《三山五园」 suffix_scan @div_sxwj_muzhuang（《sxwj》）
- **水渠** ←「水渠」 suffix_scan @div_minglu2_ahc（《minglu_2》）
- **水渠** ←「水渠」 suffix_scan @div_hd_anhe1965（《hd_gov_open》）
- **水渠** ←「水渠」 suffix_scan @div_anhe_xiaoshi（《anheqiao_xiaoshi》）
- **重要重修** ←「重要重修」 cue:有 @div_wjbz_gl（《wjbz_open》）
- **古桥** ←「古桥」 suffix_scan @div_wjbz_gl（《wjbz_open》）
- **建公路桥** ←「建公路桥」 suffix_scan @div_wjbz_gl（《wjbz_open》）
- **桥北归海淀** ←「桥北归海淀」 suffix_scan @div_wjbz_gl（《wjbz_open》）
- **界桥** ←「界桥」 suffix_scan @div_wjbz_gl（《wjbz_open》）
- **大运河** ←「大运河」 suffix_scan @div_wjbz_gl（《wjbz_open》）
- **桥上置闸** ←「桥上置闸」 suffix_scan @div_wjbz_gl（《wjbz_open》）
- **该闸** ←「该闸」 suffix_scan @div_wjbz_gl（《wjbz_open》）
- **船坞** ←「船坞」 cue:有 @div_hd_yht（《hd_gov_open》）
- **高梁桥是长河** ←「高梁桥是长河」 suffix_scan @div_hd_zhuanhe（《hd_gov_open》）
- **转河** ←「转河」 suffix_scan @div_hd_zhuanhe（《hd_gov_open》）
- **大河** ←「大河」 suffix_scan @div_hd_zhuanhe（《hd_gov_open》）
- **白石桥** ←「白石桥」 suffix_scan @div_hd_zhuanhe（《hd_gov_open》）
- **历史旧安河桥** ←「历史旧安河桥」 suffix_scan @div_hd_anhe1965（《hd_gov_open》）
- **历史旧安河桥** ←「历史旧安河桥」 suffix_scan @div_bma_anhe（《bma_1929》）
- **新桥** ←「新桥」 suffix_scan @div_hd_anhe1965（《hd_gov_open》）
- **建木桥** ←「建木桥」 suffix_scan @div_anhe_xiaoshi（《anheqiao_xiaoshi》）
- **旧料** ←「旧料」 cue:有 @div_anhe_xiaoshi（《anheqiao_xiaoshi》）
- **旧桥** ←「旧桥」 suffix_scan @div_anhe_xiaoshi（《anheqiao_xiaoshi》）
- **控水闸** ←「控水闸」 cue:有 @div_anhe_xiaoshi（《anheqiao_xiaoshi》）
- **常水输瓮山泊** ←「常水输瓮山泊」 suffix_scan @div_anhe_xiaoshi（《anheqiao_xiaoshi》）
- **洪水泄清河** ←「洪水泄清河」 suffix_scan @div_anhe_xiaoshi（《anheqiao_xiaoshi》）
- **不说桥** ←「不说桥」 suffix_scan @div_anhe_xiaoshi（《anheqiao_xiaoshi》）
- **消失** ←「消失」 cue:有 @div_anhe_xiaoshi（《anheqiao_xiaoshi》）
- **公交安河桥** ←「公交安河桥」 suffix_scan @div_anhe_xiaoshi（《anheqiao_xiaoshi》）
- **地铁安河桥** ←「地铁安河桥」 suffix_scan @div_anhe_xiaoshi（《anheqiao_xiaoshi》）
- **地铁安河桥** ←「地铁安河桥」 suffix_scan @div_anhe_xiaoshi（《anheqiao_xiaoshi》）
- **龙背村** ←「龙背村」 suffix_scan @div_anhe_xiaoshi（《anheqiao_xiaoshi》）

## 结论

首轮真实裁决覆盖全部 68 个候选：TGAZ 命中 9 个（其中 8 个 mid→high，其余命中时已是 high），零命中 59 个按纪律保留原置信；同名异地多命中 7 个已单列待消歧。
裁决后置信分布: high=14, mid=54。
注: 本报告只记录外部裁决结果，未回写任何 KB/calibration 模块；入库仍须过人工九维闸门（spec §0）。
