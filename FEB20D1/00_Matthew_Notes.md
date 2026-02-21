# Matthew's Notes | Feb 20, 2026

## Your Role
Kevin presents. You back him up. Speak when spoken to or when Kevin needs a data pull.

---

## How Things Work (so you can explain if asked)

**Intel Hub** -- https://rmm-intel-hub.onrender.com/
Internal dashboard. 33,185 independent community pharmacies loaded from a CSV built by querying the CMS NPI Registry, deduplicating (removed chains, institutions, mail-order), and enriching every record with 6 federal data sources. Each pharmacy gets a composite score (0-100) based on three dimensions: Opportunity (45% -- disease burden, Medicare density, HPSA status), Financial Impact (30% -- estimated GLP-1 losses from state Medicaid claims data), and Urgency (25% -- GLP-1 volume trends, MFP exposure). Scores map to letter grades: A = immediate outreach, B = high priority, C = conditional, D = deprioritize. The dashboard lets you search by name/NPI/city, filter by state and grade, view intelligence reports per pharmacy, and export CRM-ready CSVs.

**Forecasting Tool** -- https://rmm-pharmacy-tool.vercel.app
Customer-facing calculator. A rep or pharmacy owner enters 4 fields (pharmacy name, state, monthly scripts, GLP-1 fills). The tool runs loss estimates based on NCPA survey averages and state-level Medicaid claims data, then shows estimated monthly/annual GLP-1 losses and projected ROI from using RMM. It's designed for live conversations -- show the prospect their own numbers. Behind it, there's also a full scorecard API that accepts 12 inputs across 3 dimensions and generates a personalized PDF report.

**Landing Pages** -- 3 static HTML pages, each targeting a specific pain point:
- GLP-1 page: leads with reimbursement losses, positions RMM as the fix
- DIR Fee page: leads with PBM fee squeeze, shows how RMM reduces exposure
- MFP page: leads with Most Favored Pharmacy risk, shows compliance path
Each is designed for targeted outreach -- send the right page to the right pharmacy based on their conversation segment from the Intel Hub data.

**Scorecards** -- personalized PDF reports generated per pharmacy. 3 scoring dimensions (Financial Health, Operational Efficiency, Growth Potential), each with sub-factors. The output shows where the pharmacy ranks, what's driving their score, and specific recommendations. Sample PDFs show what a prospect would receive.

**Velo Integration** -- code and guide for embedding the qualification form into the existing RMM Wix site. 5-step form captures pharmacy info, calls the scoring API, returns a result page. Kevin owns the implementation. Not live yet -- presented as working prototype, goes into Wix once Arica approves.

**State Outreach Lists** -- 51 CSVs (one per state), each row is a pharmacy with owner name, phone, grade, score, and market data. Import directly into any CRM. The Grade A CSV is the 4,978 highest-priority pharmacies nationally.

---

## If Kevin Asks You to Demo

**Intel Hub**
1. Show national overview
2. Pick a state (Kentucky is natural)
3. Search "Albany" -- pulls up Central Kentucky Apothecary (Arica's pharmacy)
4. Show the intelligence report: Grade A, Score 86.3, HPSA designated, Albany KY 42602
5. Show CSV export

**Forecasting Tool**
1. Enter: any pharmacy name, KY, 500 scripts/mo, 25 GLP-1 fills
2. Show the result: estimated loss, ROI case
3. "This is what a prospect sees -- their numbers, not a pitch"

**Landing Pages** -- open the 3 HTML files from FEB20D1
- GLP-1, DIR Fee, MFP -- each targets a specific pain point

**Scorecards** -- open from FEB20D1
- 3 sample PDFs showing what a personalized report looks like

---

## Questions for Arica

### Her current process:
- "How are you currently finding new pharmacies to reach out to?"
- "What does a typical outreach sequence look like -- email first, then call? Cold or warm?"
- "Which states or regions are you focused on right now?"
- "Are you working from any lists today, or is it mostly referrals and conferences?"

### Pain points and messaging:
- "When you talk to a pharmacy owner for the first time, what's the hook? What gets them to listen?"
- "Is GLP-1 loss landing as a conversation opener, or is there a different pain point that resonates more?"
- "Are DIR fees or MFP compliance coming up in conversations?"

### Existing customers:
- "Do you have a list of current RMM customers we could cross-reference against this data?"
- "Kevin mentioned some pharmacies barely use the software -- what does underutilization look like?"
- "If we showed an existing customer their market data -- HPSA status, diabetes burden, estimated losses -- would that help re-engage them?"

### Her team and tools:
- "How many people are doing outreach right now?"
- "What CRM or tools are they working in?"
- "If we handed you state-segmented lists this week, what would you need to start using them?"

### Scale and priorities:
- "If you could target 5 states tomorrow, which ones?"
- "What does 'success' look like for the next 30 days in terms of new pharmacy sign-ups?"
- "Is there a conference coming up where having this data would change your approach?"

---

## Listen For
- How she currently qualifies pharmacies (manual? referrals? conferences?)
- Which states she's focused on
- What pain point opens conversations (GLP-1? DIR fees? something else?)
- Whether she has a customer list to cross-reference
- How many people are doing outreach and what tools they use
- What format she wants data in (CSV? dashboard access? email reports?)

---

## Don't Say
- Don't claim pharmacy-level fill counts (market estimates only)
- Don't promise timelines on Wix integration (Kevin's call)
- Don't overstate ROI (NCPA survey averages, not actuals)

## If She Wants Data Today
State CSVs are ready. Can email or share via Google Drive on the spot.

## Verified Numbers (if asked)
- 33,185 pharmacies in database
- 4,978 Grade A (Immediate Outreach)
- 8,296 Grade B (High Priority)
- 9,956 Grade C (Conditional)
- 9,955 Grade D (Deprioritize)
- 91.8% HPSA designation rate
- 6 federal data sources (CMS, CDC, Census, HRSA, USDA, NADAC)
- 24 data columns per pharmacy
- 51 states covered
