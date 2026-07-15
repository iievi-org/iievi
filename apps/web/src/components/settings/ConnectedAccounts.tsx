"use client";

import type { CredentialsResponse } from "@iievi/types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Link2, Plug, XCircle } from "lucide-react";
import { type FormEvent, useState } from "react";
import { toast } from "sonner";

import { Badge, Button, Card } from "@/components/linen";
import { api } from "@/lib/api";

const CREDENTIALS_KEY = ["credentials"] as const;

interface FieldSpec {
  name: string;
  label: string;
  placeholder: string;
  type?: "text" | "password";
}

interface ServiceSpec {
  service: string;
  name: string;
  description: string;
  /** Meta uses an OAuth stub; the rest collect token(s) in a modal. */
  kind: "oauth" | "token";
  fields: FieldSpec[];
}

/** The services we surface, keyed to the backend credential service names. */
const SERVICES: ServiceSpec[] = [
  {
    service: "meta",
    name: "Meta (Instagram & Facebook)",
    description: "Publish posts and manage DMs across Instagram and Facebook.",
    kind: "oauth",
    fields: [],
  },
  {
    service: "anthropic",
    name: "Anthropic (Claude)",
    description: "Bring your own Claude API key to power AI replies and post copy.",
    kind: "token",
    fields: [
      { name: "api_key", label: "API key", placeholder: "sk-ant-…", type: "password" },
    ],
  },
  {
    service: "nanobanana",
    name: "Nano Banana",
    description: "Image generation for post creatives.",
    kind: "token",
    fields: [
      { name: "api_key", label: "API key", placeholder: "nb_…", type: "password" },
    ],
  },
  {
    service: "whatsapp",
    name: "WhatsApp Business",
    description: "Reply to leads over WhatsApp using the Cloud API.",
    kind: "token",
    fields: [
      { name: "access_token", label: "Access token", placeholder: "EAAG…", type: "password" },
      { name: "phone_number_id", label: "Phone number ID", placeholder: "1234567890" },
    ],
  },
];

export function ConnectedAccounts() {
  const { data, isLoading, isError } = useQuery<CredentialsResponse>({
    queryKey: CREDENTIALS_KEY,
    queryFn: () => api.credentials.list(),
    staleTime: 60 * 1000,
  });

  const connected = new Set(data?.connected.map((c) => c.service) ?? []);

  if (isLoading) {
    return (
      <p className="font-body text-body-sm text-stone" role="status">
        Loading connected accounts…
      </p>
    );
  }
  if (isError) {
    return (
      <p className="border border-hairline bg-neutral px-4 py-3 font-body text-body-sm text-signal">
        We couldn&rsquo;t load your connected accounts. Please refresh and try again.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {SERVICES.map((spec) => {
        const isConnected = connected.has(spec.service);
        const meta = data?.connected.find((c) => c.service === spec.service);
        return (
          <ServiceCard
            key={spec.service}
            spec={spec}
            isConnected={isConnected}
            lastUsedAt={meta?.last_used_at ?? null}
          />
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// One service card
// ---------------------------------------------------------------------------

function ServiceCard({
  spec,
  isConnected,
  lastUsedAt,
}: {
  spec: ServiceSpec;
  isConnected: boolean;
  lastUsedAt: string | null;
}) {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);

  const disconnect = useMutation({
    mutationFn: () => api.credentials.disconnect(spec.service),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: CREDENTIALS_KEY });
      toast.success(`Disconnected ${spec.name}`);
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : `Couldn't disconnect ${spec.name}`),
  });

  // [OAUTH] real Meta OAuth redirect wired later — for now this is a stub that
  // does NOT navigate anywhere; it only signals that the flow is coming.
  const handleMetaConnect = () => {
    toast.message("Meta OAuth coming soon");
  };

  return (
    <Card variant="paper" className="p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="font-display text-headline-sm text-ink">{spec.name}</h3>
            {isConnected ? (
              <Badge color="#3f8f5b">Connected</Badge>
            ) : (
              <Badge>Not connected</Badge>
            )}
          </div>
          <p className="mt-2 max-w-prose font-body text-body-sm text-graphite">
            {spec.description}
          </p>
          {isConnected && lastUsedAt ? (
            <p className="mt-2 font-mono text-mono-sm text-stone">
              Last used {new Date(lastUsedAt).toLocaleDateString()}
            </p>
          ) : null}
        </div>

        <div className="flex shrink-0 items-center gap-3">
          {isConnected ? (
            <Button
              type="button"
              variant="ghost"
              onClick={() => disconnect.mutate()}
              disabled={disconnect.isPending}
            >
              {disconnect.isPending ? "Disconnecting…" : "Disconnect"}
            </Button>
          ) : spec.kind === "oauth" ? (
            <Button type="button" onClick={handleMetaConnect}>
              <Link2 aria-hidden="true" size={16} strokeWidth={1.75} />
              Connect with Meta
            </Button>
          ) : (
            <Button type="button" onClick={() => setModalOpen(true)}>
              <Plug aria-hidden="true" size={16} strokeWidth={1.75} />
              Connect
            </Button>
          )}
        </div>
      </div>

      {spec.kind === "token" && modalOpen ? (
        <ConnectModal spec={spec} onClose={() => setModalOpen(false)} />
      ) : null}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Token-entry modal with verify-before-finalize
// ---------------------------------------------------------------------------

type VerifyState =
  | { status: "idle" }
  | { status: "verifying" }
  | { status: "verified" }
  | { status: "failed" };

function ConnectModal({ spec, onClose }: { spec: ServiceSpec; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [values, setValues] = useState<Record<string, string>>({});
  const [state, setState] = useState<VerifyState>({ status: "idle" });

  const connect = useMutation({
    mutationFn: (data: Record<string, string>) => api.credentials.connect(spec.service, data),
    onMutate: () => setState({ status: "verifying" }),
    onSuccess: (result) => {
      // Show the verification result BEFORE finalizing. Only on `verified` do we
      // invalidate + toast success; otherwise the modal stays open to retry.
      if (result.verified) {
        setState({ status: "verified" });
        void queryClient.invalidateQueries({ queryKey: CREDENTIALS_KEY });
        toast.success(`${spec.name} connected`);
        // Give the user a beat to see the green state, then close.
        window.setTimeout(onClose, 900);
      } else {
        setState({ status: "failed" });
      }
    },
    onError: (error) => {
      setState({ status: "failed" });
      toast.error(error instanceof Error ? error.message : "Verification failed");
    },
  });

  const setField = (name: string, value: string) => {
    setValues((prev) => ({ ...prev, [name]: value }));
    if (state.status !== "idle") setState({ status: "idle" });
  };

  const allFilled = spec.fields.every((field) => (values[field.name] ?? "").trim() !== "");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!allFilled) return;
    // Build the payload from filled fields only (no explicit undefined values).
    const data: Record<string, string> = {};
    for (const field of spec.fields) {
      const value = (values[field.name] ?? "").trim();
      if (value) data[field.name] = value;
    }
    connect.mutate(data);
  };

  return (
    <div
      role="presentation"
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center p-6"
      style={{ backgroundColor: "rgba(20,17,13,0.55)" }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={`connect-${spec.service}-title`}
        onClick={(event) => event.stopPropagation()}
        className="w-full max-w-md border border-hairline bg-surface p-8"
      >
        <h2 id={`connect-${spec.service}-title`} className="font-display text-headline-md text-ink">
          Connect {spec.name}
        </h2>
        <p className="mt-2 font-body text-body-sm text-graphite">
          We&rsquo;ll verify your credentials before saving them.
        </p>

        <form onSubmit={submit} className="mt-6 flex flex-col gap-5">
          {spec.fields.map((field) => (
            <div key={field.name} className="flex flex-col gap-1">
              <label
                htmlFor={`connect-${spec.service}-${field.name}`}
                className="font-body text-label-sm uppercase tracking-[0.14em] text-stone"
              >
                {field.label}
              </label>
              <input
                id={`connect-${spec.service}-${field.name}`}
                name={field.name}
                type={field.type ?? "text"}
                autoComplete="off"
                spellCheck={false}
                value={values[field.name] ?? ""}
                onChange={(event) => setField(field.name, event.target.value)}
                placeholder={field.placeholder}
                className="border-0 border-b border-t border-hairline bg-transparent px-0 py-3 font-mono text-mono-sm text-ink outline-none transition-colors placeholder:text-stone focus:border-b-2 focus:border-b-signal"
              />
            </div>
          ))}

          {/* Verification result, shown before finalizing */}
          {state.status === "verified" ? (
            <p className="inline-flex items-center gap-2 font-body text-body-sm text-[#3f8f5b]">
              <CheckCircle2 aria-hidden="true" size={16} strokeWidth={1.75} />
              Verified
            </p>
          ) : null}
          {state.status === "failed" ? (
            <p className="inline-flex items-center gap-2 font-body text-body-sm text-signal" role="alert">
              <XCircle aria-hidden="true" size={16} strokeWidth={1.75} />
              Verification failed — check your credentials and try again.
            </p>
          ) : null}

          <div className="mt-2 flex items-center justify-end gap-3">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={!allFilled || connect.isPending}>
              {connect.isPending ? "Verifying…" : "Verify & connect"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
