---
version: 1
slug: "frontend-src-views-chatview-vue"
primary_target: "frontend/src/views/ChatView.vue"
related_targets: ["frontend/src/views/LoginView.vue","frontend/src/views/RegisterView.vue","frontend/src/layouts/MainLayout.vue","frontend/src/layouts/AdminLayout.vue","frontend/src/views/admin/DashboardView.vue","frontend/src/views/admin/DocumentsView.vue","frontend/src/views/admin/KnowledgeBaseView.vue","frontend/src/views/ProfileView.vue"]
---

# Surface brief —— Nano回执 · 前端全面视觉改造

- 范围：整个 Vue 前端（登录/注册、主框架、问答主页、管理后台、个人设置、404）；模式 = Operate（工作界面）。
- 受众与任务：访客（面试官/同行）第一眼认定"成熟、可信、获奖级"；使用者完成任务：提问 → 读答案 → 查出处 → 回看历史 →（管理员）维护资料。
- 约束：不换技术栈（Vue3 + Element Plus）；不引外部字体/CDN；深浅双主题与手机适配为硬需求。

## Direction contract

THESIS: 事实面板——每条回答附一张强制披露的"答案事实面板"（来源·相关度·耗时·检索漏斗），可信来自格式本身；拒绝品类默认的黑底霓虹 AI 壳与一切装饰性世界观。
OWN-WORLD: 纸白 #ffffff、近墨黑 #111111、发丝线 #d7d7d7 构成的细线网格；评分色阶 #038141→#e63e11 只做数据；字型＝系统黑体（Operate 常规）＋粗标签/细数值层级＋tabular-nums；控件黑白语言，印章红 #c8372d 仅做警示与兜底；深色＝夜间现场（#101010 纸黑翻转）。
STORY: 访客 3 秒内明白"这是每个答案都能对账的问答系统"；提一问 → 看答案逐字流入、回执逐项落定 → 展开回执 → 点编号跳到原文 → 相信它。
FIRST VIEWPORT: 标准问答外壳（左侧会话列表｜中部答案流与输入）＝首屏即见一条完整回答与其"答案回执"面板（签名动作所在：发丝线从左打印到位，行项依次落定）。
FORM: 事实面板（强制披露标签传统）；safer 候选序列第 1 位；seed key 177d4127。
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.

## 未决

- 深色主题的确切对比度与色阶需在成品验证阶段校准。
- 管理后台图表（ECharts）主题需在构建时定制并对齐本世界。
