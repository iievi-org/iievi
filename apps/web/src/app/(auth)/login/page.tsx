"use client";

import { AuthError } from "@iievi/api-client";
import { type LoginInput, loginSchema } from "@iievi/validators";
import { zodResolver } from "@hookform/resolvers/zod";
import type { Route } from "next";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { AuthShell } from "@/components/auth/AuthShell";
import { Button, Input } from "@/components/linen";
import { api } from "@/lib/api";
import { setAccessToken } from "@/lib/auth-state";

export default function LoginPage() {
  const router = useRouter();
  const [banner, setBanner] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginInput>({ resolver: zodResolver(loginSchema) });

  const onSubmit = handleSubmit(async (values) => {
    setBanner(null);
    try {
      const { access_token } = await api.auth.login(values);
      setAccessToken(access_token);
      const redirect = new URLSearchParams(window.location.search).get("redirect");
      const target = redirect && redirect.startsWith("/") ? redirect : "/dashboard/chat";
      router.replace(target as Route);
    } catch (error) {
      // Credential errors stay inline (the user's eyes are on the form).
      setBanner(
        error instanceof AuthError
          ? "Incorrect email or password."
          : "Something went wrong. Please try again.",
      );
    }
  });

  return (
    <AuthShell headline="Turn every message into a booking.">
      <h1 className="font-display text-headline-md text-ink">Sign in</h1>
      <p className="mt-2 font-body text-body-sm text-graphite">Welcome back.</p>
      {banner ? (
        <div
          role="alert"
          className="mt-4 border border-signal px-4 py-3 font-body text-body-sm text-signal"
        >
          {banner}
        </div>
      ) : null}
      <form onSubmit={onSubmit} noValidate className="mt-6 flex flex-col gap-5">
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register("email")}
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register("password")}
        />
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>
      <p className="mt-6 font-body text-body-sm text-graphite">
        No account?{" "}
        <Link href="/register" className="text-signal underline">
          Create one
        </Link>
      </p>
    </AuthShell>
  );
}
