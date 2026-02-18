/**
 * RetailMyMeds Results Page - Page Code (OPTIONAL)
 *
 * USE THIS IF: Kevin prefers a separate results page instead of
 * showing results inline on the form page.
 *
 * If using the inline approach (results on the same page as the form),
 * this file is NOT needed -- qualification-form.js handles everything.
 *
 * HOW IT WORKS:
 * - qualification-form.js stores the scorecard result in session storage
 * - This page reads it on load and displays it
 *
 * ELEMENT IDS (same as the results section in qualification-form.js):
 *   #textPharmacyName, #textOverallGrade, #textOverallScore,
 *   #textOverallLabel, #textFinancialScore, #textOperationalScore,
 *   #textMarketScore, #textRecommendation, #textBreakeven,
 *   #btnDownloadPdf, #btnScheduleCall, #btnStartOver
 */

import wixLocation from 'wix-location';
import { session } from 'wix-storage';

$w.onReady(function () {
    const raw = session.getItem('scorecardResult');

    if (!raw) {
        // No data -- user navigated here directly. Send them to the form.
        wixLocation.to('/qualification');
        return;
    }

    const result = JSON.parse(raw);

    // Populate all result fields
    $w('#textPharmacyName').text = result.pharmacyName;
    $w('#textOverallGrade').text = result.overallGrade;
    $w('#textOverallScore').text = `${result.overallScore}/100`;
    $w('#textOverallLabel').text = result.overallLabel;
    $w('#textFinancialScore').text = `${result.financialFitScore}/100`;
    $w('#textOperationalScore').text = `${result.operationalReadinessScore}/100`;
    $w('#textMarketScore').text = `${result.marketUrgencyScore}/100`;
    $w('#textRecommendation').text = result.recommendation;
    $w('#textBreakeven').text = `${result.roiBreakevenFills} fills/month to break even`;

    // Grade color
    const gradeColors = {
        'A': '#22c55e',
        'B': '#3b82f6',
        'C': '#f59e0b',
        'D': '#ef4444',
    };
    const color = gradeColors[result.overallGrade] || '#6b7280';
    $w('#textOverallGrade').html = `<span style="color:${color}; font-size:72px; font-weight:bold;">${result.overallGrade}</span>`;

    // PDF download
    if (result.pdfBase64) {
        $w('#btnDownloadPdf').show();
        $w('#btnDownloadPdf').onClick(() => {
            const byteCharacters = atob(result.pdfBase64);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = result.filename || 'pharmacy-scorecard.pdf';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    } else {
        $w('#btnDownloadPdf').hide();
    }

    // Schedule call
    $w('#btnScheduleCall').onClick(() => {
        // Kevin: update this to your scheduling link
        wixLocation.to('https://www.retailmymeds.com/contact');
    });

    // Start over
    $w('#btnStartOver').onClick(() => {
        session.removeItem('scorecardResult');
        wixLocation.to('/qualification');
    });

    // Clean up session storage
    // (Keep it available for this page load, remove after 5 min)
    setTimeout(() => {
        session.removeItem('scorecardResult');
    }, 300000);
});
