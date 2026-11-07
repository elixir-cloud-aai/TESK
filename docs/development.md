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
pytest  # the tests of the docs hooks and, with helm, of the chart
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
- **Test:** the tests in `tests/` except the chart tests, with coverage.
- **Chart:** `helm lint --strict` and `helm template` of the chart, and the
  chart tests (`tests/test_chart.py`), which render the chart with
  `helm template` for the default values and the main options (ingress,
  OpenShift route, storage backends, FTP, authentication, service info) and
  check the rendered objects, with the pinned Helm version. They fail here
  if Helm is missing (`REQUIRE_HELM`).

  The chart tests also check that the names of the objects derive from the
  release name (two releases render no common names, apart from the fixed
  ones), that references between the objects follow them, and that keys of
  earlier versions of the chart fail with their replacements.
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
  repository. A source without a `ref` gets a placeholder page. The pages
  are served at `https://tesk.readthedocs.io/en/latest/tesk-api/` and
  `.../tesk-core/`.

The commits are pinned, so that a build of this site is reproducible and a
change in another repository can't break it unnoticed. To publish newer docs
of tesk-api or tesk-core, update their `ref` in `docs-sources.yml` in a pull
request: CI then builds the site with them.

We chose this over the [multirepo
plugin](https://github.com/jdoiro3/mkdocs-multirepo-plugin), which imports
the docs of other repositories by branch or tag: a branch moves (the site
would change, or break, without a change in this repository), and tags of
the other repositories exist only for releases. The hook needs no `git`,
and no dependency beyond MkDocs and the packages it uses itself (PyYAML,
pathspec), and fails the build on any problem. It limits the
size of the compressed tarball, and the number and total size of the files
it extracts (`MAX_ARCHIVE_BYTES`, `MAX_MEMBERS` and `MAX_EXTRACTED_BYTES` in
`docs/hooks.py`); the content of a pinned commit is otherwise trusted, so
review the docs of the other repository before pinning a new commit.

The pulled pages are built with this site's `mkdocs.yml`, so in tesk-api and
tesk-core:

- Use only the Markdown extensions and plugins of this site's `mkdocs.yml`
  (their own `mkdocs.yml` should use the same).
- Link only to files in their `docs/` (relative links), or with absolute
  URLs; their strict build catches links outside it.
- Keep a `nav` in their `mkdocs.yml`, with their `index.md` first.
- Keep no Python files in `docs/` that are meant as pages (`*.py` files,
  e.g., hooks, are not pulled).
- List files in `docs/` that aren't part of the site (e.g., the
  `requirements.txt` of their Read the Docs build) in `exclude_docs` of
  their `mkdocs.yml`. The hook applies their `exclude_docs`, `draft_docs`
  and `not_in_nav` (patterns relative to their `docs/`; plain strings, not
  `!ENV`) and MkDocs' default exclusions (hidden files and a top-level
  `templates/`), as MkDocs does in their own site; settings from `INHERIT`
  are not read.

## Releases

TESK's releases are releases of its Helm chart. The chart's `version` in
`charts/tesk/Chart.yaml` and the release tag are kept in step: tag `vX.Y.Z`
releases chart version X.Y.Z, and pre-release tags `vX.Y.Z-alpha.N`,
`vX.Y.Z-beta.N` and `vX.Y.Z-rc.N` release chart versions `X.Y.Z-alpha.N`
etc. (SemVer, as Helm requires). Tags `v0.0.1` to `v0.2` exist from before
the chart and can't be reused (release tags are immutable), so chart
versions continue above 0.2.

Charts 0.1.0 and 0.1.1 were released under tags `tesk-0.1.0` and
`tesk-0.1.1` and indexed in a Helm repository on the `gh-pages` branch
(`helm repo add` with `https://elixir-cloud-aai.github.io/TESK/`). Those
releases stay as they are, but this workflow doesn't update that index:
releases from now on are only attached to their GitHub release, as in the
org's other repositories.

The workflow `Release` (`.github/workflows/release.yml`) runs on pushed
`v*` tags:

1. **Prepare release:** checks that the tag is annotated, signed (verified by
   GitHub), on `main` and matches the chart's `version` and the `version` of
   `CITATION.cff`, and that `CI` passed for a push of the tagged commit;
   lints, renders and installs the chart as `CI` does, and packages it.
2. **Publish release**, after a maintainer approved it in the `release`
   environment: attests the provenance of the packaged chart (GitHub
   artifact attestation), signs it (Sigstore bundle `*.sigstore.json`), and
   creates the GitHub release, with the chart and its bundle attached and
   generated notes, which list the pull requests since the previous release:
   the highest version among the tags in the history of the release commit
   with a published release, for a stable release among the stable ones
   (for the first release from this workflow, `v0.2`). Releases are
   immutable once published: the release is created as a draft, the files
   are uploaded, and then it is published. A stable release becomes the
   latest release only if no stable release tag on `main` has a higher
   version. Publish jobs run one at a time; GitHub keeps one waiting job,
   so if a third tag is pushed while one publishes and one waits, the
   waiting one is cancelled: re-run it.

The workflow relies on these repository settings, which maintainers with
admin rights keep: the `release` environment with required reviewers,
limited to `v*` tags; tag rulesets that allow only `v*` tags and make them
immutable; and immutable releases.

To release version X.Y.Z:

1. In a pull request to `dev`, set `version` in `charts/tesk/Chart.yaml`, and
   `version` and `date-released` in `CITATION.cff`, to X.Y.Z and the release
   date; merge it once CI passed. (`appVersion` in `Chart.yaml` is not the
   release version: it is the version of tesk-api that the chart deploys,
   the default tag of its image.)
2. Once `CI` passed for the push of that commit (`<sha>`) to `dev` (the
   check needs a commit that was pushed to `dev`, not one only tested in a
   pull request), move `main` forward to it (`main` only ever moves forward
   to released commits of `dev`), then tag it with a signed, annotated tag
   and push the tag:

    ```bash
    git push origin <sha>:main  # fails unless it is a fast-forward
    git tag -s vX.Y.Z <sha> -m "vX.Y.Z"
    git push origin vX.Y.Z
    ```

3. Approve the release in the `release` environment, then edit the notes of
   the published release.

If a run fails before publishing, fix the cause and re-run it: a re-run
completes a draft that a failed run left. If the tagged commit is wrong,
release a new version instead.

To install a released chart, see [Installation from a
release](deployment.md#from-a-release): it checks that this workflow built
and signed the chart from the release tag.
