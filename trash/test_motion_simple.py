#!/usr/bin/env python
"""
Test simple du Motion Design System pour Asmblr
"""

import os
import json
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io

def create_simple_campaign():
    """Test simple de création de campagne"""
    print("🎨 Test Simple du Motion Design System")
    print("=" * 50)
    
    try:
        # Créer le répertoire assets
        os.makedirs("assets", exist_ok=True)
        
        # Configuration de base
        brand_colors = {
            "primary": "#2563EB",
            "secondary": "#FF6B6B",
            "accent": "#FFC107",
            "text": "#FFFFFF",
            "background": "#F8F9FA"
        }
        
        # Créer un logo simple
        print("1. Création du logo...")
        img = Image.new('RGBA', (300, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Utiliser une police par défaut
        try:
            font = ImageFont.truetype("arial.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        # Dessiner le texte
        draw.text((20, 30), "Asmblr AI", font=font, fill=brand_colors["primary"])
        
        # Sauvegarder l'image
        img.save("assets/logo.png")
        print("   ✅ Logo créé: assets/logo.png")
        
        # Créer une scène simple
        print("\n2. Création des scènes...")
        scenes = [
            {
                "name": "logo_intro",
                "duration": 2.0,
                "assets": ["logo.png"],
                "transitions": [
                    {"type": "fade_in", "duration": 0.5},
                    {"type": "zoom_in", "duration": 0.3}
                ]
            },
            {
                "name": "text_innovation",
                "duration": 1.5,
                "assets": ["logo.png"],
                "transitions": [
                    {"type": "typewriter", "duration": 1.5}
                ]
            },
            {
                "name": "call_to_action",
                "duration": 1.0,
                "assets": ["logo.png"],
                "transitions": [
                    {"type": "bounce", "duration": 0.5}
                ]
            }
        ]
        
        print(f"   ✅ {len(scenes)} scènes créées")
        
        # Créer la campagne
        print("\n3. Création de la campagne...")
        campaign = {
            "name": "Asmblr AI Platform",
            "brand_name": "Asmblr AI",
            "target_audience": "Tech Companies",
            "total_duration": sum(scene["duration"] for scene in scenes),
            "scenes": scenes,
            "brand_guidelines": brand_colors,
            "created_at": datetime.utcnow().isoformat(),
            "status": "draft"
        }
        
        print(f"   ✅ Campagne créée: {campaign['name']}")
        print(f"   📊 Durée totale: {campaign['total_duration']:.1f}s")
        
        # Exporter en JSON
        print("\n4. Export en JSON...")
        with open("simple_campaign.json", "w", encoding="utf-8") as f:
            json.dump(campaign, f, indent=2, ensure_ascii=False)
        
        print("   ✅ Fichier JSON créé: simple_campaign.json")
        
        # Créer un HTML simple
        print("\n5. Création du dashboard HTML...")
        html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{campaign['name']} - Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, {brand_colors['background']}, #e3f2fd);
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }}
        .campaign-title {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .scene {{
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .scene-title {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 10px;
            color: {brand_colors['text']};
        }}
        .logo {{
            max-width: 200px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .timeline {{
            border-left: 4px solid {brand_colors['accent']};
            padding-left: 15px;
            margin: 10px 0;
        }}
        .timeline-item {{
            margin-bottom: 10px;
            position: relative;
        }}
        .timeline-content {{
            font-weight: bold;
            color: {brand_colors['text']};
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1 class="campaign-title">{campaign['name']}</h1>
        <p>Campagne pour {campaign['target_audience']}</p>
        <p>Durée totale: {campaign['total_duration']:.1f}s</p>
    </div>
    
    <div class="scene">
        <h2 class="scene-title">Logo Principal</h2>
        <img src="assets/logo.png" alt="Logo" class="logo">
    </div>
    
    <div class="timeline">
        <h2>Timeline de la Campagne</h2>
"""
        
        current_time = 0
        for scene in scenes:
            html_content += f"""
        <div class="timeline-item">
            <div class="timeline-content">
                <div>{scene['name']}</div>
                <div>{current_time:.1f}s - {current_time + scene['duration']:.1f}s</div>
            </div>
        </div>
"""
            current_time += scene['duration']
        
        html_content += """
    </div>
    
    <div style="text-align: center; margin-top: 30px;">
        <button style="background: {brand_colors['primary']}; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer;">
            Lancer la Campagne
        </button>
    </div>
</body>
</html>
"""
        
        with open("simple_dashboard.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print("   ✅ Dashboard HTML créé: simple_dashboard.html")
        
        # Résumé final
        print("\n🎉 Test terminé avec succès !")
        print("\n📁 Fichiers créés:")
        print("   - assets/logo.png")
        print("   - simple_campaign.json")
        print("   - simple_dashboard.html")
        print("\n🌐 Ouvrez simple_dashboard.html dans votre navigateur")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        return False

if __name__ == "__main__":
    create_simple_campaign()
