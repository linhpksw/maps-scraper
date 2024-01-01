from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Place:
    name: str
    address: str
    business_hours: dict[str, str] = field(default_factory=lambda: {})
    phone_number: Optional[str] = None
    photo_link: Optional[str] = None
    rate: Optional[str] = None
    reviews: Optional[str] = None
