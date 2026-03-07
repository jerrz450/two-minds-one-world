# Data Layer Rebuild Plan

## Why
The previous layer (when it mattered) was assembled in a weekend for a demo and was never intended for production. Now it's gone, so we will build it correctly, without legacy constraints. This is an opportunity to do it right from day one. No tech debt. No bandaids. No shortcuts.

## Goals
- Strong typing at the boundary (data in/data out)
- Composable schema migration system
- Efficient storage abstraction, pluggable for SQL/noSQL/file
- Separation of data access and domain logic from the start
- One source of truth for all transactional data
- Deterministic migrations — no "run twice and pray"

## Milestones
1. Define core domain entities and schema
2. Build migration runner
3. Implement data model layer (CRUD)
4. Add type-checked interface for service layer use
5. Tests for breakage (nothing else)

## Status
- Initial outline ready
- Begin spec for core schema/entities next

## Next: Draft initial core schema for review
