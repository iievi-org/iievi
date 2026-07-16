import type { FeatureName } from "@iievi/types";
import {
  BarChart3,
  FileClock,
  ImageIcon,
  type LucideIcon,
  Megaphone,
  MessageSquare,
  Settings,
  ToggleRight,
  Users,
} from "lucide-react";
import type { Route } from "next";

export interface NavItem {
  href: Route;
  label: string;
  icon: LucideIcon;
  /** Capability flag that must be true, else the item is gated/greyed. */
  feature?: FeatureName;
  /** Dynamic badge source (unread leads). */
  badge?: "leads";
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard/chat", label: "Chat", icon: MessageSquare },
  { href: "/dashboard/leads", label: "Leads", icon: Users, badge: "leads" },
  { href: "/dashboard/posts", label: "Posts", icon: ImageIcon, feature: "can_generate_posts" },
  { href: "/dashboard/ads", label: "Ads", icon: Megaphone, feature: "can_create_ads" },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

/** Platform-admin only (JWT admin claim). */
export const ADMIN_ITEMS: NavItem[] = [
  { href: "/dashboard/admin/audit-logs", label: "Audit Logs", icon: FileClock },
  { href: "/dashboard/admin/feature-flags", label: "Feature Flags", icon: ToggleRight },
];

/** Bottom tab bar on < 768px — five destinations. */
export const MOBILE_TABS: NavItem[] = [
  { href: "/dashboard/chat", label: "Chat", icon: MessageSquare },
  { href: "/dashboard/leads", label: "Leads", icon: Users, badge: "leads" },
  { href: "/dashboard/posts", label: "Posts", icon: ImageIcon, feature: "can_generate_posts" },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];
