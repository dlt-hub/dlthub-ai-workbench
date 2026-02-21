.PHONY: validate-plugins

validate-plugins:
	uv run python tools/validate_plugins.py
