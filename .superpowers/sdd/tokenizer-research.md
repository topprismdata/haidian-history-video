# 中文分词/NER 框架调研报告(2026-10-02)

> 调研:TokenizerResearch scout(带证据链) | 结论:**不上**,触发条件再评估
> 背景问题:FullTextMiner(接口已预留)的内部实现要不要用分词/NER?

## Verdict

**不上**。分词/NER 在四个环节均非最优工具,且关键公开证据缺失:
- 历史地名 LOC 类古籍 NER:无公开 benchmark
- 现代分词器(jieba/pkuseg/HanLP/LTP/THULAC)文言文适配:无量化证据(只报现代语料)

重新评估触发条件(任一满足):
1. FullTextMiner 上线后噪声率 >20% 且人工过滤成本 >每集 1 小时
2. 目标文本变为无标点原刻本文言
3. 出现 LOC 类古籍 NER 公开 benchmark(F1≥85%)

届时优先做 TGAZ/CHGIS gazetteer 消歧而非分词器。

## 一、候选清单

| 框架 | 文言适配 | NER | license | py3.9 | 维护 | 来源 |
|---|---|---|---|---|---|---|
| jieba | 低(现代词典先验) | 无 | MIT | ✓ | 停更(2020) | github.com/fxsjy/jieba |
| pkuseg | 低-中(新闻语料) | 无 | MIT | ✓ | 低 | github.com/lancopku/PKUSeg-python |
| HanLP | 低(需自行微调) | 强(现代实体) | Apache-2.0 | ✓ | 高 | github.com/hankcs/HanLP |
| LTP 4.x | 低 | 强 | Apache-2.0 | ✓ | 中 | github.com/HIT-SCIR/ltp |
| THULAC | 低 | 无(仅词性ns) | MIT类 | ✓ | 低(2019停更) | github.com/thunlp/THULAC-Python |
| sikufenci | 高(四库专建) | 无 | 见SikuBERT仓库 | 未声明 | 科研一次性 | github.com/hsc748NLP/SikuBERT-... |
| SikuBERT | 高(5.36亿字四库) | 微调后F1 83-86% | GPL-3.0 | ✓ | 低-中 | arxiv.org/pdf/2403.15088 |
| GuwenBERT | 高(殆知阁1.7亿字) | 小样本微调超通用;无LOC头 | GPL-3.0 | ✓ | 冻结 | github.com/Ethan-yt/guwenbert |
| GujiBERT/GujiRoBERTa_fan | 高(繁体) | F1 84-86.5% | 见仓库 | ✓ | 中 | github.com/hsc748NLP/GujiBERT-and-GujiGPT |

(erhshenM 查无此项目,两次定向检索无结果,不作为候选)

## 二、文言文实测证据

- GuNER 2023(北大 CCL 古籍 NER 评测):二十四史语料,PER/BOOK/OFI 三类——**不含 LOC 为主**(guner2023.pkudh.org)
- EvaHan 2022(古汉语分词评测,史记/左传):F1 ~85-95%,域外掉点(aclanthology.org/2022.lt4hala-1.19.pdf)
- EvaHan 2024(转句读/断句):句切分 F1 88.47%、标点 75.29%,unseen 文体掉 ~10%(aclanthology.org/2024.lt4hala-1.27)
- 古籍 NER F1:bert-base-chinese 基线 77-79% → 古籍专预训练 83-86.5%(评测集分布,非《日下旧闻考》体)(github.com/hsc748NLP/GujiBERT-and-GujiGPT)
- **历史地名 LOC benchmark:无公开证据**(未检索到以历史地名 LOC 为主标注类的公开古籍 NER 评测)
- **现代分词器文言 F1:无公开证据**

## 三、历史地名专项(社区技术路线)

| 项目 | 路线 | 来源 |
|---|---|---|
| CHGIS | 权威历史政区 GIS(秦-1911),不做 NER,是对齐目标 | chgis.fas.harvard.edu |
| TGAZ | 时空地名 API:汉字/拼音+时间跨度→历史实体+LOD,处理同名异地 | gis.harvard.edu/projects/temporal-gazetteer-tgaz |
| CBDB geocoding | NER→朝代/上下文→TGAZ/CHGIS 查表消歧 | cbdb.hsites.harvard.edu |
| LoGaRT | 方志数字化研究平台,语料/工具底座 | mpiwg-berlin.mpg.de |
| WHG | 跨时空历史地名 Linked Data | whgazetteer.org |
| LoGHMA | 查无此项目,无公开证据 | — |

## 四、与现方案(ToponymMiner v3)互补分析

| 环节 | 判断 | 理由 |
|---|---|---|
| a. 边界切分 | **不值得** | M3 回溯缺陷更便宜的解是 gazetteer 后缀白名单查表;现代分词器文言切分无公开证据 |
| b. 新词发现 | **不值得单独上框架** | 互信息/左右熵 n-gram 自算即可(~100 行) |
| c. NER 直出地名 | **最诱人但不值得现在上** | LOC 无 benchmark、《日下旧闻考》按语结构是 OOD、需 torch+GB 级依赖+自标语料 |
| d. 同名消歧 | **值得做,但用 gazetteer 不用分词** | 接 TGAZ HTTP API(零重依赖) |

## 五、试点设计(触发后启动,当前否决)

- A/B:三书各抽 3 卷,人工标注全部地名 mention(~3000 条,2-3 人日,标注手册复用三层身份定义)
- A=ToponymMiner v3;B=v3+GujiBERT_fan/SikuBERT+CRF 微调 LOC(GuNER 公开数据+6 卷训练,3 卷 holdout)
- 指标:mention 级 P/R/F1,分身份层报告
- 判定:B 噪声率降 ≥50% 且 recall 降 ≤2pp,否则否决
- 预算:GPU 半天,全程 ≤1 周
