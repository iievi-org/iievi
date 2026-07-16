"use client";

import type { PostStatus } from "@iievi/types";
import { LayoutGrid, List, Sparkles } from "lucide-react";
import { useCallback, useState } from "react";

import { ComingSoon } from "@/components/dashboard/ComingSoon";
import { ButtonLink, Container } from "@/components/linen";
import { GeneratePostForm } from "@/components/posts/GeneratePostForm";
import { PostApprovalModal } from "@/components/posts/PostApprovalModal";
import { PostCard } from "@/components/posts/PostCard";
import type { SessionPost } from "@/components/posts/types";
import { useCapabilities } from "@/hooks/useCapabilities";

type ViewMode = "list" | "grid";

export default function PostsPage() {
  const { hasFeature, query } = useCapabilities();

  // NOTE: there is no list/persistence endpoint (only generate + progress), so
  // this gallery is SESSION-SCOPED — it holds only posts generated in this tab
  // and is lost on reload.
  const [posts, setPosts] = useState<SessionPost[]>([]);
  const [view, setView] = useState<ViewMode>("grid");
  const [active, setActive] = useState<SessionPost | null>(null);

  const handleQueued = useCallback((post: SessionPost) => {
    setPosts((prev) => [post, ...prev]);
  }, []);

  const handleStage = useCallback((postId: string, stage: PostStatus) => {
    setPosts((prev) =>
      prev.map((p) => (p.postId === postId && p.stage !== stage ? { ...p, stage } : p)),
    );
  }, []);

  const openPost = useCallback((post: SessionPost) => setActive(post), []);
  const closePost = useCallback(() => setActive(null), []);

  // Gate: capabilities still loading → let the render fall through to the shell
  // (the form disables itself on error); only hard-gate once we know the answer.
  if (!query.isLoading && !hasFeature("can_generate_posts")) {
    return (
      <ComingSoon
        icon={Sparkles}
        eyebrow="Posts · Starter and up"
        title="Post generation"
        description="Draft, preview and schedule on-brand social posts in seconds. Post generation is available on the Starter, Growth and Agency plans."
        note="Upgrade to start generating."
      >
        <ButtonLink href="/dashboard/billing" variant="primary">
          View plans
        </ButtonLink>
      </ComingSoon>
    );
  }

  // The active post, re-read from state so its stage stays live while the modal
  // is open (progress polling in the gallery updates the same session entry).
  const activePost = active ? posts.find((p) => p.postId === active.postId) ?? active : null;

  return (
    <Container className="py-10">
      {/* Header */}
      <header className="flex flex-col gap-3 border-b border-hairline pb-6">
        <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">Studio</p>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-display text-headline-md text-ink">Posts</h1>
            <p className="mt-2 max-w-xl font-body text-body-md text-graphite">
              Describe a post, generate a creative, and preview how it reads on each
              network before you schedule it.
            </p>
          </div>

          {/* View switcher (List / Grid) */}
          {posts.length > 0 ? (
            <div
              role="tablist"
              aria-label="Gallery layout"
              className="inline-flex border border-hairline"
            >
              <ViewButton
                active={view === "grid"}
                onClick={() => setView("grid")}
                label="Grid view"
              >
                <LayoutGrid size={16} strokeWidth={1.5} aria-hidden="true" />
              </ViewButton>
              <ViewButton
                active={view === "list"}
                onClick={() => setView("list")}
                label="List view"
              >
                <List size={16} strokeWidth={1.5} aria-hidden="true" />
              </ViewButton>
            </div>
          ) : null}
        </div>
      </header>

      {/* Generator */}
      <section className="mt-8">
        <GeneratePostForm onQueued={handleQueued} />
      </section>

      {/* Session gallery */}
      <section className="mt-12">
        <div className="flex items-center justify-between gap-4">
          <h2 className="font-display text-headline-sm text-ink">This session</h2>
          {posts.length > 0 ? (
            <span className="font-mono text-mono-sm text-stone">
              {posts.length} {posts.length === 1 ? "post" : "posts"}
            </span>
          ) : null}
        </div>

        {posts.length === 0 ? (
          <div className="mt-6 flex flex-col items-center gap-2 border border-hairline bg-neutral px-6 py-16 text-center">
            <Sparkles size={28} strokeWidth={1.25} className="text-stone" aria-hidden="true" />
            <p className="font-body text-body-sm text-graphite">
              No posts yet — generate your first one above.
            </p>
          </div>
        ) : view === "grid" ? (
          <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {posts.map((post) => (
              <PostCard
                key={post.postId}
                post={post}
                layout="grid"
                onStage={handleStage}
                onOpen={openPost}
              />
            ))}
          </div>
        ) : (
          <div className="mt-6 flex flex-col gap-4">
            {posts.map((post) => (
              <PostCard
                key={post.postId}
                post={post}
                layout="list"
                onStage={handleStage}
                onOpen={openPost}
              />
            ))}
          </div>
        )}
      </section>

      {/* Honest limitation note */}
      <p className="mt-12 border-t border-hairline pt-6 font-mono text-mono-sm text-stone">
        Full post management — a saved library, approval and scheduling — lands when the
        backend endpoints ship. For now, generation and live progress are wired end-to-end;
        the gallery and approval flow are session-scoped previews.
      </p>

      {activePost ? <PostApprovalModal post={activePost} onClose={closePost} /> : null}
    </Container>
  );
}

function ViewButton({
  active,
  onClick,
  label,
  children,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      aria-label={label}
      onClick={onClick}
      className={`inline-flex h-9 w-10 items-center justify-center transition-colors ${
        active ? "bg-ink text-surface" : "bg-transparent text-graphite hover:bg-neutral"
      }`}
    >
      {children}
    </button>
  );
}
