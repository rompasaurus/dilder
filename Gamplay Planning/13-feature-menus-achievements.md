# Feature Systems, Menus & Achievement Viewer

> Implementation spec for the in-game achievement system, feature tracking, stats viewer, and all menu screens that let the player discover and review every feature of the game.

---

## Table of Contents

1. [Achievement System Implementation](#1-achievement-system-implementation)
2. [Achievement Viewer Menu](#2-achievement-viewer-menu)
3. [Stats Viewer Screen](#3-stats-viewer-screen)
4. [Activity Summary Screens](#4-activity-summary-screens)
5. [Decor Browser Menu](#5-decor-browser-menu)
6. [Dialogue Log & Bestiary](#6-dialogue-log--bestiary)
7. [Memorial & Heritage Viewer](#7-memorial--heritage-viewer)
8. [Notification & Toast System](#8-notification--toast-system)
9. [Settings Menu](#9-settings-menu)
10. [Full Menu Map](#10-full-menu-map)

---

## 1. Achievement System Implementation

### Achievement Categories & IDs

```c
typedef enum {
    ACH_CAT_CARE,           // Feeding, cleaning, streaks
    ACH_CAT_EXPLORATION,    // Steps, locations, distance
    ACH_CAT_SOCIAL,         // Mic, voice, music
    ACH_CAT_ENVIRONMENT,    // Temperature, light, weather
    ACH_CAT_MASTERY,        // Completionist, all-emotions, evolution
    ACH_CAT_STEPS,          // Step milestones and streaks
    ACH_CAT_SECRET,         // Hidden until unlocked
    ACH_CAT_COUNT
} achievement_category_t;

static const char *CATEGORY_NAMES[] = {
    "Care", "Exploration", "Social",
    "Environment", "Mastery", "Steps", "???"
};

static const char *CATEGORY_ICONS[] = {
    "♥", "⚑", "♪", "☀", "★", "↑", "?"
};
```

### Achievement Definition Table

Each achievement has a compact definition for flash storage:

```c
typedef struct {
    uint8_t          id;               // Unique ID (0-63, bitfield position)
    uint8_t          category;         // achievement_category_t
    const char      *name;             // Display name (max 20 chars for e-ink)
    const char      *description;      // One line (max 40 chars)
    const char      *hint;             // Shown when locked ("???" for secrets)
    uint16_t         xp_reward;
    uint8_t          decor_reward;     // DECOR_NONE or item ID
    uint8_t          tier;             // 0=bronze, 1=silver, 2=gold, 3=legendary
    bool             secret;           // Hidden until unlocked
    bool           (*check)(void);     // Evaluation function pointer
} achievement_def_t;

// Tier determines the icon drawn next to the achievement name
// Bronze: [o]  Silver: [◊]  Gold: [★]  Legendary: [✦]
```

### Full Achievement Registry

```c
static const achievement_def_t ACHIEVEMENT_REGISTRY[] = {
    // ─── CARE (0-11) ─────────────────────────────────────────
    { 0,  ACH_CAT_CARE, "First Meal",
      "Feed Dilder for the first time",
      "Feed your octopus", 10, DECOR_NONE, 0, false, check_first_meal },

    { 1,  ACH_CAT_CARE, "Full Course",
      "Use all 3 food types in one session",
      "Try every food type", 25, DECOR_NONE, 0, false, check_full_course },

    { 2,  ACH_CAT_CARE, "Perfect Day",
      "No care mistakes for 24 hours",
      "A flawless day of care", 100, DECOR_NONE, 1, false, check_perfect_day },

    { 3,  ACH_CAT_CARE, "Week of Love",
      "7-day care streak",
      "Care for 7 days straight", 200, DECOR_HEART_ANIM, 1, false, check_7_streak },

    { 4,  ACH_CAT_CARE, "Month of Devotion",
      "30-day care streak",
      "One month of dedication", 750, DECOR_RARE_SET, 2, false, check_30_streak },

    { 5,  ACH_CAT_CARE, "Nurse",
      "Administer medicine 3 times",
      "Heal the sick", 50, DECOR_NONE, 0, false, check_nurse },

    { 6,  ACH_CAT_CARE, "Master Caretaker",
      "All stats >50 for 24 hours",
      "Sustained excellent care", 150, DECOR_NONE, 1, false, check_master_care },

    { 7,  ACH_CAT_CARE, "Overachiever",
      "All stats >80 for 8 hours",
      "Above and beyond", 300, DECOR_NONE, 2, false, check_overachiever },

    { 8,  ACH_CAT_CARE, "Spotless",
      "Clean when hygiene >90",
      "Can't be too clean?", 10, DECOR_NONE, 0, false, check_spotless },

    { 9,  ACH_CAT_CARE, "Helicopter Parent",
      "50+ interactions in one day",
      "So... much... attention", 100, DECOR_NONE, 1, false, check_helicopter },

    // ─── EXPLORATION (10-19) ─────────────────────────────────
    { 10, ACH_CAT_EXPLORATION, "First Steps",
      "Walk 100 steps with Dilder",
      "Take your first walk", 10, DECOR_NONE, 0, false, check_100_steps },

    { 11, ACH_CAT_EXPLORATION, "Morning Walk",
      "Bronze target before 8 AM",
      "Early morning activity", 25, DECOR_NONE, 0, false, check_morning_walk },

    { 12, ACH_CAT_EXPLORATION, "Neighborhood",
      "Visit 5 unique locations",
      "Explore nearby", 50, DECOR_EXPLORER_HAT, 1, false, check_5_locations },

    { 13, ACH_CAT_EXPLORATION, "City Mapper",
      "Visit 25 unique locations",
      "Map your city", 200, DECOR_BG_MAP, 2, false, check_25_locations },

    { 14, ACH_CAT_EXPLORATION, "Globetrotter",
      "Visit 50 unique locations",
      "World traveler", 500, DECOR_GLOBE, 2, false, check_50_locations },

    { 15, ACH_CAT_EXPLORATION, "Marathon",
      "42,195 steps in one day",
      "A full marathon distance", 500, DECOR_RUNNING_ANIM, 3, false, check_marathon },

    { 16, ACH_CAT_EXPLORATION, "Homecoming",
      "Return home after 8+ hours",
      "There's no place like home", 30, DECOR_NONE, 0, false, check_homecoming },

    { 17, ACH_CAT_EXPLORATION, "Night Walker",
      "1,000+ steps midnight-5 AM",
      "Who walks at this hour?", 50, DECOR_NONE, 1, false, check_night_walker },

    { 18, ACH_CAT_EXPLORATION, "7-Day Explorer",
      "New location every day for 7 days",
      "A week of discovery", 300, DECOR_NONE, 2, false, check_7day_explorer },

    // ─── SOCIAL (20-27) ──────────────────────────────────────
    { 20, ACH_CAT_SOCIAL, "First Words",
      "Talk via mic for 10 seconds",
      "Say something!", 10, DECOR_NONE, 0, false, check_first_words },

    { 21, ACH_CAT_SOCIAL, "Storyteller",
      "100 min cumulative mic activity",
      "A lot to say", 200, DECOR_NONE, 1, false, check_storyteller },

    { 22, ACH_CAT_SOCIAL, "Loud and Proud",
      "Yell at Dilder intentionally",
      "Use your outside voice", 25, DECOR_NONE, 0, false, check_loud },

    { 23, ACH_CAT_SOCIAL, "Whisper Secret",
      "Low-volume mic for 30 seconds",
      "Speak softly...", 50, DECOR_NONE, 1, false, check_whisper },

    { 24, ACH_CAT_SOCIAL, "Serenade",
      "Singing detected for 60 seconds",
      "Carry a tune", 100, DECOR_NONE, 1, false, check_serenade },

    { 25, ACH_CAT_SOCIAL, "DJ Dilder",
      "Music detected for 30 minutes",
      "Set the mood", 150, DECOR_CHILL_MODE, 2, false, check_dj },

    { 26, ACH_CAT_SOCIAL, "Silence Golden",
      "No mic 8 hours while awake",
      "...", 30, DECOR_NONE, 0, false, check_silence },

    { 27, ACH_CAT_SOCIAL, "Motivational",
      "Talk for 5 min continuously",
      "Inspirational speech", 100, DECOR_NONE, 1, false, check_motivational },

    // ─── ENVIRONMENT (28-35) ─────────────────────────────────
    { 28, ACH_CAT_ENVIRONMENT, "Night Owl",
      "Awake past midnight",
      "Burn the midnight oil", 25, DECOR_NONE, 0, false, check_night_owl },

    { 29, ACH_CAT_ENVIRONMENT, "Early Bird",
      "Interact before 6 AM",
      "The early worm...", 25, DECOR_NONE, 0, false, check_early_bird },

    { 30, ACH_CAT_ENVIRONMENT, "Weather Friend",
      "Rain detected (humidity spike)",
      "Dancing in the rain", 50, DECOR_HAPPY_DANCE, 1, false, check_weather },

    { 31, ACH_CAT_ENVIRONMENT, "Cozy Keeper",
      "Optimal temp/humidity 8 hours",
      "Perfect conditions", 100, DECOR_COMFORT, 1, false, check_cozy },

    { 32, ACH_CAT_ENVIRONMENT, "Sauna Mode",
      ">30C for 30 minutes",
      "It's getting hot", 30, DECOR_NONE, 0, false, check_sauna },

    { 33, ACH_CAT_ENVIRONMENT, "Arctic Explorer",
      "<10C for 30 minutes",
      "Brrrrr", 30, DECOR_SHIVER_ANIM, 0, false, check_arctic },

    { 34, ACH_CAT_ENVIRONMENT, "Darkness Dweller",
      "Dark 4 hours, energy full",
      "Embrace the void", 50, DECOR_NONE, 1, false, check_darkness },

    { 35, ACH_CAT_ENVIRONMENT, "Flash Bang",
      "Sudden bright startle x5",
      "Surprise!", 25, DECOR_NONE, 0, false, check_flash },

    // ─── MASTERY (36-45) ─────────────────────────────────────
    { 36, ACH_CAT_MASTERY, "All Emotions",
      "Witness all 16 emotions",
      "The full spectrum", 300, DECOR_EMOTION_GALLERY, 2, false, check_all_emotions },

    { 37, ACH_CAT_MASTERY, "Disciplinarian",
      "100% discipline in one stage",
      "Firm but fair", 200, DECOR_NONE, 1, false, check_disciplinarian },

    { 38, ACH_CAT_MASTERY, "Zen Master",
      "All stats >60 for 72 hours",
      "Inner peace", 500, DECOR_CHILL_MODE, 2, false, check_zen },

    { 39, ACH_CAT_MASTERY, "Chaos Agent",
      "Chaotic+Unhinged+Weird in 1 day",
      "Embrace the chaos", 200, DECOR_NONE, 1, false, check_chaos },

    { 40, ACH_CAT_MASTERY, "Full Wardrobe",
      "Unlock 20 decor items",
      "Fashion icon", 300, DECOR_NONE, 2, false, check_wardrobe },

    { 41, ACH_CAT_MASTERY, "Polyglot",
      "Max intelligence (100)",
      "Smartest octopus alive", 400, DECOR_NONE, 2, false, check_polyglot },

    { 42, ACH_CAT_MASTERY, "All Forms",
      "Evolve all 6 adult forms",
      "Master of evolution", 1000, DECOR_MASTER_BADGE, 3, false, check_all_forms },

    { 43, ACH_CAT_MASTERY, "Elder Wisdom",
      "Reach Elder stage",
      "Age brings wisdom", 500, DECOR_NONE, 2, false, check_elder },

    { 44, ACH_CAT_MASTERY, "Generational",
      "Complete 3 rebirth cycles",
      "A family legacy", 750, DECOR_HERITAGE, 2, false, check_generational },

    { 45, ACH_CAT_MASTERY, "Completionist",
      "Unlock 50 achievements",
      "You did it all", 2000, DECOR_GOLDEN_FRAME, 3, false, check_completionist },

    // ─── STEPS (46-55) ───────────────────────────────────────
    { 46, ACH_CAT_STEPS, "Bronze Walker",
      "First 2,000-step day",
      "Getting started", 10, DECOR_NONE, 0, false, check_bronze },

    { 47, ACH_CAT_STEPS, "Silver Strider",
      "First 5,000-step day",
      "Finding your stride", 25, DECOR_NONE, 0, false, check_silver },

    { 48, ACH_CAT_STEPS, "Gold Crusher",
      "First 8,000-step day",
      "Going the distance", 50, DECOR_NONE, 1, false, check_gold },

    { 49, ACH_CAT_STEPS, "Platinum Pacer",
      "First 12,000-step day",
      "Unstoppable", 100, DECOR_NONE, 1, false, check_platinum },

    { 50, ACH_CAT_STEPS, "Diamond Destroyer",
      "First 20,000-step day",
      "Peak performance", 200, DECOR_RARE_COSMETIC, 2, false, check_diamond },

    { 51, ACH_CAT_STEPS, "Week Titan",
      "100,000 steps in one week",
      "A titan among walkers", 1500, DECOR_UNIQUE_ANIM, 3, false, check_week_titan },

    { 52, ACH_CAT_STEPS, "Monthly Mythic",
      "500,000 steps in one month",
      "Mythical endurance", 5000, DECOR_HOF_ENTRY, 3, false, check_monthly_mythic },

    { 53, ACH_CAT_STEPS, "Million Steps",
      "1,000,000 lifetime steps",
      "A million footfalls", 3000, DECOR_LEGEND_BADGE, 3, false, check_million },

    { 54, ACH_CAT_STEPS, "Streak Master",
      "90-day streak",
      "Legendary consistency", 5000, DECOR_NONE, 3, false, check_streak_90 },

    { 55, ACH_CAT_STEPS, "Eternal Bond",
      "365-day streak",
      "One full year", 25000, DECOR_ETERNAL, 3, false, check_streak_365 },

    // ─── SECRET (56-63) ──────────────────────────────────────
    { 56, ACH_CAT_SECRET, "Midnight Wish",
      "Active at midnight New Year's",
      "???", 500, DECOR_NONE, 2, true, check_midnight_wish },

    { 57, ACH_CAT_SECRET, "Emotional Rainbow",
      "All 16 emotions in 24 hours",
      "???", 1000, DECOR_NONE, 3, true, check_emotional_rainbow },

    { 58, ACH_CAT_SECRET, "Picky Eater",
      "Dilder refuses food 5x in a row",
      "???", 50, DECOR_NONE, 0, true, check_picky },

    { 59, ACH_CAT_SECRET, "Pacifist",
      "Bond 8 without ever scolding",
      "???", 500, DECOR_NONE, 2, true, check_pacifist },

    { 60, ACH_CAT_SECRET, "Mythic Finder",
      "Find an Elder Relic treasure",
      "???", 2000, DECOR_NONE, 3, true, check_mythic_finder },

    { 61, ACH_CAT_SECRET, "Perfect Weight",
      "Weight exactly 100 for 24 hours",
      "???", 100, DECOR_NONE, 1, true, check_perfect_weight },

    { 62, ACH_CAT_SECRET, "Deep Comfort",
      "Pet back zone 60 seconds",
      "???", 75, DECOR_NONE, 0, true, check_deep_comfort },

    { 63, ACH_CAT_SECRET, "Concert Goer",
      "Music for 2 hours cumulative",
      "???", 200, DECOR_NONE, 1, true, check_concert },
};

#define ACHIEVEMENT_COUNT 64
```

### Persistent Tracking State

```c
// Stored in save_data_t (see 09-persistence-storage.md)
typedef struct {
    uint64_t unlocked;             // Bitfield: 64 achievements
    uint16_t emotions_witnessed;   // Bitfield: 16 emotions
    uint16_t evolution_forms_seen; // Bitfield: 6 forms across generations
    uint32_t total_interactions;   // Lifetime interaction counter
    uint32_t mic_total_seconds;    // Cumulative mic activity
    uint32_t music_total_seconds;  // Cumulative music detection
    uint16_t medicine_count;       // Times medicine given
    uint16_t food_types_today;     // Bitfield: which food types used today
    uint8_t  today_interactions;   // Interactions today (for helicopter)
    uint32_t balanced_start_ms;    // When all stats became >60
    uint32_t optimal_env_start_ms; // When temp/humidity became optimal
    uint8_t  startle_count;        // Flash-bang count
    uint8_t  food_refuse_streak;   // Consecutive food refusals
    bool     ever_scolded;         // Has the player ever scolded
    uint8_t  decor_unlocked_count; // Total decor items unlocked
} achievement_tracker_t;
```

---

## 2. Achievement Viewer Menu

### Screen Layout: Achievement Category List

```
┌──────────────────────────────────────────────────┐
│ ACHIEVEMENTS              12 / 64                │
├──────────────────────────────────────────────────┤
│                                                  │
│  > ♥ Care              4/10   ████░░░░           │
│    ⚑ Exploration       2/9    ██░░░░░░           │
│    ♪ Social            1/8    █░░░░░░░           │
│    ☀ Environment       3/8    ███░░░░░           │
│    ★ Mastery           0/10   ░░░░░░░░           │
│    ↑ Steps             2/10   ██░░░░░░           │
│    ? Secrets           0/8    ????????           │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Screen Layout: Achievement List (within a category)

```
┌──────────────────────────────────────────────────┐
│ ♥ CARE ACHIEVEMENTS       4/10                   │
├──────────────────────────────────────────────────┤
│                                                  │
│  [★] First Meal              +10 XP              │
│  [★] Full Course             +25 XP              │
│  [★] Perfect Day             +100 XP             │
│  [★] Week of Love            +200 XP  ♥          │
│  [ ] Month of Devotion       ???                 │
│  [ ] Nurse                   ???                 │
│  [ ] Master Caretaker        ???                 │
│  [ ] Overachiever            ???                 │
│                                                  │
│  [BACK: Return]    [SELECT: View Details]        │
└──────────────────────────────────────────────────┘
```

`[★]` = unlocked, `[ ]` = locked. Secret achievements show only "???" for both name and hint until unlocked.

### Screen Layout: Achievement Detail

```
┌──────────────────────────────────────────────────┐
│ ★ WEEK OF LOVE                                   │
├──────────────────────────────────────────────────┤
│                                                  │
│  "7-day care streak"                             │
│                                                  │
│  Reward: +200 XP                                 │
│  Bonus:  Heart Animation                         │
│                                                  │
│  Unlocked: 2026-04-22                            │
│  Tier: Silver                                    │
│                                                  │
│  [BACK: Return]                                  │
└──────────────────────────────────────────────────┘
```

### Navigation Flow

```c
void ui_achievement_handle_input(button_event_t btn) {
    switch (ach_screen_state) {
        case ACH_SCREEN_CATEGORIES:
            if (btn.id == BTN_UP)     ach_cursor--;
            if (btn.id == BTN_DOWN)   ach_cursor++;
            if (btn.id == BTN_SELECT) ach_screen_state = ACH_SCREEN_LIST;
            if (btn.id == BTN_BACK)   ui_set_screen(SCREEN_PET);
            break;

        case ACH_SCREEN_LIST:
            if (btn.id == BTN_UP)     ach_item_cursor--;
            if (btn.id == BTN_DOWN)   ach_item_cursor++;
            if (btn.id == BTN_SELECT) ach_screen_state = ACH_SCREEN_DETAIL;
            if (btn.id == BTN_BACK)   ach_screen_state = ACH_SCREEN_CATEGORIES;
            break;

        case ACH_SCREEN_DETAIL:
            if (btn.id == BTN_BACK)   ach_screen_state = ACH_SCREEN_LIST;
            break;
    }
    ui_mark_dirty();
}
```

---

## 3. Stats Viewer Screen

### Accessible from: Main Menu → Stats

Three sub-screens cycled with UP/DOWN:

### 3a. Health Meters

```
┌──────────────────────────────────────────────────┐
│ STATS — Health                        Page 1/3   │
├──────────────────────────────────────────────────┤
│                                                  │
│  HUN ██████████████████░░  72/100                │
│  HAP █████████████░░░░░░░  55/100                │
│  ENE ████████████████████  94/100                │
│  HYG █████████░░░░░░░░░░░  38/100                │
│  HEA ████████████████████  100/100               │
│                                                  │
│  Weight: 105 (normal)                            │
│  Stage: Juvenile (Day 5)                         │
│                                                  │
│  [UP/DOWN: Pages]        [BACK: Close]           │
└──────────────────────────────────────────────────┘
```

### 3b. Bond & Progression

```
┌──────────────────────────────────────────────────┐
│ STATS — Bond                          Page 2/3   │
├──────────────────────────────────────────────────┤
│                                                  │
│  Bond: Lv3 Companion                             │
│  XP: 723 / 1,500 ████████░░░░  48%              │
│                                                  │
│  Discipline:    62/100                           │
│  Intelligence:  35/100                           │
│  Fitness:       48/100                           │
│  Exploration:   12/100                           │
│                                                  │
│  Achievements:  12/64                            │
│  Decor Items:   5 unlocked                       │
│                                                  │
│  [UP/DOWN: Pages]        [BACK: Close]           │
└──────────────────────────────────────────────────┘
```

### 3c. Today's Activity

```
┌──────────────────────────────────────────────────┐
│ STATS — Today                         Page 3/3   │
├──────────────────────────────────────────────────┤
│                                                  │
│  Steps Today:  4,231                             │
│  ██████████████░░░░░  Silver (5,000)             │
│                                                  │
│  Week Total:   18,450                            │
│  Month Total:  67,230                            │
│  Lifetime:     142,890                           │
│                                                  │
│  Streak: 12 days  🔥                             │
│  New Locations Today: 1                          │
│                                                  │
│  [UP/DOWN: Pages]        [BACK: Close]           │
└──────────────────────────────────────────────────┘
```

---

## 4. Activity Summary Screens

### Daily Summary (shown at day change)

```
┌──────────────────────────────────────────────────┐
│ DAILY SUMMARY                                    │
├──────────────────────────────────────────────────┤
│                                                  │
│  Steps: 6,847    Rank: Silver                    │
│  Locations: 2 new                                │
│  Care Quality: 94% (stats >50)                   │
│                                                  │
│  Dilder says:                                    │
│  "Not bad! My tentacles got a good               │
│   workout today."                                │
│                                                  │
│  Streak: 13 days  🔥🔥                            │
│                                                  │
│  [SELECT: Dismiss]                               │
└──────────────────────────────────────────────────┘
```

### Weekly Summary (shown Sunday evening)

```
┌──────────────────────────────────────────────────┐
│ WEEKLY SUMMARY                                   │
├──────────────────────────────────────────────────┤
│                                                  │
│  Total Steps:  34,891                            │
│  Rank: Week Runner                               │
│                                                  │
│  Best Day: Thursday (8,234)                      │
│  Rest Day: Sunday (1,102)                        │
│  Daily Streak: 5 active days                     │
│                                                  │
│  "We explored 3 new places this week!"           │
│  Reward: Ocean Sunset Background                 │
│                                                  │
│  [SELECT: Dismiss]                               │
└──────────────────────────────────────────────────┘
```

---

## 5. Decor Browser Menu

### Accessible from: Main Menu → Decor (Bond 3+)

```c
typedef enum {
    DECOR_TAB_HATS,
    DECOR_TAB_BACKGROUNDS,
    DECOR_TAB_ACCESSORIES,
    DECOR_TAB_ANIMATIONS,
    DECOR_TAB_COUNT
} decor_tab_t;
```

### Screen Layout: Slot Selection

```
┌──────────────────────────────────────────────────┐
│ DECOR                                            │
├──────────────────────────────────────────────────┤
│                                                  │
│  > Hats          [Crown]         3 unlocked      │
│    Backgrounds   [Ocean Floor]   2 unlocked      │
│    Accessories   [None]          1 unlocked      │
│    Animations    [Calm Sway]     2 unlocked      │
│                                                  │
│  Current shows equipped item name.               │
│  Number shows how many available.                │
│                                                  │
│  [SELECT: Browse]        [BACK: Close]           │
└──────────────────────────────────────────────────┘
```

### Screen Layout: Item Browser

```
┌──────────────────────────────────────────────────┐
│ HATS                        3 / 8 unlocked       │
├──────────────────────────────────────────────────┤
│            ┌──────────┐                          │
│            │ PREVIEW  │  > Crown                 │
│            │          │    Bow                    │
│            │ [octopus │    Explorer Hat           │
│            │  wearing │    ░░░░ (locked)          │
│            │  crown]  │    ░░░░ (locked)          │
│            │          │    ░░░░ (locked)          │
│            └──────────┘    ░░░░ (locked)          │
│                            ░░░░ (locked)          │
│  [SELECT: Equip]  [ACTION: Preview]  [BACK]     │
└──────────────────────────────────────────────────┘
```

The left half shows a live preview of the octopus wearing the highlighted item. The right half lists all items with locked ones shown as `░░░░`. SELECT equips the item, ACTION previews without equipping.

### Equip / Unequip Logic

```c
void decor_browser_select(decor_tab_t tab, uint8_t item_index) {
    decor_id_t item = decor_get_item_for_tab(tab, item_index);

    if (!decor_is_unlocked(&game.decor, item)) return;  // Can't equip locked

    decor_slot_t slot = decor_get_slot(item);

    if (game.decor.equipped[slot] == item) {
        // Already equipped → unequip
        game.decor.equipped[slot] = DECOR_NONE;
    } else {
        // Equip
        game.decor.equipped[slot] = item;
    }

    ui_mark_dirty();
}
```

---

## 6. Dialogue Log & Bestiary

### Emotion Gallery (unlocked via "All Emotions" achievement)

Shows all 16 emotions with their animation preview and a sample quote:

```
┌──────────────────────────────────────────────────┐
│ EMOTION GALLERY              16/16 seen          │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────┐                                      │
│  │ NORMAL │  "MATTRESSES ARE BODY SHELVES."      │
│  │ [face] │  Balanced stats, default mood.       │
│  └────────┘  First seen: Day 1                   │
│                                                  │
│  [UP/DOWN: Browse]   [BACK: Close]               │
└──────────────────────────────────────────────────┘
```

Locked emotions show "???" with the hint "Keep exploring to discover this emotion."

### Evolution Bestiary (tracks forms across all generations)

```
┌──────────────────────────────────────────────────┐
│ EVOLUTION FORMS              2/6 discovered       │
├──────────────────────────────────────────────────┤
│                                                  │
│  [★] Deep-Sea Scholar                            │
│      "High intelligence + bond"                  │
│      Gen 1 — Day 14                              │
│                                                  │
│  [★] Storm Kraken                                │
│      "Forged through adversity"                  │
│      Gen 2 — Day 14                              │
│                                                  │
│  [ ] ??? — "High fitness + exploration"          │
│  [ ] ??? — "Low discipline, high happiness"      │
│  [ ] ??? — "Quiet, self-sufficient"              │
│  [ ] ??? — "Creative, musical"                   │
│                                                  │
│  [BACK: Close]                                   │
└──────────────────────────────────────────────────┘
```

Undiscovered forms show their requirement hint but not their name or visual.

---

## 7. Memorial & Heritage Viewer

### Accessible from: Main Menu → Stats → Memorial

Shows rebirth history — every generation's octopus:

```
┌──────────────────────────────────────────────────┐
│ MEMORIAL                    3 generations        │
├──────────────────────────────────────────────────┤
│                                                  │
│  Gen 1: Deep-Sea Scholar                         │
│         Age: 42 days  Bond: Lv6 Soulmate         │
│         "The one who started it all"             │
│                                                  │
│  Gen 2: Storm Kraken                             │
│         Age: 35 days  Bond: Lv5 Best Friend      │
│         "Forged in thunder"                      │
│                                                  │
│  Gen 3: (Current — Juvenile, Day 5)              │
│         Heritage: Storm Kraken lineage           │
│                                                  │
│  [UP/DOWN: Scroll]   [BACK: Close]               │
└──────────────────────────────────────────────────┘
```

Up to 8 generations stored in flash. Oldest entries are displaced when full.

---

## 8. Notification & Toast System

Achievements, level-ups, and milestones pop up as toast notifications overlaid on the current screen:

```c
typedef struct {
    const char *line1;           // Top text (e.g., "ACHIEVEMENT UNLOCKED")
    const char *line2;           // Bottom text (e.g., "Week of Love ♥")
    uint32_t   show_start_ms;
    uint32_t   duration_ms;      // 5 seconds default
    uint8_t    priority;         // Higher priority replaces lower
    bool       active;
} toast_t;

#define TOAST_QUEUE_SIZE 4
static toast_t toast_queue[TOAST_QUEUE_SIZE];

void toast_show(const char *line1, const char *line2, uint8_t priority) {
    // Find empty slot or replace lowest priority
    // ...
}
```

### Toast Layout (overlaid on bottom 24px of any screen)

```
┌──────────────────────────────────────────────────┐
│                                                  │
│              [current screen]                    │
│                                                  │
├──════════════════════════════════════════════════─┤
│ ★ ACHIEVEMENT UNLOCKED                           │
│   Week of Love ♥                    +200 XP      │
└──────────────────────────────────────────────────┘
```

### Event → Toast Mapping

```c
void on_achievement_unlock(event_type_t type, const event_data_t *data) {
    uint8_t id = data->value;
    const achievement_def_t *ach = &ACHIEVEMENT_REGISTRY[id];

    char xp_str[16];
    snprintf(xp_str, sizeof(xp_str), "+%d XP", ach->xp_reward);

    toast_show("ACHIEVEMENT UNLOCKED", ach->name, 8);
}

void on_bond_level_up(event_type_t type, const event_data_t *data) {
    static const char *LEVEL_NAMES[] = {
        "Stranger", "Acquaintance", "Companion", "Friend",
        "Best Friend", "Soulmate", "Bonded", "Legendary"
    };
    char msg[32];
    snprintf(msg, sizeof(msg), "Bond: %s", LEVEL_NAMES[data->value]);
    toast_show("LEVEL UP!", msg, 9);
}

void on_step_milestone(event_type_t type, const event_data_t *data) {
    static const char *TIER_NAMES[] = {
        "", "Bronze", "Silver", "Gold", "Platinum", "Diamond"
    };
    char msg[32];
    snprintf(msg, sizeof(msg), "%s Target!", TIER_NAMES[data->value]);
    toast_show("STEP MILESTONE", msg, 6);
}

void on_evolution(event_type_t type, const event_data_t *data) {
    // Full-screen takeover — not a toast
    ui_set_screen(SCREEN_EVOLUTION);
    game_state_transition(GAME_STATE_EVENT);
}
```

---

## 9. Settings Menu

### Accessible from: Main Menu → Settings

```
┌──────────────────────────────────────────────────┐
│ SETTINGS                                         │
├──────────────────────────────────────────────────┤
│                                                  │
│  > Sound         [ON]                            │
│    Time Format   [12h]                           │
│    Step Goal     [Bronze 2,000]                  │
│    Home WiFi     [Set: "HomeNetwork"]            │
│    Factory Reset [Hold SELECT 5s]                │
│                                                  │
│  Firmware: v0.4.0                                │
│  Generation: 3                                   │
│  Uptime: 5d 14h                                  │
│                                                  │
│  [SELECT: Toggle/Edit]   [BACK: Close]           │
└──────────────────────────────────────────────────┘
```

**Sound:** Toggle the piezo buzzer for notification beeps.
**Time Format:** Toggle 12h/24h display.
**Step Goal:** Choose which daily target to display as the primary goal bar.
**Home WiFi:** Long-press SELECT to set the current WiFi as "home" for location mechanics.
**Factory Reset:** Hold SELECT for 5 seconds on this item to erase all save data and start fresh.

---

## 10. Full Menu Map

Complete hierarchical menu structure with unlock gates:

```
Long-Press SELECT → Main Menu
│
├── Feed
│   ├── Meal                          [Always]
│   ├── Snack                         [Always]
│   └── Treat                         [Bond 4+]
│
├── Play
│   ├── Mini-game                     [Bond 4+]
│   └── Tickle                        [Always]
│
├── Care
│   ├── Clean                         [Always]
│   ├── Medicine                      [Health < 30 only]
│   └── Light (sleep toggle)          [Always]
│
├── Stats
│   ├── Health Meters        (Page 1) [Always]
│   ├── Bond & Progression   (Page 2) [Always]
│   ├── Today's Activity     (Page 3) [Always]
│   ├── Achievements                  [Always]
│   │   ├── Category List
│   │   │   ├── Care
│   │   │   ├── Exploration
│   │   │   ├── Social
│   │   │   ├── Environment
│   │   │   ├── Mastery
│   │   │   ├── Steps
│   │   │   └── Secrets (???)
│   │   └── Achievement Detail
│   ├── Emotion Gallery               [Achievement: All Emotions]
│   ├── Evolution Bestiary            [Bond 5+]
│   └── Memorial                      [Generation 2+]
│
├── Decor                             [Bond 3+]
│   ├── Hats          (browse + equip)
│   ├── Backgrounds   (browse + equip)
│   ├── Accessories   (browse + equip)
│   └── Animations    (browse + equip)
│
└── Settings
    ├── Sound          [ON/OFF]
    ├── Time Format    [12h/24h]
    ├── Step Goal      [Bronze-Diamond]
    ├── Home WiFi      [Set Current]
    └── Factory Reset  [Hold 5s]


Special Screens (triggered by events, not menu):
├── Daily Summary          (midnight rollover)
├── Weekly Summary         (Sunday evening)
├── Gift Box Animation     (treasure collected)
├── Evolution Reveal       (day 14 transition)
├── Compass / Hunt Mode    (treasure hunt active)
├── Egg Hatch Animation    (new game / rebirth)
└── Memorial / Rebirth     (elder stage choice)
```

### Unlock Gate Implementation

```c
typedef struct {
    menu_id_t   menu;
    uint8_t     item_index;
    bool      (*visible)(void);
} menu_gate_t;

bool gate_bond_3(void)     { return game.progression.bond_level >= BOND_COMPANION; }
bool gate_bond_4(void)     { return game.progression.bond_level >= BOND_FRIEND; }
bool gate_bond_5(void)     { return game.progression.bond_level >= BOND_BEST_FRIEND; }
bool gate_is_sick(void)    { return game.stats.primary.health < 30; }
bool gate_generation_2(void) { return game.life.generation >= 1; }
bool gate_all_emotions(void) {
    return game.progression.achievements & (1ULL << ACH_ALL_EMOTIONS_ID);
}

// Items with a visibility gate that returns false are hidden from the menu.
// The menu renderer skips them and adjusts cursor indices.
```

---

### Feature Systems API Summary

```c
// ─── Achievement System ──────────────────────────────────────
void achievement_init(achievement_tracker_t *tracker);
void achievement_check_all(void);        // Called on relevant events
void achievement_on_event(event_type_t type, const event_data_t *data);
bool achievement_is_unlocked(uint8_t id);
uint8_t achievement_count_in_category(uint8_t category);
uint8_t achievement_unlocked_in_category(uint8_t category);
const achievement_def_t* achievement_get(uint8_t id);

// ─── Toast Notifications ─────────────────────────────────────
void toast_show(const char *line1, const char *line2, uint8_t priority);
void toast_update(uint32_t now);         // Called each render frame
void toast_render(void);                 // Draw active toast on screen
bool toast_active(void);

// ─── Stats Viewer ────────────────────────────────────────────
void ui_stats_render(uint8_t page);
void ui_stats_handle_input(button_event_t btn);

// ─── Achievement Viewer ──────────────────────────────────────
void ui_achievement_render(void);
void ui_achievement_handle_input(button_event_t btn);

// ─── Decor Browser ───────────────────────────────────────────
void ui_decor_render(void);
void ui_decor_handle_input(button_event_t btn);

// ─── Summary Screens ─────────────────────────────────────────
void ui_daily_summary_render(void);
void ui_weekly_summary_render(void);

// ─── Memorial Viewer ─────────────────────────────────────────
void ui_memorial_render(void);
void ui_memorial_handle_input(button_event_t btn);
```

---

*These two documents ([12-user-guide.md](12-user-guide.md) and this file) complete the gameplay planning series. The User Guide presents every feature as if the player is holding a finished device. This document provides the implementation spec for all the menus and systems that let them discover those features.*
