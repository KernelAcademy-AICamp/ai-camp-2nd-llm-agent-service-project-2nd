# API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <token>
```

## Endpoints

### Health Check

#### GET /health
Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "service": "FastAPI Backend",
  "version": "0.1.0"
}
```

#### GET /health/db
Check database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-01T00:00:00"
}
```

### Authentication

#### POST /auth/register
Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password",
  "full_name": "Full Name"
}
```

**Response:**
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "full_name": "Full Name"
  }
}
```

#### POST /auth/login
Login with email or username.

**Request Body (form-data):**
- `username`: Email or username
- `password`: User password

**Response:**
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

#### POST /auth/logout
Logout (invalidate token on client side).

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

### User Management

#### GET /users/me
Get current user information.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "is_active": true,
  "is_verified": false,
  "is_superuser": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "last_login": "2024-01-01T00:00:00"
}
```

#### PUT /users/me
Update current user information.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "full_name": "New Name",
  "email": "newemail@example.com"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "newemail@example.com",
  "username": "username",
  "full_name": "New Name"
}
```

#### PUT /users/me/password
Change current user password.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword"
}
```

**Response:**
```json
{
  "message": "Password updated successfully"
}
```

#### DELETE /users/me
Delete current user account.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

#### GET /users (Admin Only)
Get all users (requires superuser privileges).

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "full_name": "Full Name",
    "is_active": true,
    "is_verified": false,
    "is_superuser": false,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

#### GET /users/{user_id} (Admin Only)
Get specific user by ID.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "is_active": true,
  "is_verified": false,
  "is_superuser": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Error message describing the issue"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- Default: 100 requests per minute per IP
- Can be configured via environment variables

## Pagination

List endpoints support pagination:
- `skip`: Number of records to skip
- `limit`: Maximum number of records to return

Example:
```
GET /api/v1/users?skip=20&limit=10
```

## Filtering and Sorting

(To be implemented based on specific requirements)

## Webhooks

(To be implemented based on specific requirements)