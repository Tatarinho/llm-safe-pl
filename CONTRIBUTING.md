# Contributing to llm-safe-pl

Thanks for your interest. This document describes what kinds of contributions are welcome right now, and how to get a change merged.

## Status: pre-1.0

The library is under active design. The v0.1 scope and the public API surface (`Shield`, `Match`, `Mapping`, `AnonymizeResult`, `PIIType`) are **locked** — see [README.md](README.md). Until v1.0, scope discipline matters more than breadth of contributions.

### What's welcome right now

- Bug fixes (with a test that reproduces the bug).
- Test coverage improvements.
- Documentation fixes (typos, clarity, examples).
- Fixes to the CI workflow, packaging, or dev tooling.

### What to open an issue for first

- New detectors, validators, or recognizers.
- Changes to the public API or to anything exported from `llm_safe_pl.__init__`.
- New optional-dependency groups.
- Performance work (please include a benchmark in the issue).
- Anything listed as "Deferred to v0.2+" in the README — those are tracked, not forgotten.

Please do not open PRs for locked-scope changes without an issue discussion first. They will be closed with a pointer here.

## Development setup

```bash
git clone https://github.com/<your-fork>/llm-safe-pl.git
cd llm-safe-pl
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # macOS / Linux
pip install -e ".[dev]"
```

Python 3.10 or newer is required.

## Workflow

1. Create a branch from `main`: `git checkout -b short-descriptive-name`.
2. Make your change. Keep commits small and focused.
3. Run the four CI gates locally — the same ones CI will run:

   ```bash
   ruff check .
   ruff format --check .
   mypy
   pytest
   ```

   All four must pass. The coverage gate is 80%; dropping below that fails the build.
4. Push the branch and open a pull request against `main`.
5. CI runs on every push. Please address failures before asking for review.

## Commit and PR style

- Write commit messages in the imperative mood ("Add PESEL validator", not "Added").
- One logical change per commit where practical.
- Keep PR descriptions short and focused on the *why*, not a diff retelling.
- Do not include attribution trailers (`Co-Authored-By`, AI-assistant credits, etc.); if you used tooling to help write code, that is your business, not the project's history.

## Licensing

By submitting a contribution, you agree that it will be distributed under the project's MIT license (see [LICENSE](LICENSE)). No CLA is required.

## Questions

Open a GitHub issue with the `question` label. Please search existing issues first.
