# DILA 地名規範資料库 API 契约探测 findings

- 日期：2026-10-02（agent DilaConnectorProbe，闭包管线外部裁决基建）
- 探测对象：`authority.dila.edu.tw`（法鼓文理学院 DDBC）
- 产出代码：`haidian_kg/providers/dila.py`（`DilaProvider`），测试 `tests/haidian_kg/test_dila_provider.py`（20 例，全 mock，0.04s 零网络）

## 1. 结论总览

| 任务书给的 URL | 真实角色 |
|---|---|
| `/place/search.php` | 人机界面：**服务端渲染 HTML**。空壳页含大量侧栏示例 `search.php?code=PL...` 链接；`code=<ID>` 渲染单条详情页；真正的名称搜索参数是 **`ml`**（来自 `form.php` 的表单 `name="fml" action="search.php" method="get"`）。 |
| `/docs/services/place_query.php` | 服务文档页，给出**真实数据 API**：`/webwidget/getAuthorityData.php?type=place&id=<AuthorityID>&jsoncallback=<cb>` |

数据 API 与搜索界面是两个覆盖面不同的层（文档原文）：
- API/下载仅含 **DILA 自修纂 ~18,000 筆**（CC BY-SA 3.0，允许本地镜像）；
- 在线搜索界面另含与中研院 CCTS 授权的 ~40,000 筆 —— 这部分**只能看搜索 HTML，id 详情 API 取不到数据** [INFERENCE：由文档声明 + 未实测具体中研院条目 id；连接器对 `data1` 为空一律静默跳过，行为安全]。

## 2. 详情接口（getAuthorityData.php）

样例请求（实测）：
```
GET https://authority.dila.edu.tw/webwidget/getAuthorityData.php?type=place&id=PL000000010214&jsoncallback=probe1
```
样例响应（原始，UTF-8，`\uXXXX` 转义中文）：
```
probe1({"data1":{"authorityID":"PL000000010214","name":"遯村","dynasty":null,
"long":"120.6467","lat":"31.1657","districtHistorical":null,
"districtModern":"中國-江蘇省-蘇州市-吳江區",
"note":"位吳江。蘇州府遯村報恩浮石通賢禪師，出住吳江之報恩上堂。（X82n1571_p0313c24）",
"lang":"中文","shortAuthorityID":"PL10214","names":"",
"pinyin":{"遯村":"dùn cūn"}}})
```

格式判定：
- 带 `jsoncallback` → **JSONP**：`<cb>({...})`；省略该参数 → **裸 JSON**（实测二者皆可）。
- 解包：正则 `^[^(]*\((.*)\)\s*;?\s*$` 剥壳后 `json.loads`；裸 JSON 直接 loads。
- 未命中/无效参数的行为（实测）：`id=PL999999999999` → `cb(null)`；`name=遯村`（API 不认名称参数）→ `cb({"data1":""})`。

字段表（文档字段表 ∪ 实测字段）：

| 字段 | 类型/示例 | 说明 |
|---|---|---|
| `authorityID` | `"PL000000010214"` | 规范码（长码，PL+12 位） |
| `shortAuthorityID` | `"PL10214"` | 短码（PL+5 位，与长码后段一致，可本地补零互转） |
| `name` | `"遯村"` | 规范权威名 |
| `dynasty` | `null` / `"慣用名"` / 朝代名 | 朝代/使用期标注，可空 |
| `long` / `lat` | `"120.6467"` / `"31.1657"`（字符串） | 经纬度。**搜索页注明站内 Z 码系统用 GRS67 基准，与 GPS/Google Earth 的 WGS84 略有出入**；API 字段未标基准，跨源比对坐标时留 ±量级容差 |
| `districtHistorical` | `null` | 历史行政区（本例为空） |
| `districtModern` | `"中國-江蘇省-蘇州市-吳江區"` | 现代行政区，`-` 分级 |
| `names` | `""` / `"嵩高山,中嶽,外方"` | 异名串（逗号分隔） |
| `note` | `"位吳江。……（X82n1571_p0313c24）"` | 说明；**末尾括注即文献出处**（卍续藏 X82n1571 页行号），连接器用尾括注正则提取入 `source_citation` |
| `lang` | `"中文"` | 主名语言 |
| `pinyin` | `{"遯村":"dùn cūn", ...}` | 主名+异名的拼音映射 |
| `mergeTo` | Place ID | 文档声明：已合并条目的合并目标（实测样本未遇到） |

## 3. 名称搜索接口（search.php）

样例请求（实测）：
```
GET https://authority.dila.edu.tw/place/search.php?ml=%E9%81%AF%E6%9D%91&isLikeSearch=1&isFurther=0
```

参数（来自 `form.php` 表单 `name="fml"`）：

| 参数 | 值 | 说明 |
|---|---|---|
| `ml` | UTF-8 名称词 | 搜索词（**`searchWord`/`code`+中文名 均无效**：实测 `searchWord=` 返回空壳页、`code=<非ID串>` 同） |
| `isLikeSearch` | `1`（默认，模糊 LIKE）/ `0`（精确） | |
| `isFurther` | `0`/`1` | 高级过滤开关（`country_admin_lv1`=国家码 A000001=中國 等级联） |

返回：**HTML**（非 JSON）。命中条目结构（逐块）：
- 命中块定界：`<div id="" class="fpr_div"> … </div>`；页头计数行 `檢索【 遯村 】(地名：1 筆，群組：0 筆)`。
- 块内字段（文本形式）：名+拼音、規範碼 `PLxxxxxxxxxxxx`、規範碼短碼、**舊規範碼 `CN0320584A06AA(僅供參考請勿使用)`（勿用）**、地名分類、緯度/經度(估計值) + KML 下载、行政區、註解、Occurs in（文献出处，如 `g009p0397(普陀洛迦新志)`）。
- **提取纪律**：规范码只准在 `fpr_div` 块内提取——搜索壳页侧栏含大量示例 PL 链接（实测 `PL000000000083` 等），整页正则会污染结果。连接器 `_extract_hit_ids` 已按块定界并有回归测试。

## 4. 限速观察

- 无官方限速文档（docs 三页均未提及）。
- 实测 2026-10-02：连续 10+ 次请求（详情+搜索混发），单次延迟 0.7s~4.5s，无 429/无验证码/无封禁。
- 连接器保守节流：默认相邻请求 ≥1.2s（`DilaProvider(min_interval_sec=...)` 可调），并在 UA 里带项目标识。

## 5. 连接器（haidian_kg/providers/dila.py）

- `DilaProvider.fetch_by_id(authority_id) -> Optional[AuthorityMatchRecord]`
  - 长码原样；`PL+5位` 短码本地补零展开为长码；其余格式拒收（不发请求）。
  - 字段映射：`name→matched_name`、`dynasty→historical_years`、`districtModern→parent_jurisdiction`、note 尾括注→`source_citation`、坐标/异名/拼音/短码全量进 `raw_payload`；`license_class=CC_BY_SA`、`granularity=MICRO_VILLAGE_SETTLEMENT`、`match_method=EXACT`、`matched_uri=详情页 URL`。
- `DilaProvider.fetch_by_name(name, max_results=5) -> Optional[List[AuthorityMatchRecord]]`
  - `ml` 模糊搜索 → 块内提规范码 → 逐条 `fetch_by_id`（受 `max_results` 上限）→ 中研院授权子集条目（`data1` 空）静默跳过。
  - 语义区分：**传输层失败 → None；成功零命中 → []**。
- 失败纪律：`_http_get` 捕获一切异常返回 None（含 URLError/超时/解码）；解析失败同样 None；绝不抛异常阻塞闭包流水线（与 `authority_resolver.py` 设计纪律第 5 条一致）。
- 不修改任何 `calibration/*.py` 与 `authority_resolver.py`（按冲突协调改放独立文件，复用其类型）。

## 6. 测试覆盖（tests/haidian_kg/test_dila_provider.py，20 例全 mock）

字段全映射、朝代透传、短码展开、非法 id 拒收（零网络）、`null`/`data1:""`/乱码 → None、真 urlopen 抛 URLError 全链路静默、搜索→详情管线、fpr_div 定界防侧栏污染、`max_results` 上限、授权子集跳过、零命中 `[]`、搜索失败 None、JSONP/裸 JSON 解析、大小写/补零归一。
