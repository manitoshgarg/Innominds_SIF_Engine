# INNOMINDS SIH 2026 Prototype — Day 1

Problem Statement: SIH26165
Theme: Smart Automation
Project: AI/NLP Safety Intelligence Engine

## Current MVP
A baseline text classifier that predicts SIF-Potential vs Non-SIF from safety-report text.

## Important
`safety_reports_demo.csv` is SYNTHETIC DEVELOPMENT DATA created for prototyping.
It is NOT OIL's proprietary HSSE dataset.

## Run
1. Create a virtual environment.
2. Install requirements.
3. Run `python src/train_sif_classifier.py`.

Next modules:
- Life-Saving Rule semantic mapping
- Activity/location/barrier extraction
- FastAPI backend
- React dashboard
