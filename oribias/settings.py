from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse
import hashlib
import json
import os

from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("config") / "codex_models.json"


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

    @classmethod
    def load(cls, root: Path = ROOT):
        values = {**dotenv_values(root / ".env"), **os.environ}

        def get(name, default=None):
            value = values.get(name, default)
            if value is None or value == "":
                raise ValueError(f"Set {name} in {root / '.env'}")
            return value

        result = cls(
            base_url=get("ORIBIAS_LLM_BASE_URL").rstrip("/"),
            api_key=get("ORIBIAS_LLM_API_KEY"),
            model=get("ORIBIAS_LLM_MODEL"),
            effort=get("ORIBIAS_LLM_EFFORT", "medium"),
            asp_url=get("ORIBIAS_ASP_URL", "http://127.0.0.1:8765").rstrip("/"),
            asp_token=get("ORIBIAS_ASP_TOKEN"),
            codex_bin=get("ORIBIAS_CODEX_BIN", "codex"),
            timeout=int(get("ORIBIAS_RUN_TIMEOUT", "300")),
            context_tokens=int(get("ORIBIAS_CONTEXT_TOKENS", "1050000")),
            max_prompt_tokens=int(get("ORIBIAS_MAX_PROMPT_TOKENS", "922000")),
            judge_output_tokens=int(get("ORIBIAS_JUDGE_OUTPUT_TOKENS", "16384")),
            web_search=get("ORIBIAS_WEB_SEARCH", "live"),
        )
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
                    "codex_catalog_sha256": hashlib.sha256(CATALOG.read_bytes()).hexdigest()
                }

    def fingerprint(self):
        return hashlib.sha256(json.dumps(self.public(), sort_keys=True).encode()).hexdigest()

    def redact(self, text: str):
        for secret in (self.api_key, self.asp_token):
            text = text.replace(secret, "[REDACTED]")
        return text
