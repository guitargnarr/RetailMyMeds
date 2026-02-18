# Kevin Briefing: The Data, The Strategy, and How It Fits Into RMM

**From:** Matthew
**Date:** Feb 18, 2026
**Purpose:** Understand what we built so you can frame it for Arica on Friday

---

## Why This Data Matters

Independent pharmacies are losing money every time they fill a GLP-1 prescription. Ozempic, Wegovy, Mounjaro, Zepbound -- these are the fastest-growing drug class in the country, and the reimbursement model is broken. Pharmacies fill the script, absorb the cost, and get paid back less than they spent. The more GLP-1s they fill, the more they lose.

Most pharmacy owners know they're losing money. What they don't know is how they compare to other pharmacies in their state, what their local market conditions look like, or that there's a way to recover it. That's the gap RetailMyMeds fills.

**The data we built identifies every CMS-verified independent pharmacy in the US and maps their market conditions using federal data. No estimates. No assumptions. Every data point traces back to a government source.**

---

## What We Verified (Feb 18, 2026)

We queried every single NPI in our database against the CMS NPI Registry API -- all 41,775 of them. This is the same system CMS uses to track every healthcare provider in the country.

**Results:**

| Metric | Count |
|---|---|
| Total NPIs queried | 41,775 |
| Found in NPI Registry | 41,763 |
| CMS-confirmed Active | 41,763 |
| Primary Community/Retail Pharmacy | 40,157 |
| Excluding mail-order | 39,611 |
| Not found in registry | 12 |
| Address matches our records | 99.98% |
| Phone matches our records | 99.97% |

**Key finding:** Our original database estimated 9,571 pharmacies as "Likely Closed" and 10,185 as "Uncertain." CMS says they are ALL active. That's 19,754 pharmacies we were about to exclude from outreach that are real, operating, reachable businesses.

**Previous target list:** 5,922 pharmacies (filtered by our estimates)
**Verified target list:** 39,611 pharmacies (every one CMS-confirmed active)
**That's 6.7x more pharmacies than we were going to show Arica.**

---

## What Drives the Data

The verified database runs on three layers of public federal data:

**Layer 1: Who are they? (CMS NPI Registry -- verified Feb 18, 2026)**
- Every pharmacy individually queried against the CMS NPI Registry API
- 39,611 confirmed active community/retail pharmacies
- Each record verified: name, address, phone, taxonomy classification, active status
- CMS updates this registry weekly -- we can re-verify at any time

**Layer 2: What's happening in their market? (CDC, Census, HRSA, CMS Part D)**
- CMS Medicare Part D Spending Data -- actual Medicare spending on GLP-1 drugs by state
- CDC/Census demographic data at the zip code level: diabetes prevalence, obesity rates, % over 65, median income
- HRSA Health Professional Shortage Area (HPSA) designations -- 36,350 of our 39,611 pharmacies (91.8%) are in federally designated shortage areas

**Layer 3: How do we rank them?**
- Pharmacies are sorted by market indicators: HPSA score, local diabetes prevalence, senior population %, and state-level GLP-1 spending
- A pharmacy in a high-HPSA, high-diabetes, high-Medicare zip code in a high-GLP-1 state ranks higher
- This ranking is based entirely on public data -- no financial estimates, no modeled assumptions

**What we DON'T claim to know:** Individual pharmacy fill counts, revenue, or specific dollar losses. No public database provides pharmacy-level prescription volume. If Arica has pipeline data with real pharmacy-level numbers, that plugs directly in and makes the ranking pharmacy-specific. The framework is built to accept better data.

---

## How the Data Gets Updated

Right now, the data is a snapshot verified against the most recent CMS data. The system is designed to be refreshed:

- **NPI Registry:** Updated weekly by CMS. New pharmacies, closures, and ownership changes show up here. We can re-verify the entire database in under an hour.
- **Part D Spending:** Released annually by CMS. When 2025 data drops, we re-run the GLP-1 market calculations.
- **Demographics:** Census/CDC data updates periodically. Zip-level health indicators refresh yearly.
- **Verification:** The verification script is automated. One command re-queries all 39,611 NPIs against CMS.

The vision: as RMM onboards pharmacies, their ACTUAL performance data feeds back into the ranking. Market indicators get supplemented with real fill data. The data gets better with every pharmacy that signs up.

---

## How This Operates as a Sales Tool

### The Outreach Lists (what Arica's team uses)

We have 39,611 CMS-verified active community/retail pharmacies, organized by state and ranked by market conditions.

| State | Pharmacies | | State | Pharmacies |
|---|---|---|---|---|
| NY | 4,712 | | GA | 1,146 |
| TX | 3,774 | | IL | 1,024 |
| CA | 3,631 | | OH | 923 |
| FL | 3,250 | | LA | 874 |
| MI | 2,032 | | AL | 841 |
| PA | 1,601 | | TN | 822 |
| NJ | 1,524 | | KY | 800 |
| NC | 1,161 | | MO | 798 |

Each pharmacy has: NPI, name, owner name, city, state, zip, phone (verified against CMS), taxonomy classification, local diabetes rate, obesity rate, senior population %, median income, HPSA designation and score, and state-level GLP-1 market data.

### The Sales Conversation Flow

1. **Open with their market:** "Your pharmacy is in a zip code where [X]% of adults have diabetes and [Y]% of the population is over 65. Your state averages $[Z] in GLP-1 Medicare spending per pharmacy."
2. **Establish credibility:** "This comes from CMS, CDC, and Census data. We verified your NPI is active through the CMS registry as of this week."
3. **Create the comparison:** "Pharmacies in your market conditions are prime candidates for GLP-1 reimbursement optimization. The ones working with RetailMyMeds are recovering margin they were losing."
4. **Ask, don't tell:** "Does this match what you're seeing? Are GLP-1 losses something you're tracking? What does your current volume look like?"
5. **Bridge to RMM:** Their answer provides the real numbers. The data got you in the door. Their situation determines the pitch.

### Integration Into retailmymeds.com

The data serves four channels, not just phone calls:

**1. Email Campaigns and Ad Targeting (state-level segmentation)**

The data is organized by state with verified contact information. This means:

- **Email campaigns by state:** "Florida has 3,250 independent pharmacies. Here's what CMS data shows about GLP-1 spending in your state." Each state gets tailored messaging because the market conditions are different.
- **Ad targeting by geography:** Run ads in the states with the highest concentration of pharmacies (NY 4,712, TX 3,774, CA 3,631, FL 3,250). The ad spend goes where the pharmacies are.
- **Lookalike audiences:** 39,611 verified pharmacy profiles define the target. Platforms can find similar businesses.

The state lists are CSV files. They import directly into Mailchimp, HubSpot, Constant Contact, or any email platform. Each row has owner name, pharmacy name, city, phone, and market data -- everything needed to personalize an email.

**2. Re-Engaging Existing Customers**

Kevin mentioned that pharmacies already on the RMM software barely use it. The data helps here too:

- **Match existing customers against the verified database.** If Arica provides a list of current RMM pharmacies (even just names and states), we can cross-reference them and show each one their market conditions -- what their zip code looks like, what their state's GLP-1 spending is, and how their area compares.
- **"Your market shows [X]% diabetes prevalence and your state averages $[Y] in GLP-1 costs per pharmacy -- and you already have the tool to capture that"** -- that's a re-engagement message grounded in data, not sales pressure.
- **Identify which existing customers are in the highest-need markets.** Prioritize re-engagement outreach to the ones in high-HPSA, high-diabetes, high-GLP-1 areas -- they have the most to gain from actually using the software.

This is potentially the fastest win for Friday. Arica doesn't need to cold call anyone. She can start with pharmacies that already said yes and aren't using what they paid for.

**3. Inbound (pharmacies finding RMM online)**

- The Pharmacy Forecasting page on retailmymeds.com will have a qualification form
- A pharmacy owner enters their info, the scoring API returns their personalized market analysis
- This is what you're building in Wix -- the Multi-State Box with 5 steps + results
- The backend code (scorecard.jsw) is already in place. The form UI needs to be completed.

**4. New Outbound (Arica's team calling net-new pharmacies)**

- 51 state-level outreach lists ready to load into any CRM or call sheet
- Each pharmacy has: name, owner, phone (CMS-verified), market indicators, HPSA status
- Ranked by market conditions so the strongest leads are at the top
- Can be sliced by state however Arica's team organizes territories

**The flywheel:** Email and ads drive pharmacies to the website. The website qualifies them with the scoring form. Outbound calls follow up the strongest market leads. Existing customers get re-engaged with their own market data. Every pharmacy that engages adds real data to the system. The data gets better with use, not stale with time.

---

## Wix Status and Options

I got into Wix Studio today. Here's what you built and where it stands:

**What's done:**
- scorecard.jsw is in the backend with the API code
- Multi-State Box on the Pharmacy Forecasting page with 6 states (step1-step5 + results)
- Structure matches the integration guide exactly

**What remains:**
- Form elements need to be placed inside each state (~40 elements: inputs, dropdowns, buttons)
- Page code needs to be pasted (already written)

**Options by effort level:**

| Option | Effort | What You Get |
|---|---|---|
| **Embed the demo page** | 30 min | Drop an HTML widget on the Pharmacy Forecasting page pointing to the working demo. Functional immediately. Not native Wix styling. |
| **Complete the native form** | 2-3 hrs | Place all form elements in the Multi-State Box, paste the page code. Fully native, matches site design. |
| **Demo only for Friday** | 0 min | Show Arica the working demo page (not on Wix). Prove the engine works. Build the Wix integration after her feedback. |

My recommendation: use the existing demo for Friday. Build the native Wix form after Arica confirms the approach and tells us what her team needs. Her feedback might change what the form should ask.

---

## What Arica Should Walk Away From Friday Understanding

1. We have a database of 39,611 CMS-verified active independent pharmacies -- every one confirmed through the NPI Registry this week
2. Each pharmacy has verified contact info, CMS taxonomy classification, and local market data from federal sources
3. The data is organized by state and ranked by market indicators -- ready for email, ads, outbound calls, or re-engagement
4. 91.8% of these pharmacies are in federally designated Health Professional Shortage Areas
5. **Existing RMM customers can be cross-referenced immediately.** If she gives us the list, we show each one their market conditions. That might be the quickest win.
6. The state-level lists are ready to import into any email platform or CRM today
7. The same data powers a real-time qualification tool that will live on retailmymeds.com
8. This isn't a one-time report. The entire database can be re-verified against CMS in under an hour.

---

## Questions for Arica

**About her current operation:**
1. How is her team currently identifying and qualifying new pharmacies?
2. What does outreach look like today -- email, phone, in-person, ads?
3. Which states or regions is she focused on right now?

**About the data:**
4. Does she have a list of existing RMM customers we could cross-reference? (fastest win)
5. Does she have pharmacy-level data from her pipeline that would sharpen our market analysis?
6. Is GLP-1 loss the right lead-in, or do her conversations start with a different pain point?

**About the existing customer problem:**
7. What does "barely using the software" look like? Which features are underused?
8. Has she tried re-engagement campaigns before? What worked, what didn't?
9. Would showing an existing customer their market conditions and what they're missing be useful?

**About her team:**
10. How many people does she have on outreach? What tools do they use (CRM, email platform)?
11. If we gave her state-segmented lists tomorrow, what would she need to start using them?

---

## One-Liner

"We verified every independent pharmacy in the US through the CMS NPI Registry. 39,611 are confirmed active. Each one has verified contact info and local market data from federal sources. The lists are organized by state and ready to load into any CRM or email platform. We need Arica to tell us where to aim it first."
