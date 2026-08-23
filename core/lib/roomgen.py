import random
from data.rooms import ROOMS, ROOMS_BY_FLOOR

FINAL_ROOM = 8

def gen_room(rank, floor, number):
    if number == 1:
        return ROOMS["basecamp"].generate(rank)

    if number == FINAL_ROOM:
        if floor == 4:
            return ROOMS["finalboss"].generate(rank)
        return ROOMS["boss"].generate(rank, floor)

    candidates: list = ROOMS_BY_FLOOR[floor]
    weights = [ROOMS[room].weight for room in candidates]

    return ROOMS[random.choices(candidates, weights=weights)].generate(rank, floor)