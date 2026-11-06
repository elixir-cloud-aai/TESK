# API

TESK implements the [GA4GH Task Execution Service (TES)
API](https://github.com/ga4gh/task-execution-schemas). With the default
values, it is served at `/ga4gh/tes/v1` below the host and path of the
deployment (`ingress.path` + `tesk.tes_api_base_path`, see
[Configuration](configuration.md)), e.g.,
`https://tes.example.org/ga4gh/tes/v1`.

| Operation | Endpoint |
| --- | --- |
| Information about the service | `GET /service-info` |
| Create a task | `POST /tasks` |
| List tasks | `GET /tasks` |
| Get a task | `GET /tasks/{id}` |
| Cancel a task | `POST /tasks/{id}:cancel` |

The API also serves a Swagger UI, at the root path of the deployment. With
`auth.mode: auth`, requests need an OIDC access token (see [Authentication
and authorisation](deployment.md#authentication-and-authorisation)).

For example, to create a task and get its state:

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
