import { MessageSquare } from "lucide-react";

import { ComingSoon } from "@/components/dashboard/ComingSoon";
import { ButtonLink } from "@/components/linen";

export default function ChatPage() {
  return (
    <ComingSoon
      icon={MessageSquare}
      eyebrow="Chat"
      title="One chat to run everything"
      description="The unified command chat — where you generate posts, launch campaigns, and manage leads just by typing — is arriving next."
      bullets={[
        "Generate & schedule posts from a message",
        "Draft and launch ad campaigns",
        "Ask for analytics in plain language",
      ]}
      note="Backend chat endpoint in progress."
    >
      <ButtonLink href="/dashboard/leads" variant="ghost">
        Go to Leads
      </ButtonLink>
      <ButtonLink href="/dashboard/posts" variant="ghost">
        Create a post
      </ButtonLink>
    </ComingSoon>
  );
}
