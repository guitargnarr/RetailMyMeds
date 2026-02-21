/**
 * RetailMyMeds Deep-Dive Evaluation - Page Code
 *
 * Paste this into the code panel for your deep-dive form page.
 *
 * Dependencies:
 *   backend/deepdive.jsw (must be set up first)
 *
 * Element IDs referenced below must match what you build in the Editor.
 * See DEEPDIVE_INTEGRATION_GUIDE.md for the full element ID table.
 */

import { generateDeepdive, warmUpApi } from 'backend/deepdive';

// ── State ──────────────────────────────────────────────────────────

let currentSection = 1;
const TOTAL_SECTIONS = 4;
let glp1DrugCount = 1;
let mfpDrugCount = 0;
const MAX_DRUGS = 10;

$w.onReady(() => {
    // Warm up API on page load (Render cold-start mitigation)
    warmUpApi();

    // Show section 1, hide others
    showSection(1);

    // Section navigation
    $w('#btnNextSection1').onClick(() => {
        if (validateSection1()) showSection(2);
    });
    $w('#btnNextSection2').onClick(() => {
        if (validateSection2()) showSection(3);
    });
    $w('#btnNextSection3').onClick(() => showSection(4));
    $w('#btnBackSection2').onClick(() => showSection(1));
    $w('#btnBackSection3').onClick(() => showSection(2));
    $w('#btnBackSection4').onClick(() => showSection(3));

    // GLP-1 drug rows: add/remove
    $w('#btnAddGlp1').onClick(() => addGlp1Row());
    // Set up remove buttons for initial row(s)
    setupGlp1RowListeners(1);

    // Auto-calculate net/fill when acquisition or reimbursement changes
    setupAutoCalc(1);

    // MFP toggle
    $w('#ddMfpToggle').onChange(() => {
        const showMfp = $w('#ddMfpToggle').value === 'Yes';
        if (showMfp) {
            $w('#mfpSection').show();
            if (mfpDrugCount === 0) addMfpRow();
        } else {
            $w('#mfpSection').hide();
            mfpDrugCount = 0;
        }
    });

    // Submit
    $w('#btnSubmitDeepdive').onClick(() => submitDeepdive());

    // PDF download
    $w('#btnDownloadDeepdive').onClick(() => downloadPdf());
});

// ── Section Navigation ─────────────────────────────────────────────

function showSection(num) {
    for (let i = 1; i <= TOTAL_SECTIONS; i++) {
        if (i === num) {
            $w(`#section${i}`).show();
        } else {
            $w(`#section${i}`).hide();
        }
    }
    currentSection = num;

    // Update progress
    const pct = Math.round((num / TOTAL_SECTIONS) * 100);
    $w('#ddProgressBar').value = pct;
    $w('#ddStepLabel').text = `Section ${num} of ${TOTAL_SECTIONS}`;
}

// ── Validation ─────────────────────────────────────────────────────

function validateSection1() {
    const name = $w('#ddPharmacyName').value;
    const owner = $w('#ddOwnerName').value;
    if (!name || !owner) {
        showError('Pharmacy name and owner name are required.');
        return false;
    }
    clearError();
    return true;
}

function validateSection2() {
    // Must have at least 1 GLP-1 drug with all required fields
    for (let i = 1; i <= glp1DrugCount; i++) {
        const drug = $w(`#ddGlp1Drug_${i}`).value;
        const fills = $w(`#ddGlp1Fills_${i}`).value;
        const acq = $w(`#ddGlp1Acq_${i}`).value;
        const reimb = $w(`#ddGlp1Reimb_${i}`).value;

        if (!drug) {
            showError(`Drug ${i}: select a drug name.`);
            return false;
        }
        if (!fills || fills <= 0) {
            showError(`${drug}: enter fills per month.`);
            return false;
        }
        if (!acq || acq <= 0) {
            showError(`${drug}: enter acquisition cost.`);
            return false;
        }
        if (reimb == null || reimb < 0) {
            showError(`${drug}: enter average reimbursement.`);
            return false;
        }
    }
    clearError();
    return true;
}

// ── GLP-1 Drug Row Management ──────────────────────────────────────

function addGlp1Row() {
    if (glp1DrugCount >= MAX_DRUGS) {
        showError('Maximum 10 GLP-1 drugs.');
        return;
    }
    glp1DrugCount++;
    $w(`#glp1Row_${glp1DrugCount}`).show();
    setupGlp1RowListeners(glp1DrugCount);
    setupAutoCalc(glp1DrugCount);
    clearError();
}

function setupGlp1RowListeners(rowNum) {
    const removeBtn = $w(`#btnRemoveGlp1_${rowNum}`);
    if (removeBtn) {
        removeBtn.onClick(() => {
            if (glp1DrugCount <= 1) return; // Keep at least 1
            $w(`#glp1Row_${rowNum}`).hide();
            // Clear values
            $w(`#ddGlp1Drug_${rowNum}`).value = '';
            $w(`#ddGlp1Fills_${rowNum}`).value = null;
            $w(`#ddGlp1Acq_${rowNum}`).value = null;
            $w(`#ddGlp1Reimb_${rowNum}`).value = null;
        });
    }
}

function setupAutoCalc(rowNum) {
    const acqEl = $w(`#ddGlp1Acq_${rowNum}`);
    const reimbEl = $w(`#ddGlp1Reimb_${rowNum}`);
    const netEl = $w(`#ddGlp1Net_${rowNum}`);

    const calc = () => {
        const acq = Number(acqEl.value) || 0;
        const reimb = Number(reimbEl.value) || 0;
        const net = reimb - acq;
        if (acq > 0) {
            const sign = net >= 0 ? '+' : '';
            netEl.text = `${sign}$${net.toFixed(2)}`;
            netEl.style.color = net < 0 ? '#DC2626' : '#16A34A';
        } else {
            netEl.text = '--';
            netEl.style.color = '#64748B';
        }
    };

    acqEl.onInput(calc);
    reimbEl.onInput(calc);
}

// ── MFP Drug Row Management ────────────────────────────────────────

function addMfpRow() {
    if (mfpDrugCount >= MAX_DRUGS) return;
    mfpDrugCount++;
    $w(`#mfpRow_${mfpDrugCount}`).show();

    const removeBtn = $w(`#btnRemoveMfp_${mfpDrugCount}`);
    if (removeBtn) {
        removeBtn.onClick(() => {
            $w(`#mfpRow_${mfpDrugCount}`).hide();
        });
    }
}

// ── Submit ──────────────────────────────────────────────────────────

async function submitDeepdive() {
    clearError();
    $w('#ddLoadingOverlay').show();
    $w('#btnSubmitDeepdive').disable();

    // Collect GLP-1 drugs
    const glp1Drugs = [];
    for (let i = 1; i <= glp1DrugCount; i++) {
        const drug = $w(`#ddGlp1Drug_${i}`).value;
        if (!drug) continue; // Skip empty rows
        glp1Drugs.push({
            drugName: drug,
            fillsPerMonth: Number($w(`#ddGlp1Fills_${i}`).value),
            acquisitionCost: Number($w(`#ddGlp1Acq_${i}`).value),
            avgReimbursement: Number($w(`#ddGlp1Reimb_${i}`).value),
            payerType: $w(`#ddGlp1Payer_${i}`).value || 'Commercial PBM',
        });
    }

    // Collect MFP drugs (if toggle is on)
    const mfpDrugs = [];
    if ($w('#ddMfpToggle').value === 'Yes') {
        for (let i = 1; i <= mfpDrugCount; i++) {
            const drug = $w(`#ddMfpDrug_${i}`).value;
            if (!drug) continue;
            mfpDrugs.push({
                drugName: drug,
                fillsPerMonth: Number($w(`#ddMfpFills_${i}`).value),
                acquisitionCost: Number($w(`#ddMfpAcq_${i}`).value),
                pbmReimbursement: Number($w(`#ddMfpReimb_${i}`).value),
                expectedRebate: Number($w(`#ddMfpExpRebate_${i}`).value),
                actualRebateReceived: $w(`#ddMfpActRebate_${i}`).value || null,
                daysOutstanding: Number($w(`#ddMfpDays_${i}`).value) || 60,
            });
        }
    }

    const formData = {
        pharmacyName: $w('#ddPharmacyName').value,
        ownerName: $w('#ddOwnerName').value,
        city: $w('#ddCity').value || '',
        state: $w('#ddState').value || '',
        email: $w('#ddEmail').value || null,
        phone: $w('#ddPhone').value || null,
        npiNumber: $w('#ddNpi').value || null,
        pmsSystem: $w('#ddPmsSystem').value || '',
        glp1Drugs: glp1Drugs,
        mfpDrugs: mfpDrugs,
        specialtyMonthlyLoss: Number($w('#ddSpecialtyLoss').value) || 0,
        genericBelowNadacPct: Number($w('#ddGenericBelowNadac').value) || 0,
        monthlyRxVolume: Number($w('#ddMonthlyRxVolume').value) || 0,
        identifyMethod: $w('#ddIdentifyMethod').value || "We don't",
        routingAction: $w('#ddRoutingAction').value || "We don't route",
    };

    try {
        const result = await generateDeepdive(formData);

        $w('#ddLoadingOverlay').hide();
        $w('#btnSubmitDeepdive').enable();

        if (!result.success) {
            showError(result.error || 'Analysis failed. Please try again.');
            return;
        }

        displayResults(result);

    } catch (err) {
        $w('#ddLoadingOverlay').hide();
        $w('#btnSubmitDeepdive').enable();
        showError('Something went wrong. Please try again.');
        console.error('Deep-dive submission error:', err);
    }
}

// ── Display Results ─────────────────────────────────────────────────

let _pdfBase64 = null;
let _pdfFilename = null;

function displayResults(result) {
    // Hide the form sections, show results
    for (let i = 1; i <= TOTAL_SECTIONS; i++) {
        $w(`#section${i}`).hide();
    }
    $w('#ddProgressBar').value = 100;
    $w('#ddStepLabel').text = 'Analysis Complete';

    // Populate results
    $w('#ddResultPharmacyName').text = result.pharmacyName;
    $w('#ddResultMonthlyLoss').text = result.totalMonthlyLoss;
    $w('#ddResultAnnualLoss').text = result.totalAnnualLoss;
    $w('#ddResultLosingDrugs').text = `${result.losingDrugCount} drug${result.losingDrugCount !== 1 ? 's' : ''} losing money`;
    $w('#ddResultAvgLoss').text = `${result.weightedAvgLoss}/fill avg loss`;
    $w('#ddResultBreakeven').text = `${result.breakevenFills} fills/month to break even with RMM`;

    // Store PDF for download
    _pdfBase64 = result.pdfBase64;
    _pdfFilename = result.filename;

    if (_pdfBase64) {
        $w('#btnDownloadDeepdive').show();
    } else {
        $w('#btnDownloadDeepdive').hide();
    }

    $w('#ddResultsSection').show();
}

// ── PDF Download ───────────────────────────────────────────────────

function downloadPdf() {
    if (!_pdfBase64) return;

    const byteChars = atob(_pdfBase64);
    const byteNums = new Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) {
        byteNums[i] = byteChars.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNums);
    const blob = new Blob([byteArray], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = _pdfFilename || 'deepdive_report.pdf';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ── Error Handling ─────────────────────────────────────────────────

function showError(msg) {
    $w('#ddErrorMessage').text = msg;
    $w('#ddErrorMessage').show();
}

function clearError() {
    $w('#ddErrorMessage').hide();
}
