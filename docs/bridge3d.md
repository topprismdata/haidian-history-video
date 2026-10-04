# bridge3d —— 古建三维 L1 验收框架接入指南

> 中国古建(石拱桥 / 牌楼 / 亭 / 佛塔 / 城墙 / 闸)三维管线通用的**数据层(L1)验收框架**。
> 首个验证项目: E30 石拱桥。第二个项目照本页接入, 不需要改框架一行代码。

## 0. 设计三原则(为什么长这样)

1. **拓扑不变量与项目常数分离** —— 判据源码里没有任何项目数值
   (框架由 `tests/bridge3d/test_no_project_literals.py` 用 AST 锁死, 连注释都不放)。
   项目常数只存在于项目 facts; 判据只验证"facts 自身声明的关系"。
2. **语义铁约**: 只有 `fail` 阻塞; `warn` 不阻塞但必须列出;
   `skip`=未执行, **不算通过**, 且绝不因缺可选事实而 `fail`。
3. **每条判据必须可证伪** —— 有"故意破坏"用例且破坏被抓;
   框架自带恒真检测器(自动生成破坏用例, 杀不死的判据即恒真, 直接红)。

## 1. 写 facts 模块(纯数据, 零 import)

```python
# myproject/facts.py  ——  ordinary module, 不要继承任何东西
"""<项目名> 尺寸事实清单。
禁令: 未标定照片不得产生绝对米制尺寸; 超分(ESRGAN)结果禁止进入计量链; GPT 聊天记录不算来源。
"""                                   # ← 三条禁令必须逐条在 docstring 里, 框架逐条锁
RESEARCH_DONE = True                  # 研究轮旗标(必填登记)
BRIDGE_LEN = 132.0                    # [必填] 拓扑递推的基准长
N_SPAN = 9                            # [必填] int(孔数是拓扑量, 不是测量值)
SPRINGER = 2.1                        # [必填] 起拱线标高
PIER_W = 2.0                          # [必填] 内墩宽
BRIDGE_ABUT = 1.4                     # [必填] 桥台宽
SPAN_DISTINCT = [4.0, 5.0, 6.0]       # [必填] 完整净跨表, 两种形态(2026-10-05 终审 I1):
                                      #   len == N_SPAN → 全长表直接用(任意桥: 不对称/偶数孔/等跨);
                                      #   len == (N_SPAN+1)/2 → 半侧含中央孔, 镜像展开 2n-1
                                      #   (对称奇数孔便利路径; 对称本身由 RELATIONS 自声明)
CLOSURE_TOL = 0.02                    # [可选] 闭合容差; 不给则闭合判据 skip(阈值必须有依据)
ARCH_RATIO = 0.5                      # [可选] 矢高/跨; 未给则券形类判据 skip
ARCH_RATIO_TARGET = 0.5; ARCH_RATIO_TOL = 0.05     # [可选] 券形设计意图(项目自声明)
RING_T = 0.35; DECK_UP_W = 5.0; DECK_DOWN_W = 9.0  # [可选]
DECK_Z_TOP = 6.0; DECK_Z_END = 4.8    # [可选] 纵坡控制点; 未给则纵坡类判据 skip
ASSUMPTION_NAMES = ("MESH_TOL",)      # [可选] 假设层参数名(不得混进 SOURCES)
RELATIONS = {                         # [可选] 项目自声明的关系型不变量:
    "central_span_largest":           # 判据只验证你声明的约束,
      lambda f: all(list(f.SPAN_DISTINCT)[i] <= list(f.SPAN_DISTINCT)[i+1] + 1e-9
                    for i in range(len(f.SPAN_DISTINCT) - 1)),
}
SOURCES = {                           # 来源五级: 测绘>档案>官方>图像推导>工作值
    "BRIDGE_LEN": ("官方", "县志 1993 卷三 http://..."),
    "N_SPAN": ("官方", "文保碑 2019 照片转记 http://..."),
    "PIER_W": ("工作值", "无文献, 沿用设计稿值"),   # 工作值必须写明"为什么没来源"
}
```

规则: 必填项缺一登记即 fail; 等级必须在五级内; `[工作值]` 必须写明出处状态;
说明自认"无文献/沿用"却标高等级 = 等级造假 = fail; `[官方]` 必须给 URL 或"机构+年份"
(否定语境里的年份不算); RELATIONS 的 lambda 必须纯函数(只读 f, 不 import 框架)。

## 2. 验收一行

```python
import bridge3d
findings = bridge3d.audit(facts)        # L1 三层(INV/MET/IMP) + 事实层校验
assert not bridge3d.has_fail(findings), bridge3d.summarize(findings)
```

只要 5 孔、23 孔还是 200 孔, 同一套判据直接可用 —— 这就是与首项目判据
(`if f.N_SPAN != <具体孔数>`) 的本质区别。

## 3. 负控制义务(写进项目 tests, 一条判据一个破坏用例)

```python
from bridge3d import negative_control as nc
nc.assert_criterion_rejects(bridge3d.run_l1, nc.mutate(facts, BRIDGE_ABUT=9.9),
                            "MET_CLOSURE")          # 破坏必须红
nc.assert_no_always_true(bridge3d.run_l1, facts,
                         corruptions=[("窄墩", nc.mutate(facts, PIER_W=0.1))],
                         derive_corruptions=[...])  # 恒真审计(双向)
```

**`corruptions` 的格式约定（踩过一次，务必照做）**：元素是 `(标签, 坏facts模块)`，
**不是** `(标签, lambda)`。检测器内部直接 `check(cf)`，传函数会让 `getattr(函数, "PIER_W", 默认)`
取到默认值、破坏永不触发，症状是"正常判据也被报恒真嫌疑"——看着像框架误杀，其实是用例无效。
**构造坏 facts 一律用 `nc.mutate(facts, 字段=新值)`**，别手写 lambda。

`assert_no_always_true` 区分**四种失败模式**（输出可能一样，成因不同）：

| # | 模式 | 成因 | 后果 |
|---|---|---|---|
| 1 | **过度约束**（合法基线就红） | 把单项目构型当普适律，如原 `MET_TAPER` 强制收分、原对称契约 | 拦。这是"见谁都咬"，比恒真更隐蔽 |
| 2 | **恒真**（任何破坏都不红） | 判据没在看东西，或用例不足 | 拦 |
| 3 | **死判据**（`codes` 点名的代码从没被触发） | 判据写了但永不生效；`codes=None` 时会被活代码的杀伤掩盖 | 拦（故**逐判据要点名**，或用 `assert_criterion_alive`） |
| 4 | **脆弱判据**（破坏下抛异常而非报告） | 缺前置防御 | 拦（铁律：必须报告，不能崩） |

推导规则护栏类判据(如支承数= N_SPAN+1: 递推规则恒产等长输出, 经由 facts 输入不可达)
用 `patched_derive`
做检测器级负控: 临时改坏推导, 判据必须红。

## 4. 边界(本框架管什么 / 不管什么)

- 管: facts 结构、来源完备性、拓扑自洽、度量自洽(阈值须有依据)、实现完整性。
- 不管: L2 网格实测判据、渲染/材质、冻结哈希 —— 仍属项目侧
  (参见 E30 `qa_l2.py` / `freeze_hash.py` 的做法)。
- 迁移提示: 旧判据里的项目数字 → 移进 facts(REQUIRED/RELATIONS);
  旧判据里的经验阈值 → facts 显式条目(如 CLOSURE_TOL)或调用参数;
  假设层参数 → assumptions 模块 + `ASSUMPTION_NAMES` 登记。
