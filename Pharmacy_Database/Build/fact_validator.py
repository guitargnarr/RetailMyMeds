#!/usr/bin/env python3
"""
RMM Fact Validator
===================
Pure Python fact-checker for model output. No LLM needed.

Extracts specific claims (dollar amounts, percentages, counts,
grade references) from model output and validates each against
the pharmacy CSV data and RMM reference constants.

Modeled after ai_framework_git/mirador_fact_validator.py but
adapted for RMM domain: ground truth is the targeting CSV,
not external APIs.

Usage as module:
    from fact_validator import validate_output
    result = validate_output(model_text, pharmacy_row)
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


# --- Load NADAC loss data if available ---

_LOSS_DATA_PATH = (
    Path(__file__).resolve().parent / 'reference_data'
    / 'glp1_loss_per_fill.json'
)

_NADAC_LOSS_NATIONAL = None
_NADAC_LOSS_RANGE = (15.0, 35.0)  # reasonable range for NADAC-weighted

if _LOSS_DATA_PATH.exists():
    try:
        with open(_LOSS_DATA_PATH, 'r') as _f:
            _loss_data = json.load(_f)
        _NADAC_LOSS_NATIONAL = _loss_data.get(
            'national_weighted_loss_per_fill',
        )
        _state_losses = [
            v['weighted_loss_per_fill']
            for v in _loss_data.get('per_state', {}).values()
            if v.get('weighted_loss_per_fill')
        ]
        if _state_losses:
            _NADAC_LOSS_RANGE = (
                min(_state_losses) * 0.8,
                max(_state_losses) * 1.2,
            )
    except (json.JSONDecodeError, KeyError):
        pass


# --- Reference constants (ground truth from scoring engine) ---
# NOTE: grade counts and thresholds will shift after re-scoring with
# exposure index. These are updated by running score_pharmacies.py.
# The values below are the PREVIOUS baseline -- they'll be updated
# after the first full pipeline run.

REFERENCE = {
    'total_pharmacies': 33185,
    'grade_a_count': 4978,
    'grade_b_count': 8296,
    'grade_c_count': 9956,
    'grade_d_count': 9955,
    'grade_a_pct': 15.0,
    'grade_b_pct': 25.0,
    'grade_c_pct': 30.0,
    'grade_d_pct': 30.0,
    'grade_a_threshold': 72.0,
    'hpsa_count': 30387,
    'hpsa_pct': 91.6,
    'score_min': 7.0,
    'score_max': 98.7,
    'loss_per_fill_nadac': _NADAC_LOSS_NATIONAL,
    'loss_per_fill_range': _NADAC_LOSS_RANGE,
    'exposure_index_min': 0.0,
    'exposure_index_max': 100.0,
    'ncpa_count': 18984,
    'metro_count': 26480,
    'rural_adjacent_count': 3990,
    'rural_remote_count': 2428,
    'unmapped_count': 287,
    'glp1_cost_min': 246795,
    'glp1_cost_max': 2002843,
    'diabetes_pct_max': 31.0,
    'obesity_pct_max': 58.5,
    'income_max': 250001,
    'population_max': 137213,
    # State Grade A counts (updated after exposure index re-scoring)
    'state_grade_a': {
        'FL': 583, 'TX': 481, 'MI': 382, 'LA': 367,
        'OH': 329, 'AL': 258, 'TN': 246, 'NC': 239,
        'WV': 225, 'VA': 178, 'SC': 176, 'GA': 162,
        'CA': 159, 'NY': 150, 'IL': 148,
        'KY': 11,
    },
    # State totals (pharmacy counts -- these don't change)
    'state_totals': {
        'NY': 3894, 'TX': 3108, 'CA': 3037, 'FL': 2677,
        'MI': 1698, 'PA': 1399, 'NJ': 1284, 'GA': 993,
        'IL': 930, 'NC': 910, 'OH': 779, 'AL': 736,
        'LA': 719, 'TN': 714, 'MO': 703, 'KY': 696,
        'OK': 617, 'MS': 523, 'MD': 548,
    },
}

# Scoring weight names for reference
WEIGHT_LABELS = {
    'glp1': 25,
    'diabetes': 20,
    'age_65': 15,
    'obesity': 10,
    'hpsa': 10,
    'income': 10,
    'population': 10,
}


# --- Claim extraction patterns ---

PATTERNS = {
    'dollar_amount': re.compile(
        r'\$\s?([\d,]+(?:\.\d{1,2})?)'
    ),
    'percentage': re.compile(
        r'([\d]+\.?\d*)\s*%'
    ),
    'count_with_context': re.compile(
        r'([\d,]+)\s+'
        r'(?:pharmacies|pharmacys|stores|locations|independents)'
    ),
    'grade_count': re.compile(
        r'(?:Grade\s+[ABCD])\s*[:\-]?\s*([\d,]+)',
        re.IGNORECASE,
    ),
    'score_value': re.compile(
        r'(?:score|scored|rating)\s*(?:of|is|:)?\s*'
        r'([\d]+\.?\d*)',
        re.IGNORECASE,
    ),
    'loss_per_fill': re.compile(
        r'\$\s?(\d+)\s*(?:per\s+fill|/fill|loss\s+per)',
        re.IGNORECASE,
    ),
    'exposure_index': re.compile(
        r'(?:exposure\s+index)\s*[:\-]?\s*([\d]+\.?\d*)',
        re.IGNORECASE,
    ),
}


@dataclass
class Claim:
    """A single extracted claim from model output."""

    claim_type: str
    raw_text: str
    value: float | str
    context: str
    status: str = 'unverified'  # verified | flagged | unverified
    confidence: float = 0.0
    note: str = ''


@dataclass
class ValidationResult:
    """Full validation result for a model run."""

    claims: list[Claim] = field(default_factory=list)
    verified: int = 0
    flagged: int = 0
    unverified: int = 0
    confidence: float = 0.0
    summary: str = ''


def _parse_number(s: str) -> float:
    """Parse a number string, stripping commas."""
    return float(s.replace(',', ''))


def _extract_context(text: str, match_str: str) -> str:
    """Get ~80 chars surrounding a match."""
    pos = text.find(match_str)
    if pos == -1:
        pos = text.lower().find(match_str.lower())
    if pos == -1:
        return ''
    start = max(0, pos - 40)
    end = min(len(text), pos + len(match_str) + 40)
    return text[start:end].strip()


def _validate_dollar(
    claim: Claim, pharmacy: dict | None,
) -> None:
    """Validate a dollar amount claim."""
    val = claim.value
    ctx_lower = claim.context.lower()

    # Check against pharmacy-specific data if available
    if pharmacy:
        annual_loss = pharmacy.get('est_annual_glp1_loss', '')
        if annual_loss:
            try:
                csv_loss = float(annual_loss)
                if abs(val - csv_loss) < 1:
                    claim.status = 'verified'
                    claim.confidence = 1.0
                    claim.note = (
                        'Matches CSV est_annual_glp1_loss'
                    )
                    return
            except (ValueError, TypeError):
                pass

        loss_per_fill = pharmacy.get('est_loss_per_fill', '')
        if loss_per_fill:
            try:
                csv_lpf = float(loss_per_fill)
                if abs(val - csv_lpf) < 0.5:
                    claim.status = 'verified'
                    claim.confidence = 1.0
                    claim.note = (
                        'Matches CSV est_loss_per_fill '
                        '(NADAC-weighted)'
                    )
                    return
            except (ValueError, TypeError):
                pass

        glp1_cost = pharmacy.get(
            'state_glp1_cost_per_pharmacy', '',
        )
        if glp1_cost:
            try:
                csv_cost = float(glp1_cost)
                if abs(val - csv_cost) < 1:
                    claim.status = 'verified'
                    claim.confidence = 1.0
                    claim.note = (
                        'Matches CSV '
                        'state_glp1_cost_per_pharmacy'
                    )
                    return
            except (ValueError, TypeError):
                pass

        income = pharmacy.get('zip_median_income', '')
        if income:
            try:
                csv_income = float(income)
                if abs(val - csv_income) < 1:
                    claim.status = 'verified'
                    claim.confidence = 1.0
                    claim.note = 'Matches CSV zip_median_income'
                    return
            except (ValueError, TypeError):
                pass

    # Check against reference constants
    # Check loss per fill (NADAC-weighted or legacy $37)
    lo, hi = REFERENCE['loss_per_fill_range']
    nadac_national = REFERENCE.get('loss_per_fill_nadac')
    if nadac_national and abs(val - nadac_national) < 1:
        claim.status = 'verified'
        claim.confidence = 1.0
        claim.note = f'Matches NADAC national loss/fill (${nadac_national})'
        return
    if lo <= val <= hi:
        claim.status = 'verified'
        claim.confidence = 0.8
        claim.note = f'Within NADAC loss/fill range (${lo:.0f}-${hi:.0f})'
        return
    if val == 37:
        claim.status = 'verified'
        claim.confidence = 0.6
        claim.note = 'Legacy $37/fill (NCPA survey, now superseded by NADAC)'
        return

    if 'cost' in ctx_lower or 'glp' in ctx_lower:
        lo = REFERENCE['glp1_cost_min']
        hi = REFERENCE['glp1_cost_max']
        if lo <= val <= hi:
            claim.status = 'unverified'
            claim.confidence = 0.5
            claim.note = (
                f'In GLP-1 range (${lo:,}-${hi:,}) '
                f'but not verified against specific state'
            )
            return

    # SaaS pricing
    if val == 275:
        claim.status = 'verified'
        claim.confidence = 1.0
        claim.note = 'RMM standard pricing'
        return
    if val == 225:
        claim.status = 'verified'
        claim.confidence = 1.0
        claim.note = 'RMM 5+ stores pricing'
        return

    claim.status = 'unverified'
    claim.confidence = 0.3
    claim.note = 'Dollar amount not matched to CSV or reference'


def _validate_percentage(
    claim: Claim, pharmacy: dict | None,
) -> None:
    """Validate a percentage claim."""
    val = claim.value
    ctx_lower = claim.context.lower()

    # Check pharmacy-specific percentages
    if pharmacy:
        pct_fields = {
            'diabetes': 'zip_diabetes_pct',
            'obesity': 'zip_obesity_pct',
            'age 65': 'zip_pct_65_plus',
            'senior': 'zip_pct_65_plus',
            '65+': 'zip_pct_65_plus',
            'elderly': 'zip_pct_65_plus',
        }
        for keyword, col in pct_fields.items():
            if keyword in ctx_lower:
                csv_val = pharmacy.get(col, '')
                if csv_val:
                    try:
                        csv_pct = float(csv_val)
                        if abs(val - csv_pct) < 0.15:
                            claim.status = 'verified'
                            claim.confidence = 1.0
                            claim.note = (
                                f'Matches CSV {col}'
                            )
                            return
                    except (ValueError, TypeError):
                        pass

    # Reference percentages
    ref_pcts = {
        REFERENCE['hpsa_pct']: 'HPSA coverage (91.6%)',
        REFERENCE['grade_a_pct']: 'Grade A = 15%',
        REFERENCE['grade_b_pct']: 'Grade B = 25%',
        REFERENCE['grade_c_pct']: 'Grade C = 30%',
        REFERENCE['grade_d_pct']: 'Grade D = 30%',
    }
    for ref_val, label in ref_pcts.items():
        if abs(val - ref_val) < 0.15:
            claim.status = 'verified'
            claim.confidence = 1.0
            claim.note = label
            return

    claim.status = 'unverified'
    claim.confidence = 0.3
    claim.note = 'Percentage not matched to CSV or reference'


def _validate_count(
    claim: Claim, pharmacy: dict | None,
) -> None:
    """Validate a pharmacy count claim."""
    val = int(claim.value)

    # Check exact reference counts
    ref_counts = {
        REFERENCE['total_pharmacies']: 'Total pharmacies',
        REFERENCE['grade_a_count']: 'Grade A count',
        REFERENCE['grade_b_count']: 'Grade B count',
        REFERENCE['grade_c_count']: 'Grade C count',
        REFERENCE['grade_d_count']: 'Grade D count',
        REFERENCE['hpsa_count']: 'HPSA designated count',
        REFERENCE['ncpa_count']: 'NCPA reported count',
        REFERENCE['metro_count']: 'Metro count',
        REFERENCE['rural_adjacent_count']: 'Rural-Adjacent',
        REFERENCE['rural_remote_count']: 'Rural-Remote',
    }
    if val in ref_counts:
        claim.status = 'verified'
        claim.confidence = 1.0
        claim.note = ref_counts[val]
        return

    # Check state totals and Grade A counts
    for st, cnt in REFERENCE['state_totals'].items():
        if val == cnt:
            claim.status = 'verified'
            claim.confidence = 1.0
            claim.note = f'{st} total pharmacies'
            return
    for st, cnt in REFERENCE['state_grade_a'].items():
        if val == cnt:
            claim.status = 'verified'
            claim.confidence = 1.0
            claim.note = f'{st} Grade A count'
            return

    claim.status = 'unverified'
    claim.confidence = 0.3
    claim.note = 'Count not matched to reference data'


def _validate_score(
    claim: Claim, pharmacy: dict | None,
) -> None:
    """Validate an RMM score claim."""
    val = claim.value

    if pharmacy:
        csv_score = pharmacy.get('rmm_score', '')
        if csv_score:
            try:
                if abs(val - float(csv_score)) < 0.15:
                    claim.status = 'verified'
                    claim.confidence = 1.0
                    claim.note = 'Matches CSV rmm_score'
                    return
            except (ValueError, TypeError):
                pass

    lo = REFERENCE['score_min']
    hi = REFERENCE['score_max']
    if lo <= val <= hi:
        claim.status = 'unverified'
        claim.confidence = 0.4
        claim.note = (
            f'In valid range ({lo}-{hi}) '
            f'but not matched to specific pharmacy'
        )
        return

    claim.status = 'flagged'
    claim.confidence = 0.0
    claim.note = f'Outside valid score range ({lo}-{hi})'


# --- Main validator ---


def validate_output(
    model_text: str,
    pharmacy: dict | None = None,
) -> ValidationResult:
    """Validate all extractable claims in model output.

    Args:
        model_text: Full text output from the model.
        pharmacy: Optional CSV row dict for the pharmacy
                  being discussed (enables per-pharmacy
                  validation).

    Returns:
        ValidationResult with per-claim verdicts and
        overall confidence.
    """
    result = ValidationResult()

    # Extract and validate dollar amounts
    for m in PATTERNS['dollar_amount'].finditer(model_text):
        raw = m.group(0)
        try:
            val = _parse_number(m.group(1))
        except ValueError:
            continue
        claim = Claim(
            claim_type='dollar_amount',
            raw_text=raw,
            value=val,
            context=_extract_context(model_text, raw),
        )
        _validate_dollar(claim, pharmacy)
        result.claims.append(claim)

    # Extract and validate percentages
    for m in PATTERNS['percentage'].finditer(model_text):
        raw = m.group(0)
        try:
            val = float(m.group(1))
        except ValueError:
            continue
        claim = Claim(
            claim_type='percentage',
            raw_text=raw,
            value=val,
            context=_extract_context(model_text, raw),
        )
        _validate_percentage(claim, pharmacy)
        result.claims.append(claim)

    # Extract and validate pharmacy counts
    for m in PATTERNS['count_with_context'].finditer(
        model_text,
    ):
        raw = m.group(0)
        try:
            val = _parse_number(m.group(1))
        except ValueError:
            continue
        claim = Claim(
            claim_type='count',
            raw_text=raw,
            value=int(val),
            context=_extract_context(model_text, raw),
        )
        _validate_count(claim, pharmacy)
        result.claims.append(claim)

    # Extract and validate grade counts
    for m in PATTERNS['grade_count'].finditer(model_text):
        raw = m.group(0)
        try:
            val = _parse_number(m.group(1))
        except ValueError:
            continue
        claim = Claim(
            claim_type='grade_count',
            raw_text=raw,
            value=int(val),
            context=_extract_context(model_text, raw),
        )
        _validate_count(claim, pharmacy)
        result.claims.append(claim)

    # Extract and validate score references
    for m in PATTERNS['score_value'].finditer(model_text):
        raw = m.group(0)
        try:
            val = float(m.group(1))
        except ValueError:
            continue
        # Skip if it looks like a percentage (already caught)
        if val > 100:
            continue
        claim = Claim(
            claim_type='score',
            raw_text=raw,
            value=val,
            context=_extract_context(model_text, raw),
        )
        _validate_score(claim, pharmacy)
        result.claims.append(claim)

    # Extract loss-per-fill claims
    for m in PATTERNS['loss_per_fill'].finditer(model_text):
        raw = m.group(0)
        try:
            val = float(m.group(1))
        except ValueError:
            continue
        claim = Claim(
            claim_type='loss_per_fill',
            raw_text=raw,
            value=val,
            context=_extract_context(model_text, raw),
        )
        lo, hi = REFERENCE['loss_per_fill_range']
        nadac_national = REFERENCE.get('loss_per_fill_nadac')
        if nadac_national and abs(val - nadac_national) < 1:
            claim.status = 'verified'
            claim.confidence = 1.0
            claim.note = (
                f'Matches NADAC national '
                f'(${nadac_national:.0f}/fill)'
            )
        elif lo <= val <= hi:
            claim.status = 'verified'
            claim.confidence = 0.8
            claim.note = (
                f'Within NADAC state range '
                f'(${lo:.0f}-${hi:.0f})'
            )
        elif val == 37:
            claim.status = 'verified'
            claim.confidence = 0.6
            claim.note = (
                'Legacy $37/fill NCPA '
                '(superseded by NADAC)'
            )
        else:
            claim.status = 'flagged'
            claim.confidence = 0.0
            claim.note = (
                f'Loss per fill ${val:.0f} outside '
                f'expected NADAC range '
                f'(${lo:.0f}-${hi:.0f})'
            )
        result.claims.append(claim)

    # Extract exposure index claims
    for m in PATTERNS['exposure_index'].finditer(model_text):
        raw = m.group(0)
        try:
            val = float(m.group(1))
        except ValueError:
            continue
        claim = Claim(
            claim_type='exposure_index',
            raw_text=raw,
            value=val,
            context=_extract_context(model_text, raw),
        )
        ei_min = REFERENCE['exposure_index_min']
        ei_max = REFERENCE['exposure_index_max']
        if pharmacy:
            csv_ei = pharmacy.get('glp1_exposure_index', '')
            if csv_ei:
                try:
                    if abs(val - float(csv_ei)) < 0.15:
                        claim.status = 'verified'
                        claim.confidence = 1.0
                        claim.note = (
                            'Matches CSV glp1_exposure_index'
                        )
                        result.claims.append(claim)
                        continue
                except (ValueError, TypeError):
                    pass
        if ei_min <= val <= ei_max:
            claim.status = 'unverified'
            claim.confidence = 0.5
            claim.note = (
                f'In valid range ({ei_min}-{ei_max}) '
                f'but not matched to specific pharmacy'
            )
        else:
            claim.status = 'flagged'
            claim.confidence = 0.0
            claim.note = (
                f'Outside valid range ({ei_min}-{ei_max})'
            )
        result.claims.append(claim)

    # Compute summary stats
    for c in result.claims:
        if c.status == 'verified':
            result.verified += 1
        elif c.status == 'flagged':
            result.flagged += 1
        else:
            result.unverified += 1

    total = len(result.claims)
    if total > 0:
        result.confidence = result.verified / total
    else:
        result.confidence = 1.0  # no claims = nothing to flag

    result.summary = _build_summary(result)
    return result


def _build_summary(result: ValidationResult) -> str:
    """Build human-readable validation summary."""
    total = len(result.claims)
    if total == 0:
        return 'No verifiable claims extracted.'

    lines = []
    lines.append(
        f'FACT CHECK: {result.verified}/{total} verified, '
        f'{result.flagged} flagged, '
        f'{result.unverified} unverified'
    )

    confidence_pct = result.confidence * 100
    if confidence_pct >= 80:
        level = 'HIGH CONFIDENCE'
    elif confidence_pct >= 50:
        level = 'MEDIUM CONFIDENCE'
    else:
        level = 'LOW CONFIDENCE'
    lines.append(f'{level} ({confidence_pct:.0f}%)')
    lines.append('')

    # Group by status
    if result.flagged > 0:
        lines.append('FLAGGED:')
        for c in result.claims:
            if c.status == 'flagged':
                lines.append(
                    f'  {c.raw_text} -- {c.note}'
                )
        lines.append('')

    if result.unverified > 0:
        lines.append('UNVERIFIED:')
        for c in result.claims:
            if c.status == 'unverified':
                lines.append(
                    f'  {c.raw_text} -- {c.note}'
                )
        lines.append('')

    if result.verified > 0:
        lines.append('VERIFIED:')
        for c in result.claims:
            if c.status == 'verified':
                lines.append(
                    f'  {c.raw_text} -- {c.note}'
                )

    return '\n'.join(lines)


def format_validation_json(
    result: ValidationResult,
) -> dict:
    """Convert ValidationResult to JSON-serializable dict."""
    return {
        'verified': result.verified,
        'flagged': result.flagged,
        'unverified': result.unverified,
        'total': len(result.claims),
        'confidence': round(result.confidence, 3),
        'summary': result.summary,
        'claims': [
            {
                'type': c.claim_type,
                'raw': c.raw_text,
                'status': c.status,
                'confidence': round(c.confidence, 2),
                'note': c.note,
            }
            for c in result.claims
        ],
    }


# --- CLI test ---

if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pharmacy_lookup import lookup_npi

    # Test with a sample model output
    sample = """
    Central Kentucky Apothecary has a score of 82.8 and is
    Grade A. Exposure index: 57.2 with 900 nearby prescriber
    claims. Located in a ZIP with 20.1% diabetes prevalence
    and 41.1% obesity. The estimated annual GLP-1 loss is
    $72,901 based on $53 per fill (NADAC-weighted). Kentucky
    has 696 total pharmacies and 11 Grade A. The database
    contains 33,185 pharmacies with 91.6% in HPSA areas.
    """

    pharmacy = lookup_npi('1497754923')
    result = validate_output(sample, pharmacy)
    print(result.summary)
