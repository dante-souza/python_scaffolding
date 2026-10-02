# Canonical human-facing command interface for this repository.
# Conda chooses Python. uv is managed inside the active Conda environment.

PYTHON ?= python

ifeq ($(OS),Windows_NT)
VENV_PYTHON := .venv/Scripts/python.exe
else
VENV_PYTHON := .venv/bin/python
endif

.PHONY: help doctor doctor-no-color doctor-force-color bootstrap setup sync lock \
        env-rebuild test lint format check clean run agents-list skills-list agents-check

.DEFAULT_GOAL := help

help:
	@$(PYTHON) scripts/repo.py help

doctor:
	@$(PYTHON) scripts/doctor.py

doctor-no-color:
	@$(PYTHON) scripts/doctor.py --no-color

doctor-force-color:
	@$(PYTHON) scripts/doctor.py --force-color

bootstrap:
	@$(PYTHON) scripts/bootstrap.py

sync:
	@$(PYTHON) scripts/repo.py sync

lock:
	@$(PYTHON) scripts/repo.py lock

setup: bootstrap sync doctor

env-rebuild:
	@$(PYTHON) scripts/repo.py env-rebuild
	@$(MAKE) bootstrap
	@$(MAKE) sync
	@$(MAKE) doctor

test:
	@$(PYTHON) scripts/repo.py test

lint:
	@$(PYTHON) scripts/repo.py lint

format:
	@$(PYTHON) scripts/repo.py format

check:
	@$(PYTHON) scripts/repo.py check

run:
	@$(PYTHON) scripts/repo.py run

clean:
	@$(PYTHON) scripts/repo.py clean

agents-list:
	@$(PYTHON) scripts/agents_check.py --list-agents

skills-list:
	@$(PYTHON) scripts/agents_check.py --list-skills

agents-check:
	@$(PYTHON) scripts/agents_check.py --check
