"""
ControlPlane.ai — Business Proposal PDF Generator
Generates a professional, color-illustrated PDF business proposal.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Polygon, Group,
    Circle
)
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ─────────────────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────────────────
C_BG_DARK      = colors.HexColor("#0D1117")
C_BG_CARD      = colors.HexColor("#161B22")
C_ACCENT_BLUE  = colors.HexColor("#3B82F6")
C_ACCENT_CYAN  = colors.HexColor("#06B6D4")
C_ACCENT_GREEN = colors.HexColor("#10B981")
C_ACCENT_AMBER = colors.HexColor("#F59E0B")
C_ACCENT_RED   = colors.HexColor("#EF4444")
C_ACCENT_PURPLE= colors.HexColor("#8B5CF6")
C_TEXT_PRIMARY = colors.HexColor("#F0F6FC")
C_TEXT_MUTED   = colors.HexColor("#8B949E")
C_BORDER       = colors.HexColor("#30363D")
C_HEADER_BG    = colors.HexColor("#1C2333")
C_WHITE        = colors.white
C_ALLOW        = colors.HexColor("#10B981")
C_REPAIR       = colors.HexColor("#F59E0B")
C_ESCALATE     = colors.HexColor("#8B5CF6")
C_BLOCK        = colors.HexColor("#EF4444")

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm

# ─────────────────────────────────────────────────────────
# CUSTOM FLOWABLES
# ─────────────────────────────────────────────────────────

class ColoredRect(Flowable):
    def __init__(self, width, height, fill_color, text="", text_color=colors.white,
                 radius=6, font_size=10, bold=False):
        self.width = width
        self.height = height
        self.fill_color = fill_color
        self.text = text
        self.text_color = text_color
        self.radius = radius
        self.font_size = font_size
        self.bold = bold

    def draw(self):
        c = self.canv
        c.setFillColor(self.fill_color)
        c.roundRect(0, 0, self.width, self.height, self.radius, fill=1, stroke=0)
        if self.text:
            c.setFillColor(self.text_color)
            font = "Helvetica-Bold" if self.bold else "Helvetica"
            c.setFont(font, self.font_size)
            c.drawCentredString(self.width / 2, self.height / 2 - self.font_size / 3, self.text)


class PipelineFlowchart(Flowable):
    """The 6-phase evaluation pipeline diagram."""
    def __init__(self, width):
        self.width = width
        self.height = 260

    def draw(self):
        c = self.canv
        w = self.width

        # Background
        c.setFillColor(C_BG_CARD)
        c.roundRect(0, 0, w, self.height, 8, fill=1, stroke=0)

        # Title
        c.setFillColor(C_ACCENT_CYAN)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w / 2, self.height - 20, "THE 6-PHASE EVALUATION PIPELINE")

        # Helper: draw a box with arrow
        def box(x, y, bw, bh, color, label, sublabel="", text_color=colors.white):
            c.setFillColor(color)
            c.roundRect(x, y, bw, bh, 5, fill=1, stroke=0)
            c.setFillColor(text_color)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(x + bw / 2, y + bh / 2 + 4, label)
            if sublabel:
                c.setFont("Helvetica", 6.5)
                c.setFillColor(colors.HexColor("#CBD5E1"))
                c.drawCentredString(x + bw / 2, y + bh / 2 - 7, sublabel)

        def arrow_down(x, y, length=18, color=C_TEXT_MUTED):
            c.setStrokeColor(color)
            c.setLineWidth(1.5)
            c.line(x, y, x, y - length + 5)
            c.setFillColor(color)
            c.setStrokeColor(color)
            p = c.beginPath()
            p.moveTo(x - 4, y - length + 7)
            p.lineTo(x + 4, y - length + 7)
            p.lineTo(x, y - length)
            p.close()
            c.drawPath(p, fill=1, stroke=0)

        def arrow_right(x, y, length=30, color=C_TEXT_MUTED):
            c.setStrokeColor(color)
            c.setLineWidth(1.5)
            c.line(x, y, x + length - 5, y)
            c.setFillColor(color)
            p = c.beginPath()
            p.moveTo(x + length - 7, y - 4)
            p.lineTo(x + length - 7, y + 4)
            p.lineTo(x + length, y)
            p.close()
            c.drawPath(p, fill=1, stroke=0)

        # Layout — center column for main flow
        cx = w / 2
        bw, bh = 130, 32

        # === REQUEST BOX ===
        box(cx - bw/2, self.height - 52, bw, bh,
            colors.HexColor("#1E3A5F"), "AI RESPONSE RECEIVED", "{ request, response, context, telemetry }")

        arrow_down(cx, self.height - 52, 22, C_ACCENT_BLUE)

        # === PHASE 1 ===
        box(cx - bw/2, self.height - 102, bw, bh,
            C_ACCENT_BLUE, "PHASE 1: FAST SCREEN", "< 50ms  •  Zero API calls  •  Deterministic")

        # Branch: LOW and HIGH
        # Low arrow left
        y_branch = self.height - 102
        c.setStrokeColor(C_ACCENT_GREEN)
        c.setLineWidth(1.5)
        c.line(cx - bw/2, y_branch + bh/2, cx - bw/2 - 20, y_branch + bh/2)
        c.line(cx - bw/2 - 20, y_branch + bh/2, cx - bw/2 - 20, y_branch - 10)
        # "LOW RISK" label
        c.setFillColor(C_ACCENT_GREEN)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(cx - bw/2 - 20, y_branch + bh/2 + 5, "LOW")
        # ALLOW box left
        allow_x = cx - bw/2 - 55
        box(allow_x, y_branch - 40, 50, 26, C_ALLOW, "ALLOW", "Fast path")

        # High risk arrow — continues down
        c.setFillColor(C_ACCENT_AMBER)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(cx + bw/2 + 4, y_branch + bh/2 - 3, "RISKY")
        arrow_down(cx, self.height - 102, 22, C_ACCENT_AMBER)

        # === PHASE 2 parallel ===
        p2y = self.height - 148
        p2bw, p2bh = 80, 44
        gap = 8
        total_p2w = 3 * p2bw + 2 * gap
        p2x_start = cx - total_p2w / 2

        c.setFillColor(C_TEXT_MUTED)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(cx, p2y + p2bh + 4, "PHASE 2: DEEP EVALUATION (parallel)")

        box(p2x_start, p2y, p2bw, p2bh,
            colors.HexColor("#1E40AF"), "PERFORMANCE\nENGINE", "Hallucination\nContradiction")
        box(p2x_start + p2bw + gap, p2y, p2bw, p2bh,
            colors.HexColor("#92400E"), "COST\nENGINE", "Agent loops\nToken usage")
        box(p2x_start + 2*(p2bw + gap), p2y, p2bw, p2bh,
            colors.HexColor("#6D28D9"), "RESPONSIBILITY\nENGINE", "PII • Safety\nPolicy rules")

        # Converge arrow down from center of 3 boxes
        for xi in [p2x_start + p2bw/2, p2x_start + p2bw + gap + p2bw/2, p2x_start + 2*(p2bw+gap) + p2bw/2]:
            c.setStrokeColor(C_TEXT_MUTED)
            c.setLineWidth(1)
            c.line(xi, p2y, cx, p2y - 16)

        arrow_down(cx, p2y - 14, 8, C_ACCENT_CYAN)

        # === PHASE 3 ===
        p3y = p2y - 52
        box(cx - bw/2, p3y, bw, bh, C_ACCENT_CYAN, "PHASE 3: RISK ENGINE", "Weighted scoring + context multipliers")
        arrow_down(cx, p3y, 22, C_ACCENT_CYAN)

        # === PHASE 4 ===
        p4y = p3y - 54
        box(cx - bw/2, p4y, bw, bh, colors.HexColor("#BE185D"), "PHASE 4: ACTION ENGINE", "ALLOW / REPAIR / ESCALATE / BLOCK")

        # Four outcome boxes
        out_y = p4y - 38
        out_bw, out_bh = 58, 22
        outcomes = [
            (C_ALLOW, "ALLOW"),
            (C_REPAIR, "REPAIR"),
            (C_ESCALATE, "ESCALATE"),
            (C_BLOCK, "BLOCK"),
        ]
        out_total = 4 * out_bw + 3 * 5
        out_x = cx - out_total / 2
        for i, (col, label) in enumerate(outcomes):
            ox = out_x + i * (out_bw + 5)
            c.setStrokeColor(col)
            c.setLineWidth(1)
            c.line(cx, p4y, ox + out_bw/2, out_y + out_bh)
            box(ox, out_y, out_bw, out_bh, col, label)

        # Phase 5/6 label at bottom
        c.setFillColor(C_TEXT_MUTED)
        c.setFont("Helvetica", 7)
        c.drawCentredString(cx, 14, "PHASE 5: Persist to PostgreSQL  •  PHASE 6: WebSocket broadcast to dashboard")


class FailureModesFlowchart(Flowable):
    """The 4 failure modes."""
    def __init__(self, width):
        self.width = width
        self.height = 210

    def draw(self):
        c = self.canv
        w = self.width

        c.setFillColor(C_BG_CARD)
        c.roundRect(0, 0, w, self.height, 8, fill=1, stroke=0)

        c.setFillColor(C_ACCENT_RED)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w / 2, self.height - 20, "THE 4 AI FAILURE MODES")

        modes = [
            (C_ACCENT_RED,    "① HALLUCINATION",     "AI invents facts with confidence",     "Trust erosion • Support escalations • Legal liability"),
            (C_ACCENT_AMBER,  "② PII LEAKAGE",       "AI exposes sensitive personal data",   "GDPR/DPDP fines • Regulatory investigations"),
            (C_ACCENT_PURPLE, "③ COST ANOMALY",      "Agent loops burn compute silently",     "Unexpected infrastructure costs • SLA violations"),
            (C_BLOCK,         "④ POLICY VIOLATION",  "AI gives unqualified dangerous advice", "Regulatory sanctions • Fiduciary liability"),
        ]

        bw = (w - 30) / 2
        bh = 68
        gap = 8
        for i, (col, title, desc, impact) in enumerate(modes):
            row = i // 2
            col_idx = i % 2
            bx = 10 + col_idx * (bw + gap)
            by = self.height - 50 - row * (bh + gap)

            c.setFillColor(colors.HexColor("#1A1F2E"))
            c.roundRect(bx, by, bw, bh, 5, fill=1, stroke=0)

            # Left accent bar
            c.setFillColor(col)
            c.rect(bx, by, 4, bh, fill=1, stroke=0)

            c.setFillColor(col)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(bx + 10, by + bh - 16, title)

            c.setFillColor(C_TEXT_PRIMARY)
            c.setFont("Helvetica", 7.5)
            c.drawString(bx + 10, by + bh - 30, desc)

            c.setFillColor(C_TEXT_MUTED)
            c.setFont("Helvetica", 6.5)
            c.drawString(bx + 10, by + bh - 44, "Impact:")
            c.setFillColor(col)
            # Wrap impact text
            words = impact.split(" • ")
            for j, word in enumerate(words[:2]):
                c.setFillColor(C_TEXT_MUTED)
                c.drawString(bx + 10, by + bh - 54 - j * 10, f"• {word}")


class CompetitiveMatrix(Flowable):
    """Visual competitive landscape."""
    def __init__(self, width):
        self.width = width
        self.height = 180

    def draw(self):
        c = self.canv
        w = self.width

        c.setFillColor(C_BG_CARD)
        c.roundRect(0, 0, w, self.height, 8, fill=1, stroke=0)

        c.setFillColor(C_ACCENT_BLUE)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w / 2, self.height - 20, "COMPETITIVE LANDSCAPE")

        # Axis labels
        mid_x, mid_y = w / 2, self.height / 2 - 10
        axis_len_x = w / 2 - 30
        axis_len_y = self.height / 2 - 30

        c.setStrokeColor(C_BORDER)
        c.setLineWidth(1)
        c.line(mid_x - axis_len_x, mid_y, mid_x + axis_len_x, mid_y)
        c.line(mid_x, mid_y - axis_len_y, mid_x, mid_y + axis_len_y)

        # Axis labels
        c.setFillColor(C_TEXT_MUTED)
        c.setFont("Helvetica", 7)
        c.drawCentredString(mid_x, mid_y + axis_len_y + 5, "PROACTIVE (Inline)")
        c.drawCentredString(mid_x, mid_y - axis_len_y - 10, "REACTIVE (Post-hoc)")
        c.drawString(mid_x + axis_len_x - 10, mid_y + 5, "Specific")
        c.drawString(mid_x - axis_len_x, mid_y + 5, "Generic")

        # Competitors
        competitors = [
            (-0.4, 0.35,  C_TEXT_MUTED,   "Observability\nTools"),
            (-0.6, -0.30, C_TEXT_MUTED,   "LLM Provider\nGuardrails"),
            (0.2,  -0.45, C_TEXT_MUTED,   "Prompt\nTools"),
        ]
        for rx, ry, col, label in competitors:
            px = mid_x + rx * axis_len_x
            py = mid_y + ry * axis_len_y
            c.setFillColor(col)
            c.circle(px, py, 5, fill=1, stroke=0)
            c.setFont("Helvetica", 6.5)
            c.drawCentredString(px, py - 14, label)

        # US — ControlPlane
        px = mid_x + 0.65 * axis_len_x
        py = mid_y + 0.60 * axis_len_y
        c.setFillColor(C_ACCENT_CYAN)
        c.circle(px, py, 10, fill=1, stroke=0)
        c.setFillColor(C_BG_DARK)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawCentredString(px, py - 2, "CP.ai")
        c.setFillColor(C_ACCENT_CYAN)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(px, py - 18, "ControlPlane")

        # Legend
        c.setFillColor(C_ACCENT_CYAN)
        c.circle(20, 20, 5, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(28, 17, "ControlPlane.ai — INLINE + CONTEXTUAL (unique positioning)")


class RoadmapChart(Flowable):
    """5-phase roadmap timeline."""
    def __init__(self, width):
        self.width = width
        self.height = 150

    def draw(self):
        c = self.canv
        w = self.width

        c.setFillColor(C_BG_CARD)
        c.roundRect(0, 0, w, self.height, 8, fill=1, stroke=0)

        c.setFillColor(C_ACCENT_BLUE)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w / 2, self.height - 20, "5-PHASE PRODUCT ROADMAP")

        phases = [
            ("Phase 1\n2026 H2", "Foundation\n& PMF", C_ACCENT_GREEN),
            ("Phase 2\n2027 H1", "Scale &\nGTM", C_ACCENT_CYAN),
            ("Phase 3\n2027 H2", "Enterprise\nReady", C_ACCENT_BLUE),
            ("Phase 4\n2028 H1", "Platform\nEcosystem", C_ACCENT_PURPLE),
            ("Phase 5\n2028 H2", "Market\nLeadership", C_ACCENT_AMBER),
        ]

        n = len(phases)
        bw = (w - 30) / n - 5
        bh = 80
        by = 20

        for i, (period, label, col) in enumerate(phases):
            bx = 12 + i * (bw + 6)

            # Height grows with phase (maturity)
            h = bh * (0.5 + i * 0.12)
            actual_by = by + (bh - h)

            c.setFillColor(col)
            c.setFillColorAlpha = 0.8
            c.roundRect(bx, actual_by, bw, h, 4, fill=1, stroke=0)

            # Arrow between phases
            if i < n - 1:
                ax = bx + bw + 3
                ay = actual_by + h / 2
                c.setFillColor(C_TEXT_MUTED)
                c.setStrokeColor(C_TEXT_MUTED)
                c.setLineWidth(1)
                c.line(ax, ay, ax + 3, ay)

            c.setFillColor(C_BG_DARK)
            c.setFont("Helvetica-Bold", 7)
            lines = period.split("\n")
            c.drawCentredString(bx + bw / 2, actual_by + h - 13, lines[0])
            if len(lines) > 1:
                c.setFont("Helvetica", 6)
                c.drawCentredString(bx + bw / 2, actual_by + h - 23, lines[1])

            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 7.5)
            label_lines = label.split("\n")
            for j, ll in enumerate(label_lines):
                c.drawCentredString(bx + bw / 2, actual_by + 16 + (len(label_lines) - 1 - j) * 11, ll)


class ARRProjection(Flowable):
    """ARR growth chart."""
    def __init__(self, width):
        self.width = width
        self.height = 150

    def draw(self):
        c = self.canv
        w = self.width

        c.setFillColor(C_BG_CARD)
        c.roundRect(0, 0, w, self.height, 8, fill=1, stroke=0)

        c.setFillColor(C_ACCENT_GREEN)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w / 2, self.height - 20, "5-YEAR ARR PROJECTION")

        years = ["Y1\n$660K", "Y2\n$3.3M", "Y3\n$9.6M", "Y4\n$21M", "Y5\n$48M"]
        values = [660, 3300, 9600, 21000, 48000]
        max_v = 48000

        n = len(years)
        bw = (w - 40) / n - 8
        chart_h = 95
        by = 18

        for i, (label, val) in enumerate(zip(years, values)):
            bx = 18 + i * (bw + 8)
            h = chart_h * (val / max_v)

            # Gradient-ish effect with lighter version
            alpha = 0.4 + 0.6 * (val / max_v)
            col = colors.HexColor(f"#{'%02x' % int(16 + 200*(val/max_v)):s}{'%02x' % int(100 + 80*(val/max_v)):s}FF"
                                  ) if False else C_ACCENT_GREEN

            # Bar
            c.setFillColor(colors.HexColor(f"#10{'%02x' % int(80 + 100*(val/max_v)):s}{'%02x' % int(50 + 80*(val/max_v)):s}"))
            c.roundRect(bx, by, bw, h, 3, fill=1, stroke=0)

            # Value label
            c.setFillColor(C_ACCENT_GREEN)
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(bx + bw / 2, by + h + 3, label.split("\n")[1])

            # Year label
            c.setFillColor(C_TEXT_MUTED)
            c.setFont("Helvetica", 7)
            c.drawCentredString(bx + bw / 2, 6, label.split("\n")[0])


class ROIBox(Flowable):
    """ROI calculation visual."""
    def __init__(self, width):
        self.width = width
        self.height = 120

    def draw(self):
        c = self.canv
        w = self.width

        c.setFillColor(C_BG_CARD)
        c.roundRect(0, 0, w, self.height, 8, fill=1, stroke=0)

        # Title
        c.setFillColor(C_ACCENT_AMBER)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w / 2, self.height - 20, "ROI ANALYSIS — Mid-Size Enterprise")

        items = [
            ("Annual Risk Exposure (without ControlPlane)", "$550K – $3.2M", C_ACCENT_RED),
            ("ControlPlane Enterprise Cost", "$72K / year", C_ACCENT_CYAN),
            ("Return on Investment", "7× – 44×", C_ACCENT_GREEN),
        ]

        bw = (w - 30) / len(items) - 5
        for i, (label, value, col) in enumerate(items):
            bx = 10 + i * (bw + 5)
            by = 15

            c.setFillColor(colors.HexColor("#1A1F2E"))
            c.roundRect(bx, by, bw, 75, 5, fill=1, stroke=0)

            c.setFillColor(col)
            c.rect(bx, by + 70, bw, 5, fill=1, stroke=0)

            c.setFillColor(col)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(bx + bw / 2, by + 38, value)

            c.setFillColor(C_TEXT_MUTED)
            c.setFont("Helvetica", 6.5)
            # Wrap label
            words = label.split()
            line1 = " ".join(words[:4])
            line2 = " ".join(words[4:])
            c.drawCentredString(bx + bw / 2, by + 22, line1)
            if line2:
                c.drawCentredString(bx + bw / 2, by + 12, line2)


# ─────────────────────────────────────────────────────────
# PAGE TEMPLATE (dark background)
# ─────────────────────────────────────────────────────────

class DarkCanvas:
    def __init__(self, filename):
        self.filename = filename

    def beforePage(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(C_BG_DARK)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        canvas.restoreState()

    def afterPage(self, canvas, doc):
        canvas.saveState()
        # Footer
        canvas.setFillColor(C_TEXT_MUTED)
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(PAGE_W / 2, 10 * mm, f"ControlPlane.ai — Business Proposal — Confidential  |  Page {doc.page}")
        # Top line accent
        canvas.setFillColor(C_ACCENT_BLUE)
        canvas.rect(0, PAGE_H - 3, PAGE_W, 3, fill=1, stroke=0)
        canvas.restoreState()


# ─────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────

def make_styles():
    s = getSampleStyleSheet()

    title_cover = ParagraphStyle("TitleCover",
        fontSize=38, fontName="Helvetica-Bold",
        textColor=C_WHITE, alignment=TA_CENTER,
        spaceAfter=6)

    subtitle_cover = ParagraphStyle("SubtitleCover",
        fontSize=16, fontName="Helvetica",
        textColor=C_ACCENT_CYAN, alignment=TA_CENTER,
        spaceAfter=4)

    section_h = ParagraphStyle("SectionH",
        fontSize=16, fontName="Helvetica-Bold",
        textColor=C_ACCENT_CYAN,
        spaceBefore=14, spaceAfter=8,
        borderPad=(0, 0, 0, 8))

    subsection_h = ParagraphStyle("SubsectionH",
        fontSize=11, fontName="Helvetica-Bold",
        textColor=C_ACCENT_BLUE,
        spaceBefore=10, spaceAfter=5)

    body = ParagraphStyle("Body",
        fontSize=9, fontName="Helvetica",
        textColor=C_TEXT_PRIMARY,
        leading=15, spaceAfter=6,
        alignment=TA_JUSTIFY)

    body_muted = ParagraphStyle("BodyMuted",
        fontSize=8.5, fontName="Helvetica",
        textColor=C_TEXT_MUTED,
        leading=14, spaceAfter=4)

    bullet = ParagraphStyle("Bullet",
        fontSize=9, fontName="Helvetica",
        textColor=C_TEXT_PRIMARY,
        leading=14, spaceAfter=3,
        leftIndent=14, bulletIndent=0)

    callout = ParagraphStyle("Callout",
        fontSize=9.5, fontName="Helvetica-Bold",
        textColor=C_ACCENT_AMBER,
        leading=15, spaceAfter=4,
        alignment=TA_CENTER)

    return dict(
        title_cover=title_cover,
        subtitle_cover=subtitle_cover,
        section_h=section_h,
        subsection_h=subsection_h,
        body=body,
        body_muted=body_muted,
        bullet=bullet,
        callout=callout,
    )


# ─────────────────────────────────────────────────────────
# HELPER — coloured table
# ─────────────────────────────────────────────────────────

def make_table(data, col_widths=None, header_color=C_HEADER_BG):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR",  (0, 0), (-1, 0), C_ACCENT_CYAN),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), C_BG_CARD),
        ("TEXTCOLOR",  (0, 1), (-1, -1), C_TEXT_PRIMARY),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_BG_CARD, colors.HexColor("#1C2333")]),
        ("GRID",       (0, 0), (-1, -1), 0.5, C_BORDER),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]
    t.setStyle(TableStyle(style))
    return t


def highlight_cell(t, row, col, color):
    t._tblStyle.add("BACKGROUND", (col, row), (col, row), color)
    t._tblStyle.add("TEXTCOLOR", (col, row), (col, row), C_BG_DARK)
    t._tblStyle.add("FONTNAME", (col, row), (col, row), "Helvetica-Bold")


def colored_para(text, color, style, prefix=""):
    return Paragraph(f'<font color="{color.hexval() if hasattr(color,"hexval") else "#3B82F6"}">{prefix}{text}</font>', style)


# ─────────────────────────────────────────────────────────
# BUILD PDF
# ─────────────────────────────────────────────────────────

def build_pdf(output_path):
    dc = DarkCanvas(output_path)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 10,
    )

    S = make_styles()
    story = []
    usable_w = PAGE_W - 2 * MARGIN

    def H1(text):
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width=usable_w, thickness=1, color=C_ACCENT_BLUE, spaceAfter=6))
        story.append(Paragraph(text, S["section_h"]))

    def H2(text):
        story.append(Paragraph(text, S["subsection_h"]))

    def P(text):
        story.append(Paragraph(text, S["body"]))

    def PM(text):
        story.append(Paragraph(text, S["body_muted"]))

    def B(text):
        story.append(Paragraph(f"• &nbsp; {text}", S["bullet"]))

    def SP(h=8):
        story.append(Spacer(1, h))

    # ── COVER PAGE ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 30 * mm))

    # Logo-style top bar
    cover_bar = Table([["  ControlPlane.ai"]], colWidths=[usable_w])
    cover_bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_ACCENT_BLUE),
        ("TEXTCOLOR",  (0, 0), (-1, -1), C_WHITE),
        ("FONTNAME",   (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 13),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(cover_bar)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Business Proposal", S["title_cover"]))
    story.append(Paragraph("Real-Time AI Governance & Compliance Infrastructure", S["subtitle_cover"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "Stop Bad AI Responses Before They Reach Your Users",
        ParagraphStyle("TagCover", fontSize=13, fontName="Helvetica",
                       textColor=C_TEXT_MUTED, alignment=TA_CENTER)))

    story.append(Spacer(1, 18 * mm))

    # Cover stats cards
    stats = [
        ("$4.3B", "Total Addressable Market", C_ACCENT_BLUE),
        ("7×–44×", "Customer ROI", C_ACCENT_GREEN),
        ("< 50ms", "Fast-path Latency", C_ACCENT_CYAN),
        ("300+", "Demo Scenarios", C_ACCENT_AMBER),
    ]
    stat_data = [[Paragraph(
        f'<font color="{c.hexval() if hasattr(c,"hexval") else "#3B82F6"}" size="18"><b>{v}</b></font><br/>'
        f'<font color="#8B949E" size="7">{l}</font>', ParagraphStyle("Stat", alignment=TA_CENTER, leading=20))
        for v, l, c in stats]]

    stat_t = Table(stat_data, colWidths=[usable_w / 4] * 4)
    stat_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_BG_CARD),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    story.append(stat_t)

    story.append(Spacer(1, 20 * mm))
    story.append(Paragraph("Prepared for: Strategic Investors & Enterprise Partners", S["body_muted"]))
    story.append(Paragraph("Version: 1.0  |  Date: August 2026  |  Confidential", S["body_muted"]))
    story.append(PageBreak())

    # ── EXECUTIVE SUMMARY ───────────────────────────────────────────────────
    H1("Executive Summary")
    P(
        "Artificial intelligence is being embedded into the most consequential operations of modern "
        "enterprises — customer support, financial advice, medical triage, and HR decisions. But AI systems "
        "<b>hallucinate</b>. They <b>leak sensitive data</b>. They make unqualified recommendations with "
        "dangerous confidence. And they do it silently, at scale, every second of every day."
    )
    SP()
    P(
        "Existing monitoring solutions catch these failures <b>after the fact</b> — in logs, in dashboards, "
        "in post-mortems. By then, the damage is done: a GDPR fine has been issued, a customer has acted "
        "on wrong financial advice, a hallucinated refund has created a support escalation crisis."
    )
    SP()

    callout_t = Table([[Paragraph(
        '<font color="#06B6D4"><b>ControlPlane.ai is the first real-time AI governance layer '
        'designed to sit inline between an AI system and its users</b></font> — evaluating every '
        'response before it is shown, repairing it automatically when possible, and escalating to a '
        'human reviewer when the stakes are too high.',
        S["body"])]],
        colWidths=[usable_w])
    callout_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0E3057")),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LINEAFTER", (0, 0), (0, -1), 3, C_ACCENT_CYAN),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    story.append(callout_t)

    # ── FAILURE MODES ────────────────────────────────────────────────────────
    H1("1. The Problem — AI Failure Modes")
    P(
        "AI deployment is outpacing governance. Every enterprise deploying conversational AI faces four "
        "distinct, recurring failure modes that cause measurable business harm:"
    )
    SP(6)
    story.append(FailureModesFlowchart(usable_w))
    SP(8)

    # Before/after table
    H2("1.1  Why Current Solutions Fail")
    before_after = [
        ["Existing Approach", "What it Does", "Why it Fails"],
        ["LLM Provider Guardrails", "Filters during training/inference", "No business-context; can't check live data"],
        ["Logging & Observability", "Records what happened", "Reactive — harm already occurred"],
        ["Prompt Engineering", "Instructions in the system prompt", "Easily bypassed; no audit trail"],
        ["Manual QA / Red-teaming", "Periodic human review of sample output", "Doesn't scale to millions of real interactions"],
        ["LLM Evals Frameworks", "Batch evaluation pipelines", "Offline only — can't prevent bad responses"],
    ]
    story.append(make_table(before_after,
                            col_widths=[usable_w * 0.28, usable_w * 0.30, usable_w * 0.42]))

    # ── SOLUTION ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    H1("2. The Solution — ControlPlane.ai")
    P(
        "ControlPlane is an <b>API proxy</b> — a single POST endpoint that sits between any AI system "
        "and its users. It requires <b>zero changes</b> to the upstream AI model and zero changes to the "
        "downstream application UI."
    )
    SP(6)
    story.append(PipelineFlowchart(usable_w))
    SP(10)

    H2("2.1  Five Core Value Propositions")
    props = [
        ("① INTERCEPT — Not monitor", C_ACCENT_RED,
         "The only solution that stops bad responses BEFORE they reach users. Every other tool is a rear-view mirror. We are the windshield."),
        ("② REPAIR — Not just alert", C_ACCENT_AMBER,
         "When a response is risky, ControlPlane automatically repairs it: redacts PII, corrects contradictions, or replaces with a safe fallback."),
        ("③ CONTEXTUAL — Not generic", C_ACCENT_BLUE,
         "Risk decisions use full business context: use-case, business impact level, country regulations, trusted data."),
        ("④ AUDITABLE — Built for compliance", C_ACCENT_GREEN,
         "Every evaluation produces a complete, immutable audit trail ready for GDPR/DPDP regulatory submissions."),
        ("⑤ PROVIDER-AGNOSTIC — Works with any LLM", C_ACCENT_PURPLE,
         "OpenAI, Gemini, Anthropic, Mistral, open-source models — customers aren't locked into a provider choice."),
    ]
    for title, col, desc in props:
        prop_t = Table([[
            Paragraph(f'<font color="{col.hexval() if hasattr(col,"hexval") else "#3B82F6"}"><b>{title}</b></font>', S["body"]),
            Paragraph(desc, S["body"])
        ]], colWidths=[usable_w * 0.32, usable_w * 0.68])
        prop_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1A1F2E")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ]))
        story.append(prop_t)
        story.append(Spacer(1, 3))

    # ── COMPETITIVE LANDSCAPE ────────────────────────────────────────────────
    story.append(PageBreak())
    H1("3. Competitive Landscape")
    story.append(CompetitiveMatrix(usable_w))
    SP(8)

    H2("3.1  Feature Comparison")
    cap_data = [
        ["Capability", "ControlPlane", "LLM Guardrails", "Observability", "Prompt Tools"],
        ["Inline interception (before user)", "✅", "⚠ Partial", "❌", "❌"],
        ["Context-aware (trusted data)", "✅", "❌", "❌", "❌"],
        ["Automatic repair", "✅", "❌", "❌", "❌"],
        ["PII detection & redaction", "✅", "⚠ Basic", "❌", "❌"],
        ["Cost / agent loop detection", "✅", "❌", "⚠ Logs only", "❌"],
        ["Human review escalation", "✅", "❌", "❌", "❌"],
        ["Full audit trail", "✅", "❌", "✅", "❌"],
        ["Provider-agnostic", "✅", "❌", "✅", "✅"],
        ["Custom policy rules", "✅", "❌", "❌", "⚠ Limited"],
    ]
    cap_t = make_table(cap_data,
                       col_widths=[usable_w*0.36, usable_w*0.16, usable_w*0.16, usable_w*0.16, usable_w*0.16])
    # Highlight ControlPlane column green
    extra = [("TEXTCOLOR", (1, row), (1, row), C_ACCENT_GREEN) for row in range(1, len(cap_data))]
    extra += [("FONTNAME", (1, row), (1, row), "Helvetica-Bold") for row in range(1, len(cap_data))]
    cap_t.setStyle(TableStyle(extra))
    story.append(cap_t)

    # ── TARGET MARKET ─────────────────────────────────────────────────────────
    H1("4. Target Market & Segments")
    H2("4.1  Total Addressable Market")
    tam_data = [
        ["Segment", "TAM (2026)", "SAM (3-yr Target)", "CAGR"],
        ["AI Observability & Monitoring", "$2.1B", "$400M", "45%"],
        ["Enterprise AI Governance", "$1.4B", "$250M", "52%"],
        ["AI Safety Tooling", "$0.8B", "$150M", "60%"],
        ["Combined Total", "$4.3B", "$800M", "~45%"],
    ]
    tam_t = make_table(tam_data, col_widths=[usable_w*0.42, usable_w*0.20, usable_w*0.22, usable_w*0.16])
    tam_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#0E3057")),
        ("TEXTCOLOR",  (0, 4), (-1, 4), C_ACCENT_CYAN),
        ("FONTNAME",   (0, 4), (-1, 4), "Helvetica-Bold"),
    ]))
    story.append(tam_t)
    SP(8)

    H2("4.2  Priority Verticals")
    vert_data = [
        ["Vertical", "Key AI Use Cases", "Regulatory Driver", "Priority"],
        ["BFSI (Banking, Financial)", "Customer support, loan advisory, fraud", "RBI/SEBI, GDPR, EU AI Act", "🔴 Tier 1"],
        ["Healthcare", "Patient triage, symptom guidance", "HIPAA, EU AI Act High-Risk", "🔴 Tier 1"],
        ["E-Commerce / D2C", "Order support, refund status", "DPDP, GDPR, Consumer Law", "🟠 Tier 2"],
        ["HR Tech", "Candidate screening, HR policy Q&A", "EU AI Act, GDPR", "🟠 Tier 2"],
        ["LegalTech / InsurTech", "Contract summarization, claims", "Bar rules, Financial regulation", "🟡 Tier 3"],
    ]
    story.append(make_table(vert_data, col_widths=[usable_w*0.24, usable_w*0.30, usable_w*0.27, usable_w*0.19]))

    # ── BUSINESS MODEL ────────────────────────────────────────────────────────
    story.append(PageBreak())
    H1("5. Business Model & Pricing")

    pricing = [
        ["", "Developer (Free)", "Growth", "Enterprise"],
        ["Monthly Price", "$0", "$499/month", "Custom / $5K+"],
        ["Evaluations", "10,000 / month", "500,000 / month", "Unlimited"],
        ["LLM-as-Judge", "❌", "✅", "✅"],
        ["Custom Policy Rules", "❌", "✅", "✅"],
        ["Private Deployment", "❌", "❌", "✅"],
        ["Compliance Modules", "❌", "❌", "✅ (GDPR, DPDP, EU AI Act)"],
        ["SLA", "Best effort", "99.9% uptime", "99.99% + < 100ms P95"],
        ["Support", "Community", "Email < 24h", "Dedicated CSM"],
        ["Audit Export", "❌", "✅ Basic", "✅ Regulatory-grade"],
    ]
    p_t = make_table(pricing, col_widths=[usable_w*0.28, usable_w*0.22, usable_w*0.22, usable_w*0.28])
    # Highlight Enterprise column
    ent_extra = [("BACKGROUND", (3, row), (3, row), colors.HexColor("#0E1A2E")) for row in range(1, len(pricing))]
    ent_extra += [("TEXTCOLOR", (3, row), (3, row), C_ACCENT_CYAN) for row in range(1, len(pricing))]
    p_t.setStyle(TableStyle(ent_extra))
    story.append(p_t)

    SP(8)
    H2("5.1  Unit Economics (Year 2 Targets)")
    econ = [
        ["Metric", "Growth Plan", "Enterprise Plan"],
        ["Average Contract Value (ACV)", "$6,000/yr", "$72,000/yr"],
        ["Customer Acquisition Cost (CAC)", "$800", "$2,500"],
        ["Payback Period", "~2 months", "~5 months"],
        ["Gross Margin", "80%", "78%"],
        ["Net Revenue Retention (NRR)", "115%", "130%"],
    ]
    story.append(make_table(econ, col_widths=[usable_w*0.45, usable_w*0.27, usable_w*0.28]))

    # ── BUSINESS CASE ─────────────────────────────────────────────────────────
    story.append(PageBreak())
    H1("6. Business Case & Financial Impact")
    story.append(ROIBox(usable_w))
    SP(10)

    H2("6.1  Quantified Risk Exposure (Mid-Size Enterprise, 100K AI Interactions/Month)")
    risk_rows = [
        ["Failure Mode", "Incidents/Year", "Estimated Annual Cost", "Mitigation"],
        ["PII Breach via AI Response", "2–3", "$500K – $3M", "GDPR/DPDP fines + legal + churn"],
        ["Hallucination → Escalation (1% rate)", "12,000 wrong responses", "$18K – $54K", "300 unnecessary human contacts/month"],
        ["Agent Loop Cost Overrun (0.5%)", "500 loops/month", "$7K – $100K", "Undetected until billing shock"],
        ["Policy Violation (financial advice)", "1 incident", "$200K – $1M+", "Regulatory sanctions, fiduciary liability"],
        ["TOTAL ANNUAL EXPOSURE", "—", "$550K – $3.2M", "Conservative estimate"],
    ]
    risk_t = make_table(risk_rows,
                        col_widths=[usable_w*0.24, usable_w*0.20, usable_w*0.22, usable_w*0.34])
    risk_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#3B0000")),
        ("TEXTCOLOR",  (0, 5), (-1, 5), C_ACCENT_RED),
        ("FONTNAME",   (0, 5), (-1, 5), "Helvetica-Bold"),
    ]))
    story.append(risk_t)

    SP(10)
    H2("6.2  5-Year ARR Projection")
    story.append(ARRProjection(usable_w))
    SP(8)

    arr_data = [
        ["Year", "Growth Customers", "Enterprise Customers", "ARR", "Key Driver"],
        ["Year 1", "50", "5", "$660K", "Design partners, PMF"],
        ["Year 2", "200", "25", "$3.3M", "GTM scaling, SDKs"],
        ["Year 3", "500", "80", "$9.6M", "EU AI Act enforcement"],
        ["Year 4", "1,000", "200", "$21M", "Platform ecosystem"],
        ["Year 5", "2,000", "500", "$48M", "Market leadership"],
    ]
    story.append(make_table(arr_data,
                            col_widths=[usable_w*0.12, usable_w*0.20, usable_w*0.22, usable_w*0.14, usable_w*0.32]))

    # ── ROADMAP ──────────────────────────────────────────────────────────────
    story.append(PageBreak())
    H1("7. Phased Product Roadmap")
    story.append(RoadmapChart(usable_w))
    SP(10)

    roadmap = [
        ["Phase", "Period", "Theme", "Key Milestones"],
        ["Phase 1", "2026 H2", "Foundation & PMF",
         "Core pipeline live • Multi-LLM support • Python + Node SDKs • 10 design partners • $50K ARR"],
        ["Phase 2", "2027 H1", "Scale & GTM",
         "Multi-tenant SaaS • DPDP module • GDPR export • Slack/Jira integration • Series A ($5-8M)"],
        ["Phase 3", "2027 H2", "Enterprise Ready",
         "Private cloud deployment • EU AI Act module • RBAC • SOC2 Type II • 5 Global 2000 customers"],
        ["Phase 4", "2028 H1", "Platform & Ecosystem",
         "Plugin marketplace • Policy-as-Code • OTel integration • 1,000+ active integrators"],
        ["Phase 5", "2028 H2", "Market Leadership",
         "$48M ARR • IPO readiness • EU regulatory certification • APAC & EMEA expansion"],
    ]
    rm_t = make_table(roadmap, col_widths=[usable_w*0.12, usable_w*0.13, usable_w*0.22, usable_w*0.53])
    colors_by_row = [None, C_ACCENT_GREEN, C_ACCENT_CYAN, C_ACCENT_BLUE, C_ACCENT_PURPLE, C_ACCENT_AMBER]
    rm_extra = []
    for row, col in enumerate(colors_by_row):
        if col:
            rm_extra.append(("TEXTCOLOR", (0, row), (1, row), col))
            rm_extra.append(("FONTNAME",  (0, row), (1, row), "Helvetica-Bold"))
    rm_t.setStyle(TableStyle(rm_extra))
    story.append(rm_t)

    # ── RISKS ────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    H1("8. Key Risks & Mitigations")

    risks = [
        ("⚡ Latency in critical path", "MEDIUM", "HIGH",
         "Fast path (<50ms) for low-risk traffic. Async evaluation mode. Self-hosted deployment option. Target: P95 < 150ms."),
        ("⚠ False Positives (over-blocking)", "MEDIUM", "HIGH",
         "Tunable thresholds per use-case. Human review queue for borderlines. A/B testing mode for first 30 days."),
        ("🏢 Enterprise security review", "HIGH", "HIGH",
         "Private VPC/on-prem deployment from Phase 3. SOC2 + ISO 27001 roadmap. Zero-retention mode available."),
        ("🤖 LLM providers build this natively", "MEDIUM", "HIGH",
         "Providers are conflicted — can't police their own outputs. Our contextual value (trusted data, policy) is irreplicable by providers."),
        ("🐢 Slow enterprise sales cycles", "HIGH", "MEDIUM",
         "Product-led growth: developer lands the tool before procurement. Regulatory urgency creates buying pressure."),
        ("📉 Recession reduces AI spend", "MEDIUM", "MEDIUM",
         "Compliance tools are last to be cut. Strong ROI story (7x–44x). Regulatory fines don't go away in recessions."),
    ]

    risk_head = [["Risk", "Probability", "Impact", "Mitigation Strategy"]]
    risk_rows2 = []
    for risk, prob, impact, mit in risks:
        prob_col = C_ACCENT_RED if prob == "HIGH" else C_ACCENT_AMBER if prob == "MEDIUM" else C_ACCENT_GREEN
        impact_col = C_ACCENT_RED if impact == "HIGH" else C_ACCENT_AMBER if impact == "MEDIUM" else C_ACCENT_GREEN
        risk_rows2.append([
            Paragraph(risk, S["body"]),
            Paragraph(f'<font color="{prob_col.hexval() if hasattr(prob_col,"hexval") else "#F59E0B"}"><b>{prob}</b></font>', S["body"]),
            Paragraph(f'<font color="{impact_col.hexval() if hasattr(impact_col,"hexval") else "#EF4444"}"><b>{impact}</b></font>', S["body"]),
            Paragraph(mit, S["body_muted"]),
        ])

    risk_t2 = Table(risk_head + risk_rows2,
                    colWidths=[usable_w*0.28, usable_w*0.14, usable_w*0.12, usable_w*0.46],
                    repeatRows=1)
    risk_t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_HEADER_BG),
        ("TEXTCOLOR",  (0, 0), (-1, 0), C_ACCENT_CYAN),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_BG_CARD, colors.HexColor("#1C2333")]),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(risk_t2)

    # ── ASK ──────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    H1("9. The Ask — Seed Round: $1.5M")

    use_data = [
        ["Category", "Allocation", "Amount", "Details"],
        ["Engineering & Product", "55%", "$825K",
         "3 senior engineers (18 months), AWS/GCP infra, SOC2 Type I audit"],
        ["Sales & Marketing", "25%", "$375K",
         "Head of Sales hire, conference presence, content marketing, developer relations"],
        ["Operations & Legal", "15%", "$225K",
         "Legal (contracts, DPAs, IP), compliance certifications, finance & HR"],
        ["Reserve", "5%", "$75K", "Contingency buffer"],
    ]
    use_t = make_table(use_data, col_widths=[usable_w*0.28, usable_w*0.14, usable_w*0.14, usable_w*0.44])
    story.append(use_t)

    SP(10)
    H2("9.1  Series A Milestones (18 months)")
    milestones = [
        "✅  $2M ARR — 20 Enterprise + 200 Growth customers",
        "✅  SOC2 Type II certification in progress",
        "✅  3 published enterprise case studies (BFSI, e-commerce, healthcare)",
        "✅  Python + Node.js SDKs — 5,000+ monthly active developers",
        "✅  1 strategic partnership signed (cloud marketplace or SI)",
        "✅  Series A raise: $6-8M at $25-30M valuation",
    ]
    for m in milestones:
        B(m)

    # ── CLOSING ──────────────────────────────────────────────────────────────
    SP(16)
    close_t = Table([[Paragraph(
        '<font color="#06B6D4"><b>The AI governance market is not a feature — it is mandatory infrastructure.</b></font><br/><br/>'
        '<font color="#F0F6FC">Every enterprise deploying AI in a regulated context will need a layer that sits between their AI '
        'system and their users, evaluating every response before it causes harm, repairing it when possible, '
        'and escalating when the stakes are too high.<br/><br/></font>'
        '<font color="#3B82F6"><b>ControlPlane.ai is that layer. We are live. We are production-tested. '
        'And we are the only solution that intercepts AI failures before they reach users.</b></font>',
        S["body"])]],
        colWidths=[usable_w])
    close_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0E1A30")),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LINEBEFORE", (0, 0), (0, -1), 4, C_ACCENT_CYAN),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    story.append(close_t)

    SP(12)
    story.append(Paragraph(
        "ControlPlane.ai  —  Detect AI risk before it becomes a business incident.",
        ParagraphStyle("Final", fontSize=10, fontName="Helvetica-Bold",
                       textColor=C_TEXT_MUTED, alignment=TA_CENTER)))

    # ── BUILD ────────────────────────────────────────────────────────────────
    doc.build(
        story,
        onFirstPage=lambda cv, d: (dc.beforePage(cv, d), dc.afterPage(cv, d)),
        onLaterPages=lambda cv, d: (dc.beforePage(cv, d), dc.afterPage(cv, d)),
    )
    print(f"[OK] PDF generated: {output_path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "docs", "ControlPlane_Business_Proposal.pdf")
    build_pdf(out)
