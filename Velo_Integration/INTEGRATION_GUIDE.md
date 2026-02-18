# RetailMyMeds Qualification Form - Wix Velo Integration Guide

**For:** Kevin McCarron
**From:** Matthew Scott
**Date:** February 2026

---

## What's in This Package

```
Velo_Integration/
  backend/
    scorecard.jsw        <- Server-side API caller (goes in Wix backend)
  page-code/
    qualification-form.js <- Form page logic (copy into page code panel)
    results.js           <- Optional: separate results page
  INTEGRATION_GUIDE.md   <- This file
```

## What It Does

1. User fills out a 5-step form on retailmymeds.com
2. Form submits to the live scoring API at `texume-api.onrender.com`
3. API scores the pharmacy across 3 dimensions (Financial Fit, Operational Readiness, Market Urgency)
4. User sees their grade (A/B/C/D), scores, projected ROI, and can download a PDF scorecard

The API is already live and tested. This code connects your Wix site to it.

---

## Setup Steps

### Step 1: Add the Backend Module (5 min)

1. In Wix Editor, open the code panel (Dev Mode must be enabled)
2. In the file tree on the left, find **Backend & Public** > **backend**
3. Create a new file: `scorecard.jsw` (the `.jsw` extension is required)
4. Paste the contents of `backend/scorecard.jsw` into it
5. Save

That's it. The backend module exposes two functions:
- `generateScorecard(formData)` -- scores a pharmacy and returns the result
- `warmUpApi()` -- pings the API on page load so it's warm when the user submits

### Step 2: Build the Form Page in Wix Editor (1-2 hrs)

Create a new page called "Qualification" (or whatever you prefer). Build these UI elements:

**Option A: Multi-State Box (recommended)**
Use a Multi-State Box with 5 states (step1 through step5), plus a results state. Each state contains that step's fields. The code shows/hides states.

**Option B: Show/Hide Groups**
Create container boxes named `#step1` through `#step5` and `#resultsSection`. The code shows/hides them.

#### Element IDs to Create

The code references these exact IDs. Set them in the Properties panel for each element:

**Step 1 - "Your Pharmacy"**
| Element | ID | Type |
|---------|-----|------|
| Pharmacy Name | `#inputPharmacyName` | Text Input |
| City | `#inputCity` | Text Input |
| State | `#dropdownState` | Dropdown (50 states) |
| Years in Business | `#dropdownYears` | Dropdown |

State dropdown options: AL, AK, AZ, AR, CA, CO, CT, DE, FL, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NY, NC, ND, OH, OK, OR, PA, RI, SC, SD, TN, TX, UT, VT, VA, WA, WV, WI, WY

Years dropdown options: `Less than 5`, `5-10`, `10-20`, `20+`

**Step 2 - "Your Volume"**
| Element | ID | Type |
|---------|-----|------|
| Monthly Rx Volume | `#dropdownRxVolume` | Dropdown |
| GLP-1 Fills/Month | `#dropdownGlp1Fills` | Dropdown |
| Gov Payer % | `#dropdownGovPayer` | Dropdown |

Rx Volume options: `Under 2,000`, `2,000-3,999`, `4,000-5,999`, `6,000-7,999`, `8,000+`

GLP-1 options: `I'm not sure`, `Under 100`, `100-200`, `200-350`, `350-500`, `500+`

Gov Payer options: `Under 20%`, `20-40%`, `40-60%`, `60-80%`, `Over 80%`

**Step 3 - "Your Systems"**
| Element | ID | Type |
|---------|-----|------|
| PMS System | `#dropdownPms` | Dropdown |
| Technicians | `#dropdownTechnicians` | Dropdown |

PMS options: `PioneerRx`, `Liberty Software`, `PrimeRx`, `Rx30`, `BestRx`, `QS/1`, `Computer-Rx`, `Other`, `I don't know`

Technicians options: `0`, `1`, `2`, `3-4`, `5+`

**Step 4 - "Your Situation"**
| Element | ID | Type |
|---------|-----|------|
| Losing money on Rx? | `#radioUnderwaterRx` | Radio Buttons |
| Lost patients to mail-order? | `#radioMailOrder` | Radio Buttons |
| DIR fee impact | `#radioDirFees` | Radio Buttons |
| MFP drugs? | `#radioMfp` | Radio Buttons |

Underwater Rx options: `Yes`, `No`, `I'm not sure`

Mail Order options: `Yes`, `No`

DIR Fees options: `Manageable`, `Significant squeeze`, `Threatening viability`

MFP options: `Yes`, `No`, `I'm not sure`

**Step 5 - "Get Your Scorecard"**
| Element | ID | Type |
|---------|-----|------|
| Your Name | `#inputOwnerName` | Text Input |
| Email | `#inputEmail` | Text Input |
| Phone | `#inputPhone` | Text Input |

**Navigation Buttons (one set per step)**
| Element | ID | Notes |
|---------|-----|-------|
| Next (step 1) | `#btnNext1` | |
| Next (step 2) | `#btnNext2` | |
| Next (step 3) | `#btnNext3` | |
| Next (step 4) | `#btnNext4` | |
| Back (step 2) | `#btnBack2` | |
| Back (step 3) | `#btnBack3` | |
| Back (step 4) | `#btnBack4` | |
| Back (step 5) | `#btnBack5` | |
| Submit | `#btnSubmit` | Label: "Get My Scorecard" |

**Progress**
| Element | ID | Type |
|---------|-----|------|
| Progress Bar | `#progressBar` | Progress Bar |
| Step Label | `#textStepLabel` | Text ("Step 1 of 5") |

**Results Section**
| Element | ID | Type |
|---------|-----|------|
| Container | `#resultsSection` | Box (hidden by default) |
| Loading | `#loadingOverlay` | Box with spinner (hidden by default) |
| Error | `#errorMessage` | Text (hidden by default, red) |
| Pharmacy Name | `#textPharmacyName` | Text |
| Grade | `#textOverallGrade` | Text (large) |
| Score | `#textOverallScore` | Text |
| Label | `#textOverallLabel` | Text |
| Financial Score | `#textFinancialScore` | Text |
| Operational Score | `#textOperationalScore` | Text |
| Market Score | `#textMarketScore` | Text |
| Recommendation | `#textRecommendation` | Text (multi-line) |
| Breakeven | `#textBreakeven` | Text |
| Download PDF | `#btnDownloadPdf` | Button |
| Schedule Call | `#btnScheduleCall` | Button |

### Step 3: Add the Page Code (2 min)

1. Select the qualification form page
2. Open the code panel at the bottom
3. Paste the contents of `page-code/qualification-form.js`
4. Save

### Step 4: Test It

1. Preview the site in Wix Editor
2. Fill out the form with test data:
   - Pharmacy Name: "Test Pharmacy"
   - City: "Louisville", State: "KY"
   - Monthly Rx: "4,000-5,999"
   - GLP-1: "200-350"
   - Gov Payer: "40-60%"
   - PMS: "PioneerRx"
   - Technicians: "2"
   - Answer the situation questions
   - Name: "Test User"
3. Submit and verify you get a score back

**First submission may take 30-60 seconds** -- the API runs on Render's free tier and cold-starts. The code calls `warmUpApi()` on page load to minimize this, but the first ever request of the day will be slow.

### Step 5: Publish

Once the form works in preview, publish the site. The API is already configured to accept requests from `www.retailmymeds.com` and `retailmymeds.com` (CORS is set up).

---

## Architecture

```
[Wix Site]                        [Render]

User fills form
    |
    v
qualification-form.js
    |
    v
backend/scorecard.jsw  ------>  POST /scorecard
  (server-side fetch)             |
                                  v
                              pharmacy_scorecard.py
                              (scoring engine)
                                  |
                                  v
                              scorecard_pharmacy.tex
                              (LaTeX template)
                                  |
                                  v
                              latex.ytotech.com
                              (PDF compilation)
                                  |
                                  v
                              JSON + PDF base64
    <------------------------------
    |
    v
Results displayed on page
User downloads PDF
```

---

## Dropdown Values Must Match Exactly

The API maps dropdown text to numeric values. The text in your Wix dropdowns must match these strings exactly (case-sensitive):

```
Monthly Rx Volume:     "Under 2,000" | "2,000-3,999" | "4,000-5,999" | "6,000-7,999" | "8,000+"
GLP-1 Fills:           "I'm not sure" | "Under 100" | "100-200" | "200-350" | "350-500" | "500+"
Gov Payer %:           "Under 20%" | "20-40%" | "40-60%" | "60-80%" | "Over 80%"
PMS:                   "PioneerRx" | "Liberty Software" | "PrimeRx" | "Rx30" | "BestRx" | "QS/1" | "Computer-Rx" | "Other" | "I don't know"
Technicians:           "0" | "1" | "2" | "3-4" | "5+"
Years in Business:     "Less than 5" | "5-10" | "10-20" | "20+"
DIR Fees:              "Manageable" | "Significant squeeze" | "Threatening viability"
```

If a dropdown value doesn't match, the API will fall back to a default -- it won't crash, but the score may be less accurate.

---

## Customization Points

Things you might want to change:

1. **Schedule Call link** -- In `qualification-form.js` line 218, update the URL from `/contact` to your Calendly or scheduling page
2. **Step copy** -- The header text for each step is in the Wix Editor, not the code. Change it there.
3. **3-step variant** -- The form spec mentions an A/B test with 3 steps instead of 5 (combining steps 1+2 and 3+4). To do this, merge the containers and update the step count in the code.
4. **Separate results page** -- If you prefer results on a new page instead of inline, use `results.js` (see the file for setup instructions). In `qualification-form.js`, replace the `displayResults()` call with a redirect: `import wixLocation from 'wix-location'; import { session } from 'wix-storage'; session.setItem('scorecardResult', JSON.stringify(result)); wixLocation.to('/results');`

---

## Known Limitations

1. **Cold start** -- Render free tier sleeps after 15 min of inactivity. First request takes 30-60s. The `warmUpApi()` call on page load helps but doesn't eliminate it. Upgrade to Render Starter ($7/month) for instant responses.
2. **Email delivery not implemented** -- The API returns `email_sent: false`. Scorecards are not automatically emailed to the pharmacy. For now, the user downloads the PDF from the results page. Phase 2 will add SendGrid integration.
3. **PDF download on mobile** -- The `downloadPdf()` function creates a blob URL. This works on desktop browsers and most mobile browsers, but some older mobile browsers may not support it. Test on iOS Safari and Android Chrome.

---

## Testing the API Directly

You can test the API without Wix to verify it's working:

```bash
curl -X POST https://texume-api.onrender.com/scorecard \
  -H "Content-Type: application/json" \
  -d '{
    "pharmacy_name": "Test Pharmacy",
    "city": "Louisville",
    "state": "KY",
    "monthly_rx_volume": "4,000-5,999",
    "glp1_monthly_fills": "200-350",
    "gov_payer_pct": "40-60%",
    "pms_system": "PioneerRx",
    "num_technicians": "2",
    "aware_of_underwater_rx": "Yes",
    "lost_patients_to_mail_order": "Yes",
    "dir_fee_pressure": "Significant squeeze",
    "owner_name": "Test User"
  }'
```

Expected response: JSON with `success: true`, `overall_grade`, `overall_score`, `pdf_base64`, etc.

---

## Questions?

Text or call Matthew. The API is live, the scoring engine is tested, and the PDF template is proven. The only piece that needs building is the Wix form UI -- which is what you're best at.
