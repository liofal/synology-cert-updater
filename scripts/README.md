# Helm Chart Scripts & Usage

This directory contains helper scripts. The primary way to manage the Synology Certificate Updater deployment is now via the Helm chart located in the `../kube` directory.

## Prerequisites

- `helm` v3+ installed ([https://helm.sh/docs/intro/install/](https://helm.sh/docs/intro/install/))
- `kubectl` installed and configured to connect to your Kubernetes cluster
- Access to the target Kubernetes cluster and namespace

## Helm Chart Usage

The Helm chart manages the deployment of all necessary Kubernetes resources (CronJob, Job, RBAC, Secrets, etc.).

### Installation

To install the chart, use the `helm install` command. You **must** provide your Synology credentials.

```bash
# Example installation with required values set
helm install my-updater ../kube \
  --namespace synology \
  --create-namespace \
  --set synology.host="YOUR_SYNOLOGY_HOST:5001" \
  --set synology.username="YOUR_SYNOLOGY_USER" \
  --set synology.password="YOUR_SYNOLOGY_PASSWORD"

# Example using a pre-existing secret for credentials
helm install my-updater ../kube \
  --namespace synology \
  --create-namespace \
  --set secrets.existingCredentialsSecretName="my-manual-syno-secret"
```

**Important Configuration:**

- `synology.host`, `synology.username`, `synology.password`: Required if *not* using `secrets.existingCredentialsSecretName`.
- `secrets.existingCredentialsSecretName`: Set this to the name of a secret you created manually (containing `host`, `username`, `password` keys) if you don't want the chart to create its own credentials secret.
- `secrets.certificate`: Name of the secret containing the TLS certificate and key to be uploaded to Synology (default: `ingress-certmanager-tls`). Ensure this secret exists in the target namespace.
- `domainPattern`: The domain pattern for the certificate on Synology (default: `*.liofal.net`).
- `job.enabled`: Set to `false` if you don't need the one-off Job created (default: `true`).
- `cronJob.schedule`: Customize the CronJob schedule (default: `0 0 1 * *`).

Refer to `../kube/values.yaml` for all available configuration options.

### Manually Creating the Credentials Secret (Optional)

If you prefer to manage the Synology credentials secret outside of Helm, you can create it manually before installing the chart. Ensure the secret contains the keys `host`, `username`, and `password`.

Example using `kubectl`:
```bash
kubectl create secret generic my-manual-syno-secret \
  --namespace synology \
  --from-literal=host='YOUR_SYNOLOGY_HOST:5001' \
  --from-literal=username='YOUR_SYNOLOGY_USER' \
  --from-literal=password='YOUR_SYNOLOGY_PASSWORD'
```

Then, install the Helm chart using the `secrets.existingCredentialsSecretName` value:
```bash
helm install my-updater ../kube \
  --namespace synology \
  --set secrets.existingCredentialsSecretName="my-manual-syno-secret"
  # ... other values ...
```

### Upgrading

To upgrade an existing release with new configuration or a new chart version:

```bash
helm upgrade my-updater ../kube \
  --namespace synology \
  --set image.tag="new-version" # Example: update image tag
```

### Uninstallation

To remove the deployment:

```bash
helm uninstall my-updater --namespace synology
```

This will delete all resources created by the Helm chart installation (CronJob, Job, ServiceAccount, RBAC, and the credentials Secret *if created by the chart*). It will **not** delete secrets specified via `secrets.existingCredentialsSecretName` or the input certificate secret (`secrets.certificate`).

## Helper Scripts

### extract-k8s-cert.sh

Extracts `tls.crt` and `tls.key` from a Kubernetes TLS secret, useful for local testing or inspection.

```bash
./scripts/extract-k8s-cert.sh [options]
```

Options:
- `-s, --secret SECRET_NAME` - Name of the TLS secret (default: `ingress-certmanager-tls`)
- `-n, --namespace NAMESPACE` - Kubernetes namespace (default: `default`)
- `-o, --output OUTPUT_DIR` - Directory to save the certs (default: `./test/certs`)
- `-h, --help` - Show help message

Example:
```bash
# Extract from 'my-tls-secret' in namespace 'production' to './output'
./scripts/extract-k8s-cert.sh -s my-tls-secret -n production -o ./output
