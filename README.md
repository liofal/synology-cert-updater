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

- Node.js (for commit hooks)
- Python 3.11+
- Docker (for local testing)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/[your-github-username]/synology-cert-updater.git
   cd synology-cert-updater
   ```

2. Install development dependencies:
   ```bash
   npm install
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
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

### Kubernetes

1. Create a namespace (optional):
   ```bash
   kubectl create namespace synology-updater
   ```

2. Deploy using the provided script:
   ```bash
   ./scripts/deploy.sh -n synology-updater
   ```

3. Create the required secrets:
   ```bash
   kubectl create secret generic synology-credentials \
     --from-literal=host=your-synology-host \
     --from-literal=username=your-username \
     --from-literal=password=your-password \
     -n synology-updater
   ```

### Using Released Versions

You can use specific released versions from GitHub Container Registry:

```yaml
image: ghcr.io/[your-github-username]/synology-cert-updater:1.0.0
```

## License

[MIT License](LICENSE)
