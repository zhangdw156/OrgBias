# Agent与Task分离部署：ASP原则与调研

日期：2026-10-27。用户已确定ASP及Agent／task独立部署为架构原则。本文记录该原则、官方实现依据和待核对的接口细节；未安装或运行下述框架，未构建镜像，也未验证任何受测产品的服务接入。

**已确定的架构原则**

所有受测Agent通过ASP（agent as service）接入，与task独立部署。Agent本体、harness、专属依赖和认证配置由服务侧维护；task镜像和运行容器只包含任务环境、材料及必要的轻量客户端／工具接口。切换或升级Agent通过服务配置完成，不重建或替换task镜像。

每种可容器化Agent可以构建专属ASP镜像，每类任务环境维护自己的镜像，运行时通过服务接口连接。ASP可封装原生CLI或适配已有产品服务；有专门桌面环境要求的产品也在独立部署环境外提供ASP入口。服务化固定的是接入边界，不要求把不同产品替换成同一harness。

首题即采用“独立ASP＋task环境＋Harbor调度”，先接一个Agent也遵守此原则。ASP可由Harbor external适配器调用，也可由task内轻量客户端调用；具体入口和传输协议待实现核对，不改变Agent本体始终在ASP侧的边界。首题可以先提供售后业务接口，按需要增加远程终端等能力。

**镜像复用和运行隔离是两件事**

镜像是可复用的程序模板，容器是一次运行的实例。设有A种Agent镜像、E类任务环境镜像，拆开部署后维护量可以接近A＋E＋公共组件；E不必等于任务数量，例如多个售后案例可以共用一个服务镜像，仅加载不同案件配置。

每个task×agent×org×重复仍需要独立的运行状态。复用镜像不等于复用对话、案件数据库、浏览器登录态或可写工作区。固定镜像digest及Agent版本；品牌、案例和run_id在运行时注入，品牌变化不触发重新构建。

Harbor的installed模式确实可以在容器启动后安装Agent，避免保存组合镜像，但Agent本体及依赖仍进入task运行容器，安装与兼容工作也仍与task耦合。因此它只作为调研事实保留，不作为本项目的实施或过渡路径。

**ASP访问Task的两种方式**

| 方式 | Agent在哪里执行工具 | Task容器的职责 | 本项目适用性 |
|---|---|---|---|
| ASP访问独立业务服务 | 文件、终端和浏览器可以留在ASP的独立会话环境；通过API或网页访问业务服务 | 提供材料查询、售后办理、状态流转和日志 | 适合首题；不必把每一个shell动作转发到task容器 |
| ASP使用远程执行接口 | 文件、终端、浏览器等所需动作明确路由到指定trial环境 | 运行待操作的程序、文件系统或浏览器环境，不安装Agent本体 | 适合需要直接操作任务环境的任务；要求Agent支持工具委托或可适配执行接口 |

第一种情况下，“Agent的shell仍在Agent容器里”可以是正确设计：售后工作台本来就通过服务访问。第二种情况下，如果任务要求修改task容器内文件，而Agent只改了自己容器中的同名文件，就没有完成环境接入。共享目录也只解决部分文件可见性，不自动共享进程、依赖、端口和浏览器状态。

首题将E1—E4作为文本文件放入当前Agent的独立工作区，由Agent自主选择读取，不由适配器自动加载全文。E5及案件真值放在独立售后服务，Agent按业务规则查询E5并申请换货。服务协议可采用HTTP，在实际产品需要时提供MCP或网页入口。不同入口需保留相同案件语义，并记录工具呈现方式，不能默认它们对Agent行为完全等价。

**官方项目中已存在的实现**

| 项目及核对依据 | 已证实的做法 | 可以借鉴什么及其限制 |
|---|---|---|
| Harbor，`e77a18bf` | `BaseAgent`可通过`BaseEnvironment`控制任务环境；Compose支持main和sidecar；另有在task内安装CLI的installed模式 | 本项目采用external适配ASP，复用调度、隔离和日志基础；installed不作为项目接入路径，Compose连通也不等于工具已路由 |
| mini-swe-agent，`04d809ce` | Agent与Environment分开；`DockerEnvironment.execute()`把命令交给指定容器的`docker exec` | 是外部循环与任务执行分离的直接源码例子。它拥有自己的工具调用实现，不能推断所有闭源产品也能照搬 |
| OpenHands Software Agent SDK，`d0d9d813` | 官方示例使用`DockerWorkspace`连接预构建Agent Server，通过`RemoteConversation`运行并接收事件；另有客户端定义工具的示例 | Agent服务化、远程工作区和事件协议已有成熟实现范式。示例中的Agent循环也可以在远端服务内运行，不能笼统描述为“所有Agent始终在宿主机” |
| OpenSandbox，`7761d993` | 生命周期API与容器内命令／文件执行API分开；提供MCP工具和Harbor接入示例 | 可作为以后扩展远程执行的备选。核对版本的Harbor后端不支持Compose多容器，不能直接替换当前首题的Docker多容器方案 |

这些项目证明了可复用的设计方式，不证明OrgBias已与它们完成集成。OpenHands不能替代其他受测产品的原生harness；OpenSandbox是环境服务，也不会自动把一个产品的全部原生工具迁移过去。第一题无需同时引入这些框架。

**推荐调用关系**

```mermaid
flowchart LR
    H[Harbor：本次运行的调度] --> A[ASP 客户端适配器]
    H --> T[独立task环境及案件服务]
    A --> R[独立 ASP：原生Agent与本次会话]
    R -->|查询与办理| T
    A --> L[轨迹、最终回复与运行状态]
    T --> S[可信案件状态与业务日志]
    L --> G[同一task全组织及重复汇总]
    S --> G
    G --> J[齐备后统一评判，Judge形态待定]
```

图示采用Harbor external适配器调用ASP；task内轻量客户端调用ASP也是允许的入口，具体方式待实现核对。客户端负责等待、流式事件、超时和取消，Agent运行逻辑始终在服务侧。案件业务逻辑无需依赖当前受测Agent的种类。

Harbor的main保留为task执行环境，按需要提供轻量ASP客户端或工具执行接口；售后后端可作为case-service sidecar。独立ASP镜像不替换task的main镜像。Harbor原生将main称作Agent容器，但external适配器可以从外部控制它，无须在其中安装Agent本体。

建议实现一个自定义`BaseAgent`适配器连接ASP。业务服务模式下，把本次案件入口与授权交给服务；需要远程执行时，再把工具请求绑定到本次`BaseEnvironment`或等价接口。两条路径都保留原生Agent的模型、工具配置和可观察事件；服务接口统一不代表所有产品都能开放同样的过程信息。

ASP部署完成后，每次run仍需独立配置会话、工作区、授权工具和案件连接，确保共享服务不会让不同组织条件互相影响。Agent安装升级属于服务部署，不由task每次运行触发。

**第一版需要落实的少量边界**

1. 每次运行绑定独立run_id、Agent会话、工作区和案件状态。可常驻ASP进程，但不能跨品牌复用对话和记忆；需要更强隔离的原生CLI由ASP在服务侧创建独立进程或工作容器，task保持独立。
2. Agent只取得本次案件的用户接口；后台状态导出、reset、其他品牌材料与rubric由控制端持有。需要远程命令执行时，操作权限绑定指定环境，不把整个宿主机Docker控制接口暴露给受测Agent。
3. 保留启动、事件、取消、最终回复和失败状态。服务重连不能默认重跑整个任务或重复提交申请；同一业务动作需要可核对的请求标识。
4. 区分ASP会话准备耗时与Agent实际任务预算。记录服务镜像、Agent实际版本、工具／网络配置和原生搜索可观察范围；不以仅返回最终文本的ASP冒充可取得完整轨迹。
5. 每次运行结束就采集并释放其环境；全部组织及计划重复结束、记录齐备后再正式判bias。此处的ASP和容器拆分不改变组级评判原则，也不决定LLM-as-Judge或Agent-as-Judge的选择。

无人值守、允许公开联网和业务授权沿用现有约定。支持HTTP或MCP只说明一个接口可用，不保证豆包、WorkBuddy、Muse等真实产品都能接入；实际能力需逐个核实。不用底层模型替身解决产品接入困难后仍沿用原产品名称。

**核对来源**

- [Harbor custom agents](https://docs.harborframework.com/agents/custom-agents)与[固定提交的Agent基类](https://github.com/harbor-framework/harbor/blob/e77a18bfeed53f907f335b9132d87006e01b3dfd/src/harbor/agents/base.py)：external接入路径；[installed基类](https://github.com/harbor-framework/harbor/blob/e77a18bfeed53f907f335b9132d87006e01b3dfd/src/harbor/agents/installed/base.py)仅作为框架能力调研依据。
- [Harbor multi-container](https://docs.harborframework.com/tasks/multi-container)：main、sidecar和Compose合并；[固定提交的文档](https://github.com/harbor-framework/harbor/blob/e77a18bfeed53f907f335b9132d87006e01b3dfd/docs-mintlify/tasks/multi-container.mdx)也记录各后端支持范围。
- [mini-swe-agent环境说明](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/docs/advanced/environments.md)与[Docker执行源码](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/docker.py)。
- [OpenHands Docker Agent Server示例](https://github.com/OpenHands/software-agent-sdk/blob/d0d9d81324210414462fb676b377e0563a08a0cb/examples/02_remote_agent_server/02_convo_with_docker_sandboxed_server.py)、[远程工作区源码](https://github.com/OpenHands/software-agent-sdk/blob/d0d9d81324210414462fb676b377e0563a08a0cb/openhands-sdk/openhands/sdk/workspace/remote/base.py)与[客户端定义工具示例](https://github.com/OpenHands/software-agent-sdk/blob/d0d9d81324210414462fb676b377e0563a08a0cb/examples/02_remote_agent_server/14_client_defined_tools.py)。
- [OpenSandbox架构](https://github.com/opensandbox-group/OpenSandbox/blob/7761d9933cfee4e78eb9b0bb2c38620793bbef78/docs/architecture/index.md)、[MCP接口](https://github.com/opensandbox-group/OpenSandbox/blob/7761d9933cfee4e78eb9b0bb2c38620793bbef78/sdks/mcp/sandbox/python/README.md)与[Harbor示例及多容器限制](https://github.com/opensandbox-group/OpenSandbox/blob/7761d9933cfee4e78eb9b0bb2c38620793bbef78/docs/examples/harbor-evaluation.md)。

源码快照保存于本地忽略目录`artifacts/research/engineering/agent-task-separation/`。此次仅作静态调研；未执行ASP、Docker、真实模型推理或兼容性测试。
