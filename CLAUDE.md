# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Riksdagen is a data visualization project built on the Swedish parliament's open data API. It aggregates voting records for all parliament members and visualizes similarity between members and parties — including a Kohonen Self-Organizing Map (SOM) on a hexagonal grid where users can explore members, questions, and aggregate patterns interactively.

Data source: https://data.riksdagen.se/

## Repo layout

```
pipeline/   # Python — data fetching, processing, and model training
frontend/   # React + TypeScript — web visualization app
```

## Python (`pipeline/`)

- Package manager: **uv** (`uv run`, `uv add`, `uv sync`)
- Linting + formatting: **ruff** (`uv run ruff check`, `uv run ruff format`)
- Testing: **pytest** (`uv run pytest`)
- Type checking: **mypy** (`uv run mypy`)
- Run a single test: `uv run pytest -k "test_name"`

## Frontend (`frontend/`)

- React + TypeScript
- Add subdirectory CLAUDE.md once the frontend tooling (Vite, test framework, CSS) is settled

## Riksdagen API

The API is open and requires no authentication. Key domains:
- Votes (`votering`): individual member votes per proposition
- Members (`ledamot`): current and historical parliament members
- Documents (`dokument`): propositions, motions, committee reports

Base URL: `https://data.riksdagen.se/`  
API docs and data formats: https://www.riksdagen.se/sv/dokument-och-lagar/riksdagens-oppna-data/

## GitHub CLI

Always use `--json` when fetching issues or PRs with `gh issue view` / `gh pr view` to avoid a GraphQL error caused by Projects Classic deprecation:

```
gh issue view <number> --repo <owner/repo> --json title,body,labels
gh pr view <number> --repo <owner/repo> --json title,body,state
```

Alternatively use the REST API directly:

```
gh api repos/<owner/repo>/issues/<number>
gh api repos/<owner/repo>/pulls/<number>
```

## Key algorithms

- **Kohonen SOM**: hexagonal grid topology. Nodes represent clusters of similar voting behavior; members, parties, and topics can be projected onto the trained map.
