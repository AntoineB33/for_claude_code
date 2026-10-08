@echo off
cd /d "%~dp0"
uv run "get_prompts.py" || pause