"""Original room-specific KIP guidance. Three progressive, optional exchanges.

The first line establishes the room's central observation and includes a joke.
Subsequent lines reveal a relationship without listing a full input sequence.
"""
KIP_GUIDE = {
    1: (
        "Welcome to the facility. That control panel wakes machinery, and the floor plate wants a heavier friend. I have volunteered the crate.",
        "A panel can stay active after you walk away. A pressure plate cannot. One of us has commitment issues.",
        "Think about what should remain on the plate when you head for the exit.",
    ),
    2: (
        "Two pressure plates, one secured passage. Whoever designed this door really disliked guests.",
        "Look for ways to reach the upper switch before committing the cargo below.",
        "The two plates need simultaneous weight; use the available objects, not your optimism.",
    ),
    3: (
        "Freight is our most valuable employee. It does two jobs and has never asked for a break.",
        "A staging sensor can power a station that remembers the crate, even after it moves.",
        "Get the staging relay latched before sending cargo to dispatch. The same crate can then do both jobs.",
    ),
    4: (
        "Emergency procedures say to remain calm. The timed gate says to remain unusually athletic.",
        "Disable the dangerous machinery before attempting a timed crossing.",
        "Think about where you can stand safely before starting the final timed switch.",
    ),
    5: (
        "New maintenance skills: hold against a wall to slide, then jump away. The lifts have been inspected. The inspector was me, unfortunately.",
        "A lift's route depends on what is powering it, not just where it is now.",
        "Look for a way to hold the second lift's plate while you reach the upper lock.",
    ),
    6: (
        "Welcome to heavy machinery. The safety manual is also quite heavy, so nobody reads it.",
        "The crusher and the exit have different controls. Learn which state makes movement safe.",
        "Secure the first plate and stop the crusher before attempting the final door.",
    ),
    7: (
        "Counterweights are brilliant. They lift everything except workplace morale.",
        "The first plate powers a crossing. The relay on the far side can remember that power.",
        "Latch the first crossing before asking the cargo to perform its second task.",
    ),
    8: (
        "Shutdown takes three steps. We had a fourth, but management deleted the instructions.",
        "This machinery cares about order: watch what changes after each station.",
        "Find the sequence indicators and activate the stages in their intended order, then secure the core plate.",
    ),
    9: (
        "Your suit now has a directional dash: press X with movement keys. The backup generators have stopped arguing. Neither is running.",
        "Separate generators can power different stretches; one start button is not the whole story.",
        "Trace each cable and consider when the pressure plate must remain occupied.",
    ),
    10: (
        "Circuit breakers like rules. We have approximately seventeen, and all disagree.",
        "The numbered stations form a sequence, then two conditional controls complete the circuit.",
        "Resolve the sequence before expecting the final pair of switches to matter.",
    ),
    11: (
        "One mirror, two destinations. I also multitask, mainly by making two mistakes at once.",
        "The beam can power a ferry or the exit receiver, but not both at once.",
        "Store the ferry's powered state at the far relay before redirecting the light.",
    ),
    12: (
        "This system is overloaded. I submitted a ticket; the ticket is also overloaded.",
        "Generator supply and optical calibration are separate dependencies.",
        "Establish stable power and calibration before placing weight and triggering overload control.",
    ),
    13: (
        "The drainage system works. Unfortunately, so does the refill system.",
        "Dry and flooded states are both useful. Ask yourself what must be remembered between them.",
        "Store the dry-state signal at the sump relay, then restore water for the exit.",
    ),
    14: (
        "Ventilation pushes you around, and the spring pad gives you a boost. Mine mostly move paperwork.",
        "Observe the fan's direction before jumping into its airflow.",
        "Use the fan to reach the high sensor, then handle the gate separately.",
    ),
    15: (
        "The pressure valves have personality. One of them is extremely dramatic.",
        "Steam, plate weight, and auxiliary pressure have different jobs.",
        "Identify which valve removes the hazard and which one makes the final route possible.",
    ),
    16: (
        "The gaps now have dash rechargers. Structural integrity remains a suggestion. Please treat the floor as a colleague on probation.",
        "Some platforms won't support you for long; plan a safe resting place first.",
        "Stabilize the anchor and power systems before relying on the final valve route.",
    ),
    17: (
        "Rebooting the system is easy. Rebooting the paperwork takes three business weeks.",
        "The west generator, optical sync, and east generator aren't interchangeable.",
        "Follow the power path and hold the core plate when both sides are ready.",
    ),
    18: (
        "The Core has a sequence, a wind channel, and a heavy plate. I have a headache.",
        "Watch the sequence indicators and how wind changes the cargo route.",
        "Complete the sequence before using the wind control to position weight on the plate.",
    ),
    19: (
        "Containment is mostly intact, according to the signs. The signs are on fire metaphorically.",
        "Coolant and stabilization must come before any rushed crossing.",
        "Make the route safe, then start the final sprint only when ready.",
    ),
    20: (
        "The striped service panel yields to a dash, but the ferry still needs power. I booked you a seat; dispatch says it's technically a crate.",
        "The ferry and exit circuit share reserve power. A second source could settle their argument.",
        "Cross while the ferry has reserve power, establish independent supply, then transfer the reserve to evacuation.",
    ),
}

KIP_CHAPTER_MILESTONES = {
    1: "KIP: Orientation complete. The facility is surprised. So am I.",
    2: "KIP: The foundry is behind us. I have requested a less explosive department.",
    3: "KIP: You fixed the power grid. While you're here, could you charge my battery?",
    4: "KIP: The optics are stable. My outlook remains under maintenance.",
    5: "KIP: The flooding stopped. Accounting would like the water returned.",
    6: "KIP: The furnace is quiet. You have angered all the safety inspectors.",
    7: "KIP: One sector to daylight. Please bring the crate, not the building.",
}

AUX_GUIDE = {
    21: ("Optional freight duty! Dash the striped panel to clear service access. The crate requested overtime; I declined on its behalf.", "The route rewards doing more with one cargo load.", "Study the changeover rather than activating every console."),
    22: ("Optional optics challenge. If you see me twice, please tell both of me to work.", "One alignment can grant access to the next.", "Use a reachable mirror station to change what the beam feeds."),
    23: ("Optional sump inspection. I've brought waterproof paperwork.", "Wet and dry states reveal different routes.", "Use the water controls to reposition cargo, then change the state again."),
    24: ("Blackstart procedure: there is a dash-breakable service seal along the route. It sounds ominous because accounting named it.", "A fresh power source needs an order of operations.", "Trace dependencies before energizing the final receiver."),
}


# Expansion dialogues: each archetype has a different objective and a small joke.
EXPANSION_TOPICS = [
    ("crosswire", "Trace both sides of the gate before moving the cargo."),
    ("freight belt", "Try changing which way the freight belt moves."),
    ("counterweight", "Power the shuttle before trusting the crossing."),
    ("security beam", "A low console controls that intimidating vertical beam."),
    ("ventilation", "The fan and the steam valve solve separate problems."),
    ("relay sequence", "Three stations in the intended order, not the convenient order."),
    ("optical inspection", "The gallery control disables the beam, and the generator stops the shutter."),
    ("brittle bridge", "The bridge will not wait politely for your decision."),
    ("ballast valve", "The basin changes when the valve is turned."),
    ("crusher corridor", "The generator shuts down the hammer before freight moves."),
    ("relay memory", "A relay can remember two active feeds."),
    ("dual freight", "Separate cargo loads must stay on separate sensors."),
]
EXPANSION_JOKES = [
    "The safety inspection passed. The inspector was the door.",
    "This floor has commitment issues. The ceiling has opinions.",
    "The crate requested overtime pay. Management offered gravity.",
    "I filed a hazard report. It was immediately classified as a hazard.",
    "The equipment warranty excludes being equipment.",
    "We built a relay that remembers better than I do. Rude.",
    "The vent is the only employee who gets to blow off steam.",
    "I was promoted to facility morale. Results are inconclusive.",
]
EXPANSION_GUIDE = {
    number: (
        f"Room {number:02d}: {EXPANSION_TOPICS[(number - 25) % 12][0]}. "
        + EXPANSION_JOKES[(number + (number-25)//12) % len(EXPANSION_JOKES)],
        EXPANSION_TOPICS[(number - 25) % 12][1],
        "Reach the upper service platform first, then secure the crate plates at the eastern bulkhead.",
    )
    for number in range(25, 81)
}

def dialogue_for_room(level_num: int, stage: int, story_flags=()) -> str:
    exchanges = KIP_GUIDE.get(level_num) or AUX_GUIDE.get(level_num) or EXPANSION_GUIDE.get(level_num)
    if exchanges is None:
        return "This sector isn't in my maintenance route. Which, frankly, is a relief."
    stage = min(max(0, int(stage)), len(exchanges) - 1)
    line = exchanges[stage]
    if stage == 0 and level_num >= 9 and level_num < 20 and "freight_twice" in story_flags:
        line += " Also, the freight crate still has a better performance review than me."
    if level_num == 20 and stage == 0 and "kip_room_1" in story_flags:
        line = "Remember our first plate and crate? You learned a lot since then. " + line
    return line
