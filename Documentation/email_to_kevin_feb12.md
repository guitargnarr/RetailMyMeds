**Subject: Research results + updated Wix spec from today**

---

Kevin,

Good talking today. Here's what I built after our call and how it connects to what you're building for Arica.

**The big picture**

The targeting database identifies which pharmacies to reach. The qualification form on your site scores them when they respond. Together they give Arica a system: she knows who to call, the website qualifies them when they engage, and the scoring engine delivers a personalized report automatically. My work feeds the data layer. Your site is where it comes to life.

**1. New: GLP-1 Pharmacy Targeting Database**

I ran the 41,775 independent pharmacies from the NPPES extraction against six federal datasets (CMS Medicare Part D, Medicaid SDUD, CDC PLACES, Census ACS, HRSA HPSA) to score and rank every pharmacy by GLP-1 financial exposure.

The result is a single CSV -- 41,775 rows, 36 columns -- where each pharmacy has:
- Estimated monthly GLP-1 fills and projected financial loss (low/mid/high)
- Area health context (diabetes rate, obesity rate, Medicare density, HPSA designation)
- A final score, letter grade (A/B/C/D), conversation segment (GLP-1 / MFP / DIR), and outreach priority

11,190 pharmacies are flagged "Immediate Outreach." Louisiana alone has 759 of those, averaging ~$20K/month in estimated GLP-1 losses with a 2.5x projected ROI.

I've attached two PDFs that explain the data:
- **Independent Pharmacy Database -- Session Report** (12 pages): How the base dataset was built, what it contains, what it can't answer yet, and the enrichment path forward
- **GLP-1 Pharmacy Targeting** (6 pages): The scoring methodology, grade distribution, outreach priorities, financial model, and top 10 states by immediate outreach volume

I've also attached the CSV itself (**pharmacies_glp1_targeting.csv**). This is the raw dataset -- one row per pharmacy, 36 columns of scores, financials, and area health data. You won't need it for the site build, but it's the source of truth behind everything in the reports and it's what Arica will work from when she starts outreach.

Every number traces to a named federal source. The financial projections (loss per fill, savings, ROI) are estimates built on NCPA survey data and are clearly labeled as such in both reports. The underlying area health and claims data is measured, not estimated.

**2. Updated: Wix Qualification Form Spec (v2.1)**

Also attached. This reflects what we discussed today:
- Replaced the webhook/Google Sheets approach with Wix Velo -- I'll provide the backend code, you handle the form layout in Studio
- Updated all references for Wix Studio (your platform), not the classic Editor
- Added an effort estimate for your side: roughly 2-4 hours of Studio work, no custom JavaScript to write
- The spec is self-contained enough to hand off to another developer if you'd rather delegate it

The deployment checklist is on page 11. The qualification form uses the same scoring dimensions as the targeting database -- when a pharmacy owner fills out the form on your site, the system scores them the same way the CSV scores the 41,775 we already have data on.

**Clarifications from today:**
- Nothing is live or connected to your site. Everything exists and is tested, but nothing activates until you integrate.
- I'll provide the Velo code (backend module, form handler, email template). You own the form layout, the site design, and when it goes live.

**Next steps:**
1. I deliver the Velo code package
2. You build the 5-step form layout in Studio using the field specs
3. We test end-to-end with a sample submission
4. Arica starts running real prospects through the system -- the targeting CSV tells her who to call, your site qualifies them when they come in

Let me know when you want to pick up on step 1.

-- Matthew
