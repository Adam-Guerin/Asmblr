from app.signal_insights import (
    cluster_pains,
    extract_structured_pains,
    generate_opportunities,
)


def test_pain_requires_actor_and_problem():
    pages = [
        {"url": "https://signal.example", "text": "Operators struggle to keep compliance hubs synchronized with manual notes."},
        {"url": "https://noise.example", "text": "Need better automation for scheduling reports."},
    ]
    result = extract_structured_pains(pages)
    assert len(result["pains"]) == 1
    assert result["pains"][0]["actor"].lower() == "operators"
    assert len(result["rejected"]) == 1
    assert result["rejected"][0]["reason"] == "missing actor"


def test_cluster_assigns_job():
    pains = [
        {
            "id": "pain_1",
            "problem": "Operators need faster approvals for compliance sign-offs.",
            "text": "Operators need faster approvals for compliance sign-offs.",
            "actor": "Operators",
            "context": "during audits",
            "difficulty": "concrete",
        },
        {
            "id": "pain_2",
            "problem": "Managers need to align budgets with supplier risk quickly.",
            "text": "Managers need to align budgets with supplier risk quickly.",
            "actor": "Managers",
            "context": "during planning",
            "difficulty": "medium",
        },
    ]
    clusters = cluster_pains(pains)
    assert clusters
    assert any("Job" in cluster["cluster_label"] for cluster in clusters)
    assert clusters[0]["density"] == len(clusters[0]["pain_ids"])


def test_opportunity_links_pains():
    clusters = [
        {
            "cluster_id": 0,
            "cluster_label": "Job 1: approvals",
            "pain_ids": ["pain_1"],
            "keywords": ["approval", "compliance"],
            "density": 1,
        }
    ]
    pains = [
        {
            "id": "pain_1",
            "actor": "Operators",
            "problem": "Operators need faster approvals.",
            "text": "Operators need faster approvals.",
            "context": "during audits",
            "difficulty": "concrete",
        }
    ]
    opportunities = generate_opportunities(clusters, pains)
    assert opportunities
    for opp in opportunities:
        assert opp["linked_pains"] == ["pain_1"]
        assert "Operators" in opp["name"]
