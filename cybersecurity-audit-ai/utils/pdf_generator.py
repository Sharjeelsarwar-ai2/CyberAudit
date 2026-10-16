from fpdf import FPDF
import re
import io


class SecurityReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(0, 200, 150)
        self.cell(0, 10, "CyberAudit AI - Security Assessment Report", ln=True, align="C")
        self.set_draw_color(0, 200, 150)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Confidential", align="C")

    def add_section(self, title: str, content: str):
        self.add_page()
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(0, 200, 150)
        self.cell(0, 12, title, ln=True)
        self.ln(3)
        
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        
        cleaned = re.sub(r'[^\x00-\x7F]+', ' ', content)
        cleaned = cleaned.replace('**', '').replace('##', '').replace('###', '').replace('#', '')
        cleaned = cleaned.replace('`', '').replace('---', '────────────────')
        
        for line in cleaned.split('\n'):
            line = line.strip()
            if not line:
                self.ln(3)
                continue
            if line.startswith('|'):
                self.set_font("Courier", "", 8)
                self.multi_cell(0, 5, line)
                self.set_font("Helvetica", "", 10)
            elif line.startswith('- ') or line.startswith('* '):
                self.cell(5)
                self.multi_cell(0, 5, f"  {line}")
            elif line.isupper() or line.startswith('CRITICAL') or line.startswith('HIGH'):
                self.set_font("Helvetica", "B", 10)
                self.multi_cell(0, 5, line)
                self.set_font("Helvetica", "", 10)
            else:
                self.multi_cell(0, 5, line)


def generate_pdf(results: dict) -> bytes:
    pdf = SecurityReportPDF()
    pdf.alias_nb_pages()
    
    sections = [
        ("Executive Summary & Final Report", results.get("final_report", "")),
        ("Threat Model Analysis", results.get("threat_model", "")),
        ("Vulnerability Assessment", results.get("vuln_scan", "")),
        ("Compliance Evaluation", results.get("compliance", "")),
        ("Incident Response Plan", results.get("incident_response", ""))
    ]

    for title, content in sections:
        if content:
            pdf.add_section(title, content)

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.getvalue()