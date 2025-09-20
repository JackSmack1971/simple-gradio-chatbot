# Complete API Contracts

> **Status**: 🔄 Pending - To be completed by Architecture Oracle
> **Phase**: Context Engineering - Architecture Design

## API Design Standards

### RESTful Conventions
- **Base URL**: `https://api.example.com/v1`
- **Authentication**: Bearer token in Authorization header
- **Content-Type**: `application/json`
- **Error Format**: RFC 7807 Problem Details

### Standard Response Format
```json
{
  "data": {},
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "requestId": "uuid",
    "version": "1.0.0"
  }
}
```

### Error Response Format
```json
{
  "type": "https://api.example.com/errors/validation",
  "title": "Validation Error",
  "status": 400,
  "detail": "Field 'email' is required",
  "instance": "/users",
  "errors": [
    {
      "field": "email",
      "code": "REQUIRED",
      "message": "Email is required"
    }
  ]
}
```

## Endpoint Specifications

### Authentication Endpoints
<!-- Architecture Oracle will specify every endpoint -->

#### POST /auth/login
**Purpose**: User authentication
**Request**:
```json
{
  "email": "string (required, email format)",
  "password": "string (required, min 8 chars)"
}
```
**Response 200**:
```json
{
  "data": {
    "token": "string (JWT)",
    "refreshToken": "string",
    "expiresIn": "number (seconds)",
    "user": {
      "id": "string",
      "email": "string",
      "role": "string"
    }
  }
}
```
**Error Responses**:
- 400: Invalid credentials format
- 401: Authentication failed
- 429: Too many attempts
- 500: Internal server error

---
**Coverage**: Every possible API interaction documented with exact request/response formats.
