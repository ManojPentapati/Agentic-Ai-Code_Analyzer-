import re
from datetime import datetime
from fpdf import FPDF


class ReportPDF(FPDF):
    """Custom FPDF class with structured header, footer, and utility methods."""

    def header(self) -> None:
        """Draw header banner on every page."""
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "CODE ANALYZER - EXECUTIVE REPORT", border=0, align="L")
        # Right-aligned date with page/line transition
        self.cell(
            0,
            10,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            border=0,
            align="R",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.set_draw_color(200, 200, 200)
        self.line(15, 20, 195, 20)
        self.ln(5)

    def footer(self) -> None:
        """Draw footer page numbers."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        # Page X of Y (using alias_nb_pages() placeholder)
        page_str = f"Page {self.page_no()} of {{nb}}"
        self.cell(0, 10, page_str, border=0, align="C")


def generate_analysis_pdf(report_data: dict) -> bytes:
    """
    Generate a styled PDF report from analysis results.

    Args:
        report_data: The st.session_state.current_result structure.

    Returns:
        Raw PDF file bytes.
    """
    code = report_data.get("code", "")
    result = report_data.get("result", {})
    elapsed = report_data.get("elapsed", 0.0)
    model = report_data.get("model", "")

    lang = result.get("language", "unknown").upper()
    cpx = result.get("complexity_score", 0)
    atype = result.get("analysis_type", "quick").upper()
    report = result.get("final_report", "")

    # Parse scorecard & vulnerabilities
    scores = _extract_scores(report)
    health = int(sum(scores.values()) / len(scores)) if scores else 0

    # Initialize FPDF
    pdf = ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_margins(15, 25, 15)  # left, top, right
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # 1. Title Block
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(17, 17, 17)
    pdf.cell(0, 12, "Code Analysis & Quality Audit", border=0, align="L", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Target Model: {model}  |  Language: {lang}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # 2. Key Metrics Table
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Key Metrics", border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(40, 7, "Health Index", border=1, align="C", fill=True)
    pdf.cell(40, 7, "Complexity Score", border=1, align="C", fill=True)
    pdf.cell(40, 7, "Analysis Route", border=1, align="C", fill=True)
    pdf.cell(40, 7, "Analysis Duration", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(17, 17, 17)
    pdf.cell(40, 8, f"{health}%", border=1, align="C")
    pdf.cell(40, 8, f"{cpx}/100", border=1, align="C")
    pdf.cell(40, 8, atype, border=1, align="C")
    pdf.cell(40, 8, f"{elapsed:.2f}s", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # 3. Quality Scorecard Table
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Quality Scorecard", border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(90, 7, "Category", border=1, fill=True)
    pdf.cell(70, 7, "Rating", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    for cat, val in scores.items():
        pdf.cell(90, 7, f"  {cat}", border=1)
        # Render stars
        stars = "*" * (val // 20)
        pdf.cell(70, 7, f"  {stars} ({val}%)", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # 4. Detailed Analysis
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Detailed Analysis Report", border=0, new_x="LMARGIN", new_y="NEXT")
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    # Clean markdown formatting tags for basic PDF rendering
    clean_report = _clean_markdown(report)

    # Render report paragraph by paragraph
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)

    for line in clean_report.split("\n"):
        line = line.strip()
        if not line:
            pdf.ln(2)
            continue

        # Section headings
        if line.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(17, 17, 17)
            pdf.cell(0, 8, line[3:], border=0, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
        elif line.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 6, line[4:], border=0, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
        elif line.startswith("- ") or line.startswith("* "):
            pdf.multi_cell(0, 5, f"  {line}", border=0, new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.multi_cell(0, 5, line, border=0, new_x="LMARGIN", new_y="NEXT")

    # 5. Appendix: Original Source Code
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Appendix: Analyzed Source Code", border=0, new_x="LMARGIN", new_y="NEXT")
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Courier", "", 8)
    pdf.set_fill_color(248, 248, 248)

    # Render code block line by line to support pagination
    for line in code.split("\n"):
        # Strip trailing carriage returns
        line_str = line.rstrip("\r\n")
        # Simple tab replacement
        line_str = line_str.replace("\t", "    ")
        # Ensure we don't break the cell
        pdf.cell(0, 4, line_str, border=0, fill=True, new_x="LMARGIN", new_y="NEXT")

    return pdf.output()


def _extract_scores(report_text: str) -> dict:
    """Helper to parse scores from aggregator markdown output."""
    scores = {
        "Correctness": 80,
        "Security": 90,
        "Performance": 85,
        "Readability": 80,
        "Best Practices": 80,
    }
    if not report_text:
        return scores
    for cat, stars in re.findall(
        r"\|\s*([A-Za-z ]+)\s*\|\s*([*]+|⭐+)\s*\|", report_text
    ):
        c = cat.strip()
        if c in scores:
            # Count either * or ⭐
            scores[c] = len(stars) * 20
    return scores


def _clean_markdown(text: str) -> str:
    """Clean markdown styling like asterisks and HTML tags for PDF rendering."""
    # Remove bold/italic markers
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    # Remove code tick marks
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove emoji markers or unsupported unicode where possible
    text = text.replace("⭐", "*")
    return text
