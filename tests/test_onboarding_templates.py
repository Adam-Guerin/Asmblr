from app.onboarding_templates import get_onboarding_templates, get_onboarding_template


def test_onboarding_templates_have_expected_paths():
    templates = get_onboarding_templates()
    assert {"idee_floue", "idee_validee", "copie_concurrent"}.issubset(set(templates.keys()))


def test_onboarding_template_contains_seed_defaults():
    template = get_onboarding_template("idee_floue")
    assert template["seed_icp"]
    assert template["seed_pains"]
    assert template["seed_competitors"]
    assert isinstance(template["n_ideas"], int)
