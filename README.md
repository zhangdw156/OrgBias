# OrgBias

研究组织身份如何影响personal agent的证据判断、行动和用户结果。组织范围包括公司、品牌、平台、医院等；首个实验聚焦笔记本售后争议。

当前阶段：任务prompt为v0.2，采用无人值守、允许联网、多步执行、只交付最终回复的协议；rubric及材料约定为v0.3，正式bias评判在同一任务对应的全部组织与计划重复结束后统一进行。Judge形态和上下文组织待讨论；售后工作台、Harbor集成、模型评测与专用评测器尚未实现或运行。

架构原则已确定：受测Agent统一通过ASP（agent as service）接入，Agent部署与task独立维护。Task不安装Agent本体、harness及其专属依赖，切换Agent通过服务配置完成。ASP协议与工具路由尚未实现。

**开发环境**

项目使用Python 3.12和uv。在仓库根目录执行：

```bash
uv sync --locked
```

该命令按 `uv.lock` 准备项目自己的 `.venv`，无需手动激活。后续项目命令使用 `uv run`。当前尚无实验运行入口，也尚未加入Harbor或模型SDK等运行依赖。

**研究与任务文档**

- [文档索引](docs/README.md)：阅读顺序与文档状态。
- [研究路线与当前决定](docs/research-plan.md)：目标、范围、实验和评测原则。
- [首题任务prompt](prompts/laptop-screen/task.md)与[组级rubric草案](prompts/laptop-screen/rubric.md)：分别用于单次执行和全组织运行组的正式评审。
- [首题材料与输入约定](docs/laptop-screen-prompt-contract.md)：E1—E5、角色、时间线、工作台规则与judge输入。
- [工程设计讨论](docs/engineering-design.md)：ASP架构原则、Harbor接口、品牌渲染、无人值守与环境隔离。
- [Agent与Task分离部署](docs/agent-task-deployment-review.md)：独立ASP部署、任务服务、远程工具与官方项目实现对照。
- [首个任务草案](docs/laptop-orgbias-first-task.md)：售后取证、模拟工具、申请状态和分类式rubric。
- [笔记本场景调研](docs/laptop-orgbias-pilot-research.md)：品牌材料、真实案例、场景选择和证据边界。
- [Personal agent相关工作](docs/personal-agent-orgbias-review.md)：直接相关研究及相邻工作的区别。

**贡献约定**

遵守 [AGENTS.md](AGENTS.md)。Commit message必须使用Angular style，例如：

```text
feat(tasks): add laptop warranty dispute task
docs(rubric): clarify evidence classification rules
```
