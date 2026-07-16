import type { OnboardingStage } from "@iievi/types";

export interface OnboardingMessage {
  id: string;
  role: "ai" | "user";
  text: string;
  stage?: OnboardingStage;
}

export interface OnboardingState {
  messages: OnboardingMessage[];
  stage: OnboardingStage;
  status: "idle" | "sending" | "typing";
  completed: boolean;
  requiresAuth: boolean;
  error: string | null;
}

export type OnboardingAction =
  | { type: "USER_MESSAGE"; text: string }
  | { type: "AI_TYPING" }
  | {
      type: "AI_MESSAGE";
      text: string;
      stage: OnboardingStage;
      completed: boolean;
      requiresAuth: boolean;
    }
  | { type: "ERROR"; message: string };

const newId = (): string =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.round(Math.random() * 1e9)}`;

const WELCOME_TEXT =
  "Hi! I'm your IIEVI setup assistant — I'll get your AI ready to capture leads and post for you, in just a few minutes. Ready to start?";

export const initialOnboardingState: OnboardingState = {
  messages: [{ id: newId(), role: "ai", text: WELCOME_TEXT, stage: "welcome" }],
  stage: "welcome",
  status: "idle",
  completed: false,
  requiresAuth: false,
  error: null,
};

export function onboardingReducer(
  state: OnboardingState,
  action: OnboardingAction,
): OnboardingState {
  switch (action.type) {
    case "USER_MESSAGE":
      return {
        ...state,
        error: null,
        status: "sending",
        messages: [...state.messages, { id: newId(), role: "user", text: action.text }],
      };
    case "AI_TYPING":
      return { ...state, status: "typing" };
    case "AI_MESSAGE":
      return {
        ...state,
        status: "idle",
        stage: action.stage,
        completed: action.completed,
        requiresAuth: action.requiresAuth,
        messages: [
          ...state.messages,
          { id: newId(), role: "ai", text: action.text, stage: action.stage },
        ],
      };
    case "ERROR":
      return { ...state, status: "idle", error: action.message };
    default:
      return state;
  }
}

/** Typing rhythm: message length × 40ms, bounded 800–2500ms. */
export function typingDelayMs(text: string): number {
  return Math.min(2500, Math.max(800, text.length * 40));
}
