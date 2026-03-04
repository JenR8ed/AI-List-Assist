# Contributing to AI List Assist 🤝

Thank you for your interest in contributing to AI List Assist! This document provides guidelines and best practices for contributing to the project.

## 📜 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Issue Reporting](#issue-reporting)

## 🤝 Code of Conduct

This project values professionalism, respect, and constructive collaboration. Please:

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a positive community
- Report inappropriate behavior

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Git
- Docker (optional, for containerized development)
- Google Cloud API access
- eBay Developer account

### Initial Setup

1. **Fork the repository** (if you don't have write access)
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/AI-List-Assist.git
   cd AI-List-Assist
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

5. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

6. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 💻 Development Workflow

### Branch Naming Convention

- `feature/` - New features (e.g., `feature/multi-platform-support`)
- `bugfix/` - Bug fixes (e.g., `bugfix/valuation-calculation`)
- `hotfix/` - Urgent production fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or updates

### Commit Message Guidelines

Follow conventional commit format:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(valuation): add support for completed listings analysis

fix(ebay-api): handle rate limiting with exponential backoff

docs(readme): update installation instructions for WSL
```

## 💯 Coding Standards

### Python Style Guide

- Follow **PEP 8** style guidelines
- Use **type hints** for function signatures
- Maximum line length: **88 characters** (Black formatter default)
- Use descriptive variable and function names
- Add docstrings for all classes and public methods

### Code Quality Tools

```bash
# Format code with Black
black .

# Lint with flake8
flake8 .

# Type checking with mypy
mypy .

# Sort imports with isort
isort .
```

### Documentation Standards

- Use Google-style docstrings:

```python
def calculate_valuation(item_data: dict, market_history: list) -> float:
    """Calculate valuation score for a resale item.
    
    Args:
        item_data: Dictionary containing item attributes
        market_history: List of recent sold items
        
    Returns:
        Valuation score between 0-10
        
    Raises:
        ValueError: If required item data is missing
    """
    pass
```

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_valuation.py

# Run tests matching pattern
pytest -k "test_ebay"
```

### Writing Tests

- Write unit tests for all new functionality
- Maintain or improve code coverage
- Use descriptive test names
- Mock external API calls
- Test edge cases and error conditions

**Example Test:**

```python
import pytest
from services.valuation import ValuationService


class TestValuationService:
    def test_calculate_resale_score_valid_data(self):
        """Test resale score calculation with valid market data."""
        service = ValuationService()
        score = service.calculate_resale_score(
            avg_price=50.0,
            sold_count=20,
            days=30
        )
        assert 0 <= score <= 10
        
    def test_calculate_resale_score_missing_data(self):
        """Test that missing data raises ValueError."""
        service = ValuationService()
        with pytest.raises(ValueError):
            service.calculate_resale_score(avg_price=None)
```

## 📤 Submitting Changes

### Pull Request Process

1. **Update your branch** with latest main:
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-branch
   git rebase main
   ```

2. **Run tests and linting**:
   ```bash
   pytest
   black .
   flake8 .
   ```

3. **Push to your fork**:
   ```bash
   git push origin your-branch
   ```

4. **Create Pull Request** on GitHub:
   - Use the PR template
   - Link related issues
   - Provide clear description
   - Add screenshots for UI changes

5. **Address review feedback**:
   - Make requested changes
   - Push additional commits
   - Respond to comments

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts
- [ ] PR description is clear and complete

## 🐛 Issue Reporting

### Before Creating an Issue

1. Search existing issues to avoid duplicates
2. Check if the issue exists in the latest version
3. Gather relevant information (logs, screenshots, etc.)

### Bug Reports

Use the bug report template and include:

- Clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Environment details
- Error logs
- Screenshots if applicable

### Feature Requests

Use the feature request template and include:

- Problem statement
- Proposed solution
- Use case and benefits
- Alternative approaches considered

## 📁 Project Structure

```
AI-List-Assist/
├── services/          # Core service modules
├── routes/            # Flask routes
├── templates/         # HTML templates
├── static/            # CSS, JS, images
├── tests/             # Test files
├── docs/              # Documentation
├── migrations/        # Database migrations
├── config/            # Configuration files
└── scripts/           # Utility scripts
```

## ❓ Questions?

If you have questions about contributing:

- Open a discussion in the Issues tab
- Check existing documentation
- Review the [README](README.md)
- Contact [@JenR8ed](https://github.com/JenR8ed)

## 🚀 Areas for Contribution

We especially welcome contributions in:

- 🐛 Bug fixes and error handling
- 📝 Documentation improvements
- 🧪 Test coverage expansion
- 🌐 Multi-platform marketplace support
- 📦 Performance optimization
- 🎨 UI/UX enhancements
- 🔌 API integration improvements

---

Thank you for contributing to AI List Assist! 🎉
