/**
 * Zod schemas shared by frontend forms and API-client response validation.
 * Schemas here mirror the interfaces in @iievi/types and the backend's
 * Pydantic validation (apps/api) — keep the two in sync.
 */

import { z } from "zod";

// ---------------------------------------------------------------------------
// Error envelope + health
// ---------------------------------------------------------------------------

/** Error envelope every non-2xx response must match. */
export const apiErrorSchema = z.object({
  code: z.string(),
  message: z.string(),
  details: z.record(z.unknown()),
});
export type ApiErrorShape = z.infer<typeof apiErrorSchema>;

export const healthResponseSchema = z.object({
  status: z.literal("ok"),
  version: z.string(),
  commit: z.string(),
  uptime_seconds: z.number(),
});

export const dependencyStatusSchema = z.object({
  healthy: z.boolean(),
  detail: z.string(),
});

export const deepHealthResponseSchema = z.object({
  status: z.union([z.literal("ok"), z.literal("degraded")]),
  database: dependencyStatusSchema,
  redis: dependencyStatusSchema,
  celery: dependencyStatusSchema,
});

export const versionResponseSchema = z.object({
  commit: z.string(),
  deployed_at: z.string(),
  version: z.string(),
});

// ---------------------------------------------------------------------------
// Shared field regexes
// ---------------------------------------------------------------------------

/** 24-hour time, HH:MM (00:00–23:59). */
export const TIME_24H = /^([01]\d|2[0-3]):[0-5]\d$/;
/** #RGB or #RRGGBB hex colour. */
export const HEX_COLOR = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;

// ---------------------------------------------------------------------------
// Profile form schemas (mirror the backend Pydantic validators)
// ---------------------------------------------------------------------------

/** A single service offering. price_max must be >= price_min (backend .refine). */
export const serviceItemSchema = z
  .object({
    name: z.string().trim().min(1, "Name is required").max(255),
    price_min_paise: z.number().int().nonnegative(),
    price_max_paise: z.number().int().nonnegative(),
    unit: z.string().trim().min(1, "Unit is required").max(64),
  })
  .refine((s) => s.price_max_paise >= s.price_min_paise, {
    message: "Maximum price must be greater than or equal to the minimum price",
    path: ["price_max_paise"],
  });
export type ServiceItemInput = z.infer<typeof serviceItemSchema>;

/** One day's opening hours, or a closed day. */
export const workingHoursDaySchema = z
  .object({
    open: z.string().regex(TIME_24H, "Use 24-hour time, e.g. 09:00"),
    close: z.string().regex(TIME_24H, "Use 24-hour time, e.g. 18:00"),
    closed: z.boolean().optional(),
  })
  .refine((d) => d.closed === true || d.open < d.close, {
    message: "Closing time must be after opening time",
    path: ["close"],
  });

/** Working hours keyed by weekday (monday, tuesday, …). */
export const workingHoursSchema = z.record(z.string(), workingHoursDaySchema);
export type WorkingHoursInput = z.infer<typeof workingHoursSchema>;

/** Brand palette — hex colours only. */
export const brandColorsSchema = z.object({
  primary: z.string().regex(HEX_COLOR, "Enter a hex colour like #C8462C"),
  secondary: z.string().regex(HEX_COLOR, "Enter a hex colour like #C8462C").optional(),
  accent: z.string().regex(HEX_COLOR, "Enter a hex colour like #C8462C").optional(),
});
export type BrandColorsInput = z.infer<typeof brandColorsSchema>;

// ---------------------------------------------------------------------------
// Auth form schemas (mirror auth/schemas.py RegisterRequest / LoginRequest)
// ---------------------------------------------------------------------------

export const loginSchema = z.object({
  email: z.string().trim().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required").max(128),
});
export type LoginInput = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  business_name: z.string().trim().min(2, "Business name is too short").max(255),
  full_name: z.string().trim().min(2, "Your name is too short").max(255),
  email: z.string().trim().email("Enter a valid email address"),
  password: z
    .string()
    .min(10, "Use at least 10 characters")
    .max(128, "Password is too long"),
});
export type RegisterInput = z.infer<typeof registerSchema>;

// ---------------------------------------------------------------------------
// Critical response schemas (validated at the API boundary)
// ---------------------------------------------------------------------------

export const tokenResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.literal("bearer"),
  expires_in: z.number(),
});

export const wsTokenResponseSchema = z.object({
  token: z.string(),
  expires_in: z.number(),
});
