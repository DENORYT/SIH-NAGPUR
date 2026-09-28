from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os

pdf_path = r"C:\Users\gamin\Downloads\ShadowLink_Final_Report.pdf"

doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                        rightMargin=72, leftMargin=72,
                        topMargin=72, bottomMargin=18)
styles = getSampleStyleSheet()

# Create custom styles
title_style = ParagraphStyle(
    'TitleStyle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=colors.HexColor("#1a365d"),
    spaceAfter=20,
    alignment=1 # Center
)
heading_style = ParagraphStyle(
    'HeadingStyle',
    parent=styles['Heading2'],
    fontSize=16,
    textColor=colors.HexColor("#2b6cb0"),
    spaceBefore=15,
    spaceAfter=10
)
sub_heading_style = ParagraphStyle(
    'SubHeadingStyle',
    parent=styles['Heading3'],
    fontSize=14,
    textColor=colors.HexColor("#2d3748"),
    spaceBefore=10,
    spaceAfter=5
)
normal_style = styles["Normal"]
normal_style.fontSize = 11
normal_style.spaceAfter = 8

bullet_style = ParagraphStyle(
    'BulletStyle',
    parent=normal_style,
    leftIndent=20,
    bulletIndent=10,
    spaceAfter=5
)

warning_style = ParagraphStyle(
    'WarningStyle',
    parent=normal_style,
    textColor=colors.darkred,
    fontName="Helvetica-Oblique",
    spaceBefore=10,
    spaceAfter=15
)

Story = []

# Title
Story.append(Paragraph("ShadowLink", title_style))
Story.append(Paragraph("Threat Actor De-Anonymization Platform", ParagraphStyle('SubTitle', parent=title_style, fontSize=16, textColor=colors.gray)))
Story.append(Spacer(1, 20))
Story.append(Paragraph("Project Code: SIH 26151", normal_style))
Story.append(Paragraph("Version: 1.0.0 (Hackathon Release)", normal_style))
Story.append(Spacer(1, 30))

# 1. Executive Summary
Story.append(Paragraph("1. Executive Summary", heading_style))
Story.append(Paragraph("ShadowLink is a comprehensive forensic intelligence platform designed for Law Enforcement Agencies (LEAs) to de-anonymize threat actors operating on the dark web. The core challenge in dark web investigations is the fragmentation of identity—criminals use multiple aliases, rapidly switch forums, and rotate infrastructure to evade capture.", normal_style))
Story.append(Paragraph("ShadowLink solves this by fusing three distinct streams of intelligence to build a unified identity graph:", normal_style))
Story.append(Paragraph("• Infrastructure Analysis: Correlating dark web (.onion) services to public internet infrastructure.", bullet_style))
Story.append(Paragraph("• Cryptographic Correlation: Mapping reused PGP keys and cryptocurrency wallets across disparate personas.", bullet_style))
Story.append(Paragraph("• AI Stylometry: Using NLP to detect matching linguistic patterns across forums, identifying rebranded personas.", bullet_style))
Story.append(Paragraph("Hackathon Compliance Note: To ensure strict adherence to ethical guidelines, 100% of the data processed in this demo is generated via a custom synthetic data engine. No real PII is utilized.", warning_style))

# 2. System Architecture
Story.append(Paragraph("2. System Architecture & Tech Stack", heading_style))
Story.append(Paragraph("• Backend Engine: Python, FastAPI, Uvicorn", bullet_style))
Story.append(Paragraph("• Database: SQLite (In-memory fallback for demo portability)", bullet_style))
Story.append(Paragraph("• Graph Analytics: NetworkX (Python)", bullet_style))
Story.append(Paragraph("• AI / NLP: Scikit-Learn (TF-IDF, Cosine Similarity)", bullet_style))
Story.append(Paragraph("• Frontend Dashboard: HTML5, Vanilla JavaScript, Tailwind CSS", bullet_style))
Story.append(Paragraph("• Graph Visualization: Cytoscape.js", bullet_style))

# 3. Core Modules
Story.append(Paragraph("3. The Three Intelligence Engines", heading_style))
Story.append(Paragraph("3.1 Infrastructure Matcher", sub_heading_style))
Story.append(Paragraph("Scans a database of .onion sites and matches them against public IP addresses using SSL certificate hashes and custom HTTP server banners.", normal_style))

Story.append(Paragraph("3.2 Cryptographic Identity Graph", sub_heading_style))
Story.append(Paragraph("Scans the database for hard identifiers. If two personas share the same Bitcoin Address (SAME_WALLET) or PGP Public Key Fingerprint (SAME_PGP), a high-confidence link is created.", normal_style))

Story.append(Paragraph("3.3 AI Stylometry (Linguistic Analysis)", sub_heading_style))
Story.append(Paragraph("Uses TF-IDF Vectorization and Cosine Similarity to calculate the geometric angle between text vectors of forum posts. High similarity flags potential rebranded aliases for human analyst verification.", normal_style))

# 4. Database Schema
Story.append(Paragraph("4. Database Schema", heading_style))
data = [
    ["Table Name", "Purpose"],
    ["actors", "Root entity tracking risk category and confidence scores."],
    ["aliases", "Specific usernames used across different platforms."],
    ["identifiers", "PGP fingerprints and Crypto Wallets linked to aliases."],
    ["posts", "Raw text content scraped from forums for Stylometry."],
    ["infra_leaks", "Records of matched Tor to Clearnet vulnerabilities."],
    ["trust_links", "Central relationships (SAME_PGP, STYLE_MATCH, etc.)."]
]

table = Table(data, colWidths=[150, 300])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#f7fafc")),
    ('TEXTCOLOR', (0, 0), (1, 0), colors.HexColor("#1a365d")),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
Story.append(Spacer(1, 10))
Story.append(table)
Story.append(Spacer(1, 20))

# 5. Conclusion
Story.append(Paragraph("5. Conclusion", heading_style))
Story.append(Paragraph("ShadowLink successfully demonstrates how fusing network engineering, cryptography, and artificial intelligence can pierce the veil of dark web anonymity. By providing analysts with an interactive, mathematically backed identity graph, ShadowLink reduces investigation times from months to minutes.", normal_style))
Story.append(Spacer(1, 40))
Story.append(Paragraph("-- End of Report --", ParagraphStyle('Center', parent=normal_style, alignment=1, textColor=colors.gray)))

doc.build(Story)
print(f"PDF successfully generated at: {pdf_path}")
