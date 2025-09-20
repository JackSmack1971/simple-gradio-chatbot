# Detailed Database Schema

> **Status**: 🔄 Pending - To be completed by Architecture Oracle
> **Phase**: Context Engineering - Architecture Design

## Database Design Principles

### Normalization Strategy
- **Target**: 3NF with performance denormalization where justified
- **Rationale**: Balance data integrity with query performance
- **Trade-offs**: Storage vs query complexity analysis

### Naming Conventions
- **Tables**: snake_case, plural nouns (users, order_items)
- **Columns**: snake_case, descriptive names
- **Indexes**: idx_tablename_columnname
- **Foreign Keys**: fk_tablename_referenced_table

## Core Tables

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at);
```

### Relationships & Constraints
<!-- Architecture Oracle will define all tables, relationships, and constraints -->

## Data Integrity Rules

### Business Logic Constraints
- **Email Uniqueness**: Enforced at database level
- **Password Requirements**: Minimum length validation in application
- **Role Validation**: Enum constraint on valid roles

### Referential Integrity
- **Foreign Key Constraints**: All relationships enforced
- **Cascade Rules**: Defined for each relationship
- **Orphan Prevention**: Strategies for data cleanup

## Performance Optimization

### Indexing Strategy
| Table | Column(s) | Type | Purpose |
|-------|-----------|------|---------|
| | | | |

### Query Optimization
- **Common Queries**: Identified and optimized
- **Execution Plans**: Analyzed and documented
- **Performance Targets**: Response time requirements

---
**Schema Evolution**: Migration scripts and versioning strategy documented.
