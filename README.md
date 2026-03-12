# TakvenOps — AI-Native Project Management Platform

## What This Is

A comprehensive project management tool like Jira/Linear, but with a revolutionary difference: **AI coding agents (Claude Code, Antigravity) are first-class team members**, not just suggestion engines.

## How to Build This

Claude Code: Read ALL files in this folder before starting. The build order is:

1. Read `PRODUCT_REQUIREMENTS.md` — what to build and why
2. Read `TECHNICAL_SPEC.md` — architecture, database, API design
3. Read `UI_DESIGN.md` — frontend pages and components
4. Read `existing_prototype/` — working CLI prototype to build upon
5. Build it as a full-stack web app

## Key Principle

Tasks are stored as **structured markdown files** in a `.takvenops/` directory inside any project repo. The web dashboard reads/writes these files. AI agents also read/write them directly. This creates a bidirectional loop where AI and humans work on the same task board.

## Tech Stack (Recommended)

- **Frontend**: React + Vite (same stack as ROE platform)
- **Backend**: Python FastAPI (same as ROE)
- **Database**: SQLite (lightweight, no setup) or PostgreSQL
- **File system**: `.takvenops/` directory with markdown task files
- **No external dependencies** — runs locally, integrates with any repo
