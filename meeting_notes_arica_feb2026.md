# Meeting Notes
## Kevin & Arica | Feb 20, 2026

---

## ROLES

Kevin is presenting. Matthew is support -- backup demos, technical questions, live data pulls if needed. Arica is the expert. Listen first, demo second.

---

## PRE-MEETING (5 min before)
- Wake up Render: hit https://texume-api.onrender.com/health and https://rmm-intel-hub.onrender.com/
- Have FEB20D1 folder open (all assets numbered by agenda order)
- Open in browser tabs:
  - https://rmm-intel-hub.onrender.com/ (Intelligence Hub dashboard)
  - https://rmm-pharmacy-tool.vercel.app (pharmacy forecasting tool)
  - Landing pages (3 HTML files from FEB20D1 folder)
- Have sample scorecards open (3 PDFs from FEB20D1 folder)

---

## KEVIN'S AGENDA (in order)

### 1. Research & Analysis Impacting Strategy (Kevin presents)

How the data and tools are driving real-time strategy decisions.

**Assets:** Methodology PDF (01_Research_Strategy--Methodology.pdf)
- 33,185 independent community pharmacies across 51 states
- Every pharmacy scored, graded, enriched with 6 federal data sources
- CMS Part D, Medicaid SDUD, CDC PLACES, Census ACS, HRSA HPSA, NADAC
- 24 columns per pharmacy, every number traceable to a government source

**Key stat:** "91.8% of these pharmacies are in federally designated Health Professional Shortage Areas."

### 2. Driving Enrollment in Mail-to-Retail (Discussion)

Arica's domain. Listen to how enrollment currently works. The tools support this but don't replace her process.

### 3. Listen/Learn from Arica on GLP-1 Landscape (Arica talks)

Take notes. Her knowledge of the current GLP-1 landscape shapes how the tools get used. Don't lecture -- ask:
- "What are you seeing with GLP-1 reimbursement right now?"
- "Is GLP-1 loss the right lead-in, or do conversations start with a different pain point?"

### 4. Targeted Landing Page Concepts (Kevin presents)

**Assets:** 3 HTML landing pages (02_Landing_Page--*.html)
- GLP-1 Optimization landing page
- DIR Fee Relief landing page
- MFP Alternative landing page
- A/B Testing Spec PDF (05_Marketing_Outreach--AB_Testing_Spec.pdf)

Each targets a specific pain point. Static concepts ready for feedback before going live.

### 5. 10-Question Survey & Scorecard for Lead Capture (Kevin presents)

**Assets:**
- Live forecasting tool: https://rmm-pharmacy-tool.vercel.app (4-field calculator, instant results)
- Velo Integration Guide (03_Survey_Scorecard--Velo_Integration_Guide.md) -- 5-step qualification form ready for Wix
- 3 sample scorecard PDFs (03_Survey_Scorecard--Sample_*.pdf)
- Full scorecard API generates personalized PDF per pharmacy

Kevin framing: these are working prototypes. The survey/scorecard lives inside Wix once Arica approves the approach.

### 6. RMM Intelligence Application (Kevin presents -- biggest demo moment)

**Asset:** https://rmm-intel-hub.onrender.com/

Demo flow:
1. Show the national overview (33,185 pharmacies, grade distribution)
2. Show the state table (Grade A concentration by state)
3. **Search "Albany" or "Arica Collins" to pull up her pharmacy** (Central Kentucky Apothecary, NPI 1497754923, Grade A, Score 86.3)
4. Show the intelligence report for her pharmacy
5. Show CSV export (filter by state, grade, export for CRM)

**Quick Start Guide available:** 04_Intel_Hub--Quick_Start_Guide.pdf (how to use the tool daily)

### 7. Fast-Acting Marketing Outreach/Campaign (Discussion)

Frame as a question for Arica: "What would outreach to a pre-qualified pharmacy look like from your side?"

**Supporting assets:**
- A/B Testing Spec for the landing pages
- State outreach CSVs (CRM-ready, every row has owner name, phone, market data)

### 8. Identify Pharmacy Lists to Approach (Kevin + Arica)

**Assets:**
- 06_Pharmacy_Lists--Grade_A_All_States.csv (4,978 Grade A pharmacies)
- 06_Pharmacy_Lists--Full_Database.csv (33,185 pharmacies)
- 51 state-level CSVs in State_Outreach_Lists_Verified/

Top states by Grade A concentration: West Virginia 84.5%, Mississippi, Arkansas, Alabama, Kentucky.

"Which states or regions do you want to start with? We can slice by state, grade, or conversation segment right now."

### 9. Conference/Event Follow-Up Lists (Arica provides)

Arica has the conference attendee data. We can cross-reference against the database to prioritize follow-ups by score and grade.

---

## QUESTIONS FOR ARICA

### Current operation:
- "How is your team currently identifying and qualifying new pharmacies?"
- "What does outreach look like today -- email, phone, in-person, ads?"
- "Which states or regions are you focused on right now?"

### The data:
- "Do you have a list of existing RMM customers we could cross-reference?" *(fastest win)*
- "Is GLP-1 loss the right lead-in, or do your conversations start with a different pain point?"

### Existing customers:
- "Kevin mentioned some pharmacies on the software barely use it. What does that look like?"
- "Would showing an existing customer their market conditions help re-engage them?"

### Her team:
- "How many people on outreach? What tools do they use?"
- "If we gave you state-segmented lists this week, what would you need to start using them?"

---

## FASTEST WIN

"The fastest thing we can do is cross-reference your existing customer list against this database. We show each one their market conditions -- what they're sitting on and what they're missing. No cold calls. These are pharmacies that already said yes."

---

## GUARDRAILS

**Don't say:**
- Don't claim pharmacy-level fill counts (we have market-level estimates, not actuals)
- Don't overstate ROI projections -- based on NCPA survey averages, not individual pharmacy data
- Don't promise Wix integration timeline -- Kevin owns that
- Don't say "we" when meaning Matthew's work -- position as "here's what I built, Kevin is integrating it"

**If Arica asks about pricing:**
- Data and scoring system are part of the engagement Kevin contracted
- How it's packaged for pharmacy customers is Arica's decision
- $275/mo subscription and ROI math are in the system but defer to her on positioning

**If she wants the data today:**
- State lists are CSV files, ready to email or share via Google Drive
- Can slice by any state, grade, or conversation segment on the spot

---

## LIVE URLS

| Resource | URL |
|----------|-----|
| Intel Hub Dashboard | https://rmm-intel-hub.onrender.com/ |
| Pharmacy Forecasting Tool | https://rmm-pharmacy-tool.vercel.app |
| Render API (health check) | https://texume-api.onrender.com/health |

---

## KEY NUMBERS (verified from source CSV)

| Metric | Value |
|--------|-------|
| Total pharmacies in database | 33,185 |
| Grade A (Immediate Outreach) | 4,978 |
| Grade B (High Priority) | 8,296 |
| Grade C (Conditional) | 9,956 |
| Grade D (Deprioritize) | 9,955 |
| HPSA designation rate | 91.8% |
| Data columns per pharmacy | 24 |
| Federal data sources | 6 |
| States covered | 51 |
| State outreach CSVs | 51 |

---

## FEB20D1 FOLDER CONTENTS (presentation order)

| # | Agenda Item | File |
|---|---|---|
| 01 | Research & Strategy | Methodology PDF |
| 02 | Landing Pages | GLP-1, DIR Fee, MFP (3 HTML) |
| 03 | Survey & Scorecard | Velo guide + 3 sample scorecard PDFs |
| 04 | Intelligence App | Quick Start Guide PDF |
| 05 | Marketing Outreach | A/B Testing Spec PDF |
| 06 | Pharmacy Lists | Grade A CSV + Full Database CSV |
