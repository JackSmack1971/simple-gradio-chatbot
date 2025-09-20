# Git Workflow & Conventions

> **Status**: 🔄 Pending - To be completed by Standards Authority
> **Phase**: Context Engineering - Standards Definition

## Branching Strategy

### GitFlow Model
```
main (production)
├── develop (integration)
    ├── feature/user-authentication
    ├── feature/payment-integration
    ├── hotfix/critical-security-fix
    └── release/v1.2.0
```

### Branch Naming Conventions
- **Feature**: `feature/ticket-number-brief-description`
- **Bugfix**: `bugfix/ticket-number-brief-description`
- **Hotfix**: `hotfix/ticket-number-brief-description`
- **Release**: `release/version-number`

## Commit Message Standards

### Conventional Commits Format
```
type(scope): brief description

Detailed explanation of what changed and why.

Closes #123
```

### Commit Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting)
- **refactor**: Code refactoring
- **test**: Adding or modifying tests
- **chore**: Build process or auxiliary tool changes

### Examples
```
feat(auth): add JWT token refresh mechanism

Implement automatic token refresh to improve user experience
and reduce authentication failures.

- Add refresh token storage
- Implement background refresh logic
- Update API error handling

Closes #456
```

## Pull Request Standards

### PR Title Format
- Follow same format as commit messages
- Include ticket number when applicable

### PR Description Template
```
## Description
Brief description of changes

## Changes Made
- [ ] Change 1
- [ ] Change 2

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Breaking changes documented
```

## Code Review Process

### Review Requirements
- **Minimum Reviewers**: 2 for main features, 1 for minor changes
- **Required Checks**: All CI/CD checks must pass
- **Merge Strategy**: Squash and merge for clean history

---
**Automation**: GitHub Actions enforce all conventions and requirements.
