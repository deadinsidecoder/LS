from dataclasses import dataclass


@dataclass
class URLRecord:
    id: int
    short: str
    long: str
    created_at: int
    clicks_count: int