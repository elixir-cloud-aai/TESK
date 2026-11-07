{{/*
Standard labels (https://helm.sh/docs/chart_best_practices/labels/) of all
objects of the chart, in their metadata. They are never used in selectors:
selectors can't be changed by `helm upgrade`, so these keep `app: tesk-api`.
*/}}
{{- define "tesk.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{ include "tesk.podLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Standard labels of the API's pods: only those that don't change with the
chart's version, so that upgrading the chart alone doesn't restart them.
*/}}
{{- define "tesk.podLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name | quote }}
{{- end -}}

{{/*
Values keys renamed to follow Helm's conventions (camelCase, `image` and
`resources` blocks): the map that holds the old key (empty: the top level),
the old key, the new key's path, and `yaml` for old values that the
earlier templates printed into YAML, so that they are parsed as YAML (e.g.,
an empty string drops a resource limit, as before). The templates read these values with
`tesk.resolveValues`, so the old keys still work, and `tesk.deprecatedValues`
lists those in use. `tesk.image` as a string (not in this list) is the old
form of the `tesk.image` block.
*/}}
{{- define "tesk.renamedValues" -}}
- ["", host_name, hostName]
- [tesk, tes_api_base_path, tesk.tesApiBasePath]
- [tesk, taskmaster_image_name, tesk.taskmaster.image.repository]
- [tesk, taskmaster_image_version, tesk.taskmaster.image.tag]
- [tesk, taskmaster_filer_image_name, tesk.filer.image.repository]
- [tesk, taskmaster_filer_image_version, tesk.filer.image.tag]
- [tesk, executor_retries, tesk.executorRetries]
- [tesk, filer_retries, tesk.filerRetries]
- [tesk, limitsCpu, tesk.resources.limits.cpu, yaml]
- [tesk, limitsMemory, tesk.resources.limits.memory, yaml]
- [tesk, requestsCpu, tesk.resources.requests.cpu, yaml]
- [tesk, requestsMemory, tesk.resources.requests.memory, yaml]
- [transfer, wes_base_path, transfer.wesBasePath]
- [transfer, tes_base_path, transfer.tesBasePath]
- [transfer, pvc_name, transfer.pvcName]
- [auth, env_subgroup, auth.envSubgroup]
- [auth, env_basegroup, auth.envBasegroup]
- [auth, service_info_public, auth.serviceInfoPublic]
- [auth, client_id, auth.clientId]
- [auth, client_secret, auth.clientSecret]
- [service, node_port, service.nodePort]
- [ftp, classic_ftp_secret, ftp.classicFtpSecret]
- [ftp, netrc_secret, ftp.netrcSecret]
- [ingress, tls_secret_name, ingress.tlsSecretName]
{{- end -}}

{{/*
Resolves the renamed values (`tesk.renamedValues`) of the root context
(`root`) into a dict (`out`), by the new keys' paths (e.g.,
`out.hostName`): from the old key if it is set (also to null or empty),
else from the new key (null if missing). The old keys take precedence: they
can only be set by users (they aren't in `values.yaml`), and
`helm upgrade --reuse-values` replaces `values.yaml` with the defaults of
the installed chart, which has the old keys only. Renders nothing; the
templates call it as
`{{- $values := dict -}}{{- include "tesk.resolveValues" (dict "root" . "out" $values) -}}`.
Old values marked `yaml` are parsed as YAML; invalid YAML fails, as with
the earlier templates.
*/}}
{{- define "tesk.resolveValues" -}}
{{- $root := .root.Values -}}
{{- $out := .out -}}
{{- range include "tesk.renamedValues" .root | fromYamlArray -}}
{{- $parent := ternary $root (index $root (index . 0)) (eq (index . 0) "") -}}
{{- $value := $root -}}
{{- if and (kindIs "map" $parent) (hasKey $parent (index . 1)) -}}
{{- $value = index $parent (index . 1) -}}
{{- if has "yaml" . -}}
{{- $text := ternary "" (toString $value) (kindIs "invalid" $value) -}}
{{- $parsed := printf "value: %s" $text | fromYaml -}}
{{- if hasKey $parsed "Error" -}}
{{- fail (printf "%s%s is not valid YAML: %s" (ternary "" (printf "%s." (index . 0)) (eq (index . 0) "")) (index . 1) $parsed.Error) -}}
{{- end -}}
{{- $value = $parsed.value -}}
{{- end -}}
{{- else -}}
{{- /* Null if a map on the path is missing (or not a map) */ -}}
{{- range splitList "." (index . 2) -}}
{{- $value = index (ternary $value (dict) (kindIs "map" $value)) . -}}
{{- end -}}
{{- end -}}
{{- $_ := set $out (index . 2) $value -}}
{{- end -}}
{{- end -}}

{{/*
The deprecated keys in use, one per line, with their new keys; empty if
there are none.
*/}}
{{- define "tesk.deprecatedValues" -}}
{{- $values := .Values -}}
{{- range include "tesk.renamedValues" . | fromYamlArray -}}
{{- $map := $values -}}
{{- $prefix := "" -}}
{{- if index . 0 -}}
{{- $map = index $values (index . 0) -}}
{{- $prefix = printf "%s." (index . 0) -}}
{{- end -}}
{{- if and (kindIs "map" $map) (hasKey $map (index . 1)) }}
  - {{ $prefix }}{{ index . 1 }}: use {{ index . 2 }}
{{- end -}}
{{- end -}}
{{- if and (kindIs "map" .Values.tesk) (kindIs "string" .Values.tesk.image) }}
  - tesk.image (a string): use tesk.image.repository and tesk.image.tag
{{- end -}}
{{- end -}}

{{/*
The notes that `helm install` and `helm upgrade` print (`NOTES.txt`).
*/}}
{{- define "tesk.notes" -}}
TESK is deployed as release {{ .Release.Name }} in namespace {{ .Release.Namespace }}.
See https://tesk.readthedocs.io/en/latest/deployment/ to check the installation.
{{- with include "tesk.deprecatedValues" . }}

WARNING: Your values use deprecated keys, which a later release will remove.
Rename them (see
https://tesk.readthedocs.io/en/latest/upgrading/#values-renamed-to-camelcase):
{{- . }}
With --reuse-values, the values include the defaults of the earlier chart,
with all of these keys: upgrade once with your values files (-f) instead.
{{- end }}
{{- end -}}

{{/*
A secret value as a quoted YAML string. Helm parses numbers in values
files as floats, which Go renders in scientific notation from 1e21 (and
rounds above 2^53); whole numbers up to 2^53 are rendered as written, and
larger ones fail: quote them in the values file (e.g., `"12345678901234567890"`)
or set them with `--set-string`.
*/}}
{{- define "tesk.secretValue" -}}
{{- if and (kindIs "float64" .) (eq (floor .) .) -}}
{{- if and (lt . 9007199254740992.0) (gt . -9007199254740992.0) -}}
{{- printf "%.0f" . | quote -}}
{{- else -}}
{{- fail "a secret value is a number too large to be exact: quote it in the values file or use --set-string" -}}
{{- end -}}
{{- else -}}
{{- quote . -}}
{{- end -}}
{{- end -}}
