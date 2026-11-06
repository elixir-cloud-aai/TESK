# TESK Helm repository (archived)

This branch serves the Helm repository at
`https://elixir-cloud-aai.github.io/TESK/`. Its `index.yaml` lists only the
TESK charts 0.1.0 and 0.1.1, and gets no new versions. It is kept so that
existing setups that added it with

```bash
helm repo add tesk https://elixir-cloud-aai.github.io/TESK/
```

still resolve.

From 0.3.0 on, TESK's charts are attached to the [GitHub
releases](https://github.com/elixir-cloud-aai/TESK/releases), with a GitHub
artifact attestation and a Sigstore bundle. See [From a
release](https://tesk.readthedocs.io/en/latest/deployment/#from-a-release)
in TESK's docs for how to check and install them, and the
[repository](https://github.com/elixir-cloud-aai/TESK) for everything else.
