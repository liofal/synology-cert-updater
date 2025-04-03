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

Deployment is managed via the Helm chart located in the `kube/` directory.

### Prerequisites

- `helm` v3+ installed ([https://helm.sh/docs/intro/install/](https://helm.sh/docs/intro/install/))
- `kubectl` installed and configured to connect to your Kubernetes cluster

### Installation

Install the chart using `helm install`. You must provide your Synology credentials either directly via `--set` arguments or by referencing a pre-existing secret.

```bash
# Example installation setting credentials directly
helm install my-updater ./kube \
  --namespace synology \
  --create-namespace \
  --set synology.host="YOUR_SYNOLOGY_HOST:5001" \
  --set synology.username="YOUR_SYNOLOGY_USER" \
  --set synology.password="YOUR_SYNOLOGY_PASSWORD"

# Example using a pre-existing secret for credentials
# (Create the secret first, e.g., 'my-manual-syno-secret')
helm install my-updater ./kube \
  --namespace synology \
  --create-namespace \
  --set secrets.existingCredentialsSecretName="my-manual-syno-secret"
```

For detailed configuration options, upgrade instructions, and uninstallation steps, please refer to the [Helm Chart Usage documentation](./scripts/README.md#helm-chart-usage).

### Using Released Versions

You can use specific released versions from GitHub Container Registry:

```yaml
image: ghcr.io/[your-github-username]/synology-cert-updater:1.0.0
```

## License

[MIT License](LICENSE)
