#!/usr/bin/env python
"""
Test du Motion Design System pour Asmblr
"""

from app.core.motion_design_final import motion_design_system
from datetime import datetime

def test_motion_design():
    """Test complet du système de motion design"""
    print("🎨 Test du Motion Design System")
    print("=" * 50)
    
    try:
        # Test 1: Création de campagne
        print("1. Création d'une campagne marketing...")
        campaign = motion_design_system.create_campaign(
            name="AI Compliance Platform",
            brand_name="Asmblr AI",
            target_audience="Tech Companies",
            duration=6.0
        )
        
        print(f"   ✅ Campagne créée: {campaign.name}")
        print(f"   📊 Scènes: {len(campaign.scenes)}")
        print(f"   🎯 Durée totale: {campaign.total_duration:.1f}s")
        
        # Test 2: Export en HTML
        print("\n2. Export en HTML...")
        html_export = motion_design_system.export_campaign(campaign, format_type="html")
        
        with open("test_campaign.html", "w", encoding="utf-8") as f:
            f.write(html_export)
        
        print("   ✅ Fichier HTML créé: test_campaign.html")
        
        # Test 3: Export en JSON
        print("\n3. Export en JSON...")
        json_export = motion_design_system.export_campaign(campaign, format_type="json")
        
        with open("test_campaign.json", "w", encoding="utf-8") as f:
            f.write(json_export)
        
        print("   ✅ Fichier JSON créé: test_campaign.json")
        
        # Test 4: Résumé de campagne
        print("\n4. Résumé de la campagne...")
        summary = motion_design_system.get_campaign_summary(campaign)
        
        print(f"   📝 Nom: {summary['name']}")
        print(f"   🎯 Audience: {summary['target_audience']}")
        print(f"   🎨 Couleur marque: {summary['brand']}")
        print(f"   📊 Scènes: {summary['scenes_count']}")
        print(f"   🎯 Assets totaux: {summary['total_assets']}")
        print(f"   📅 Statut: {summary['status']}")
        
        print("\n🎉 Motion Design System testé avec succès !")
        print("\n📁 Fichiers créés:")
        print("   - test_campaign.html (dashboard interactif)")
        print("   - test_campaign.json (données structurées)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        return False

if __name__ == "__main__":
    test_motion_design()
