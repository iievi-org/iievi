/* ──────────────────────────────────────────────────────────
 * Solution Playbook – data layer
 * One record per category. Each category has exactly 8 steps
 * that map 1-to-1 to the PlaybookMockup component states.
 * ────────────────────────────────────────────────────────── */

// ── Mockup data types ────────────────────────────────────

export interface OnboardingData {
  businessName: string;
  industry: string;
  goals: string[];
  selectedGoal: number;
}

export interface BusinessProfileData {
  brandVoice: string;
  products: string[];
  targetAudience: string;
  profileComplete: number;
}

export interface SecureApiData {
  platforms: { name: string; connected: boolean }[];
  statusItems: string[];
  securityScore: number;
}

export interface AiCommandData {
  prompt: string;
}

export interface ContentGeneratorData {
  campaignName: string;
  channels: string[];
}

export interface PublishingData {
  platforms: { name: string; status: string }[];
  reach: number;
}

export interface AiConversationData {
  customerMessage: string;
  aiResponse: string;
  responseTime: string;
}

export interface LeadPipelineData {
  stages: string[];
  activeStage: number;
  leadScore: number;
}

export interface AdBudgetData {
  campaignObjective: string;
  buyingType: string;
  budgetType: string;
  amount: number;
}

export interface TargetReachData {
  locations: string[];
  ageRange: string;
  gender: string;
  detailedTargeting: string[];
  placements: string;
}

export type MockupData =
  | { type: "onboarding"; data: OnboardingData }
  | { type: "business-profile"; data: BusinessProfileData }
  | { type: "secure-api"; data: SecureApiData }
  | { type: "ai-command"; data: AiCommandData }
  | { type: "content-generator"; data: ContentGeneratorData }
  | { type: "ad-budget"; data: AdBudgetData }
  | { type: "target-reach"; data: TargetReachData }
  | { type: "publishing"; data: PublishingData }
  | { type: "ai-conversation"; data: AiConversationData }
  | { type: "lead-pipeline"; data: LeadPipelineData };

// ── Step & category types ────────────────────────────────

export interface PlaybookStep {
  stepNumber: string;
  heading: string;
  description: string;
  highlightsLabel: string;
  highlights: string[];
  mockup: MockupData;
}

export interface FinalStat {
  label: string;
  value: number;
}

export interface CategoryData {
  slug: string;
  label: string;
  headline: string;
  intro: string;
  playbook: PlaybookStep[];
  finalStats: FinalStat[];
}

// ── Shared constants ─────────────────────────────────────

const SHARED_PLATFORMS = [
  { name: "Facebook", connected: true },
  { name: "Instagram", connected: true },
  { name: "Google Business", connected: true },
  { name: "WhatsApp", connected: true },
];

const SHARED_API_STATUS = ["Encrypted", "Stored Securely", "Access Restricted"];

const SHARED_SECURITY_HIGHLIGHTS = [
  "AES-256 encryption",
  "Secure vault storage",
  "Role-based access",
  "No plaintext key exposure",
];

const SHARED_PUBLISH_PLATFORMS = [
  { name: "Instagram", status: "Posted" },
  { name: "Facebook", status: "Posted" },
  { name: "Google", status: "Posted" },
  { name: "LinkedIn", status: "Posted" },
  { name: "WhatsApp", status: "Sent" },
];

const SHARED_PIPELINE_STAGES = [
  "New Lead",
  "Qualified",
  "Interested",
  "Booking Offered",
  "Appointment Confirmed",
];

// ── Category definitions ─────────────────────────────────

const petWellness: CategoryData = {
  slug: "pet-wellness",
  label: "Pet Wellness",
  headline: "Turn pet parents into lifelong customers.",
  intro:
    "From herbal shampoos to vet consultations — IIEVI automates lead capture, content creation, and follow-ups for pet wellness brands.",
  playbook: [
    {
      stepNumber: "01",
      heading: "Onboarding",
      description:
        "Connect your business in minutes. Answer a few questions about your business goals, services, and target audience. Our AI automatically configures the optimal content and lead-generation workflow for your industry.",
      highlightsLabel: "Highlights",
      highlights: ["2-minute setup", "No technical expertise required", "AI-guided configuration"],
      mockup: {
        type: "onboarding",
        data: {
          businessName: "Pawwcious",
          industry: "Pet Wellness",
          goals: ["Generate Leads", "Grow Social Media", "Book Consultations"],
          selectedGoal: 1,
        },
      },
    },
    {
      stepNumber: "02",
      heading: "Create Business Profile",
      description:
        "Build your digital business identity. The AI learns your products, services, brand voice, locations, and customer segments to generate highly relevant content and conversations.",
      highlightsLabel: "What AI learns",
      highlights: ["Brand tone & personality", "Full product catalogue", "Customer demographics"],
      mockup: {
        type: "business-profile",
        data: {
          brandVoice: "Friendly & Educational",
          products: ["Herbal Pet Shampoo", "Tick Protection Spray", "Digestive Support"],
          targetAudience: "Pet Parents",
          profileComplete: 82,
        },
      },
    },
    {
      stepNumber: "03",
      heading: "Secure API Integration",
      description:
        "Connect your channels securely. API credentials are encrypted at rest, transmitted over secure channels, and isolated per workspace. Users maintain complete ownership and control of connected platforms.",
      highlightsLabel: "Security Features",
      highlights: SHARED_SECURITY_HIGHLIGHTS,
      mockup: {
        type: "secure-api",
        data: {
          platforms: SHARED_PLATFORMS,
          statusItems: SHARED_API_STATUS,
          securityScore: 100,
        },
      },
    },
    {
      stepNumber: "04",
      heading: "Start Conversation",
      description:
        "Tell the AI what you want to achieve. Provide a simple instruction and watch the AI create a complete campaign strategy tailored to your business.",
      highlightsLabel: "Capabilities",
      highlights: [
        "Natural language prompts",
        "Multi-channel strategy",
        "Industry-specific templates",
      ],
      mockup: {
        type: "ai-command",
        data: {
          prompt: "Create content for dog owners during summer season.",
        },
      },
    },
    {
      stepNumber: "05",
      heading: "AI Content Generation",
      description:
        "Generate high-performing content automatically. The system creates posts, captions, hashtags, creatives, and engagement hooks specifically designed for your industry.",
      highlightsLabel: "Output",
      highlights: ["Platform-optimised captions", "Industry hashtags", "Engagement-first hooks"],
      mockup: {
        type: "content-generator",
        data: {
          campaignName: "Summer Pet Care",
          channels: [
            "Instagram Post",
            "Facebook Post",
            "Google Business Update",
            "WhatsApp Broadcast",
          ],
        },
      },
    },
    {
      stepNumber: "06",
      heading: "Publish Everywhere",
      description:
        "Reach customers wherever they are. One click distributes content across all connected platforms while maintaining platform-specific formatting.",
      highlightsLabel: "Channels",
      highlights: ["Cross-platform publishing", "Format auto-adaptation", "Scheduled delivery"],
      mockup: {
        type: "publishing",
        data: {
          platforms: SHARED_PUBLISH_PLATFORMS,
          reach: 12458,
        },
      },
    },
    {
      stepNumber: "07",
      heading: "AI Handles Conversations",
      description:
        "Never miss an opportunity. When a prospect comments, messages, or replies, the AI responds instantly using your business knowledge and predefined policies.",
      highlightsLabel: "Intelligence",
      highlights: ["3-second response time", "Context-aware answers", "Automatic escalation"],
      mockup: {
        type: "ai-conversation",
        data: {
          customerMessage: "Hi, is this safe for puppies?",
          aiResponse:
            "Yes! Our herbal formula is designed for puppies above 12 weeks of age. Would you like to see our puppy care range?",
          responseTime: "3 sec",
        },
      },
    },
    {
      stepNumber: "08",
      heading: "Booking Offered",
      description:
        "Turn conversations into revenue. When the AI detects buying intent, the lead automatically moves through your sales pipeline and receives booking options.",
      highlightsLabel: "Pipeline",
      highlights: ["Intent detection", "Auto-qualification", "One-tap booking link"],
      mockup: {
        type: "lead-pipeline",
        data: {
          stages: SHARED_PIPELINE_STAGES,
          activeStage: 3,
          leadScore: 94,
        },
      },
    },
  ],
  finalStats: [
    { label: "Posts Generated", value: 47 },
    { label: "Posts Published", value: 47 },
    { label: "Leads Captured", value: 126 },
    { label: "Conversations Handled", value: 311 },
    { label: "Bookings Offered", value: 39 },
  ],
};

const plumbing: CategoryData = {
  slug: "plumbing",
  label: "Plumbing Services",
  headline: "Every leak fixed. Every job booked.",
  intro:
    "From emergency repairs to annual maintenance — IIEVI automates lead capture, dispatch, and follow-ups for plumbing businesses.",
  playbook: [
    {
      stepNumber: "01",
      heading: "Onboarding",
      description:
        "Connect your business in minutes. Answer a few questions about your service area, specialties, and team size. Our AI configures the optimal lead-capture and dispatch workflow for plumbing businesses.",
      highlightsLabel: "Highlights",
      highlights: ["2-minute setup", "No technical expertise required", "AI-guided configuration"],
      mockup: {
        type: "onboarding",
        data: {
          businessName: "QuickFix Plumbing",
          industry: "Plumbing Services",
          goals: ["Generate Leads", "Emergency Bookings", "Service Contracts"],
          selectedGoal: 0,
        },
      },
    },
    {
      stepNumber: "02",
      heading: "Create Business Profile",
      description:
        "Build your digital business identity. The AI learns your services, pricing, service areas, and technician availability to handle customer queries conversationally.",
      highlightsLabel: "What AI learns",
      highlights: ["Service catalogue & pricing", "Coverage areas & zones", "Technician schedules"],
      mockup: {
        type: "business-profile",
        data: {
          brandVoice: "Professional & Reliable",
          products: ["Pipe Repair & Fitting", "Drain Cleaning", "Water Heater Installation"],
          targetAudience: "Homeowners",
          profileComplete: 88,
        },
      },
    },
    {
      stepNumber: "03",
      heading: "Secure API Integration",
      description:
        "Connect your channels securely. API credentials are encrypted at rest, transmitted over secure channels, and isolated per workspace.",
      highlightsLabel: "Security Features",
      highlights: SHARED_SECURITY_HIGHLIGHTS,
      mockup: {
        type: "secure-api",
        data: {
          platforms: SHARED_PLATFORMS,
          statusItems: SHARED_API_STATUS,
          securityScore: 100,
        },
      },
    },
    {
      stepNumber: "04",
      heading: "Start Conversation",
      description:
        "Tell the AI what you want to achieve. Describe a campaign and watch the AI create targeted content for homeowners in your service area.",
      highlightsLabel: "Capabilities",
      highlights: [
        "Natural language prompts",
        "Seasonal campaign templates",
        "Location-targeted content",
      ],
      mockup: {
        type: "ai-command",
        data: {
          prompt: "Create content for homeowners about monsoon pipe maintenance tips.",
        },
      },
    },
    {
      stepNumber: "05",
      heading: "AI Content Generation",
      description:
        "Generate high-performing content automatically. The system creates maintenance tips, emergency guides, and seasonal reminders that position you as the trusted local plumber.",
      highlightsLabel: "Output",
      highlights: [
        "Seasonal maintenance tips",
        "Emergency awareness posts",
        "Trust-building content",
      ],
      mockup: {
        type: "content-generator",
        data: {
          campaignName: "Monsoon Pipe Care",
          channels: [
            "Instagram Post",
            "Facebook Post",
            "Google Business Update",
            "WhatsApp Broadcast",
          ],
        },
      },
    },
    {
      stepNumber: "06",
      heading: "Publish Everywhere",
      description:
        "Reach homeowners wherever they search. One click distributes content across all connected platforms with area-specific targeting.",
      highlightsLabel: "Channels",
      highlights: ["Cross-platform publishing", "Area-specific targeting", "Scheduled delivery"],
      mockup: {
        type: "publishing",
        data: {
          platforms: SHARED_PUBLISH_PLATFORMS,
          reach: 8920,
        },
      },
    },
    {
      stepNumber: "07",
      heading: "AI Handles Conversations",
      description:
        "Never miss an emergency call. When a homeowner messages about a leak or blockage, the AI responds instantly with diagnosis questions and dispatch options.",
      highlightsLabel: "Intelligence",
      highlights: ["Instant emergency triage", "Technician dispatch", "Upfront pricing"],
      mockup: {
        type: "ai-conversation",
        data: {
          customerMessage: "My kitchen pipe is leaking badly, need help urgently!",
          aiResponse:
            "I understand the urgency. We can dispatch a technician within 2 hours. ₹500 inspection fee, adjustable against repair cost. Shall I book?",
          responseTime: "3 sec",
        },
      },
    },
    {
      stepNumber: "08",
      heading: "Booking Offered",
      description:
        "Turn emergencies into booked jobs. When the AI detects urgency, it fast-tracks the lead through your pipeline and offers immediate dispatch.",
      highlightsLabel: "Pipeline",
      highlights: ["Urgency detection", "Same-day dispatch", "Estimate approval flow"],
      mockup: {
        type: "lead-pipeline",
        data: {
          stages: SHARED_PIPELINE_STAGES,
          activeStage: 3,
          leadScore: 91,
        },
      },
    },
  ],
  finalStats: [
    { label: "Posts Generated", value: 38 },
    { label: "Posts Published", value: 38 },
    { label: "Leads Captured", value: 94 },
    { label: "Conversations Handled", value: 247 },
    { label: "Bookings Offered", value: 52 },
  ],
};

const electrician: CategoryData = {
  slug: "electrician",
  label: "Electrician Services",
  headline: "Every fault diagnosed. Every call answered.",
  intro:
    "From MCB trips to full rewiring — IIEVI automates lead capture, safety-first content, and technician dispatch for electrical businesses.",
  playbook: [
    {
      stepNumber: "01",
      heading: "Onboarding",
      description:
        "Connect your business in minutes. Answer a few questions about your service specialties, coverage area, and team certifications. The AI configures a workflow optimised for electrical services.",
      highlightsLabel: "Highlights",
      highlights: ["2-minute setup", "No technical expertise required", "AI-guided configuration"],
      mockup: {
        type: "onboarding",
        data: {
          businessName: "BrightSpark Electric",
          industry: "Electrical Services",
          goals: ["Generate Leads", "Emergency Calls", "AMC Contracts"],
          selectedGoal: 0,
        },
      },
    },
    {
      stepNumber: "02",
      heading: "Create Business Profile",
      description:
        "Build your digital business identity. The AI learns your service list, certifications, coverage zones, and pricing to handle queries with precision.",
      highlightsLabel: "What AI learns",
      highlights: ["Service list & certifications", "Coverage zones & rates", "Safety protocols"],
      mockup: {
        type: "business-profile",
        data: {
          brandVoice: "Professional & Safety-focused",
          products: ["Wiring & Rewiring", "MCB & Panel Installation", "AC Wiring & Setup"],
          targetAudience: "Homeowners & Offices",
          profileComplete: 85,
        },
      },
    },
    {
      stepNumber: "03",
      heading: "Secure API Integration",
      description:
        "Connect your channels securely. API credentials are encrypted at rest, transmitted over secure channels, and isolated per workspace.",
      highlightsLabel: "Security Features",
      highlights: SHARED_SECURITY_HIGHLIGHTS,
      mockup: {
        type: "secure-api",
        data: {
          platforms: SHARED_PLATFORMS,
          statusItems: SHARED_API_STATUS,
          securityScore: 100,
        },
      },
    },
    {
      stepNumber: "04",
      heading: "Start Conversation",
      description:
        "Tell the AI what you want to achieve. Describe a campaign and the AI creates safety tips, seasonal alerts, and awareness content for your audience.",
      highlightsLabel: "Capabilities",
      highlights: [
        "Natural language prompts",
        "Safety-first content",
        "Seasonal campaign templates",
      ],
      mockup: {
        type: "ai-command",
        data: {
          prompt: "Create content about electrical safety tips for summer and monsoon season.",
        },
      },
    },
    {
      stepNumber: "05",
      heading: "AI Content Generation",
      description:
        "Generate high-performing content automatically. The system creates safety guides, maintenance checklists, and seasonal alerts that build trust and authority.",
      highlightsLabel: "Output",
      highlights: ["Safety awareness posts", "Maintenance checklists", "Seasonal alerts"],
      mockup: {
        type: "content-generator",
        data: {
          campaignName: "Summer Safety Tips",
          channels: [
            "Instagram Post",
            "Facebook Post",
            "Google Business Update",
            "WhatsApp Broadcast",
          ],
        },
      },
    },
    {
      stepNumber: "06",
      heading: "Publish Everywhere",
      description:
        "Reach customers wherever they search. One click distributes safety content and service offers across all your connected platforms.",
      highlightsLabel: "Channels",
      highlights: ["Cross-platform publishing", "Locality-based targeting", "Scheduled delivery"],
      mockup: {
        type: "publishing",
        data: {
          platforms: SHARED_PUBLISH_PLATFORMS,
          reach: 7640,
        },
      },
    },
    {
      stepNumber: "07",
      heading: "AI Handles Conversations",
      description:
        "Never miss an emergency. When someone messages about a tripping MCB or a sparking outlet, the AI triages instantly and dispatches your certified team.",
      highlightsLabel: "Intelligence",
      highlights: ["Emergency triage logic", "Certified tech dispatch", "Safety-first responses"],
      mockup: {
        type: "ai-conversation",
        data: {
          customerMessage: "My MCB keeps tripping every few minutes, is this dangerous?",
          aiResponse:
            "This could indicate an overloaded circuit — please avoid using heavy appliances. We can send a certified electrician to diagnose within 3 hours. ₹400 visit charge. Book now?",
          responseTime: "3 sec",
        },
      },
    },
    {
      stepNumber: "08",
      heading: "Booking Offered",
      description:
        "Turn emergency calls into dispatched jobs. When the AI detects a safety concern, it prioritises the lead and offers immediate technician dispatch.",
      highlightsLabel: "Pipeline",
      highlights: ["Safety-priority routing", "Express dispatch", "AMC conversion offers"],
      mockup: {
        type: "lead-pipeline",
        data: {
          stages: SHARED_PIPELINE_STAGES,
          activeStage: 3,
          leadScore: 88,
        },
      },
    },
  ],
  finalStats: [
    { label: "Posts Generated", value: 34 },
    { label: "Posts Published", value: 34 },
    { label: "Leads Captured", value: 81 },
    { label: "Conversations Handled", value: 198 },
    { label: "Bookings Offered", value: 44 },
  ],
};

const realEstate: CategoryData = {
  slug: "real-estate",
  label: "Real Estate Brokers",
  headline: "Every enquiry answered. Every site visit booked.",
  intro:
    "From property listings to site visit scheduling — IIEVI automates lead qualification, content distribution, and follow-ups for real estate brokers.",
  playbook: [
    {
      stepNumber: "01",
      heading: "Onboarding",
      description:
        "Connect your brokerage in minutes. Answer a few questions about your property portfolio, target locations, and buyer segments. The AI configures a workflow built for real estate.",
      highlightsLabel: "Highlights",
      highlights: ["2-minute setup", "No technical expertise required", "AI-guided configuration"],
      mockup: {
        type: "onboarding",
        data: {
          businessName: "PrimeNest Realty",
          industry: "Real Estate Brokerage",
          goals: ["Generate Leads", "Schedule Site Visits", "Close Deals"],
          selectedGoal: 0,
        },
      },
    },
    {
      stepNumber: "02",
      heading: "Create Business Profile",
      description:
        "Build your digital brokerage identity. The AI learns your active listings, price ranges, localities, and buyer preferences to match enquiries intelligently.",
      highlightsLabel: "What AI learns",
      highlights: [
        "Active property listings",
        "Price range & localities",
        "Buyer segment profiles",
      ],
      mockup: {
        type: "business-profile",
        data: {
          brandVoice: "Trustworthy & Market-savvy",
          products: [
            "2BHK Andheri West — ₹1.35 Cr",
            "3BHK Powai Lake View — ₹2.8 Cr",
            "Commercial Bandra — ₹4.2 Cr",
          ],
          targetAudience: "Home Buyers & Investors",
          profileComplete: 78,
        },
      },
    },
    {
      stepNumber: "03",
      heading: "Secure API Integration",
      description:
        "Connect your channels securely. API credentials are encrypted at rest, transmitted over secure channels, and isolated per workspace.",
      highlightsLabel: "Security Features",
      highlights: SHARED_SECURITY_HIGHLIGHTS,
      mockup: {
        type: "secure-api",
        data: {
          platforms: SHARED_PLATFORMS,
          statusItems: SHARED_API_STATUS,
          securityScore: 100,
        },
      },
    },
    {
      stepNumber: "04",
      heading: "Start Conversation",
      description:
        "Tell the AI what you want to promote. Describe your listing and the AI creates a multi-channel marketing strategy to attract qualified buyers.",
      highlightsLabel: "Capabilities",
      highlights: [
        "Natural language prompts",
        "Listing-focused strategies",
        "Location-targeted content",
      ],
      mockup: {
        type: "ai-command",
        data: {
          prompt:
            "Create content for first-time home buyers looking at 2BHK apartments in Mumbai under 1.5 Cr.",
        },
      },
    },
    {
      stepNumber: "05",
      heading: "AI Content Generation",
      description:
        "Generate high-performing listing content automatically. The system creates property showcases, neighbourhood guides, and investment insights tailored to your target buyers.",
      highlightsLabel: "Output",
      highlights: ["Property showcase posts", "Neighbourhood guides", "Investment insights"],
      mockup: {
        type: "content-generator",
        data: {
          campaignName: "First Home Guide — Mumbai",
          channels: [
            "Instagram Post",
            "Facebook Post",
            "Google Business Update",
            "WhatsApp Broadcast",
          ],
        },
      },
    },
    {
      stepNumber: "06",
      heading: "Publish Everywhere",
      description:
        "Reach buyers wherever they search. One click distributes listings and market insights across all platforms with locality-specific targeting.",
      highlightsLabel: "Channels",
      highlights: ["Cross-platform publishing", "Micro-locality targeting", "Scheduled delivery"],
      mockup: {
        type: "publishing",
        data: {
          platforms: SHARED_PUBLISH_PLATFORMS,
          reach: 18740,
        },
      },
    },
    {
      stepNumber: "07",
      heading: "AI Handles Conversations",
      description:
        "Never miss a buyer. When someone enquires about a property, the AI qualifies their budget, location preference, and timeline — then offers matching listings instantly.",
      highlightsLabel: "Intelligence",
      highlights: ["Budget qualification", "Instant listing match", "Site visit scheduling"],
      mockup: {
        type: "ai-conversation",
        data: {
          customerMessage: "Looking for a 2BHK under 1.5 Cr in Andheri, ready to move in.",
          aiResponse:
            "We have 3 matching properties in Andheri West. Best match: 2BHK, 850 sqft, ₹1.35 Cr, ready possession. Would you like to schedule a site visit this weekend?",
          responseTime: "3 sec",
        },
      },
    },
    {
      stepNumber: "08",
      heading: "Booking Offered",
      description:
        "Turn enquiries into site visits. When the AI detects serious buying intent, it schedules site visits, sends location pins, and follows up automatically.",
      highlightsLabel: "Pipeline",
      highlights: ["Intent scoring", "Auto site-visit scheduling", "Post-visit follow-up"],
      mockup: {
        type: "lead-pipeline",
        data: {
          stages: ["New Enquiry", "Qualified", "Site Visit Scheduled", "Offer Made", "Deal Closed"],
          activeStage: 3,
          leadScore: 87,
        },
      },
    },
  ],
  finalStats: [
    { label: "Posts Generated", value: 52 },
    { label: "Posts Published", value: 52 },
    { label: "Leads Captured", value: 184 },
    { label: "Conversations Handled", value: 420 },
    { label: "Site Visits Booked", value: 67 },
  ],
};

const loanBrokers: CategoryData = {
  slug: "loan-brokers",
  label: "Loan Brokers",
  headline: "Every application pre-qualified. Every lead nurtured.",
  intro:
    "From home loans to business finance — IIEVI automates lead capture, pre-qualification, and lender matching for loan brokers.",
  playbook: [
    {
      stepNumber: "01",
      heading: "Onboarding",
      description:
        "Connect your brokerage in minutes. Answer a few questions about your loan products, lender network, and target audience. The AI configures a workflow designed for financial services.",
      highlightsLabel: "Highlights",
      highlights: ["2-minute setup", "No technical expertise required", "AI-guided configuration"],
      mockup: {
        type: "onboarding",
        data: {
          businessName: "FinBridge Loans",
          industry: "Loan Brokerage",
          goals: ["Generate Leads", "Pre-qualify Applicants", "Schedule Consultations"],
          selectedGoal: 0,
        },
      },
    },
    {
      stepNumber: "02",
      heading: "Create Business Profile",
      description:
        "Build your digital brokerage identity. The AI learns your loan products, lender tie-ups, interest rate ranges, and eligibility criteria to answer applicant queries accurately.",
      highlightsLabel: "What AI learns",
      highlights: ["Loan products & rates", "Lender partnerships", "Eligibility criteria"],
      mockup: {
        type: "business-profile",
        data: {
          brandVoice: "Expert & Transparent",
          products: [
            "Home Loans — from 8.5%",
            "Business Loans — from 10.5%",
            "Personal Loans — from 11%",
          ],
          targetAudience: "Salaried & Self-employed",
          profileComplete: 80,
        },
      },
    },
    {
      stepNumber: "03",
      heading: "Secure API Integration",
      description:
        "Connect your channels securely. Financial data demands the highest security — credentials are encrypted, isolated per workspace, and never shared.",
      highlightsLabel: "Security Features",
      highlights: SHARED_SECURITY_HIGHLIGHTS,
      mockup: {
        type: "secure-api",
        data: {
          platforms: SHARED_PLATFORMS,
          statusItems: SHARED_API_STATUS,
          securityScore: 100,
        },
      },
    },
    {
      stepNumber: "04",
      heading: "Start Conversation",
      description:
        "Tell the AI what you want to promote. Describe a loan offer and the AI creates educational content and lead-generation campaigns for your target segment.",
      highlightsLabel: "Capabilities",
      highlights: [
        "Natural language prompts",
        "Regulatory-aware content",
        "Segment-targeted campaigns",
      ],
      mockup: {
        type: "ai-command",
        data: {
          prompt:
            "Create content about low-interest home loan options for salaried professionals in metro cities.",
        },
      },
    },
    {
      stepNumber: "05",
      heading: "AI Content Generation",
      description:
        "Generate high-performing financial content automatically. The system creates rate comparisons, eligibility guides, and EMI calculators that attract serious applicants.",
      highlightsLabel: "Output",
      highlights: ["Rate comparison posts", "Eligibility guides", "EMI calculator content"],
      mockup: {
        type: "content-generator",
        data: {
          campaignName: "Home Loan Festival — Q3",
          channels: [
            "Instagram Post",
            "Facebook Post",
            "Google Business Update",
            "WhatsApp Broadcast",
          ],
        },
      },
    },
    {
      stepNumber: "06",
      heading: "Publish Everywhere",
      description:
        "Reach potential borrowers wherever they research. One click distributes content across all platforms with income-segment and city-level targeting.",
      highlightsLabel: "Channels",
      highlights: ["Cross-platform publishing", "Income-segment targeting", "City-level reach"],
      mockup: {
        type: "publishing",
        data: {
          platforms: SHARED_PUBLISH_PLATFORMS,
          reach: 22180,
        },
      },
    },
    {
      stepNumber: "07",
      heading: "AI Handles Conversations",
      description:
        "Never miss an applicant. When someone asks about rates, eligibility, or EMI, the AI responds instantly with personalised options from your lender network.",
      highlightsLabel: "Intelligence",
      highlights: ["Instant rate lookup", "Pre-qualification checks", "Lender matching"],
      mockup: {
        type: "ai-conversation",
        data: {
          customerMessage: "What's the best rate for a 50L home loan? I'm salaried, 12L annual.",
          aiResponse:
            "Based on current offers, SBI is at 8.5% and HDFC at 8.65% for your profile. EMI would be approx ₹43,391/mo for 20 years. Shall I check your pre-approval eligibility?",
          responseTime: "3 sec",
        },
      },
    },
    {
      stepNumber: "08",
      heading: "Booking Offered",
      description:
        "Turn enquiries into consultations. When the AI confirms eligibility, it auto-schedules a consultation and sends the applicant a document checklist.",
      highlightsLabel: "Pipeline",
      highlights: ["Eligibility pre-check", "Auto-consultation booking", "Document checklist sent"],
      mockup: {
        type: "lead-pipeline",
        data: {
          stages: [
            "New Enquiry",
            "Pre-qualified",
            "Documents Collected",
            "Lender Matched",
            "Application Submitted",
          ],
          activeStage: 3,
          leadScore: 92,
        },
      },
    },
  ],
  finalStats: [
    { label: "Posts Generated", value: 41 },
    { label: "Posts Published", value: 41 },
    { label: "Leads Captured", value: 156 },
    { label: "Conversations Handled", value: 389 },
    { label: "Consultations Booked", value: 58 },
  ],
};

// ── Exports ──────────────────────────────────────────────

export const SOLUTION_CATEGORIES: Record<string, CategoryData> = {
  "pet-wellness": petWellness,
  plumbing,
  electrician,
  "real-estate": realEstate,
  "loan-brokers": loanBrokers,
};

export const CATEGORY_SLUGS = Object.keys(SOLUTION_CATEGORIES);

export function getCategoryData(slug: string): CategoryData | undefined {
  if (Object.prototype.hasOwnProperty.call(SOLUTION_CATEGORIES, slug)) {
    return SOLUTION_CATEGORIES[slug as keyof typeof SOLUTION_CATEGORIES];
  }
  return undefined;
}
