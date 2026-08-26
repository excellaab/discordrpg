import random
from data.rooms import ROOMS, ROOMS_BY_FLOOR

# config
TOTAL_FLOORS = 4
ROOMS_PER_FLOOR = 8
MAX_RUN_LEVEL = 20

def gen_room(rank, floor, number, current_room):
    if number == 1:
        return ROOMS["basecamp"].generate(rank)

    if number == ROOMS_PER_FLOOR:
        if floor == 4:
            return ROOMS["finalboss"].generate(rank)
        return ROOMS["boss"].generate(rank, floor)

    candidates: list = ROOMS_BY_FLOOR[floor]
    weights = [
        ROOMS[room].weight
        for room in candidates
        if not (ROOMS[room].tag == "safe" and ROOMS[current_room].tag == "safe")
    ]

    return ROOMS[random.choices(candidates, weights=weights)].generate(rank, floor)