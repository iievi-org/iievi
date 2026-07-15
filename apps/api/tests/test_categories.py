"""Sync and sanity tests for the business category configs.

The TypeScript side (packages/constants/src/categories.ts) is checked by its
own type system — `CATEGORIES: Record<BusinessCategory, CategoryConfig>` fails
to compile if any of the 16 keys is missing or misspelled. This test pins the
Python mirror to the same hardcoded key set.
"""

from app.modules.profiles.categories import CATEGORIES, CATEGORY_KEYS

# Mirror of BUSINESS_CATEGORIES in packages/constants/src/index.ts.
BUSINESS_CATEGORIES: tuple[str, ...] = (
    "home_cleaning",
    "plumbing",
    "electrical",
    "wedding_photography",
    "interior_design",
    "personal_training",
    "salon_beauty",
    "pet_care",
    "tutoring",
    "catering",
    "event_planning",
    "ac_appliance_repair",
    "pest_control",
    "physiotherapy",
    "yoga_wellness",
    "landscaping",
)


def test_category_keys_match_business_categories() -> None:
    assert CATEGORY_KEYS == BUSINESS_CATEGORIES


def test_configs_are_well_formed() -> None:
    for key, config in CATEGORIES.items():
        assert config.key == key
        assert 4 <= len(config.qualification_questions) <= 6, key
        assert 3 <= len(config.default_services) <= 5, key
        for service in config.default_services:
            assert service.price_min_paise < service.price_max_paise, (key, service.name)
