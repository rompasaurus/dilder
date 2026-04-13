# Peer Discovery & Multiplayer Sync Research

Research into enabling Dilder pets to detect nearby peers and reward players for real-world encounters.

---

## Feature Overview

When two (or more) Pico W devices running compatible Dilder firmware are within range of each other, they should automatically discover one another and provide a **bonus or notification** to both players — rewarding real-world social interaction between pet owners.

### Player Experience

1. You're carrying your Dilder around.
2. Another player walks into range.
3. Your pet reacts — a unique animation, a stat boost, or a collectible "encounter" logged to memory.
4. Both players benefit without needing to press anything.

---

## Communication Methods

The Pico W's CYW43439 chip supports both **Wi-Fi** and **Bluetooth Low Energy (BLE)**. Three viable approaches exist, each with different trade-offs.

### 1. Wi-Fi: Infrastructure Mode (Router Required)

All Picos connect to the same local Wi-Fi network (e.g., at home or a meetup).

| Step | Mechanism |
|---|---|
| **Detection** | UDP broadcast (`255.255.255.255`) heartbeat packets containing device ID + firmware version |
| **Sync** | TCP or HTTP connection to exchange state data (pet name, emotion, stats) |

- **Pros:** High throughput, simple to implement, well-documented in Pico SDK.
- **Cons:** Requires an existing Wi-Fi router — not portable.
- **Best for:** Home base, LAN parties, events with shared Wi-Fi.

### 2. Wi-Fi: SoftAP Mode (Peer-to-Peer)

One Pico acts as a Wi-Fi Access Point; others connect as clients. No router needed.

| Step | Mechanism |
|---|---|
| **Detection** | Client Picos scan for and auto-connect to a known SSID (e.g., `DILDER_<ID>`) |
| **Sync** | Master Pico aggregates client state and broadcasts global state back |

- **Pros:** Works anywhere without external hardware; self-contained.
- **Cons:** Master is a single point of failure; limited connection capacity; one device must be designated as AP.
- **Best for:** Small groups, outdoor meetups, no-infrastructure scenarios.

### 3. Bluetooth Low Energy (BLE) Advertising

The most autonomous method — no network infrastructure needed at all.

| Step | Mechanism |
|---|---|
| **Detection** | All Picos advertise a specific **Service UUID** in BLE advertising packets. All Picos simultaneously scan for that UUID. |
| **Sync** | On match, establish a BLE connection using a GATT profile with characteristics for pet data exchange. |

- **Pros:** Extremely low power; true proximity detection; zero setup; works while walking around.
- **Cons:** Low bandwidth (~20 bytes per packet in advertising mode); more complex connection management; ~10m range typical.
- **Best for:** Passive discovery while carrying the device — the core "StreetPass" use case.

---

## Recommended Approach

**BLE Advertising** is the primary method for peer discovery. It aligns best with the Dilder vision:

- Devices should discover each other **passively**, without the player doing anything.
- No Wi-Fi network dependency — works outdoors, in transit, anywhere.
- Low power consumption fits a battery-powered handheld.
- The limited bandwidth is fine — we only need to exchange a small handshake, not stream data.

Wi-Fi modes (Infrastructure or SoftAP) can be added later as **optional enhanced sync** for richer data exchange at home or events.

---

## Discovery Protocol Design

### Handshake Packet

Every BLE advertisement (or UDP broadcast, if using Wi-Fi) must include a metadata header:

| Field | Size | Purpose |
|---|---|---|
| `group_id` | 4 bytes | Project identifier (e.g., `DLDR`) — filters out non-Dilder BLE traffic |
| `version` | 2 bytes | Protocol version — prevents incompatible firmware from syncing |
| `device_id` | 4 bytes | Unique per-device identifier — prevents self-detection and enables encounter logging |
| `pet_name_hash` | 2 bytes | Short hash of pet name — used for display on discovery |
| `emotion_state` | 1 byte | Current emotion ID (0–15) — lets the other pet "react" to your pet's mood |

**Total: 13 bytes** — fits within a single BLE advertising packet (max ~31 bytes usable).

### Validation Logic

```
if packet.group_id == MY_GROUP_ID and packet.version == MY_VERSION:
    if packet.device_id != MY_DEVICE_ID:
        if not already_encountered_recently(packet.device_id):
            trigger_discovery_event(packet)
else:
    # Ignore — different project or incompatible firmware version
```

### Cooldown

To prevent spamming notifications when two players are near each other for an extended period:

- After discovering a specific `device_id`, set a **cooldown timer** (e.g., 30 minutes).
- During cooldown, the device is still detected but no new bonus/notification fires.
- Cooldown resets when the device leaves range and is rediscovered later.

---

## Reward & Notification System

### On Discovery

When a new peer is detected, the pet should react in a way that feels alive:

| Reward Type | Description |
|---|---|
| **Animation** | A unique "excited" or "curious" animation plays — the pet notices the other player |
| **Stat Boost** | Small happiness/energy bonus (e.g., +10 happiness) — social encounters are good for your pet |
| **Encounter Log** | The discovery is saved to flash memory with a timestamp and the peer's emotion state |
| **Streak Bonus** | Discovering the *same* pet multiple times across different days builds a "friendship" counter with escalating rewards |

### Encounter Log (Persistent)

Store encounters in a simple ring buffer on flash:

```
struct Encounter {
    uint32_t device_id;
    uint8_t  emotion_state;
    uint32_t timestamp;      // RTC time or uptime counter
    uint8_t  encounter_count; // friendship level with this device
};
```

A fixed-size buffer (e.g., 64 entries) keeps flash usage predictable. Oldest entries are overwritten when full.

### Display Feedback

On the e-ink display, the discovery event could show:

- A brief icon or animation overlay (e.g., a small heart or exclamation mark near the pet).
- A counter in the status bar: `Friends nearby: 2`.
- After the encounter, a summary screen accessible via button press: "Met 3 pets today!"

---

## Mating & Offspring System

Peer discovery opens up a breeding mechanic — when two pets meet via proximity, they can produce a unique offspring whose traits are derived from both parents.

### Core Concept

Each Dilder pet has a set of **genetic traits** encoded as numeric values. When two compatible pets encounter each other, the player can choose to "mate" them. The resulting offspring inherits a mix of both parents' traits, with a chance for mutation, producing a creature that is visually and behaviorally unique.

This turns every real-world encounter into a potential gameplay event — you never know what combination you'll get.

### Genetic Trait System

Each pet carries a compact genome that defines its visual appearance and personality:

| Trait | Bits | Range | Effect |
|---|---|---|---|
| `body_shape` | 3 | 0–7 | Base body silhouette (round, tall, wide, etc.) |
| `eye_style` | 3 | 0–7 | Eye shape (round, narrow, big, dot, etc.) |
| `tentacle_pattern` | 3 | 0–7 | Tentacle count, length, curl style |
| `personality` | 3 | 0–7 | Disposition bias (cheerful, grumpy, shy, energetic, etc.) |
| `marking_pattern` | 3 | 0–7 | Visual markings/patterns on the body |
| `rarity_modifier` | 2 | 0–3 | Affects mutation chance and trait expression intensity |

**Total: 17 bits (~3 bytes)** — easily fits in the BLE handshake packet or a short GATT exchange.

### Inheritance Algorithm

When two pets mate, each offspring trait is resolved independently:

```
for each trait:
    roll = random(0, 100)
    if roll < 45:
        offspring.trait = parent_a.trait    # inherit from parent A
    elif roll < 90:
        offspring.trait = parent_b.trait    # inherit from parent B
    else:
        offspring.trait = random_value()    # mutation — completely new
```

- **45/45/10 split** gives both parents roughly equal influence with a 10% mutation rate per trait.
- Mutations keep the gene pool fresh and make rare combinations possible even between similar parents.
- The `rarity_modifier` can shift the mutation chance (e.g., a rare parent increases offspring mutation rate to 15%).

### Mating Eligibility

Not every encounter should trigger mating — conditions add meaning to the event:

| Condition | Rationale |
|---|---|
| **Friendship level >= 2** | Pets must have encountered each other at least twice before mating is offered — encourages repeat meetups |
| **Maturity** | Pet must have been alive for a minimum duration (e.g., 3 days) — prevents instant breeding loops |
| **Cooldown** | After mating, a pet cannot mate again for a set period (e.g., 24 hours) — prevents farming |
| **Player consent** | Mating is opt-in via button press, not automatic — the player chooses when to breed |

### Offspring Lifecycle

1. **Conception:** Both devices exchange genetic data via BLE (GATT connection, ~6 bytes each direction).
2. **Egg state:** The offspring doesn't appear immediately. An "egg" icon appears on screen with a hatch timer (e.g., 4–12 hours based on rarity).
3. **Hatching:** The new creature is revealed with a unique animation. Its traits are displayed so the player can see what they got.
4. **Slot system:** The player has limited offspring slots (e.g., 3). They must choose to keep or release offspring, adding a collection/decision element.
5. **Switching:** The player can swap their active pet for one of their offspring, changing the creature others encounter.

### Offspring Data Structure

```
struct Offspring {
    uint8_t  genes[3];         // packed trait genome (17 bits)
    uint32_t parent_a_id;      // device_id of parent A
    uint32_t parent_b_id;      // device_id of parent B
    uint32_t birth_timestamp;  // when the egg was created
    uint16_t hatch_timer;      // minutes until hatching
    uint8_t  generation;       // how many breeding steps from "original" (gen 0)
};
```

**~14 bytes per offspring.** With 3 slots + 1 active pet = 56 bytes total — trivial flash usage.

### Generation Tracking

Each offspring carries a `generation` counter (parent's max generation + 1). This enables:

- **Visual indicators:** Higher-generation pets could have subtle visual flourishes (e.g., slightly different tentacle tips).
- **Bragging rights:** "My pet is a Gen 5" shows a lineage of real-world encounters.
- **Balance lever:** Generation could influence stat growth curves or unlock cosmetic variations.

### BLE Protocol Extension

To support mating, the BLE packet needs a small addition:

| Field | Size | Purpose |
|---|---|---|
| `genes` | 3 bytes | The pet's current genome |
| `mate_ready` | 1 bit | Flag indicating the pet is eligible and willing to mate |

This fits within the existing advertising packet budget (original handshake was 13 bytes, adding 3.1 bytes brings it to ~17 bytes, well under the 31-byte limit).

For the actual gene exchange during mating, a brief GATT connection is established to confirm consent from both sides and transfer the full offspring calculation inputs.

### Display Integration

| Event | Display |
|---|---|
| **Mate available** | A small heart icon pulses near a discovered peer's indicator |
| **Mating initiated** | A brief two-pet animation (both creatures on screen) |
| **Egg received** | Egg icon appears in a status area with a progress indicator |
| **Hatching** | Full-screen reveal animation showing the new creature's unique traits |
| **Offspring menu** | Button-accessible screen to view, swap, or release offspring |

---

## Computational Feasibility on the Pico W

The RP2040 (133MHz ARM Cortex-M0+, 264KB SRAM, 2MB flash) is more than sufficient for breeding and trait-based rendering. Here's why.

### Genetics Calculation Cost

The inheritance algorithm is a loop over 6 traits, each requiring one random number and two comparisons:

```c
// Total cost: ~6 random rolls + ~12 comparisons + ~6 assignments
for (int i = 0; i < NUM_TRAITS; i++) {
    uint8_t roll = rng() % 100;
    if (roll < 45)       offspring.traits[i] = parent_a.traits[i];
    else if (roll < 90)  offspring.traits[i] = parent_b.traits[i];
    else                 offspring.traits[i] = rng() % trait_max[i];
}
```

At 133MHz this completes in **under 1 microsecond** — roughly 50 clock cycles. It runs once per mating event (at most a few times per day), making it effectively free.

### Rendering Cost: Parameterized, Not Procedurally Generated

The existing firmware already renders the octopus procedurally at runtime — body shape, eyes, mouth, tentacles, and body transforms are all driven by numeric parameters per emotion state. The breeding system does not add a new rendering approach; it adds new **inputs** to the same pipeline.

| Current (emotion-driven) | With traits (genome-driven) |
|---|---|
| `body_width = emotion_params[state].width;` | `body_width = base_widths[pet->genes.body_shape];` |
| `eye_y = emotion_params[state].eye_y;` | `eye_y = eye_offsets[pet->genes.eye_style];` |
| Hardcoded per emotion | Table lookup per trait |

A table lookup (`array[index]`) is a single memory read — identical cost to the current hardcoded parameter loads. There is **zero additional rendering overhead**.

### Combinatorial Variety Without Combinatorial Cost

The modular trait system generates visual variety through composition, not unique assets:

| Trait | Values | Storage |
|---|---|---|
| `body_shape` | 8 shape parameter sets | 8 x ~6 bytes = 48 bytes |
| `eye_style` | 8 eye parameter sets | 8 x ~4 bytes = 32 bytes |
| `tentacle_pattern` | 8 tentacle configs | 8 x ~4 bytes = 32 bytes |
| `marking_pattern` | 8 marking draw routines | 8 x ~20 bytes = 160 bytes |
| `personality` | 8 behavior biases | 8 x ~4 bytes = 32 bytes |
| `rarity_modifier` | 4 scalar multipliers | 4 x 1 byte = 4 bytes |

**Total lookup table size: ~308 bytes in flash.** This produces **8 x 8 x 8 x 8 x 8 x 4 = 131,072 unique trait combinations** from less than 0.02% of available flash.

### Memory Budget

| Item | SRAM Cost | Notes |
|---|---|---|
| Active pet genome | 3 bytes | Only the current pet is in memory |
| Offspring slots (3) | 42 bytes | 14 bytes each, loaded on demand |
| Trait lookup tables | 0 bytes | Stored in flash, read directly via `const` arrays |
| Rendering buffer | ~4KB | Already allocated — shared with existing renderer |

**Total additional SRAM: ~45 bytes.** The existing renderer uses the vast majority of the 264KB budget; traits add negligible overhead.

### Flash Budget

| Item | Flash Cost | Notes |
|---|---|---|
| Trait lookup tables | ~308 bytes | `const` arrays compiled into firmware |
| Offspring persistent storage | ~56 bytes | 4 offspring x 14 bytes, written to reserved flash sector |
| Encounter log (expanded) | ~1KB | Ring buffer with breeding history |
| Breeding logic code | ~1–2KB | Inheritance algorithm, eligibility checks, GATT exchange |

**Total additional flash: ~3.4KB** out of 2MB available (~0.17%).

### What the Pico Cannot Do (and Why It Doesn't Matter)

| Limitation | Impact on breeding |
|---|---|
| No floating-point unit | Not needed — all trait values are integers, all rendering uses fixed-point math |
| 133MHz single-core (effectively) | Breeding runs once per event, not per frame — no performance concern |
| 264KB SRAM | Only one creature rendered at a time; genome is 3 bytes, not a texture atlas |
| No GPU | The e-ink display refreshes every 2–3 seconds — there's no frame rate to maintain, so even "slow" drawing is fine |

### Bottom Line

The breeding system's computational cost is dominated by **design work** (choosing which trait values map to which visual parameters), not hardware. The Pico W has orders-of-magnitude more processing power, RAM, and flash than this feature requires. The e-ink refresh cycle (~2–3 seconds) is the actual bottleneck, and it exists regardless of traits.

---

## Technical Considerations

### Power Budget

- BLE advertising at 1-second intervals: ~0.1 mA average.
- BLE scanning (duty-cycled): ~1–5 mA depending on scan window.
- Combined: manageable on battery, but scan duty cycle should be tunable to balance discovery speed vs. battery life.

### Flash Wear

- Encounter log writes are infrequent (at most a few per day in typical use).
- A 64-entry ring buffer with 10-byte entries = 640 bytes — fits in a single flash sector.
- Wear leveling is unnecessary at this write frequency.

### Firmware Version Compatibility

- The `version` field in the handshake ensures only compatible devices sync.
- When the protocol changes, bump the version number.
- Devices with mismatched versions silently ignore each other — no error state needed.

### Security

- BLE advertisements are inherently public — don't include sensitive data.
- The `device_id` should be a random identifier (not MAC address) to avoid tracking.
- No pairing or authentication is needed for the basic discovery handshake.

---

## Implementation Phases

| Phase | Scope |
|---|---|
| **Phase A** | BLE advertising + scanning with hardcoded `group_id`/`version`. Detect peers and log to serial. |
| **Phase B** | Trigger a discovery animation on the e-ink display when a peer is found. |
| **Phase C** | Implement encounter log in flash memory. Add stat boost on discovery. |
| **Phase D** | Add friendship counter (repeated encounters with same device). Streak bonuses. |
| **Phase E** | Genetic trait system — define genome structure, encode traits into BLE packets. |
| **Phase F** | Mating mechanic — eligibility checks, GATT gene exchange, offspring calculation. |
| **Phase G** | Egg/hatching lifecycle, offspring slots, active pet swapping. |
| **Phase H** | Generation tracking, visual trait expression in the rendering engine. |
| **Phase I** | Optional Wi-Fi sync mode for richer data exchange (pet name, full stats, mini-games). |

---

## Open Questions

- **Pet-to-pet interaction:** Should the discovered pet's emotion influence your pet's reaction? (e.g., meeting a happy pet makes yours happier, meeting a sad pet triggers a "comfort" animation)
- **Encounter cap:** Should there be a daily limit on discovery bonuses to prevent farming?
- **Visual identity:** Can we encode a simple visual marker (e.g., 2-bit pattern) in the BLE packet so your pet "recognizes" a friend vs. a stranger?
- **Pico 2 W:** The recommended upgrade board has BLE 5.2 — does this enable any additional features (extended advertising, coded PHY for longer range)?
- **Trait rendering:** How many visual trait combinations can the rendering engine support before we need a lookup table vs. procedural generation?
- **Offspring permanence:** Should offspring persist forever, or can they "age out" if neglected — adding stakes to the collection?
- **Cross-pollination:** If two offspring (non-originals) mate, do deeper generation depths produce diminishing returns or increasingly wild mutations?
- **Consent UX:** Both players must agree to mate — how do we handle the case where one player walks away mid-handshake?

---

## References

- [Pico W BLE documentation (btstack)](https://www.raspberrypi.com/documentation/pico-sdk/networking.html)
- [CYW43439 datasheet — Wi-Fi + BLE combo](https://www.infineon.com/cms/en/product/wireless-connectivity/airoc-wi-fi-plus-bluetooth-combos/wi-fi-4-702.11n/cyw43439/)
- [BLE advertising packet format (Bluetooth SIG)](https://www.bluetooth.com/specifications/specs/core-specification/)
- [Nintendo StreetPass — prior art for passive peer discovery in handheld devices](https://en.wikipedia.org/wiki/StreetPass)
