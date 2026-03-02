import json

# Lire le rapport existant
with open('monitoring_report.json') as f:
    report = json.load(f)

print('🎯 Asmblr Monitoring Demo - RÉSULTATS FINAUX')
print('=' * 50)
print('✅ Statut: ' + report["status"].upper())
print('📊 Métriques enregistrées: ' + str(report["demo_summary"]["metrics_registered"]))
print('🚨 Alertes créées: ' + str(report["demo_summary"]["alerts_created"]))
print('🏥 Health checks: ' + str(report["demo_summary"]["health_checks"]))
print('🔧 Services actifs: ' + str(report["demo_summary"]["services_running"]))
print()
print('📈 État des composants:')
for component, status in report['components'].items():
    print('  ' + component + ': ' + status)
print()
print('📊 Échantillon de métriques:')
for metric, value in report['metrics_sample'].items():
    print('  ' + metric + ': ' + str(value))
print()
print('📄 Rapport complet disponible: monitoring_report.json')
print('🚀 Le monitoring Asmblr est opérationnel!')
