class TimerMechanism:
    """Manages countdown timers for timed switches and ordered sequence puzzles."""

    def __init__(self) -> None:
        self.timers: dict[str, tuple[float, float]] = {}
        self.sequences: dict[str, dict] = {}

    def start_timer(self, link_id: str, duration: float) -> None:
        self.timers[link_id] = (duration, max(0.01, duration))

    def register_sequence(self, group_id: str, ordered_links: list[str]) -> None:
        self.sequences[group_id] = {
            "order": list(ordered_links),
            "progress": 0,
            "completed": False,
        }

    def notify_sequence_step(
        self, link_id: str, switches_by_id: dict
    ) -> tuple[bool, bool]:
        for group in self.sequences.values():
            if link_id in group["order"]:
                if group["completed"]:
                    return True, False
                expected = group["order"][group["progress"]]
                if link_id == expected:
                    group["progress"] += 1
                    if group["progress"] >= len(group["order"]):
                        group["completed"] = True
                    return True, False
                else:
                    group["progress"] = 0
                    for lid in group["order"]:
                        if lid in switches_by_id:
                            switches_by_id[lid].active = False
                    return False, True
        return True, False

    def update(self, dt: float, devices_by_id: dict) -> None:
        expired = []
        for link_id, (rem, total) in list(self.timers.items()):
            new_rem = rem - dt
            if new_rem <= 0.0:
                expired.append(link_id)
                if link_id in devices_by_id:
                    devices_by_id[link_id].active = False
            else:
                self.timers[link_id] = (new_rem, total)
        for link_id in expired:
            del self.timers[link_id]

    def get_ratio(self, link_id: str) -> float:
        if link_id not in self.timers:
            return 0.0
        rem, total = self.timers[link_id]
        return rem / total

    def is_sequence_complete(self, group_id: str) -> bool:
        return bool(self.sequences.get(group_id, {}).get("completed", False))

    def get_state(self) -> dict:
        return {
            "timers": dict(self.timers),
            "sequences": {
                k: {
                    "order": list(v["order"]),
                    "progress": v["progress"],
                    "completed": v["completed"],
                }
                for k, v in self.sequences.items()
            },
        }

    def set_state(self, state: dict) -> None:
        self.timers = {k: tuple(v) for k, v in state.get("timers", {}).items()}
        self.sequences = {
            k: {
                "order": list(v["order"]),
                "progress": int(v["progress"]),
                "completed": bool(v["completed"]),
            }
            for k, v in state.get("sequences", {}).items()
        }