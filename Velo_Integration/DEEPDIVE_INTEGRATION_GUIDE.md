# RetailMyMeds Deep-Dive Evaluation - Wix Velo Integration Guide

**For:** Kevin McCarron
**From:** Matthew Scott
**Date:** February 20, 2026

---

## What This Is

The Deep-Dive is a **$149 paid evaluation** that sits above the free scorecard in the funnel. Instead of industry benchmarks, it uses the pharmacy's **actual dispensing data** -- drug-by-drug acquisition costs, reimbursement, payer type, MFP rebate shortfalls -- and produces a 6-8 page PDF with real numbers.

```
Free Scorecard (lead gen)  -->  Paid Deep-Dive ($149)  -->  RMM Subscription ($275/mo)
10-question form                Drug-level actuals          Prescription routing
Industry benchmarks             Real loss-per-fill
~2 minutes                      ~5 minutes
```

The $149 is credited toward the first month of the $275/mo subscription if they enroll within 30 days. Filters tire-kickers, creates standalone revenue, below approval threshold for pharmacy owners.

---

## What's in This Package

```
Velo_Integration/
  backend/
    scorecard.jsw              <- Existing (no changes)
    deepdive.jsw               <- NEW: Server-side API caller
  page-code/
    qualification-form.js      <- Existing (no changes)
    deepdive-form.js           <- NEW: Deep-dive form page logic
  INTEGRATION_GUIDE.md         <- Existing scorecard guide
  DEEPDIVE_INTEGRATION_GUIDE.md <- This file
```

---

## API Contract

**Endpoint:** `POST https://texume-api.onrender.com/deepdive`
**Alt:** `POST https://texume-api.onrender.com/deepdive/pdf` (returns raw PDF, no JSON)

### Request Schema (DeepDiveRequest)

```json
{
  "pharmacy_name": "Delaware Family Pharmacy",
  "owner_name": "Jane Smith",
  "city": "Wilmington",
  "state": "DE",
  "email": "jane@example.com",
  "phone": "302-555-1234",
  "npi_number": "1234567890",
  "pms_system": "PioneerRx",

  "glp1_drugs": [
    {
      "drug_name": "Ozempic",
      "fills_per_month": 45,
      "acquisition_cost": 950.00,
      "avg_reimbursement": 912.00,
      "payer_type": "Medicare Part D"
    },
    {
      "drug_name": "Mounjaro",
      "fills_per_month": 30,
      "acquisition_cost": 1050.00,
      "avg_reimbursement": 985.00,
      "payer_type": "Commercial PBM"
    },
    {
      "drug_name": "Wegovy",
      "fills_per_month": 15,
      "acquisition_cost": 1350.00,
      "avg_reimbursement": 1180.00,
      "payer_type": "Cash/GoodRx"
    }
  ],

  "mfp_drugs": [
    {
      "drug_name": "Eliquis",
      "fills_per_month": 20,
      "acquisition_cost": 550.00,
      "pbm_reimbursement": 320.00,
      "expected_rebate": 200.00,
      "actual_rebate_received": 120.00,
      "days_outstanding": 55
    }
  ],

  "specialty_monthly_loss": 1500.00,
  "generic_below_nadac_pct": 8,
  "monthly_rx_volume": 4500,

  "how_identify_underwater_now": "Review remittance",
  "current_routing_action": "We don't route"
}
```

### Response Schema (DeepDiveResponse)

```json
{
  "success": true,
  "pharmacy_name": "Delaware Family Pharmacy",
  "total_monthly_loss": "$12,541",
  "total_annual_loss": "$150,492",
  "losing_drug_count": 3,
  "weighted_avg_loss_per_fill": "$69.00",
  "breakeven_fills": 4,
  "has_mfp": true,
  "pdf_base64": "JVBERi0xLjQK...",
  "filename": "deepdive_delaware_family_pharmacy.pdf",
  "email_sent": false,
  "message": "Deep-dive analysis generated successfully with PDF"
}
```

### Required vs Optional Fields

| Field | Required | Default |
|-------|----------|---------|
| `pharmacy_name` | Yes | -- |
| `owner_name` | Yes | -- |
| `glp1_drugs` | Yes (1+ entries) | -- |
| `city` | No | `""` |
| `state` | No | `""` |
| `email` | No | `null` |
| `phone` | No | `null` |
| `npi_number` | No | `null` |
| `pms_system` | No | `""` |
| `mfp_drugs` | No | `[]` |
| `specialty_monthly_loss` | No | `0` |
| `generic_below_nadac_pct` | No | `0` |
| `monthly_rx_volume` | No | `0` |
| `how_identify_underwater_now` | No | `"We don't"` |
| `current_routing_action` | No | `"We don't route"` |

### GLP-1 Drug Entry Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `drug_name` | string | Yes | Picklist value (see below) |
| `fills_per_month` | integer | Yes | |
| `acquisition_cost` | float | Yes | Per-fill cost to pharmacy |
| `avg_reimbursement` | float | Yes | Per-fill PBM reimbursement |
| `payer_type` | string | No | Default: `"Commercial PBM"` |

**Drug name picklist:** `Ozempic`, `Wegovy`, `Mounjaro`, `Zepbound`, `Rybelsus`, `Trulicity`, `Saxenda`, `Victoza`, `Other`

**Payer type picklist:** `Medicare Part D`, `Medicaid`, `Commercial PBM`, `Cash/GoodRx`, `MFP`

### MFP Drug Entry Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `drug_name` | string | Yes | Picklist value (see below) |
| `fills_per_month` | integer | Yes | |
| `acquisition_cost` | float | Yes | Per-fill cost to pharmacy |
| `pbm_reimbursement` | float | Yes | What PBM pays |
| `expected_rebate` | float | Yes | What manufacturer should rebate |
| `actual_rebate_received` | float | No | Default: `null` (not yet received) |
| `days_outstanding` | integer | No | Default: `60` |

**MFP drug picklist (Cycle 1 -- active now):** `Eliquis`, `Jardiance`, `Xarelto`, `Januvia`, `Entresto`, `Xtandi`, `Ibrance`, `Imbruvica`, `Stelara`, `Fiasp/NovoLog`

---

## Form Design

The deep-dive form is longer than the scorecard (the pharmacy is providing real data, not dropdown estimates). It has 4 sections:

### Section 1: Pharmacy Identity

Pre-populate from the free scorecard if the pharmacy already completed one. Otherwise, collect fresh.

| Element | ID | Type | Notes |
|---------|-----|------|-------|
| Pharmacy Name | `#ddPharmacyName` | Text Input | Required |
| Owner Name | `#ddOwnerName` | Text Input | Required |
| City | `#ddCity` | Text Input | |
| State | `#ddState` | Dropdown (50 states) | |
| Email | `#ddEmail` | Text Input | |
| Phone | `#ddPhone` | Text Input | |
| NPI | `#ddNpi` | Text Input | Optional, 10 digits |
| PMS System | `#ddPmsSystem` | Dropdown | Same options as scorecard |

### Section 2: GLP-1 Drug Table

This is a **repeating section** -- the pharmacy adds 1-10 rows, one per GLP-1 drug they dispense.

**Implementation options:**

**Option A: Repeater (recommended)**
Use a Wix Repeater with add/remove buttons. Each row has:

| Element | ID Pattern | Type |
|---------|------------|------|
| Drug Name | `#ddGlp1Drug_{i}` | Dropdown |
| Fills/Month | `#ddGlp1Fills_{i}` | Number Input |
| Acquisition Cost | `#ddGlp1Acq_{i}` | Number Input (currency) |
| Reimbursement | `#ddGlp1Reimb_{i}` | Number Input (currency) |
| Payer Type | `#ddGlp1Payer_{i}` | Dropdown |
| Net/Fill (auto) | `#ddGlp1Net_{i}` | Text (computed: reimb - acq) |

| Button | ID | Action |
|--------|-----|--------|
| Add Drug | `#btnAddGlp1` | Add row (max 10) |
| Remove | `#btnRemoveGlp1_{i}` | Remove row (min 1) |

**Option B: Fixed rows**
Show 3 rows by default, "Add another drug" button reveals up to 10. Simpler but less clean.

**Net/Fill auto-calculation:**
When the user enters acquisition and reimbursement, immediately calculate and display net/fill. Color it red if negative, green if positive. This gives instant feedback before they even submit.

```javascript
// Pseudo-code for auto-calc
const acq = $w('#ddGlp1Acq_1').value;
const reimb = $w('#ddGlp1Reimb_1').value;
const net = reimb - acq;
$w('#ddGlp1Net_1').text = `${net >= 0 ? '+' : ''}$${net.toFixed(2)}`;
$w('#ddGlp1Net_1').style.color = net < 0 ? '#DC2626' : '#16A34A';
```

### Section 3: MFP Drug Table (Optional)

Same repeating pattern, but this section is hidden behind a toggle:

| Element | ID | Type |
|---------|-----|------|
| "Do you dispense MFP drugs?" | `#ddMfpToggle` | Toggle/Radio |

If yes, reveal the MFP table. Each row:

| Element | ID Pattern | Type |
|---------|------------|------|
| Drug Name | `#ddMfpDrug_{i}` | Dropdown |
| Fills/Month | `#ddMfpFills_{i}` | Number Input |
| Acquisition Cost | `#ddMfpAcq_{i}` | Number Input (currency) |
| PBM Reimbursement | `#ddMfpReimb_{i}` | Number Input (currency) |
| Expected Rebate | `#ddMfpExpRebate_{i}` | Number Input (currency) |
| Actual Rebate | `#ddMfpActRebate_{i}` | Number Input (currency, blank OK) |
| Days Outstanding | `#ddMfpDays_{i}` | Number Input (default: 60) |

### Section 4: Additional Context (Optional)

| Element | ID | Type | Notes |
|---------|-----|------|-------|
| Specialty Loss/Month | `#ddSpecialtyLoss` | Number Input (currency) | Self-reported |
| % Generics Below NADAC | `#ddGenericBelowNadac` | Number Input (0-100) | |
| Total Rx Volume/Month | `#ddMonthlyRxVolume` | Number Input | |
| How do you identify underwater Rx? | `#ddIdentifyMethod` | Dropdown | |
| Current routing? | `#ddRoutingAction` | Dropdown | |

**Identify method options:** `We don't`, `Staff flags manually`, `Review remittance after the fact`, `PMS reports`, `Third-party tool`

**Routing action options:** `We don't route`, `Refer to mail order informally`, `Have a process but it's manual`, `Tried but gave up`

### Payment Gate

The deep-dive requires payment before submission. Options:

1. **Wix Payments** -- charge $149 before API call
2. **Promo code fallback** -- text input `#ddPromoCode`, validate against a list (for Arica to give to pharmacies during outreach)
3. **Stripe Checkout** -- redirect to Stripe, return with session ID

Your call on which payment method. The API doesn't validate payment -- it generates the report for any valid request. Payment enforcement lives in the Wix layer.

### Submit + Results

| Element | ID | Type |
|---------|-----|------|
| Submit Button | `#btnSubmitDeepdive` | Button ("Generate My Analysis") |
| Loading Overlay | `#ddLoadingOverlay` | Box with spinner |
| Error Message | `#ddErrorMessage` | Text (red, hidden) |
| Results Container | `#ddResultsSection` | Box (hidden) |
| Monthly Loss | `#ddResultMonthlyLoss` | Text (large) |
| Annual Loss | `#ddResultAnnualLoss` | Text |
| Losing Drugs | `#ddResultLosingDrugs` | Text |
| Avg Loss/Fill | `#ddResultAvgLoss` | Text |
| Breakeven | `#ddResultBreakeven` | Text |
| Download PDF | `#btnDownloadDeepdive` | Button |
| Schedule Call | `#btnScheduleCallDd` | Button |

---

## What the PDF Contains

The API generates a 6-8 page PDF with:

1. **Cover page** -- pharmacy name, date, "Pharmacy Financial Deep-Dive" title
2. **Executive summary** -- total monthly/annual loss, breakeven fills, weighted average loss vs NCPA benchmark
3. **GLP-1 drug-by-drug loss table** -- every drug they entered, with net/fill color-coded (red = losing, green = profitable), routing recommendation per drug
4. **MFP cash-flow impact** (if applicable) -- current cash float tied up, rebate shortfalls by drug, projected exposure growth for 2027/2028
5. **Total financial picture** -- GLP-1 losses + MFP shortfalls + specialty + generic below-NADAC, all aggregated
6. **Routing plan** -- drug-by-drug: Route / Retain / Investigate with rationale
7. **ROI section** -- breakeven fills using their actual loss-per-fill (not the $39.50 NCPA default), 3 scenarios (2%/5%/10% routing)
8. **90-day action plan** -- immediate (flag at counter, configure RMM), 30-day (staff training, PMS config), 60-90 day (re-run analysis, MFP escalation)

---

## Architecture

```
[Wix Site]                          [Render]

User fills deep-dive form
  (drug-level data)
    |
    v
deepdive-form.js
    |
    v
backend/deepdive.jsw  -------->  POST /deepdive
  (server-side fetch)               |
                                    v
                                pharmacy_deepdive.py
                                (analysis engine)
                                    |
                                    v
                                deepdive_pharmacy.tex
                                (LaTeX template)
                                    |
                                    v
                                latex.ytotech.com
                                (PDF compilation)
                                    |
                                    v
                                JSON + PDF base64
    <--------------------------------
    |
    v
Results displayed on page
User downloads PDF
```

---

## Testing the API Directly

```bash
curl -X POST https://texume-api.onrender.com/deepdive \
  -H "Content-Type: application/json" \
  -d '{
    "pharmacy_name": "Test Pharmacy",
    "owner_name": "Jane Smith",
    "city": "Louisville",
    "state": "KY",
    "pms_system": "PioneerRx",
    "glp1_drugs": [
      {
        "drug_name": "Ozempic",
        "fills_per_month": 45,
        "acquisition_cost": 950,
        "avg_reimbursement": 912,
        "payer_type": "Medicare Part D"
      },
      {
        "drug_name": "Mounjaro",
        "fills_per_month": 30,
        "acquisition_cost": 1050,
        "avg_reimbursement": 985,
        "payer_type": "Commercial PBM"
      }
    ]
  }'
```

Expected: `success: true`, `total_monthly_loss`, `pdf_base64`, etc.

**To get just the PDF file:**
```bash
curl -X POST https://texume-api.onrender.com/deepdive/pdf \
  -H "Content-Type: application/json" \
  -d '{ ... same payload ... }' \
  -o test_deepdive.pdf
```

---

## Differences from Scorecard

| | Free Scorecard | Paid Deep-Dive |
|---|---|---|
| Price | Free | $149 |
| Input | 10 dropdowns, ~2 min | Drug-level actuals, ~5 min |
| Data source | Industry benchmarks | Pharmacy's own numbers |
| Loss calc | $39.50/fill NCPA avg | Actual acquisition vs reimbursement |
| MFP analysis | Binary flag (yes/no) | Drug-by-drug: float, rebate shortfall |
| ROI | Benchmark-based | Uses their weighted avg loss/fill |
| Output | 3-page scorecard PDF | 6-8 page analysis PDF |
| Routing plan | None | Drug-by-drug: Route/Retain/Investigate |
| Action plan | None | 90-day structured plan |
| API endpoint | `POST /scorecard` | `POST /deepdive` |

---

## Implementation Estimate

| Task | Time |
|------|------|
| Backend module (deepdive.jsw) | 5 min (copy + paste) |
| Form page UI (4 sections + repeating drug rows) | 3-4 hrs |
| Payment gate (Wix Payments or promo code) | 1-2 hrs |
| Results display + PDF download | 30 min |
| Testing | 30 min |
| **Total** | **5-7 hrs** |

The drug table repeater is the main build. Everything else follows the scorecard pattern you already built.

---

## Questions?

The API is live and tested. I've verified it generates the PDF correctly with a 3-drug GLP-1 + 2-drug MFP test payload. The test PDF is at `~/Desktop/RetailMyMeds/deepdive_test.pdf` if you want to see what the output looks like.

Text or call Matthew.
