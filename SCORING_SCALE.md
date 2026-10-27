
# Database Selection Scoring Scale

## 1. Purpose
This document defines how database alternatives will be evaluated before MCDM ranking.

## 2. Scoring Scale

| Score | Meaning |
|---|---|
| 1 | Very poor suitability |
| 2 | Poor suitability |
| 3 | Moderate suitability |
| 4 | Good suitability |
| 5 | Very good suitability |

Scores must be assigned according to documented evidence and clearly defined criteria.

## 3. Unknown Values
- Use `null` when a value is unknown or not verified.
- Never replace an unknown value with 0, 3, or an assumed average.
- If an unknown value affects a mandatory application requirement, flag it for verification.
- Do not exclude a database solely because information is missing.

## 4. Evidence
Each database record should include:
- Official documentation URL
- Source or evidence supporting the score
- Verification date
- Notes explaining assumptions or limitations

## 5. Mandatory Requirements
Check mandatory application requirements separately from preference-based scoring.
A database should be excluded only when reliable evidence confirms that it fails a mandatory requirement.

## 6. MCDM Integration
- AHP determines the relative importance of criteria.
- TOPSIS ranks eligible database alternatives using criterion scores and weights.
- Missing values must be handled explicitly before ranking; they must not silently become zero or an average.

## 7. Current Limitations
Initial scores are provisional until verified against reliable sources.
The scoring scale alone does not establish that a database is suitable for a particular application.
