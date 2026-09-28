from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

pdf_path = "ShadowLink_Project_Guide.pdf"
doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
styles = getSampleStyleSheet()

title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontSize=26, textColor=colors.HexColor("#14b8a6"), spaceAfter=10, alignment=1)
subtitle_style = ParagraphStyle("SubTitle", parent=styles["Normal"], fontSize=14, textColor=colors.HexColor("#a1a1aa"), spaceAfter=30, alignment=1)
h1_style = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#0f766e"), spaceBefore=20, spaceAfter=10)
h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#115e59"), spaceBefore=15, spaceAfter=8)
normal_style = ParagraphStyle("NormalText", parent=styles["Normal"], fontSize=11, textColor=colors.black, spaceAfter=10, leading=16)
bullet_style = ParagraphStyle("Bullet", parent=styles["Normal"], fontSize=11, textColor=colors.black, leftIndent=20, bulletIndent=10, spaceAfter=6, leading=16)

story = []

story.append(Spacer(1, 100))
story.append(Paragraph("SHADOWLINK OS", title_style))
story.append(Paragraph("Enterprise-Grade Cyber Intelligence Platform", subtitle_style))
story.append(Paragraph("Project Guide & Hackathon Pitch Document", subtitle_style))
story.append(PageBreak())

story.append(Paragraph("1. The Core Idea", h1_style))
story.append(Paragraph("<b>The Problem:</b> Cybercriminals hide behind fragmented, anonymous personas on the dark web (like AlphaBay or Agora). Law enforcement and cyber intelligence agencies struggle to connect these isolated usernames to a single real-world identity.", normal_style))
story.append(Paragraph("<b>The Solution:</b> ShadowLink is an automated Threat Intelligence Platform. It ingests massive amounts of raw dark web data and automatically correlates cryptographic keys, infrastructure mistakes, and linguistic patterns to de-anonymize threat actors. It connects the dots that humans miss.", normal_style))

story.append(Paragraph("2. How It Works (The Secret Sauce)", h1_style))
story.append(Paragraph("ShadowLink operates on three custom-built Python intelligence engines:", normal_style))
story.append(Paragraph("- <b>Infrastructure Mapping (OPSEC Failures):</b> Scans hidden .onion sites and correlates their SSL certificates and server banners against public clearnet servers. This exposes the physical location and IP address of hidden illicit servers.", bullet_style))
story.append(Paragraph("- <b>Cryptographic Identity Graph:</b> Uses graph theory (Cytoscape) to map shared identifiers. If Hacker A and Hacker B use the same PGP Encryption Key or Ethereum Wallet across different forums, the graph links them as the exact same real-world person.", bullet_style))
story.append(Paragraph("- <b>NLP Stylometry (AI Profiling):</b> Analyzes the typing style, slang, and syntax of forum posts. It mathematically proves two anonymous users are the same person based purely on how they type, even if they never share a crypto wallet.", bullet_style))

story.append(Paragraph("3. Real-World Integrations (The Wow Factor)", h1_style))
story.append(Paragraph("To prove the platform works on real data, ShadowLink features three live API integrations:", normal_style))
story.append(Paragraph("- <b>Live Etherscan Forensics:</b> Threat actors are seeded with real historical Whale and Hacker wallets (e.g., the Ronin Bridge Exploiter). The platform hits the live Ethereum mainnet to retrieve multi-million dollar balances and transaction histories in real time.", bullet_style))
story.append(Paragraph("- <b>Live Shodan OSINT:</b> When a hidden server's IP is exposed, ShadowLink queries the Shodan API to reveal live open ports, vulnerabilities, and ISP data.", bullet_style))
story.append(Paragraph("- <b>Generative AI Briefings:</b> An AI engine reads the complex graphs and auto-generates readable, executive-level threat intelligence reports for law enforcement.", bullet_style))

story.append(Paragraph("4. Technologies Used", h1_style))
story.append(Paragraph("- <b>Frontend:</b> HTML5, Tailwind CSS, JavaScript (Vanilla)", bullet_style))
story.append(Paragraph("- <b>Frontend Libraries:</b> Cytoscape.js (Graph Rendering), Leaflet.js (Geospatial Mapping)", bullet_style))
story.append(Paragraph("- <b>Backend:</b> Python 3, FastAPI, Uvicorn (Asynchronous API)", bullet_style))
story.append(Paragraph("- <b>Database:</b> SQLite (Memory-mapped via SQLAlchemy)", bullet_style))
story.append(Paragraph("- <b>Integrations:</b> Etherscan API (Blockchain), Shodan API (OSINT)", bullet_style))
story.append(PageBreak())

story.append(Paragraph("5. What Your Team Needs to Tell the Judges", h1_style))
story.append(Paragraph("<b>Q: Is this legal? Are you hacking real people?</b>", h2_style))
story.append(Paragraph("<i>A: We designed ShadowLink with strict safety boundaries. We are not actively scraping live, unmitigated dark web forums, as that violates ethical reconnaissance rules. Instead, our engine runs on a massive synthetic dataset injected with historical public case studies (like known ransomware wallets). This proves our algorithms and live integrations work perfectly at scale without causing real-world harm.</i>", normal_style))

story.append(Paragraph("<b>Q: What makes this better than existing tools?</b>", h2_style))
story.append(Paragraph("<i>A: Most OSINT tools require manual human investigation. ShadowLink is fully automated. By combining Stylometry (NLP) with Cryptographic mapping, we catch threat actors who change their encryption keys but forget to change their typing style.</i>", normal_style))

story.append(Paragraph("<b>Q: What is the most impressive part of the UI?</b>", h2_style))
story.append(Paragraph("<i>A: The UI is built to Palantir/Enterprise standards. It features a cinematic boot sequence, real-time threat tickers, and cascading data animations. But visually, the Cytoscape Identity Graph and the Live Etherscan Wallet Tracer are our most powerful demonstrations.</i>", normal_style))

doc.build(story)
print("PDF generated successfully.")
