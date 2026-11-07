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
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Values keys renamed to follow Helm's conventions (camelCase, `image` and
`resources` blocks), by the map that holds them (empty: the top level). The
templates still read the old keys, which take precedence over the new ones:
they can only be set by users (they aren't in `values.yaml`), and
`helm upgrade --reuse-values` replaces `values.yaml` with the defaults of the
installed chart, which has the old keys only. `tesk.image` as a string (not
in this list) is the old form of the `tesk.image` block.
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
- [tesk, limitsCpu, tesk.resources.limits.cpu]
- [tesk, limitsMemory, tesk.resources.limits.memory]
- [tesk, requestsCpu, tesk.resources.requests.cpu]
- [tesk, requestsMemory, tesk.resources.requests.memory]
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
{{- end }}
{{- end -}}
