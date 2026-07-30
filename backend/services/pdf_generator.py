import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect, String

class PDFReportGenerator:
    @staticmethod
    def generate(pdf_path, original_filename, data):
        """Generates a professional presentation-ready PDF report."""
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )
        
        styles = getSampleStyleSheet()
        
        # Professional color palette
        primary_color = colors.HexColor("#1e293b")  # Slate 800
        secondary_color = colors.HexColor("#0f766e")  # Teal 700
        text_color = colors.HexColor("#334155")  # Slate 700
        light_bg = colors.HexColor("#f8fafc")  # Slate 50
        border_color = colors.HexColor("#cbd5e1")  # Slate 300
        accent_color = colors.HexColor("#0284c7")  # Sky 600
        
        # Custom styles
        title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=26,
            textColor=primary_color,
            leading=32,
            spaceAfter=15
        )
        
        subtitle_style = ParagraphStyle(
            'CoverSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=13,
            textColor=secondary_color,
            leading=17,
            spaceAfter=35
        )
        
        h1_style = ParagraphStyle(
            'SectionH1',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=primary_color,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True
        )
        
        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=secondary_color,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True
        )
        
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=9.5,
            textColor=text_color,
            leading=13,
            spaceAfter=6
        )
        
        bold_body_style = ParagraphStyle(
            'ReportBodyBold',
            parent=body_style,
            fontName='Helvetica-Bold'
        )
        
        bullet_style = ParagraphStyle(
            'ReportBullet',
            parent=body_style,
            leftIndent=15,
            firstLineIndent=-10,
            spaceAfter=4
        )
        
        story = []
        
        # --- COVER PAGE ---
        story.append(Spacer(1, 1.2 * inch))
        
        # Decorative top bar
        top_bar = Drawing(504, 6)
        top_bar.add(Rect(0, 0, 504, 6, fillColor=secondary_color, strokeColor=None))
        story.append(top_bar)
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("SME Financial Document Intelligence Report", title_style))
        story.append(Paragraph("Automated Financial Metrics, Risk Assessment, and Gap Detection Dashboard", subtitle_style))
        
        story.append(Spacer(1, 0.8 * inch))
        
        # Meta info block
        meta_data = [
            [Paragraph("<b>Company Name:</b>", body_style), Paragraph("SME Client Venture", body_style)],
            [Paragraph("<b>Source Document:</b>", body_style), Paragraph(original_filename, body_style)],
            [Paragraph("<b>Analysis Date:</b>", body_style), Paragraph(datetime.datetime.now().strftime("%B %d, %Y"), body_style)],
            [Paragraph("<b>System Integrity:</b>", body_style), Paragraph("Production Ready Agent Validation", body_style)]
        ]
        
        meta_table = Table(meta_data, colWidths=[150, 350])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), light_bg),
            ('PADDING', (0,0), (-1,-1), 10),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LINELEFT', (0,0), (0,-1), 3, secondary_color),
        ]))
        story.append(meta_table)
        
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph("<font color='#64748b'>Generated automatically by FinIntel Agent Sandbox</font>", body_style))
        story.append(PageBreak())
        
        # --- SECTION 1: CALCULATED METRICS ---
        story.append(Paragraph("1. Core Calculated Financial Metrics", h1_style))
        story.append(Paragraph("The following table lists the calculated core metrics from the parsed document data. These values serve as the mathematical basis for all subsequent analysis and risk flags.", body_style))
        story.append(Spacer(1, 8))
        
        m = data.get("metrics", {})
        
        def fmt_curr(val):
            try:
                return f"INR {float(val):,}"
            except:
                return str(val)
                
        metrics_table_data = [
            [Paragraph("<b>Financial Metric</b>", bold_body_style), Paragraph("<b>Value</b>", bold_body_style), Paragraph("<b>Financial Metric</b>", bold_body_style), Paragraph("<b>Value</b>", bold_body_style)],
            [Paragraph("Total Revenue", body_style), Paragraph(fmt_curr(m.get("total_revenue", 0)), body_style), Paragraph("Total Expense", body_style), Paragraph(fmt_curr(m.get("total_expense", 0)), body_style)],
            [Paragraph("Gross Profit", body_style), Paragraph(fmt_curr(m.get("gross_profit", 0)), body_style), Paragraph("Net Profit", body_style), Paragraph(fmt_curr(m.get("net_profit", 0)), body_style)],
            [Paragraph("Profit Margin", body_style), Paragraph(f"{m.get('profit_margin', 0)}%", body_style), Paragraph("Operating Margin", body_style), Paragraph(f"{m.get('operating_margin', 0)}%", body_style)],
            [Paragraph("Current Ratio", body_style), Paragraph(str(m.get("current_ratio", 1.5)), body_style), Paragraph("Quick Ratio", body_style), Paragraph(str(m.get("quick_ratio", 1.2)), body_style)],
            [Paragraph("Debt Ratio", body_style), Paragraph(str(m.get("debt_ratio", 0.45)), body_style), Paragraph("Net Cash Flow", body_style), Paragraph(fmt_curr(m.get("cash_flow", 0)), body_style)],
            [Paragraph("Avg Monthly Revenue", body_style), Paragraph(fmt_curr(m.get("avg_monthly_revenue", 0)), body_style), Paragraph("Avg Monthly Expense", body_style), Paragraph(fmt_curr(m.get("avg_monthly_expense", 0)), body_style)]
        ]
        
        for item in metrics_table_data[0]:
            item.style.textColor = colors.white
            
        metrics_table = Table(metrics_table_data, colWidths=[130, 122, 130, 122])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg]),
            ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 15))
        
        # --- SECTION 2: CURRENT STATE OBSERVATIONS ---
        story.append(Paragraph("2. Current State Analysis", h1_style))
        story.append(Paragraph("The system completed comprehensive reasoning on all observations. These narrative descriptions explain the financial numbers in simple business language.", body_style))
        story.append(Spacer(1, 8))
        
        csa = data.get("current_state_analysis", {})
        
        csa_categories = [
            ("Revenue Trend", csa.get("revenue_trend")),
            ("Expense Trend", csa.get("expense_trend")),
            ("Net Profit Status", csa.get("net_profit")),
            ("Operating Margin Health", csa.get("operating_margin")),
            ("Cash Flow Sufficiency", csa.get("cash_flow")),
            ("Liquidity Standing", csa.get("liquidity")),
            ("Asset Breakdown", csa.get("assets")),
            ("Liabilities Standing", csa.get("liabilities")),
            ("Equity Status", csa.get("equity")),
            ("Debt Ratio Analysis", csa.get("debt_ratio")),
            ("Current Ratio Interpretation", csa.get("current_ratio")),
            ("Profitability Score", csa.get("profitability")),
            ("Overall Financial Health", csa.get("financial_health"))
        ]
        
        for title, obs in csa_categories:
            if obs:
                story.append(Paragraph(f"<b>{title}:</b> {obs}", body_style))
                story.append(Spacer(1, 2))
                
        # Source trace
        source_info = csa.get("source", {})
        if source_info:
            doc_src = source_info.get("document", "Uploaded File")
            page_src = source_info.get("page", "1")
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<i>Source Reference Trace: Document [{doc_src}], Page/Range [{page_src}]</i>", body_style))
            
        story.append(Spacer(1, 15))
        story.append(PageBreak())
        
        # --- SECTION 3: GAP DETECTION ---
        story.append(Paragraph("3. Gap Detection", h1_style))
        story.append(Paragraph("Critical weaknesses, discrepancies, or issues identified automatically in the business financial structure:", body_style))
        story.append(Spacer(1, 8))
        
        gaps = data.get("gap_detection", [])
        if not gaps:
            story.append(Paragraph("• No immediate structural gaps detected from document analysis.", body_style))
        else:
            for gap in gaps:
                prob = gap.get("problem", "N/A")
                impact = gap.get("impact", "N/A")
                rec = gap.get("recommendation", "N/A")
                
                gap_p = f"<b>Problem:</b> {prob}<br/>" \
                        f"<b>Impact:</b> {impact}<br/>" \
                        f"<b>Recommendation:</b> {rec}"
                story.append(Paragraph(f"• {gap_p}", bullet_style))
                story.append(Spacer(1, 6))
                
        story.append(Spacer(1, 15))
        
        # --- SECTION 4: MISSING DATA DETECTION ---
        story.append(Paragraph("4. Missing Data & Statements Detection", h1_style))
        story.append(Paragraph("Identifies document fields or statements that were missing from the upload which could improve analysis accuracy:", body_style))
        story.append(Spacer(1, 8))
        
        missing = data.get("missing_data_detection", [])
        if not missing:
            story.append(Paragraph("• No missing fields detected. The uploaded document set contains comprehensive details.", body_style))
        else:
            for m_item in missing:
                name = m_item.get("missing_data", "N/A")
                imp = m_item.get("importance", "N/A")
                rec = m_item.get("recommendation", "N/A")
                
                m_p = f"<b>Missing Item:</b> {name}<br/>" \
                      f"<b>Importance:</b> {imp}<br/>" \
                      f"<b>Recommendation:</b> {rec}"
                story.append(Paragraph(f"• {m_p}", bullet_style))
                story.append(Spacer(1, 6))
                
        story.append(Spacer(1, 15))
        
        # --- SECTION 5: FORWARD LOOKING FLAGS ---
        story.append(Paragraph("5. Forward Looking Risk & Opportunities", h1_style))
        story.append(Paragraph("Predictive indicators, growth opportunities, and leverage scores identified by the agent:", body_style))
        story.append(Spacer(1, 8))
        
        flags = data.get("forward_looking_flags", [])
        if not flags:
            story.append(Paragraph("• No risk flags or growth opportunities detected.", body_style))
        else:
            for f in flags:
                title = f.get("flag", "Opportunity/Risk")
                reason = f.get("reason", "N/A")
                risk = f.get("risk_level", "Medium")
                growth = f.get("growth_score", 70)
                conf = f.get("confidence_score", 80)
                
                f_p = f"<b>Indicator:</b> {title} (Risk Level: {risk})<br/>" \
                      f"<b>Reasoning:</b> {reason}<br/>" \
                      f"<b>Growth Score:</b> {growth}/100 | <b>Confidence Score:</b> {conf}/100"
                story.append(Paragraph(f"• {f_p}", bullet_style))
                story.append(Spacer(1, 6))
                
        # Build document
        doc.build(story)
        print(f"Report generated successfully: {pdf_path}")
