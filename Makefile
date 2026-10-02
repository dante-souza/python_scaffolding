# Canonical human-facing command interface for this repository.
# Conda chooses Python. uv is managed inside the active Conda environment.
# Recipes stay shell-light so the same Makefile works from Bash/POSIX shells
# as well as Windows shells supported by GNU Make.

PYTHON ?= python
PROJECT_CLI := $(PYTHON) scripts/repo.py

.PHONY: help doctor doctor-no-color doctor-force-color bootstrap setup sync lock \
        env-rebuild test lint format check clean run agents-list skills-list agents-check

.DEFAULT_GOAL := help

help:
	@$(PROJECT_CLI) help

doctor:
	@$(PROJECT_CLI) doctor

doctor-no-color:
	@$(PROJECT_CLI) doctor-no-color

doctor-force-color:
	@$(PROJECT_CLI) doctor-force-color

bootstrap:
	@$(PROJECT_CLI) bootstrap

sync:
	@$(PROJECT_CLI) sync

lock:
	@$(PROJECT_CLI) lock

setup:
	@$(PROJECT_CLI) setup

env-rebuild:
	@$(PROJECT_CLI) env-rebuild

test:
	@$(PROJECT_CLI) test

lint:
	@$(PROJECT_CLI) lint

format:
	@$(PROJECT_CLI) format

check:
	@$(PROJECT_CLI) check

run:
	@$(PROJECT_CLI) run

clean:
	@$(PROJECT_CLI) clean

agents-list:
	@$(PROJECT_CLI) agents-list

skills-list:
	@$(PROJECT_CLI) skills-list

agents-check:
	@$(PROJECT_CLI) agents-check
