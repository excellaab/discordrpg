from dataclasses import dataclass, field
from collections import defaultdict
from typing import Callable
from lib import roomgen


@dataclass
class Room:
    floors: set[int]
    generate: Callable[..., None]
    weight: float = 1.0
    tags: set[str] = field(default_factory=set)

ROOMS: dict[str, Room] = {
    "battle": Room(
        floors={1,2,3,4},
        generate=roomgen.gen_battle,
        weight=1.0,
        tags={"combat", "common", "danger"},
    ),
    "event": Room(
        floors={1,2,3,4},
        generate=roomgen.gen_event,
        weight=0.8,
        tags={"event", "common", "neutral"},
    ),
    "fountain": Room(
        floors={1,2,3,4},
        generate=roomgen.gen_fountain,
        weight = 0.5,
        tags={"event", "rare", "safe"},
    ),
    "market": Room(
        floors={2,3,4},
        generate=roomgen.gen_market,
        weight=0.4,
        tags={"shop", "rare", "safe"},
    ),
    "blacksmith": Room(
        floors={3,4},
        generate=roomgen.gen_blacksmith,
        weight=0.4,
        tags={"shop", "rare", "safe"},
    ),
    "cursed": Room(
        floors={3,4},
        generate=roomgen.gen_cursed,
        weight=0.2,
        tags={"combat", "legendary", "danger"},
    ),
    "boss": Room(
        floors={1,2,3,4},
        generate=roomgen.gen_boss,
        weight=0,
        tags={"boss", "legendary", "danger"},
    ),
    "finalboss": Room(
        floors={4},
        generate=roomgen.gen_finalboss,
        weight=0,
        tags={"boss", "prismatic", "danger"}
    ),
    "basecamp": Room(
        floors={1},
        generate=roomgen.gen_basecamp,
        weight=0,
        tags={"event", "common", "safe"}
    )
}

ROOMS_BY_FLOOR: dict[int, list[str]] = defaultdict(list)
for room, data in ROOMS.items():
    for floor in data.floors:
        ROOMS_BY_FLOOR[floor].append(room)