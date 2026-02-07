from __future__ import annotations

from copy import deepcopy
from typing import Any


ONBOARDING_TEMPLATES: dict[str, dict[str, Any]] = {
    "idee_floue": {
        "label": "Idee floue",
        "description": "Tu as une intuition mais pas encore de persona ou de douleur bien qualifies.",
        "topic": "Assistant IA pour automatiser les operations repetitives d'une petite equipe",
        "theme": "validation rapide",
        "seed_icp": "Fondateur ou PM dans une equipe de 2-10 personnes, sans equipe data dediee.",
        "seed_pains": [
            "On perd du temps a prioriser les taches sans signal clair.",
            "Le suivi des retours clients est manuel et incomplet.",
            "On lance des features sans valider la demande avant dev.",
        ],
        "seed_competitors": [
            "Notion AI",
            "ClickUp",
            "Trello + automatisations no-code",
        ],
        "seed_context": "Objectif: obtenir un premier MVP pertinent en moins de 10 minutes.",
        "n_ideas": 3,
        "fast_mode": True,
    },
    "idee_validee": {
        "label": "Idee validee",
        "description": "Le probleme est clair et documente. Tu veux accelerer l'execution go-to-market.",
        "topic": "SaaS B2B de gestion des incidents conformite pour PME",
        "theme": "execution go-to-market",
        "seed_icp": "Responsable operations ou conformite dans une PME de 20-200 employes.",
        "seed_pains": [
            "Les preuves d'audit sont eparpillees entre plusieurs outils.",
            "Les equipes perdent du temps a preparer les controles de conformite.",
            "La detection des ecarts est tardive, donc couteuse.",
        ],
        "seed_competitors": [
            "Vanta",
            "Drata",
            "Secureframe",
        ],
        "seed_context": "Hypothese: differenciation par vitesse de mise en place et simplicite operative.",
        "n_ideas": 6,
        "fast_mode": False,
    },
    "copie_concurrent": {
        "label": "Copie concurrent",
        "description": "Tu veux reproduire/ameliorer une offre existante avec un angle plus niche ou plus simple.",
        "topic": "Alternative simple a un outil de social scheduling pour createurs independants",
        "theme": "repositionnement concurrentiel",
        "seed_icp": "Createur solo (YouTube, TikTok, newsletter) avec besoin d'automatisation legere.",
        "seed_pains": [
            "Les outils existants sont trop complexes pour un usage solo.",
            "Le prix augmente vite des qu'on veut des automatisations.",
            "La publication multi-plateforme prend trop de temps chaque semaine.",
        ],
        "seed_competitors": [
            "Buffer",
            "Hootsuite",
            "Later",
        ],
        "seed_context": "Strategie: copier la valeur coeur, supprimer la complexite, baisser le time-to-value.",
        "n_ideas": 4,
        "fast_mode": True,
    },
}


def get_onboarding_templates() -> dict[str, dict[str, Any]]:
    return deepcopy(ONBOARDING_TEMPLATES)


def get_onboarding_template(template_id: str) -> dict[str, Any]:
    template = ONBOARDING_TEMPLATES.get(template_id)
    if not template:
        raise KeyError(f"Unknown onboarding template: {template_id}")
    return deepcopy(template)
