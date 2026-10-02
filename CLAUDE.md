# CLAUDE.md

Claude Code should treat `AGENTS.md` as the repository-wide operating policy and `PROJECT.md` as the project intent/specification.

Before implementation:

1. read `AGENTS.md`;
2. read `PROJECT.md` and `README.md`;
3. select the relevant canonical role from `ai/agents/`;
4. load the relevant `ai/skills/*/SKILL.md` files;
5. use Makefile targets for normal repository operations.

Do not create a separate Claude-specific environment policy. The canonical Conda → Conda-local `uv` → `.venv` contract remains defined by the repository documents and scripts.
