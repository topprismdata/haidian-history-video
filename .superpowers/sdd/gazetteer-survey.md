# 中国历史地名 Gazetteer 多源调研报告(TGAZ/CHGIS/CBDB/LoGaRT/WHG 之外)
日期:2026-10-02。调研:GazetteerSurvey scout(托管 fetch 实测,记录读取成功/403/404)。

## 第一节 发现清单
1. CCTS 中华文明之时空基础架构(中研院人社中心 GIS 专题中心,台湾)— 有 API(地名整合检索+WMTS)
2. DILA/DDBC 地名规范资料库(法鼓文理学院,台湾)— Web Services API + KML + 开放下载
3. CCVG Data 数字村庄(匹兹堡大学,美国)— CSV 免费下载,村落粒度
4. 东洋文库「大明地理之図」(日本)— 仅网页/IIIF
5. 京都大学人文研(日本)— 仅网页
6. 复旦数字禹贡(大陆)— CHGIS 生态对照项,旧入口 404
7. 中研院史语所历史地名查询系统(台湾)— 仅网页,无 API
8. EFEO(法国)— 无中国历史地名库,无效方向
排除已调研:TGAZ/CHGIS/CBDB/LoGaRT/WHG/哈佛燕京方志库。

## 第二节 每源评估
### 1) CCTS — 同源确认档(P2)
- https://ccts.sinica.edu.tw (在线,2024 更新痕迹);WMTS: data.depositar.io/dataset/wmts-sinica-ccts
- 先秦至清/今,谭其骧图集为底;政区级非村落;学术授权
- 交叉价值:与 TGAZ 同源(谭图)独立实现,TGAZ 命中后的第二确认;对未命中补益有限

### 2) DILA — 异源裁决档(P1,接入成本最低)
- https://authority.dila.edu.tw/place (Web Services API+KML+开放下载,自述 open-sourced)
- 佛典地名带经纬度,秦至今;宗教/文献视角完全独立
- 交叉价值:对寺/庙/山/泉类海淀地名有独立考证——大钟寺/万寿寺/大觉寺类词条的直接增量

### 3) CCVG — 古今夹逼档(P1,村落粒度唯一)
- https://www.chinesevillagedata.library.pitt.edu/ ;CSV 存档: d-scholarship.pitt.edu/concern/generic_works/182abd9b-da12-47fc-b023-2ad444c92cfd
- 2,601 行政村 CSV(2022-11,源 2,701 村志);开放数据,活跃;无 API
- 交叉价值:当代村志验证历史小地名是否延续至今——与 TGAZ 构成古今夹逼:
  历史名查 TGAZ 政区归属、当代名在 CCVG 验证存续;两源皆命中→高置信;仅 CCVG→提示近代/当代新名

### 4-8) 低增量
- 东洋文库:明代道/府级,IIIF 图像非结构化
- 京大人文研:无地名结构化库
- 复旦数字禹贡:yugong.fudan.edu.cn/CHGIS/ 与 chgis.fudan.edu.cn 均 HTTP 404,现行入口即 TGAZ
- 史语所:仅网页人工核对
- EFEO:无效方向;CBDB 官网实测 HTTP 403(已知源仅记录)

## 第三节 接入建议(digital_resources.py 登记)
| source_id | 类别 | 形态 | 优先级 |
|---|---|---|---|
| ccvg_pitt | contemporary_village_gazetteer | CSV 批量下载,离线数据源 | **P1**(零 API 成本,海淀村落粒度唯一直接命中) |
| dila_place_authority | authority_gazetteer | Web API+KML,免注册 | **P1**(接入成本最低) |
| ccts_sinica | historical_gis_gazetteer | API(须先确认 endpoint 公开程度)+WMTS | P2 |
| shiyu_place_query | web_only | 不进裁决层 | 不登记 |
| 东洋文库/京大 | web_only | 不登记 | — |

**verdict:多源交叉验证可行,三档架构——同源确认(CCTS)/异源裁决(DILA)/古今夹逼(CCVG+TGAZ)。优先接入:①CCVG CSV 建本地倒排索引 ②DILA API ③CCTS。**
