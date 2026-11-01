# OrgBias

**Open research on how organizational identity affects AI agents acting for users.**

We invite researchers to reproduce these experiments, challenge their assumptions, contribute better tasks, and build stronger evidence about organizational bias in personal agents. Positive findings, small effects, and well-supported null results are all valuable. The aim is to understand when organization names change an agent's judgments and actions, whether those changes are justified, and what they mean for the user.

This repository shares **three exploratory tasks, an agent evaluation runtime, and a public record of our pilot experiments**. It is a research starting point, not a validated leaderboard or a claim that any named organization or model is systematically biased.

[Read the results](results/README.md) · [Browse the tasks](#tasks) · [Research questions and related work](docs/research-status.md) · [Contribute](CONTRIBUTING.md)

## What we observed

The public pilot archive contains **18 groups, 138 declared conditions and 101 final replies** from October 27–29, 2026. Of those replies, **94 have a validated `no_observed_signal` classification and 7 have no valid Judge result**. There are also 33 failed and 4 cancelled conditions. These are archive counts across different versions and configurations, not independent cases or an estimate of bias prevalence.

- **Laptop disputes:** GPT, Doubao Pro and Doubao Lite each requested technical review in all seven conditions of task001 v0.8. Wording varied; the principal action did not.
- **Hospital affiliation:** replacing the signature was accompanied by different follow-up routes and management positions in GLM and Kimi runs. Each condition was sampled once per model. These differences are candidates for replication, not established bias or clinical harm. Kimi's five replies have no valid Judge result.
- **Laptop recommendations:** GPT selected the same first choice and backup in all 14 brand/order conditions. Doubao Pro selected the same first choice in its 11 available replies, with one backup change. Three Pro replies are missing.

`no_observed_signal` means that the fixed Judge found no sufficient bias evidence **in the supplied final text**. It does not establish neutrality, validate the agent's medical advice, or rule out effects on information gathering and actions. Our current data do not demonstrate a stable organizational-bias effect.

See the [evidence and limitations](docs/research-status.md), [group-by-group archive](results/README.md), and [machine-readable catalog](results/catalog.json). The archive includes replies, rendered prompts, observed task-tool calls and returns, saved outcomes, original Judge inputs/results, and task snapshots. Engineering runs and authored evaluator controls are explicitly separated from pilot observations. Missing and failed results remain visible.

## Tasks

| Task | Controlled identity | What the agent does | Current version |
|---|---|---|---|
| [001: Laptop-screen dispute](tasks/001/README.md) | Six manufacturers plus an undisclosed control | Read case records, obtain an inspection report, assess the dispute, request a review | v0.8; earlier versions preserved |
| [002: Hospital affiliation](tasks/002/README.md) | Four hospitals plus an undisclosed control | Review clinical records, save a care memo, request one next step | v0.2; earlier GPT data used v0.1 |
| [003: Laptop recommendation](tasks/003/README.md) | Six brands rotated over fixed offers, with order and anonymous controls | Retrieve offers and measurements, rank options, save a recommendation | v0.1; 14 conditions |

All task inputs are English and text-only. Cases, clinical records, offers, measurements and service outcomes are **synthetic research fixtures**. Named organizations are identity treatments, not subjects of real complaints or measurements. The `private/` directories contain simulator-held fixtures exposed through tools; they do not contain private patient or customer data. Tasks perform no real purchases, payments, appointments or clinical treatment.

## Evaluation design

Agents run through an independent **ASP (agent as service)**. The current adapter wraps the locally installed Codex CLI on the host; Harbor runs isolated task containers. The task image does not install the agent. Each run receives fresh state and may voluntarily read files, use task tools and, when configured, search the web. Agents are instructed to finish without follow-up questions.

After all planned conditions in a group are terminal, a **single Judge call** compares the task prompts and all final replies, returning categorical labels with quotations. Trajectories and trusted state are audited separately. There are no automatic experiment retries, account fallbacks or failed-Judge repair calls.

The released experiments use one configured Codex harness with different provider-reported model identifiers. They are **not** a comparison of untouched commercial personal-agent products. `gpt-6.1-sol` / medium is the identifier recorded by the local provider for the reference agent and fixed Judge; it is not a public API availability guarantee. Requested reasoning effort, provider budgets and live retrieval are not necessarily equivalent across models. [Runtime and provenance](docs/local-runtime.md).

## Explore without model access

All released evidence can be read directly on GitHub. To check its integrity locally, with Python 3.12 and [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/zhangdw156/OrgBias.git
cd OrgBias
uv sync --locked
uv run python scripts/verify_results.py
```

This checks the file inventory, hashes, group coverage, saved outcomes, and Judge schemas/identities/quotations. It makes **no model calls** and requires neither Docker nor credentials. Passing these checks does not establish the substantive correctness of Judge labels.

## Run a new experiment

Install the local Codex CLI and start Docker. Copy `.env.example` to `.env` and configure your own compatible model endpoints, credentials and local ASP token. The example preserves the original local setup; it does not provision the service on port 4141. Models need an explicit matching [compatibility descriptor](oribias/config/README.md).

```bash
cp .env.example .env
# Edit .env with your own endpoint settings before running.
uv run python -m oribias run --task 001
```

This starts the host ASP when needed, runs all seven task001 conditions once and invokes the configured Judge once. New outputs go to ignored `runs/`; existing public results are not overwritten. Use `--task 002` or `--task 003` for the other tasks. See [configuration and experimental limits](docs/local-runtime.md) before a larger study. The earlier 15-model sweep was interrupted; its old job declarations are historical records, not a ready-made continuation plan.

## Help move this research forward

We especially welcome:

- Independent cases and repeated, controlled organization substitutions, including credible null results.
- Human calibration of categorical judgments and objective checks of consequential actions.
- Experiments separating identity effects from evidence, presentation order, sampling variation, search results and harness behavior.
- Studies of how identity changes verification, correction, user costs or memory, with clear comparisons to prior work.
- Interventions that reduce unjustified differences while preserving task quality and useful personalization.

Use [Issues](https://github.com/zhangdw156/OrgBias/issues) for research questions, replications and corrections, or submit a pull request following [CONTRIBUTING.md](CONTRIBUTING.md). Existing work already studies affiliation, source and commercial preferences; we make no claim to be the first. [Related work and research boundaries](docs/research-status.md).

## License and citation

Original project contributions are available under [Apache-2.0](LICENSE). Third-party attribution and the scope of the released model-output records are described in [NOTICE](NOTICE). Use [CITATION.cff](CITATION.cff) to cite the repository, and identify the task version, group IDs and source commit when using experimental results. This repository is not a peer-reviewed publication.

For dated protocols, earlier design decisions and engineering reports, see the [document index](docs/README.md). The public release was prepared on November 1, 2026; no new model inference was performed for publication.
