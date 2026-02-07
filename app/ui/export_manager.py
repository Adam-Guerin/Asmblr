"""Export manager for multi-format result exports."""

from __future__ import annotations
import streamlit as st
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import zipfile
import io
from datetime import datetime
import base64


class ExportManager:
    """Manages multi-format exports of Asmblr results."""
    
    def __init__(self):
        self.supported_formats = ["json", "csv", "markdown", "pdf", "zip"]
    
    def export_results(self, results: Dict[str, Any], format_type: str, run_id: str) -> Optional[bytes]:
        """Export results in the specified format."""
        try:
            if format_type == "json":
                return self._export_json(results, run_id)
            elif format_type == "csv":
                return self._export_csv(results, run_id)
            elif format_type == "markdown":
                return self._export_markdown(results, run_id)
            elif format_type == "pdf":
                return self._export_pdf(results, run_id)
            elif format_type == "zip":
                return self._export_zip(results, run_id)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
        except Exception as e:
            st.error(f"Erreur lors de l'export {format_type}: {str(e)}")
            return None
    
    def _export_json(self, results: Dict[str, Any], run_id: str) -> bytes:
        """Export results as JSON."""
        export_data = {
            "run_id": run_id,
            "export_timestamp": datetime.now().isoformat(),
            "results": results
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False).encode('utf-8')
    
    def _export_csv(self, results: Dict[str, Any], run_id: str) -> bytes:
        """Export results as CSV."""
        csv_data = []
        
        # Extract ideas
        if "research" in results and "ideas" in results["research"]:
            for idea in results["research"]["ideas"]:
                csv_data.append({
                    "run_id": run_id,
                    "type": "idea",
                    "name": idea.get("name", ""),
                    "score": idea.get("score", 0),
                    "description": idea.get("one_liner", ""),
                    "target_user": idea.get("target_user", ""),
                    "problem": idea.get("problem", ""),
                    "solution": idea.get("solution", "")
                })
        
        # Extract pain points
        if "research" in results and "pain_statements" in results["research"]:
            for i, pain in enumerate(results["research"]["pain_statements"]):
                csv_data.append({
                    "run_id": run_id,
                    "type": "pain_point",
                    "name": f"Pain Point {i+1}",
                    "description": pain,
                    "score": "",
                    "target_user": "",
                    "problem": pain,
                    "solution": ""
                })
        
        # Extract metrics
        if "analysis" in results:
            analysis = results["analysis"]
            csv_data.append({
                "run_id": run_id,
                "type": "metric",
                "name": "Top Idea Score",
                "score": analysis.get("top_idea", {}).get("score", 0),
                "description": analysis.get("top_idea", {}).get("rationale", ""),
                "target_user": "",
                "problem": "",
                "solution": ""
            })
        
        df = pd.DataFrame(csv_data)
        return df.to_csv(index=False).encode('utf-8')
    
    def _export_markdown(self, results: Dict[str, Any], run_id: str) -> bytes:
        """Export results as Markdown."""
        md_content = f"""# 🚀 Asmblr Results Report
        
**Run ID:** {run_id}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 Executive Summary

"""
        
        # Add top idea
        if "analysis" in results and "top_idea" in results["analysis"]:
            top_idea = results["analysis"]["top_idea"]
            md_content += f"""### 🏆 Top Idea: {top_idea.get('name', 'N/A')}

**Score:** {top_idea.get('score', 'N/A')}  
**Rationale:** {top_idea.get('rationale', 'N/A')}

---

"""
        
        # Add research findings
        if "research" in results:
            research = results["research"]
            md_content += "## 🔍 Research Findings\n\n"
            
            if "pain_statements" in research:
                md_content += "### Pain Points Identified\n\n"
                for i, pain in enumerate(research["pain_statements"][:5], 1):
                    md_content += f"{i}. {pain}\n"
                md_content += "\n"
            
            if "ideas" in research:
                md_content += "### Generated Ideas\n\n"
                for idea in research["ideas"]:
                    md_content += f"""#### 💡 {idea.get('name', 'Unnamed Idea')}

- **One-liner:** {idea.get('one_liner', 'N/A')}
- **Target User:** {idea.get('target_user', 'N/A')}
- **Problem:** {idea.get('problem', 'N/A')}
- **Solution:** {idea.get('solution', 'N/A')}

"""
        
        # Add product requirements
        if "product" in results and "prd_markdown" in results["product"]:
            md_content += """## 📋 Product Requirements

"""
            md_content += results["product"]["prd_markdown"] + "\n\n"
        
        # Add technical specifications
        if "tech" in results and "tech_spec_markdown" in results["tech"]:
            md_content += """## 🛠️ Technical Specifications

"""
            md_content += results["tech"]["tech_spec_markdown"] + "\n\n"
        
        md_content += """---

*Generated by Asmblr - AI-Powered MVP Generator*"""
        
        return md_content.encode('utf-8')
    
    def _export_pdf(self, results: Dict[str, Any], run_id: str) -> bytes:
        """Export results as PDF (simplified version)."""
        # For now, we'll create a simple text-based PDF
        # In a real implementation, you'd use a library like reportlab or weasyprint
        md_content = self._export_markdown(results, run_id).decode('utf-8')
        
        # Convert markdown to simple text for PDF
        text_content = f"""Asmblr Results Report
========================

Run ID: {run_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{md_content.replace('#', '').replace('*', '').replace('`', '')}
"""
        
        return text_content.encode('utf-8')
    
    def _export_zip(self, results: Dict[str, Any], run_id: str) -> bytes:
        """Export results as a ZIP package."""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add JSON export
            json_data = self._export_json(results, run_id)
            zip_file.writestr(f"{run_id}_results.json", json_data)
            
            # Add CSV export
            csv_data = self._export_csv(results, run_id)
            zip_file.writestr(f"{run_id}_results.csv", csv_data)
            
            # Add Markdown export
            md_data = self._export_markdown(results, run_id)
            zip_file.writestr(f"{run_id}_report.md", md_data)
            
            # Add individual artifacts if available
            if "research" in results:
                research = results["research"]
                
                # Export ideas separately
                if "ideas" in research:
                    ideas_json = json.dumps(research["ideas"], indent=2, ensure_ascii=False)
                    zip_file.writestr(f"{run_id}_ideas.json", ideas_json.encode('utf-8'))
                
                # Export pain points
                if "pain_statements" in research:
                    pain_points = {"pain_points": research["pain_statements"]}
                    pain_json = json.dumps(pain_points, indent=2, ensure_ascii=False)
                    zip_file.writestr(f"{run_id}_pain_points.json", pain_json.encode('utf-8'))
            
            # Add README
            readme_content = f"""Asmblr Results Package
========================

This package contains all results from run {run_id}.

Files included:
- {run_id}_results.json - Complete results in JSON format
- {run_id}_results.csv - Tabular data in CSV format
- {run_id}_report.md - Human-readable report in Markdown format
- {run_id}_ideas.json - Generated ideas (if available)
- {run_id}_pain_points.json - Identified pain points (if available)

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Tool: Asmblr - AI-Powered MVP Generator
"""
            zip_file.writestr("README.txt", readme_content.encode('utf-8'))
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    def get_download_link(self, data: bytes, filename: str, format_type: str) -> str:
        """Generate a download link for the exported data."""
        b64 = base64.b64encode(data).decode()
        
        # Determine MIME type
        mime_types = {
            "json": "application/json",
            "csv": "text/csv",
            "markdown": "text/markdown",
            "pdf": "application/pdf",
            "zip": "application/zip"
        }
        mime_type = mime_types.get(format_type, "application/octet-stream")
        
        return f'<a href="data:{mime_type};base64,{b64}" download="{filename}">📥 Télécharger {format_type.upper()}</a>'
    
    def render_export_buttons(self, results: Dict[str, Any], run_id: str) -> None:
        """Render export buttons in the UI."""
        st.subheader("📤 Exporter les Résultats")
        
        # Create columns for different export formats
        cols = st.columns(len(self.supported_formats))
        
        for i, format_type in enumerate(self.supported_formats):
            with cols[i]:
                if st.button(f"📄 {format_type.upper()}", key=f"export_{format_type}"):
                    with st.spinner(f"Génération de l'export {format_type}..."):
                        data = self.export_results(results, format_type, run_id)
                        if data:
                            filename = f"{run_id}_results.{format_type}"
                            download_link = self.get_download_link(data, filename, format_type)
                            st.markdown(download_link, unsafe_allow_html=True)
                            st.success(f"✅ Export {format_type} prêt!")
        
        # Bulk export option
        st.markdown("---")
        st.subheader("📦 Export Complet")
        
        if st.button("📥 Télécharger Tout (ZIP)", key="export_all"):
            with st.spinner("Génération du package complet..."):
                data = self.export_results(results, "zip", run_id)
                if data:
                    filename = f"{run_id}_complete_package.zip"
                    download_link = self.get_download_link(data, filename, "zip")
                    st.markdown(download_link, unsafe_allow_html=True)
                    st.success("✅ Package complet prêt!")
    
    def render_export_preview(self, results: Dict[str, Any], format_type: str) -> None:
        """Render a preview of the export data."""
        if format_type == "json":
            st.json(results)
        elif format_type == "csv":
            # Create a preview DataFrame
            preview_data = []
            if "research" in results and "ideas" in results["research"]:
                for idea in results["research"]["ideas"][:3]:  # Show first 3 ideas
                    preview_data.append({
                        "Nom": idea.get("name", ""),
                        "Score": idea.get("score", 0),
                        "Description": idea.get("one_liner", "")
                    })
            
            if preview_data:
                df = pd.DataFrame(preview_data)
                st.dataframe(df)
            else:
                st.info("Aucune donnée à prévisualiser")
        
        elif format_type == "markdown":
            md_preview = self._export_markdown(results, "preview").decode('utf-8')
            st.markdown(md_preview[:1000] + "..." if len(md_preview) > 1000 else md_preview)


# Global export manager instance
_global_export_manager = ExportManager()


def get_export_manager() -> ExportManager:
    """Get the global export manager instance."""
    return _global_export_manager
