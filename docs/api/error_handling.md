# Error Handling

## Overview

Error handling in the Social Share Scheduler occurs at multiple layers: Django validation, Inngest workflow execution, and LinkedIn API integration.

## Django Validation Errors

### Post Model Validation

**Method**: `Post.clean()`

**Validation Rules**:

| Rule | Error Message | HTTP Response |
|------|---------------|---------------|
| Either `share_now` or `share_at` required | "You must select a time to share or share it now" | 200 (form redisplay) |
| Content length ≥ 5 for LinkedIn | "Content must be at least 5 characters long." | 200 (form redisplay) |
| User must have LinkedIn connection | "You must connect LinkedIn before sharing to LinkedIn." | 200 (form redisplay) |
| Post not already published | "Content is already shared on LinkedIn at {timestamp}." | 200 (form redisplay) |

**Error Display**:
- Errors shown inline in Django admin form
- Field-specific errors highlighted
- Generic errors shown at top of form

**Example Error Response** (HTML):
```html
<ul class="errorlist">
    <li>You must select a time to share or share it now</li>
</ul>
```

### Admin Permission Errors

**Error Types**:
- 403 Forbidden - User doesn't have permission
- 404 Not Found - Post doesn't exist or not accessible

**Permission Denied Scenarios**:
- Attempting to view other user's posts (non-superuser)
- Attempting to delete published post
- Attempting to edit published post (non-superuser)

## Inn gest Workflow Errors

### Error Handling Strategy

**Automatic Retries**: Inngest retries failed steps automatically

**Retry Configuration** (Inngest defaults):
- Maximum attempts: 3
- Backoff: Exponential (1s, 2s, 4s)
- Timeout: 5 minutes per step

### Common Workflow Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| Post not found | Post deleted before workflow execution | Workflow fails, no retry |
| LinkedIn not connected | User revoked LinkedIn access | Workflow fails, user must reconnect |
| LinkedIn API 401 | Token expired | Workflow retries, likely fails, user must reauthenticate |
| LinkedIn API 429 | Rate limit | Workflow retries with backoff, may succeed |
| LinkedIn API 500 | LinkedIn server error | Workflow retries, may succeed |
| Network timeout | Connection issue | Workflow retries, may succeed |

### Error Logging

**Logged to**:
- Inngest dashboard (workflow execution history)
- Django console output (if `DEBUG=True`)

**Log Format** (example):
```
Error in workflow step 'linkedin-share-workflow-step':
ValidationError: Could not share to linkedin.
```

## LinkedIn API Errors

### Error Response Format

```json
{
  "status": 401,
  "message": "Unauthorized"
}
```

### Error Codes

| HTTP Status | LinkedIn Error | Meaning | Handling |
|-------------|----------------|---------|----------|
| 400 | `BAD_REQUEST` | Invalid request | Log error, fail workflow |
| 401 | `UNAUTHORIZED` | Invalid/expired token | Fail workflow, notify user |
| 403 | `FORBIDDEN` | Insufficient permissions | Fail workflow, notify user |
| 422 | `UNPROCESSABLE_ENTITY` | Content validation failed | Fail workflow, notify user |
| 429 | `TOO_MANY_REQUESTS` | Rate limit exceeded | Retry with backoff |
| 500 | `INTERNAL_ERROR` | LinkedIn server error | Retry with backoff |
| 503 | `SERVICE_UNAVAILABLE` | LinkedIn maintenance | Retry with backoff |

### Error Handling in Code

**Location**: `helpers/linkedin.py`

```python
response = requests.post(endpoint, json=payload, headers=headers)
try:
    response.raise_for_status()
except:
    raise Exception("Invalid post, please try again later")
return response
```

**Issue**: Generic error message, no specific handling based on status code

**Recommendation**: Implement specific error handling:
```python
if response.status_code == 401:
    raise TokenExpiredError("LinkedIn token expired, please reconnect")
elif response.status_code == 429:
    raise RateLimitError("Rate limit exceeded, retry later")
elif response.status_code >= 500:
    raise LinkedInServerError("LinkedIn service unavailable")
else:
    response.raise_for_status()
```

## Database Errors

### Common Errors

| Error | Cause | Handling |
|-------|-------|----------|
| `IntegrityError` | Foreign key violation | Should not occur (Django prevents) |
| `OperationalError` | Database locked (SQLite) | Django retries automatically |
| `DatabaseError` | Connection lost | Re-raise as 500 error |

**SQLite Specific**: Write lock contention

**Solution**: Migrate to PostgreSQL for production

## HTTP Error Responses

### Django Admin

**Error Pages**:
- 400 Bad Request - Invalid form data
- 403 Forbidden - Permission denied
- 404 Not Found - Resource not found
- 500 Internal Server Error - Unhandled exception

**Debug Mode** (`DEBUG=True`):
- Full stack trace shown
- Local variables displayed
- SQL queries logged

**Production Mode** (`DEBUG=False`):
- Generic error page
- No sensitive information exposed
- Errors logged to server logs

### Custom Error Pages

**Not implemented**

**Recommended** (create templates):
- `templates/400.html`
- `templates/403.html`
- `templates/404.html`
- `templates/500.html`

## Error Monitoring

### Current State

**No error monitoring implemented**

### Recommendations

**Production Error Tracking**:
1. **Sentry** (recommended)
   ```python
   # settings.py
   import sentry_sdk
   from sentry_sdk.integrations.django import DjangoIntegration
   
   sentry_sdk.init(
       dsn="https://...",
       integrations=[DjangoIntegration()],
       traces_sample_rate=0.1,
   )
   ```

2. **Error Metrics**:
   - Error rate per endpoint
   - LinkedIn API error breakdown
   - Workflow failure reasons

3. **Alerting**:
   - Email on critical errors
   - Slack notifications for high error rates
   - PagerDuty for production incidents

## Error Recovery

### User-Initiated Recovery

**Failed LinkedIn Publishing**:
1. User sees post in admin with no `shared_at_linkedin`
2. User edits post
3. User sets new `share_at` time
4. New workflow triggered

**Expired LinkedIn Token**:
1. Workflow fails with 401 error
2. User sees error in Inngest dashboard (if access) or no published post
3. User navigates to `/accounts/linkedin/login/`
4. User re-authenticates
5. User re-schedules post

### Automatic Recovery

**Not implemented**

**Potential Improvements**:
- Exponential backoff with jitter for LinkedIn API
- Dead letter queue for permanently failed posts
- Automatic notification to user on workflow failure
- Webhook to send post back to draft state on failure

## Error Handling Best Practices

### Current Implementation

✅ Django validation errors displayed to user
✅ Inngest automatic retries
✅ Exception handling in LinkedIn API calls
❌ No centralized error logging
❌ No error monitoring/alerting
❌ Generic error messages (not user-friendly)
❌ No rollback mechanism for partial failures

### Recommended Improvements

1. **Structured Error Responses**:
   ```python
   class APIError(Exception):
       def __init__(self, message, code, retry_able=False):
           self.message = message
           self.code = code
           self.retryable = retryable
   ```

2. **User-Friendly Error Messages**:
   - "Your LinkedIn connection expired. Please reconnect and try again."
   - "LinkedIn is temporarily unavailable. Your post will be retried automatically."

3. **Error Context**:
   - Log user ID, post ID, timestamp
   - Include stack trace
   - Add relevant state information

4. **Graceful Degradation**:
   - Mark post as "failed" instead of leaving in limbo
   - Allow manual retry from admin interface
   - Queue failed posts for admin review

## Testing Error Handling

### Manual Testing

**Test Validation Errors**:
1. Create post without setting `share_now` or `share_at`
2. Verify error message displayed

**Test LinkedIn Connection Error**:
1. Create post with `share_on_linkedin=True`
2. Ensure no LinkedIn account linked
3. Verify error message

**Test LinkedIn API Error** (mock):
```python
# In tests, mock LinkedIn API to return 401
import unittest.mock as mock

with mock.patch('helpers.linkedin.requests.post') as mock_post:
    mock_post.return_value.status_code = 401
    # Trigger workflow, verify failure
```

### Automated Tests

**Not implemented**

**Recommended Test Cases**:
- Validation error display
- Permission denied scenarios
- LinkedIn API error handling
- Workflow retry logic
- Database error recovery
