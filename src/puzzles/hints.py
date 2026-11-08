"""On-demand clues derived from the next unsatisfied signal in the authored route."""

def next_hint(manager, route, player_rect, previous, depth, hint_notes=None):
    signals = manager.active_signals
    hint_notes = hint_notes or {}
    for link in route:
        if link in signals:
            continue
        if link in hint_notes:
            depth = min(depth + 1, 2) if previous == link else 0
            return link, depth, hint_notes[link][depth]
        for group in manager.timer_mech.sequences.values():
            if link in group["order"] and not group["completed"]:
                link = group["order"][group["progress"]]
        devices = [
            (manager.plates, "floor sensor", "It needs a weight after you walk away.", "Park a crate on the lit strip."),
            (manager.switches, "control panel", "Look for its indicator lamp.", "Use Interact beside the panel."),
            (manager.generators, "generator", "The machine has a local starter.", "Use Interact at the generator housing."),
            (manager.valves, "valve", "Follow the pipe to its handwheel.", "Turn the wheel with Interact."),
            (manager.optical_beams, "optical receiver", "Follow the light and check for obstructions.", "Clear the light path and align any mirror toward the pickup."),
        ]
        for objects, name, second, third in devices:
            for obj in objects:
                if obj.link_id != link:
                    continue
                rect = getattr(obj, "rect", None)
                if rect is None:
                    rect = obj.base_rect if hasattr(obj, "base_rect") else obj.receiver_rect
                side = "right" if rect.centerx >= player_rect.centerx else "left"
                clues = [f"Look for a {name}.", second, f"{third} Look to your {side}."]
                depth = min(depth + 1, 2) if previous == link else 0
                return link, depth, clues[depth]
    return None, 0, "The marked route leads to the exit portal."
