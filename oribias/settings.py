from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse
import hashlib
import json
import os

from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("config") / "codex_models.json"
ARK_CATALOG = CATALOG.with_name("ark_models.json")


def model_catalog(model):
    catalog = json.loads(CATALOG.read_text())
    if model in {entry["slug"] for entry in catalog["models"]}:
        return catalog
    entry = next((m for m in json.loads(ARK_CATALOG.read_text())["models"] if m["id"] == model), None)
    if entry is None:
        raise ValueError(f"No explicit Codex model catalog entry for {model}")
    # Reuse the documented generic Codex fallback prompt, not GPT-specific prompts.
    descriptor = catalog["models"][0]
    descriptor.update(
        slug=model, display_name=model,
        description="OrgBias Ark compatibility descriptor; not a product-default profile.",
        context_window=entry["context_window"], max_context_window=entry["context_window"],
        supported_reasoning_levels=[{"effort": "medium", "description": "Requested medium; provider-specific interpretation."}],
        supports_reasoning_summary_parameter=False, input_modalities=["text"],
    )
    return {"models": [descriptor]}


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str = field(repr=False)
    model: str
    effort: str
    asp_url: str
    asp_token: str = field(repr=False)
    codex_bin: str
    timeout: int
    context_tokens: int
    max_prompt_tokens: int
    judge_output_tokens: int
    web_search: str
    request_interval_seconds: float = 0.0
    pacing_state: str = ""

    @classmethod
    def load(cls, root: Path = ROOT, *, role="agent"):
        values = {**dotenv_values(root / ".env"), **os.environ}

        if role not in {"agent", "judge"}:
            raise ValueError("Unknown model role")
        # Resolve the judge from the original LLM settings, never from a plan key.
        if role == "judge":
            for suffix in ("BASE_URL", "API_KEY", "MODEL", "EFFORT"):
                if values.get("ORIBIAS_JUDGE_" + suffix):
                    values["ORIBIAS_LLM_" + suffix] = values["ORIBIAS_JUDGE_" + suffix]
            for suffix in ("CONTEXT_TOKENS", "MAX_PROMPT_TOKENS"):
                if values.get("ORIBIAS_JUDGE_" + suffix):
                    values["ORIBIAS_" + suffix] = values["ORIBIAS_JUDGE_" + suffix]
        elif plan := values.get("ORIBIAS_PLAN"):
            if plan not in {"coding", "plan"}:
                raise ValueError("ORIBIAS_PLAN must be coding or plan")
            prefix = "ORIBIAS_ARK_" + plan.upper() + "_"
            base_url = values.get(prefix + "BASE_URL", "").rstrip("/")
            if not base_url:
                raise ValueError(f"Set {prefix}BASE_URL")
            values["ORIBIAS_LLM_BASE_URL"] = base_url + "/v3"
            values["ORIBIAS_LLM_API_KEY"] = values.get(prefix + "API_KEY")
            model = values.get("ORIBIAS_AGENT_MODEL") or values.get("ORIBIAS_ARK_DEFAULT_MODEL", "glm-5.3")
            models = json.loads(ARK_CATALOG.read_text())["models"]
            entry = next((m for m in models if m["id"] == model), None)
            if entry is None:
                raise ValueError(f"Model is not in the pinned Ark plan catalogue: {model}")
            values["ORIBIAS_LLM_MODEL"] = model
            values["ORIBIAS_LLM_EFFORT"] = values.get("ORIBIAS_ARK_EFFORT", "medium")
            values["ORIBIAS_CONTEXT_TOKENS"] = str(entry["context_window"])
            values["ORIBIAS_MAX_PROMPT_TOKENS"] = str(entry["context_window"] - 32768)

        def get(name, default=None):
            value = values.get(name, default)
            if value is None or value == "":
                raise ValueError(f"Set {name} in {root / '.env'}")
            return value

        paced_agent = role == "agent" and bool(values.get("ORIBIAS_PLAN"))
        result = cls(
            base_url=get("ORIBIAS_LLM_BASE_URL").rstrip("/"),
            api_key=get("ORIBIAS_LLM_API_KEY"),
            model=get("ORIBIAS_LLM_MODEL"),
            effort=get("ORIBIAS_LLM_EFFORT", "medium"),
            asp_url=get("ORIBIAS_ASP_URL", "http://127.0.0.1:8765").rstrip("/"),
            asp_token=get("ORIBIAS_ASP_TOKEN"),
            codex_bin=get("ORIBIAS_CODEX_BIN", "codex"),
            timeout=int(values.get("ORIBIAS_ARK_RUN_TIMEOUT", get("ORIBIAS_RUN_TIMEOUT", "300")) if paced_agent else get("ORIBIAS_RUN_TIMEOUT", "300")),
            context_tokens=int(get("ORIBIAS_CONTEXT_TOKENS", "1050000")),
            max_prompt_tokens=int(get("ORIBIAS_MAX_PROMPT_TOKENS", "922000")),
            judge_output_tokens=int(get("ORIBIAS_JUDGE_OUTPUT_TOKENS", "16384")),
            web_search=get("ORIBIAS_WEB_SEARCH", "live"),
            request_interval_seconds=float(values.get("ORIBIAS_ARK_REQUEST_INTERVAL_SECONDS", "0")) if paced_agent else 0.0,
            pacing_state=str(root / "runs" / ".provider-pacing") if paced_agent else "",
        )
        import math
        if not math.isfinite(result.request_interval_seconds) or result.request_interval_seconds < 0:
            raise ValueError("Request interval must be finite and nonnegative")
        asp = urlparse(result.asp_url)
        if asp.scheme != "http" or asp.hostname not in {"127.0.0.1", "localhost"}:
            raise ValueError("The local-debug ASP must bind to loopback HTTP")
        if min(result.timeout, result.context_tokens, result.max_prompt_tokens,
               result.judge_output_tokens) <= 0:
            raise ValueError("Budgets must be positive")
        if result.web_search not in {"live", "disabled"}:
            raise ValueError("ORIBIAS_WEB_SEARCH must be live or disabled")
        return result

    def public(self):
        return {key: value for key, value in vars(self).items()
                if key not in {"api_key", "asp_token"}} | {
                    "codex_catalog_sha256": hashlib.sha256(
                        json.dumps(model_catalog(self.model), sort_keys=True).encode()).hexdigest()
                }

    def fingerprint(self):
        return hashlib.sha256(json.dumps(self.public(), sort_keys=True).encode()).hexdigest()

    def redact(self, text: str):
        for secret in (self.api_key, self.asp_token):
            text = text.replace(secret, "[REDACTED]")
        return text
