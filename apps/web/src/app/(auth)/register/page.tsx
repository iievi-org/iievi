"use client";

import { ApiRequestError } from "@iievi/api-client";
import { type BusinessCategory, CATEGORIES } from "@iievi/constants";
import { type RegisterInput, registerSchema } from "@iievi/validators";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { AuthShell } from "@/components/auth/AuthShell";
import { CategoryModal } from "@/components/auth/CategoryModal";
import { Button, Input } from "@/components/linen";
import { api } from "@/lib/api";
import { setAccessToken } from "@/lib/auth-state";

export default function RegisterPage() {
  const router = useRouter();
  const [banner, setBanner] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [category, setCategory] = useState<BusinessCategory | null>(null);
  const [categoryError, setCategoryError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterInput>({ resolver: zodResolver(registerSchema) });

  const onSubmit = handleSubmit(async (values) => {
    setBanner(null);
    if (!category) {
      setCategoryError("Please choose your business type.");
      return;
    }
    try {
      const { access_token } = await api.auth.register(values);
      setAccessToken(access_token);
      try {
        sessionStorage.setItem("onboarding_category", category);
      } catch {
        /* private mode — the category is re-collected during onboarding */
      }
      router.replace("/onboarding");
    } catch (error) {
      setBanner(
        error instanceof ApiRequestError
          ? error.message
          : "Something went wrong. Please try again.",
      );
    }
  });

  return (
    <AuthShell headline="Set up your AI in minutes.">
      <h1 className="font-display text-headline-md text-ink">Create your account</h1>
      <p className="mt-2 font-body text-body-sm text-graphite">Start capturing leads today.</p>
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
          label="Business name"
          error={errors.business_name?.message}
          {...register("business_name")}
        />
        <div className="flex flex-col gap-1">
          <span className="font-body text-label-sm uppercase tracking-[0.14em] text-stone">
            Business type
          </span>
          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="flex items-center justify-between border-b border-hairline py-3 text-left font-body text-body-md"
          >
            <span className={category ? "text-ink" : "text-stone"}>
              {category ? CATEGORIES[category].displayName : "Choose your business type"}
            </span>
            <span aria-hidden="true" className="text-stone">
              →
            </span>
          </button>
          {categoryError ? (
            <p role="alert" className="font-mono text-mono-sm text-signal">
              {categoryError}
            </p>
          ) : null}
        </div>
        <Input
          label="Your name"
          autoComplete="name"
          error={errors.full_name?.message}
          {...register("full_name")}
        />
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
          autoComplete="new-password"
          error={errors.password?.message}
          {...register("password")}
        />
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating…" : "Create account"}
        </Button>
      </form>
      <p className="mt-6 font-body text-body-sm text-graphite">
        Have an account?{" "}
        <Link href="/login" className="text-signal underline">
          Sign in
        </Link>
      </p>
      <CategoryModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSelect={(key) => {
          setCategory(key);
          setCategoryError(null);
          setModalOpen(false);
        }}
      />
    </AuthShell>
  );
}
