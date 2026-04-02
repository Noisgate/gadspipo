# Background Tasks & Scheduling

Background jobs for periodic syncing of Google Ads data.

## Jobs

### Daily Campaign Sync
- **Trigger:** Cron job at 6 AM UTC (configurable)
- **Function:** `sync_all_campaigns()`
- **What it does:**
  - Fetch all active Google Ads accounts for all users
  - For each account, fetch campaigns from Google Ads API
  - Create or update campaigns in database
  - Store daily metrics (impressions, clicks, conversions, cost)
  - Calculate derived metrics (CTR, CPA, ROAS)

### Scheduler Health Check
- **Trigger:** Every 5 minutes
- **Function:** Just logs heartbeat
- **Purpose:** Ensure scheduler is alive

## Architecture

```
startup event
  ↓
start_scheduler()
  ↓
APScheduler (background thread)
  ├─ Daily Sync @ 6 AM
  ├─ Health Check @ 5 min intervals
  └─ (More jobs can be added)

User makes request
  ↓
endpoint calls sync_account(account_id)
  ↓
sync_worker triggers campaign sync
  ↓
Returns stats to user

shutdown event
  ↓
stop_scheduler()
  ↓
Close all resources
```

## Sync Process

1. **Query active accounts** from `google_ads_accounts` where `is_active=true`
2. **For each account:**
   - Create Google Ads client with stored refresh token
   - Fetch campaigns via `GoogleAdsClientWrapper.get_campaigns()`
   - For each campaign:
     - Check if exists in DB (by google_campaign_id)
     - Update or create campaign record
     - Add today's metrics (impressions, clicks, etc)
     - Calculate CTR, CPC, ROAS
3. **Commit to database**
4. **Log results** (created, updated, errors)

## Manual Sync

Users can manually trigger sync for an account:

```bash
POST /api/v1/campaigns/sync/{account_id}
Authorization: Bearer {jwt_token}
```

Response:
```json
{
  "status": "success",
  "account_id": "123e4567-e89b-12d3-a456-426614174000",
  "stats": {
    "fetched": 45,
    "created": 5,
    "updated": 40,
    "errors": 0
  }
}
```

## Configuration

In `.env`:

```
SCHEDULER_ENABLED=true          # Enable/disable scheduler
SYNC_SCHEDULE_HOUR=6            # UTC hour for daily sync (0-23)
```

## Monitoring

Get scheduler status:

```python
from tasks.scheduler import get_scheduler_status

status = get_scheduler_status()
# {
#   "running": true,
#   "jobs_count": 2,
#   "jobs": [
#     {
#       "id": "sync_campaigns_daily",
#       "name": "Daily Google Ads Sync",
#       "trigger": "cron[hour='6']",
#       "next_run": "2024-03-24T06:00:00+00:00"
#     }
#   ]
# }
```

## Error Handling

- If account has invalid refresh token → logs error, skips account
- If Google Ads API fails → logs error, continues with next account
- If database commit fails → logs error, rollback changes
- All errors are logged but don't stop the scheduler

## Future Enhancements

- Email notifications on sync completion
- Sync status tracking (last_sync_at, last_sync_status)
- Exponential backoff for failed accounts
- Partial sync (only updated campaigns)
- Webhook notifications to frontend
