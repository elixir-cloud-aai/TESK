# Upgrading

Changes that affect existing deployments, newest first. Upgrade a release
with the same values files as before, adapted as described here:

```bash
helm upgrade tesk charts/tesk --namespace tesk -f my-values.yaml -f secrets.yaml
```

## Unreleased

### Releases and chart versions

Charts are now released from signed `vX.Y.Z` tags as files attached to
[GitHub releases](https://github.com/elixir-cloud-aai/TESK/releases), with
an attestation and a signature (see [Releases](development.md#releases)).
The chart version equals the release version. As tags up to `v0.2` exist
from earlier releases, the next chart version is higher than 0.2, although
the last chart released to the Helm repository at
`https://elixir-cloud-aai.github.io/TESK/` was 0.1.1. That Helm repository
gets no new versions.

### Taskmaster and filer v0.10.6

The default taskmaster and filer are now v0.10.6 (were v0.10.2):

- Taskmaster v0.10.2 ends tasks in `SYSTEM_ERROR` on Kubernetes 1.31 or
  later, as it reads only the first condition of a job. If your values set
  `tesk.taskmaster_image_version`, set it to v0.10.6 or later.
- **Resource limits:** v0.10.6 sets the resources that a task requests
  (`resources.cpu_cores`, `resources.ram_gb`) as the limits of its executors
  too. A task that uses more memory than it requested is now killed (OOM),
  and its CPU is throttled. Tasks that relied on using more than they
  requested must request more.

### Public service info

The new value `auth.service_info_public` (default `true`) controls whether
`GET /service-info` needs a token with `auth.mode: auth`. It needs tesk-api
1.2.0 or later; earlier versions ignore it and keep the endpoint public.
The default keeps the endpoint public; set it to `false` to require a
token.

### Swagger UI with tesk-api 1.2.0

The new value `tesk.swaggerUi.enabled` (default `false`) controls whether
tesk-api serves the Swagger UI (see [Swagger UI](deployment.md#swagger-ui)).
Upgrading the chart alone changes nothing: tesk-api before 1.2.0 (the
chart's default `tesk.image` is still 1.1.0) ignores the value and always
serves the Swagger UI. tesk-api 1.2.0 or later serves it only if the value
is `true`. If you use the Swagger UI, set `tesk.swaggerUi.enabled: true`
when you upgrade to tesk-api 1.2.0 or later. Turning it on serves the
Swagger UI publicly; enable it only where needed.
