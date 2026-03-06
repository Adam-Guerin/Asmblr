"""Export manager for multi-format result exports with enhanced error handling."""

from __future__ import annotations
import streamlit as st
import json
import pandas as pd
from typing import Any, Dict, List, Optional, Union, Tuple
import zipfile
import io
from datetime import datetime
import base64
from dataclasses import dataclass

from app.core.error_formatter import format_runtime_error, format_file_error, ErrorSeverity


@dataclass
class ExportResult:
    """Result of an export operation"""
    success: bool
    data: Optional[bytes] = None
    filename: Optional[str] = None
    format_type: Optional[str] = None
    error_message: Optional[str] = None
    file_size: Optional[int] = None


class ExportManager:
    """Manages multi-format exports of Asmblr results with enhanced error handling."""
    
    def __init__(self) -> None:
        self.supported_formats: List[str] = ["json", "csv", "markdown", "pdf", "zip"]
        self.max_file_size: int = 50 * 1024 * 1024  # 50MB limit
        self.default_encoding: str = 'utf-8'
    
    def export_results(self, results: Dict[str, Any], format_type: str, run_id: str) -> ExportResult:
        """Export results in the specified format with comprehensive error handling."""
        try:
            # Validate inputs
            validation_result = self._validate_export_inputs(results, format_type, run_id)
            if not validation_result.success:
                return validation_result
            
            # Check format support
            if format_type not in self.supported_formats:
                return ExportResult(
                    success=False,
                    error_message=f"Unsupported format: {format_type}. Supported: {', '.join(self.supported_formats)}",
                    format_type=format_type
                )
            
            # Export based on format
            export_methods = {
                "json": self._export_json,
                "csv": self._export_csv,
                "markdown": self._export_markdown,
                "pdf": self._export_pdf,
                "zip": self._export_zip
            }
            
            export_method = export_methods[format_type]
            data = export_method(results, run_id)
            
            # Validate export data
            if not data:
                return ExportResult(
                    success=False,
                    error_message=f"No data generated for {format_type} export",
                    format_type=format_type
                )
            
            # Check file size
            if len(data) > self.max_file_size:
                return ExportResult(
                    success=False,
                    error_message=f"Export file too large: {len(data) / (1024*1024):.1f}MB (max: {self.max_file_size / (1024*1024):.1f}MB)",
                    format_type=format_type
                )
            
            filename = f"{run_id}_results.{format_type}"
            
            return ExportResult(
                success=True,
                data=data,
                filename=filename,
                format_type=format_type,
                file_size=len(data)
            )
            
        except Exception as e:
            error_msg = format_runtime_error(f"Failed to export {format_type}: {e}", ErrorSeverity.MEDIUM)
            st.error(error_msg)
            return ExportResult(
                success=False,
                error_message=str(e),
                format_type=format_type
            )
    
    def _validate_export_inputs(self, results: Dict[str, Any], format_type: str, run_id: str) -> ExportResult:
        """Validate export inputs."""
        if not isinstance(results, dict):
            return ExportResult(
                success=False,
                error_message="Results must be a dictionary"
            )
        
        if not format_type or not isinstance(format_type, str):
            return ExportResult(
                success=False,
                error_message="Format type must be a non-empty string"
            )
        
        if not run_id or not isinstance(run_id, str):
            return ExportResult(
                success=False,
                error_message="Run ID must be a non-empty string"
            )
        
        # Sanitize run ID for filename
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
        for char in invalid_chars:
            if char in run_id:
                return ExportResult(
                    success=False,
                    error_message=f"Run ID contains invalid character: {char}"
                )
        
        return ExportResult(success=True)
    
    def _export_json(self, results: Dict[str, Any], run_id: str) -> bytes:
        """Export results as JSON with validation."""
        try:
            export_data = {
                "run_id": run_id,
                "export_timestamp": datetime.now().isoformat(),
                "export_version": "1.0",
                "results": results
            }
            
            # Validate JSON serialization
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
            return json_str.encode(self.default_encoding)
            
        except Exception as e:
            raise ValueError(f"JSON export failed: {e}")
    
    def _export_csv(self, results: Dict[str, Any], run_id: str) -> bytes:
        """Export results as CSV with enhanced data extraction."""
        try:
            csv_data: List[Dict[str, Any]] = []
            
            # Extract ideas with validation
            if "research" in results and isinstance(results["research"], dict):
                research = results["research"]
                if "ideas" in research and isinstance(research["ideas"], list):
                    for idea in research["ideas"]:
                        if isinstance(idea, dict):
                            csv_data.append({
                                "run_id": run_id,
                                "type": "idea",
                                "name": str(idea.get("name", "")),
                                "score": float(idea.get("score", 0)),
                                "description": str(idea.get("one_liner", "")),
                                "target_user": str(idea.get("target_user", "")),
                                "problem": str(idea.get("problem", "")),
                                "solution": str(idea.get("solution", ""))
                            })
            
            # Extract pain points with validation
            if "research" in results and isinstance(results["research"], dict):
                research = results["research"]
                if "pain_statements" in research and isinstance(research["pain_statements"], list):
                    for i, pain in enumerate(research["pain_statements"]):
                        if isinstance(pain, str):
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
            
            # Extract metrics with validation
            if "analysis" in results and isinstance(results["analysis"], dict):
                analysis = results["analysis"]
                if "top_idea" in analysis and isinstance(analysis["top_idea"], dict):
                    top_idea = analysis["top_idea"]
                    csv_data.append({
                        "run_id": run_id,
                        "type": "metric",
                        "name": "Top Idea Score",
                        "score": float(top_idea.get("score", 0)),
                        "description": str(top_idea.get("rationale", "")),
                        "target_user": "",
                        "problem": "",
                        "solution": ""
                    })
            
            if not csv_data:
                # Create minimal CSV if no data
                csv_data = [{
                    "run_id": run_id,
                    "type": "info",
                    "name": "No Data",
                    "description": "No exportable data found",
                    "score": 0,
                    "target_user": "",
                    "problem": "",
                    "solution": ""
                }]
            
            df = pd.DataFrame(csv_data)
            return df.to_csv(index=False).encode(self.default_encoding)
            
        except Exception as e:
            raise ValueError(f"CSV export failed: {e}")
    
    def _export_markdown(self, results: Dict[str, Any], run_id: str) -> bytes:
        """Export results as Markdown with enhanced formatting."""
        try:
            md_content = f"""# 🚀 Asmblr Results Report
        
**Run ID:** {run_id}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Export Version:** 1.0

---

## 📊 Executive Summary

"""
            
            # Add top idea with validation
            if "analysis" in results and isinstance(results["analysis"], dict):
                analysis = results["analysis"]
                if "top_idea" in analysis and isinstance(analysis["top_idea"], dict):
                    top_idea = analysis["top_idea"]
                    md_content += f"""### 🏆 Top Idea: {top_idea.get('name', 'N/A')}

**Score:** {top_idea.get('score', 'N/A')}  
**Rationale:** {top_idea.get('rationale', 'N/A')}

---

"""
            
            # Add research findings with validation
            if "research" in results and isinstance(results["research"], dict):
                research = results["research"]
                md_content += "## 🔍 Research Findings\n\n"
                
                if "pain_statements" in research and isinstance(research["pain_statements"], list):
                    md_content += "### Pain Points Identified\n\n"
                    for i, pain in enumerate(research["pain_statements"][:5], 1):
                        if isinstance(pain, str):
                            md_content += f"{i}. {pain}\n"
                    md_content += "\n"
                
                if "ideas" in research and isinstance(research["ideas"], list):
                    md_content += "### Generated Ideas\n\n"
                    for idea in research["ideas"]:
                        if isinstance(idea, dict):
                            md_content += f"""#### 💡 {idea.get('name', 'Unnamed Idea')}

- **One-liner:** {idea.get('one_liner', 'N/A')}
- **Target User:** {idea.get('target_user', 'N/A')}
- **Problem:** {idea.get('problem', 'N/A')}
- **Solution:** {idea.get('solution', 'N/A')}

"""
            
            # Add product requirements with validation
            if "product" in results and isinstance(results["product"], dict):
                product = results["product"]
                if "prd_markdown" in product and isinstance(product["prd_markdown"], str):
                    md_content += """## 📋 Product Requirements

"""
                    md_content += product["prd_markdown"] + "\n\n"
            
            # Add technical specifications with validation
            if "tech" in results and isinstance(results["tech"], dict):
                tech = results["tech"]
                if "tech_spec_markdown" in tech and isinstance(tech["tech_spec_markdown"], str):
                    md_content += """## 🛠️ Technical Specifications

"""
                    md_content += tech["tech_spec_markdown"] + "\n\n"
            
            md_content += """---

*Generated by Asmblr - AI-Powered MVP Generator*"""
            
            return md_content.encode(self.default_encoding)
            
        except Exception as e:
            raise ValueError(f"Markdown export failed: {e}")
    
    def _export_pdf(self, results: Dict[str, Any], run_id: str) -> bytes:
        """Export results as PDF (simplified text-based version)."""
        try:
            # Get markdown content and convert to text
            md_content = self._export_markdown(results, run_id).decode(self.default_encoding)
            
            # Convert markdown to simple text for PDF
            text_content = f"""Asmblr Results Report
========================

Run ID: {run_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Export Version: 1.0

{md_content.replace('#', '').replace('*', '').replace('`', '').replace('**', '').replace('##', '').replace('###', '')}

---

*Generated by Asmblr - AI-Powered MVP Generator*
"""
            
            return text_content.encode(self.default_encoding)
            
        except Exception as e:
            raise ValueError(f"PDF export failed: {e}")
    
    def _export_zip(self, results: Dict[str, Any], run_id: str) -> bytes:
        """Export results as a ZIP package with enhanced error handling."""
        try:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add JSON export
                json_result = self._export_json(results, run_id)
                zip_file.writestr(f"{run_id}_results.json", json_result)
                
                # Add CSV export
                csv_result = self._export_csv(results, run_id)
                zip_file.writestr(f"{run_id}_results.csv", csv_result)
                
                # Add Markdown export
                md_result = self._export_markdown(results, run_id)
                zip_file.writestr(f"{run_id}_report.md", md_result)
                
                # Add individual artifacts if available
                if "research" in results and isinstance(results["research"], dict):
                    research = results["research"]
                    
                    # Export ideas separately
                    if "ideas" in research and isinstance(research["ideas"], list):
                        ideas_json = json.dumps(research["ideas"], indent=2, ensure_ascii=False, default=str)
                        zip_file.writestr(f"{run_id}_ideas.json", ideas_json.encode(self.default_encoding))
                    
                    # Export pain points
                    if "pain_statements" in research and isinstance(research["pain_statements"], list):
                        pain_points = {"pain_points": research["pain_statements"]}
                        pain_json = json.dumps(pain_points, indent=2, ensure_ascii=False, default=str)
                        zip_file.writestr(f"{run_id}_pain_points.json", pain_json.encode(self.default_encoding))
                
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
Export Version: 1.0
Tool: Asmblr - AI-Powered MVP Generator
"""
                zip_file.writestr("README.txt", readme_content.encode(self.default_encoding))
            
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
            
        except Exception as e:
            raise ValueError(f"ZIP export failed: {e}")
    
    def get_download_link(self, export_result: ExportResult) -> str:
        """Generate a download link for the exported data with validation."""
        if not export_result.success or not export_result.data or not export_result.filename:
            return "❌ Export failed - no download available"
        
        try:
            b64 = base64.b64encode(export_result.data).decode()
            
            # Determine MIME type
            mime_types = {
                "json": "application/json",
                "csv": "text/csv",
                "markdown": "text/markdown",
                "pdf": "application/pdf",
                "zip": "application/zip"
            }
            mime_type = mime_types.get(export_result.format_type, "application/octet-stream")
            
            # Add file size to display
            size_mb = export_result.file_size / (1024 * 1024) if export_result.file_size else 0
            size_text = f" ({size_mb:.1f}MB)" if size_mb > 0.1 else f" ({export_result.file_size}B)"
            
            return f'<a href="data:{mime_type};base64,{b64}" download="{export_result.filename}">📥 Télécharger {export_result.format_type.upper()}{size_text}</a>'
            
        except Exception as e:
            return f"❌ Failed to generate download link: {e}"
    
    def render_export_buttons(self, results: Dict[str, Any], run_id: str) -> None:
        """Render export buttons in the UI with enhanced error handling."""
        st.subheader("📤 Exporter les Résultats")
        
        # Validate inputs before rendering
        validation = self._validate_export_inputs(results, "json", run_id)  # Use json as representative
        if not validation.success:
            st.error(f"❌ Cannot export: {validation.error_message}")
            return
        
        # Create columns for different export formats
        cols = st.columns(len(self.supported_formats))
        
        for i, format_type in enumerate(self.supported_formats):
            with cols[i]:
                button_key = f"export_{format_type}"
                if st.button(f"📄 {format_type.upper()}", key=button_key):
                    with st.spinner(f"Génération de l'export {format_type}..."):
                        export_result = self.export_results(results, format_type, run_id)
                        
                        if export_result.success:
                            download_link = self.get_download_link(export_result)
                            st.markdown(download_link, unsafe_allow_html=True)
                            st.success(f"✅ Export {format_type} prêt!")
                        else:
                            st.error(f"❌ Export {format_type} failed: {export_result.error_message}")
        
        # Bulk export option
        st.markdown("---")
        st.subheader("📦 Export Complet")
        
        if st.button("📥 Télécharger Tout (ZIP)", key="export_all"):
            with st.spinner("Génération du package complet..."):
                export_result = self.export_results(results, "zip", run_id)
                
                if export_result.success:
                    download_link = self.get_download_link(export_result)
                    st.markdown(download_link, unsafe_allow_html=True)
                    st.success("✅ Package complet prêt!")
                else:
                    st.error(f"❌ ZIP export failed: {export_result.error_message}")
    
    def render_export_preview(self, results: Dict[str, Any], format_type: str) -> None:
        """Render a preview of the export data with validation."""
        try:
            if format_type == "json":
                st.json(results)
            
            elif format_type == "csv":
                # Create a preview DataFrame
                preview_data: List[Dict[str, Any]] = []
                if "research" in results and isinstance(results["research"], dict):
                    research = results["research"]
                    if "ideas" in research and isinstance(research["ideas"], list):
                        for idea in research["ideas"][:3]:  # Show first 3 ideas
                            if isinstance(idea, dict):
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
                md_preview = self._export_markdown(results, "preview").decode(self.default_encoding)
                preview_text = md_preview[:1000] + "..." if len(md_preview) > 1000 else md_preview
                st.markdown(preview_text)
            
            else:
                st.info(f"Preview not available for {format_type} format")
                
        except Exception as e:
            st.error(f"Failed to generate preview: {e}")
    
    def get_supported_formats_info(self) -> Dict[str, str]:
        """Get information about supported export formats."""
        return {
            "json": "Complete results in JSON format - Best for data processing",
            "csv": "Tabular data in CSV format - Best for spreadsheet analysis",
            "markdown": "Human-readable report in Markdown format - Best for documentation",
            "pdf": "Text-based PDF report - Best for sharing and printing",
            "zip": "Complete package with all formats - Best for archival"
        }


# Global export manager instance
_global_export_manager = ExportManager()


def get_export_manager() -> ExportManager:
    """Get the global export manager instance."""
    return _global_export_manager
