# RetailMyMeds Full Site Scrape & Technical Research
**Date:** February 18, 2026
**Conducted by:** Matthew Scott (Project Lavos)
**Method:** Playwright screenshots, Python Playwright DOM extraction, WHOIS lookups, web search

---

## Table of Contents
1. [Site Structure & Pages](#site-structure--pages)
2. [Homepage](#homepage)
3. [About Us / How RMM Works](#about-us--how-rmm-works)
4. [Case Study](#case-study)
5. [FAQs](#faqs)
6. [Contact Us](#contact-us)
7. [Resources](#resources)
8. [Privacy Notice](#privacy-notice)
9. [Terms & Conditions](#terms--conditions)
10. [Member Dashboard (quick-rx.com:7005)](#member-dashboard)
11. [Technical Architecture](#technical-architecture)
12. [ThatWasEZ (Web Agency)](#thatwasez)
13. [quick-rx.com (Pharmacy Site)](#quickrxcom)
14. [White's Pharmacy / Dalton GA Connection](#whites-pharmacy--dalton-ga)
15. [Key People](#key-people)
16. [Domain Intelligence](#domain-intelligence)
17. [Pricing Discrepancy](#pricing-discrepancy)
18. [Analysis & Conclusions](#analysis--conclusions)

---

## Site Structure & Pages

| Page | URL | Status |
|------|-----|--------|
| Homepage | retailmymeds.com | Live |
| About Us / How RMM Works | /about-us | Live (both nav links go here) |
| Case Study | /case-study | Live |
| FAQs | /blank | Live (poor URL slug) |
| Contact Us | /contact-us | Live |
| Resources | /resources | Live (login-gated) |
| Privacy Notice | /privacy-notice | Live |
| Terms & Conditions | /terms-conditions | Live |
| Member Dashboard | quick-rx.com:7005 | Live (login required) |
| /how-rmm-works | 404 | Dead link -- nav says "How RMM Works" but links to /about-us |

**Platform:** Wix Thunderbolt renderer (v1.16889.0) with Velo
**Site builder credit:** "Created by ThatWasEZ" (visible in FAQs footer)
**Copyright:** 2026 RetailMyMeds

---

## Homepage

### Header / Nav
- Logo: "RetailMyMeds" (top left) with tagline "Profitable Patient Care"
- Nav items: About Us, How RMM Works, Case Study, FAQs
- CTAs: "Request Info/Enroll" (blue), "Member Dashboard" (black outline)

### Hero Section
- **Headline:** "Independent Pharmacy Profit Protection"
- **Subhead:** "More Profit in Your Pocket and Savings for Your Patients"
- Dr. Arica Collins featured with title "Independent Pharmacy Consultant" and email retailmymeds.com
- Blue CTA: "Let's Chat"

### "Featuring" Section
- Mail to Retail logo/partnership highlighted
- "Real Time - Real Numbers From Our Featured Locations"
- Three column callouts: Locations | Acquisition Cost Avoided | Net Loss Avoided

### Value Props (3 columns)
1. Recover Lost Profit from Net Negative Prescriptions
2. Decrease PBM Fees and True-ups
3. No Long-term Commitment
- Blue CTA: "Enroll with RMM"

### "How RetailMyMeds Works" Section
- Paragraph explaining the process -- identifying net-negative prescriptions, analyzing data, recovering profit
- Links: "View RMM Case Studies"

### Testimonials (6 cards)
- **Krystal Medlock** -- recovered lost profit, reduced DIR fees
- **Terry Davis** -- calls it a 4-in-1 independent pharmacy program
- **Kevin Ward** -- better cases of medication orders, decreased returns
- **Emily B.** -- worth every penny
- **Bryan M.** -- saving $4k in purchases, adding more customers
- One more partially visible -- "best thing for our pharmacy"

### Blue Banner
- "RetailMyMeds Delivers Continuously More Savings and Benefits to Pharmacies and Patients"
- Photo of pharmacist with patient

### Footer
- Menu and Contact columns
- Phone and email
- "Ready to Save with RMM? Get started today"

---

## About Us / How RMM Works

**URL:** /about-us (both "About Us" and "How RMM Works" nav links point here)

### What RMM Does
RetailMyMeds (RMM) was established for independent pharmacy professionals, for pharmacies and patients. Focus tied to: insurance cost, reimbursement, DIR fees, and PBM true-ups looking to recapture lost profit on net-negative prescriptions meant to help independents do the right thing for patients and still earn a living.

### The Method
"...let's be secret: life is happy so let's make it transparent. We will show you how your pharmacy can switch those net-negative or marginally profitable prescriptions to mail order and coordinate them for the patients."

### The Program
- Custom workflow integration designed to be managed by a technician
- Member dashboard provides extensive mail-order pharmacy information
- Easy to coordinate orders for many patients using different mail-order pharmacies
- Comprehensive training videos and program manual
- Individualized live performance trackers show pharmacy savings in real time

### Key Statement (bold on page)
> "RetailMyMeds is the software-based subscription model that makes this method easy, manageable, fast and immediately profitable"

### Pricing (About Us page)
- Subscription: $175/month (NOTE: conflicts with FAQ page -- see Pricing Discrepancy section)
- Positioned as potential for significant returns / positive ROI

### Independence Claim
"We are not affiliated with a PBM or mail order pharmacy, nor do we retain Rx. Our program was created by an independent for independents."

### Meet Dr. Collins
- Dr. Arica Collins -- President and CEO
- Pharmacy owner since 2008
- Experienced the highs and lows of ownership
- Leadership team experienced in analytics, provider sourcing, inventory management

---

## Case Study

**URL:** /case-study
**PDF:** https://www.retailmymeds.com/_files/ugd/edec96_02d0e47fc7774132b7449ef9a972742f.pdf

### TEST STORE DATA (2023-2024)

| Store | Months Enrolled | Total LPCs* | Patients Enrolled | Coordinated Rx* | Acquisition Avoided | Net Loss Avoided | Daily Rx Volume | Region | Est. Population (City) |
|-------|----------------|-------------|-------------------|-----------------|--------------------|-----------------|----|--------|----------------------|
| 1 | 3 months | 1 | 60 | 253 | $188,388 | $7,421 | 750 | Mid-Atlantic | 1,800 |
| 2 | 10 months | 2 | 148 | 922 | $658,578 | $31,360 | 500 | Southeast | 298,000 |
| 3 | 13 months | 1 | 54 | 487 | $320,240 | $9,610 | 450 | Southeast | 6,900 |
| 4 | 15 months | 1 | 70 | 559 | $405,574 | $16,361 | 275 | Southeast | 200 |

### 2024 PROJECTIONS (annualized, no growth assumed)

| Store | Coordinated Rx*** | Acquisition Avoided | Net Loss Avoided |
|-------|-------------------|--------------------|-----------------|
| 1 | 582 | $458,977 | $17,194 |
| 2 | 246 | $157,395 | $8,303 |
| 3 | 168 | $103,064 | $5,452 |
| 4 | 372 | $308,755 | $10,841 |

### Notes
- *LPCS = primary pharmacy employee overseeing the program
- ***Transferred prescriptions are based on 30-day fills
- Data collected from 4 member stores in 4 states (Southeast and Mid-Atlantic)
- Projections based on Jan 1 - Feb 29, 2024 initial totals, maintained without growth

### Key Observations
- Store 1 standout: only 3 months, smallest city (1,800 pop), highest acquisition avoided ($188k), highest Rx volume (750)
- Store 4 in a town of 200 people, projects $308k acquisition avoided -- rural viability proof
- "Acquisition avoided" is the headline number (hundreds of thousands). "Net loss avoided" is actual profit recovery ($5k-$31k range)
- Projected acquisition avoided across all 4 stores: ~$1.03M/year
- Projected net loss avoided across all 4 stores: ~$41.8k/year

---

## FAQs

**URL:** /blank (Wix accordion component)

| Question | Answer |
|----------|--------|
| Membership fee? | **$275/month per pharmacy**. Discounted rate **$225/month** for large groups or 5+ stores under common ownership |
| What's included? | Initial onboarding call, patient setup call, patient dashboard access, on-demand training videos, support via dashboard messaging/email/phone (8:30am-5pm CT Mon-Fri) |
| Contract length? | **No long-term commitment.** 30-day written notice to cancel |
| Payment methods? | Credit/debit cards, recurring ACH payments (ACH requires Plaid verification) |
| Plaid required? | Only for ACH. Credit card payments don't require Plaid |
| How to start? | Visit retailmymeds.com > Request Info/Enroll > fill out form > choose "Register and Begin" |
| References in my state? | Limited number of owners available as references -- email info@retailmymeds.com |
| Portal login issues? | Use "Forgot Your Password" link or email info@retailmymeds.com |

---

## Contact Us

**URL:** /contact-us

- **Headline:** "Ready to Protect Your Profit or Have Questions?"
- **Existing members:** Use Live Chat or email info@retailmymeds.com
- **Form fields:**
  - First Name, Last Name
  - Email*, Phone
  - NPI (if applicable)
  - Message
- **"Tell Us About Yourself":** Single Pharmacy Owner / Multiple Pharmacies / Other
- **"How Can RMM Help You?":** Register & Begin RMM / Questions for Now / Other
- **SMS opt-in** checkbox (opt-in / do not opt-in)
- **Support phone:** (866) 991-9791
- **Email:** info@retailmymeds.com

---

## Resources

**URL:** /resources

- **Title:** "Retail My Meds: Site Resources"
- Two sections, both require login:
  - **Training Videos & Manual** -- "Go to Video Training" (requires login)
  - **Print ProShop** -- "Visit Print ProShop" (requires login)

---

## Privacy Notice

**URL:** /privacy-notice
**Effective date:** February 8, 2023
**Entity:** Retailmymeds, LLC

### Personal Information Gathered
- **Information you provide:** Name, addresses, email, phone, username/password, credit card info, patients'/customers' names and personal info, financial info including SSN/EIN/TIN
- **Automatic information:** IP address, email address, browser type/version, OS, platform, full URL clickstream, date/time, precise location, cookies, JavaScript session data (page response times, clicks, scrolling, mouseovers)
- **Information from other sources:** Third-party accounts, identity verification providers

### How They Share Information
- **Agents** -- third parties performing functions (data analysis, marketing, payment processing, customer service)
- **Affiliated businesses** -- third parties involved in transactions
- **Business transfers** -- user info transferred in sale/acquisition
- **Promotional offers** -- select group offers on behalf of other businesses
- **Legal/protection** -- law enforcement, fraud protection, credit risk reduction
- **Service provision** -- as needed to deliver requested services
- **With consent** -- notification before sharing otherwise

### Key Details
- Cookies: Standard alphanumeric identifiers; recommend leaving enabled
- Children: Not directed at children under 13; does not knowingly collect their data
- Governing law: State of Kentucky
- Disputes: Subject to arbitration per Terms and Conditions
- **Contact for data requests:** Arica Collins, 104 E Cumberland St., Albany, KY 42602 / info@retailmymeds.com

---

## Terms & Conditions

**URL:** /terms-conditions
**Effective date:** February 8, 2023

### Binding Arbitration Warning
Contains binding arbitration provision and jury trial waiver.

### Key Sections

**Electronic Communications:** Consent to receive all communications electronically.

**Pricing and Payment:** Governed by Primary Agreement (the enrollment contract), not the website terms. Access can be terminated for non-payment.

**Intellectual Property:**
- Personal, limited, revocable, nonexclusive, non-transferable license during Primary Agreement term
- No reverse engineering, decompiling, or derivative works
- No resale (except identifying RMM to your customers)
- Competitors prohibited from using site for benchmarking

**Disclaimer of Warranties:** Site provided "AS IS" and "AS AVAILABLE". No warranties express or implied. Use at your sole risk.

**Limitation of Liability:** Maximum liability = amount paid for services in prior 12 months. No indirect, special, incidental, punitive, or consequential damages.

**Indemnification:** User indemnifies Retailmymeds from all claims arising from use.

**Governing Law:** Commonwealth of Kentucky

**Arbitration:**
1. Good faith negotiations first
2. Then neutral mediator
3. Then binding arbitration under American Health Law Association rules
4. Mediation/arbitration in Commonwealth of Kentucky
5. Costs split equally (except attorney's fees -- each party bears own, prevailing party recovers)
6. Judgment entered in County of Clinton, Kentucky
7. Jury trial waived

**Termination:** Retailmymeds can restrict/deny/suspend services immediately without notice for fraud, security, illegal activity, policy violations, or failure to comply with Terms.

**Legal Notices Address:**
```
Retailmymeds, LLC
c/o Arica Collins
104 E Cumberland St.
Albany, KY 42602
info@retailmymeds.com
```

---

## Member Dashboard

**URL:** https://quick-rx.com:7005/
**Page title:** "RetailMyMeds"
**Copyright:** "2025 Retail My Meds. All Rights Reserved"

### Login Page
- RetailMyMeds logo
- Username / Password fields
- "Remember me" checkbox
- Login button (green)
- "Forgot Password?" link
- Light blue background

### Technical Stack (extracted from page source)

| Layer | Technology | Evidence |
|-------|-----------|----------|
| **Framework** | Blazor WebAssembly (.NET/C#) | `blazor.webassembly.js`, `RetailMyMeds.Client.styles.css` |
| **UI Components** | Radzen Blazor | `Radzen.Blazor.js`, `default-base.css` |
| **UI Components** | Syncfusion Blazor | `syncfusion-blazor.min.js`, `bootstrap5.css` theme |
| **UI Components** | Blazor.Bootstrap | `blazor.bootstrap.js/css` |
| **UI Components** | Blazorise (FontAwesome icons) | `Blazorise.Icons.FontAwesome`, v1.8.9.0 |
| **Modals** | Blazored.Modal | `blazored.modal.js/css` |
| **Rich Text** | Blazored.TextEditor (Quill.js) | `Blazored-BlazorQuill.js`, `quill.snow.css` |
| **Charts** | Chart.js 4.0.1 + datalabels plugin | CDN loaded |
| **Calendar** | BlazorCalendar + FullCalendar | `BlazorCalendar.css`, `fullcalendar.bundle.js` |
| **Data Tables** | DataTables | `datatables.bundle.js/css` |
| **Drag/Drop** | SortableJS | CDN loaded |
| **CSS Framework** | Bootstrap 5.3.2/5.3.5 | CDN loaded |
| **Fonts** | Poppins, Roboto, Lato + Material Icons + FontAwesome 4.7 | Multiple font loads |
| **Analytics** | fngservices.com tracker | `t.fngservices.com/tracker.js` |
| **Iconography** | Iconify (beta) | `iconify-icon.min.js` |

### All Script Sources
```
https://quick-rx.com:7005/_framework/blazor.webassembly.js
https://quick-rx.com:7005/js/Custom.js
https://quick-rx.com:7005/assets/plugins/global/plugins.bundle.js
https://quick-rx.com:7005/assets/js/scripts.bundle.js
https://quick-rx.com:7005/assets/plugins/custom/fullcalendar/fullcalendar.bundle.js
https://quick-rx.com:7005/assets/plugins/custom/datatables/datatables.bundle.js
https://quick-rx.com:7005/assets/js/widgets.bundle.js
https://quick-rx.com:7005/assets/js/custom/widgets.js
https://quick-rx.com:7005/assets/js/custom/apps/chat/chat.js
https://quick-rx.com:7005/assets/js/custom/intro.js
https://quick-rx.com:7005/assets/js/custom/utilities/modals/upgrade-plan.js
https://quick-rx.com:7005/assets/js/custom/utilities/modals/create-campaign.js
https://quick-rx.com:7005/assets/js/custom/utilities/modals/users-search.js
https://quick-rx.com:7005/_content/Radzen.Blazor/Radzen.Blazor.js
https://quick-rx.com:7005/_content/Blazored.Modal/blazored.modal.js
https://code.iconify.design/iconify-icon/1.0.0-beta.3/iconify-icon.min.js
https://cdn.quilljs.com/1.3.6/quill.js
https://quick-rx.com:7005/_content/Blazored.TextEditor/quill-blot-formatter.min.js
https://quick-rx.com:7005/_content/Blazored.TextEditor/Blazored-BlazorQuill.js
https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js
https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.0.1/chart.umd.js
https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-datalabels/2.2.0/chartjs-plugin-datalabels.min.js
https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js
https://quick-rx.com:7005/_content/Blazor.Bootstrap/blazor.bootstrap.js
https://t.fngservices.com/tracker.js
https://quick-rx.com:7005/_content/Syncfusion.Blazor.Core/scripts/syncfusion-blazor.min.js
```

### All Stylesheets
```
https://quick-rx.com:7005/css/app.css
https://quick-rx.com:7005/RetailMyMeds.Client.styles.css
https://fonts.googleapis.com/css?family=Poppins:300,400,500,600,700
https://quick-rx.com:7005/assets/plugins/custom/fullcalendar/fullcalendar.bundle.css
https://quick-rx.com:7005/assets/plugins/custom/datatables/datatables.bundle.css
https://quick-rx.com:7005/assets/plugins/global/plugins.bundle.css
https://quick-rx.com:7005/assets/css/style.bundle.css
https://quick-rx.com:7005/_content/Radzen.Blazor/css/default-base.css
https://quick-rx.com:7005/_content/Blazored.Modal/blazored-modal.css
https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap
https://fonts.googleapis.com/icon?family=Material+Icons
https://quick-rx.com:7005/_content/BlazorCalendar/BlazorCalendar.css
https://cdn.quilljs.com/1.3.6/quill.snow.css
https://cdn.quilljs.com/1.3.6/quill.bubble.css
https://quick-rx.com:7005/_content/Blazorise.Icons.FontAwesome/v6/css/all.min.css
https://quick-rx.com:7005/_content/Blazorise/blazorise.css?v=1.8.9.0
https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/css/bootstrap.min.css
https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css
https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css
https://quick-rx.com:7005/_content/Blazor.Bootstrap/blazor.bootstrap.css
https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,100;0,300;0,400;0,700;0,900;1,100;1,300;1,400;1,700;1,900&display=swap
https://quick-rx.com:7005/_content/Syncfusion.Blazor.Themes/bootstrap5.css
```

### Dashboard Feature Clues (from script filenames)
- `chat.js` -- in-app messaging/chat system
- `upgrade-plan.js` -- tiered subscription/upgrade flow
- `create-campaign.js` -- campaign creation (outreach?)
- `users-search.js` -- user directory/search
- `widgets.js` -- dashboard widgets
- `fullcalendar` -- scheduling/calendar view
- `datatables` -- tabular data display
- `Chart.js` -- data visualization/charts
- `SortableJS` -- drag-and-drop list ordering
- `Quill.js` -- rich text editing (notes? communications?)
- `intro.js` -- onboarding/tutorial walkthrough

---

## Technical Architecture

### Summary
The RMM operation runs on two completely separate tech stacks:

**Marketing/Enrollment Site (retailmymeds.com):**
- Wix Thunderbolt + Velo
- Built by ThatWasEZ (Kevin McCarron + Chris Whelan)
- Handles: marketing, enrollment forms, case study distribution, FAQs
- Registered on GoDaddy

**Product Dashboard (quick-rx.com:7005):**
- Blazor WebAssembly (.NET/C#)
- Commercial UI components (Syncfusion -- requires paid license)
- Built by unknown developer(s)
- Handles: actual pharmacy workflow, prescription coordination, analytics, chat, campaigns
- Hosted on quick-rx.com infrastructure
- Domain registered to 2955 Cleveland Rd Ste C, Dalton, GA 30721

### What We Don't Know
1. Who built the Blazor dashboard? (Not ThatWasEZ -- different tech stack entirely)
2. Where does prescription data come from? (PMS integration? Manual entry? PBM remittance data?)
3. How are mail-order transfers coordinated? (Automated? Manual fax/call?)
4. Which mail-order pharmacies do they work with?
5. What does the dashboard actually look like behind login?
6. What is fngservices.com? (analytics tracker on dashboard, no public info found)
7. Is there a mobile app?
8. How many total member pharmacies beyond the 4 case study stores?

---

## ThatWasEZ

**URL:** https://www.thatwasez.com/about
**Platform:** Wix

### Co-Founders

**Kevin McCarron**
- Business development guide, digital craftsman, designer, project leader
- 20+ years experience
- "I am a design practitioner with a conscious focus on user experience, creative/content balance, and measurable goal achievement."

**Chris Whelan**
- Marketing strategist, market analyst, writer, product developer, SEO and PPC expert
- Gets clients in front of prospects with messaging that engages
- "We are in this life and world for the one purpose of connecting for good."

### Background
- Both worked together mostly in WordPress before finding Wix
- ThatWasEZ focuses on Wix-based websites and marketing
- Makes websites "truly customized and accountable to business objectives"
- Copyright 2021

### Relationship to RMM
- Built and maintains retailmymeds.com (Wix site)
- Kevin is Matthew's primary contact for the RMM engagement
- Kevin wants involvement and ownership in the technical direction
- Kevin identified Velo as the integration path for qualification forms
- Did NOT build the Blazor WebAssembly dashboard -- completely different skillset

---

## quickrx.com

**URL:** https://www.quickrx.com/
**Platform:** Digital Pharmacist (pharmacy website builder)
**Patient Portal:** RxLocal (PioneerRx ecosystem)

### Quick Pharmacy (Round Rock, TX)

| Detail | Value |
|--------|-------|
| Owner | Gilbert R. Sarmiento, PharmD (purchased 2023 with wife Randi) |
| Address | 701 E Palm Valley Blvd, Round Rock, TX 78664 |
| Phone | 512-255-2144 |
| Fax | 512-255-2422 |
| Hours | Mon-Fri 9a-6p, Sat 9a-1p, Sun closed |
| Claim | "Williamson County's #1 trusted compounding pharmacy for over 100 years" |

### Services
- Medication Therapy Management
- Medication Synchronization
- Most Insurance Plans Accepted
- Home Delivery (Round Rock area)
- Compounding (100+ years)
- Immunizations
- Over the Counter
- Medication Adherence

### Testimonials
- Doug W. -- "always professional, extremely helpful, super-nice"
- Veronica M. -- "pharmacists always make sure to go over medications, even on busiest days"

### Key Links from Site
- Refill: patient.rxlocal.com/onboarding/index (RxLocal)
- Terms: digitalpharmacist.com/patient-terms-conditions/
- Site credit: "Pharmacy website and mobile app provided by [Digital Pharmacist]"

### Connection to RMM
- The quick-rx.com domain hosts the RMM dashboard on port 7005
- The pharmacy website (port 80/443) is completely separate from the dashboard
- Gilbert Sarmiento is in Round Rock, TX; the WHOIS address is Dalton, GA
- No visible mention of RetailMyMeds on the quickrx.com pharmacy site
- Both Quick Pharmacy and White's Pharmacy (Dalton) use RxLocal (PioneerRx ecosystem)

---

## White's Pharmacy / Dalton GA

### The WHOIS Connection
The domain `quick-rx.com` is registered to:
```
2955 Cleveland Rd Ste C
Dalton, GA 30721
```

### White's Pharmacy of Dalton, LLC

| Detail | Value |
|--------|-------|
| Address | 2955 Cleveland Rd **Suite B**, Dalton, GA 30721 |
| Phone | (706) 259-9707 |
| Fax | (706) 259-2278 |
| In business since | 1991 (33 years) |
| Pharmacists | Dr. John White, Dr. Chris Sams, Dr. Ann Mathis |
| Affiliation | HealthMart |
| NPI | 1518018290 |
| Patient platform | RxLocal (same as Quick Pharmacy) |
| Services | Medicaid, immunizations, delivery, DME |

### The Address (2955 Cleveland Rd, Dalton, GA 30721)
Multi-tenant commercial property housing:
- Suite B: White's Pharmacy
- Suite C: quick-rx.com domain registrant (unknown entity)
- Also at this address: Gettin Piggy Wit It BBQ, GameChangerU Gym, Varnell Medical Center, Classic Cleaners, Tasty J's

### Significance
- quick-rx.com registered to Suite C, White's Pharmacy in Suite B -- same building, adjacent suites
- White's Pharmacy is likely an RMM member store (Southeast region, fits case study profile)
- Someone at this address (Suite C) likely hosts the Blazor dashboard infrastructure
- No public evidence directly linking White's Pharmacy to RetailMyMeds
- Both pharmacies in this investigation (Quick Pharmacy TX, White's Pharmacy GA) use RxLocal/PioneerRx

---

## Key People

| Person | Role | Location | Connection |
|--------|------|----------|------------|
| **Dr. Arica Collins, PharmD** | President & CEO, RetailMyMeds LLC | Albany, KY 42602 | Business owner, pharmacy domain expert, face of RMM. Pharmacy owner since 2008 |
| **Kevin McCarron** | Co-founder, ThatWasEZ | Unknown | Built retailmymeds.com (Wix). Matthew's primary contact. Wants involvement/ownership |
| **Chris Whelan** | Co-founder, ThatWasEZ | Unknown | Marketing strategy, SEO/PPC, copywriting for RMM site |
| **Unknown .NET developer** | Built Blazor dashboard | Likely Dalton, GA area | Created the actual product. Uses Syncfusion (paid), Radzen, full commercial stack |
| **Gilbert R. Sarmiento, PharmD** | Owner, Quick Pharmacy | Round Rock, TX | Owns quickrx.com domain (pharmacy site). Dashboard hosted on his domain's port 7005 |
| **Dr. John White** | White's Pharmacy | Dalton, GA | Pharmacy at same address as quick-rx.com WHOIS registrant (adjacent suite) |
| **Dr. Chris Sams** | White's Pharmacy | Dalton, GA | Pharmacist at White's |
| **Dr. Ann Mathis** | White's Pharmacy | Dalton, GA | Pharmacist at White's |

---

## Domain Intelligence

### retailmymeds.com
| Field | Value |
|-------|-------|
| Registrar | GoDaddy |
| Nameservers | PDNS05/06.DOMAINCONTROL.COM (pointing to Wix) |
| Expiry | July 14, 2027 |
| Last updated | July 15, 2025 |
| Status | clientTransferProhibited, clientUpdateProhibited, clientRenewProhibited, clientDeleteProhibited |

### quick-rx.com
| Field | Value |
|-------|-------|
| Registrar | web.com (Network Solutions) |
| Nameservers | NS83/84.WORLDNIC.COM |
| Expiry | May 20, 2026 |
| Last updated | March 21, 2024 |
| Status | clientTransferProhibited |
| **Registrant address** | **2955 Cleveland Rd Ste C, Dalton, GA 30721** |

---

## Pricing Discrepancy

| Source | Price Stated |
|--------|-------------|
| About Us page (/about-us) | $175/month |
| FAQ page (/blank) | $275/month ($225/month for 5+ stores) |
| Terms & Conditions | "Governed by Primary Agreement" (individual contract) |

The FAQ page is more detailed and likely current. The About Us page is probably stale. The actual price may vary by individual enrollment contract per the Terms.

---

## Analysis & Conclusions

### What RMM Is
A subscription SaaS for independent pharmacies that identifies net-negative prescriptions (ones the pharmacy loses money filling) and coordinates transferring them to mail-order pharmacies. The pharmacy stops losing money on those scripts, and RMM takes a flat monthly fee. They are not a PBM, not a mail-order pharmacy, and don't retain prescriptions.

### The Product is Real and Working, But the Operation is Small
Four test stores, a $275/month subscription, a support line 8:30-5 CT weekdays. Case study data shows genuine results -- pharmacies avoiding hundreds of thousands in acquisition costs. But the infrastructure (pricing inconsistency, FAQs at `/blank`, case study as a single PDF image) says lean operation grown from Arica's pharmacy expertise, not a product team.

### The Technical Side Has More Depth Than Expected -- But It's Opaque
Someone built a serious Blazor WebAssembly application with paid Syncfusion components, Chart.js dashboards, DataTables, a calendar, chat, rich text editing, campaign creation, and upgrade plan modals. That's not Kevin and Chris (their skill is Wix sites and marketing). There's an unknown .NET developer in the picture, likely connected to the Dalton, GA / White's Pharmacy address. This person (or small team) is the technical backbone of the actual product.

### Kevin's Position is More Interesting Than It First Appeared
He's not "a developer helping RMM." He co-owns the agency that controls RMM's web presence, and he's the one who brought Matthew in. He wants involvement and ownership. He identified Velo as the integration path. But the real product -- the dashboard where pharmacies actually work -- is a .NET application that Kevin's agency didn't build and probably doesn't maintain. Kevin's leverage is the front door (marketing site, enrollment flow, CRM). The back door (the actual analytics engine) belongs to someone else.

### Our Pharmacy Qualification Data Fills a Visible Gap
RMM's site has a contact form (name, phone, NPI, single/multi pharmacy) and a case study PDF. That's their entire top-of-funnel. There's no targeting, no segmentation, no pre-qualification. A pharmacy finds them, fills out the form, gets an onboarding call. The 41,775-pharmacy dataset with scoring, GLP-1 targeting, and geographic segmentation is the piece they don't have -- a way to go find pharmacies instead of waiting for pharmacies to find them.

### The Question for the Arica Meeting is Who Controls What
The Blazor dashboard developer, the data pipeline (where does net-negative prescription data come from?), the mail-order pharmacy relationships, the PioneerRx/RxLocal connection across member stores -- these are the load-bearing walls. Arica owns the methodology and the business. Kevin owns the marketing surface. Someone else owns the technical product. Understanding that power structure determines where our work actually plugs in and how durable the relationship is.

### Questions to Ask in the Arica Meeting
1. "Walk us through what happens when a pharmacy enrolls -- what systems touch what?" (reveals full tech pipeline)
2. "When the LPCS opens the dashboard in the morning, what are they looking at?" (gets at data sources, UI, workflow)
3. "How does the system know a script is net-negative?" (reveals PBM data feeds, manual entry, or PMS integrations)
4. "Who keeps the technical platform running?" (identifies the .NET developer/team)
5. "How are you currently finding new pharmacies to enroll?" (establishes baseline for our data's value)
6. "Which states are you operating in?" (maps to our geographic targeting data)

### RMM Operation Structure (at least 4 parties)
1. **Arica Collins** (Albany, KY) -- business owner, pharmacy domain expert, methodology creator
2. **Kevin McCarron + Chris Whelan / ThatWasEZ** -- Wix marketing site, business development, enrollment flow
3. **Unknown .NET developer** (connected to Dalton, GA) -- built the actual Blazor dashboard product
4. **White's Pharmacy / quick-rx.com infrastructure** (Dalton, GA) -- likely early adopter/test store, hosts dashboard

---

---

# PART 2: PRE-MEETING RESEARCH (February 18, 2026)

Research conducted via parallel web search agents to prepare for the Arica Collins meeting.

---

## 19. Dr. Arica Collins -- Full Background Profile

### Personal & Professional Identity

| Field | Value |
|-------|-------|
| Full Name | Arica V. Conner Collins, PharmD |
| Title | President/CEO of RetailMyMeds LLC; Pharmacy Owner & Pharmacist-in-Charge at Dyer Drug Company |
| Location | Albany, KY 42602 (Clinton County native) |
| Email Domain | dyerdrug.com (per ZoomInfo: a***@dyerdrug.com) |
| LinkedIn | https://www.linkedin.com/in/arica-collins-6296a08b |
| Doximity | https://www.doximity.com/pub/arica-collins-pharmacist-b4f1a037 |

### Education
- **Degree:** Doctor of Pharmacy (PharmD)
- **School:** Purdue University College of Pharmacy, West Lafayette, Indiana
- **Graduation:** Likely ~2007-2008 (purchased Dyer Drug in September 2008, described as "Purdue College of Pharmacy graduate" at time of purchase)

### Career Trajectory

**Pre-ownership (Kroger):** Before purchasing Dyer Drug, Arica progressed through multiple roles at Kroger, advancing from Pharmacy Technician to Pharmacy Intern to Pharmacy Manager. She worked her way up from the technician level through school and into management at a large chain before going independent.

**Dyer Drug Acquisition (September 2008):** Purchased Dyer Drug Company, becoming the first owner outside the Dyer family in the pharmacy's 92-year history. She has now been a pharmacy owner for approximately 17-18 years.

**RetailMyMeds Founding (2021):** Founded RetailMyMeds LLC after experiencing firsthand the financial pressures of independent pharmacy ownership -- particularly around PBM reimbursement, DIR fees, and net-negative prescriptions. She describes it as a "passion project."

**Weight Loss Clinic Co-Founder (January 2019):** Co-founded "The Doctor's Health and Weight Loss Clinic" in Albany, KY alongside Dr. Carol Peddicord, MD. By October 2019, the clinic had served 433 patients who collectively lost 4,078.75 pounds.

### Dyer Drug Company

| Field | Value |
|-------|-------|
| Entity Name | Central Kentucky Apothecary, LLC DBA Dyer Drug |
| NPI (Organization) | 1497754923 |
| NPI (Individual -- Arica Collins) | 1518439678 |
| Address | 100 E Cumberland Street, Albany, KY 42602 |
| Phone | (606) 387-6444 |
| Fax | (606) 387-9224 |
| Email | dyerdrugky@live.com |
| Website | https://dyerdrugky.com/ |
| KY License | P07288 |
| NPI Enumeration Date | July 18, 2005 |
| Authorized Official | Arica V. Collins, Pharm.D., President/CEO/Owner |

**Pharmacy History:**
- Founded 1916 by Cincinnati College of Pharmacy graduate James F. Dyer
- 1943: William "Bill" DeForest joined as staff pharmacist
- September 2008: Sold to Arica Conner Collins -- first non-Dyer family owner in 92 years
- Now 110 years in continuous operation

**Taxonomy/Classification:**
- Primary: Community/Retail Pharmacy (3336C0003X)
- Secondary: Pharmacy (333600000X)
- Tertiary: Durable Medical Equipment & Medical Supplies (332B00000X)

**Services:** Conventional prescriptions, compounding, medication synchronization, specialty pharmacy (HIV/AIDS, Hep C, oncology, RA, MS), clinical services (flu/shingles/pneumonia/COVID vaccinations, diabetes management, smoking cessation), diagnostics (BP, cholesterol, A1C, COVID, flu, strep), curbside pickup, delivery, drive-thru, DME, Medicare open enrollment counseling, adherence packaging, comprehensive medication reviews.

### RetailMyMeds LLC

| Field | Value |
|-------|-------|
| Registered Name | Retailmymeds.com, LLC |
| State | Kentucky |
| Organization Number | 1159623 |
| Filing Date | July 16, 2021 |
| Status | Active, Good Standing |
| Registered Agent | Amonett Bookkeeping |
| Address | 104 E Cumberland St, Albany, KY 42602 (4 doors from Dyer Drug at 100 E Cumberland) |

**Origin Story:** Arica experienced a specialty drug that cost $20,000, totally drained cash flow, and resulted in a net loss of $200 on that single claim. This was the catalyst for building RetailMyMeds.

### Media & Industry Presence

**Podcast:** "Discover New Revenue with Retail My Meds" -- TWIRx episode on the Pharmacy Podcast Network, September 20, 2024 (55 min 51 sec). Guest: Wyatt Walker, PharmD, pharmacy owner of Walker's Pharmacy in Livonia, LA.
- Podbean: https://pharmacypodcastnetwork.podbean.com/e/discover-new-revenue-with-retail-my-meds-twirx/
- Spotify: https://open.spotify.com/episode/1yd2kyB9hpWdHlRNl6vCpV

**News:** Kentucky Health News (Oct 24, 2019) -- "Albany weight loss clinic sees big results with old-fashioned methods" featuring Arica Collins and Dr. Carol Peddicord.

**Industry:** Sykes & Company CPA article: "How to Recover Lost Profit in Your Pharmacy" -- explicitly endorses RMM.

**Sponsorship:** West Virginia Independent Pharmacy Association (WVIPA) -- RetailMyMeds is a sponsor (https://www.wvipa.org/wvipa-sponsors/retailmymeds)

### Association Memberships
- **NCPA** (National Community Pharmacists Association) -- confirmed via RxLocal Pharmacy Finder
- **WVIPA** -- RetailMyMeds is a sponsor
- KPhA (likely but not confirmed)

### Albany, KY Market Context
- County seat of Clinton County
- Population: 1,738 (2026 est.), declining
- County population: ~9,183
- Median household income: $42,168-$44,007
- 4 pharmacies serving the county (~2,300 residents per pharmacy)
- Rural Appalachian-adjacent with significant health disparities (obesity, diabetes)

### Key Takeaways for the Meeting
1. She is a practitioner first. 17+ years owning Dyer Drug in a tiny rural market. Independent pharmacy economics from the inside -- not consulting or theory.
2. She built RetailMyMeds out of personal pain ($20k specialty drug / $200 net loss).
3. Clinton County native who came back home. Bought a 92-year-old institution.
4. Moves laterally: weight loss clinic, podcast, WVIPA sponsorship, SaaS dashboard.
5. Her pharmacy serves a medically vulnerable population.
6. RetailMyMeds has real industry traction: podcast feature, WVIPA sponsorship, CPA firm endorsement, testimonial user.

### Sources
- https://dyerdrugky.com/about-us/
- https://www.doximity.com/pub/arica-collins-pharmacist-b4f1a037
- https://www.linkedin.com/in/arica-collins-6296a08b
- https://www.zoominfo.com/p/Arica-Collins/1880757304
- https://npiregistry.cms.hhs.gov/provider-view/1497754923
- https://npino.com/pharmacy/1497754923-dyer-drug/
- https://opencorporates.com/companies/us_ky/1159623
- https://www.kycompanydir.com/companies/retailmymedscom-llc/
- https://www.wvipa.org/wvipa-sponsors/retailmymeds
- https://pharmacypodcastnetwork.podbean.com/e/discover-new-revenue-with-retail-my-meds-twirx/
- https://kyhealthnews.net/2019/10/24/albany-weight-loss-clinic-sees-big-results-with-old-fashioned-methods-eat-better-food-less-of-it-and-exercise/
- http://clintonnews.net/pages/?p=17248
- https://www.sykes-cpa.com/unleash-profitability-recover-lost-profit-from-net-negative-prescriptions/
- https://pharmacyfinder.rxlocal.com/pharmacyFinder/ky/albany/dyer-drug-co
- https://worldpopulationreview.com/us-cities/kentucky/albany
- https://www.kentucky-demographics.com/clinton-county-demographics

---

## 20. Competitive Landscape Analysis

### Finding: RMM Occupies an Uncontested Niche

After extensive searching, there is no other company offering a subscription service specifically designed to identify net-negative prescriptions and coordinate their transfer to mail order while retaining the patient at the retail pharmacy. This is a genuinely novel niche.

### What "Mail to Retail" Is

"Mail to Retail" is RetailMyMeds' own branding for its core program concept -- not a separate company or external partner. The name refers to the value proposition: the retail pharmacy becomes the coordination hub and patient-facing touchpoint, while mail order handles fulfillment. "Mail to Retail" = "bringing the mail-order coordination capability INTO the retail pharmacy."

### Category 1: Pharmacy Profitability Analytics (Identify the Problem, Don't Solve It)

| Company | What | How It Compares to RMM |
|---------|------|----------------------|
| **Stratos Insights** (Edmond, OK) | Pharmacy BI dashboards -- claim-level profitability, DIR fee tracking, adherence metrics | Shows the problem. RMM shows the problem AND provides the workflow to fix it. Complementary. |
| **EnlivenHealth** (Omnicell) | Claims reconciliation, payer profitability, adherence tracking | Reconciliation tool, not redirection tool. Complementary. |
| **Datascan (WinPharm)** | PMS with integrated DIR fee estimator, real-time per-script warnings | Flags losing scripts before fill. Doesn't provide the "what to do" workflow. Complementary. |
| **PioneerRx** (RedSail Technologies) | Leading PMS with profit reports factoring DIR/GER fees | Same as Datascan -- shows profitability but doesn't coordinate mail-order transfer. Complementary. |

### Category 2: Pharmacy Consulting Firms (Advise on the Problem)

| Company | What | How It Compares to RMM |
|---------|------|----------------------|
| **Sykes & Company CPA** (Ollin Sykes) | CPA firm specializing in independent pharmacy | **Active referral partner.** Wrote the blog post promoting RMM. Ally, not competitor. |
| **Independent Rx Consulting** | Pharmacy-specific accounting, data dashboards | Identifies problem via accounting. Potential referral partner. |
| **Waypoint Rx** | Comprehensive consulting -- profitability, succession, insurance | Broader strategy. Could recommend RMM as part of profitability plan. |

### Category 3: Education/Membership Communities

| Company | What | How It Compares to RMM |
|---------|------|----------------------|
| **DiversifyRx / Pharmacy Badass University** | Membership community, coaching, "6 Pillars of Pharmacy Profitability" | Teaches HOW to think about profitability. RMM provides a tool to ACT on it. Complementary. |

### Category 4: Purchasing Optimization (Reduce COGS)

| Company | What | How It Compares to RMM |
|---------|------|----------------------|
| **ProfitGuard** (PBA Health) | GPO + purchasing optimization tool, avg 6% savings on volume | Reduces acquisition cost. RMM avoids filling drugs that lose money regardless. Different lever. |
| **SureCost** | Purchasing and inventory management, 1,600+ pharmacies | Purely purchasing. Complementary. |

### Category 5: PSAOs and Networks (Upstream Fix)

| Company | What | How It Compares to RMM |
|---------|------|----------------------|
| **PSAOs** (McKesson/Health Mart, Cardinal, ABC) | Negotiate PBM contract terms. 83% of independents use one. | Try to prevent the problem. RMM deals with what remains after PSAO negotiations. |
| **CPESN** | Clinically integrated networks, medical-side revenue | Creates new revenue streams. RMM optimizes dispensing revenue. Different strategy. |

### Category 6: Mark Cuban Cost Plus Drugs

Cost Plus addresses acquisition cost for GENERICS ($drug + 15% + $5). RMM addresses reimbursement below cost regardless of sourcing. For expensive brands (like the $20K specialty drug), Cost Plus doesn't apply. Different problem, some overlap on generics.

### Competitive Positioning Summary Table

| Company | Identifies Net-Negative Scripts? | Provides Mail-Order Coordination? | Price | Relationship to RMM |
|---------|--------------------------------|----------------------------------|-------|---------------------|
| **RetailMyMeds** | Yes | **Yes** (core feature) | $275/mo | -- |
| Stratos Insights | Yes | No | Fee-for-service | Complementary |
| EnlivenHealth | Partially | No | Via cooperatives | Complementary |
| Datascan (WinPharm) | Yes (real-time) | No | $200-800/mo (full PMS) | Complementary |
| PioneerRx | Yes | No | PMS pricing | Complementary |
| Sykes CPA | Yes (via accounting) | No | Consulting fees | **Active referral partner** |
| DiversifyRx | Teaches concept | No | Membership tiers | Complementary |
| ProfitGuard (PBA) | No | No | With membership | Complementary |
| PSAOs | No | No | With membership | Upstream fix |
| Cost Plus Drugs | No | N/A (IS the mail order) | N/A | Partially complementary |

### Key Takeaway

RMM occupies a genuinely uncontested niche. Many companies help pharmacies SEE they're losing money. Many help NEGOTIATE better rates or REDUCE acquisition costs. But no other company provides the operational workflow of: "identify the losers, coordinate their transfer to mail order, keep the patient, stop the bleeding."

The risk is not from current competitors but from pharmacy management systems (PioneerRx, Datascan, BestRx) potentially adding a "redirect to mail order" workflow on top of their existing per-script profitability reporting. But coordinating across multiple mail-order pharmacies with different requirements is operationally complex enough to be a defensible moat for now.

### Sources
- https://www.stratosinsights.com/services/
- https://www.enlivenhealth.co/insights-outcomes/pharmacy-analytics-intelligence
- https://datascanpharmacy.com/what-are-dir-fees-why-do-they-exist-and-what-can-we-do-about-them/
- https://www.pioneerrx.com/blog/7-pioneerrx-features-to-grow-your-pharmacys-profitability
- https://www.sykes-cpa.com/unleash-profitability-recover-lost-profit-from-net-negative-prescriptions/
- https://diversifyrx.com/the-pharmacy-profit-matrix/
- https://www.pbahealth.com/elements/these-networks-break-pharmacies-into-the-lucrative-side-of-healthcare/
- https://www.surecost.com/smarter-purchasing-report
- https://cpesn.com/
- https://www.pcmanet.org/pharmacy-services-administrative-organizations-psaos-and-their-little-known-connections-to-independent-pharmacies/
- https://www.waypointus.com/waypoint-rx
- https://independentrxconsulting.com/pharmacy-accounting-data-services/
- https://www.costplusdrugs.com/
- https://www.wvipa.org/wvipa-sponsors/retailmymeds
- https://ncpa.org/sites/default/files/2025-01/1.27.2025-FinalExecSummary.NCPA_.MemberSurvey.pdf
- https://www.cardinalhealth.com/en/services/retail-pharmacy/resources-for-pharmaceutical-distribution/ncpa-digest.html
- https://www.drugtopics.com/view/glp-1s-present-profitability-challenges-to-independent-pharmacies-aap-2025

---

## 21. PioneerRx, RxLocal, and Independent Pharmacy Software Ecosystem

### PioneerRx -- What It Is

PioneerRx is a pharmacy management system (PMS) -- the core software that independent pharmacies use to process prescriptions, manage inventory, handle claims adjudication, track patients, and run their entire dispensing workflow. It is the most installed independent pharmacy software in the United States.

### Ownership

Owned by **RedSail Technologies, LLC**, backed by **Francisco Partners** (private equity). RedSail acquired PioneerRx in December 2020.

**RedSail brand portfolio:**
- PioneerRx (flagship), BestRx (budget), QS/1 (retail/hospital), NRx, PrimeCare (LTC), Axys LTC, PowerLine, TransactRx (claims), Emporos (POS), RxMile
- Combined: **12,000+ pharmacies**

**Antitrust (Dec 2025):** DOJ actively weighing challenge to RedSail's proposed acquisition of Micro Merchant Systems (PrimeRx), which would further consolidate the independent pharmacy software market. Not yet resolved.

### Market Share

- PioneerRx: 5,000+ installations as of Feb 2023 (most recent public milestone)
- #1 most-installed independent pharmacy software
- Highest customer satisfaction score (Direct Opinions study)
- ~18,984 independent pharmacies in US (June 2024, NCPA)
- PioneerRx at ~26%+ market share

### Financial Data PioneerRx Tracks

**Per-prescription:**
- Acquisition cost (what pharmacy paid)
- Amount adjudicated by third parties (what PBM/insurer paid)
- Copay amounts
- Gross profit per prescription
- DIR/GER fee estimates
- NDC codes, days supply, refill counts

**Key Reports:**
1. Rx Transaction Summary by Submission Type -- claims by date, adjudicated amount, copay, acquisition cost, gross profit by payer
2. Daily Summary -- top 10 and **bottom 10 prescriptions** (identifies underwater scripts)
3. Basis of Reimbursement Summary -- how scripts are reimbursed, low-paying plans
4. Profit Report -- can factor in estimated DIR/GER fees
5. Cash Pricing Estimator -- based on chain competitors nearby

### PioneerRx API Ecosystem (Critical for RMM Integration)

PioneerRx has 7 documented APIs:

| API | Purpose | Key Data |
|-----|---------|----------|
| **Enterprise API** (v1.8.3, July 2025) | Custom workflow integrations | Patient demographics, prescriptions, insurance, financial data, prescriber info |
| **Rx Event API** | Real-time prescription event streaming | Prescription details transmitted in real-time based on configurable system events |
| **Patient Data Exchange API** | Bidirectional patient data sync | Patient onboarding, updates, synchronization |
| **POS Universal API** | Third-party POS integration | RxQuery (query Rx info), RxComplete (submit sales) |
| **MTM Action Incoming API** | Medication Therapy Management | Submit MTM actions with status, due dates, completion |
| **MTM SSO Extension** | Single sign-on for MTM vendors | Automatic user auth into vendor systems |
| **Patient Data Exchange SSO** | SSO for patient data | Automatic auth via profile_url parameter |

**Enterprise API Authentication:** HMAC signature-based with three headers:
- `prx-api-key` -- enrollment identifier (provided by PioneerRx)
- `prx-timestamp` -- UTC ISO format
- `prx-signature` -- SHA512 hash of timestamp + shared secret, UTF-16-LE encoded, Base64 output

**Key Enterprise API Endpoints:**
- `/api/enterprise/IsAuthenticated` -- validate auth
- `/api/enterprise/method/list` -- self-documenting method list
- `/api/enterprise/method/process` -- production calls
- `/api/enterprise/method/test/process` -- test database
- `/api/enterprise/method/validate` -- parameter validation
- `/api/enterprise/method/sample` -- mock data generation

**Accessible Data:**
- GetPatient -- demographics, allergies, conditions, medications, insurance, payment methods, AR records
- GetPatientProfile -- active prescriptions with refill counts, dispensing history, days supply, therapeutic classifications
- SearchPatient -- filter by name, DOB, phone, address, external IDs
- Prescription records -- Rx number, status, fill history, NDC codes, DEA scheduling, **payment method and cost data**
- Financial/Insurance -- BIN, PCN, group numbers, billing order, **acquisition costs and pricing**

**Connected Vendor Program:** 80+ connected vendors across 31 categories. Apply via Vendor Integration Inquiry Form. Contact: PioneerRxDataPrograms@PioneerRx.com

### RxLocal -- Patient Engagement Platform

RxLocal is PioneerRx's patient-facing layer. Features:
- Patient profile, prescription info, refill requests, pickup reminders
- HIPAA-compliant two-way messaging with pharmacist
- Medication reminders, family medication management
- **Partner Network** -- connects community pharmacies with specialty pharmacies within PioneerRx
- **Pharmacy Finder** -- SEO profiles for independent pharmacies
- **Deep Linking API** -- third-party apps can deep-link into RxLocal mobile app

RxLocal is exclusively for PioneerRx pharmacies (for full feature set).

### Digital Pharmacist (Separate from PioneerRx)

Digital Pharmacist is a **software-agnostic** digital engagement platform (now owned by AnewHealth via Lumistry). Serves 9,000+ pharmacies globally. Works with any PMS. Competes with RxLocal but serves a broader market.

### HealthMart

McKesson's independent pharmacy franchise (~5,000 locations). **Not a software company.** Provides branding, managed care access (Health Mart Atlas PSAO), marketing, training, McKesson wholesale pricing. **Software-agnostic** -- Health Mart pharmacies can run any PMS (PioneerRx, Liberty, Rx30, etc.).

### Pharmacy Management System Market

| Rank | Software | Owner | Est. Pharmacies | Notes |
|------|----------|-------|----------------|-------|
| 1 | PioneerRx | RedSail (Francisco Partners) | 5,000+ | Most installed, highest satisfaction |
| 2 | Rx30 | Transaction Data Systems (TDS) | ~3,000-4,000 | Shares ownership with Computer-Rx |
| 3 | PrimeRx | TA Associates | ~3,000+ | DOJ reviewing RedSail acquisition |
| 4 | Computer-Rx | TDS | ~2,000-3,000 | Paired with Rx30 under TDS |
| 5 | Liberty Software | Independent | Growing | Absorbed McKesson Pharmaserv refugees |
| 6 | BestRx | RedSail | ~1,000+ | Budget option in RedSail portfolio |
| 7 | QS/1 | RedSail | Significant | Retail community, hospital outpatient |

### Integration Paths for RetailMyMeds

**Path 1 -- PioneerRx Connected Vendor (Preferred):**
1. Apply via Vendor Integration Inquiry Form
2. Get provisioned API access (Enterprise API + Rx Event API)
3. Pull active prescriptions with cost data via GetPatientProfile
4. Cross-reference acquisition cost vs adjudicated amount to compute per-script profitability
5. Factor in estimated DIR/GER fees
6. Build scoring/flagging layer in RetailMyMeds

**Path 2 -- Excel/CSV Export (Manual, No API):**
PioneerRx allows grid/column export to Excel/PDF. Pharmacy exports Rx Transaction Summary or Profit Report, uploads to RMM. Lower-tech but immediate.

**Path 3 -- Multi-PMS via NCPDP Standards (Long-term):**
Build to industry data exchange standards (NCPDP) for interoperability beyond just PioneerRx.

**Technical Note for Blazor:** Enterprise API is standard HTTPS REST with JSON payloads -- fully compatible with Blazor WASM HttpClient. However, HMAC signing must be server-side (shared secret can't be exposed in WASM). A backend API proxy (ASP.NET, Azure Function) would handle PioneerRx auth.

### Sources
- https://support.pioneerrx.com/apidoc/
- https://support.pioneerrx.com/apidoc/PioneerRxEnterpriseAPI/
- https://www.pioneerrx.com/connected-vendors
- https://www.pioneerrx.com/blog/want-to-earn-more-start-by-tracking-these-14-pharmacy-kpis
- https://www.pioneerrx.com/blog/six-financial-reports-you-should-be-running
- https://www.pioneerrx.com/blog/pioneerrx-expands-pharmacy-network-to-5-000-independent-pharmacies
- https://www.redsailtechnologies.com/press-releases/redsail-technologies-llc-buys-pioneerrx
- https://www.redsailtechnologies.com/our-brands
- https://www.rxlocal.com/patient-mobile-app
- https://www.rxlocal.com/blog/the-rxlocal-partner-network-is-now-available-in-pioneerrx
- https://deeplink.api.rxlocal.com/
- https://www.digitalpharmacist.com/
- https://lumistry.com/about/company/
- https://www.mckesson.com/pharmacy-management/health-mart-franchise/
- https://www.ainvest.com/news/doj-considers-blocking-redsail-primerx-merger-market-concentration-fears-2512/

---

## 22. Industry Economics Summary (DIR Fees, PBM Reform, Closures)

Full briefing saved separately: `~/Desktop/RetailMyMeds/pharmacy_economics_briefing_feb2026.md`

### Key Numbers for the Meeting

| Metric | Value | Source |
|--------|-------|--------|
| DIR fee growth (2010-2020) | 107,400% increase | CMS |
| Pharmacies reporting lower reimbursement after DIR reform | 99% | NCPA |
| Pharmacists losing money on 30%+ of scripts | 50%+ | NCPA Feb 2024 |
| Pharmacists losing money on GLP-1 fills | 95% | Drug Topics |
| Average GLP-1 loss per fill | >$37 per 30-day supply | NCPA |
| Independent pharmacies stopped stocking GLP-1s | 14% | NCPA |
| Independent pharmacies considering closing (2025) | 30.3% | NCPA Jan 2025 |
| Total pharmacy closures since Jan 2024 | 3,179+ | Economic Liberties Project |
| Independent pharmacy marketplace (2024) | $103 billion | NCPA 2025 Digest |
| Gross profit margin (2024) | 10-year low | NCPA 2025 Digest |
| Big Three PBMs (CVS Caremark, Express Scripts, OptumRx) market share | ~80% of all US prescriptions | Industry data |

### PBM Reform Act of 2026 (Signed Feb 3, 2026)

First major federal PBM reform in decades. Key provisions:
1. **100% rebate pass-through** -- PBMs must remit all rebates/fees/discounts to plan clients (quarterly, 90 days)
2. **Bona fide service fees only (2028)** -- PBM compensation must be flat-dollar, fair-market-value
3. **Any-willing-pharmacy (2029)** -- Any pharmacy meeting terms must be allowed into Part D networks
4. **Transparency reporting** -- Semiannual reporting on net spending, rebates, spread pricing, self-dealing
5. **CMS enforcement authority**

### FTC Express Scripts Settlement (Feb 4, 2026)
- Express Scripts must stop preferring high-list-price drugs when cheaper equivalents exist
- Must delink compensation from manufacturer list prices
- Expected $7 billion reduction in patient costs over 10 years
- CVS Caremark and OptumRx cases ongoing

### Sources
- https://www.pharmacytimes.com/view/pbm-reform-within-2026-appropriations-bill-signed-into-law
- https://www.mintz.com/insights-center/viewpoints/2146/2026-02-06-congress-passes-landmark-pbm-reform-2026-spending-bill
- https://ncpa.org/newsroom/news-releases/2026/02/03/ncpa-cheers-trump-signs-first-major-pbm-reform-decades
- https://www.economicliberties.us/press-release/326-pharmacies-have-closed-since-elon-musk-tanked-pbm-reform/
- https://www.drugtopics.com/view/independent-pharmacies-continue-to-face-financial-hardships-as-clock-ticks-on-pbm-reform
- Full briefing: ~/Desktop/RetailMyMeds/pharmacy_economics_briefing_feb2026.md

---

## 23. Strategic Synthesis -- What This Means for the Arica Meeting

### 1. Arica is not a consultant playing entrepreneur. She's a 17-year pharmacy owner who built RMM because she lost $200 on a $20,000 specialty claim. This is personal. Approach accordingly.

### 2. RMM has no real competitors. The niche is genuinely uncontested. Many companies help pharmacies see the problem (Stratos, EnlivenHealth, PioneerRx reports). Many help negotiate better rates (PSAOs). Nobody else provides the operational workflow of identifying net-negative scripts AND coordinating their mail-order transfer while keeping the patient.

### 3. The market timing is extraordinary. PBM Reform Act signed 15 days ago. FTC settlement with Express Scripts 14 days ago. 3,179+ pharmacy closures since Jan 2024. 30% of independents considering closing. 95% losing money on GLP-1s. The pain is acute, growing, and now politically visible.

### 4. PioneerRx's API is the technical integration path. The Enterprise API (v1.8.3) provides exactly the data RMM needs -- acquisition cost vs. adjudicated amount, per prescription. The Rx Event API can stream this in real-time. PioneerRx has 80+ connected vendors and is open to partnerships. 26%+ of independents run PioneerRx.

### 5. Our 41,775-pharmacy dataset is RMM's missing growth engine. RMM has no targeting, no pre-qualification, no outbound capability. A contact form and case study PDF are the entire top of funnel. The GLP-1 targeting data with scoring and geographic segmentation enables RMM to go find pharmacies instead of waiting for them to find RMM.

### 6. The meeting questions should be about operations, not sales. Arica needs to trust us through demonstrated understanding of her business. Ask about the enrollment workflow, what the LPCS sees daily, how net-negative scripts are identified, who runs the tech platform, what states she's in, and how she's currently finding pharmacies. These establish credibility and reveal where our work plugs in.

---

## Source URLs (Part 2)

### Arica Collins / Dyer Drug
- https://dyerdrugky.com/about-us/
- https://www.doximity.com/pub/arica-collins-pharmacist-b4f1a037
- https://www.linkedin.com/in/arica-collins-6296a08b
- https://www.zoominfo.com/p/Arica-Collins/1880757304
- https://npiregistry.cms.hhs.gov/provider-view/1497754923
- https://opencorporates.com/companies/us_ky/1159623
- https://www.wvipa.org/wvipa-sponsors/retailmymeds
- https://pharmacypodcastnetwork.podbean.com/e/discover-new-revenue-with-retail-my-meds-twirx/

### Competitive Landscape
- https://www.stratosinsights.com/services/
- https://www.enlivenhealth.co/insights-outcomes/pharmacy-analytics-intelligence
- https://datascanpharmacy.com/what-are-dir-fees-why-do-they-exist-and-what-can-we-do-about-them/
- https://www.pioneerrx.com/blog/7-pioneerrx-features-to-grow-your-pharmacys-profitability
- https://www.sykes-cpa.com/unleash-profitability-recover-lost-profit-from-net-negative-prescriptions/
- https://diversifyrx.com/the-pharmacy-profit-matrix/

### PioneerRx / RxLocal / Ecosystem
- https://support.pioneerrx.com/apidoc/
- https://support.pioneerrx.com/apidoc/PioneerRxEnterpriseAPI/
- https://www.pioneerrx.com/connected-vendors
- https://www.redsailtechnologies.com/our-brands
- https://www.rxlocal.com/patient-mobile-app
- https://deeplink.api.rxlocal.com/
- https://www.mckesson.com/pharmacy-management/health-mart-franchise/

### Industry Economics
- https://www.pharmacytimes.com/view/pbm-reform-within-2026-appropriations-bill-signed-into-law
- https://ncpa.org/newsroom/news-releases/2026/02/03/ncpa-cheers-trump-signs-first-major-pbm-reform-decades
- https://www.economicliberties.us/press-release/326-pharmacies-have-closed-since-elon-musk-tanked-pbm-reform/
- https://ncpa.org/sites/default/files/2025-01/1.27.2025-FinalExecSummary.NCPA_.MemberSurvey.pdf
- https://www.cardinalhealth.com/en/services/retail-pharmacy/resources-for-pharmaceutical-distribution/ncpa-digest.html
