"""Role-based access control.

Permissions are resource.action strings. Roles map to fixed permission sets:
- OWNER: everything
- ADMIN: everything except billing.manage and admin.access
- MEMBER: read-only on leads, conversations, analytics

check_permission() composes with require_plan() — an endpoint can demand both
a plan tier and a permission.
"""

import enum

from app.db.models import UserRole


class Permission(enum.StrEnum):
    LEADS_READ = "leads.read"
    LEADS_WRITE = "leads.write"
    CONVERSATIONS_READ = "conversations.read"
    POSTS_CREATE = "posts.create"
    POSTS_PUBLISH = "posts.publish"
    ADS_CREATE = "ads.create"
    ANALYTICS_VIEW = "analytics.view"
    BILLING_MANAGE = "billing.manage"
    CREDENTIALS_WRITE = "credentials.write"
    ADMIN_ACCESS = "admin.access"


_ALL = frozenset(Permission)

ROLE_PERMISSIONS: dict[UserRole, frozenset[Permission]] = {
    UserRole.OWNER: _ALL,
    UserRole.ADMIN: _ALL - {Permission.BILLING_MANAGE, Permission.ADMIN_ACCESS},
    UserRole.MEMBER: frozenset(
        {Permission.LEADS_READ, Permission.CONVERSATIONS_READ, Permission.ANALYTICS_VIEW}
    ),
}


def role_has_permission(role: UserRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())
