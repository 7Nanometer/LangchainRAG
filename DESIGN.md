---
name: "Nano回执"
description: "电商知识库问答系统的设计系统——纸白、墨黑、发丝线；颜色只落在数据与状态上，每条答案附一张可对账的回执"
colors:
  paper: "#ffffff"
  paper-2: "#f6f6f4"
  panel: "#ffffff"
  ink: "#111111"
  ink-hover: "#2e2e2e"
  ink-2: "#575757"
  ink-3: "#6f6f6f"
  rule: "#d7d7d7"
  rule-2: "#ebebe9"
  tint: "rgba(17, 17, 17, 0.045)"
  tint-2: "rgba(17, 17, 17, 0.09)"
  stamp: "#c8372d"
  ok: "#038141"
  warn: "#b36b00"
  score-1: "#038141"
  score-2: "#6aa62c"
  score-3: "#c9a600"
  score-4: "#d97300"
  score-5: "#e63e11"
  focus-ring: "#111111"
typography:
  display:
    fontSize: "34px"
    fontWeight: 700
    fontFeature: "'tnum' 1"
  title:
    fontSize: "26px"
    fontWeight: 800
    letterSpacing: "-0.01em"
  stat:
    fontSize: "22px"
    fontWeight: 700
    letterSpacing: "-0.01em"
    fontFeature: "'tnum' 1"
  headline:
    fontSize: "20px"
    fontWeight: 700
    letterSpacing: "-0.01em"
  section:
    fontSize: "16px"
    fontWeight: 700
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.7
  small:
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.7
  meta:
    fontSize: "12px"
    fontWeight: 400
  label:
    fontSize: "11px"
    fontWeight: 600
    letterSpacing: "0.08em"
rounded:
  r-1: "3px"
  r-2: "2px"
spacing:
  sp-1: "4px"
  sp-2: "8px"
  sp-3: "12px"
  sp-4: "16px"
  sp-6: "24px"
  sp-8: "32px"
  sp-12: "48px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.r-1}"
    padding: "8px 15px"
    height: "32px"
  button-primary-hover:
    backgroundColor: "{colors.ink-hover}"
  button-primary-active:
    backgroundColor: "#000000"
  button-default:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.r-1}"
    height: "32px"
  button-text:
    textColor: "{colors.ink-2}"
    rounded: "{rounded.r-1}"
    padding: "4px 8px"
  input:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.r-1}"
    height: "32px"
  tag:
    backgroundColor: "transparent"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.r-2}"
    padding: "0 6px"
    height: "20px"
  panel:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.r-1}"
    padding: "{spacing.sp-4}"
  menu-item:
    textColor: "{colors.ink-2}"
    rounded: "{rounded.r-1}"
    height: "38px"
  receipt-strip:
    textColor: "{colors.ink-2}"
    padding: "7px 8px 7px 0"
---

# Design System: Nano回执

## Overview

**Creative North Star: "The Open Receipt（公开回执）"**

这个系统的核心隐喻是：**每一条回答都开出一张可审计的回执**。可信不来自说辞，而来自格式本身——答案旁边永远贴着来源、相关度、耗时与检索漏斗，逐项披露、可以核对。视觉世界是"事实面板"（强制披露标签传统）：纸白、近墨黑、发丝细线构成一张细线网格；颜色是数据与状态的特权，其余一切只剩墨、纸与留白。已确认的视觉反参考：黑底霓虹 AI 聊天壳、大圆角卡片流、玻璃拟态与渐变文字——它们都试图用氛围代替证据，与这个世界相反。

界面的密度与节奏像一份印刷对账单：一行就是一行，数字纵向对齐，线只画在该画的地方。组件哲学是"像一支好用的对账笔"——精确、克制、不装饰。深度默认是平的：常态表面没有阴影，只有发丝线与纸面明暗（凹陷处用更浅的纸色），阴影留给弹窗、下拉、提示这类"临时浮层"。动效只有一个签名：回执"打印"（一条 1px 墨线从左展开到位，行项依次落定）；其余动效只是 120/240ms 的状态反馈，并全局遵循 `prefers-reduced-motion`。夜间现场（深色主题）把纸翻黑、墨翻白，各岗位颜色只换曝光不下岗。

**Key Characteristics:**
- 纸白 · 墨黑 · 发丝线：全站靠 1px 细线"画画"，靠留白与线划分层次。
- 颜色只落在数据与状态上：评分色阶（绿→红）、印章红、完成绿、处理中琥珀，各有岗位，不许装饰性使用。
- 控件是黑白语言；主按钮像一枚"盖章"（墨底纸字）。
- 一切数字 tabular-nums；粗标签（11px/600/加字距）配细数值（400 字重）。
- 圆角一律收在 1–3px；无胶囊、无正圆（连圆形图标按钮都方化为 3px 圆角）。
- 唯一的"出场"动画属于回执打印：墨线展开＋行项落定。
- 深度不用阴影表达：常态平面＋发丝线＋纸面明暗；阴影只给临时浮层。

## Colors

一份"黑白为主、颜色上岗"的调色盘：纸白与墨黑承担结构与强调，饱和度高的颜色全部有明确职务（警示、状态、相关度数据），任何一处彩色都必须能回答"它披露了什么"。

### Primary

- **墨黑 Ink Black** (#111111)：全站唯一的强调。主文字、主按钮底（墨底纸字）、聚焦环、选区反白、回答里的引用编号角标。强调靠面积与黑白对比，不靠色相。

### Secondary

状态色（各司其职，只报状态不做强调）：
- **印章红 Stamp Red** (#c8372d)：只做警示、失败与"未命中 · 兜底回答"。表单里连 Element 默认的红色必填星号都被隐藏——红在本世界是"印章色"，不许出现在非警示场合。
- **完成绿 Resolved Green** (#038141)：完成 / 高相关。
- **处理中琥珀 Waiting Amber** (#b36b00)：进行中 / 中等。

### Tertiary

评分色阶（相关度专用，绿→红五档）：**score-1** (#038141) → **score-2** (#6aa62c) → **score-3** (#c9a600) → **score-4** (#d97300) → **score-5** (#e63e11)。只出现在回执来源行的 8px 小方块与百分比旁边；分档阈值：≥70% / ≥64% / ≥58% / ≥52% / 其余。它不是品牌色，不是装饰色，是数据本身。

### Neutral

- **纸白 Paper** (#ffffff)：页面底色与面板底。
- **浅纸 Paper-2** (#f6f6f4)：凹陷区域——回执展开体、输入底、表头、统计单元格。
- **次级墨 Ink-2** (#575757)：对账信息（对比度 7:1）——回执摘要行、次级说明、默认按钮文字。
- **三级墨 Ink-3** (#6f6f6f)：元信息与标签（对比度 5:1）——时间戳、标签、占位文案。
- **发丝线 Rule** (#d7d7d7)：明线——面板边框、栏位分隔、行分隔。
- **内部分隔线 Rule-2** (#ebebe9)：暗线——面板内部的琐碎分隔（来源行、事实格）。
- **悬停 / 按压填充 Tint / Tint-2** (rgba(17,17,17,0.045) / 0.09)：所有 hover 与 active 只靠这层极淡的墨，不换色。

夜间现场（深色主题，`html.dark`）：纸翻黑 #101010、面板 #161616、浅纸 #191919（凹陷在夜里靠"更亮"表达）；墨翻白 #ececec、次级 #b4b4b4、三级 #8f8f8f；线转 #2e2e2e / #232323；悬停填充改为白色极淡（rgba(255,255,255,0.05) / 0.10）；状态色与评分色阶只调曝光：印章红 #e0604f、完成绿 #2da05e、处理中琥珀 #d08a2e，评分五档换为夜间版本。切换机制＝给 `html` 加 `dark` 类（记忆在 localStorage，可跟随系统）。

### Named Rules

**The Ink Chrome Rule（墨色控件规则）。** 控件只有黑白语言：主按钮墨底纸字，其余控件透明底加发丝描边；不存在彩色按钮、彩色链接或彩色图标（图标一律继承墨色）。

**The Stamp Rule（红只盖章规则）。** 印章红只允许出现在警示、失败与兜底标记上；禁止作为按钮、品牌、选中或装饰色。它是印章，用一次就作废一次。

**The Data-Only Color Rule（颜色只上数据规则）。** 评分色阶与状态色只画数据（相关度、成败、进度）；界面其余部分只准出现墨、纸与线。

## Typography

**Display Font:** 系统字体栈（-apple-system, BlinkMacSystemFont, PingFang SC, Microsoft YaHei, Segoe UI, Helvetica Neue, Arial, sans-serif）
**Body Font:** 同上——一套系统字解决全部界面
**Label/Mono Font:** 数字＝同栈 + tabular-nums；代码块例外，用 Cascadia Mono / Consolas 等宽栈

**Character:** 中文优先的系统黑体，层级不靠换字体，靠字号阶梯（11/12/13/14/16/20/22/26/34）、字重与字距。这不是"还没选字体"：本地部署可能无法访问外网，不引外部字体与 CDN 是硬约束，系统字体栈是明确的决定——靠等宽数字与加字距的粗标签，把"对账"的质感做出来。

### Hierarchy

- **Display** (700, 34px, tabular-nums): 结果页大数字（404 / 异常页）——全站最大字号，用来报数。
- **Title** (800, 26px, -0.01em): 登录/注册页标题。
- **Stat** (700, 22px, -0.01em, tabular-nums): 看板"事实格"的大数字。
- **Headline** (700, 20px, -0.01em): 页面标题（page-head）。
- **Section** (700, 16px): 面板标题、弹窗标题、回答正文内标题。
- **Body** (400, 14px, 1.7): 正文与回答（中文行高 1.7）。
- **Small** (400, 13px, 1.7): 面板主文、会话标题、表格、键值行。
- **Meta** (400, 12px): 回执摘要行、次级说明、表单错误文案。
- **Label** (600, 11px, 0.08em): 粗标签——字段名、表头（0.06em）、漏斗标签（10.5px 光学特例）。

### Named Rules

**The Lined Numbers Rule（数字必等齐规则）。** 一切数字——编号、百分比、耗时、时间戳、计数——必须 tabular-nums。对账的前提是纵向能对齐，数字不齐等于不可信。

**The Coarse Label, Thin Value Rule（粗标签 · 细数值规则）。** 披露总成对出现：标签是 11px/600/0.08em 的小粗字，数值是 400 字重的等宽数字。标签负责说"这是什么"，数值负责"是多少"，两者不许抢戏。

## Layout

工作界面的空间模型是"细线网格里的阅读栏"：顶部一条 54px 导航横栏（发丝底边），其下按场景分栏——问答页＝252px 会话侧栏 + 中部 820px 阅读栏（消息流与输入框共用同一限宽、居中）；管理后台＝208px 左侧菜单 + 全宽披露区；登录/注册＝880px 双栏面板（左表单、右"示例回执"）。

响应式有三个断点，各司其职：**768px**（问答页侧栏收进 272px 抽屉，顶部出现一条细栏）、**840px**（登录/注册面板转单列）、**900px**（后台菜单由竖排转横排，看板事实格 4 列转 2 列）。手机是"能用且不降级"的目标，不是另一套设计。

间距节奏以 4px 为基数（4/8/12/16/24/32/48），并允许 1–2px 级的光学微调（如 7px、9px 行内边距，让文字对上线）。密度偏"工作报告"：列表行 32–38px，信息以行与格逐项披露，一屏能读多条对账信息。

### Named Rules

**The Reading Column Rule（阅读栏规则）。** 对话流与输入框共用 820px 限宽居中；任何新页面都不许让正文随窗口无限拉伸。桌面越宽，留白越多，文字列不变。

## Elevation & Depth

**默认是平的。** 常态表面（面板、侧栏、顶栏、列表行）没有阴影，层次由两件事表达：1px 发丝线（rule / rule-2）与纸面明暗（paper 与 paper-2 的凹陷）。阴影只出现在"临时浮层"上——弹窗、下拉、消息提示——并且永远是"向下偏移＋大模糊"的柔影，用来表示"它浮在纸面上"，不做光晕、不做贴边硬影。夜间现场把阴影加深（透明度 0.55/0.45/0.40），因为纸面本身变暗，需要更重的落影才浮得起来。

### Shadow Vocabulary

- **浮层大（dialog）** (`0 10px 32px rgba(0, 0, 0, 0.1)`): 弹窗、确认框。
- **浮层中（dropdown / popper）** (`0 6px 20px rgba(0, 0, 0, 0.08)`): 下拉菜单、选择器、消息提示（toast）。
- **浮层小** (`0 4px 14px rgba(0, 0, 0, 0.07)`): 更轻的浮层档位（Element 的 lighter 档）。
- **夜间浮层** (`0 10px 32px rgba(0, 0, 0, 0.55)` 等): 同岗位、深曝光的三档。

### Named Rules

**The Flat-By-Default Rule（默认平面规则）。** 表面在静止状态永远是平的；阴影是"浮层出现"的响应，不是装饰。新组件若想要阴影，先回答：它是浮层吗？

## Shapes

形式语言是印刷品：**1px 发丝线是主要的绘画手段**——面板边框、行分隔、栏分隔、回执的打印墨线，都是同一条线的变体。圆角收紧在 1–3px 带内：3px（r-1）用于面板、按钮、输入框、弹窗、菜单项；2px（r-2）用于小签、代码、菜单行；评分方块 1px。没有胶囊、没有装饰性正圆——圆形图标按钮被强制 3px 圆角，头像 3px 圆角；圆形的例外只剩功能性器件：滚动条拇指（6px，必须抓得住）、加载旋转环与图表里的数据圆点。

反复出现的几何是**小方块家族**：8px 评分方块、8px 印章方块、5px 选中墨点、3×12px 回执打印墨块、15px 引用编号小方块、标志里偏右下的实心方块——方块＝"这是数据 / 这是状态"的通用标记。品牌标志本身就是这个语法：细线外框（圆角 4px 的方框）＋内部一枚偏右下的实心方块，单色可用。

### Named Rules

**The Paper-Corner Rule（印刷直角规则）。** 圆角一律 1–3px；任何大于 3px 的圆角、胶囊或正圆，都要先证明自己为什么不是一份印刷品。

## Components

组件哲学是"像一支好用的对账笔"：精确、克制、不装饰；每个组件先回答"我在披露什么"。

### Buttons

- **Shape:** 3px 圆角 (r-1)，字重 500、字距 0.01em。
- **Primary:** 墨底纸字（{colors.ink} / {colors.paper}）——像一枚"盖章"；常规高 32px、大号 40px、聊天发送钮 38px（0 20px 内距）。
- **Hover / Focus:** hover 升到 #2e2e2e、按下到 #000000（黑上加黑，不换色相）；夜间反转——底 #ececec、字 #101010，hover 全白、按下 #d6d6d6；聚焦一律 2px 墨色细环、offset 2px，只在 `:focus-visible` 出现。
- **Ghost / Text:** 默认按钮＝面板底＋1px 发丝描边＋ink-2 文字；文字按钮（is-text）hover 只加一层 tint 底；"停止生成"按钮平时是发丝描边，hover 时描边与文字才升到墨色。

### Chips

- **Style:** 一律"发丝小签"：透明底、1px 发丝描边、2px 圆角、11px 字、高 20px、tabular-nums。
- **State:** 状态签只变描边与文字颜色（完成绿 / 危险红 / 警示琥珀 / 墨色）；不存在实心彩色签。回执里的"复用"签同此制。

### Cards / Containers

- **Corner Style:** 3px (r-1)。
- **Background:** 面板＝纸白 {colors.panel}；凹陷体＝浅纸 paper-2。
- **Shadow Strategy:** 无——见 Elevation & Depth（平面＋发丝线）。
- **Border:** 1px 发丝线（rule）；内部细分隔线 rule-2。
- **Internal Padding:** 16px 起（panel-pad 为 16/16/12，底边略收做光学平衡）。

### Inputs / Fields

- **Style:** 描边以内阴影形式给出（`0 0 0 1px rule inset`），3px 圆角、面板底；占位文案 ink-3；光标是墨色（caret-color）。
- **Focus:** 内描边加粗到 1.5px 墨色（不是外发光）；hover 时先升到 ink-3。
- **Error / Disabled:** 错误文案用小号印章红（12px）；禁用文字 ink-3。

### Navigation

- **Topbar:** 54px、发丝底边；左侧品牌标志（点击回问答页），右侧主题切换按钮（圆形按钮被方化为 3px 圆角）＋ 1×18px 发丝竖分隔 ＋ 用户区（24px 墨底纸字头像、13px 用户名、管理员发丝签）；下拉菜单项 13px、3px 圆角、hover 加 tint。
- **Chat sidebar:** 252px、发丝右边；会话行＝5px 选中墨点（选中才填墨）＋13px 标题＋11px 时间；hover 加 tint，选中 tint-2＋字重 600；改名/删除只在 hover 或选中时现身。
- **Admin menu:** 38px 行高、3px 圆角、1px 6px 外距；hover tint、选中 tint-2＋600 字重；窄屏整条菜单转横排（不藏进抽屉），"返回问答"文字按钮常驻。
- **Mobile:** 小于 768px 时会话列表进入 272px 抽屉，顶部细栏放"会话"文字按钮与小号标志。

### 答案回执 ReceiptPanel（签名组件）

每条 AI 回答下方的一张"强制披露"面板：折叠态是一条发丝线上的对账行（3×12px 墨块＋"回执"＋№编号＋来源段数＋相关度＋复用签＋耗时＋时间）；展开态是逐项披露（来源明细、检索漏斗四格、生成指标）。它承担全站唯一的"出场"动画：一条 1px 墨线从左打印到位（420ms），展开体的行项以 45ms 步进依次落定（240ms，最多 8 步）。兜底回答用印章红方块＋红字"未命中 · 兜底回答"标记。回答正文里的 [n] 角标是墨底纸字的 15px 小方块，点击可展开回执并高亮定位到该条来源。

### Named Rules

**The One Signature Rule（唯一签名规则）。** 全站唯一的"出场"动画属于回执打印（墨线展开＋行项落定）；其余一切动效只是状态反馈（120/240ms，统一缓动 cubic-bezier(0.16, 1, 0.3, 1)）。禁止给其他元素加出场动画；`prefers-reduced-motion` 下全部动效收为瞬态。

## Do's and Don'ts

### Do:

- **Do** 让墨黑承担一切强调：主按钮（墨底纸字）、选中（tint-2）、聚焦环（2px 墨色细环）、引用编号——靠黑白对比，不靠色相。
- **Do** 一切数字加 tabular-nums；披露行永远"标签在左、数值在右"。
- **Do** 新表面先试"只用一条 1px 线"划分层次；需要凹陷就用 paper-2，不用阴影。
- **Do** 阴影只给弹窗、下拉、提示这类浮层，用带偏移的大模糊柔影（见 Elevation 词汇表）。
- **Do** 圆角保持 1–3px、方块标记保持直角；状态只用"描边＋文字颜色"表达。
- **Do** 状态色按职务使用：印章红＝警示/兜底，绿＝完成/高相关，琥珀＝处理中；评分色阶只画相关度。
- **Do** 面板与表单遵循 4px 间距节奏（12/16/24/32/48），允许 1–2px 的光学微调让文字对上线。

### Don't:

- **Don't** 使用黑底霓虹 AI 聊天壳、发光或渐变文字、玻璃拟态（已确认的反参考）。
- **Don't** 使用大圆角卡片流（大于 3px 的卡片圆角）、胶囊按钮、正圆头像或圆形装饰点。
- **Don't** 把印章红（#c8372d）用作按钮、品牌或强调色；连表单必填星号都已隐藏。
- **Don't** 给常态表面加投影、光晕或多层阴影。
- **Don't** 引入外部字体或 CDN；中文排版走系统字体栈（本地部署可能无外网的硬约束）。
- **Don't** 给回执以外的元素加"出场"动画；数据、状态、数量之外的东西不要动起来。
