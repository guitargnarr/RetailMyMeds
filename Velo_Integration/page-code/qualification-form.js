/**
 * RetailMyMeds Qualification Form - Page Code
 *
 * This file goes in: the page code panel of the qualification form page.
 *
 * SETUP: Kevin builds the form UI in Wix Editor with these element IDs.
 * This code handles step navigation, validation, submission, and results.
 *
 * ---------------------------------------------------------------
 * ELEMENT IDS (Kevin creates these in the Wix Editor)
 * ---------------------------------------------------------------
 *
 * CONTAINERS (MultiStateBox or show/hide groups):
 *   #step1, #step2, #step3, #step4, #step5
 *   #resultsSection
 *   #loadingOverlay
 *   #errorMessage
 *
 * STEP 1 - Your Pharmacy:
 *   #inputPharmacyName     (text input)
 *   #inputCity             (text input)
 *   #dropdownState         (dropdown - 50 states)
 *   #dropdownYears         (dropdown - Less than 5 / 5-10 / 10-20 / 20+)
 *
 * STEP 2 - Your Volume:
 *   #dropdownRxVolume      (dropdown - Under 2,000 / 2,000-3,999 / etc.)
 *   #dropdownGlp1Fills     (dropdown - I'm not sure / Under 100 / etc.)
 *   #dropdownGovPayer      (dropdown - Under 20% / 20-40% / etc.)
 *
 * STEP 3 - Your Systems:
 *   #dropdownPms           (dropdown - PioneerRx / Liberty / etc.)
 *   #dropdownTechnicians   (dropdown - 0 / 1 / 2 / 3-4 / 5+)
 *
 * STEP 4 - Your Situation:
 *   #radioUnderwaterRx     (radio group - Yes / No / I'm not sure)
 *   #radioMailOrder        (radio group - Yes / No)
 *   #radioDirFees          (radio group - Manageable / Significant squeeze / Threatening viability)
 *   #radioMfp              (radio group - Yes / No / I'm not sure)
 *
 * STEP 5 - Contact:
 *   #inputOwnerName        (text input)
 *   #inputEmail            (text input)
 *   #inputPhone            (text input)
 *
 * NAVIGATION:
 *   #btnNext1, #btnNext2, #btnNext3, #btnNext4  (next buttons per step)
 *   #btnBack2, #btnBack3, #btnBack4, #btnBack5  (back buttons per step)
 *   #btnSubmit                                    (final submit on step 5)
 *
 * PROGRESS:
 *   #progressBar           (progress bar element)
 *   #textStepLabel         (text: "Step 1 of 5")
 *
 * RESULTS:
 *   #textPharmacyName      (text)
 *   #textOverallGrade      (text - A/B/C/D)
 *   #textOverallScore      (text - 0-100)
 *   #textOverallLabel      (text - "Strong Candidate" etc.)
 *   #textFinancialScore    (text)
 *   #textOperationalScore  (text)
 *   #textMarketScore       (text)
 *   #textRecommendation    (text)
 *   #textBreakeven         (text)
 *   #btnDownloadPdf        (button)
 *   #btnScheduleCall       (button)
 *
 * ---------------------------------------------------------------
 */

import { generateScorecard, warmUpApi } from 'backend/scorecard';

// Total steps in the form
const TOTAL_STEPS = 5;
let currentStep = 1;

$w.onReady(function () {
    // Warm up the API while the user is on step 1
    warmUpApi();

    // Show step 1, hide everything else
    showStep(1);
    $w('#resultsSection').hide();
    $w('#loadingOverlay').hide();
    $w('#errorMessage').hide();

    // Wire up navigation buttons
    $w('#btnNext1').onClick(() => goToStep(2));
    $w('#btnNext2').onClick(() => goToStep(3));
    $w('#btnNext3').onClick(() => goToStep(4));
    $w('#btnNext4').onClick(() => goToStep(5));

    $w('#btnBack2').onClick(() => goToStep(1));
    $w('#btnBack3').onClick(() => goToStep(2));
    $w('#btnBack4').onClick(() => goToStep(3));
    $w('#btnBack5').onClick(() => goToStep(4));

    // Submit button
    $w('#btnSubmit').onClick(() => handleSubmit());
});

/**
 * Show one step, hide the others.
 */
function showStep(step) {
    for (let i = 1; i <= TOTAL_STEPS; i++) {
        if (i === step) {
            $w(`#step${i}`).show();
        } else {
            $w(`#step${i}`).hide();
        }
    }
    currentStep = step;
    updateProgress(step);
}

/**
 * Validate the current step before advancing.
 */
function goToStep(targetStep) {
    // Moving forward requires validation
    if (targetStep > currentStep) {
        const errors = validateStep(currentStep);
        if (errors.length > 0) {
            showError(errors.join(' '));
            return;
        }
    }
    $w('#errorMessage').hide();
    showStep(targetStep);

    // Scroll to top of form
    $w('#step' + targetStep).scrollTo();
}

/**
 * Update the progress bar and step label.
 */
function updateProgress(step) {
    const pct = (step / TOTAL_STEPS) * 100;

    // If using a Wix ProgressBar element:
    if ($w('#progressBar').targetValue !== undefined) {
        $w('#progressBar').targetValue = pct;
    }

    $w('#textStepLabel').text = `Step ${step} of ${TOTAL_STEPS}`;
}

/**
 * Validate fields for a given step.
 * Returns an array of error messages (empty = valid).
 */
function validateStep(step) {
    const errors = [];

    switch (step) {
        case 1:
            if (!$w('#inputPharmacyName').value.trim()) {
                errors.push('Please enter your pharmacy name.');
            }
            if (!$w('#inputCity').value.trim()) {
                errors.push('Please enter your city.');
            }
            if (!$w('#dropdownState').value) {
                errors.push('Please select your state.');
            }
            break;

        case 2:
            if (!$w('#dropdownRxVolume').value) {
                errors.push('Please select your monthly prescription volume.');
            }
            if (!$w('#dropdownGlp1Fills').value) {
                errors.push('Please select your GLP-1 fill volume.');
            }
            if (!$w('#dropdownGovPayer').value) {
                errors.push('Please select your government payer percentage.');
            }
            break;

        case 3:
            if (!$w('#dropdownPms').value) {
                errors.push('Please select your pharmacy management software.');
            }
            if (!$w('#dropdownTechnicians').value) {
                errors.push('Please select the number of technicians.');
            }
            break;

        case 4:
            if (!$w('#radioUnderwaterRx').value) {
                errors.push('Please answer whether you are losing money on prescriptions.');
            }
            if (!$w('#radioMailOrder').value) {
                errors.push('Please answer the mail-order question.');
            }
            if (!$w('#radioDirFees').value) {
                errors.push('Please describe your DIR fee impact.');
            }
            break;

        case 5:
            if (!$w('#inputOwnerName').value.trim()) {
                errors.push('Please enter your name.');
            }
            // Email recommended but not blocking
            break;
    }

    return errors;
}

/**
 * Collect all form data and submit to the backend.
 */
async function handleSubmit() {
    // Validate step 5
    const errors = validateStep(5);
    if (errors.length > 0) {
        showError(errors.join(' '));
        return;
    }

    // Show loading state
    $w('#btnSubmit').disable();
    $w('#btnSubmit').label = 'Generating scorecard...';
    $w('#loadingOverlay').show();
    $w('#errorMessage').hide();

    // Build the form data object
    const formData = {
        // Step 1
        pharmacyName: $w('#inputPharmacyName').value.trim(),
        city: $w('#inputCity').value.trim(),
        state: $w('#dropdownState').value,
        yearsInBusiness: $w('#dropdownYears').value || null,

        // Step 2
        monthlyRxVolume: $w('#dropdownRxVolume').value,
        glp1MonthlyFills: $w('#dropdownGlp1Fills').value,
        govPayerPct: $w('#dropdownGovPayer').value,

        // Step 3
        pmsSystem: $w('#dropdownPms').value,
        numTechnicians: $w('#dropdownTechnicians').value,

        // Step 4
        awareOfUnderwaterRx: $w('#radioUnderwaterRx').value || "I'm not sure",
        lostPatientsToMailOrder: $w('#radioMailOrder').value || "No",
        dirFeePressure: $w('#radioDirFees').value || "Significant squeeze",
        dispensesMfpDrugs: $w('#radioMfp').value || "I'm not sure",

        // Step 5
        ownerName: $w('#inputOwnerName').value.trim(),
        email: $w('#inputEmail').value.trim() || null,
        phone: $w('#inputPhone').value.trim() || null,
    };

    try {
        const result = await generateScorecard(formData);

        if (result.success) {
            displayResults(result);
        } else {
            showError(result.error || 'Something went wrong. Please try again.');
            $w('#btnSubmit').enable();
            $w('#btnSubmit').label = 'Get My Scorecard';
            $w('#loadingOverlay').hide();
        }
    } catch (err) {
        console.error('Submission error:', err);
        showError('Unable to connect to the scoring service. Please try again in a moment.');
        $w('#btnSubmit').enable();
        $w('#btnSubmit').label = 'Get My Scorecard';
        $w('#loadingOverlay').hide();
    }
}

/**
 * Display the scorecard results.
 */
function displayResults(result) {
    $w('#loadingOverlay').hide();

    // Hide the form steps
    for (let i = 1; i <= TOTAL_STEPS; i++) {
        $w(`#step${i}`).hide();
    }

    // Populate results
    $w('#textPharmacyName').text = result.pharmacyName;
    $w('#textOverallGrade').text = result.overallGrade;
    $w('#textOverallScore').text = `${result.overallScore}/100`;
    $w('#textOverallLabel').text = result.overallLabel;
    $w('#textFinancialScore').text = `${result.financialFitScore}/100`;
    $w('#textOperationalScore').text = `${result.operationalReadinessScore}/100`;
    $w('#textMarketScore').text = `${result.marketUrgencyScore}/100`;
    $w('#textRecommendation').text = result.recommendation;
    $w('#textBreakeven').text = `${result.roiBreakevenFills} fills/month to break even`;

    // Grade color styling
    const gradeColors = {
        'A': '#22c55e',  // green
        'B': '#3b82f6',  // blue
        'C': '#f59e0b',  // amber
        'D': '#ef4444',  // red
    };
    const color = gradeColors[result.overallGrade] || '#6b7280';
    $w('#textOverallGrade').html = `<span style="color:${color}; font-size:72px; font-weight:bold;">${result.overallGrade}</span>`;

    // PDF download button
    if (result.pdfBase64) {
        $w('#btnDownloadPdf').show();
        $w('#btnDownloadPdf').onClick(() => {
            downloadPdf(result.pdfBase64, result.filename);
        });
    } else {
        $w('#btnDownloadPdf').hide();
    }

    // Schedule call CTA
    $w('#btnScheduleCall').onClick(() => {
        // Link to Calendly, phone number, or contact page
        // Kevin: update this URL to your scheduling link
        $w('#btnScheduleCall').link = 'https://www.retailmymeds.com/contact';
    });

    // Show results
    $w('#resultsSection').show();
    $w('#resultsSection').scrollTo();
}

/**
 * Trigger a browser download of the PDF scorecard.
 */
function downloadPdf(base64Data, filename) {
    // Convert base64 to blob and trigger download
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'application/pdf' });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'pharmacy-scorecard.pdf';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Show an error message to the user.
 */
function showError(message) {
    $w('#errorMessage').text = message;
    $w('#errorMessage').show();
}
