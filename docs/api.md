# API

TESK implements the [GA4GH Task Execution Service (TES)
API](https://github.com/ga4gh/task-execution-schemas). With the default
values, it is served at `/ga4gh/tes/v1` below the host and path of the
deployment (`ingress.path` + `tesk.tesApiBasePath`, see
[Configuration](configuration.md)), e.g.,
`https://tes.example.org/ga4gh/tes/v1`.

| Operation | Endpoint |
| --- | --- |
| Information about the service | `GET /service-info` |
| Create a task | `POST /tasks` |
| List tasks | `GET /tasks` |
| Get a task | `GET /tasks/{id}` |
| Cancel a task | `POST /tasks/{id}:cancel` |

With tesk-api 1.2.0 or later, the API serves a Swagger UI, at the root
path of the deployment, only if `tesk.swaggerUi.enabled` is `true` (see
[Swagger UI](deployment.md#swagger-ui)); earlier versions always serve it.
With `auth.mode: auth`, requests need an OIDC access token (see
[Authentication and
authorisation](deployment.md#authentication-and-authorisation)), except
`GET /service-info`, which stays public unless `auth.serviceInfoPublic` is
`false` (see [Configuration](configuration.md)), the API description
(`GET /v3/api-docs`, OpenAPI 3.1; tesk-api 2.0.0 serves the same
description at the deprecated `/v2/api-docs`, where earlier versions
served Swagger 2.0), and the Swagger UI if it is on. With the default
`auth.mode: noauth`, all endpoints are open: use it only on local or
trusted networks.

The chart doesn't support private executor images: the experimental
executor fields `docker_registry`, `docker_login` and `docker_pass` (see
[Private executor images](tesk-api/api.md#private-executor-images)) need
tesk-api to create and delete secrets, which the chart's Role doesn't
allow, so such tasks fail (HTTP 500).

For example, to create a task from a checkout of this repository and get
its state:

```bash
TES=https://tes.example.org/ga4gh/tes/v1
curl -X POST "${TES}/tasks" -H 'Content-Type: application/json' \
    -d @examples/success/hello.json
curl "${TES}/tasks/<id>?view=BASIC"
```

The [examples](https://github.com/elixir-cloud-aai/TESK/tree/dev/examples)
directory has more tasks, which succeed or fail on purpose. See the
[tesk-api section](tesk-api/index.md) for details of the API's
implementation, its settings and its extensions to the specification.
