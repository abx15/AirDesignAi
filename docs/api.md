# MotionMath AI: API Documentation

## Overview

MotionMath AI provides a comprehensive REST API for mathematical equation solving, user management, and analytics. The API is designed for high performance, security, and scalability.

## Base URL

- **Production**: `https://api.motionmath.ai`
- **Staging**: `https://api-staging.motionmath.ai`
- **Development**: `http://localhost:8000`

## Authentication

### JWT Token Authentication
All API endpoints (except public endpoints) require JWT authentication.

```http
Authorization: Bearer <jwt_token>
```

### Getting a Token
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Rate Limiting

- **Standard Users**: 1000 requests/hour
- **Premium Users**: 5000 requests/hour
- **Enterprise**: Custom limits

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Endpoints

### Authentication

#### Login
```http
POST /auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "username",
    "created_at": "2023-01-01T00:00:00Z"
  }
}
```

#### Register
```http
POST /auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "secure_password",
  "confirm_password": "secure_password"
}
```

#### Refresh Token
```http
POST /auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Logout
```http
POST /auth/logout
Authorization: Bearer <token>
```

### User Management

#### Get Current User
```http
GET /users/me
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "username",
  "preferences": {
    "theme": "dark",
    "language": "en",
    "notifications": true
  },
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

#### Update User
```http
PUT /users/me
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "username": "new_username",
  "preferences": {
    "theme": "light",
    "language": "es",
    "notifications": false
  }
}
```

#### Change Password
```http
POST /users/change-password
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "current_password": "old_password",
  "new_password": "new_password",
  "confirm_password": "new_password"
}
```

### Equation Solving

#### Solve Equation
```http
POST /equations/solve
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "equation": "2x + 5 = 15",
  "method": "algebraic",
  "steps": true,
  "explanation": true
}
```

**Response:**
```json
{
  "id": "uuid",
  "equation": "2x + 5 = 15",
  "solution": {
    "value": "x = 5",
    "type": "linear",
    "variables": ["x"],
    "confidence": 0.95
  },
  "steps": [
    {
      "step": 1,
      "description": "Subtract 5 from both sides",
      "equation": "2x = 10",
      "explanation": "2x + 5 - 5 = 15 - 5"
    },
    {
      "step": 2,
      "description": "Divide both sides by 2",
      "equation": "x = 5",
      "explanation": "2x/2 = 10/2"
    }
  ],
  "explanation": "To solve the equation 2x + 5 = 15, we first isolate the variable term by subtracting 5 from both sides, then divide by the coefficient 2.",
  "processing_time": 0.045,
  "created_at": "2023-01-01T00:00:00Z"
}
```

#### Solve Multiple Equations
```http
POST /equations/solve-batch
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "equations": [
    "2x + 5 = 15",
    "3y - 7 = 14",
    "z^2 = 25"
  ],
  "method": "algebraic",
  "steps": true
}
```

#### Validate Equation
```http
POST /equations/validate
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "equation": "2x + 5 = 15"
}
```

**Response:**
```json
{
  "valid": true,
  "type": "linear",
  "variables": ["x"],
  "complexity": "simple",
  "suggestions": []
}
```

### Gesture Recognition

#### Process Gesture
```http
POST /gestures/process
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "gesture_data": [
    {"x": 100, "y": 200, "timestamp": 1640995200},
    {"x": 105, "y": 205, "timestamp": 1640995201},
    {"x": 110, "y": 210, "timestamp": 1640995202}
  ],
  "canvas_size": {"width": 800, "height": 600},
  "interpretation": true
}
```

**Response:**
```json
{
  "id": "uuid",
  "gesture_type": "number",
  "recognized_value": "5",
  "confidence": 0.87,
  "equation_suggestion": "5x + 3 = 18",
  "processing_time": 0.123,
  "created_at": "2023-01-01T00:00:00Z"
}
```

#### Get Gesture History
```http
GET /gestures/history
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset (default: 0)
- `type`: Filter by gesture type

**Response:**
```json
{
  "gestures": [
    {
      "id": "uuid",
      "gesture_type": "number",
      "recognized_value": "5",
      "confidence": 0.87,
      "created_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

### Analytics

#### Get User Analytics
```http
GET /analytics/user
Authorization: Bearer <token>
```

**Query Parameters:**
- `period`: Time period (day, week, month, year)
- `start_date`: Start date (ISO 8601)
- `end_date`: End date (ISO 8601)

**Response:**
```json
{
  "period": "week",
  "equations_solved": 45,
  "gestures_processed": 123,
  "average_solve_time": 0.056,
  "success_rate": 0.92,
  "popular_equations": [
    {"equation": "2x + 5 = 15", "count": 12},
    {"equation": "x^2 = 25", "count": 8}
  ],
  "daily_stats": [
    {
      "date": "2023-01-01",
      "equations_solved": 6,
      "gestures_processed": 17
    }
  ]
}
```

#### Get System Analytics (Admin)
```http
GET /analytics/system
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "total_users": 10000,
  "active_users_today": 500,
  "equations_solved_today": 2500,
  "average_response_time": 0.045,
  "error_rate": 0.02,
  "system_health": "good",
  "resource_usage": {
    "cpu_usage": 0.45,
    "memory_usage": 0.67,
    "disk_usage": 0.34
  }
}
```

### Files and Media

#### Upload File
```http
POST /files/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request Body:**
```
file: <binary_data>
type: "equation_image" | "user_avatar" | "document"
```

**Response:**
```json
{
  "id": "uuid",
  "filename": "equation_123.jpg",
  "type": "equation_image",
  "size": 1024000,
  "url": "https://api.motionmath.ai/files/uuid",
  "uploaded_at": "2023-01-01T00:00:00Z"
}
```

#### Get File
```http
GET /files/{file_id}
Authorization: Bearer <token>
```

#### Delete File
```http
DELETE /files/{file_id}
Authorization: Bearer <token>
```

### Webhooks

#### Create Webhook
```http
POST /webhooks
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "url": "https://your-app.com/webhook",
  "events": ["equation.solved", "user.registered"],
  "secret": "webhook_secret",
  "active": true
}
```

#### List Webhooks
```http
GET /webhooks
Authorization: Bearer <token>
```

#### Delete Webhook
```http
DELETE /webhooks/{webhook_id}
Authorization: Bearer <token>
```

## Error Handling

### Error Response Format
All errors return a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    },
    "timestamp": "2023-01-01T00:00:00Z",
    "request_id": "uuid"
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Unprocessable Entity |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 502 | Bad Gateway |
| 503 | Service Unavailable |

### Error Codes

| Code | Description |
|------|-------------|
| VALIDATION_ERROR | Input validation failed |
| AUTHENTICATION_ERROR | Authentication failed |
| AUTHORIZATION_ERROR | Insufficient permissions |
| NOT_FOUND | Resource not found |
| RATE_LIMIT_EXCEEDED | Rate limit exceeded |
| PROCESSING_ERROR | Equation processing failed |
| GESTURE_NOT_RECOGNIZED | Gesture could not be recognized |
| SYSTEM_ERROR | Internal system error |

## SDKs and Libraries

### JavaScript/TypeScript
```bash
npm install @motionmath/api-client
```

```typescript
import { MotionMathAPI } from '@motionmath/api-client';

const client = new MotionMathAPI({
  baseURL: 'https://api.motionmath.ai',
  apiKey: 'your-api-key'
});

// Solve equation
const result = await client.equations.solve({
  equation: '2x + 5 = 15',
  steps: true
});

// Process gesture
const gesture = await client.gestures.process({
  gestureData: [...],
  canvasSize: { width: 800, height: 600 }
});
```

### Python
```bash
pip install motionmath-python
```

```python
from motionmath import MotionMathClient

client = MotionMathClient(
    base_url='https://api.motionmath.ai',
    api_key='your-api-key'
)

# Solve equation
result = client.equations.solve(
    equation='2x + 5 = 15',
    steps=True
)

# Process gesture
gesture = client.gestures.process(
    gesture_data=[...],
    canvas_size={'width': 800, 'height': 600}
)
```

## Testing

### API Testing Examples

#### Using curl
```bash
# Login
curl -X POST https://api.motionmath.ai/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Solve equation
curl -X POST https://api.motionmath.ai/equations/solve \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"equation": "2x + 5 = 15", "steps": true}'
```

#### Using Postman
Import the Postman collection from `docs/postman-collection.json`.

### Performance Testing

#### Load Testing Script
```javascript
// k6 load test script
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 0 },
  ],
};

export default function () {
  let response = http.post('https://api.motionmath.ai/equations/solve', {
    equation: '2x + 5 = 15',
    steps: true
  }, {
    headers: {
      'Authorization': 'Bearer <token>',
      'Content-Type': 'application/json',
    },
  });
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  sleep(1);
}
```

## Changelog

### v2.0.0 (2023-01-01)
- Added gesture recognition endpoints
- Improved equation solving algorithms
- Enhanced error handling
- Added analytics endpoints

### v1.5.0 (2022-12-01)
- Added batch equation processing
- Improved rate limiting
- Added webhook support
- Enhanced user management

### v1.0.0 (2022-10-01)
- Initial API release
- Basic equation solving
- User authentication
- File upload support

## Support

### Documentation
- [Getting Started](docs/getting-started.md)
- [SDK Documentation](docs/sdks.md)
- [Troubleshooting](docs/troubleshooting.md)

### Community
- GitHub Issues: https://github.com/your-org/motionmath-ai/issues
- Discord: https://discord.gg/motionmath
- Stack Overflow: https://stackoverflow.com/questions/tagged/motionmath

### Support Team
- Email: api-support@motionmath.ai
- Status Page: https://status.motionmath.ai
- Twitter: @MotionMathAPI

## License

This API is licensed under the MIT License. See [LICENSE](../LICENSE) for details.
