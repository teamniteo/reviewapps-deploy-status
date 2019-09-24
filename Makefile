.PHONY: tests
tests: 
	pytest --cov=review_app_status tests.py --cov-report term --cov-fail-under=100
