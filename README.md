# Database Selection and Recommendation System using AHP-TOPSIS

## 1. About the Project

The **Database Selection and Recommendation System** is a web-based application that helps users identify a suitable database for their application requirements.

Different applications have different database requirements. For example, a general web application, document application, real-time cache, and distributed wide-column application may require different database features.

This project uses **Multi-Criteria Decision Making (MCDM)** techniques to evaluate and rank databases based on user preferences and application requirements.

The system combines AHP and TOPSIS to calculate criterion weights and recommend the most suitable database from the available alternatives.

## 2. Main Features

### Application Selection
Users can select an application domain for which they want a database recommendation.

The system currently supports:
- General Web Application
- Document Application
- Real-Time Cache
- Distributed Wide-Column Application

### Mandatory Requirement Filtering
The system checks whether databases satisfy the mandatory requirements of the selected application.

Databases that do not meet these requirements are excluded from the ranking process.

### Criterion Selection
Users can select the criteria they want to consider while comparing databases.

Each database is evaluated using scores on a 1–5 scale, supported by evidence references.

### AHP – Criteria Weight Calculation
The Analytic Hierarchy Process (AHP) calculates the importance of each selected criterion based on user preferences.

The user compares criteria in pairs using Saaty's Fundamental Scale of Relative Importance.

The system:
1. Creates a pairwise comparison matrix.
2. Normalizes the matrix.
3. Calculates the criterion weights.

### TOPSIS – Database Ranking
The Technique for Order Preference by Similarity to Ideal Solution (TOPSIS) ranks the eligible databases using their criterion scores and AHP weights.

The process includes:
1. Creating the decision matrix.
2. Normalizing the decision matrix.
3. Calculating the weighted normalized matrix.
4. Identifying the ideal best and ideal worst solutions.
5. Calculating distances from both solutions.
6. Calculating the closeness coefficient.
7. Ranking databases in descending order of their TOPSIS scores.

The database with the highest TOPSIS score receives Rank 1.

### TOPSIS Explainability
The system provides an explanation of why a database is recommended.

The basic explanation highlights the criteria where the recommended database performs well and where other databases may perform better.

Users can also open a detailed explanation to view additional information about criterion weights, TOPSIS results, and sensitivity analysis.

### Sensitivity Analysis
Sensitivity analysis checks how the database ranking changes when the importance of a criterion is increased by 20%.

The system recalculates TOPSIS and compares the new ranking with the original ranking.

This helps understand whether the recommendation is affected by changes in user preferences.

### Ranking Reliability Testing
This optional feature checks how stable the database ranking is when individual database criterion scores are changed.

The system tests hypothetical score values of 1, 3, and 5.

Scenarios that do not change the original score are skipped so that unchanged scenarios do not inflate the stability results.

The test reports:
- Ranking-order stability.
- Top recommendation retention.
- Average rank movement.
- Individual test scenario results.

This testing does not overwrite the original database scores or saved ranking.

### Visual Comparison
A TOPSIS score comparison chart allows users to compare the scores of eligible databases visually.

### Saved Configurations
The system includes functionality for storing and managing saved recommendation configurations using SQLite.

## 3. System Methodology

The overall workflow is:

1. The user selects an application domain.
2. The system filters databases using mandatory requirements.
3. The user selects the criteria for comparison.
4. The user performs pairwise comparisons using AHP.
5. AHP calculates the criterion weights.
6. TOPSIS evaluates the eligible databases using the selected criteria and calculated weights.
7. The system calculates TOPSIS scores and ranks the databases.
8. The system displays the ranked databases, score comparison chart, and recommendation explanation.
9. Users can optionally explore detailed explanations, sensitivity analysis, and ranking reliability testing.
10. The user can save recommendation configurations.

## 4. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| User Interface | Streamlit |
| Decision-Making Methods | AHP and TOPSIS |
| Data Processing | Pandas and NumPy |
| Data Storage | JSON and SQLite |
| Testing | Pytest |
| Version Control | Git and GitHub |

## 5. Project Folder Structure

```text
minor/
│
├── core/
│   ├── __init__.py
│   ├── ahp.py
│   ├── application_scoring.py
│   ├── catalogue.py
│   ├── explanations.py
│   ├── filtering.py
│   ├── ranking_reliability.py
│   ├── recommendation.py
│   └── topsis_explainability.py
│
├── data/
│   ├── application_scores.json
│   ├── application_scores.json.bak
│   ├── applications.json
│   └── databases.json
│
├── storage/
│   ├── __init__.py
│   ├── configurations.db
│   └── database.py
│
├── tests/
│   ├── test_ahp.py
│   ├── test_catalogue_validation.py
│   ├── test_catalogue_view.py
│   ├── test_catalogue.py
│   ├── test_explanations.py
│   ├── test_filtering_requirements.py
│   ├── test_filtering.py
│   ├── test_ranking_reliability.py
│   ├── test_recommendation_storage.py
│   ├── test_recommendation.py
│   ├── test_storage.py
│   └── test_topsis.py
│
├── tools/
│   └── import_scores_from_xlsx.py
│
├── topsis/
│   ├── __init__.py
│   └── topsis.py
│
├── ui/
│   ├── ahp_ui.py
│   └── catalogue_view.py
│
├── .gitignore
├── app.py
├── database_criteria_scoring_workbook.xlsx
├── README.md
├── requirements.txt
├── SCORING_SCALE.md
└── update_catalogue.py
```

## 6. Installation and Setup

### Prerequisites
- Python 3.10 or later
- pip
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/dikshitaydv/minor.git
```

### Step 2: Open the Project Directory

```bash
cd minor
```

### Step 3: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Run the Application

```bash
streamlit run app.py
```

The application will open in your browser.

## 7. Running Tests

To run all project tests:

```bash
python -m pytest -q
```

To run only the ranking reliability tests:

```bash
python -m pytest tests/test_ranking_reliability.py -v
```

## 8. Scoring Methodology

Database criteria are evaluated using a 1–5 scoring scale.

Each score represents the level of support or suitability of a database for a particular criterion.

The scores are maintained in the application's data files and supported by evidence references.

Refer to **SCORING_SCALE.md** for the scoring definitions.

The scoring workbook, `database_criteria_scoring_workbook.xlsx`, is used to review and maintain database criterion scores.

## 9. Understanding the Results

- A higher TOPSIS score indicates a better relative position among the eligible databases.
- Rank 1 represents the highest-ranked database for the selected application, criteria, and user preferences.
- AHP weights represent the relative importance of the selected criteria.
- Sensitivity analysis shows how changes in criterion importance affect the ranking.
- Ranking reliability testing shows how the ranking responds to the hypothetical score changes tested.

**Important:** The recommendation identifies the most suitable database among the evaluated alternatives under the selected criteria, scores, and preferences. It does not claim that one database is universally best.

## 10. Limitations

- Recommendations depend on the available database catalogue and its evaluation scores.
- Scores represent the project's defined evaluation scale and supporting evidence; they are not automatically equivalent to benchmark measurements.
- Results depend on the user's selected criteria and AHP preferences.
- Sensitivity analysis and reliability testing cover only the specific hypothetical changes tested by the system.
- A high ranking stability percentage does not establish real-world database performance or guarantee recommendation accuracy.

## 11. Future Improvements

- Expand the database catalogue and application domains.
- Add more evidence-backed evaluation criteria.
- Improve the handling of uncertain or incomplete database information.
- Introduce workload-based performance comparisons.
- Extend recommendation validation using independent expert assessments.

## 12. Contributors

Developed as a college minor project focused on database selection using Multi-Criteria Decision Making (MCDM).

**GitHub Repository:**  
https://github.com/dikshitaydv/minor