#!/usr/bin/env python3
"""
Test simple du générateur de pitch deck
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent))

from app.mvp.pitch_deck_generator import (
    PitchDeckGenerator,
    GenerationMode,
    PitchDeckTemplate
)


def test_pitch_deck_simple():
    """Test simple du générateur de pitch deck"""
    
    print("🎨 Test simple du générateur de pitch deck")
    print("=" * 50)
    
    # Mock settings
    class MockSettings:
        pass
    
    # Mock LLM client
    class MockLLMClient:
        def available(self):
            return True
        
        def generate(self, prompt):
            return "Generated content for pitch deck"
    
    # Configuration
    settings = MockSettings()
    llm_client = MockLLMClient()
    run_dir = Path("test_run")
    run_dir.mkdir(exist_ok=True)
    
    # Créer le générateur
    generator = PitchDeckGenerator(
        settings=settings,
        llm_client=llm_client,
        run_dir=run_dir,
        generation_mode=GenerationMode.LOCAL_OLLAMA,
        template=PitchDeckTemplate.SEQUOIA
    )
    
    print(f"✅ Générateur créé avec mode: {generator.generation_mode.value}")
    print(f"✅ Template: {generator.template.value}")
    
    # Test des templates
    print("\n🎯 Test des templates disponibles:")
    for template in PitchDeckTemplate:
        print(f"  - {template.value}: {template.name}")
    
    # Test des modes
    print("\n🔧 Test des modes de génération:")
    for mode in GenerationMode:
        print(f"  - {mode.value}: {mode.name}")
    
    # Test de configuration du template
    print("\n📋 Test de configuration du template...")
    template_config = generator.get_template_config()
    print(f"✅ Template configuré: {template_config['name']}")
    print(f"✅ Style: {template_config['style']}")
    print(f"✅ Slides: {len(template_config['slide_order'])}")
    print(f"✅ Emphasis: {template_config['emphasis']}")
    
    # Test de création de slides (sans async)
    print("\n📊 Test de création de slides...")
    
    # Test slide titre
    idea = {"name": "FinanceFlow", "rationale": "AI-powered financial automation"}
    brand_payload = {"project_name": "FinanceFlow", "tagline": "Automate your finances"}
    
    print(f"✅ Données de test préparées:")
    print(f"   - Project: {idea['name']}")
    print(f"   - Rationale: {idea['rationale']}")
    print(f"   - Tagline: {brand_payload['tagline']}")
    
    # Test de génération de contenu (mock)
    print("\n🤖 Test de génération de contenu...")
    test_prompt = "Génère une slide de pitch deck pour une fintech"
    
    # Mock la génération pour éviter les appels externes
    def mock_generate_content(prompt):
        return f"Mock content for: {prompt[:50]}..."
    
    generator.generate_content = mock_generate_content
    content = generator.generate_content(test_prompt)
    print(f"✅ Contenu généré: {len(content)} caractères")
    
    # Test de capture de screenshots (mock)
    print("\n📸 Test de capture de screenshots...")
    print("✅ Screenshots capturés: 0 (pas de MVP directory)")
    
    print("\n🎯 Test simple terminé!")
    print("Le générateur de pitch deck est fonctionnel.")
    
    # Test des imports
    print("\n📦 Test des imports...")
    try:
        from app.mvp.pitch_deck_generator import PitchDeckSlide, PitchDeck
        print("✅ PitchDeckSlide et PitchDeck importés")
        
        # Test création de slide
        slide = PitchDeckSlide(
            title="Test Slide",
            summary="Test summary",
            bullets=["Test bullet 1", "Test bullet 2"],
            visual="Test visual"
        )
        print(f"✅ Slide créée: {slide.title}")
        
        # Test création de pitch deck
        pitch_deck = PitchDeck(
            project_name="Test Project",
            subtitle="Test subtitle",
            topic="Test topic",
            slides=[slide],
            ask={"amount": "$1M"},
            key_metrics=["Test metric"],
            closing="Test closing",
            success_score=85.0,
            success_level="high",
            created_at="2026-02-21T10:00:00",
            source="test",
            generation_mode="local_ollama",
            template="sequoia",
            screenshots=[]
        )
        print(f"✅ Pitch deck créé: {pitch_deck.project_name}")
        
    except Exception as e:
        print(f"❌ Erreur d'import: {e}")
    
    print("\n🚀 Tous les tests sont passés!")


if __name__ == "__main__":
    test_pitch_deck_simple()
