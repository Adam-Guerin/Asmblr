# Contributing to Asmblr

Thank you for your interest in contributing to Asmblr! This document provides guidelines for contributors to help maintain code quality and ensure a smooth collaboration process.

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- Ollama installed and running
- Git
- Docker (optional, for containerized development)

### Setup Steps
1. Fork the repository
2. Clone your fork locally
3. Create a virtual environment: `python -m venv .venv`
4. Activate the environment: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
5. Install dependencies: `pip install -r requirements.txt`
6. Copy `.env.example` to `.env` and configure as needed
7. Run the setup script: `python setup.py`

## 📋 Development Workflow

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Changes
- Follow the existing code style and patterns
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass: `pytest`

### 3. Commit Changes
Use clear, descriptive commit messages:
```bash
git commit -m "feat: add new feature for XYZ"
git commit -m "fix: resolve issue with ABC"
git commit -m "docs: update installation guide"
```

### 4. Create Pull Request
- Push your branch to your fork
- Create a pull request with a clear description
- Link any relevant issues
- Wait for code review

## 🏗️ Code Standards

### Python Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Keep functions focused and small
- Add docstrings for public functions and classes
- Use meaningful variable and function names

### Code Organization
- Keep related functionality together
- Use clear module structure
- Avoid circular imports
- Separate concerns properly

### Testing
- Write tests for new features
- Ensure test coverage remains high
- Use descriptive test names
- Test both success and failure cases

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_specific.py

# Run with verbose output
pytest -v
```

### Test Structure
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- End-to-end tests in `tests/e2e/`
- Performance tests in `tests/performance/`

## 📚 Documentation

### Types of Documentation
- **README.md**: Project overview and quick start
- **API docs**: Generated from docstrings
- **User guides**: Step-by-step tutorials
- **Developer docs**: Architecture and development guides

### Documentation Standards
- Use clear, concise language
- Include code examples
- Keep documentation up to date
- Use consistent formatting

## 🐛 Bug Reports

### Reporting Bugs
1. Check existing issues first
2. Use the bug report template
3. Provide clear steps to reproduce
4. Include system information
5. Add relevant logs or screenshots

### Bug Report Template
```markdown
## Description
Brief description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Windows 10, macOS 12.0, Ubuntu 20.04]
- Python version: [e.g., 3.9.0]
- Asmblr version: [e.g., 1.0.0]

## Additional Context
Any other relevant information
```

## 💡 Feature Requests

### Requesting Features
1. Check existing issues and discussions
2. Use the feature request template
3. Describe the use case clearly
4. Explain why it's valuable
5. Consider implementation suggestions

### Feature Request Template
```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why this feature is needed and how it would be used

## Proposed Solution
How you envision the feature working

## Alternatives Considered
Other approaches you've thought about

## Additional Context
Any other relevant information
```

## 🔧 Code Review Process

### Review Guidelines
- Be constructive and respectful
- Focus on code quality and design
- Ask questions if something is unclear
- Suggest improvements when possible
- Acknowledge good work

### Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No breaking changes (unless intended)
- [ ] Security considerations addressed
- [ ] Performance impact considered

## 🚀 Release Process

### Version Management
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version numbers in appropriate files
- Create release notes
- Tag releases in Git

### Release Steps
1. Update version numbers
2. Update CHANGELOG.md
3. Create release tag
4. Generate release notes
5. Publish release

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Avoid personal attacks or criticism
- Maintain professional communication

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Pull Requests**: Code contributions and reviews

### Getting Help
- Check documentation first
- Search existing issues and discussions
- Create a new issue if needed
- Be patient with responses

## 🏆 Recognition

### Contributor Recognition
- Contributors are acknowledged in releases
- Notable contributions are highlighted
- Community members are celebrated

### Ways to Contribute
- Code contributions
- Bug reports and testing
- Documentation improvements
- Community support
- Design and feedback

## 📄 Legal

### License
- All contributions are licensed under the MIT License
- Contributors retain copyright to their work
- By contributing, you agree to the license terms

### CLA (Contributor License Agreement)
- Currently not required
- May be implemented in the future if needed

## 🔄 Maintenance

### Project Maintainers
- Review and merge pull requests
- Manage issues and discussions
- Plan releases and roadmap
- Ensure code quality standards

### Maintenance Tasks
- Regular dependency updates
- Security vulnerability checks
- Performance monitoring
- Documentation updates

## 📞 Contact

### Getting in Touch
- Create an issue for bugs or features
- Start a discussion for questions
- Mention maintainainers for urgent matters

### Project Leadership
- Project maintainers are listed in README.md
- Technical decisions are made collaboratively
- Community input is valued and considered

---

Thank you for contributing to Asmblr! Your contributions help make this project better for everyone. 🎉
