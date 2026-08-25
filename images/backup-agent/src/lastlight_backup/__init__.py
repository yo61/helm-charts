"""Backup and restore agent for Last Light's two-store state.

Last Light keeps durable state in two places that reference each other: a
relational database of execution lifecycles, and per-session JSONL transcripts
on disk, keyed from `executions.session_id`. Backing up either alone produces a
restore that looks healthy and is not.
"""
