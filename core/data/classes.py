from enum import StrEnum


class CharacterClass(StrEnum):
    DAGGER = "Dagger"
    PET = "Pet"
    GUNNER = "Gunner"


CLASSES = {
    CharacterClass.DAGGER: {
        "name": "Dagger",
        "description": "A swift melee fighter.",
        "base_passive": {
            "name": "Placeholder Dagger Passive",
            "description": "Increases CRIT rate by 5%.",
            "stats": {"crit": 5}
        },
        "starter_cards": ["slash", "slash", "dash", "block"]
    },
    CharacterClass.PET: {
        "name": "Pet",
        "description": "Fights alongside a loyal companion.",
        "base_passive": {
            "name": "Placeholder Pet Passive",
            "description": "Increases EVA rate by 5%.",
            "stats": {"eva": 5}
        },
        "starter_cards": ["command", "command", "block", "block"]
    },
    CharacterClass.GUNNER: {
        "name": "Gunner",
        "description": "A ranged specialist.",
        "base_passive": {
            "name": "Placeholder Gunner Passive",
            "description": "Increases ACC by 5%.",
            "stats": {"acc": 5}
        },
        "starter_cards": ["shoot", "shoot", "block", "block"]
    }
}
