# TGAZ API 真实契约（浏览器实测核验）

- 实测日期: 2026-10-02
- 方法: omp browser tab "tgaz"（同源页面）内 Node fetch，逐请求记录 status/Content-Type/响应体；共 ~80 次请求
- 官方文档页（用户找到，实测 200）: https://tgaz.fudan.edu.cn/tgaz/indexAPI.html
- 实测与文档不一致处均在下文标注

## 结论：能否编程接入 —— **YES**

理由：
1. 分面搜索与 ID 精取两条端点均返回合法 JSON（`text/json; charset=utf-8`），结构稳定、字段名固定；
2. http/https 均可用（https 已验证 200 + JSON）；
3. 无需鉴权、无 cookie、无 token；
4. 连续 20 次快速请求（avg 520ms/次）全部 200，未见 429/5xx/封禁；
5. 唯二硬限制：①单次 JSON 搜索最多返回 200 条且 JSON 模式分页参数被忽略（须用更精确前缀/过滤条件收敛）；②搜索端点 `fmt=xml` 服务端 PHP 直接 Fatal error（用 json 或走 ID 直取的 `/xml/` 路径均可绕开）。

注意：响应头**无** `Access-Control-Allow-Origin` → 浏览器端跨域 fetch 会被 CORS 拦；编程接入须走服务端（Node/Python 直连 OK）。

---

## 1. 端点

### 1.1 分面搜索（Faceted Search）
```
GET http(s)://tgaz.fudan.edu.cn/tgaz/placename?<QUERY_PARAMS>
```
- 路径必须精确为 `/tgaz/placename`（**无尾斜杠**：`/tgaz/placename/` → 404 "No placename found for id: "，尾斜杠被当作 ID 直取）。
- 查询参数（实测）：

| 参数 | 含义 | 实测行为 |
|---|---|---|
| `n` | 地名 | **前缀匹配** `LIKE 'X%'`（后缀不行：n=壽寺→0）。同时匹配汉字名与拼音转写（n=Wan→913 命中，n=wanshou→9）。大小写不敏感（wanshou 与 Wan 同机制）。必须 UTF-8 |
| `yr` | 年份（点值） | 存在性过滤：n=北京&yr=1140→1，yr=1149→1，yr=1150→0（北京路 1138~1149）。**不支持区间**："1800-1911"→0。DB 起止 -222~1911（文档口径；TBRC 条目 end 可为 9999） |
| `ftyp` | 行政等级/要素类型 | 匹配中文名或拼音转写：`cun zhen`→1、`村镇`→1、英文 `villages and small towns`→0 |
| `src` | 数据源 | `CHGIS`/`TBRC`/`HGR`（首页表单口径）；实测 src=CHGIS 正常过滤。文档页写 "CHGIS, RAS"，以表单枚举为准 |
| `p` | 上级单位（parent 地名前缀） | n=大&p=2→0 命中（p 按 parent 前缀匹配）。**p 不是分页参数** |
| `fmt` | 输出格式 | 合法值 `json`/`html`（均实测）。**`xml` 触发服务端 Fatal error**（ArgumentCountError, search.php:200），HTTP 200 但 body 是 PHP 错误文本。fmt 值大小写敏感：`fmt=JSON` 被当 html 处理。缺省=html |
| `pg` | 页码（HTML 专用） | HTML 模式正确翻页（pg=2 内容变化）；**JSON 模式 pg 被完全忽略**（pg=1/2/3 返回逐字节相同结果，均前 200 条） |

- 缺 `n`（无该参数）且 fmt=json：**HTTP 200 + 空 body**（解析会炸，客户端需防御）。
- `n=`（空值）：全库扫描 `'%'`，total=81292，返回前 200 条——避免误用。

### 1.2 ID 精取（Canonical Placename）
```
GET http(s)://tgaz.fudan.edu.cn/tgaz/placename/<fmt>/<ID>
GET http(s)://tgaz.fudan.edu.cn/tgaz/placename/<ID>      # 等价于 /html/<ID>
```
- `<fmt>` 为**路径段**（官方文档明确列出）：`json`/`xml`/`rdf`/`html`，四种全部实测 200。
- Content-Type 实测：json→`text/json; charset=utf-8`；xml→`text/xml; charset=utf-8`；rdf→`application/rdf+xml`（实际是 Turtle/N3 序列化）；html→`text/html`。
- **错误形态**：`/json/hvd_999999999` → HTTP **404**，body `<h1>404 Not Found</h1><p>CHGIS:  No placename found for id: hvd_999999999</p>`（HTML，非 JSON——客户端按 status 判错）。
- 反模式（实测失败，勿用）：
  - `/tgaz/placename/<ID>?fmt=json` → **fmt 被忽略**，返回 HTML 详情页；
  - `/tgaz/placename/<ID>.json` → 404（整个 `.json` 被当作 ID）；
  - `/tgaz/placename/json?n=X`（路径式 fmt + 搜索参数）→ PHP Notice + 404。
- `Accept: application/json` 头无效（照样返回 HTML）。

### 1.3 ID 格式
- CHGIS 条目：`hvd_<数字>`（如 hvd_141901；文档：CHGIS ID 32180 → hvd_32180）。
- TBRC（藏传佛教）条目：`TBRC_<编码>`（如 TBRC_G1KR1856，年份可到 9999=开放结束）。
- HGR（俄国）条目未实测，预期有独立前缀。
- ID 可从搜索结果的 `sys_id` / `uri` 字段直接获得。

---

## 2. JSON 响应样例（实测截取）

### 2.1 分面搜索（完整实测响应，682B）
```
GET http://tgaz.fudan.edu.cn/tgaz/placename?n=%E4%B8%87%E5%AF%BF%E5%AF%BA&fmt=json
→ 200, Content-Type: text/json; charset=utf-8
```
```json
{
    "system" : "CHGIS - Harvard University & Fudan University",
    "memo" : "Results for query matching key '万寿寺%'",
    "count of displayed results" : "1",
    "count of total results" : "1",
    "placenames" : [
      {
        "sys_id" : "hvd_141901",
        "uri" : "http://tgaz.fudan.edu.cn/tgaz/placename/hvd_141901",
        "name" : "万寿寺",
        "transcription" : "Wanshousi",
        "years" : "1911 ~ 1911",
        "parent sys_id" : "hvd_121715",
        "parent name" : "浮梁县 (Fuliang Xian)",
        "feature type" : "村镇 (cun zhen)",
        "object type" : "POINT",
        "xy coordinates" : "117.20749, 29.54609",
        "data source" : "CHGIS"
      }
    ]
}
```
字段名含**空格**（`"count of total results"`、`"parent sys_id"`、`"xy coordinates"`），计数是**字符串**不是数字。>200 条时 `memo` 附加 "Returned more than the maximum. Please refine your search."，`count of displayed results`=200、`placenames` 恰 200 项。

### 2.2 ID 精取（`/tgaz/placename/json/hvd_141901`，source note 字段截断）
```json
{
  "system": "China Historical GIS, Harvard University and Fudan University",
  "license": "CC BY-NC 4.0",
  "uri": "http://tgaz.fudan.edu.cn/tgaz/placename/hvd_141901",
  "sys_id": "hvd_141901",
  "sys_id of alternate": "",
  "spellings": [
    { "written form": "萬壽寺", "script": "traditional Chinese", "exonym language": "", "attested by": "", "note": "" },
    { "written form": "万寿寺", "script": "simplified Chinese", "exonym language": "", "attested by": "", "note": "" },
    { "written form": "Wanshousi", "transcribed in": "Pinyin", "attested by": "", "note": "" }
  ],
  "feature_type": { "name": "村镇", "alternate name": "村鎮", "transcription": "cun zhen", "English": "villages and small towns" },
  "temporal": { "begin": "1911", "begin rule": "9", "end": "1911", "end rule": "9" },
  "spatial": {
    "object_type": "POINT", "xy_type": "point",
    "latitude": "29.54609", "longitude": "117.20749", "source": "FROM_AC",
    "present_location": [ { "country code": "cn", "text": "江西景德镇市万寿山垦殖场", "source": "Fudan", "attestation": "" } ]
  },
  "historical_context": {
    "part of": [ { "begin year": "1911", "end year": "1911", "parent id": "hvd_121715", "name": "浮梁县", "transcribed": "Fuliang Xian" } ],
    "subordinate units": [],
    "preceded by": []
  },
  "data source": "CHGIS",
  "source note": "<html><body>…（长 HTML 说明，可含整段数据来源考据）…</body></html>",
  "source uri": ""
}
```
两种 schema 不同：搜索=轻量平铺数组；ID=完整记录（含繁简拼写过载拼写、层级 `part of`/`subordinate units`、经纬度分字段）。层级遍历可行：parent/child id 再走 `/json/<id>`。

---

## 3. 匹配语义与繁简敏感度（实测）

- **前缀匹配**：`memo` 显示 `key 'X%'`；后缀查询 n=壽寺→0。
- **繁简归一**：服务端把繁体查询归一为简体再匹配（n=萬壽寺 命中 name=万寿寺 的记录）。**绝大多数两形命中数一致**，但存在漏配：

| 简体/繁体 | 简体命中 | 繁体命中 |
|---|---|---|
| 万寿寺/萬壽寺 | 1 | 1 |
| 汉口/漢口 | 3 | 3 |
| 广安/廣安 | 8 | 8 |
| **龙泉/龍泉** | **35** | **34** |
| 西山/西山 | 19 | 19 |

→ **编程接入一律用简体查询**（库内规范名是简体），繁体仅作人工兜底，勿依赖计数相等。
- 编码：参数值 UTF-8 百分号编码（`%E4%B8%87%E5%AF%BF%E5%AF%BA`）实测完全正常；文档称"必须发普通 UTF-8 不需 URLencode"，两者实测等效（服务器会解码 query string），按常规 URLencode 即可。
- 命中数上限：单次 JSON 最多 200（n=大→1927 total/200 displayed）。

---

## 4. 限速 / 稳定性（实测）

- 连续 20 次请求（n=西山&fmt=json）：全部 200，total 11.97s，min/avg/max = 435/520/641 ms，无 429/5xx/封禁；停 1s 后第 21 次照常 200。
- 本次会话累计 ~80 次请求未见任何限速迹象。单次延迟 ~0.5s，客户端建议串行 + 超时 ≥10s。
- 服务端栈是 PHP（错误信息泄露路径 /var/www/html/tgaz/api/），`fmt=xml` 的 Fatal error 说明错误处理薄弱——客户端必须校验 body 是否以 `{` 开头再 JSON.parse，不能只看 HTTP 200。

---

## 5. 与本项目相关的阴性结果（重要）

以下查询实测 **0 命中**（前缀匹配，CHGIS 收政区级+1911 聚落，不含北京城内寺观）：
- `n=樹村` / `n=树村` → 0
- `n=覺生寺` / `n=覺生` / `n=大钟寺` / `n=大鐘寺` → 0
- `n=万寿寺`（北京万寿寺）→ 0（唯一命中是江西浮梁县村镇 hvd_141901，非北京）

→ E9 大钟寺（覺生寺）相关研究**不能**依赖 TGAZ 取点位/层级；须回 CHGIS 下载包或其它来源。

## 6. 附加实测记录

- https 与 http 行为一致（搜索与 ID 直取均验证 200 + 正确 Content-Type）。
- `OPTIONS` → 200（无 ACAO 头、无 Allow 头）；`HEAD` → 200 且 Content-Type 正确（可做健康检查）。
- 文档页自称"默认返回 XML"，实测默认（无 fmt）返回 **HTML**；文档同页也写"默认输出为 HTML"，以后者/实测为准。
