# Contributing to HubbOps Platform

Thank you for your interest in contributing to HubbOps! We welcome contributions from the community to help make this the best Internal Developer Platform.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please treat everyone with respect and kindness.

## How to Contribute

### Reporting Bugs

1.  **Search existing issues** to see if the bug has already been reported.
2.  If not, **open a new issue** using the Bug Report template.
3.  Provide as much detail as possible, including steps to reproduce, expected behavior, and screenshots if applicable.

### Suggesting Enhancements

1.  **Open a new issue** using the Feature Request template.
2.  Describe the feature you'd like to see and why it would be useful.
3.  If possible, provide examples or mockups.

### Pull Requests

1.  **Fork the repository** and create a new branch for your feature or fix.
    ```bash
    git checkout -b feature/my-awesome-feature
    ```
2.  **Make your changes** and ensure they follow the project's coding style.
3.  **Run tests** (if available) to ensure your changes don't break anything.
4.  **Commit your changes** with descriptive commit messages.
    ```bash
    git commit -m "feat: add support for new service template"
    ```
    We follow [Conventional Commits](https://www.conventionalcommits.org/).
5.  **Push your branch** to your fork.
    ```bash
    git push origin feature/my-awesome-feature
    ```
6.  **Open a Pull Request** against the `main` branch of the original repository.

## Development Setup

Please refer to [docs/SETUP.md](docs/SETUP.md) for detailed instructions on setting up your local development environment.

## Project Structure

-   `backend/`: FastAPI application
-   `frontend/`: React application
-   `ops-cli/`: Python CLI for automation
-   `k8s/`: Kubernetes manifests for the platform
-   `config/`: Configuration templates

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
