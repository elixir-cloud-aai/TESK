# Development

This repository holds the Helm chart of TESK (`charts/tesk/`), example tasks
(`examples/`) and the documentation of TESK, which covers
[tesk-api](https://github.com/elixir-cloud-aai/tesk-api) and
[tesk-core](https://github.com/elixir-cloud-aai/tesk-core) too. This page
describes the development setup, the checks and the documentation.

Development needs [uv](https://docs.astral.sh/uv/) (which installs Python
3.13 if needed) and, for the chart, [Helm](https://helm.sh/) 3. To set up a
development environment with the versions of the lock (`uv.lock`), as CI
does, and run the checks that CI runs:

```bash
uv sync --locked --group dev --group docs  # the tools, in `.venv`
source .venv/bin/activate  # or `activate.fish` etc.
pre-commit install  # run the checks on every commit
pre-commit run --all-files  # whitespace, YAML/JSON, ruff, mypy, actionlint
pre-commit run --all-files --hook-stage manual gitleaks-all  # secrets
pytest  # the tests of the docs hooks
helm lint charts/tesk --strict
mkdocs build --strict  # the docs, as CI and Read the Docs build them
```

The checks are configured in
[`.pre-commit-config.yaml`](https://github.com/elixir-cloud-aai/TESK/blob/dev/.pre-commit-config.yaml)
and
[`pyproject.toml`](https://github.com/elixir-cloud-aai/TESK/blob/dev/pyproject.toml).

## Continuous integration

The workflow `CI` (`.github/workflows/ci.yml`) runs on every pull request to
`dev` and every push to `dev`:

- **PR title:** the title follows [Conventional
  Commits](https://www.conventionalcommits.org/) (squash merges use it as
  the commit message).
- **Lint:** the pre-commit hooks above.
- **Test:** the tests in `tests/`, with coverage.
- **Chart:** `helm lint --strict` and `helm template` of the chart.
- **Chart install:** installs the chart with its default values on a
  [kind](https://kind.sigs.k8s.io/) cluster and checks that
  `GET /ga4gh/tes/v1/service-info` answers.
- **Docs:** builds the documentation strictly (`mkdocs build --strict`).
- **CI passed:** the only required check; it fails if any of the other jobs
  failed, or was skipped where it must run.

Nothing is published from `CI`.

## Documentation

The documentation is built with [MkDocs](https://www.mkdocs.org/) and the
[Material](https://squidfunk.github.io/mkdocs-material/) theme
([`mkdocs.yml`](https://github.com/elixir-cloud-aai/TESK/blob/dev/mkdocs.yml)),
from the Markdown pages in `docs/`, and published on [Read the
Docs](https://tesk.readthedocs.io/)
([`.readthedocs.yaml`](https://github.com/elixir-cloud-aai/TESK/blob/dev/.readthedocs.yaml)).
Both CI and Read the Docs build it strictly, from the lock: warnings, e.g.,
of broken links, fail the build. To preview it while editing:

```bash
mkdocs serve
```

Pages that were moved or renamed get a redirect from their old URL (plugin
`redirects` in `mkdocs.yml`), so that links to them keep working.

### Docs of tesk-api and tesk-core

The site has a section each for tesk-api and tesk-core, whose docs are kept
in their own repositories, next to their code, in `docs/`. Those repositories
build their docs strictly in their own CI and publish nothing themselves;
this site pulls them in at build time:

- [`docs-sources.yml`](https://github.com/elixir-cloud-aai/TESK/blob/dev/docs-sources.yml)
  lists each repository with the commit to pull (`ref`, a full commit SHA).
- The hooks in `docs/hooks.py` download that commit from GitHub, take its
  `docs/` and add its pages to the site under `tesk-api/` and `tesk-core/`,
  as the nav sections that `external:tesk-api` and `external:tesk-core` mark
  in `mkdocs.yml`. The pages and their order come from the `nav` of the
  repository's own `mkdocs.yml`; "Edit" links point to the page in its
  repository. A source without a `ref` gets a placeholder page.

The commits are pinned, so that a build of this site is reproducible and a
change in another repository can't break it unnoticed. To publish newer docs
of tesk-api or tesk-core, update their `ref` in `docs-sources.yml` in a pull
request: CI then builds the site with them.

We chose this over the [multirepo
plugin](https://github.com/jdoiro3/mkdocs-multirepo-plugin), which imports
the docs of other repositories by branch or tag: a branch moves (the site
would change, or break, without a change in this repository), and tags of
the other repositories exist only for releases. The hook needs no extra
dependency and no `git`, and fails the build on any problem.

The pulled pages are built with this site's `mkdocs.yml`, so in tesk-api and
tesk-core:

- Use only the Markdown extensions and plugins of this site's `mkdocs.yml`
  (their own `mkdocs.yml` should use the same).
- Link only to files in their `docs/` (relative links), or with absolute
  URLs; their strict build catches links outside it.
- Keep a `nav` in their `mkdocs.yml`, with their `index.md` first.
- Keep no Python files in `docs/` that are meant as pages (`*.py` files,
  e.g., hooks, are not pulled).
