.PHONY: install generate load analyze dashboard report test lint clean

install:
	pip install -r requirements.txt

generate:
	python src/ingestion/generate_data.py --users 5000 --jobs 2000 --events 50000

load:
	python src/ingestion/load_to_db.py

analyze:
	python src/analysis/match_quality.py
	python src/analysis/funnel_conversion.py
	python src/analysis/agent_drift.py

dashboard:
	streamlit run dashboard/app.py

report:
	jupyter nbconvert --to html --execute notebooks/05_weekly_report.ipynb --output reports/weekly_report.html

test:
	pytest tests/ -v

lint:
	ruff check src/ dashboard/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf data/raw/*.csv data/processed/*.duckdb .coverage htmlcov/