{{/*
The chart's name (`nameOverride` replaces it), for the label
`app.kubernetes.io/name`: cut to 63 characters, without trailing dashes.
Fails if it isn't a valid label value (letters, digits, `-`, `_` and `.`,
starting and ending with a letter or digit).
*/}}
{{- define "tesk.name" -}}
{{- $name := regexReplaceAll "-+$" (default .Chart.Name .Values.nameOverride | toString | trunc 63) "" -}}
{{- if not (regexMatch "^[A-Za-z0-9]([-A-Za-z0-9_.]*[A-Za-z0-9])?$" $name) -}}
{{- fail (printf "nameOverride %q isn't a valid label value (letters, digits, -, _ and ., starting and ending with a letter or digit)" $name) -}}
{{- end -}}
{{- $name -}}
{{- end -}}

{{/*
The prefix of the names of the chart's objects, as in `helm create`:
`fullnameOverride` if set, else the release name if it contains the chart's
name (`tesk`, or `nameOverride`), else `<release>-<name>`. Cut to 50
characters, so that the names with the longest suffix (`-service-info`)
fit the 63 characters of a DNS label. Fails if the prefix isn't a valid
start of a Service name (DNS-1035: a lowercase letter first, then
lowercase letters, digits and dashes), e.g. for the release names `123` or
`tesk.prod`, which Helm accepts: set `fullnameOverride` then.
*/}}
{{- define "tesk.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride | toString -}}
{{- $fullname := printf "%s-%s" .Release.Name $name -}}
{{- if .Values.fullnameOverride -}}
{{- $fullname = toString .Values.fullnameOverride -}}
{{- else if contains $name .Release.Name -}}
{{- $fullname = .Release.Name -}}
{{- end -}}
{{- $fullname = regexReplaceAll "-+$" ($fullname | trunc 50) "" -}}
{{- if not (regexMatch "^[a-z]([-a-z0-9]*[a-z0-9])?$" $fullname) -}}
{{- fail (printf "the names of the objects would start with %q, which isn't a valid Service name (a lowercase letter first, then lowercase letters, digits and dashes): use another release name or nameOverride, or set fullnameOverride" $fullname) -}}
{{- end -}}
{{- $fullname -}}
{{- end -}}

{{/*
Names of the chart's objects, derived from `tesk.fullname`: the API's
Deployment and Service, the taskmasters' ServiceAccount, Role and
RoleBinding, the ConfigMaps with the service info and the executors'
security context, and the secret with the OAuth client. tesk-api gets
the names that it passes on to the taskmasters (service account, FTP
secret) from its environment.
*/}}
{{- define "tesk.apiName" -}}
{{- include "tesk.fullname" . }}-api
{{- end -}}

{{- define "tesk.taskmasterName" -}}
{{- include "tesk.fullname" . }}-taskmaster
{{- end -}}

{{- define "tesk.serviceInfoName" -}}
{{- include "tesk.fullname" . }}-service-info
{{- end -}}

{{/*
The ConfigMap with the service info that the API mounts: the operator's
(`serviceInfo.existingConfigMap`, if set, also if YAML reads it as 0 or
false) or the chart's (`tesk.serviceInfoName`, rendered only then).
*/}}
{{- define "tesk.serviceInfoConfigMapName" -}}
{{- $existing := (default dict .Values.serviceInfo).existingConfigMap -}}
{{- if include "tesk.isSet" $existing -}}
{{- toString $existing -}}
{{- else -}}
{{- include "tesk.serviceInfoName" . -}}
{{- end -}}
{{- end -}}

{{/*
The tag of the API's image (tesk-api): `tesk.image.tag`, or the chart's
`appVersion` if it is unset or empty (not `default`, which would replace a
tag of 0). Whole numbers, which Helm reads from values files as floats,
are rendered as written (e.g., 20261110, not 2.026111e+07) up to 2^53, and
fail above, where they would be rounded (as in `tesk.yamlText`).
*/}}
{{- define "tesk.apiImageTag" -}}
{{- $tag := dig "image" "tag" "" .Values.tesk -}}
{{- if or (kindIs "invalid" $tag) (eq (toString $tag) "") -}}
{{- $tag = .Chart.AppVersion -}}
{{- end -}}
{{- if and (kindIs "float64" $tag) (eq (floor $tag) $tag) -}}
{{- if not (and (lt $tag 9007199254740992.0) (gt $tag -9007199254740992.0)) -}}
{{- fail "tesk.image.tag is a number too large to be exact: quote it in the values file or use --set-string" -}}
{{- end -}}
{{- printf "%.0f" $tag -}}
{{- else -}}
{{- toString $tag -}}
{{- end -}}
{{- end -}}

{{- define "tesk.oauthClientName" -}}
{{- include "tesk.fullname" . }}-oauth-client
{{- end -}}

{{- define "tesk.executorConfigName" -}}
{{- include "tesk.fullname" . }}-executor
{{- end -}}

{{/*
The executors' security context (`tesk.executor.securityContext`) as
tesk-api reads it (`KubernetesObjectsSupplier`): the fields `fsGroup`,
`runAsGroup` and `runAsUser` as integers (Helm reads numbers in values
files as floats, which YAML would render as, e.g., 1e+06), and
`runAsNonRoot` as `nonRoot`; empty if none is set.
*/}}
{{- define "tesk.executorSecurityContext" -}}
{{- $context := dig "executor" "securityContext" dict .Values.tesk | default dict -}}
{{- $lines := list -}}
{{- range $key := list "fsGroup" "runAsGroup" "runAsUser" -}}
{{- if hasKey $context $key -}}
{{- $lines = append $lines (printf "%s: %d" $key (index $context $key | int64)) -}}
{{- end -}}
{{- end -}}
{{- if and (hasKey $context "runAsUser") (eq (index $context "runAsUser" | int64) 0) (eq (toString (index $context "runAsNonRoot")) "true") -}}
{{- fail "tesk.executor.securityContext: runAsUser 0 contradicts runAsNonRoot true; Kubernetes wouldn't start the executors" -}}
{{- end -}}
{{- if hasKey $context "runAsNonRoot" -}}
{{- $lines = append $lines (printf "nonRoot: %t" (index $context "runAsNonRoot")) -}}
{{- end -}}
{{- join "\n" $lines -}}
{{- end -}}

{{/*
Name of the secret with the FTP credentials: `ftp.classicFtpSecret`, or
`<fullname>-ftp` if it is null (unset); empty (no secret) if it is empty or
otherwise false (e.g., `false`), as in earlier versions of the chart. Also
empty without credentials: neither `ftp.username` nor `ftp.password` is set
(any value counts, also one that YAML reads as 0 or false), so that the
chart creates no secret with empty credentials and tesk-api gets no FTP
secret.
*/}}
{{- define "tesk.ftpSecretName" -}}
{{- $name := .Values.ftp.classicFtpSecret -}}
{{- $credentials := or (include "tesk.isSet" .Values.ftp.username) (include "tesk.isSet" .Values.ftp.password) -}}
{{- if $credentials -}}
{{- if kindIs "invalid" $name -}}
{{- include "tesk.fullname" . }}-ftp
{{- else if $name -}}
{{- toString $name -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Selector labels of the API's pods, as in `helm create`: they tell the pods
of different releases apart. Selectors can't change after an install.
*/}}
{{- define "tesk.selectorLabels" -}}
app.kubernetes.io/name: {{ include "tesk.name" . | quote }}
app.kubernetes.io/instance: {{ .Release.Name | quote }}
{{- end -}}

{{/*
Standard labels (https://helm.sh/docs/chart_best_practices/labels/) of all
objects of the chart, in their metadata.
*/}}
{{- define "tesk.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{ include "tesk.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Values keys of earlier versions of the chart, which this one no longer
reads, and what replaces them: the map that holds the old key (empty: the
top level; nested maps separated by dots), the old key, and the
replacement. The chart fails if any of them is set
(`tesk.checkRemovedValues`), so that they aren't ignored unnoticed; the
schema (`values.schema.json`) lets them through for that. Besides the keys
of released charts, the list has `auth.envBasegroup`, a name that the chart
had on `dev` only, as it would otherwise fall back to the default group.
Keep in sync (tests/test_chart.py checks it): the removed keys in
`values.schema.json`, `REMOVED` in tests/test_chart.py and the table in
docs/upgrading.md.
*/}}
{{- define "tesk.removedValues" -}}
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
- [auth, env_basegroup, auth.envBaseGroup]
- [auth, service_info_public, auth.serviceInfoPublic]
- [auth, client_id, auth.clientId]
- [auth, client_secret, "nothing (auth.clientSecret, its new name, is deprecated: leave it unset)"]
- [service, node_port, service.nodePort]
- [ftp, classic_ftp_secret, ftp.classicFtpSecret]
- [ftp, netrc_secret, ftp.netrcSecret]
- [ingress, tls_secret_name, ingress.tlsSecretName]
- [tesk.securityContext, enabled, tesk.podSecurityContext and tesk.securityContext (maps; null for none)]
- [transfer, active, transfer.enabled]
- [auth, envBasegroup, auth.envBaseGroup]
- [ftp, hostip, ftp.hostIp]
- [ingress, rules, ingress.enabled]
- [ingress, ingressClassName, ingress.className]
{{- end -}}

{{/*
Fails if the values set keys of `tesk.removedValues` (also to null or
empty) or `tesk.image` as a string (the old form), listing them with their
replacements, but not their values; renders nothing otherwise.
*/}}
{{- define "tesk.checkRemovedValues" -}}
{{- $values := .Values -}}
{{- $found := list -}}
{{- range include "tesk.removedValues" . | fromYamlArray -}}
{{- $map := $values -}}
{{- $prefix := "" -}}
{{- if index . 0 -}}
{{- range $part := splitList "." (index . 0) -}}
{{- if kindIs "map" $map -}}
{{- $map = get $map $part -}}
{{- end -}}
{{- end -}}
{{- $prefix = printf "%s." (index . 0) -}}
{{- end -}}
{{- if and (kindIs "map" $map) (hasKey $map (index . 1)) -}}
{{- $found = append $found (printf "%s%s: use %s" $prefix (index . 1) (index . 2)) -}}
{{- end -}}
{{- end -}}
{{- if and (kindIs "map" $values.tesk) (kindIs "string" $values.tesk.image) -}}
{{- $found = append $found "tesk.image (a string): use tesk.image.repository and tesk.image.tag" -}}
{{- end -}}
{{- if $found -}}
{{- fail (printf "\n\nThe values use keys that this chart no longer reads. Rename them (see\nhttps://tesk.readthedocs.io/en/latest/upgrading/#resource-names-from-the-release-name):\n  - %s\n" (join "\n  - " $found)) -}}
{{- end -}}
{{- end -}}

{{/*
Fails if the taskmaster and the filer are of different releases, one of
them 0.11.0 or later: from 0.11.0 on, the filer must be of the taskmaster's
release, and a task with another one fails. Release tags are compared
without their `v` (`v0.11.0` is `0.11.0`); releases up to v0.10.6 could be
mixed, and tags that aren't release versions (e.g., `dev`) aren't checked.
*/}}
{{- define "tesk.checkImageReleases" -}}
{{- $tags := dict -}}
{{- range $component := list "taskmaster" "filer" -}}
{{- $_ := set $tags $component (toString (dig $component "image" "tag" "" $.Values.tesk)) -}}
{{- end -}}
{{- $taskmaster := trimPrefix "v" $tags.taskmaster -}}
{{- $filer := trimPrefix "v" $tags.filer -}}
{{- $release := "^[0-9]+\\.[0-9]+\\.[0-9]+$" -}}
{{- if and (regexMatch $release $taskmaster) (regexMatch $release $filer) (ne $taskmaster $filer) (or (semverCompare ">0.10.6" $taskmaster) (semverCompare ">0.10.6" $filer)) -}}
{{- fail (printf "tesk.taskmaster.image.tag (%s) and tesk.filer.image.tag (%s) must be the same release: from 0.11.0 on, the filer must be of the taskmaster's release; see https://tesk.readthedocs.io/en/latest/upgrading/#tesk-api-120-taskmaster-and-filer-0110" $tags.taskmaster $tags.filer) -}}
{{- end -}}
{{- end -}}

{{/*
The notes that `helm install` and `helm upgrade` print (`NOTES.txt`).
*/}}
{{- define "tesk.notes" -}}
TESK is deployed as release {{ .Release.Name }} in namespace {{ .Release.Namespace }}.
See https://tesk.readthedocs.io/en/latest/deployment/ to check the installation.
{{- $serviceInfo := default dict .Values.serviceInfo -}}
{{- if and (not (include "tesk.isSet" $serviceInfo.existingConfigMap)) (eq (toString $serviceInfo.id) "uk.ac.ebi.tsc.tesk") }}

NOTE: serviceInfo.id is the chart's default, so GET /service-info describes
no particular deployment. Set serviceInfo.id, serviceInfo.organization,
serviceInfo.contactUrl and serviceInfo.environment for yours; see
https://tesk.readthedocs.io/en/latest/configuration/#service-info-serviceinfo
{{- end }}
{{- /* Any user name, also one that YAML reads as 0 or false */ -}}
{{- $username := .Values.ftp.username -}}
{{- $hasUsername := include "tesk.isSet" $username -}}
{{- if and (include "tesk.ftpSecretName" .) (not .Values.ftp.netrcSecret) $hasUsername (not .Values.ftp.hosts) }}

WARNING: ftp.username is set, but ftp.hosts is empty. With taskmaster and
filer images newer than v0.10.6, the filer sends the FTP credentials to no
host, and logs in anonymously. Set ftp.hosts to the hosts of the FTP
account, or use a .netrc file (ftp.netrcSecret); see
https://tesk.readthedocs.io/en/latest/upgrading/#ftp-credentials-go-only-to-configured-hosts
{{- end }}
{{- /* A secret named in the values, but no credentials for it: the chart
creates and passes on none (`tesk.ftpSecretName`), also not a secret of
that name made outside the chart */ -}}
{{- $ftpSecret := .Values.ftp.classicFtpSecret -}}
{{- if and $ftpSecret (not (include "tesk.ftpSecretName" .)) }}

WARNING: ftp.classicFtpSecret is set, but neither ftp.username nor
ftp.password is: the chart creates no FTP secret, and tasks get none, also
if a secret of that name exists. Put the FTP credentials into the values
(secrets.yaml); see
https://tesk.readthedocs.io/en/latest/upgrading/#no-ftp-secret-without-credentials
{{- end }}
{{- /* Any client secret, also one that YAML reads as 0 or false */ -}}
{{- if include "tesk.isSet" .Values.auth.clientSecret }}

WARNING: auth.clientSecret is deprecated: the Swagger UI is a public client,
which needs no secret, and tesk-api 1.2.0 and later ignore it. Register the
Swagger UI's client as a public client, remove auth.clientSecret from your
values, and rotate the secret at your identity provider; see
https://tesk.readthedocs.io/en/latest/upgrading/#swagger-ui-client-secret-deprecated
{{- end }}
{{- /* Release tags (X.Y.Z or vX.Y.Z) up to v0.10.6 ignore ftp.hosts,
tesk.filerHttpTimeout, tesk.taskTtlSeconds and tesk.maxQueueSeconds; others
(e.g., dev) are assumed to support them */ -}}
{{- $oldImages := list -}}
{{- range $component := list "taskmaster" "filer" -}}
{{- $tag := toString (dig $component "image" "tag" "" $.Values.tesk) | trimPrefix "v" -}}
{{- if and (regexMatch "^[0-9]+\\.[0-9]+\\.[0-9]+$" $tag) (semverCompare "<=0.10.6" $tag) -}}
{{- $oldImages = append $oldImages (printf "tesk.%s.image.tag" $component) -}}
{{- end -}}
{{- end -}}
{{- if and .Values.ftp.hosts $oldImages }}

WARNING: ftp.hosts is set, but {{ join " and " $oldImages }} {{ ternary "is" "are" (eq (len $oldImages) 1) }}
v0.10.6 or older, which ignores ftp.hosts: the filer sends the FTP
credentials to every FTP host, as before. Use images newer than v0.10.6.
{{- end }}
{{- $oldTaskmaster := has "tesk.taskmaster.image.tag" $oldImages -}}
{{- range $name, $minimum := dict "taskTtlSeconds" 0 "maxQueueSeconds" 1 -}}
{{- if and (include "tesk.seconds" (dict "root" $ "name" $name "minimum" $minimum)) $oldTaskmaster }}

WARNING: tesk.{{ $name }} is set, but tesk.taskmaster.image.tag is
v0.10.6 or older, which ignores it. Use a taskmaster image newer than
v0.10.6.
{{- end -}}
{{- end -}}
{{- /* tesk-api 1.1 and older report a task whose executor was deleted for
the max queue time as COMPLETE (tesk-api#104); tags that aren't versions
(e.g., dev) are assumed to be newer */ -}}
{{- $apiTag := toString (dig "image" "tag" "" .Values.tesk) | default .Chart.AppVersion | trimPrefix "v" -}}
{{- if and (include "tesk.seconds" (dict "root" . "name" "maxQueueSeconds" "minimum" 1)) (regexMatch "^[0-9]+\\.[0-9]+(\\.[0-9]+)?([-+][0-9A-Za-z.+-]*)?$" $apiTag) (semverCompare "<1.2.0-0" $apiTag) }}

WARNING: tesk.maxQueueSeconds is set, but tesk-api {{ $apiTag }} (tesk.image.tag)
reports a task whose executor wasn't scheduled in time as COMPLETE instead
of SYSTEM_ERROR. Set it only with a tesk-api image newer than 1.1; see
https://tesk.readthedocs.io/en/latest/deployment/#tasks-that-cant-be-scheduled
{{- end }}
{{- /* tesk-api before 1.2.0 ignores the legacy creator labels setting,
which the chart only passes on with mode auth */ -}}
{{- $oldApi := and (regexMatch "^[0-9]+\\.[0-9]+(\\.[0-9]+)?([-+][0-9A-Za-z.+-]*)?$" $apiTag) (semverCompare "<1.2.0-0" $apiTag) -}}
{{- if and (eq (toString .Values.auth.mode) "auth") (eq (toString .Values.auth.legacyUserLabels) "true") $oldApi }}

WARNING: auth.legacyUserLabels is on, but tesk-api {{ $apiTag }} (tesk.image.tag)
ignores it. It is for tesk-api 1.2.0 or later; see
https://tesk.readthedocs.io/en/latest/deployment/#tasks-created-before-tesk-api-120
{{- end }}
{{- /* tesk-api 1.2.0 and older ignore the tokens of allow-listed clients,
which the chart only passes on with mode auth (and fails without it) */ -}}
{{- $tokenClientsOn := eq (toString (dig "tokenClients" "enabled" "" .Values.auth)) "true" -}}
{{- if and $tokenClientsOn (regexMatch "^[0-9]+\\.[0-9]+(\\.[0-9]+)?([-+][0-9A-Za-z.+-]*)?$" $apiTag) (semverCompare "<=1.2.0" $apiTag) }}

WARNING: auth.tokenClients is on, but tesk-api {{ $apiTag }} (tesk.image.tag)
ignores it and refuses the clients' tokens. It is for tesk-api releases after
1.2.0; see
https://tesk.readthedocs.io/en/latest/deployment/#tokens-of-services
{{- end }}
{{- if and .Values.tesk.filerHttpTimeout $oldImages }}

WARNING: tesk.filerHttpTimeout is set, but {{ join " and " $oldImages }} {{ ternary "is" "are" (eq (len $oldImages) 1) }}
v0.10.6 or older, which ignores it: HTTP(S) requests of the filer have no
timeout, as before. Use images newer than v0.10.6.
{{- end }}
{{- /* auth.envBaseGroup replaces the parent group and the subgroup in
tesk-api */ -}}
{{- if and (include "tesk.isSet" (dig "groups" "parentGroup" "" .Values.auth)) (include "tesk.isSet" .Values.auth.envBaseGroup) }}

WARNING: auth.groups.parentGroup is set, but tesk-api ignores it, as
auth.envBaseGroup is set too, which replaces it and auth.envSubgroup. Set
auth.envBaseGroup to the full name of the environment group, or set it to
"" to use auth.groups.parentGroup and auth.envSubgroup; see
https://tesk.readthedocs.io/en/latest/deployment/#ls-login-and-other-providers
{{- end }}
{{- /* tesk-api sends every request's token to the user info endpoint */ -}}
{{- if hasPrefix "http://" (toString (default "" .Values.auth.userInfoUri)) }}

WARNING: auth.userInfoUri is an http:// URL: tesk-api sends the access token
of every request to it unencrypted. Use https://, unless the endpoint is
reached only within a trusted network (e.g., a provider in the cluster).
{{- end }}
{{- end -}}

{{/*
The service info (`serviceInfo`) as the YAML file that tesk-api reads
(`TesServiceInfo`), or nothing with `serviceInfo.existingConfigMap`. Text
fields are quoted (`tesk.yamlText`), so that tesk-api reads them as
text whatever they look like; `createdAt` and `updatedAt` are YAML
timestamps, unquoted, as tesk-api reads them as dates. Empty optional
fields are left out; the fields that the GA4GH service-info specification
requires fail if empty. `type` (TES 1.0.0, which tesk-api implements) and
`version` (the tag of tesk-api's image) are set here.
`type.artifact` is `TES`, the name of tesk-api's Java enum constant, which
it reads with SnakeYAML and serves as `tes` (the TES specification's
artifact); with `tes` here, tesk-api can't read the service info.
*/}}
{{- define "tesk.serviceInfo" -}}
{{- $info := default dict .Values.serviceInfo -}}
{{- if not (include "tesk.isSet" $info.existingConfigMap) -}}
{{- $organization := default dict $info.organization -}}
{{- range $field, $value := dict "id" $info.id "name" $info.name "organization.name" $organization.name "organization.url" $organization.url -}}
{{- if not (include "tesk.isSet" $value) -}}
{{- fail (printf "serviceInfo.%s must be set: the GA4GH service-info specification requires it" $field) -}}
{{- end -}}
{{- end -}}
{{- /* YAML 1.1 timestamps, as SnakeYAML resolves them (two-digit month
and day without a time); the same pattern as `$defs/timestamp` in
values.schema.json, which checks them first */ -}}
{{- $timestamp := "^([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}([Tt]|[ \t]+)[0-9]{1,2}:[0-9]{2}:[0-9]{2}(\\.[0-9]*)?([ \t]*(Z|[-+][0-9]{1,2}(:[0-9]{2})?))?)$" -}}
{{- range $field := list "createdAt" "updatedAt" -}}
{{- $value := index $info $field -}}
{{- if include "tesk.isSet" $value -}}
{{- $text := toString $value -}}
{{- /* Dates and times that don't exist (e.g., 2021-02-30, 24:00:00),
which SnakeYAML would read as other ones, fail too: Go's parser rejects
them, and `toDate` then gives the zero time. The date part has no colons,
so the first match of the time pattern is the time */ -}}
{{- $valid := regexMatch $timestamp $text -}}
{{- if $valid -}}
{{- $valid = not (toDate "2006-1-2" (regexFind "^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}" $text)).IsZero -}}
{{- end -}}
{{- $time := regexFind "[0-9]{1,2}:[0-9]{2}:[0-9]{2}" $text -}}
{{- if and $valid $time -}}
{{- $valid = not (toDate "15:04:05" $time).IsZero -}}
{{- end -}}
{{- if not $valid -}}
{{- fail (printf "serviceInfo.%s must be a date (e.g., 2026-11-10) or a date and time (e.g., 2026-11-10T12:00:00Z), not %q" $field $text) -}}
{{- end -}}
{{- end -}}
{{- end -}}
id: {{ include "tesk.yamlText" (dict "value" $info.id "key" "serviceInfo.id") }}
name: {{ include "tesk.yamlText" (dict "value" $info.name "key" "serviceInfo.name") }}
type:
  group: "org.ga4gh"
  {{- /* tesk-api serves "tes"; see above */}}
  artifact: "TES"
  version: "1.0.0"
{{- if include "tesk.isSet" $info.description }}
description: {{ include "tesk.yamlText" (dict "value" $info.description "key" "serviceInfo.description") }}
{{- end }}
organization:
  name: {{ include "tesk.yamlText" (dict "value" $organization.name "key" "serviceInfo.organization.name") }}
  url: {{ include "tesk.yamlText" (dict "value" $organization.url "key" "serviceInfo.organization.url") }}
{{- range $field := list "contactUrl" "documentationUrl" }}
{{- $value := index $info . }}
{{- if include "tesk.isSet" $value }}
{{ $field }}: {{ include "tesk.yamlText" (dict "value" $value "key" (printf "serviceInfo.%s" $field)) }}
{{- end }}
{{- end }}
{{- range $field := list "createdAt" "updatedAt" }}
{{- $value := index $info . }}
{{- if include "tesk.isSet" $value }}
{{ $field }}: {{ toString $value }}
{{- end }}
{{- end }}
{{- if include "tesk.isSet" $info.environment }}
environment: {{ include "tesk.yamlText" (dict "value" $info.environment "key" "serviceInfo.environment") }}
{{- end }}
version: {{ include "tesk.apiImageTag" . | toJson }}
{{- with $info.storage }}
storage:
{{- range . }}
- {{ include "tesk.yamlText" (dict "value" . "key" "serviceInfo.storage") }}
{{- end }}
{{- end }}
{{- end -}}
{{- end -}}

{{/*
A value as a quoted YAML string (a JSON string, which YAML reads as a
double-quoted scalar, with DEL and NEL escaped too, which JSON leaves as
they are and Helm's YAML parser rejects). Other characters that YAML
doesn't allow and JSON doesn't escape (the other C1 controls, U+FFFE and
U+FFFF) fail with the value's key. Whole numbers, which Helm reads from values files as floats,
are rendered as written (e.g., 12345678, not 1.2345678e+07) up to 2^53,
and fail above, where they would be rounded: quote them in the values
file. Decimals lose trailing zeros (1.10 is 1.1).

Takes the value (`value`) and its key (`key`), for the errors.
*/}}
{{- define "tesk.yamlText" -}}
{{- $value := .value -}}
{{- $text := toString $value -}}
{{- if and (kindIs "float64" $value) (eq (floor $value) $value) -}}
{{- if not (and (lt $value 9007199254740992.0) (gt $value -9007199254740992.0)) -}}
{{- fail (printf "%s is a number too large to be exact: quote it in the values file or use --set-string" .key) -}}
{{- end -}}
{{- $text = printf "%.0f" $value -}}
{{- end -}}
{{- if regexMatch "[\u0080-\u0084\u0086-\u009f\ufffe\uffff]" $text -}}
{{- fail (printf "%s has a control character that YAML doesn't allow (U+0080 to U+009F but U+0085, U+FFFE or U+FFFF)" .key) -}}
{{- end -}}
{{- toJson $text | replace "\u007f" "\\u007f" | replace "\u0085" "\\u0085" -}}
{{- end -}}

{{/*
Whole seconds from a value under `tesk` (`name`), with a `minimum` (0 or 1),
as the taskmaster reads them: empty if unset (null or empty); fails on
anything but whole seconds from `minimum` to 2147483647, which the
taskmaster would ignore, also without the schema. Numbers from values files
are floats, rendered as integers; strings of digits lose their leading
zeros. The range is checked on the digits, not with `atoi`, whose `int` has
32 bits on some platforms.
*/}}
{{- define "tesk.seconds" -}}
{{- $value := index .root.Values.tesk .name -}}
{{- if include "tesk.isSet" $value -}}
{{- $seconds := "" -}}
{{- if kindIs "string" $value -}}
{{- $seconds = $value -}}
{{- else if and (or (kindIs "int" $value) (kindIs "int64" $value) (kindIs "float64" $value)) (eq (float64 $value) (floor $value)) -}}
{{- $seconds = printf "%d" ($value | int64) -}}
{{- end -}}
{{- $digits := regexReplaceAll "^0+([0-9])" $seconds "${1}" -}}
{{- if or (not (regexMatch "^[0-9]+$" $seconds)) (gt (len $digits) 10) (and (eq (len $digits) 10) (gt $digits "2147483647")) (and (eq (int .minimum) 1) (eq $digits "0")) -}}
{{- fail (printf "tesk.%s must be whole seconds from %d to 2147483647, not %q" .name (int .minimum) (toString $value)) -}}
{{- end -}}
{{- $digits -}}
{{- end -}}
{{- end -}}

{{/*
"true" if a value is set: not null and not empty, also if YAML reads it as
0 or false; empty otherwise.
*/}}
{{- define "tesk.isSet" -}}
{{- if and (not (kindIs "invalid" .)) (ne (toString .) "") -}}
true
{{- end -}}
{{- end -}}

{{/*
A secret value as a quoted YAML string. Helm parses numbers in values
files as floats, which Go renders in scientific notation from 1e21 (and
rounds above 2^53); whole numbers up to 2^53 are rendered as written, and
larger ones fail: quote them in the values file (e.g., `"12345678901234567890"`)
or set them with `--set-string`. Also used for the provider and group values
under `auth`, which tesk-api compares as text.
*/}}
{{- define "tesk.secretValue" -}}
{{- if and (kindIs "float64" .) (eq (floor .) .) -}}
{{- if and (lt . 9007199254740992.0) (gt . -9007199254740992.0) -}}
{{- printf "%.0f" . | quote -}}
{{- else -}}
{{- fail "a value (a secret, or a provider or group value under auth) is a number too large to be exact: quote it in the values file or use --set-string" -}}
{{- end -}}
{{- else -}}
{{- quote . -}}
{{- end -}}
{{- end -}}

{{/*
The environment variables of tesk-api's tokens of allow-listed clients
(`auth.tokenClients`), as YAML entries of `env`, or nothing if the setting
is off. The names of the variables are only here. Fails if it is on without
mode auth (noauth leaves all endpoints open, so no token would be checked),
an issuer or a non-blank client ID. Client IDs are trimmed, blank ones left
out, and joined with commas, as tesk-api splits them; empty or null optional
keys leave tesk-api's defaults: the JWKS URI from the issuer's discovery
document, no audience, the claim client_id and the type at+jwt required.
*/}}
{{- define "tesk.tokenClientsEnv" -}}
{{- $tokenClients := default dict .Values.auth.tokenClients -}}
{{- if eq (toString $tokenClients.enabled) "true" -}}
{{- if ne (toString .Values.auth.mode) "auth" -}}
{{- fail (printf "auth.tokenClients.enabled needs auth.mode auth, not %q" (toString .Values.auth.mode)) -}}
{{- end -}}
{{- $clients := list -}}
{{- range (default list $tokenClients.clients) -}}
{{- with trim (toString .) -}}
{{- $clients = append $clients . -}}
{{- end -}}
{{- end -}}
{{- if or (not (include "tesk.isSet" $tokenClients.issuer)) (not $clients) -}}
{{- fail "auth.tokenClients.enabled needs auth.tokenClients.issuer and at least one client ID in auth.tokenClients.clients" -}}
{{- end -}}
{{- $requireAtJwt := "" -}}
{{- if not (kindIs "invalid" $tokenClients.requireAtJwt) -}}
{{- $requireAtJwt = lower (toString $tokenClients.requireAtJwt) -}}
{{- end -}}
{{- $variables := list
  (list "TESK_API_AUTHORISATION_SERVICE_CLIENTS_ENABLED" "true")
  (list "TESK_API_AUTHORISATION_SERVICE_CLIENTS_ISSUER" $tokenClients.issuer)
  (list "TESK_API_AUTHORISATION_SERVICE_CLIENTS_JWKS_URI" $tokenClients.jwksUri)
  (list "TESK_API_AUTHORISATION_SERVICE_CLIENTS_AUDIENCE" $tokenClients.audience)
  (list "TESK_API_AUTHORISATION_SERVICE_CLIENTS_CLIENT_CLAIM" $tokenClients.claim)
  (list "TESK_API_AUTHORISATION_SERVICE_CLIENTS_CLIENT_IDS" (join "," $clients))
  (list "TESK_API_AUTHORISATION_SERVICE_CLIENTS_REQUIRE_ACCESS_TOKEN_TYPE" $requireAtJwt) -}}
{{- range $variables }}
{{- if include "tesk.isSet" (index . 1) }}
- name: {{ index . 0 }}
  value: {{ include "tesk.secretValue" (index . 1) }}
{{- end }}
{{- end }}
{{- end -}}
{{- end -}}

{{/*
A probe of the API's container, as YAML, or nothing if it is disabled
(`enabled: false`): the values of the probe (`tesk.startupProbe`,
`tesk.readinessProbe` or `tesk.livenessProbe`) on top of the defaults,
which are set here. The default action of the probe is
`GET <ingress.path><tesk.tesApiBasePath>/service-info`: the API answers it
from a local file, without a backend. It is a check of the port instead if
the endpoint needs a token (`auth.mode: auth` with
`auth.serviceInfoPublic: false`). A probe with an action of its own
(`httpGet`, `tcpSocket`, `exec` or `grpc`) keeps that one.

Takes the root context (`root`) and the key of the probe (`name`).
*/}}
{{- define "tesk.probe" -}}
{{- $root := .root -}}
{{- $defaults := dict
  "startupProbe" (dict "periodSeconds" 5 "timeoutSeconds" 5 "failureThreshold" 60)
  "readinessProbe" (dict "periodSeconds" 10 "timeoutSeconds" 5 "failureThreshold" 3)
  "livenessProbe" (dict "periodSeconds" 20 "timeoutSeconds" 5 "failureThreshold" 3)
-}}
{{- $user := deepCopy (dig .name dict $root.Values.tesk | default dict) -}}
{{- if ne (toString (dig "enabled" true $user)) "false" -}}
{{- $_ := unset $user "enabled" -}}
{{- $probe := mergeOverwrite (deepCopy (index $defaults .name)) $user -}}
{{- $port := $root.Values.tesk.port | int -}}
{{- $needsToken := and (eq (toString $root.Values.auth.mode) "auth") (eq (lower (toString $root.Values.auth.serviceInfoPublic)) "false") -}}
{{- $key := "httpGet" -}}
{{- $action := dict "path" (printf "%s%s/service-info" (trimSuffix "/" (toString $root.Values.ingress.path)) (trimSuffix "/" ($root.Values.tesk.tesApiBasePath | default "/ga4gh/tes/v1"))) "port" $port -}}
{{- if $needsToken -}}
{{- $key = "tcpSocket" -}}
{{- $action = dict "port" $port -}}
{{- end -}}
{{- $own := false -}}
{{- range $candidate := list "httpGet" "tcpSocket" "exec" "grpc" -}}
{{- if hasKey $user $candidate -}}
{{- $own = true -}}
{{- end -}}
{{- end -}}
{{- if not $own -}}
{{- $_ := set $probe $key $action -}}
{{- else if hasKey $user $key -}}
{{- $_ := set $probe $key (mergeOverwrite $action (index $user $key)) -}}
{{- end -}}
{{ .name }}:
  {{- toYaml $probe | nindent 2 }}
{{- end -}}
{{- end -}}
