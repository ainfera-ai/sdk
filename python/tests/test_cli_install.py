"""Tests for ``ainfera install`` — manifest discovery + identity + HTTP.

The network call is respx-mocked; the gh CLI lookup is monkey-patched
via ``_resolve_github_handle`` overrides so the test suite stays
offline and deterministic.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import respx
from ainfera import cli as cli_mod
from click.testing import CliRunner
from httpx import Response


def _write_manifest(dir_: Path, **fields: object) -> Path:
    """Write a minimal YAML manifest into ``dir_``."""
    dir_.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}: {v}" for k, v in fields.items()]
    path = dir_ / "ainfera-agent.yaml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def fake_identity(monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
    handle, token = "test-user", "ghs_fake_token_for_tests"
    monkeypatch.setattr(cli_mod, "_resolve_github_handle", lambda: (handle, token))
    return handle, token


def test_discover_finds_nested_manifests(tmp_path: Path) -> None:
    _write_manifest(tmp_path / "agents" / "alpha", handle="alpha", framework="x")
    _write_manifest(tmp_path / "agents" / "beta", handle="beta", framework="x")
    (tmp_path / ".venv" / "bad").mkdir(parents=True)
    _write_manifest(tmp_path / ".venv" / "bad", handle="poison", framework="x")

    found = cli_mod._discover_manifests(tmp_path)
    found_names = {p.parent.name for p in found}
    assert found_names == {"alpha", "beta"}, "should ignore .venv tree"


def test_load_manifest_normalises_handle_and_caps(tmp_path: Path) -> None:
    path = _write_manifest(
        tmp_path,
        handle="VARDA",
        framework="nemoclaw+openclaw",
        per_call_cap_usd=1.5,
        daily_cap_usd=20.0,
    )
    parsed = cli_mod._load_manifest(path)
    assert parsed["handle"] == "varda"
    assert parsed["framework"] == "nemoclaw+openclaw"
    assert parsed["per_call_cap_usd"] == "1.5"
    assert parsed["daily_cap_usd"] == "20.0"


def test_load_manifest_rejects_missing_required(tmp_path: Path) -> None:
    path = _write_manifest(tmp_path, framework="x")  # no handle
    import click

    with pytest.raises(click.ClickException, match="handle"):
        cli_mod._load_manifest(path)


def test_install_dry_run_prints_payload_without_network(
    tmp_path: Path, fake_identity: tuple[str, str]
) -> None:
    _write_manifest(
        tmp_path / "varda",
        handle="varda",
        framework="nemoclaw",
        per_call_cap_usd=1.5,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli_mod.cli,
        ["install", "--dir", str(tmp_path), "--dry-run"],
    )
    assert result.exit_code == 0, result.output
    assert "Discovered 1 manifest" in result.output
    assert '"github_handle": "test-user"' in result.output
    assert '"handle": "varda"' in result.output


def test_install_posts_and_writes_keys_file(
    tmp_path: Path, fake_identity: tuple[str, str]
) -> None:
    _write_manifest(tmp_path / "varda", handle="varda", framework="nemoclaw")
    _write_manifest(tmp_path / "namo", handle="namo", framework="langgraph")

    api_base = "https://api.example.test"
    with respx.mock(base_url=api_base, assert_all_called=True) as router:
        router.post("/v1/agents/install-from-local").mock(
            return_value=Response(
                201,
                json={
                    "user_id": "u-1",
                    "tenant_id": "t-1",
                    "github_handle": "test-user",
                    "agents": [
                        {
                            "handle": "varda",
                            "canonical_uri": "ainfera.ai/test-user/varda",
                            "did_web": "did:web:ainfera.ai:test-user:varda",
                            "agent_id": "a-1",
                            "api_key": "ak_live_xxx",
                            "created": True,
                        },
                        {
                            "handle": "namo",
                            "canonical_uri": "ainfera.ai/test-user/namo",
                            "did_web": "did:web:ainfera.ai:test-user:namo",
                            "agent_id": "a-2",
                            "api_key": "ak_live_xxx",
                            "created": True,
                        },
                    ],
                    "dashboard_url": "https://app.example.test/test-user",
                },
            )
        )

        runner = CliRunner()
        result = runner.invoke(
            cli_mod.cli,
            ["install", "--dir", str(tmp_path), "--api-base", api_base],
        )

    assert result.exit_code == 0, result.output
    assert "Installed 2 agent(s)" in result.output
    assert "Dashboard: https://app.example.test/test-user" in result.output

    keys_file = tmp_path / ".ainfera" / "keys.json"
    assert keys_file.exists()
    saved = json.loads(keys_file.read_text(encoding="utf-8"))
    assert saved == {"varda": "ak_live_xxx", "namo": "ak_live_xxx"}


def test_install_preserves_existing_keys_on_rerun(
    tmp_path: Path, fake_identity: tuple[str, str]
) -> None:
    """Re-install returns api_key=null for already-known agents — the
    CLI must not wipe the previously persisted key.
    """
    _write_manifest(tmp_path / "varda", handle="varda", framework="nemoclaw")

    keys_dir = tmp_path / ".ainfera"
    keys_dir.mkdir()
    (keys_dir / "keys.json").write_text(
        json.dumps({"varda": "ak_live_previously_minted"}, indent=2),
        encoding="utf-8",
    )

    api_base = "https://api.example.test"
    with respx.mock(base_url=api_base, assert_all_called=True) as router:
        router.post("/v1/agents/install-from-local").mock(
            return_value=Response(
                201,
                json={
                    "user_id": "u-1",
                    "tenant_id": "t-1",
                    "github_handle": "test-user",
                    "agents": [
                        {
                            "handle": "varda",
                            "canonical_uri": "ainfera.ai/test-user/varda",
                            "did_web": "did:web:ainfera.ai:test-user:varda",
                            "agent_id": "a-1",
                            "api_key": None,
                            "created": False,
                        }
                    ],
                    "dashboard_url": "https://app.example.test/test-user",
                },
            )
        )

        runner = CliRunner()
        result = runner.invoke(
            cli_mod.cli,
            ["install", "--dir", str(tmp_path), "--api-base", api_base],
        )

    assert result.exit_code == 0, result.output
    assert "refreshed" in result.output
    saved = json.loads((keys_dir / "keys.json").read_text(encoding="utf-8"))
    assert saved == {"varda": "ak_live_previously_minted"}


def test_install_aborts_on_empty_dir(
    tmp_path: Path, fake_identity: tuple[str, str]
) -> None:
    runner = CliRunner()
    result = runner.invoke(cli_mod.cli, ["install", "--dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "No ainfera-agent.yaml" in result.output


def test_install_surfaces_http_error(
    tmp_path: Path, fake_identity: tuple[str, str]
) -> None:
    _write_manifest(tmp_path / "varda", handle="varda", framework="nemoclaw")
    api_base = "https://api.example.test"

    with respx.mock(base_url=api_base, assert_all_called=True) as router:
        router.post("/v1/agents/install-from-local").mock(
            return_value=Response(403, json={"detail": "owner mismatch"})
        )
        runner = CliRunner()
        result = runner.invoke(
            cli_mod.cli,
            ["install", "--dir", str(tmp_path), "--api-base", api_base],
        )

    assert result.exit_code != 0
    assert "owner mismatch" in result.output
