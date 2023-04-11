from dataclasses import dataclass


@dataclass
class InhibitorInfo:
    # The application mame
    app_name: str

    # The reason, if any
    reason: str


class KeepAwakeInfo:
    def __init__(self, inhibitors: list[InhibitorInfo] | None = None):
        self.inhibitors = inhibitors or []

    def add(self, inhibitor: InhibitorInfo):
        self.inhibitors.append(inhibitor)

    @property
    def n_inhibitors(self) -> int:
        return len(self.inhibitors)

    @property
    def keepawake(self) -> bool:
        return bool(self.inhibitors)
