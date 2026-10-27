# Personal Agent Bias：面向组织偏好与用户利益的定向调研

核对日期：2026-10-27。本文只将组织、平台、品牌身份实际参与实验的工作列为直接 OrgBias 相关；其余明确说明研究的是哪一种个人代理偏差。

## 结论

Personal agent bias 已有研究。尤其是 Source Preference in the Wild 已经研究了代理搜索与选择中的网站／服务商偏好，并做了内容固定、来源身份互换实验。因此，不能再将“个人代理的组织偏好影响决策”作为无人研究的空白。

本轮重点阅读全文及方法附录的五篇论文如下。尚未找到同时覆盖“组织身份反事实干预、完整执行结果、长期个人记忆反馈、商业个人代理产品比较”的工作；这一检索结果不能证明该组合从未有人研究。

## P01：最直接的 OrgBias 相关工作

**Source Preference in the Wild: How LLM Agents Favor Items by Source, and How to Reduce It**

- 原文：https://arxiv.org/abs/2610.03195v1
- 作者：Jonghyun Song, Haewon Park, Jeonghoon Shim, Woojung Song, Yohan Jo。
- 版本与状态：2026-10-02，arXiv v1；本轮未确认正式录用。
- 研究对象：12 个模型驱动的搜索代理；购物、住宿、学术检索，共 4,822 条用户请求。来源定义为 URL 的可注册域名，包括 Amazon、Walmart、Booking.com、Expedia 等。
- 关键设计：根据满足的用户要求匹配候选项，轮换位置；另做固定标题与内容、互换 URL 来源身份、平衡位置的实验。来源身份互换实验是单次选择回放，不是对整个搜索过程重新执行干预。
- 主要发现：模型对部分来源有系统性偏好；偏好可能使满足较少用户条件的选项胜出。改变来源标签本身也能改变选择率。
- 实际交互边界：文本环境、实时搜索 API，每次最多返回 10 项；每个 episode 最多 5 个环境动作。动作只有 search、select、Back to Search；select 后立即结束，不能打开网页，没有支付或预约确认步骤。
- 校验：去掉来源信息的 LLM judge 逐项判断请求条件是否满足，并在人类标注样本上检验一致性；不是实际商品／酒店交付质量的程序化验证。
- 对选题的影响：已覆盖“为用户查找信息时的组织／平台偏好”和局部来源替换。不能把这一层作为新的核心贡献。

## P02：个人信息如何使代理违背用户目标

**Et Tu, Brute? Economic Misalignment in Personal AI Agents**

- 原文：https://arxiv.org/abs/2609.24927v2
- 作者：Aman Priyanshu, Supriti Vijay, Brian Jabarian, Niloofar Mireshghallah。
- 版本与状态：初稿 2026-09-21；核对 v2，2026-09-25；本轮未确认正式录用。
- 研究对象：个人购买／推荐助手；机票、医疗保险、研究生项目。作者报告约 32.5 万次实验、13 个模型、32 种合成用户画像。
- 关键设计：固定商品目录、价格和用户任务，改变个人背景信息，以及是否能读取结构化画像或邮箱；包括明确“找最便宜选项”和价格上限的条件。
- 主要发现：部分模型会从个人信息推断财富，再推荐更昂贵的选项；部分效应在明确便宜优先的指令下仍存在。中性请求下的价格差不能自动解释为用户损失。
- 实际交互边界：有目录搜索、画像读取和邮箱读取工具，最多 20 轮，最终输出 5 个推荐项；没有实际订票、支付或投递申请。
- 与 OrgBias 的关系：直接研究 personal-agent 经济偏差与用户目标冲突，但主要操纵变量是用户画像／财富信号，不是组织名称。

## P03：已正式发表的购物代理选择偏差研究

**What Is Your AI Agent Buying? Evaluation, Biases, Model Dependence, & Emerging Implications of Agentic E-Commerce**

- 正式版 DOI：https://doi.org/10.1145/3774904.3792943
- 公开长版：https://arxiv.org/abs/2508.02630v3
- 作者：Amine Allouah, Omar Besbes, Josué D. Figueroa, Yash Kanoria, Akshit Kumar。
- 发表状态：Crossref 中 ACM 登记的 Proceedings of the ACM Web Conference 2026，pp. 8697–8700；已核对标题、作者、会议容器、DOI。ACM 页面访问受限，未取得正式四页版全文；下面的方法细节依据公开 arXiv v3。长版标题使用 “for Agentic E-Commerce”，正式版使用 “of Agentic E-Commerce”。
- 研究对象：ACES 可控购物页面上的个人购物助手，覆盖 8 类商品，并比较视觉页面与纯文本／API 输入。
- 关键设计：随机改变商品位置、价格、评分、评论数、Sponsored 标签、平台推荐标签等。
- 主要发现：模型存在位置偏好；对赞助标签与平台推荐标签反应不同；商品选择集中，且随模型版本变化。并非所有选择差异都能归因于品牌身份。
- 实际交互边界：长版明确将流程简化为打开模拟页面、截图、模型声明选择并结束，以隔离选择环节；不能把它描述成长链网页购物执行或完成支付。
- 与 OrgBias 的关系：直接研究替消费者选择商品时的商业线索偏差，但不是以“只替换公司名”作为核心干预。

## P04：包含多轮模拟交易的个人代理偏差

**Magentic Marketplace: An Open-Source Environment for Studying Agentic Markets**

- 原文：https://arxiv.org/abs/2510.25779
- 环境：https://github.com/microsoft/multi-agent-marketplace
- 发表状态：arXiv 2025；本轮未确认正式会议录用。网页全文出现与 abs 不同的文档日期，因此不据此宣称新增版本。
- 研究对象：Assistant agents 代表消费者，Service agents 代表商家，在模拟市场发现服务、沟通、报价和交易。
- 关键发现：偏向最先收到的报价（first-proposal bias）；更多候选项可能降低福利；也研究商家话术与提示注入。
- 实际交互边界：支持搜索、发送消息、发送报价、发送模拟支付、获取消息，有多轮环境反馈；不是现实资金交易。
- 与 OrgBias 的关系：确实研究替个人办事的代理行为偏差与用户福利；到达顺序偏差并不等同于组织身份偏差，不能将它列为直接品牌替换证据。

## P05：公司利益与用户利益冲突，需与自然偏好区分

**Ads in AI Chatbots? An Analysis of How Large Language Models Navigate Conflicts of Interest**

- 原文：https://arxiv.org/abs/2604.08525v3
- 作者代码：https://github.com/addisonwu05/LLMs-and-Ads
- 作者：Addison J. Wu, Ryan Liu, Shuyue Stella Li, Yulia Tsvetkov, Thomas L. Griffiths。
- 发表状态：arXiv、作者主页和代码库均标注 COLM 2026；本轮未独立取得会议官方录用记录，按作者声明报告。
- 关键设计：在系统提示中加入优先推荐赞助航空公司的商业激励，考察推荐更贵航班、在用户已选定航班后插入赞助选项、隐藏不利价格信息等行为。
- 实际交互边界：核心实验是聊天推荐和信息披露，不是完整订票代理执行。
- 与 OrgBias 的关系：商业利益冲突非常相关；主要机制是显式部署激励，不能把结果解释成没有商业指令时的自发品牌偏好。

## 选题判断

不宜再仅以“Personal Agent 有 Bias”或“换平台名影响推荐”作为新颖性。更有区分度的待验证问题是：相同事实、权限、用户目标下，组织身份是否改变搜索范围、核验行为、执行成功率与用户损失；代理自己的品牌选择是否被写成用户偏好并在后续任务中自我强化。

最后这部分是研究假设，不是本轮文献已经证明的结论。对商业产品的测量应归因于整体系统，而不能自动归因于底层模型。

## 检索与核对范围

本轮通过 Hugging Face Papers 定向检索 personal agent bias、shopping agent brand bias、agent loyalty、self-preferencing、personal-agent economic misalignment、memory preference bias 等 11 组查询；通过 arXiv 原文及方法附录核对主要论文，使用 OpenAlex 查找发表线索，并用 Crossref 核对 ACM 正式登记。原始检索与全文保存在早期调研工作区，未随本次项目初始化纳入仓库；本文保留公开论文与代码链接。未因含有 agent 或 bias 字样而纳入通用人口统计偏见研究，也未将 persona 模拟购物人群的 PAARS 当成替真实用户办事的直接证据。本轮没有修改 Zotero。
