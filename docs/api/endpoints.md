# API Endpoints

## Endpoint Inventory

This document provides detailed specifications for all endpoints in the Social Share Scheduler system.

## Django Admin Endpoints

### POST /admin/posts/post/add/

**Purpose**: Create a new scheduled post

**Authentication**: Required (Django session)

**Form Fields**:

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `content` | textarea | Yes | Min length: 5 characters (if share_on_linkedin=True) |
| `share_now` | checkbox | Conditional | Either share_now or share_at required |
| `share_at` | datetime | Conditional | Either share_now or share_at required  Must be in future |
| `share_on_linkedin` | checkbox | No | Requires valid LinkedIn connection |

**Success Response**:
- HTTP 302 Redirect to `/admin/posts/post/`
- Post created in database
- Inngest event triggered (if scheduled)

**Error Responses**:
- HTTP 200 with form errors displayed
- Validation messages shown inline

**Example Validation Errors**:
```
- "You must select a time to share or share it now"
- "Content must be at least 5 characters long."
- "You must connect LinkedIn before sharing to LinkedIn."
```

**Business Logic**:
1. Validates either share_now or share_at is set
2. If share_on_linkedin=True, validates LinkedIn connection
3. Automatically sets user_id to logged-in user
4. Triggers Inngest event on save
5. Sets share_at to NOW if share_now=True

### GET /admin/posts/post/

**Purpose**: List all posts for current user

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Purpose |
|-----------|------|---------|
| `q` | string | Search filter (Django admin search) |
| `updated_at__gte` | date | Filter by updated date |

**Response**: HTML table with post list

**Columns** (Regular User):
- Content (truncated)
- Updated At

**Columns** (Superuser):
- Content (truncated)
- User
- Updated At

**Filtering**:
- Regular users: Only their own posts
- Superusers: All posts

### POST /admin/posts/post/{id}/change/

**Purpose**: Update an existing post

**Authentication**: Required (must be post owner or superuser)

**Readonly Fields** (if post published):
- `user`
- `content`
- `shared_at_linkedin`
- `share_on_linkedin`

**Business Logic**:
- Published posts cannot be edited
- Only post owner can edit (or superuser)
- Re-scheduling triggers new Inngest event

### POST /admin/posts/post/{id}/delete/

**Purpose**: Delete a post

**Authentication**: Required

**Permissions**:
- Post owner can delete if unpublished
- Superuser can delete any post
- Cannot delete published posts (as regular user)

**Success Response**:
- HTTP 302 Redirect to post list
- Post deleted from database

**Error Response**:
- HTTP 403 Forbidden (if no permission)

## OAuth Endpoints (django-allauth)

### GET /accounts/linkedin/login/

**Purpose**: Initiate LinkedIn OAuth flow

**Authentication**: None (public endpoint)

**Response**:
- HTTP 302 Redirect to LinkedIn OAuth server
- State parameter set in session

**Redirect URL**:
```
https://www.linkedin.com/oauth/authorize
  ?response_type=code
  &client_id={CLIENT_ID}
  &redirect_uri=http://localhost:8000/accounts/linkedin/login/callback/
  &state={STATE}
  &scope=openid%20profile%20w_member_social%20email
```

### GET /accounts/linkedin/login/callback/

**Purpose**: Handle OAuth callback from LinkedIn

**Authentication**: None (public endpoint)

**Query Parameters**:

| Parameter | Required | Description |
|-----------|----------|-------------|
| `code` | Yes | Authorization code from LinkedIn |
| `state` | Yes | State parameter for CSRF protection |

**Success Flow**:
1. Verify state parameter matches session
2. Exchange code for access token
3. Retrieve user profile from LinkedIn
4. Create or update SocialAccount
5. Store access token
6. Login user (Django session)
7. Redirect to `/admin/`

**Error Response**:
- HTTP 400 if invalid state
- HTTP 400 if LinkedIn rejects code

### POST /accounts/logout/

**Purpose**: Logout user

**Authentication**: Required

**Response**:
- HTTP 302 Redirect to login page
- Session cleared

## Inngest Webhook Endpoint

### POST /api/inngest

**Purpose**: Receive workflow execution requests from Inngest

**Authentication**:
- Dev: None
- Prod: Request signature validation

**Request Headers**:
```
Content-Type: application/json
X-Inngest-Signature: t=<timestamp>,s=<signature>  # Production only
```

**Request Body Structure**:
```json
{
  "ctx": {
    "run_id": "...",
    "function_id": "post_scheduler",
    "step_id": "...",
    "attempt": 1
  },
  "event": {
    "name": "posts/post.scheduled",
    "data": {
      "object_id": 123
    },
    "id": "posts/post.scheduled.123",
    "ts": 1675000000000
  },
  "steps": {},
  "use_api": true
}
```

**Response (Success)**:
```json
{
  "status": 200,
  "body": "done"  // or other return value from function
}
```

**Response (Error)**:
```json
{
  "status": 500,
  "body": null,
  "error": "Error message"
}
```

**Registered Workflow Functions**:

| Function ID | Trigger Event | Description |
|-------------|---------------|-------------|
| `post_scheduler` | `posts/post.scheduled` | Execute scheduled post publishing |

**Workflow Steps**:
1. `workflow-start` - Record start timestamp
2. Update `share_start_at` in database
3. `linkedin-sleeper-schedule` - Sleep until scheduled time
4. `linkedin-share-workflow-step` - Publish to LinkedIn
5. `workflow-end` - Record end timestamp
6. Update `share_complete_at` in database

**Error Handling**:
- Inngest automatically retries failed steps (up to 3 times by default)
- Exponential backoff between retries
- Errors logged to Inngest dashboard

## LinkedIn API Endpoints (External)

### POST https://api.linkedin.com/v2/ugcPosts

**Purpose**: Publish a post to LinkedIn

**Authentication**: OAuth 2.0 Bearer Token

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
X-Restli-Protocol-Version: 2.0.0
LinkedIn-Version: 202301  # API version
```

**Request Body**:
```json
{
  "author": "urn:li:person:{linkedin_user_id}",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": {
        "text": "Your post content here. Maximum 3000 characters."
      },
      "shareMediaCategory": "NONE"
    }
  },
  "visibility": {
    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
  }
}
```

**Field Descriptions**:

| Field | Description | Constraints |
|-------|-------------|-------------|
| `author` | LinkedIn user URN | Format: `urn:li:person:{uid}` |
| `lifecycleState` | Publication state | Always "PUBLISHED" |
| `shareCommentary.text` | Post content | Max 3000 chars |
| `shareMediaCategory` | Media type | "NONE" for text-only |
| `visibility` | Post visibility | "PUBLIC" or "CONNECTIONS" |

**Success Response** (201 Created):
```json
{
  "id": "urn:li:ugcPost:7123456789012345678"
}
```

**Error Responses**:

| Status | Error Code | Description | Solution |
|--------|------------|-------------|----------|
| 400 | BAD_REQUEST | Invalid request body | Check JSON structure |
| 401 | UNAUTHORIZED | Invalid/expired token | Re-authenticate user |
| 403 | FORBIDDEN | Insufficient permissions | Check OAuth scopes |
| 422 | UNPROCESSABLE_ENTITY | Content policy violation | Modify content |
| 429 | TOO_MANY_REQUESTS | Rate limit exceeded | Implement backoff |
| 500 | INTERNAL_ERROR | LinkedIn server error | Retry with backoff |

**Rate Limits**:
- Not publicly documented
- Varies by application and tier
- Implement exponential backoff on 429

## Endpoint Security Summary

| Endpoint | Auth Method | CSRF | Rate Limit | HTTPS |
|----------|-------------|------|------------|-------|
| Django Admin | Session | Yes | No | Dev: No, Prod: Yes |
| OAuth Callback | None (public) | State param | No | Dev: No, Prod: Yes |
| Inngest Webhook | Signature (prod) | No | Inngest-managed | Dev: No, Prod: Yes |
| LinkedIn API | Bearer token | N/A | LinkedIn-managed | Yes (always) |

## Testing Endpoints

### cURL Examples

**Login to Django Admin**:
```bash
# Get CSRF token
curl -c cookies.txt http://localhost:8000/admin/login/

# Login
curl -b cookies.txt -c cookies.txt \
  -d "username=admin&password=admin&csrfmiddlewaretoken=<TOKEN>" \
  http://localhost:8000/admin/login/
```

**Create Post**:
```bash
curl -b cookies.txt \
  -d "content=Test post&share_now=true&share_on_linkedin=true&csrfmiddlewaretoken=<TOKEN>" \
  http://localhost:8000/admin/posts/post/add/
```

**Trigger Inngest Event** (via Python):
```python
from scheduler.client import inngest_client
import inngest

inngest_client.send_sync(
    inngest.Event(
        name="posts/post.scheduled",
        id="test-event-1",
        data={"object_id": 123}
    )
)
```

**LinkedIn API Call**:
```bash
curl -X POST https://api.linkedin.com/v2/ugcPosts \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -H "X-Restli-Protocol-Version: 2.0.0" \
  -d '{
    "author": "urn:li:person:XXXXX",
    "lifecycleState": "PUBLISHED",
    "specificContent": {
      "com.linkedin.ugc.ShareContent": {
        "shareCommentary": {"text": "Test post"},
        "shareMediaCategory": "NONE"
      }
    },
    "visibility": {
      "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
    }
  }'
```

## Postman Collection

**Not Currently Available**

**Recommended for Future**:
- Export Postman collection with all endpoints
- Include environment variables for base URLs
- Add pre-request scripts for authentication
- Include example requests and responses

## Endpoint Changelog

### Future Additions

**Potential New Endpoints**:
- `GET /api/v1/posts/` - REST API for listing posts
- `GET /api/v1/posts/{id}/status/` - Check publishing status
- `POST /api/v1/webhooks/` - Register webhook for post events
- `GET /health/` - Health check endpoint
- `GET /ready/` - Readiness probe for Kubernetes
