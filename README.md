# Synology Certificate Updater

A tool to automatically update certificates on Synology NAS devices from Kubernetes secrets.

## Features

- Automatically updates certificates on Synology NAS from Kubernetes secrets
- Runs as a Kubernetes CronJob or on-demand Job
- Supports wildcard certificates
- Dry run mode for testing

## CI/CD Pipeline

This repository uses GitHub Actions for CI/CD:

- **Build and Test**: Runs on every push to verify code quality
- **Semantic Release**: Automatically creates releases based on conventional commits
- **Container Publishing**: Publishes Docker images to GitHub Container Registry

## Development Workflow

### Prerequisites

- Python 3.11+
- `pip` (Python package installer)
- `pre-commit` ([https://pre-commit.com/](https://pre-commit.com/))
- Docker (for local testing, optional)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/[your-github-username]/synology-cert-updater.git
   cd synology-cert-updater
   ```

2. Install Python dependencies (including development tools):
   ```bash
   pip install -r requirements.txt
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   pre-commit install --hook-type commit-msg # For commitizen integration
   ```

### Commit Guidelines

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for semantic versioning.

Commit messages should follow this format:
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: A new feature (minor version bump)
- `fix`: A bug fix (patch version bump)
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Changes to build system or dependencies
- `ci`: Changes to CI configuration
- `chore`: Other changes that don't modify src or test files

Breaking changes should include `BREAKING CHANGE:` in the commit body or use `!` after the type.

## Deployment

Deployment is managed via the Helm chart located in the `kube/charts/synology-cert-updater` directory.

### Prerequisites

- `helm` v3+ installed ([https://helm.sh/docs/intro/install/](https://helm.sh/docs/intro/install/))
- `kubectl` installed and configured to connect to your Kubernetes cluster

### Installation

Install the chart using `helm install`. You must provide your Synology credentials, the target certificate secret name, and the domain pattern. Credentials can be set directly or by referencing a pre-existing secret.

```bash
# Example installation setting credentials directly
helm install my-updater ./kube/charts \
  --namespace synology \
  --create-namespace \
  --set synology.host="YOUR_SYNOLOGY_HOST:5001" \
  --set synology.username="YOUR_SYNOLOGY_USER" \
  --set synology.password="YOUR_SYNOLOGY_PASSWORD" \
  --set secrets.certificate="my-tls-secret" \
  --set commonJobSettings.domainPattern="*.example.com"

# Example using a pre-existing secret for credentials
# (Create the secret 'my-manual-syno-secret' with keys 'host', 'username', 'password' first)
helm install my-updater ./kube/charts \
  --namespace synology \
  --create-namespace \
  --set secrets.existingCredentialsSecretName="my-manual-syno-secret" \
  --set secrets.certificate="my-tls-secret" \
  --set commonJobSettings.domainPattern="*.example.com"

# Example for a scheduled CronJob (runs daily at 2 AM)
helm install my-updater ./kube/charts \
  --namespace synology \
  --create-namespace \
  --set secrets.existingCredentialsSecretName="my-manual-syno-secret" \
  --set secrets.certificate="my-tls-secret" \
  --set commonJobSettings.domainPattern="*.example.com" \
  --set cronJob.schedule="0 2 * * *" \
  --set job.enabled=false # Disable the one-off Job
```

### Helm Chart Configuration

The following table lists the configurable parameters of the `synology-cert-updater` chart and their default values.

| Parameter                                | Description                                                                                                                               | Default                                        |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `synology.host`                          | Hostname or IP address and port of the Synology NAS API (e.g., `your-nas.local:5001`). **Required**.                                       | `""`                                           |
| `synology.username`                      | Synology username for authentication. Required if `secrets.existingCredentialsSecretName` is not set.                                     | `""`                                           |
| `synology.password`                      | Synology password for authentication. Required if `secrets.existingCredentialsSecretName` is not set.                                     | `""`                                           |
| `secrets.certificate`                    | Name of the Kubernetes TLS secret containing the certificate and key to upload (e.g., `my-tls-secret`). **Required**.                       | `""`                                           |
| `secrets.credentials`                    | Name of the Kubernetes Secret to store Synology credentials. Created if `secrets.existingCredentialsSecretName` is empty.                 | `{{ .Release.Name }}-synology-credentials`     |
| `secrets.existingCredentialsSecretName`  | Name of an existing Secret containing Synology credentials (`host`, `username`, `password`). If set, `secrets.credentials` is not created. | `""`                                           |
| `job.enabled`                            | Enable the creation of a Kubernetes Job for immediate execution. Ignored if `cronJob.schedule` is set.                                    | `true`                                         |
| `job.dryRun`                             | Run the Job in dry-run mode (simulate changes without applying them).                                                                     | `false`                                        |
| `cronJob.schedule`                       | Kubernetes CronJob schedule (e.g., `"0 2 * * *"`). If set, a CronJob is created instead of a Job.                                         | `""`                                           |
| `cronJob.dryRun`                         | Run the CronJob pods in dry-run mode.                                                                                                     | `false`                                        |
| `cronJob.startingDeadlineSeconds`        | Deadline in seconds for starting the job if it misses its scheduled time.                                                                 | `null`                                         |
| `cronJob.concurrencyPolicy`              | Concurrency policy for the CronJob (`Allow`, `Forbid`, `Replace`).                                                                        | `Allow`                                        |
| `cronJob.successfulJobsHistoryLimit`     | Number of successful finished jobs to retain.                                                                                             | `3`                                            |
| `cronJob.failedJobsHistoryLimit`         | Number of failed finished jobs to retain.                                                                                                 | `1`                                            |
| `commonJobSettings.domainPattern`        | Pattern to identify the certificate on the Synology NAS to update (e.g., `*.example.com`). **Required**.                                  | `""`                                           |
| `commonJobSettings.ttlSecondsAfterFinished` | Time-to-live in seconds after the Job/CronJob pod finishes. Automatically cleans up finished Jobs.                                        | `3600` (1 hour)                                |
| `commonJobSettings.restartPolicy`        | Restart policy for the pod (`Never`, `OnFailure`).                                                                                        | `Never`                                        |
| `commonJobSettings.backoffLimit`         | Optional backoff limit for failed pods within a Job.                                                                                      | `4`                                            |
| `image.repository`                       | Container image repository.                                                                                                               | `ghcr.io/liofal/synology-cert-updater`         |
| `image.pullPolicy`                       | Container image pull policy.                                                                                                              | `IfNotPresent`                                 |
| `image.tag`                              | Container image tag.                                                                                                                      | Defaults to chart's `appVersion` (`0.1.0`)     |
| `resources`                              | Pod resource requests and limits.                                                                                                         | `{}`                                           |
| `nodeSelector`                           | Node selector configuration for pod assignment.                                                                                           | `{}`                                           |
| `tolerations`                            | Tolerations for pod scheduling.                                                                                                           | `[]`                                           |
| `affinity`                               | Affinity configuration for pod scheduling.                                                                                                | `{}`                                           |

### Using Released Versions

You can use specific released versions from GitHub Container Registry:

```yaml
image: ghcr.io/[your-github-username]/synology-cert-updater:1.0.0
```

## License

[MIT License](LICENSE)
