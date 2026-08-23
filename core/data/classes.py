CLASSES = {
    "Dagger": {
        "name": "Dagger",
        "description": "A swift melee fighter.",
        "base_passive": {
            "name": "Placeholder Dagger Passive",
            "description": "Increases CRIT rate by 5%.",
            "stats": {"crit": 5}
        },
        "starter_cards": ["slash", "slash", "dash", "block"]
    },
    "Pet": {
        "name": "Pet",
        "description": "Fights alongside a loyal companion.",
        "base_passive": {
            "name": "Placeholder Pet Passive",
            "description": "Increases EVA rate by 5%.",
            "stats": {"eva": 5}
        },
        "starter_cards": ["command", "command", "block", "block"]
    },
    "Gunner": {
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
