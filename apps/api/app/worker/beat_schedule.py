"""Celery Beat schedule — every recurring job on the platform, in one place.

Interval choices are part of the product contract:
- publish check every 60s: a post scheduled for 09:00 goes out by 09:01
- follow-up sequencing every 5 min: outreach cadence tolerance
- ad sync every 6h: Meta insights lag makes tighter polling pointless
- usage reset at 00:00 UTC on the 1st: new MonthlyUsage rows for everyone
- onboarding cleanup daily 03:00 UTC: quiet hours in the primary market (IST)
- credential health weekly: expired tokens are surfaced before they break a publish
- DLQ check every 15 min / circuit check every 60s: ops early-warning signals
"""

from celery.schedules import crontab

BEAT_SCHEDULE: dict[str, dict[str, object]] = {
    "posts-publish-scheduled": {
        "task": "posts.check_scheduled",
        "schedule": 60.0,
        "options": {"queue": "post_publishing"},
    },
    "leads-followup-sequencing": {
        "task": "leads.followup_sequencing",
        "schedule": 300.0,
        "options": {"queue": "lead_outreach"},
    },
    "ads-performance-sync": {
        "task": "ads.sync_performance",
        "schedule": crontab(minute=0, hour="*/6"),
        "options": {"queue": "ad_management"},
    },
    "billing-monthly-usage-reset": {
        "task": "billing.monthly_usage_reset",
        "schedule": crontab(minute=0, hour=0, day_of_month="1"),
        "options": {"queue": "usage_tracking"},
    },
    "onboarding-cleanup-expired-sessions": {
        "task": "onboarding.cleanup_expired_sessions",
        "schedule": crontab(minute=0, hour=3),
        "options": {"queue": "usage_tracking"},
    },
    "credentials-weekly-health-check": {
        "task": "credentials.health_check",
        "schedule": crontab(minute=0, hour=4, day_of_week="mon"),
        "options": {"queue": "usage_tracking"},
    },
    # Weekly owner performance report — Monday 9:00am IST == 03:30 UTC.
    "reports-weekly-performance": {
        "task": "reports.generate_weekly_performance",
        "schedule": crontab(minute=30, hour=3, day_of_week="mon"),
        "options": {"queue": "usage_tracking"},
    },
    "channels-sync-tiktok-comments": {
        "task": "channels.sync_tiktok_comments",
        "schedule": crontab(minute=15),  # hourly at :15
        "options": {"queue": "lead_outreach"},
    },
    "ops-check-dlq-size": {
        "task": "ops.check_dlq_size",
        "schedule": 900.0,  # every 15 minutes
        "options": {"queue": "usage_tracking"},
    },
    "ops-monitor-circuits": {
        "task": "ops.monitor_circuits",
        "schedule": 60.0,
        "options": {"queue": "usage_tracking"},
    },
}
