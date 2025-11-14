# Contributing to FastAPI Backend

Thank you for considering contributing to this project! This document provides guidelines and instructions for contributing.

## 🤝 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/fastapi-backend.git
   cd fastapi-backend
   ```
3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/original-owner/fastapi-backend.git
   ```
4. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 💻 Development Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install development dependencies:**
   ```bash
   make dev-install
   ```

3. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```

4. **Copy environment variables:**
   ```bash
   cp .env.example .env
   ```

## 📝 Development Workflow

### Before Starting Work

1. **Sync with upstream:**
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature
   ```

### While Developing

1. **Write clean code** following project conventions
2. **Add tests** for new functionality
3. **Update documentation** if needed
4. **Run tests locally:**
   ```bash
   make test
   ```

5. **Format and lint code:**
   ```bash
   make format
   make lint
   make type-check
   ```

### Committing Changes

1. **Write clear commit messages:**
   ```
   feat: add user profile endpoint

   - Add GET /users/profile endpoint
   - Include user preferences in response
   - Add tests for new endpoint
   ```

2. **Commit message format:**
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `style:` Code style changes (formatting)
   - `refactor:` Code refactoring
   - `test:` Test additions or fixes
   - `chore:` Maintenance tasks

3. **Keep commits atomic** - one logical change per commit

## 🧪 Testing Guidelines

### Writing Tests

- Place tests in `tests/` directory
- Mirror the app structure in test files
- Use descriptive test names
- Test both success and failure cases

### Test Structure

```python
async def test_feature_success_case():
    """Test that feature works correctly with valid input"""
    # Arrange
    # Act
    # Assert

async def test_feature_failure_case():
    """Test that feature handles errors appropriately"""
    # Arrange
    # Act
    # Assert
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_specific.py -v
```

## 📚 Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> dict:
    """
    Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When invalid input provided
    """
```

### API Documentation

- Update `docs/API.md` for new endpoints
- Keep OpenAPI schemas up to date
- Include request/response examples

## 🎨 Code Style

### Python Style Guide

- Follow PEP 8
- Use Black for formatting (line length: 88)
- Use isort for import sorting
- Type hints for all function signatures

### File Organization

```python
# 1. Standard library imports
import os
import sys

# 2. Third-party imports
from fastapi import FastAPI
from sqlalchemy import create_engine

# 3. Local imports
from app.core.config import settings
from app.models.user import User
```

### Naming Conventions

- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

## 🔄 Pull Request Process

1. **Update your branch:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push to your fork:**
   ```bash
   git push origin feature/your-feature
   ```

3. **Create Pull Request:**
   - Use clear, descriptive title
   - Reference related issues
   - Describe changes made
   - Include screenshots if UI changes

4. **PR Template:**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Tests pass locally
   - [ ] Added new tests
   - [ ] Updated documentation

   ## Related Issues
   Closes #123
   ```

5. **Address review feedback:**
   - Make requested changes
   - Push new commits
   - Respond to comments

## 🐛 Reporting Issues

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version)
- Error messages/logs

### Feature Requests

Include:
- Clear description of the feature
- Use case/motivation
- Proposed implementation (if any)
- Alternative solutions considered

## 📦 Dependencies

### Adding Dependencies

1. **Production dependencies:**
   ```bash
   pip install package-name
   pip freeze > requirements.txt
   ```

2. **Development dependencies:**
   - Add to `requirements.txt` with comment
   - Update `pyproject.toml` if using Poetry

3. **Document why** the dependency is needed

## 🚀 Release Process

1. **Version Bump:**
   - Update version in `app/core/config.py`
   - Update `CHANGELOG.md`

2. **Create Release:**
   - Tag the release: `git tag v1.0.0`
   - Push tags: `git push --tags`

## 🙋 Getting Help

- Check existing issues and documentation
- Ask in discussions or create an issue
- Join our community chat (if available)

## 🏆 Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- Project documentation

Thank you for contributing!