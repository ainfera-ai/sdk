"""Ainfera CLI — `ainfera install` and friends.

The CLI is shipped as a packaging extra (``pip install ainfera[cli]``) so
the runtime SDK stays click/yaml-free for library users. Console-script
entry point: ``ainfera = ainfera.cli:cli``.

Today the surface is intentionally tiny — one command, ``install`` —
because the dashboard story is the only flow that needs it. Future
commands (``audit verify``, ``card mint``, etc.) land here alongside.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import click

DEFAULT_API_BASE = "https://api.ainfera.ai"
MANIFEST_FILENAME = "ainfera-agent.yaml"
_SCAN_SKIP_DIRS = {".venv", "venv", "node_modules", ".git", ".tox", "dist", "build", ".ainfera"}


def _resolve_github_handle() -> tuple[str, str]:
    """Return ``(handle, token)`` from the local ``gh`` CLI session.

    Raises a ``click.ClickException`` if ``gh`` is missing or the user
    isn't authenticated — the message points at ``gh auth login`` since
    that's the one-command fix.
    """
    try:
        handle = subprocess.check_output(
            ["gh", "api", "user", "-q", ".login"],
            text=True,
            stderr=subprocess.PIPE,
        ).strip()
        token = subprocess.check_output(
            ["gh", "auth", "token"],
            text=True,
            stderr=subprocess.PIPE,
        ).strip()
    except FileNotFoundError as exc:
        raise click.ClickException(
            "`gh` CLI not found on PATH. Install it from https://cli.github.com "
            "and run `gh auth login` first."
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if isinstance(exc.stderr, str) else str(exc)
        raise click.ClickException(
            "Could not resolve a GitHub identity via `gh`. Run `gh auth login` "
            f"first.\nUnderlying error: {stderr}"
        ) from exc
    if not handle or not token:
        raise click.ClickException(
            "`gh` returned an empty handle or token. Run `gh auth status` to debug."
        )
    return handle, token


def _discover_manifests(root: Path) -> list[Path]:
    """Find every ``ainfera-agent.yaml`` under ``root`` recursively.

    Walks the tree manually so we can skip noisy directories
    (.venv, node_modules, .git) without paying their walk cost.
    """
    found: list[Path] = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            for entry in current.iterdir():
                if entry.is_dir():
                    if entry.name in _SCAN_SKIP_DIRS:
                        continue
                    stack.append(entry)
                elif entry.is_file() and entry.name == MANIFEST_FILENAME:
                    found.append(entry)
        except PermissionError:
            continue
    found.sort()
    return found


def _load_manifest(path: Path) -> dict[str, Any]:
    """Parse a manifest YAML into the dict shape the install endpoint expects.

    Lazily imports yaml so `import ainfera.cli` stays cheap for users who
    only need the library surface.
    """
    try:
        import yaml
    except ImportError as exc:
        raise click.ClickException(
            "PyYAML is required for `ainfera install`. "
            "Install with `pip install 'ainfera[cli]'`."
        ) from exc

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise click.ClickException(f"{path} did not parse to a YAML mapping.")
    if "handle" not in raw:
        raise click.ClickException(f"{path} is missing required field 'handle'.")
    if "framework" not in raw:
        raise click.ClickException(f"{path} is missing required field 'framework'.")

    payload: dict[str, Any] = {
        "handle": str(raw["handle"]).lower(),
        "framework": str(raw["framework"]),
    }
    for optional in ("persona", "wallet_address"):
        if raw.get(optional) is not None:
            payload[optional] = raw[optional]
    for cap in ("per_call_cap_usd", "daily_cap_usd"):
        if raw.get(cap) is not None:
            payload[cap] = str(raw[cap])
    if isinstance(raw.get("metadata"), dict):
        payload["metadata"] = raw["metadata"]
    return payload


def _write_keys(root: Path, agents: list[dict[str, Any]]) -> Path:
    """Persist per-agent api keys to ``.ainfera/keys.json`` (gitignored).

    The install endpoint may return ``api_key=null`` for agents seen on
    a re-run (the raw key was minted once, only the hash is stored).
    We preserve any existing local key for those handles so the file
    stays usable across invocations.
    """
    keys_dir = root / ".ainfera"
    keys_dir.mkdir(exist_ok=True)
    keys_file = keys_dir / "keys.json"

    existing: dict[str, str] = {}
    if keys_file.exists():
        try:
            loaded = json.loads(keys_file.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = {str(k): str(v) for k, v in loaded.items() if isinstance(v, str)}
        except (OSError, ValueError):
            existing = {}

    for a in agents:
        key = a.get("api_key")
        handle = a.get("handle")
        if isinstance(handle, str) and isinstance(key, str):
            existing[handle] = key

    keys_file.write_text(json.dumps(existing, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return keys_file


@click.group()
@click.version_option(package_name="ainfera", prog_name="ainfera")
def cli() -> None:
    """Ainfera command-line tools.

    `ainfera install` registers agent manifests under your GitHub handle
    so they appear at app.ainfera.ai/<handle>.
    """


@cli.command("install")
@click.option(
    "--dir",
    "directory",
    default=".",
    show_default=True,
    type=click.Path(file_okay=False, dir_okay=True, exists=True, resolve_path=True),
    help="Root directory to scan for ainfera-agent.yaml manifests.",
)
@click.option(
    "--api-base",
    default=DEFAULT_API_BASE,
    show_default=True,
    metavar="URL",
    help="Override the Ainfera API base URL (useful for local dev).",
)
@click.option(
    "--token",
    default=None,
    metavar="TOKEN",
    help=(
        "Override the GitHub identity proof. Defaults to `gh auth token`. "
        "Useful in CI where gh is not present."
    ),
)
@click.option(
    "--handle",
    default=None,
    metavar="LOGIN",
    help=(
        "Override the GitHub handle. Required with --token if gh is "
        "unavailable; otherwise defaults to `gh api user -q .login`."
    ),
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Discover and parse manifests but skip the network call.",
)
def install(
    directory: str,
    api_base: str,
    token: str | None,
    handle: str | None,
    dry_run: bool,
) -> None:
    """Install agent(s) from local manifest(s) into your Ainfera fleet."""
    import httpx

    root = Path(directory).resolve()

    manifests = _discover_manifests(root)
    if not manifests:
        raise click.ClickException(f"No {MANIFEST_FILENAME} found under {root}.")

    click.echo(f"Discovered {len(manifests)} manifest(s):")
    for m in manifests:
        click.echo(f"  - {m.relative_to(root)}")

    agents_payload = [_load_manifest(m) for m in manifests]

    if handle is None or token is None:
        resolved_handle, resolved_token = _resolve_github_handle()
        handle = handle or resolved_handle
        token = token or resolved_token

    if dry_run:
        click.echo("\n--dry-run · skipping network call. Payload:")
        click.echo(
            json.dumps(
                {
                    "github_handle": handle,
                    "manifest_url": f"file://{root}",
                    "agents": agents_payload,
                },
                indent=2,
            )
        )
        return

    try:
        r = httpx.post(
            f"{api_base.rstrip('/')}/v1/agents/install-from-local",
            json={
                "github_handle": handle,
                "github_token_proof": token,
                "manifest_url": f"file://{root}",
                "agents": agents_payload,
            },
            timeout=30.0,
        )
    except httpx.HTTPError as exc:
        raise click.ClickException(f"Network error contacting {api_base}: {exc}") from exc

    if r.status_code >= 400:
        try:
            detail = r.json().get("detail", r.text)
        except ValueError:
            detail = r.text
        raise click.ClickException(f"Install failed (HTTP {r.status_code}): {detail}")

    result = r.json()
    agents = result.get("agents", [])
    created = sum(1 for a in agents if a.get("created"))
    click.echo(
        f"\nInstalled {len(agents)} agent(s) under github:{result.get('github_handle', handle)} "
        f"({created} new, {len(agents) - created} updated)"
    )
    for a in agents:
        flag = "new" if a.get("created") else "refreshed"
        click.echo(f"  - {a['handle']} ({flag}): {a['canonical_uri']}")

    keys_file = _write_keys(root, agents)
    rel_keys = keys_file.relative_to(root) if keys_file.is_relative_to(root) else keys_file
    minted = sum(1 for a in agents if a.get("api_key"))
    if minted:
        click.echo(f"\nKeys saved to {rel_keys} ({minted} key(s) written).")
    else:
        click.echo(
            f"\nNo new api_keys returned (tenant key already on file in {rel_keys})."
        )

    dashboard_url = result.get("dashboard_url") or f"https://app.ainfera.ai/{handle}"
    click.echo(f"\nDashboard: {dashboard_url}")


def main() -> None:
    """Entry point for the ``ainfera`` console script."""
    cli(prog_name="ainfera", standalone_mode=True)


if __name__ == "__main__":
    sys.exit(cli(standalone_mode=True) or 0)
