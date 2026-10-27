# 文档索引

项目文档整理日期：2026-10-27。部署原则已确定为独立ASP，task不安装Agent本体；任务prompt保持v0.2的无人值守与允许联网协议，rubric及材料约定更新为v0.3组级评判。ASP具体协议、Judge形态及上下文组织待确定，当前没有已完成的环境实现或模型实验结果。

| 文档 | 内容 | 状态 |
|---|---|---|
| [研究路线与当前决定](research-plan.md) | 研究目标、范围、先后顺序及已确定的评测原则 | 当前开发依据 |
| [首个任务草案](laptop-orgbias-first-task.md) | 案件材料、工作台行为、结果记录和分类式rubric | 待实现与试跑 |
| [任务prompt](../prompts/laptop-screen/task.md) | 受测Agent的用户任务，统一品牌占位符、无人值守授权 | v0.2，待试跑 |
| [组级rubric草案](../prompts/laptop-screen/rubric.md) | 全部组织与重复的比较、五类标签及证据要求；具体输出格式待定 | v0.3，待讨论与试标注 |
| [首题材料与输入约定](laptop-screen-prompt-contract.md) | 具体E1—E5、角色、时间线、环境规则与整组数据需求 | v0.3，具体上下文打包待定 |
| [工程设计讨论](engineering-design.md) | 独立ASP原则、Harbor接口、品牌渲染、无人值守与整组汇总 | v0.4，架构原则已定，尚未实现 |
| [Agent与Task分离部署](agent-task-deployment-review.md) | ASP与task独立维护、业务服务与远程工具；四个官方项目对照 | ASP原则已定，具体接入未实现或试跑 |
| [笔记本场景调研](laptop-orgbias-pilot-research.md) | 六品牌材料、候选争议、真实案例使用与实验边界 | 调研记录与设计依据 |
| [Personal agent相关工作](personal-agent-orgbias-review.md) | 来源偏好、购物代理与用户利益相关论文 | 文献调研；发表状态按文内核对范围说明 |

先读研究路线和首个任务草案，再使用任务prompt。首题具体材料与环境语义以材料约定为准，组级分类原则以rubric草案为准；Judge实现、上下文打包及最终输出schema待进一步确定。修改规则时同步更新相关说明，避免旧评分方案或单轨迹正式评判方案继续作为当前流程使用。

调研文档来自项目初始化前的讨论，保留原始核对日期和证据限制。原始网页抓取、私人材料、PDF及既往临时工作目录没有随本次初始化迁入仓库。
