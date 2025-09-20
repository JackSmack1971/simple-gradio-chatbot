# Project Folder Structure

> **Status**: 🔄 Pending - To be completed by Standards Authority
> **Phase**: Context Engineering - Standards Definition

## Complete Directory Structure

```
project-name/
├── .github/                    # GitHub workflows and templates
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── cd.yml
│   │   └── security.yml
│   └── ISSUE_TEMPLATE/
├── .roo/                       # Roo Code configuration
│   ├── context-engineering/    # Context documentation
│   ├── rules-code/            # Implementation rules
│   └── mcp.json               # MCP server config
├── docs/                       # Project documentation
│   ├── api/                   # API documentation
│   ├── deployment/            # Deployment guides
│   └── user/                  # User documentation
├── scripts/                    # Build and utility scripts
│   ├── build/
│   ├── deploy/
│   └── utils/
├── src/                        # Source code
│   ├── components/            # Reusable UI components
│   │   ├── common/           # Shared components
│   │   ├── forms/            # Form components
│   │   └── layout/           # Layout components
│   ├── pages/                # Page components
│   ├── hooks/                # Custom React hooks
│   ├── services/             # API and external services
│   ├── utils/                # Utility functions
│   ├── types/                # TypeScript type definitions
│   ├── constants/            # Application constants
│   └── assets/               # Static assets
├── tests/                     # Test files
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── e2e/                  # End-to-end tests
│   └── fixtures/             # Test data
├── public/                    # Public static files
└── config/                   # Configuration files
```

## File Naming Conventions

### Frontend Files
- **Components**: PascalCase (UserProfile.tsx)
- **Hooks**: camelCase with "use" prefix (useUserData.ts)
- **Utils**: camelCase (formatDate.ts)
- **Types**: PascalCase (UserTypes.ts)
- **Constants**: UPPER_SNAKE_CASE (API_ENDPOINTS.ts)

### Backend Files
- **Controllers**: PascalCase (UserController.ts)
- **Services**: PascalCase (EmailService.ts)
- **Models**: PascalCase (UserModel.ts)
- **Middleware**: camelCase (authMiddleware.ts)
- **Routes**: kebab-case (user-routes.ts)

## Directory Organization Rules

### Component Organization
```
components/
├── Button/
│   ├── Button.tsx           # Main component
│   ├── Button.test.tsx      # Component tests
│   ├── Button.stories.tsx   # Storybook stories
│   ├── Button.module.css    # Component styles
│   └── index.ts            # Re-export
```

### Service Organization
```
services/
├── api/
│   ├── users.ts            # User API calls
│   ├── auth.ts             # Authentication
│   └── types.ts            # API types
└── external/
    ├── payment.ts          # Payment service
    └── email.ts            # Email service
```

---
**Rationale**: Structure optimizes for maintainability, discoverability, and team collaboration.
