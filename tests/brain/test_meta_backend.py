from ghost_poker.brain import get_meta_backend_spec, validate_meta_backend_config
from ghost_poker.utils.runtime_config import MetaBackendConfig, MetaBackendKind


def test_openai_compatible_backend_requires_base_url_and_api_key() -> None:
    issues = validate_meta_backend_config(
        MetaBackendConfig(
            kind=MetaBackendKind.OPENAI_COMPATIBLE,
            model="gpt-poker-1",
        )
    )

    assert "meta backend distant sans cle API" in issues
    assert "backend openai_compatible sans base URL" in issues


def test_local_backend_spec_reports_local_execution() -> None:
    spec = get_meta_backend_spec(MetaBackendKind.LOCAL)

    assert spec.supports_local_execution is True
    assert spec.supports_remote_api is False
