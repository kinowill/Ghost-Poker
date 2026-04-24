"""Description minimale des backends meta supportes."""

from __future__ import annotations

from dataclasses import dataclass

from ghost_poker.utils.runtime_config import MetaBackendConfig, MetaBackendKind


@dataclass(frozen=True)
class MetaBackendSpec:
    kind: MetaBackendKind
    display_name: str
    requires_api_key: bool
    supports_local_execution: bool
    supports_remote_api: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "display_name": self.display_name,
            "requires_api_key": self.requires_api_key,
            "supports_local_execution": self.supports_local_execution,
            "supports_remote_api": self.supports_remote_api,
        }


_META_BACKEND_SPECS: dict[MetaBackendKind, MetaBackendSpec] = {
    MetaBackendKind.DISABLED: MetaBackendSpec(
        kind=MetaBackendKind.DISABLED,
        display_name="Disabled",
        requires_api_key=False,
        supports_local_execution=False,
        supports_remote_api=False,
    ),
    MetaBackendKind.MISTRAL: MetaBackendSpec(
        kind=MetaBackendKind.MISTRAL,
        display_name="Mistral API",
        requires_api_key=True,
        supports_local_execution=False,
        supports_remote_api=True,
    ),
    MetaBackendKind.GROQ: MetaBackendSpec(
        kind=MetaBackendKind.GROQ,
        display_name="Groq API",
        requires_api_key=True,
        supports_local_execution=False,
        supports_remote_api=True,
    ),
    MetaBackendKind.OPENAI_COMPATIBLE: MetaBackendSpec(
        kind=MetaBackendKind.OPENAI_COMPATIBLE,
        display_name="OpenAI-compatible API",
        requires_api_key=True,
        supports_local_execution=False,
        supports_remote_api=True,
    ),
    MetaBackendKind.OLLAMA: MetaBackendSpec(
        kind=MetaBackendKind.OLLAMA,
        display_name="Ollama local server",
        requires_api_key=False,
        supports_local_execution=True,
        supports_remote_api=False,
    ),
    MetaBackendKind.LOCAL: MetaBackendSpec(
        kind=MetaBackendKind.LOCAL,
        display_name="Local model",
        requires_api_key=False,
        supports_local_execution=True,
        supports_remote_api=False,
    ),
}


def get_meta_backend_spec(kind: MetaBackendKind) -> MetaBackendSpec:
    return _META_BACKEND_SPECS[kind]


def validate_meta_backend_config(config: MetaBackendConfig) -> list[str]:
    spec = get_meta_backend_spec(config.kind)
    issues: list[str] = []

    if config.is_enabled and not config.model:
        issues.append("meta backend active mais aucun modele configure")

    if spec.requires_api_key and not config.api_key:
        issues.append("meta backend distant sans cle API")

    if config.kind is MetaBackendKind.OPENAI_COMPATIBLE and not config.base_url:
        issues.append("backend openai_compatible sans base URL")

    if config.kind is MetaBackendKind.OLLAMA and not config.base_url:
        issues.append("backend ollama sans base URL")

    return issues
