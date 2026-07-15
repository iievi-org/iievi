"""Category configurations for the 16 supported business categories.

MUST stay in sync with packages/constants/src/categories.ts — same keys,
same questions, same paise price ranges. A mismatch between the two files
causes silent validation failures in lead qualification and onboarding.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceTemplate:
    """A default service offering with an INR price range in paise."""

    name: str
    price_min_paise: int
    price_max_paise: int
    unit: str


@dataclass(frozen=True)
class CategoryConfig:
    """Per-category lead qualification, pricing and content configuration."""

    key: str
    display_name: str
    emoji: str
    description: str
    urgency_level: str  # high | medium | low
    pricing_type: str  # package | per_job | hourly | subscription | quote
    qualification_questions: tuple[str, ...]
    default_services: tuple[ServiceTemplate, ...]
    suggested_discount_policy: str
    template_style: str
    image_style_notes: str
    ai_tone_notes: str


CATEGORIES: dict[str, CategoryConfig] = {
    "home_cleaning": CategoryConfig(
        key="home_cleaning",
        display_name="Home Cleaning",
        emoji="🧹",
        description="Professional deep and regular cleaning for homes and apartments.",
        urgency_level="medium",
        pricing_type="per_job",
        qualification_questions=(
            "What size is your home — 1BHK, 2BHK, 3BHK or a villa?",
            "Do you need a deep clean, regular clean, or move-in/move-out cleaning?",
            "Which area and pin code is the home in?",
            "Is the home currently occupied or vacant?",
            "Any pets at home, or specific areas needing extra attention like kitchen or "
            "balconies?",
            "What date and time slot works best for you?",
        ),
        default_services=(
            ServiceTemplate(
                name="Deep cleaning — 1BHK",
                price_min_paise=180000,
                price_max_paise=300000,
                unit="per 1BHK",
            ),
            ServiceTemplate(
                name="Deep cleaning — 2BHK",
                price_min_paise=250000,
                price_max_paise=450000,
                unit="per 2BHK",
            ),
            ServiceTemplate(
                name="Deep cleaning — 3BHK",
                price_min_paise=350000,
                price_max_paise=600000,
                unit="per 3BHK",
            ),
            ServiceTemplate(
                name="Sofa shampooing",
                price_min_paise=25000,
                price_max_paise=50000,
                unit="per seat",
            ),
            ServiceTemplate(
                name="Bathroom deep clean",
                price_min_paise=45000,
                price_max_paise=80000,
                unit="per bathroom",
            ),
        ),
        suggested_discount_policy=(
            "10% off the first booking; 15% off on quarterly deep-clean subscriptions."
        ),
        template_style="before/after grid",
        image_style_notes=(
            "Bright, airy interiors with visible before/after contrast; sparkling tiles and "
            "sunlight through windows. Clean whites and fresh blues, uniformed staff with branded "
            "equipment."
        ),
        ai_tone_notes=(
            "Warm and reassuring; emphasise trained, background-verified staff and safe chemicals. "
            "Confirm size and date quickly and offer a firm slot."
        ),
    ),
    "plumbing": CategoryConfig(
        key="plumbing",
        display_name="Plumbing Services",
        emoji="🔧",
        description="Repairs, fittings and full bathroom plumbing work for homes and offices.",
        urgency_level="high",
        pricing_type="per_job",
        qualification_questions=(
            "What's the issue — a leak, blockage, low pressure, or a new fitting/installation?",
            "Which area and pin code should the plumber come to?",
            "How urgent is it — is water leaking or overflowing right now?",
            "Can you share a photo or short video of the problem?",
            "Is it an apartment or independent house, and which floor?",
        ),
        default_services=(
            ServiceTemplate(
                name="Tap/faucet repair or replacement",
                price_min_paise=15000,
                price_max_paise=50000,
                unit="per fitting",
            ),
            ServiceTemplate(
                name="Drain/blockage clearing",
                price_min_paise=30000,
                price_max_paise=150000,
                unit="per job",
            ),
            ServiceTemplate(
                name="Bathroom leakage detection & fix",
                price_min_paise=50000,
                price_max_paise=250000,
                unit="per job",
            ),
            ServiceTemplate(
                name="Wash basin/sanitaryware installation",
                price_min_paise=40000,
                price_max_paise=120000,
                unit="per unit",
            ),
            ServiceTemplate(
                name="Full bathroom plumbing renovation",
                price_min_paise=800000,
                price_max_paise=2500000,
                unit="per bathroom",
            ),
        ),
        suggested_discount_policy=(
            "10% off scheduled repair visits; no discounts on emergency call-outs."
        ),
        template_style="problem/solution card",
        image_style_notes=(
            "Close-up shots of gleaming chrome fittings and tidy pipe work; a professional in "
            "uniform with a toolbox. Blue and steel-grey palette, crisp and trustworthy."
        ),
        ai_tone_notes=(
            "Fast, calm and practical — for emergencies, get the address and dispatch details "
            "first, pricing second. Reassure about visiting charges being adjusted in the bill."
        ),
    ),
    "electrical": CategoryConfig(
        key="electrical",
        display_name="Electrical Services",
        emoji="⚡",
        description="Licensed electricians for repairs, installations and wiring work.",
        urgency_level="high",
        pricing_type="per_job",
        qualification_questions=(
            "What's the problem — no power, tripping MCB, sparking, or a new installation?",
            "Is the issue in one room or the whole house?",
            "Which area and pin code should the electrician come to?",
            "Is there any sparking, burning smell or exposed wiring right now?",
            "Is it an apartment or independent house, and roughly how old is the wiring?",
        ),
        default_services=(
            ServiceTemplate(
                name="Switch/socket repair or replacement",
                price_min_paise=10000,
                price_max_paise=35000,
                unit="per point",
            ),
            ServiceTemplate(
                name="Ceiling fan installation",
                price_min_paise=25000,
                price_max_paise=60000,
                unit="per fan",
            ),
            ServiceTemplate(
                name="Inverter installation",
                price_min_paise=80000,
                price_max_paise=200000,
                unit="per unit",
            ),
            ServiceTemplate(
                name="MCB/distribution board repair",
                price_min_paise=40000,
                price_max_paise=150000,
                unit="per job",
            ),
            ServiceTemplate(
                name="Full house rewiring — 1BHK",
                price_min_paise=1500000,
                price_max_paise=4000000,
                unit="per 1BHK",
            ),
        ),
        suggested_discount_policy=(
            "Free inspection with any repair above ₹500; no discounts on emergency visits."
        ),
        template_style="safety-tip carousel",
        image_style_notes=(
            "Neat switchboards, organised wiring and an electrician with insulated tools; warm "
            "indoor lighting. Yellow-and-black safety accents without looking industrial."
        ),
        ai_tone_notes=(
            "Safety-first and urgent — if sparking or burning smell is mentioned, advise switching "
            "off the mains and prioritise dispatch. Keep questions short and sequential."
        ),
    ),
    "wedding_photography": CategoryConfig(
        key="wedding_photography",
        display_name="Wedding Photography",
        emoji="📸",
        description="Candid and traditional wedding photography and films across events.",
        urgency_level="medium",
        pricing_type="package",
        qualification_questions=(
            "What's the wedding date and city?",
            "Is the venue finalised — if yes, which one?",
            "Which events do you want covered — haldi, mehendi, sangeet, wedding, reception?",
            "Do you want candid photography, traditional, or both — and do you also need "
            "video/cinematic film?",
            "Roughly how many guests are expected at the main functions?",
            "What budget range are you considering for photography?",
        ),
        default_services=(
            ServiceTemplate(
                name="Single-day wedding shoot (candid + traditional)",
                price_min_paise=4000000,
                price_max_paise=10000000,
                unit="per day",
            ),
            ServiceTemplate(
                name="Full wedding package — 3 events, photo + video",
                price_min_paise=12000000,
                price_max_paise=35000000,
                unit="per package",
            ),
            ServiceTemplate(
                name="Pre-wedding shoot",
                price_min_paise=1500000,
                price_max_paise=5000000,
                unit="per shoot",
            ),
            ServiceTemplate(
                name="Cinematic wedding film add-on",
                price_min_paise=5000000,
                price_max_paise=15000000,
                unit="per film",
            ),
            ServiceTemplate(
                name="Premium wedding album",
                price_min_paise=800000,
                price_max_paise=2500000,
                unit="per album",
            ),
        ),
        suggested_discount_policy=(
            "5-10% off on full multi-event packages booked 6+ months in advance; no discounts on "
            "single-day peak-season dates."
        ),
        template_style="cinematic photo carousel",
        image_style_notes=(
            "Rich, golden-hour candid wedding moments — varmala, sangeet dance, emotional family "
            "shots. Warm tones, shallow depth of field, Indian bridal reds and golds."
        ),
        ai_tone_notes=(
            "Emotive and consultative — congratulate the couple first, then gather date and "
            "events. Emphasise limited dates per season to create gentle urgency."
        ),
    ),
    "interior_design": CategoryConfig(
        key="interior_design",
        display_name="Interior Design",
        emoji="🛋️",
        description="End-to-end home and office interiors, from design to execution.",
        urgency_level="low",
        pricing_type="quote",
        qualification_questions=(
            "What's the property — 2BHK, 3BHK, villa or office — and the carpet area?",
            "Which city and locality is the project in?",
            "Do you want full-home interiors or specific rooms like kitchen and wardrobes?",
            "Have you received possession, and what's your target completion timeline?",
            "Any style preference — modern, minimal, traditional, or something you've saved on "
            "Instagram?",
            "What budget band are you planning — under ₹5L, ₹5-10L, ₹10-20L, or above?",
        ),
        default_services=(
            ServiceTemplate(
                name="Design consultation & 3D concept",
                price_min_paise=200000,
                price_max_paise=500000,
                unit="per visit",
            ),
            ServiceTemplate(
                name="Modular kitchen",
                price_min_paise=12000000,
                price_max_paise=35000000,
                unit="per kitchen",
            ),
            ServiceTemplate(
                name="Full 2BHK interiors",
                price_min_paise=40000000,
                price_max_paise=90000000,
                unit="per 2BHK",
            ),
            ServiceTemplate(
                name="Full 3BHK interiors",
                price_min_paise=65000000,
                price_max_paise=150000000,
                unit="per 3BHK",
            ),
            ServiceTemplate(
                name="Sliding/hinged wardrobe",
                price_min_paise=4000000,
                price_max_paise=12000000,
                unit="per wardrobe",
            ),
        ),
        suggested_discount_policy=(
            "Consultation fee fully adjusted against the project value on booking; no flat "
            "discounts on materials."
        ),
        template_style="room transformation reel",
        image_style_notes=(
            "Magazine-quality wide shots of finished Indian living rooms and modular kitchens; "
            "warm woods, brass accents, layered lighting. Aspirational but achievable, not "
            "palatial."
        ),
        ai_tone_notes=(
            "Consultative and unhurried — this is a big-ticket decision, so focus on understanding "
            "scope and budget band before talking numbers. Offer a free/adjustable design "
            "consultation as the next step."
        ),
    ),
    "personal_training": CategoryConfig(
        key="personal_training",
        display_name="Personal Training",
        emoji="💪",
        description="Certified personal trainers for home, gym and online fitness coaching.",
        urgency_level="medium",
        pricing_type="subscription",
        qualification_questions=(
            "What's your main goal — weight loss, muscle gain, strength, or general fitness?",
            "Do you prefer training at home, at a gym, or online?",
            "Which area and pin code are you in, if you want home sessions?",
            "What's your current activity level, and any injuries or health conditions I should "
            "know about?",
            "How many sessions per week are you planning, and what time slot suits you?",
        ),
        default_services=(
            ServiceTemplate(
                name="Monthly PT — 3 sessions/week (home)",
                price_min_paise=600000,
                price_max_paise=1200000,
                unit="per month",
            ),
            ServiceTemplate(
                name="Monthly PT — 5 sessions/week (home)",
                price_min_paise=900000,
                price_max_paise=1800000,
                unit="per month",
            ),
            ServiceTemplate(
                name="Online coaching plan",
                price_min_paise=300000,
                price_max_paise=700000,
                unit="per month",
            ),
            ServiceTemplate(
                name="Trial session",
                price_min_paise=50000,
                price_max_paise=100000,
                unit="per session",
            ),
            ServiceTemplate(
                name="Customised diet + workout plan",
                price_min_paise=200000,
                price_max_paise=500000,
                unit="per plan",
            ),
        ),
        suggested_discount_policy=(
            "Trial session fee adjusted in the first month; 10% off on quarterly prepaid plans."
        ),
        template_style="client transformation spotlight",
        image_style_notes=(
            "Energetic training moments and authentic client transformation collages; natural gym "
            "or home-workout lighting. Bold typography for stats like weight lost or strength "
            "gained."
        ),
        ai_tone_notes=(
            "Motivating but not pushy — acknowledge the goal, ask about injuries sensitively, and "
            "push the low-commitment trial session as the first step."
        ),
    ),
    "salon_beauty": CategoryConfig(
        key="salon_beauty",
        display_name="Salon & Beauty",
        emoji="💇",
        description="Salon services, skincare and bridal makeup — in-salon or at home.",
        urgency_level="medium",
        pricing_type="per_job",
        qualification_questions=(
            "Which services are you looking for — hair, facial, waxing, makeup, or a combination?",
            "Would you like to visit the salon or prefer the service at home?",
            "Which area and pin code, if you'd like a home service?",
            "Is this for a special occasion like a wedding, party or festival?",
            "What date and time slot works for you?",
        ),
        default_services=(
            ServiceTemplate(
                name="Haircut & styling (women)",
                price_min_paise=50000,
                price_max_paise=150000,
                unit="per session",
            ),
            ServiceTemplate(
                name="Facial (classic to premium)",
                price_min_paise=80000,
                price_max_paise=300000,
                unit="per session",
            ),
            ServiceTemplate(
                name="Bridal makeup package",
                price_min_paise=1500000,
                price_max_paise=5000000,
                unit="per package",
            ),
            ServiceTemplate(
                name="Party makeup",
                price_min_paise=250000,
                price_max_paise=800000,
                unit="per session",
            ),
            ServiceTemplate(
                name="Hair colour/highlights",
                price_min_paise=200000,
                price_max_paise=800000,
                unit="per session",
            ),
        ),
        suggested_discount_policy=(
            "15% off first-time home service; festive combo offers instead of discounts on bridal "
            "packages."
        ),
        template_style="glam before/after reel",
        image_style_notes=(
            "Soft glam close-ups — glowing skin, bridal makeup looks, styled hair; pastel and "
            "rose-gold palette. Clean salon interiors or elegant at-home setups, Indian skin tones "
            "front and centre."
        ),
        ai_tone_notes=(
            "Friendly and pampering — mirror the customer's excitement for occasions, suggest "
            "combos, and confirm the slot fast since good slots fill up on weekends."
        ),
    ),
    "pet_care": CategoryConfig(
        key="pet_care",
        display_name="Pet Care",
        emoji="🐾",
        description="Grooming, boarding, walking and daycare for dogs and cats.",
        urgency_level="medium",
        pricing_type="per_job",
        qualification_questions=(
            "What pet do you have — dog or cat — and which breed?",
            "Which service do you need — grooming, boarding, daily walking, or daycare?",
            "How old is your pet, and are vaccinations up to date?",
            "Is your pet comfortable with strangers, or anxious/aggressive around new people?",
            "Which area and pin code are you in — and do you need home pickup?",
            "For boarding: what are the drop-off and pickup dates?",
        ),
        default_services=(
            ServiceTemplate(
                name="Dog grooming — bath, trim & nails",
                price_min_paise=80000,
                price_max_paise=250000,
                unit="per session",
            ),
            ServiceTemplate(
                name="Pet boarding",
                price_min_paise=40000,
                price_max_paise=100000,
                unit="per day",
            ),
            ServiceTemplate(
                name="Daily dog walking (monthly)",
                price_min_paise=200000,
                price_max_paise=500000,
                unit="per month",
            ),
            ServiceTemplate(
                name="Cat grooming",
                price_min_paise=70000,
                price_max_paise=200000,
                unit="per session",
            ),
            ServiceTemplate(
                name="Pet taxi / home pickup",
                price_min_paise=30000,
                price_max_paise=80000,
                unit="per trip",
            ),
        ),
        suggested_discount_policy=(
            "10% off the first grooming session; weekly boarding priced at 6 days for 7."
        ),
        template_style="cute pet spotlight",
        image_style_notes=(
            "Happy, freshly groomed pets in bright natural light; playful compositions with "
            "paw-print motifs. Real grooming shots over stock-style perfection."
        ),
        ai_tone_notes=(
            "Affectionate and detail-oriented — use the pet's name once shared, and proactively "
            "reassure about hygiene, vaccination checks and gentle handling."
        ),
    ),
    "tutoring": CategoryConfig(
        key="tutoring",
        display_name="Tutoring & Coaching",
        emoji="📚",
        description="Home, online and centre-based tutoring for school and entrance exams.",
        urgency_level="medium",
        pricing_type="subscription",
        qualification_questions=(
            "Which class is the student in, and which board — CBSE, ICSE or State?",
            "Which subjects do you need help with?",
            "Do you prefer home tuition, online classes, or visiting the tutor/centre?",
            "Which area and pin code are you in, if home tuition?",
            "Is there a specific exam target — boards, JEE, NEET, Olympiads — and how is the "
            "student doing currently?",
            "How many classes per week are you looking at?",
        ),
        default_services=(
            ServiceTemplate(
                name="Class 6-8 all subjects (monthly)",
                price_min_paise=250000,
                price_max_paise=600000,
                unit="per month",
            ),
            ServiceTemplate(
                name="Class 9-10 maths & science (monthly)",
                price_min_paise=350000,
                price_max_paise=800000,
                unit="per month",
            ),
            ServiceTemplate(
                name="Class 11-12 PCM/PCB (per subject, monthly)",
                price_min_paise=400000,
                price_max_paise=1000000,
                unit="per subject per month",
            ),
            ServiceTemplate(
                name="JEE/NEET crash course",
                price_min_paise=1500000,
                price_max_paise=4000000,
                unit="per course",
            ),
            ServiceTemplate(
                name="Spoken English (monthly)",
                price_min_paise=200000,
                price_max_paise=500000,
                unit="per month",
            ),
        ),
        suggested_discount_policy=(
            "First demo class free; 10% off on quarterly fee payment, sibling discount of 15%."
        ),
        template_style="result/rank announcement card",
        image_style_notes=(
            "Clean academic layouts — student result highlights, marks improvement graphics, tutor "
            "at a whiteboard. Trustworthy blues and whites with bold percentage/rank callouts."
        ),
        ai_tone_notes=(
            "Respectful and parent-friendly — parents are usually the decision makers, so address "
            "concerns about results and discipline, and always offer the free demo class."
        ),
    ),
    "catering": CategoryConfig(
        key="catering",
        display_name="Catering Services",
        emoji="🍽️",
        description="Wedding, party and corporate catering with customisable menus.",
        urgency_level="medium",
        pricing_type="quote",
        qualification_questions=(
            "What's the occasion — wedding, birthday, housewarming, or corporate event — and the "
            "date?",
            "Which city and venue/locality is the event at?",
            "Roughly how many guests are you expecting?",
            "Veg, non-veg or Jain — and any cuisine preference like North Indian, South Indian or "
            "multi-cuisine?",
            "Do you want buffet or sit-down service, and any live counters like chaat or dosa?",
            "What per-plate budget are you targeting?",
        ),
        default_services=(
            ServiceTemplate(
                name="Veg buffet",
                price_min_paise=25000,
                price_max_paise=60000,
                unit="per plate",
            ),
            ServiceTemplate(
                name="Non-veg buffet",
                price_min_paise=35000,
                price_max_paise=90000,
                unit="per plate",
            ),
            ServiceTemplate(
                name="Premium wedding menu",
                price_min_paise=80000,
                price_max_paise=180000,
                unit="per plate",
            ),
            ServiceTemplate(
                name="Live counter add-on (chaat/dosa)",
                price_min_paise=800000,
                price_max_paise=2000000,
                unit="per counter",
            ),
            ServiceTemplate(
                name="Corporate lunch boxes",
                price_min_paise=12000,
                price_max_paise=30000,
                unit="per box",
            ),
        ),
        suggested_discount_policy=(
            "Per-plate rates negotiable above 200 guests; free tasting session for confirmed "
            "wedding enquiries."
        ),
        template_style="menu highlight grid",
        image_style_notes=(
            "Overhead spreads of Indian thalis, live counters with steam and garnish close-ups; "
            "rich, saturated food photography. Banana leaf, copper serveware and festive table "
            "styling."
        ),
        ai_tone_notes=(
            "Hospitable and flexible — lead with menu possibilities, not price. Lock guest count "
            "and date early, and offer a tasting to move serious leads forward."
        ),
    ),
    "event_planning": CategoryConfig(
        key="event_planning",
        display_name="Event Planning",
        emoji="🎉",
        description=(
            "Decor, management and full planning for weddings, parties and corporate events."
        ),
        urgency_level="medium",
        pricing_type="quote",
        qualification_questions=(
            "What's the event — wedding, birthday, anniversary, or corporate — and the date?",
            "Which city, and is the venue already booked?",
            "How many guests are you expecting?",
            "Do you need decor only, or full planning — vendors, catering, entertainment, the "
            "works?",
            "Any theme or reference pictures you have in mind?",
            "What overall budget band are you working with?",
        ),
        default_services=(
            ServiceTemplate(
                name="Birthday party decor",
                price_min_paise=500000,
                price_max_paise=2500000,
                unit="per event",
            ),
            ServiceTemplate(
                name="Wedding decor package",
                price_min_paise=7500000,
                price_max_paise=30000000,
                unit="per event",
            ),
            ServiceTemplate(
                name="Corporate event management",
                price_min_paise=5000000,
                price_max_paise=25000000,
                unit="per event",
            ),
            ServiceTemplate(
                name="Full wedding planning",
                price_min_paise=15000000,
                price_max_paise=60000000,
                unit="per wedding",
            ),
        ),
        suggested_discount_policy=(
            "Complimentary theme mock-up on bookings above ₹1L; early-bird pricing for off-season "
            "dates."
        ),
        template_style="event showcase carousel",
        image_style_notes=(
            "Dramatic wide shots of mandaps, balloon arches and stage decor with fairy lights; "
            "vibrant marigold, pastel and royal themes. Show scale and detail shots together."
        ),
        ai_tone_notes=(
            "Enthusiastic and organised — match the excitement of the occasion, gather "
            "date/venue/guest count fast, and position a free concept call as the next step."
        ),
    ),
    "ac_appliance_repair": CategoryConfig(
        key="ac_appliance_repair",
        display_name="AC & Appliance Repair",
        emoji="❄️",
        description="Repair and servicing for ACs, refrigerators, washing machines and more.",
        urgency_level="high",
        pricing_type="per_job",
        qualification_questions=(
            "Which appliance needs attention — AC, refrigerator, washing machine, geyser — and "
            "which brand?",
            "What's the problem — not cooling, not starting, noise, or water leakage?",
            "For ACs: split or window, and how many units?",
            "How old is the appliance, and is it under warranty or AMC?",
            "Which area and pin code should the technician come to, and how soon do you need the "
            "visit?",
        ),
        default_services=(
            ServiceTemplate(
                name="AC service (jet/wet)",
                price_min_paise=45000,
                price_max_paise=80000,
                unit="per unit",
            ),
            ServiceTemplate(
                name="AC gas refill",
                price_min_paise=180000,
                price_max_paise=350000,
                unit="per unit",
            ),
            ServiceTemplate(
                name="AC installation/uninstallation",
                price_min_paise=120000,
                price_max_paise=250000,
                unit="per unit",
            ),
            ServiceTemplate(
                name="Washing machine repair",
                price_min_paise=40000,
                price_max_paise=200000,
                unit="per job",
            ),
            ServiceTemplate(
                name="Refrigerator repair",
                price_min_paise=50000,
                price_max_paise=250000,
                unit="per job",
            ),
        ),
        suggested_discount_policy=(
            "Visiting charge waived if repair is done; 20% off per-unit servicing for 3+ ACs."
        ),
        template_style="seasonal service reminder",
        image_style_notes=(
            "Technician servicing a split AC with clean tools and covered flooring; cool blue "
            "tones for summer campaigns. Simple icon-led graphics for service checklists."
        ),
        ai_tone_notes=(
            "Prompt and transparent — summer AC leads are extremely time-sensitive, so confirm "
            "locality and slot immediately. Be upfront that final quote follows inspection."
        ),
    ),
    "pest_control": CategoryConfig(
        key="pest_control",
        display_name="Pest Control",
        emoji="🐜",
        description="Safe, odourless pest control for homes, offices and societies.",
        urgency_level="medium",
        pricing_type="per_job",
        qualification_questions=(
            "Which pest is the problem — cockroaches, termites, bed bugs, mosquitoes, or rodents?",
            "What's the property — 1BHK, 2BHK, 3BHK, villa or office — and approximate area?",
            "How long have you noticed the problem, and how severe is it?",
            "Do you want a one-time treatment or an annual contract (AMC)?",
            "Are there kids, elderly people or pets at home?",
            "Which area and pin code is the property in?",
        ),
        default_services=(
            ServiceTemplate(
                name="General pest control — 1BHK",
                price_min_paise=80000,
                price_max_paise=150000,
                unit="per 1BHK",
            ),
            ServiceTemplate(
                name="General pest control — 2BHK",
                price_min_paise=100000,
                price_max_paise=200000,
                unit="per 2BHK",
            ),
            ServiceTemplate(
                name="Cockroach gel treatment",
                price_min_paise=70000,
                price_max_paise=150000,
                unit="per treatment",
            ),
            ServiceTemplate(
                name="Anti-termite treatment",
                price_min_paise=350000,
                price_max_paise=900000,
                unit="per 1,000 sq ft",
            ),
            ServiceTemplate(
                name="Bed bug treatment — 2BHK",
                price_min_paise=200000,
                price_max_paise=450000,
                unit="per 2BHK",
            ),
        ),
        suggested_discount_policy=(
            "Free re-service within 30 days if pests return; 20% effective saving on annual "
            "contracts vs one-time visits."
        ),
        template_style="myth-buster infographic",
        image_style_notes=(
            "Clean, clinical visuals — technician with sprayer in a bright home, safety icons for "
            "kid/pet-safe chemicals. Avoid gross close-ups of pests; use subtle illustrated icons "
            "instead."
        ),
        ai_tone_notes=(
            "Reassuring and educational — address safety for kids and pets proactively, explain "
            "odourless/herbal options, and recommend AMC where infestation is recurring."
        ),
    ),
    "physiotherapy": CategoryConfig(
        key="physiotherapy",
        display_name="Physiotherapy",
        emoji="🩺",
        description="Clinic and home-visit physiotherapy for pain, injury and rehabilitation.",
        urgency_level="high",
        pricing_type="per_job",
        qualification_questions=(
            "What's the concern — back/neck pain, knee pain, sports injury, post-surgery rehab, "
            "or neuro rehab?",
            "How long has this been troubling you, and do you have a doctor's referral or recent "
            "reports?",
            "Would you prefer home visits or coming to the clinic?",
            "Which area and pin code, if home visits?",
            "What's the patient's age and current mobility level?",
            "Which time slots work best for sessions?",
        ),
        default_services=(
            ServiceTemplate(
                name="Home visit session",
                price_min_paise=50000,
                price_max_paise=120000,
                unit="per session",
            ),
            ServiceTemplate(
                name="Clinic session",
                price_min_paise=30000,
                price_max_paise=80000,
                unit="per session",
            ),
            ServiceTemplate(
                name="Post-surgery rehab package (12 sessions)",
                price_min_paise=600000,
                price_max_paise=1400000,
                unit="per package",
            ),
            ServiceTemplate(
                name="Back/neck pain package (10 sessions)",
                price_min_paise=450000,
                price_max_paise=1000000,
                unit="per package",
            ),
        ),
        suggested_discount_policy=(
            "First assessment at 50% off; package rates already discounted — no further discounts "
            "on packages."
        ),
        template_style="recovery journey story",
        image_style_notes=(
            "Gentle, hopeful imagery — therapist guiding an exercise at home, senior patients "
            "smiling mid-recovery. Soft greens and whites, medical credibility without hospital "
            "coldness."
        ),
        ai_tone_notes=(
            "Empathetic and clinical — acknowledge the pain first, never promise a cure, and "
            "encourage sharing reports. Someone in pain books fast, so offer the earliest "
            "assessment slot."
        ),
    ),
    "yoga_wellness": CategoryConfig(
        key="yoga_wellness",
        display_name="Yoga & Wellness",
        emoji="🧘",
        description="Group and personal yoga, meditation and holistic wellness programs.",
        urgency_level="low",
        pricing_type="subscription",
        qualification_questions=(
            "What's your goal — flexibility, stress relief, weight management, or therapy for "
            "issues like PCOS, thyroid or back pain?",
            "Do you prefer group classes, personal sessions at home, or online?",
            "Have you practised yoga before, and any health conditions or injuries?",
            "Which area and pin code, if you want home sessions?",
            "Do mornings or evenings work better for you?",
        ),
        default_services=(
            ServiceTemplate(
                name="Group classes at studio (monthly)",
                price_min_paise=150000,
                price_max_paise=350000,
                unit="per month",
            ),
            ServiceTemplate(
                name="Personal yoga at home (monthly, 5 days/week)",
                price_min_paise=500000,
                price_max_paise=1200000,
                unit="per month",
            ),
            ServiceTemplate(
                name="Online group batch (monthly)",
                price_min_paise=100000,
                price_max_paise=250000,
                unit="per month",
            ),
            ServiceTemplate(
                name="Corporate wellness session",
                price_min_paise=250000,
                price_max_paise=800000,
                unit="per session",
            ),
            ServiceTemplate(
                name="Trial class",
                price_min_paise=20000,
                price_max_paise=50000,
                unit="per class",
            ),
        ),
        suggested_discount_policy=(
            "Trial class fee adjusted on enrolment; 15% off on quarterly memberships."
        ),
        template_style="calm quote + pose visual",
        image_style_notes=(
            "Serene sunrise practice shots, clean mats, plants and natural light; muted earth "
            "tones and soft gradients. Minimal text overlays with breathing-room layouts."
        ),
        ai_tone_notes=(
            "Calm and welcoming — never body-shame or over-promise health outcomes. Gently ask "
            "about health conditions and steer beginners to the trial class."
        ),
    ),
    "landscaping": CategoryConfig(
        key="landscaping",
        display_name="Landscaping & Gardening",
        emoji="🌿",
        description="Garden design, terrace/balcony setups and ongoing maintenance.",
        urgency_level="low",
        pricing_type="quote",
        qualification_questions=(
            "What space are we working with — villa garden, terrace, balcony, or society common "
            "area?",
            "What's the approximate area in square feet?",
            "Is this a new setup/makeover, or ongoing maintenance?",
            "Which city and locality is the property in?",
            "Is there a water point available, and how much sunlight does the space get?",
            "What budget range do you have in mind?",
        ),
        default_services=(
            ServiceTemplate(
                name="Balcony garden setup",
                price_min_paise=500000,
                price_max_paise=2000000,
                unit="per balcony",
            ),
            ServiceTemplate(
                name="Terrace garden setup",
                price_min_paise=1500000,
                price_max_paise=6000000,
                unit="per terrace",
            ),
            ServiceTemplate(
                name="Lawn installation",
                price_min_paise=4000,
                price_max_paise=9000,
                unit="per sq ft",
            ),
            ServiceTemplate(
                name="Monthly garden maintenance",
                price_min_paise=150000,
                price_max_paise=500000,
                unit="per month",
            ),
            ServiceTemplate(
                name="Vertical garden wall",
                price_min_paise=60000,
                price_max_paise=150000,
                unit="per sq ft",
            ),
        ),
        suggested_discount_policy=(
            "Free site visit and layout sketch for projects above ₹10,000; 10% off annual "
            "maintenance contracts."
        ),
        template_style="garden transformation timelapse",
        image_style_notes=(
            "Lush green terraces and balconies against city skylines; golden-hour light on "
            "planters and vertical gardens. Before/after pairs showing bare concrete turning "
            "green."
        ),
        ai_tone_notes=(
            "Passionate and advisory — ask about sunlight and water before promising plant "
            "choices, and offer the free site visit to convert browsers into bookings."
        ),
    ),
}

CATEGORY_KEYS: tuple[str, ...] = tuple(CATEGORIES)
