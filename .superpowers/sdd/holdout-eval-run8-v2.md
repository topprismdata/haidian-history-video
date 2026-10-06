# Holdout v1 首轮跑分（run1）

- 快照：`haidian_kg/evaluation/holdout_v2.jsonl`（60 段，text_sha1 全量校验通过）
- 引擎：ClosureExpander `v5` / 规则档 `rp-v5`
- 真值：calibration 8 模块 48 实体字形表（独立路径，评分代码零 expansion 依赖）；**代理金标**——mention precision 为下界（KB 未收录的真实地名计 FP），见「偏差」

## 五指标 vs 冻结闸门

| 指标 | 实测 | 阈值 | 判定 |
|---|---|---|---|
| mention precision | 0.1654 | >= 0.90 | ❌ 不过 |
| mention recall | 0.3147 | >= 0.85 | ❌ 不过 |
| high-conf precision | 0.1250 | >= 0.95 | ❌ 不过 |
| duplication | 0.0000 | <= 0.05 | ✅ 过 |
| collision | 0.0000 | == 0.00 | ✅ 过 |
| mention F1（辅助） | 0.2169 | — | — |

**闸门结论：未全过 ❌**（计数 TP=45 FP=227 FN=98；gold 实体 14，假说总数 226）

## 逐段明细

| 段 | 金标 | 预测 | TP | FP | FN | high-conf |
|---|---|---|---|---|---|---|
| `pilot_rixia_juan076:L1-L1` | 3 | 3 | 1 | 2 | 2 | 0/1 |
| `pilot_rixia_juan076:L2-L9` | 2 | 3 | 2 | 1 | 0 | 0/0 |
| `pilot_rixia_juan076:L10-L12` | 3 | 10 | 1 | 9 | 2 | 1/8 |
| `pilot_rixia_juan076:L15-L21` | 2 | 0 | 0 | 0 | 2 | 0/0 |
| `pilot_rixia_juan076:L22-L28` | 1 | 0 | 0 | 0 | 1 | 0/0 |
| `pilot_rixia_juan076:L29-L33` | 1 | 2 | 0 | 2 | 1 | 0/0 |
| `pilot_rixia_juan076:L34-L40` | 1 | 1 | 0 | 1 | 1 | 0/0 |
| `pilot_rixia_juan076:L41-L46` | 2 | 0 | 0 | 0 | 2 | 0/0 |
| `pilot_rixia_juan076:L51-L63` | 2 | 2 | 1 | 1 | 1 | 0/1 |
| `pilot_rixia_juan076:L64-L68` | 1 | 1 | 0 | 1 | 1 | 0/0 |
| `pilot_rixia_juan076:L69-L72` | 2 | 1 | 0 | 1 | 2 | 0/0 |
| `pilot_rixia_juan076:L73-L83` | 4 | 5 | 1 | 4 | 3 | 0/1 |
| `pilot_rixia_juan076:L84-L91` | 1 | 1 | 0 | 1 | 1 | 0/0 |
| `pilot_rixia_juan076:L92-L95` | 4 | 4 | 2 | 2 | 2 | 0/0 |
| `pilot_rixia_juan076:L96-L102` | 1 | 1 | 0 | 1 | 1 | 0/0 |
| `pilot_rixia_juan076:L103-L107` | 1 | 4 | 0 | 4 | 1 | 0/0 |
| `pilot_rixia_juan076:L108-L111` | 3 | 4 | 1 | 3 | 2 | 0/1 |
| `pilot_rixia_juan076:L112-L120` | 2 | 3 | 0 | 3 | 2 | 0/1 |
| `pilot_rixia_juan076:L128-L134` | 1 | 0 | 0 | 0 | 1 | 0/0 |
| `pilot_rixia_juan076:L135-L140` | 1 | 1 | 0 | 1 | 1 | 0/0 |
| `pilot_rixia_juan076:L141-L148` | 3 | 4 | 1 | 3 | 2 | 0/3 |
| `pilot_rixia_juan076:L149-L157` | 4 | 9 | 2 | 7 | 2 | 1/6 |
| `pilot_rixia_juan076:L158-L165` | 0 | 1 | 0 | 1 | 0 | 0/0 |
| `pilot_rixia_juan076:L170-L180` | 1 | 1 | 0 | 1 | 1 | 0/1 |
| `pilot_rixia_juan076:L181-L189` | 1 | 4 | 0 | 4 | 1 | 0/2 |
| `pilot_rixia_juan076:L203-L212` | 2 | 1 | 1 | 0 | 1 | 0/0 |
| `pilot_rixia_juan076:L213-L216` | 2 | 3 | 0 | 3 | 2 | 0/0 |
| `pilot_rixia_juan076:L217-L230` | 7 | 7 | 2 | 5 | 5 | 2/6 |
| `pilot_rixia_juan076:L231-L248` | 6 | 8 | 3 | 5 | 3 | 2/6 |
| `pilot_rixia_juan076:L249-L259` | 4 | 3 | 2 | 1 | 2 | 2/2 |
| `pilot_rixia_juan076:L263-L267` | 2 | 4 | 1 | 3 | 1 | 1/2 |
| `pilot_rixia_juan076:L280-L286` | 1 | 2 | 0 | 2 | 1 | 0/0 |
| `pilot_rixia_juan076:L287-L300` | 1 | 1 | 0 | 1 | 1 | 0/0 |
| `pilot_rixia_juan076:L322-L331` | 1 | 2 | 1 | 1 | 0 | 0/1 |
| `pilot_rixia_juan076:L335-L350` | 2 | 17 | 0 | 17 | 2 | 0/13 |
| `pilot_rixia_juan076:L351-L360` | 0 | 2 | 0 | 2 | 0 | 0/2 |
| `pilot_rixia_juan076:L361-L366` | 1 | 1 | 0 | 1 | 1 | 0/0 |
| `pilot_rixia_juan076:L367-L372` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `pilot_rixia_juan076:L373-L377` | 1 | 1 | 0 | 1 | 1 | 0/1 |
| `pilot_rixia_juan076:L381-L388` | 1 | 1 | 0 | 1 | 1 | 0/0 |
| `pilot_rixia_juan076:L389-L393` | 1 | 2 | 0 | 2 | 1 | 0/1 |
| `pilot_rixia_juan076:L394-L400` | 0 | 2 | 0 | 2 | 0 | 0/1 |
| `pilot_rixia_juan076:L401-L412` | 1 | 2 | 1 | 1 | 0 | 0/0 |
| `pilot_rixia_juan076:L426-L429` | 1 | 2 | 0 | 2 | 1 | 0/2 |
| `pilot_rixia_juan079:L1-L4` | 4 | 6 | 2 | 4 | 2 | 0/3 |
| `pilot_rixia_juan079:L5-L16` | 6 | 17 | 2 | 15 | 4 | 1/8 |
| `pilot_rixia_juan079:L17-L22` | 1 | 1 | 0 | 1 | 1 | 0/0 |
| `pilot_rixia_juan079:L23-L25` | 6 | 9 | 3 | 6 | 3 | 1/3 |
| `pilot_rixia_juan079:L26-L28` | 5 | 3 | 2 | 1 | 3 | 0/0 |
| `pilot_rixia_juan079:L29-L38` | 2 | 3 | 1 | 2 | 1 | 0/2 |
| `pilot_rixia_juan079:L39-L48` | 0 | 1 | 0 | 1 | 0 | 0/0 |
| `pilot_rixia_juan079:L49-L56` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `pilot_rixia_juan079:L57-L58` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `pilot_rixia_juan079:L59-L64` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `pilot_rixia_juan079:L65-L75` | 0 | 4 | 0 | 4 | 0 | 0/0 |
| `pilot_rixia_juan079:L76-L90` | 11 | 18 | 5 | 13 | 6 | 2/9 |
| `pilot_rixia_juan079:L91-L103` | 0 | 23 | 0 | 23 | 0 | 0/21 |
| `pilot_rixia_juan079:L104-L116` | 1 | 3 | 0 | 3 | 1 | 0/0 |
| `pilot_rixia_juan079:L117-L123` | 4 | 22 | 1 | 21 | 3 | 0/13 |
| `pilot_rixia_juan079:L124-L134` | 22 | 36 | 6 | 30 | 16 | 5/23 |

## 漏检归因（98 条，100% 逐条）

**cue-window-narrow（3 条）**

- `pilot_rixia_juan079:L117-L123`「髙梁水」（KB 字形「高梁水」）：仅 cue 窗通道可达（「水」非收录后缀），窗内未收拢该字形
- `pilot_rixia_juan079:L124-L134`「髙梁水」（KB 字形「高梁水」）：仅 cue 窗通道可达（「水」非收录后缀），窗内未收拢该字形
- `pilot_rixia_juan079:L124-L134`「髙梁水」（KB 字形「高梁水」）：仅 cue 窗通道可达（「水」非收录后缀），窗内未收拢该字形
**erosion（16 条）**

- `pilot_rixia_juan076:L1-L1`「南海淀」（KB 字形「南海淀」）：命中区域但字形不合：引擎发「南海淀大河莊」（suffix_scan），金标「南海淀」
- `pilot_rixia_juan076:L10-L12`「海淀」（KB 字形「海淀」）：命中区域但字形不合：引擎发「海淀淀」（cue:曰），金标「海淀」
- `pilot_rixia_juan076:L64-L68`「暢春園」（KB 字形「畅春园」）：命中区域但字形不合：引擎发「御製詣暢春園」（suffix_scan），金标「暢春園」
- `pilot_rixia_juan076:L73-L83`「暢春園」（KB 字形「畅春园」）：命中区域但字形不合：引擎发「御製詣暢春園」（suffix_scan），金标「暢春園」
- `pilot_rixia_juan076:L73-L83`「暢春園」（KB 字形「畅春园」）：命中区域但字形不合：引擎发「日赴暢春園」（suffix_scan），金标「暢春園」
- `pilot_rixia_juan076:L103-L107`「暢春園」（KB 字形「畅春园」）：命中区域但字形不合：引擎发「御製詣暢春園」（suffix_scan），金标「暢春園」
- `pilot_rixia_juan076:L112-L120`「暢春園」（KB 字形「畅春园」）：命中区域但字形不合：引擎发「宫門懸暢春園」（suffix_scan），金标「暢春園」
- `pilot_rixia_juan076:L141-L148`「香山」（KB 字形「香山」）：命中区域但字形不合：引擎发「林香山」（cue:為），金标「香山」
- `pilot_rixia_juan076:L181-L189`「暢春園」（KB 字形「畅春园」）：命中区域但字形不合：引擎发「太樸　暢春園」（cue:為），金标「暢春園」
- `pilot_rixia_juan076:L213-L216`「暢春園」（KB 字形「畅春园」）：命中区域但字形不合：引擎发「三楹　暢春園」（suffix_scan），金标「暢春園」
- `pilot_rixia_juan076:L217-L230`「恩慕寺」（KB 字形「恩慕寺」）：命中区域但字形不合：引擎发「恩慕寺殿」（cue:為），金标「恩慕寺」
- `pilot_rixia_juan076:L335-L350`「暢春園」（KB 字形「畅春园」）：命中区域但字形不合：引擎发「　暢春園」（suffix_scan），金标「暢春園」
- `pilot_rixia_juan079:L23-L25`「昆明湖」（KB 字形「昆明湖」）：命中区域但字形不合：引擎发「昆明湖經長河」（cue:為），金标「昆明湖」
- `pilot_rixia_juan079:L104-L116`「暢春園」（KB 字形「畅春园」）：命中区域但字形不合：引擎发「形北望暢春園」（suffix_scan），金标「暢春園」
- `pilot_rixia_juan079:L117-L123`「海淀」（KB 字形「海淀」）：命中区域但字形不合：引擎发「武清侯海淀」（suffix_scan），金标「海淀」
- `pilot_rixia_juan079:L124-L134`「髙梁橋」（KB 字形「高梁桥」）：命中区域但字形不合：引擎发「原髙梁橋」（suffix_scan），金标「髙梁橋」
**overlapped-hit-discarded（4 条）**

- `pilot_rixia_juan076:L73-L83`「暢春園」（KB 字形「畅春园」）：后缀命中与更右的采纳区间重叠，按子词规则让位
- `pilot_rixia_juan076:L112-L120`「暢春園」（KB 字形「畅春园」）：后缀命中与更右的采纳区间重叠，按子词规则让位
- `pilot_rixia_juan076:L335-L350`「暢春園」（KB 字形「畅春园」）：后缀命中与更右的采纳区间重叠，按子词规则让位
- `pilot_rixia_juan079:L117-L123`「海淀」（KB 字形「海淀」）：后缀命中与更右的采纳区间重叠，按子词规则让位
**same-form-elsewhere（45 条）**

- `pilot_rixia_juan076:L1-L1`「暢春園」（KB 字形「畅春园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L51-L63`「暢春園」（KB 字形「畅春园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L92-L95`「暢春園」（KB 字形「畅春园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L108-L111`「暢春園」（KB 字形「畅春园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L108-L111`「暢春園」（KB 字形「畅春园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L141-L148`「暢春園」（KB 字形「畅春园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L149-L157`「暢春園」（KB 字形「畅春园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L217-L230`「恩佑寺」（KB 字形「恩佑寺」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L217-L230`「恩佑寺」（KB 字形「恩佑寺」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L217-L230`「恩佑寺」（KB 字形「恩佑寺」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L217-L230`「暢春園」（KB 字形「畅春园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L231-L248`「恩佑寺」（KB 字形「恩佑寺」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L231-L248`「恩慕寺」（KB 字形「恩慕寺」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L231-L248`「恩慕寺」（KB 字形「恩慕寺」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L249-L259`「恩佑寺」（KB 字形「恩佑寺」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan076:L263-L267`「暢春園」（KB 字形「畅春园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L1-L4`「泉宗廟」（KB 字形「泉宗庙」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L1-L4`「泉宗廟」（KB 字形「泉宗庙」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L5-L16`「泉宗廟」（KB 字形「泉宗庙」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L5-L16`「泉宗廟」（KB 字形「泉宗庙」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L5-L16`「泉宗廟」（KB 字形「泉宗庙」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L23-L25`「萬泉莊」（KB 字形「万泉庄」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L23-L25`「萬泉莊」（KB 字形「万泉庄」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L26-L28`「暢春園」（KB 字形「畅春园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L26-L28`「暢春園」（KB 字形「畅春园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L26-L28`「泉宗廟」（KB 字形「泉宗庙」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L29-L38`「泉宗廟」（KB 字形「泉宗庙」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L76-L90`「萬泉莊」（KB 字形「万泉庄」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L76-L90`「萬泉莊」（KB 字形「万泉庄」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L76-L90`「萬泉莊」（KB 字形「万泉庄」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L76-L90`「萬泉莊」（KB 字形「万泉庄」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L76-L90`「萬泉莊」（KB 字形「万泉庄」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L76-L90`「萬泉莊」（KB 字形「万泉庄」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L124-L134`「海淀」（KB 字形「海淀」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L124-L134`「南海淀」（KB 字形「南海淀」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L124-L134`「海淀」（KB 字形「海淀」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L124-L134`「海淀」（KB 字形「海淀」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L124-L134`「海淀」（KB 字形「海淀」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L124-L134`「海淀」（KB 字形「海淀」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L124-L134`「海淀」（KB 字形「海淀」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L124-L134`「海淀」（KB 字形「海淀」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L124-L134`「海淀」（KB 字形「海淀」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L124-L134`「海淀」（KB 字形「海淀」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L124-L134`「海淀」（KB 字形「海淀」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `pilot_rixia_juan079:L124-L134`「海淀」（KB 字形「海淀」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
**walkback-overrun（30 条）**

- `pilot_rixia_juan076:L10-L12`「暢春園」（KB 字形「畅春园」）：回溯跨度 10 字 > 6 上限（「聖祖仁皇…」），该命中作废
- `pilot_rixia_juan076:L15-L21`「暢春園」（KB 字形「畅春园」）：回溯跨度 10 字 > 6 上限（「乾隆六年…」），该命中作废
- `pilot_rixia_juan076:L15-L21`「暢春園」（KB 字形「畅春园」）：回溯跨度 10 字 > 6 上限（「乾隆六年…」），该命中作废
- `pilot_rixia_juan076:L22-L28`「暢春園」（KB 字形「畅春园」）：回溯跨度 10 字 > 6 上限（「乾隆七年…」），该命中作废
- `pilot_rixia_juan076:L29-L33`「暢春園」（KB 字形「畅春园」）：回溯跨度 12 字 > 6 上限（「乾隆九年…」），该命中作废
- `pilot_rixia_juan076:L34-L40`「暢春園」（KB 字形「畅春园」）：回溯跨度 12 字 > 6 上限（「乾隆二十…」），该命中作废
- `pilot_rixia_juan076:L41-L46`「暢春園」（KB 字形「畅春园」）：回溯跨度 12 字 > 6 上限（「乾隆二十…」），该命中作废
- `pilot_rixia_juan076:L41-L46`「暢春園」（KB 字形「畅春园」）：回溯跨度 12 字 > 6 上限（「乾隆二十…」），该命中作废
- `pilot_rixia_juan076:L69-L72`「暢春園」（KB 字形「畅春园」）：回溯跨度 15 字 > 6 上限（「乾隆三十…」），该命中作废
- `pilot_rixia_juan076:L69-L72`「暢春園」（KB 字形「畅春园」）：回溯跨度 15 字 > 6 上限（「乾隆三十…」），该命中作废
- `pilot_rixia_juan076:L84-L91`「暢春園」（KB 字形「畅春园」）：回溯跨度 10 字 > 6 上限（「御製盤山…」），该命中作废
- `pilot_rixia_juan076:L92-L95`「昆明湖」（KB 字形「昆明湖」）：回溯跨度 10 字 > 6 上限（「御製玉河…」），该命中作废
- `pilot_rixia_juan076:L96-L102`「暢春園」（KB 字形「畅春园」）：回溯跨度 16 字 > 6 上限（「乾隆四十…」），该命中作废
- `pilot_rixia_juan076:L128-L134`「暢春園」（KB 字形「畅春园」）：回溯跨度 11 字 > 6 上限（「乾隆二十…」），该命中作废
- `pilot_rixia_juan076:L135-L140`「暢春園」（KB 字形「畅春园」）：回溯跨度 12 字 > 6 上限（「乾隆二十…」），该命中作废
- `pilot_rixia_juan076:L149-L157`「香山」（KB 字形「香山」）：回溯跨度 7 字 > 6 上限（「嘉蔭積芳…」），该命中作废
- `pilot_rixia_juan076:L170-L180`「暢春園」（KB 字形「畅春园」）：回溯跨度 7 字 > 6 上限（「府君廟　…」），该命中作废
- `pilot_rixia_juan076:L203-L212`「暢春園」（KB 字形「畅春园」）：回溯跨度 17 字 > 6 上限（「乾隆三十…」），该命中作废
- `pilot_rixia_juan076:L213-L216`「恩佑寺」（KB 字形「恩佑寺」）：回溯跨度 8 字 > 6 上限（「篇餘不備…」），该命中作废
- `pilot_rixia_juan076:L249-L259`「恩慕寺」（KB 字形「恩慕寺」）：回溯跨度 11 字 > 6 上限（「乾隆四十…」），该命中作废
- `pilot_rixia_juan076:L280-L286`「暢春園」（KB 字形「畅春园」）：回溯跨度 8 字 > 6 上限（「蕙畹芝原…」），该命中作废
- `pilot_rixia_juan076:L287-L300`「暢春園」（KB 字形「畅春园」）：回溯跨度 12 字 > 6 上限（「所我皇上…」），该命中作废
- `pilot_rixia_juan076:L361-L366`「暢春園」（KB 字形「畅春园」）：回溯跨度 15 字 > 6 上限（「乾隆十二…」），该命中作废
- `pilot_rixia_juan076:L373-L377`「暢春園」（KB 字形「畅春园」）：回溯跨度 7 字 > 6 上限（「流文亭　…」），该命中作废
- `pilot_rixia_juan076:L381-L388`「暢春園」（KB 字形「畅春园」）：回溯跨度 15 字 > 6 上限（「乾隆十三…」），该命中作废
- `pilot_rixia_juan076:L389-L393`「暢春園」（KB 字形「畅春园」）：回溯跨度 8 字 > 6 上限（「俯鏡清流…」），该命中作废
- `pilot_rixia_juan076:L426-L429`「暢春園」（KB 字形「畅春园」）：回溯跨度 7 字 > 6 上限（「紫雲堂　…」），该命中作废
- `pilot_rixia_juan079:L5-L16`「萬泉莊」（KB 字形「万泉庄」）：回溯跨度 14 字 > 6 上限（「皇上御書…」），该命中作废
- `pilot_rixia_juan079:L17-L22`「泉宗廟」（KB 字形「泉宗庙」）：回溯跨度 16 字 > 6 上限（「乾隆三十…」），该命中作废
- `pilot_rixia_juan079:L124-L134`「萬泉莊」（KB 字形「万泉庄」）：回溯跨度 9 字 > 6 上限（「訛也㳟繹…」），该命中作废

## 误报归因（227 条，100% 逐条）

**boundary-splice（13 条）**

- `pilot_rixia_juan076:L149-L157`「外大小河」（cue:曰/high）：头带方位/虚词「外」，回溯边界没收干净
- `pilot_rixia_juan076:L149-L157`「西北門五空閘」（suffix_scan/mid）：头带方位/虚词「西」，回溯边界没收干净
- `pilot_rixia_juan076:L149-L157`「南河」（cue:為/high）：头带方位/虚词「南」，回溯边界没收干净
- `pilot_rixia_juan076:L181-L189`「北轉山」（suffix_scan/mid）：头带方位/虚词「北」，回溯边界没收干净
- `pilot_rixia_juan076:L181-L189`「西臨湖」（cue:為/high）：头带方位/虚词「西」，回溯边界没收干净
- `pilot_rixia_juan076:L335-L350`「北小門登山」（suffix_scan/mid）：头带方位/虚词「北」，回溯边界没收干净
- `pilot_rixia_juan076:L389-L393`「西過紅橋」（suffix_scan/mid）：头带方位/虚词「西」，回溯边界没收干净
- `pilot_rixia_juan076:L394-L400`「西花園」（cue:即/high）：头带方位/虚词「西」，回溯边界没收干净
- `pilot_rixia_juan079:L5-L16`「西山」（suffix_scan/mid）：头带方位/虚词「西」，回溯边界没收干净
- `pilot_rixia_juan079:L117-L123`「南淀北淀」（cue:有/high）：头带方位/虚词「南」，回溯边界没收干净
- `pilot_rixia_juan079:L117-L123`「西山」（suffix_scan/mid）：头带方位/虚词「西」，回溯边界没收干净
- `pilot_rixia_juan079:L124-L134`「上元村」（cue:曰/high）：头带方位/虚词「上」，回溯边界没收干净
- `pilot_rixia_juan079:L124-L134`「上流是勺園」（suffix_scan/mid）：头带方位/虚词「上」，回溯边界没收干净
**erosion（35 条）**

- `pilot_rixia_juan076:L1-L1`「南海淀大河莊」（suffix_scan/mid）：与金标「南海淀」span 重叠但字形不合（引擎「南海淀大河莊」vs 金标「南海淀」）
- `pilot_rixia_juan076:L1-L1`「竒暢春園」（cue:有/high）：与金标「暢春園」span 重叠但字形不合（引擎「竒暢春園」vs 金标「暢春園」）
- `pilot_rixia_juan076:L10-L12`「海淀淀」（cue:曰/high）：与金标「海淀」span 重叠但字形不合（引擎「海淀淀」vs 金标「海淀」）
- `pilot_rixia_juan076:L64-L68`「御製詣暢春園」（suffix_scan/mid）：与金标「暢春園」span 重叠但字形不合（引擎「御製詣暢春園」vs 金标「暢春園」）
- `pilot_rixia_juan076:L73-L83`「御製詣暢春園」（suffix_scan/mid）：与金标「暢春園」span 重叠但字形不合（引擎「御製詣暢春園」vs 金标「暢春園」）
- `pilot_rixia_juan076:L73-L83`「日赴暢春園」（suffix_scan/mid）：与金标「暢春園」span 重叠但字形不合（引擎「日赴暢春園」vs 金标「暢春園」）
- `pilot_rixia_juan076:L92-L95`「斯須暢春園」（suffix_scan/mid）：与金标「暢春園」span 重叠但字形不合（引擎「斯須暢春園」vs 金标「暢春園」）
- `pilot_rixia_juan076:L103-L107`「御製詣暢春園」（suffix_scan/mid）：与金标「暢春園」span 重叠但字形不合（引擎「御製詣暢春園」vs 金标「暢春園」）
- `pilot_rixia_juan076:L108-L111`「五楹　暢春園」（suffix_scan/mid）：与金标「暢春園」span 重叠但字形不合（引擎「五楹　暢春園」vs 金标「暢春園」）
- `pilot_rixia_juan076:L112-L120`「宫門懸暢春園」（suffix_scan/mid）：与金标「暢春園」span 重叠但字形不合（引擎「宫門懸暢春園」vs 金标「暢春園」）
- `pilot_rixia_juan076:L141-L148`「林香山」（cue:為/high）：与金标「香山」span 重叠但字形不合（引擎「林香山」vs 金标「香山」）
- `pilot_rixia_juan076:L181-L189`「太樸　暢春園」（cue:為/high）：与金标「暢春園」span 重叠但字形不合（引擎「太樸　暢春園」vs 金标「暢春園」）
- `pilot_rixia_juan076:L213-L216`「三楹　暢春園」（suffix_scan/mid）：与金标「暢春園」span 重叠但字形不合（引擎「三楹　暢春園」vs 金标「暢春園」）
- `pilot_rixia_juan076:L217-L230`「恩佑寺二層山」（cue:曰/high）：与金标「恩佑寺」span 重叠但字形不合（引擎「恩佑寺二層山」vs 金标「恩佑寺」）
- `pilot_rixia_juan076:L217-L230`「恩慕寺殿」（cue:為/high）：与金标「恩慕寺」span 重叠但字形不合（引擎「恩慕寺殿」vs 金标「恩慕寺」）
- `pilot_rixia_juan076:L231-L248`「恩慕寺二層山」（cue:曰/high）：与金标「恩慕寺」span 重叠但字形不合（引擎「恩慕寺二層山」vs 金标「恩慕寺」）
- `pilot_rixia_juan076:L249-L259`「暢春園恩佑寺」（suffix_scan/mid）：与金标「暢春園」span 重叠但字形不合（引擎「暢春園恩佑寺」vs 金标「暢春園」）
- `pilot_rixia_juan076:L335-L350`「　暢春園」（suffix_scan/mid）：与金标「暢春園」span 重叠但字形不合（引擎「　暢春園」vs 金标「暢春園」）
- `pilot_rixia_juan079:L1-L4`「泉宗廟廟」（cue:曰/high）：与金标「泉宗廟」span 重叠但字形不合（引擎「泉宗廟廟」vs 金标「泉宗廟」）
- `pilot_rixia_juan079:L1-L4`「五楹　泉宗廟」（suffix_scan/mid）：与金标「泉宗廟」span 重叠但字形不合（引擎「五楹　泉宗廟」vs 金标「泉宗廟」）
- `pilot_rixia_juan079:L5-L16`「源委泉宗廟」（suffix_scan/mid）：与金标「泉宗廟」span 重叠但字形不合（引擎「源委泉宗廟」vs 金标「泉宗廟」）
- `pilot_rixia_juan079:L5-L16`「玉泉」（suffix_scan/mid）：与金标「玉泉山」span 重叠但字形不合（引擎「玉泉」vs 金标「玉泉山」）
- `pilot_rixia_juan079:L23-L25`「昆明湖經長河」（cue:為/high）：与金标「昆明湖」span 重叠但字形不合（引擎「昆明湖經長河」vs 金标「昆明湖」）
- `pilot_rixia_juan079:L26-L28`「　暢春園」（suffix_scan/mid）：与金标「暢春園」span 重叠但字形不合（引擎「　暢春園」vs 金标「暢春園」）
- `pilot_rixia_juan079:L29-L38`「三楹　泉宗廟」（cue:為/high）：与金标「泉宗廟」span 重叠但字形不合（引擎「三楹　泉宗廟」vs 金标「泉宗廟」）
- `pilot_rixia_juan079:L76-L90`「萬泉」（suffix_scan/mid）：与金标「萬泉莊」span 重叠但字形不合（引擎「萬泉」vs 金标「萬泉莊」）
- `pilot_rixia_juan079:L76-L90`「御書御製萬泉」（suffix_scan/mid）：与金标「萬泉莊」span 重叠但字形不合（引擎「御書御製萬泉」vs 金标「萬泉莊」）
- `pilot_rixia_juan079:L104-L116`「形北望暢春園」（suffix_scan/mid）：与金标「暢春園」span 重叠但字形不合（引擎「形北望暢春園」vs 金标「暢春園」）
- `pilot_rixia_juan079:L117-L123`「武清侯海淀」（suffix_scan/mid）：与金标「海淀」span 重叠但字形不合（引擎「武清侯海淀」vs 金标「海淀」）
- `pilot_rixia_juan079:L124-L134`「原髙梁橋」（suffix_scan/mid）：与金标「髙梁橋」span 重叠但字形不合（引擎「原髙梁橋」vs 金标「髙梁橋」）
- `pilot_rixia_juan079:L124-L134`「南海淀北海」（cue:為/high）：与金标「南海淀」span 重叠但字形不合（引擎「南海淀北海」vs 金标「南海淀」）
- `pilot_rixia_juan079:L124-L134`「青龍橋河」（cue:有/high）：与金标「青龍橋」span 重叠但字形不合（引擎「青龍橋河」vs 金标「青龍橋」）
- `pilot_rixia_juan079:L124-L134`「先游海淀」（suffix_scan/mid）：与金标「海淀」span 重叠但字形不合（引擎「先游海淀」vs 金标「海淀」）
- `pilot_rixia_juan079:L124-L134`「道海淀」（suffix_scan/mid）：与金标「海淀」span 重叠但字形不合（引擎「道海淀」vs 金标「海淀」）
- `pilot_rixia_juan079:L124-L134`「園不可攷海淀」（suffix_scan/mid）：与金标「海淀」span 重叠但字形不合（引擎「園不可攷海淀」vs 金标「海淀」）
**kb-coverage-gap（170 条）**

- `pilot_rixia_juan076:L2-L9`「前園」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L10-L12`「兹游憩酌泉」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L10-L12`「聴政事曲房」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L10-L12`「阿房」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L10-L12`「繡嶺」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L10-L12`「飾包山」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L10-L12`「沸泉」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L10-L12`「松軒茅殿」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L10-L12`「游豫燕喜是營」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L29-L33`「園内龍神廟」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L29-L33`「新愁薄念頻」（cue:有/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L34-L40`「御園」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L51-L63`「天津園」（cue:即/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L69-L72`「御園觀」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L73-L83`「御園」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L73-L83`「平湖」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L84-L91`「御製盤山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L92-L95`「御製玉河」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L103-L107`「御園」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L103-L107`「寒朕若園」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L103-L107`「颯景御園」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L108-L111`「五楹小河」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L108-L111`「九經三事殿殿」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L112-L120`「垂花門内殿」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L112-L120`「三楹後照殿」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L135-L140`「寝殿」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L141-L148`「夀萱春永殿」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L141-L148`「河池南北立坊」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L149-L157`「聖祖御書觀」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L149-L157`「劍山山」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L149-L157`「清逺亭由山」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L149-L157`「龍王廟」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L158-L165`「所後殿」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L170-L180`「府君廟」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L181-L189`「聖祖御書府」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L213-L216`「東垣内山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L213-L216`「石橋三殿」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L217-L230`「東垣正殿」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L217-L230`「龍象莊嚴正殿」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L217-L230`「世宗御書殿」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L231-L248`「永慕寺」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L231-L248`「側敬搆是寺」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L231-L248`「慈雲廣蔭大殿」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L231-L248`「福應天人殿」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L263-L267`「劍山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L263-L267`「如意門過小橋」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L263-L267`「玩芳齋山」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L280-L286`「買賣街」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L280-L286`「載月舫北向房」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L287-L300`「居西花園」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L322-L331`「勤政殿」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L335-L350`「菜園」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L335-L350`「闗帝廟」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L335-L350`「蓮花巖對河」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L335-L350`「松柏閘闗帝廟」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L335-L350`「松柏閘河」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L335-L350`「右河」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L335-L350`「招涼精舍河」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L335-L350`「灣轉橋」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L335-L350`「灣轉橋橋」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L335-L350`「曉烟榭河」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L335-L350`「山口」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L335-L350`「山口臨河」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L335-L350`「回芳墅北轉山」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L351-L360`「翠嵓山」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L351-L360`「翠嵓山房」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L361-L366`「正好時指山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L373-L377`「觀瀾榭西河」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L381-L388`「玉津園」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L389-L393`「錦波度河橋」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L394-L400`「循河」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L401-L412`「祝如山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L426-L429`「閘口門閘口」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan076:L426-L429`「立坊」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L1-L4`「池左右立坊」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L1-L4`「配殿」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L5-L16`「循玉岫明湖」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L5-L16`「委輸西坊」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L5-L16`「谷口」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L5-L16`「飛鷺春渠」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L5-L16`「普潤殿殿」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L5-L16`「記記泉」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L5-L16`「是若殿」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L5-L16`「水四瀆四海」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L5-L16`「也一黄河」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L5-L16`「搆殿」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L5-L16`「向記兹萬泉」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L5-L16`「地實近長河」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L17-L22`「日禮泉」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L23-L25`「園一攬泉」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L23-L25`「巴溝橋」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L29-L38`「曙觀」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L39-L48`「曙觀」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L65-L75`「曙觀」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L65-L75`「石坊」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L65-L75`「石橋橋」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L65-L75`「苑之西罩門」（cue:為/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L76-L90`「滙川印月西坊」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L76-L90`「苕霅溪山」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L76-L90`「故址也園」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L76-L90`「由玉泉」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L76-L90`「長河」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L76-L90`「通惠河」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L76-L90`「麥莊橋」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L76-L90`「巴溝橋」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L76-L90`「大沙泉小沙泉」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L76-L90`「淙泉」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L76-L90`「八廟」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「廟内外淙泉」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「大沙泉小沙泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「沸泉廟」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「滮泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「屑金泉曙觀」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「氷壺泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「氷壺泉錦瀾泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「露華泉鑑空泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「月泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「藕泉躍魚泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「晴碧泉白榆泉」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「桃花泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「琴脈泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「杏泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「杏泉澹泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「瀏泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「洗鉢泉」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「浣花泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「潄石泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「潄石泉橋」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「乳花泉漪竹泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「貫珠泉」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L91-L103`「八皆御書」（cue:有/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L104-L116`「石泉」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L104-L116`「逺臨泉」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「淀淀」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「挹海」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「狐狸淀」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「狐狸淀廣韻淀」（cue:即/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「方淀」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「方淀三角淀」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「説文無淀」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「清華園」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「花海」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「貴璫墳」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「山巖洞幽窅渠」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「雙橋」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「逰焉淀」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「勺園」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「搆園」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「樓百尺對山」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L117-L123`「飛橋」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「明李偉清華園」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「清華園」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「挹海」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「樓百尺對山」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「白龍廟」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「罋山」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「小湖」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「倒映見西山」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「巴溝達白石橋」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「謫皖山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「勺園」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「米家園」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「繪園」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「席口」（cue:即/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「曾一照米家園」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「陂陂上橋」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「雀浜勒黄山」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「勺海」（cue:為/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「李園壯麗米園」（cue:曰/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `pilot_rixia_juan079:L124-L134`「米家墳」（cue:有/high）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
**kb-variant-near-miss（3 条）**

- `pilot_rixia_juan076:L335-L350`「娘娘殿殿」（cue:為/high）：与 KB 字形「娘娘府」近形（前两字同），缺变体收编
- `pilot_rixia_juan079:L23-L25`「玉泉」（suffix_scan/mid）：与 KB 字形「玉泉山」近形（前两字同），缺变体收编
- `pilot_rixia_juan079:L124-L134`「青龍桁河」（cue:為/high）：与 KB 字形「青龙桥镇」近形（前两字同），缺变体收编
**markdown-prefix-bleed（6 条）**

- `pilot_rixia_juan076:L96-L102`「䕫然又」（cue:為/mid）：命中串带非汉字记号「䕫」——rp-v3 句读/边界表缺这些记号，回溯越过 Markdown 加粗与书名号
- `pilot_rixia_juan076:L335-L350`「緑𥦗山」（cue:為/high）：命中串带非汉字记号「𥦗」——rp-v3 句读/边界表缺这些记号，回溯越过 Markdown 加粗与书名号
- `pilot_rixia_juan079:L23-L25`「閏致春寒　泉」（suffix_scan/mid）：命中串带非汉字记号「　」——rp-v3 句读/边界表缺这些记号，回溯越过 Markdown 加粗与书名号
- `pilot_rixia_juan079:L23-L25`「原㵼北石橋」（suffix_scan/mid）：命中串带非汉字记号「㵼」——rp-v3 句读/边界表缺这些记号，回溯越过 Markdown 加粗与书名号
- `pilot_rixia_juan079:L117-L123`「或作𣵦或作澱」（suffix_scan/mid）：命中串带非汉字记号「𣵦」——rp-v3 句读/边界表缺这些记号，回溯越过 Markdown 加粗与书名号
- `pilot_rixia_juan079:L124-L134`「斜陽　市隠園」（suffix_scan/mid）：命中串带非汉字记号「　」——rp-v3 句读/边界表缺这些记号，回溯越过 Markdown 加粗与书名号

## 假说层覆盖（duplication / collision 证据）

- 被覆盖 gold 实体：12；其中被 ≥2 假说覆盖（duplication 分子）：0
  - `ent_changchunyuan_kangxi` ← 假说 畅春园
  - `ent_enmusi` ← 假说 恩慕寺
  - `ent_enyousi` ← 假说 恩佑寺
  - `ent_gaoliang_bridge` ← 假说 高梁桥
  - `ent_haidian` ← 假说 北海淀、南海淀、海淀 ⚠️duplication
  - `ent_kunminghu` ← 假说 昆明湖、西湖 ⚠️duplication
  - `ent_qinglongqiao` ← 假说 青龙桥
  - `ent_quanzongmiao` ← 假说 泉宗庙
  - `ent_wanquanzhuang` ← 假说 万泉庄
  - `ent_yuanmingyuan` ← 假说 圆明园
  - `ent_yuanmingyuan_parent` ← 假说 圆明园
  - `ent_yuquanshan` ← 假说 玉泉山
- 覆盖 ≥2 gold 实体的假说（collision 分子）：0
  - 「万泉庄」→ ent_wanquanzhuang
  - 「北海淀」→ ent_haidian
  - 「南海淀」→ ent_haidian
  - 「圆明园」→ ent_yuanmingyuan、ent_yuanmingyuan_parent ⚠️collision
  - 「恩佑寺」→ ent_enyousi
  - 「恩慕寺」→ ent_enmusi
  - 「昆明湖」→ ent_kunminghu
  - 「泉宗庙」→ ent_quanzongmiao
  - 「海淀」→ ent_haidian
  - 「玉泉山」→ ent_yuquanshan
  - 「畅春园」→ ent_changchunyuan_kangxi
  - 「西湖」→ ent_kunminghu
  - 「青龙桥」→ ent_qinglongqiao
  - 「高梁桥」→ ent_gaoliang_bridge

## 结论与最小修复路径

**闸门不通过**，卡在：mention_precision、mention_recall、high_conf_precision。

敏感度（两个有机械依据的界，非口径放水）：

- **precision 严格下界 = 实测值**：KB 覆盖缺口 FP（170 条，真实地名但 8 模块未建词条）按冻结公式计错。若经人工判定为真地名，P 上界 = 0.441——仍低于 0.90。
- **recall 受设计性拒发拖累**：0 条 FN 是引擎按身份/噪声纪律（旗名子串、机构复合词）主动拒发。若视为命中，R 上界 = 0.315——仍低于 0.85。

两个上界都够不着阈值 ⇒ 缺口是结构性的，调参无解，需按下列路径修复后重跑（holdout 不变）。

### 修复路径（按影响面排序）

| 优先级 | 归因类 | 条数(FN/FP) | 最小修复 | 说明 |
|---|---|---|---|---|
| P0 | `erosion` | 16 / 35 | 回溯边界字增补 | 「名娘娘府」「《圆明园」「**蓝靛厂」：名/记/俗 等单字边界与记号并入 _STOP_CHARS |
| P0 | `walkback-overrun` | 30 / 0 | 句读/回溯边界表扩记号 | rp-v3 的 _PUNCT_CHARS/_STOP_CHARS 缺 Markdown 记号（*、-、空格）与书名号《》；一处表修复同时治理多条 |
| P0 | `boundary-splice` | 0 / 13 | 回溯边界字增补 | 「今大觉寺」「北安河」：今/北/西 等头部边界字——注意其中部分（北安河）实为真地名，修复时须防误伤 lexicalized 方位头（西三旗先例） |
| P0 | `markdown-prefix-bleed` | 0 / 6 | 句读/回溯边界表扩记号 | rp-v3 句读/回溯边界表缺 Markdown 记号（*、-、空格、书名号《》）；与 walkback-overrun 同根同修 |
| 数据层 | `kb-coverage-gap` | 0 / 170 | KB 收录缺口 | 清水院/大觉寺/金山/万泉河等是真实海淀地名但 8 个校准模块未建词条：属代理金标口径偏差的主要来源（见敏感度），不是挖掘器缺陷 |
| P2 | `same-form-elsewhere` | 45 / 0 | 同 fact 同形只发一次 | 多次出现只记首现：跨 fact 互证是设计行为，可按 mention 密度重估 |
| P2 | `overlapped-hit-discarded` | 4 / 0 | 子词让位 | 后缀命中与更右的采纳区间重叠，按子词规则让位（策略已知代价） |
| P2 | `cue-window-narrow` | 3 / 0 | cue 窗策略 | 生僻通名（院）靠 12 字窗保不住：可在 v4 引入 known 表预匹配 |
| P2 | `kb-variant-near-miss` | 0 / 3 | 变体表扩 | 近形异体缺收编 |

### 决策项（超出本评估器权限，需主代理裁定）

v4 已落地（known-mention 通道 + rp-v4 记号/边界表，v5/rp-v5）
纯地名的已知名压制已消除。余下两类身份层张力：

1. **机构复合词内嵌已知实体**（0 条，noise-keyword）：「圆明园护军营」「圆明园副将」语境中的圆明园 mention 被职官关键词拦下——引擎按纪律拒发（这些复合词确实不是地点），冻结公式恒计 FN。出路：(a) gold 口径为「复合词内嵌」单列（冻结修正案，需你批准）；(b) v5 内嵌实体识别。
2. **旗营专名**（0 条，stopword-suppressed/旗名子串）：「正黄旗营房」类不是纯地名、是建置名，营/房后缀通道天然不可达——建议在 KB 建置层补专名通道，或 gold 口径豁免。

## 偏差声明

1. v1 真值为**代理金标**（KB 已知实体字形；人工 holdout_gold.jsonl 尚未产出）：KB 未收录的真实地名按公式计 FP，故 mention precision 实测值是真值的下界；recall 不受影响（gold 即 KB 实体提及）。
2. 分母为 0 的指标记 None 并判不过（证据不足不放行），本轮：无
3. span 恢复：挖掘器不产 offset，评估器按「同 fact 同形只发一次」的引擎保证取首现位置（`occurrence.text_span` 是窗口不是 span，不可用）。
