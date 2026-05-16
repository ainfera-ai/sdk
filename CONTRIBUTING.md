# Contributing

Thanks for your interest in contributing to Ainfera.

## Ground rules

- **One topic per PR.** Keep diffs focused — bug fix or feature, not both.
- **Match the existing style.** Don't reformat unrelated code in the same PR.
- **Tests before review.** New behavior should be covered; bug fixes should add a regression test.
- **Honest commit messages.** Subject in imperative mood (`fix: handle empty audit chain`, not `Fixed bug`).

## Workflow

1. Open an issue first if the change is larger than a small fix. We may have context that saves you time.
2. Fork → branch (`feat/short-slug` or `fix/short-slug`) → push → PR against `main`.
3. CI must be green before review. Pre-commit checks vary per repo — see `.pre-commit-config.yaml` or the repo README.
4. PRs are squash-merged. Your PR title becomes the squash commit subject — make it good.

## Code of Conduct

Participation requires adherence to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Vulnerabilities go via the process in [SECURITY.md](SECURITY.md), not the public issue tracker.

## License

By contributing you agree your contributions are licensed under the same license as this repository (see `LICENSE`).
