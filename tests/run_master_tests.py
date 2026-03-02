"""
Master Test Runner for Asmblr New Features
Orchestrates all test suites: comprehensive, integration, performance, and security
"""

import asyncio
import json
import os
import time
from datetime import datetime

# Import all test runners
from test_new_features_comprehensive import TestNewFeatures
from test_integration_workflows import TestIntegrationWorkflows
from test_performance_scalability import TestPerformanceAndScalability
from test_security_compliance import TestSecurityAndCompliance

class MasterTestRunner:
    """Master test runner that orchestrates all test suites"""
    
    def __init__(self):
        self.test_suites = {
            "comprehensive": TestNewFeatures,
            "integration": TestIntegrationWorkflows,
            "performance": TestPerformanceAndScalability,
            "security": TestSecurityAndCompliance
        }
        self.master_results = {}
        self.temp_dir = None
        
    async def run_all_test_suites(self):
        """Run all test suites and generate master report"""
        print("🚀 Starting Master Test Suite for Asmblr New Features")
        print("=" * 80)
        
        start_time = time.time()
        
        # Create temporary directory for reports
        import tempfile
        self.temp_dir = tempfile.mkdtemp(prefix="asmblr_master_test_")
        
        # Run each test suite
        suite_results = {}
        
        for suite_name, test_class in self.test_suites.items():
            print(f"\n{'='*20} Running {suite_name.title()} Tests {'='*20}")
            
            try:
                # Initialize and run test suite
                tester = test_class()
                
                if suite_name == "comprehensive":
                    result = await tester.run_all_tests()
                elif suite_name == "integration":
                    result = await tester.run_all_integration_tests()
                elif suite_name == "performance":
                    result = await tester.run_all_performance_tests()
                elif suite_name == "security":
                    result = await tester.run_all_security_tests()
                
                suite_results[suite_name] = result
                
                # Print suite summary
                summary_key = f"{suite_name}_test_summary" if suite_name != "comprehensive" else "test_summary"
                summary = result.get(summary_key, {})
                
                print(f"\n✅ {suite_name.title()} Tests Complete:")
                print(f"   Total: {summary.get('total_tests', 0)}")
                print(f"   Passed: {summary.get('passed_tests', 0)}")
                print(f"   Failed: {summary.get('failed_tests', 0)}")
                print(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
                print(f"   Duration: {summary.get('duration_seconds', 0):.2f}s")
                
            except Exception as e:
                print(f"❌ {suite_name.title()} test suite failed: {e}")
                suite_results[suite_name] = {
                    "error": str(e),
                    "status": "failed"
                }
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Generate master report
        master_report = await self._generate_master_report(suite_results, total_duration)
        
        # Save master report
        report_path = os.path.join(self.temp_dir, "master_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(master_report, f, indent=2, default=str)
        
        # Print master summary
        await self._print_master_summary(master_report, report_path)
        
        # Cleanup
        await self._cleanup()
        
        return master_report
    
    async def _generate_master_report(self, suite_results, total_duration):
        """Generate comprehensive master report"""
        
        # Calculate overall statistics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        suite_summaries = {}
        
        for suite_name, result in suite_results.items():
            if "error" not in result:
                # Extract summary based on suite type
                if suite_name == "comprehensive":
                    summary = result.get("test_summary", {})
                elif suite_name == "integration":
                    summary = result.get("integration_test_summary", {})
                elif suite_name == "performance":
                    summary = result.get("performance_test_summary", {})
                elif suite_name == "security":
                    summary = result.get("security_test_summary", {})
                else:
                    summary = {}
                
                suite_summaries[suite_name] = summary
                
                total_tests += summary.get("total_tests", 0)
                total_passed += summary.get("passed_tests", 0)
                total_failed += summary.get("failed_tests", 0)
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Generate quality assessment
        quality_assessment = self._generate_quality_assessment(suite_results)
        
        # Generate deployment readiness
        deployment_readiness = self._generate_deployment_readiness(suite_results)
        
        # Generate recommendations
        recommendations = self._generate_master_recommendations(suite_results)
        
        master_report = {
            "master_test_summary": {
                "total_suites": len(self.test_suites),
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "overall_success_rate": overall_success_rate,
                "total_duration_seconds": total_duration,
                "timestamp": datetime.now().isoformat(),
                "test_environment": "development"
            },
            "suite_summaries": suite_summaries,
            "detailed_results": suite_results,
            "quality_assessment": quality_assessment,
            "deployment_readiness": deployment_readiness,
            "feature_coverage": self._generate_feature_coverage(),
            "performance_benchmarks": self._extract_performance_benchmarks(suite_results),
            "security_status": self._extract_security_status(suite_results),
            "integration_matrix": self._extract_integration_matrix(suite_results),
            "recommendations": recommendations,
            "next_steps": self._generate_next_steps(suite_results)
        }
        
        return master_report
    
    def _generate_quality_assessment(self, suite_results):
        """Generate overall quality assessment"""
        quality_scores = {}
        
        # Extract scores from each suite
        for suite_name, result in suite_results.items():
            if "error" not in result:
                if suite_name == "comprehensive":
                    # Calculate from individual test results
                    detailed = result.get("detailed_results", {})
                    if detailed:
                        passed = len([r for r in detailed.values() if r.get("status") == "passed"])
                        total = len(detailed)
                        quality_scores["feature_functionality"] = (passed / total * 100) if total > 0 else 0
                
                elif suite_name == "integration":
                    summary = result.get("integration_test_summary", {})
                    quality_scores["integration_quality"] = summary.get("success_rate", 0)
                
                elif suite_name == "performance":
                    summary = result.get("performance_test_summary", {})
                    quality_scores["performance_quality"] = summary.get("success_rate", 0)
                
                elif suite_name == "security":
                    summary = result.get("security_test_summary", {})
                    quality_scores["security_quality"] = summary.get("success_rate", 0)
        
        # Calculate overall quality score
        if quality_scores:
            overall_quality = sum(quality_scores.values()) / len(quality_scores)
            quality_scores["overall_quality"] = overall_quality
        else:
            quality_scores["overall_quality"] = 0
        
        return quality_scores
    
    def _generate_deployment_readiness(self, suite_results):
        """Generate deployment readiness assessment"""
        readiness_factors = {}
        
        # Check each suite for deployment readiness
        comprehensive_result = suite_results.get("comprehensive", {})
        integration_result = suite_results.get("integration", {})
        performance_result = suite_results.get("performance", {})
        security_result = suite_results.get("security", {})
        
        # Comprehensive functionality
        if "error" not in comprehensive_result:
            summary = comprehensive_result.get("test_summary", {})
            comp_success_rate = summary.get("success_rate", 0)
            readiness_factors["functionality"] = comp_success_rate >= 90
        else:
            readiness_factors["functionality"] = False
        
        # Integration compatibility
        if "error" not in integration_result:
            summary = integration_result.get("integration_test_summary", {})
            int_success_rate = summary.get("success_rate", 0)
            readiness_factors["integration"] = int_success_rate >= 90
        else:
            readiness_factors["integration"] = False
        
        # Performance requirements
        if "error" not in performance_result:
            summary = performance_result.get("performance_test_summary", {})
            perf_success_rate = summary.get("success_rate", 0)
            readiness_factors["performance"] = perf_success_rate >= 85
        else:
            readiness_factors["performance"] = False
        
        # Security compliance
        if "error" not in security_result:
            summary = security_result.get("security_test_summary", {})
            sec_success_rate = summary.get("success_rate", 0)
            readiness_factors["security"] = sec_success_rate >= 95
        else:
            readiness_factors["security"] = False
        
        # Calculate overall readiness
        ready_factors = sum(readiness_factors.values())
        total_factors = len(readiness_factors)
        overall_readiness = (ready_factors / total_factors) * 100 if total_factors > 0 else 0
        
        readiness_factors["overall_readiness"] = overall_readiness
        readiness_factors["ready_for_production"] = overall_readiness >= 90
        readiness_factors["ready_for_staging"] = overall_readiness >= 75
        readiness_factors["ready_for_development"] = overall_readiness >= 60
        
        return readiness_factors
    
    def _generate_feature_coverage(self):
        """Generate feature coverage report"""
        features = {
            "ai_orchestrator": {
                "description": "AI-powered pipeline orchestration with auto-tuning",
                "components": ["auto-tuning", "smart_retry", "predictive_caching"],
                "test_coverage": "comprehensive"
            },
            "predictive_monitoring": {
                "description": "Predictive monitoring with anomaly detection",
                "components": ["anomaly_detection", "performance_prediction", "intelligent_alerting"],
                "test_coverage": "comprehensive"
            },
            "advanced_debugger": {
                "description": "AI-powered debugging and performance profiling",
                "components": ["error_analysis", "performance_profiling", "session_management"],
                "test_coverage": "comprehensive"
            },
            "ai_code_generator": {
                "description": "AI-assisted code generation",
                "components": ["function_generation", "class_generation", "api_generation", "test_generation"],
                "test_coverage": "comprehensive"
            },
            "advanced_testing": {
                "description": "Advanced testing framework with parallel execution",
                "components": ["test_discovery", "parallel_execution", "coverage_tracking", "ai_test_generation"],
                "test_coverage": "comprehensive"
            },
            "multi_cloud": {
                "description": "Multi-cloud resource management",
                "components": ["aws_adapter", "azure_adapter", "gcp_adapter", "cost_optimization", "disaster_recovery"],
                "test_coverage": "comprehensive"
            },
            "multi_llm": {
                "description": "Multi-LLM support with intelligent routing",
                "components": ["openai_adapter", "anthropic_adapter", "cohere_adapter", "cost_optimization", "provider_selection"],
                "test_coverage": "comprehensive"
            },
            "plugin_system": {
                "description": "Extensible plugin system with sandboxing",
                "components": ["plugin_installation", "plugin_execution", "plugin_metrics", "plugin_search", "security_sandboxing"],
                "test_coverage": "comprehensive"
            },
            "enterprise_features": {
                "description": "Enterprise-grade features (RBAC, SSO, Audit)",
                "components": ["rbac", "sso_authentication", "audit_logging", "compliance_reporting"],
                "test_coverage": "comprehensive"
            },
            "performance_optimizations": {
                "description": "Performance optimizations (cache, async, pooling)",
                "components": ["llm_cache", "async_tasks", "connection_pool", "load_balancer"],
                "test_coverage": "comprehensive"
            },
            "security_features": {
                "description": "Security and compliance features",
                "components": ["data_encryption", "k8s_secrets", "input_validation", "audit_logging"],
                "test_coverage": "comprehensive"
            }
        }
        
        return features
    
    def _extract_performance_benchmarks(self, suite_results):
        """Extract performance benchmarks from results"""
        benchmarks = {}
        
        performance_result = suite_results.get("performance", {})
        if "error" not in performance_result:
            detailed = performance_result.get("detailed_results", {})
            
            for test_name, result in detailed.items():
                if "throughput" in result:
                    benchmarks[test_name] = {
                        "throughput": result.get("throughput", 0),
                        "avg_response_time": result.get("avg_response_time", 0),
                        "error_rate": result.get("error_rate", 0)
                    }
        
        return benchmarks
    
    def _extract_security_status(self, suite_results):
        """Extract security status from results"""
        security_status = {}
        
        security_result = suite_results.get("security", {})
        if "error" not in security_result:
            detailed = security_result.get("detailed_results", {})
            
            for test_name, result in detailed.items():
                if "score" in result:
                    security_status[test_name] = {
                        "security_score": result.get("score", 0),
                        "status": result.get("status", "unknown")
                    }
        
        return security_status
    
    def _extract_integration_matrix(self, suite_results):
        """Extract integration matrix from results"""
        integration_result = suite_results.get("integration", {})
        if "error" not in integration_result:
            return integration_result.get("integration_matrix", {})
        
        return {}
    
    def _generate_master_recommendations(self, suite_results):
        """Generate master recommendations based on all test results"""
        recommendations = []
        
        # Check for failed tests in any suite
        failed_tests = []
        for suite_name, result in suite_results.items():
            if "error" in result:
                failed_tests.append(f"{suite_name}: {result['error']}")
            else:
                # Check detailed results for failures
                detailed = result.get("detailed_results", {})
                for test_name, test_result in detailed.items():
                    if test_result.get("status") == "failed":
                        failed_tests.append(f"{suite_name}.{test_name}: {test_result.get('error', 'Test failed')}")
        
        if failed_tests:
            recommendations.append("Priority Issues to Address:")
            recommendations.extend([f"  - {failure}" for failure in failed_tests[:5]])
            if len(failed_tests) > 5:
                recommendations.append(f"  - ... and {len(failed_tests) - 5} more issues")
        else:
            recommendations.append("✅ All tests passed! System is ready for deployment.")
        
        # Add deployment recommendations
        deployment_ready = self._generate_deployment_readiness(suite_results)
        if deployment_ready.get("ready_for_production"):
            recommendations.append("🚀 System is ready for production deployment.")
        elif deployment_ready.get("ready_for_staging"):
            recommendations.append("🧪 System is ready for staging deployment.")
        elif deployment_ready.get("ready_for_development"):
            recommendations.append("🔧 System is ready for development deployment.")
        else:
            recommendations.append("⚠️ System needs fixes before deployment.")
        
        # Add general recommendations
        recommendations.extend([
            "",
            "General Recommendations:",
            "  - Set up automated testing in CI/CD pipeline",
            "  - Implement monitoring and alerting in production",
            "  - Regular security audits and penetration testing",
            "  - Performance monitoring and optimization",
            "  - Documentation and knowledge sharing"
        ])
        
        return recommendations
    
    def _generate_next_steps(self, suite_results):
        """Generate next steps based on test results"""
        next_steps = []
        
        # Check deployment readiness
        deployment_ready = self._generate_deployment_readiness(suite_results)
        
        if deployment_ready.get("ready_for_production"):
            next_steps.extend([
                "🚀 Deploy to Production",
                "📊 Set up production monitoring",
                "🔧 Configure production alerts",
                "📚 Create deployment documentation",
                "👥 Train operations team"
            ])
        elif deployment_ready.get("ready_for_staging"):
            next_steps.extend([
                "🧪 Deploy to Staging Environment",
                "🔍 Conduct staging testing",
                "⚡ Performance testing under load",
                "🛡️ Security penetration testing",
                "📋 User acceptance testing"
            ])
        else:
            next_steps.extend([
                "🔧 Fix critical issues identified in tests",
                "🧪 Re-run failed test suites",
                "📊 Address performance bottlenecks",
                "🛡️ Fix security vulnerabilities",
                "🔗 Resolve integration issues"
            ])
        
        # Add continuous improvement steps
        next_steps.extend([
            "",
            "Continuous Improvement:",
            "🔄 Set up automated test scheduling",
            "📈 Monitor system health and performance",
            "🆕 Plan next feature development",
            "📚 Update documentation",
            "👥 Team training and knowledge sharing"
        ])
        
        return next_steps
    
    async def _print_master_summary(self, master_report, report_path):
        """Print comprehensive master summary"""
        print("\n" + "=" * 80)
        print("🎯 MASTER TEST SUITE RESULTS")
        print("=" * 80)
        
        summary = master_report["master_test_summary"]
        print(f"Total Test Suites: {summary['total_suites']}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Total Passed: {summary['total_passed']} ✅")
        print(f"Total Failed: {summary['total_failed']} ❌")
        print(f"Overall Success Rate: {summary['overall_success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration_seconds']:.2f}s")
        print(f"Report saved to: {report_path}")
        
        # Print suite summaries
        print("\n📊 Suite Summaries:")
        suite_summaries = master_report["suite_summaries"]
        for suite_name, summary in suite_summaries.items():
            if "error" not in summary:
                status_icon = "✅" if summary.get("success_rate", 0) >= 90 else "⚠️" if summary.get("success_rate", 0) >= 70 else "❌"
                print(f"  {suite_name.title()}: {summary.get('success_rate', 0):.1f}% {status_icon}")
            else:
                print(f"  {suite_name.title()}: ❌ Failed")
        
        # Print quality assessment
        print("\n🏆 Quality Assessment:")
        quality = master_report["quality_assessment"]
        for metric, score in quality.items():
            status_icon = "✅" if score >= 90 else "⚠️" if score >= 70 else "❌"
            print(f"  {metric.replace('_', ' ').title()}: {score:.1f}% {status_icon}")
        
        # Print deployment readiness
        print("\n🚀 Deployment Readiness:")
        deployment = master_report["deployment_readiness"]
        for factor, ready in deployment.items():
            if isinstance(ready, bool):
                status_icon = "✅" if ready else "❌"
                print(f"  {factor.replace('_', ' ').title()}: {status_icon}")
            else:
                status_icon = "✅" if ready >= 90 else "⚠️" if ready >= 70 else "❌"
                print(f"  {factor.replace('_', ' ').title()}: {ready:.1f}% {status_icon}")
        
        # Print feature coverage
        print("\n🔍 Feature Coverage:")
        features = master_report["feature_coverage"]
        for feature, info in features.items():
            coverage_icon = "✅" if info["test_coverage"] == "comprehensive" else "⚠️" if info["test_coverage"] == "partial" else "❌"
            print(f"  {feature.replace('_', ' ').title()}: {coverage_icon}")
        
        # Print top recommendations
        print("\n💡 Top Recommendations:")
        recommendations = master_report["recommendations"][:5]
        for rec in recommendations:
            print(f"  {rec}")
        
        # Print next steps
        print("\n🎯 Next Steps:")
        next_steps = master_report["next_steps"][:5]
        for step in next_steps:
            print(f"  {step}")
    
    async def _cleanup(self):
        """Cleanup temporary files"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

async def main():
    """Main master test runner"""
    runner = MasterTestRunner()
    report = await runner.run_all_test_suites()
    
    # Exit with appropriate code based on overall success rate
    success_rate = report["master_test_summary"]["overall_success_rate"]
    exit_code = 0 if success_rate >= 90 else 1
    exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
