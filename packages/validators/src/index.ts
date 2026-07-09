/**
 * Zod schemas shared by frontend forms and API-client response validation.
 * Schemas here mirror the interfaces in @iievi/types.
 */

import { z } from "zod";

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
