{{/*
Expand the name of the chart.
*/}}
{{- define "synology-cert-updater.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "synology-cert-updater.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Determine the name of the credentials secret to use.
Uses existingCredentialsSecretName if provided, otherwise generates one.
*/}}
{{- define "synology-cert-updater.credentialsSecretName" -}}
{{- .Values.secrets.existingCredentialsSecretName | default (printf "%s-credentials" (include "synology-cert-updater.fullname" .)) }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "synology-cert-updater.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "synology-cert-updater.labels" -}}
helm.sh/chart: {{ include "synology-cert-updater.chart" . }}
{{ include "synology-cert-updater.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "synology-cert-updater.selectorLabels" -}}
app.kubernetes.io/name: {{ include "synology-cert-updater.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "synology-cert-updater.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "synology-cert-updater.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Define the container spec for the updater job/cronjob
Accepts a dictionary as context, expecting a 'dryRun' boolean key.
*/}}
{{- define "synology-cert-updater.containerSpec" -}}
name: {{ include "synology-cert-updater.name" .Chart }} # Use .Chart here as the top-level context is passed
image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
imagePullPolicy: {{ .Values.image.pullPolicy }}
env:
- name: SYNOLOGY_HOST
  valueFrom:
    secretKeyRef:
      name: {{ include "synology-cert-updater.credentialsSecretName" .Chart | quote }} # Use .Chart here
      key: host
- name: SYNOLOGY_USER
  valueFrom:
    secretKeyRef:
      name: {{ include "synology-cert-updater.credentialsSecretName" .Chart | quote }} # Use .Chart here
      key: username
- name: SYNOLOGY_PASS
  valueFrom:
    secretKeyRef:
      name: {{ include "synology-cert-updater.credentialsSecretName" .Chart | quote }} # Use .Chart here
      key: password
- name: DOMAIN_PATTERN
  value: {{ .Values.domainPattern | quote }}
- name: DRY_RUN
  value: {{ .dryRun | quote }} # Use the passed dryRun value
volumeMounts:
- name: cert-volume
  mountPath: /certs
  readOnly: true
resources:
  {{- toYaml .Values.commonJobSettings.resources | nindent 2 }}
securityContext:
  {{- toYaml .Values.securityContext | nindent 2 }}
{{- end }}
