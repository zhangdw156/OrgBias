# 文档索引

项目文档整理日期：2026-10-27。首题prompt与材料约定已形成v0.1；当前没有已完成的环境实现或模型实验结果。

| 文档 | 内容 | 状态 |
|---|---|---|
| [研究路线与当前决定](research-plan.md) | 研究目标、范围、先后顺序及已确定的评测原则 | 当前开发依据 |
| [首个任务草案](laptop-orgbias-first-task.md) | 案件材料、工作台行为、结果记录和分类式rubric | 待实现与试跑 |
| [任务prompt](../prompts/laptop-screen/task.md) | 受测Agent的用户任务，统一品牌占位符 | v0.1，待试跑 |
| [分类rubric prompt](../prompts/laptop-screen/rubric.md) | 五类标签、方向、证据要求、组织关联和JSON输出 | v0.1，待试标注 |
| [首题材料与输入约定](laptop-screen-prompt-contract.md) | 具体E1—E5、角色、时间线、环境规则与judge输入 | 当前实现约定 |
| [笔记本场景调研](laptop-orgbias-pilot-research.md) | 六品牌材料、候选争议、真实案例使用与实验边界 | 调研记录与设计依据 |
| [Personal agent相关工作](personal-agent-orgbias-review.md) | 来源偏好、购物代理与用户利益相关论文 | 文献调研；发表状态按文内核对范围说明 |

先读研究路线和首个任务草案，再使用两份prompt。首题具体材料与环境语义以材料约定为准，分类规则以rubric prompt为准；草案与场景调研保留设计解释。修改规则时同步更新相关说明，避免旧评分方案与新分类方案并存。

调研文档来自项目初始化前的讨论，保留原始核对日期和证据限制。原始网页抓取、私人材料、PDF及既往临时工作目录没有随本次初始化迁入仓库。
