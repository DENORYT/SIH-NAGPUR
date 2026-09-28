# ShadowLink — Frontend Dashboard Architecture

## Overview
Single-page analyst dashboard built with vanilla HTML/CSS/JS + Cytoscape.js for
the interactive threat-actor graph. No heavy framework needed for a hackathon demo —
keeps the build step zero and the deploy instant.

## Page Layout (4 Views)

### View 1: Command Center (Landing Page)
```
┌──────────────────────────────────────────────────────┐
│  SHADOWLINK INTELLIGENCE PLATFORM         [Run Scan] │
├──────────┬──────────┬──────────┬─────────────────────┤
│ Actors   │ Leaks    │ Links    │ Clusters            │
│   18     │   3      │   14     │   2                 │
├──────────┴──────────┴──────────┴─────────────────────┤
│                                                      │
│  [Threat Actor Table]                                │
│  Handle  | Risk  | Confidence | Aliases | Actions    │
│  ghost77 | DRUGS | 82.5       | 3       | [View]     │
│  onyx_404| ARMS  | 91.2       | 2       | [View]     │
│  ...                                                 │
└──────────────────────────────────────────────────────┘
```

### View 2: Interactive Graph (Cytoscape.js)
```
┌──────────────────────────────────────────────────────┐
│  IDENTITY GRAPH          [Filter: All | PGP | Wallet │
│                           | Style | Vouch]           │
├──────────────────────────────────────────────────────┤
│                                                      │
│     (ghost77)───SAME_PGP───(onyx_404)                │
│         │                       │                    │
│     VOUCHED_FOR             SAME_WALLET              │
│         │                       │                    │
│     (wraith12)         (shadow_7)                    │
│                   ╌╌╌╌╌╌╌╌╌╌╌╌╌╌                    │
│              STYLE_MATCH (dashed)                    │
│                   ╌╌╌╌╌╌╌╌╌╌╌╌╌╌                    │
│              (cipher_x)                              │
│                                                      │
│  Click node → Actor Details Sidebar                  │
└──────────────────────────────────────────────────────┘
```

### View 3: Infrastructure Leaks
```
┌──────────────────────────────────────────────────────┐
│  INFRASTRUCTURE DE-ANONYMIZATION RESULTS             │
├──────────────────────────────────────────────────────┤
│  Onion Address    | Type          | Clearnet IP      │
│  abc123...onion   | SSL_CERT      | 185.220.101.42   │
│  def456...onion   | SERVER_BANNER | 91.218.67.14     │
│  ghi789...onion   | SSL_CERT      | 103.28.52.93     │
│                                                      │
│  [Click row → Evidence Detail Modal]                 │
└──────────────────────────────────────────────────────┘
```

### View 4: Stylometry Inspector
```
┌──────────────────────────────────────────────────────┐
│  AI-SUGGESTED STYLE MATCHES (Needs Human Review)     │
├─────────────────────┬────────────────────────────────┤
│  ACTOR A            │  ACTOR B                       │
│  Handle: ghost77    │  Handle: cipher_x              │
│  Avg Sentence: 3.2  │  Avg Sentence: 3.4             │
│  Vocab Richness: 0.8│  Vocab Richness: 0.79          │
│  Punct !: 0.02      │  Punct !: 0.01                 │
│                     │                                │
│  Cosine Similarity: 0.84                             │
│  [VERIFY AS MATCH]  [DISMISS]                        │
└──────────────────────────────────────────────────────┘
```

## Tech Choices
- HTML5 + Tailwind CSS (via CDN)
- Cytoscape.js (via CDN) for graph visualization
- Vanilla JavaScript fetch() calls to /api/* endpoints
- No build step, no npm, no node_modules
