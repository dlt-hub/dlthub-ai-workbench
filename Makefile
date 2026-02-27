.PHONY: dev validate-toolkits lint

dev:
	uv sync --prerelease=explicit

validate-toolkits:
	uv run python tools/validate_toolkits.py

lint: validate-toolkits
	uv run python tools/lint_install.py
