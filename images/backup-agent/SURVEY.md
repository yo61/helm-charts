# Off-the-shelf backup images: survey

Task 1 of `docs/superpowers/plans/2026-08-25-lastlight-backup-agent.md` (in
`yo61/flux-homelab`). The plan's own instruction is to stop and re-plan if
anything here passes all six behaviours, rather than build an image nobody
needed.

Surveyed 2026-08-25.

## What Last Light's backup actually requires

| # | Behaviour | Why it is not negotiable |
|---|---|---|
| 1 | SQLite online backup, never copying the live file | WAL mode means committed rows can live only in the `-wal`; a file copy captures a torn state |
| 2 | `pg_dump` streamed, no local staging | Scratch is a small `emptyDir`; an unbounded dump exceeding its `sizeLimit` evicts the pod, taking the harness down |
| 3 | Database captured strictly before file paths | `executions.session_id` keys into a JSONL filename. Capture the files first and the archive holds rows pointing at transcripts it never took |
| 4 | Staged upload promoted on success | `latest` resolves by key order, so a partial object at a newer key becomes the recovery point for every later restore |
| 5 | Restore verifies database-to-JSONL references | The two-store split makes a database-only archive possible, and it looks healthy until someone opens a run |
| 6 | Prometheus metrics: last success, duration, size, failures | A backup that stopped weeks ago is worse than none, because it buys false confidence |

## Candidates

| Candidate | 1 | 2 | 3 | 4 | 5 | 6 | Verdict |
|---|---|---|---|---|---|---|---|
| [K8up](https://github.com/k8up-io/k8up) | ~ | ✅ | ❌ | ❌ | ❌ | ✅ | Closest by a distance. Rejected on 3/4/5 |
| [KubeStash / Stash](https://kubestash.com) | ~ | ✅ | ❌ | ❌ | ~ | ✅ | Verification is repository-level, not application-level |
| [offen/docker-volume-backup](https://github.com/offen/docker-volume-backup) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Docker-oriented, volume-level, no database awareness |
| [prodrigestivill/postgres-backup-local](https://github.com/prodrigestivill/docker-postgres-backup-local) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Postgres only; no SQLite, no file paths |
| restic / kopia directly | ❌ | ❌ | ❌ | ~ | ❌ | ❌ | General-purpose engines; every behaviour above would be ours to build |

`~` = achievable but not provided.

**No candidate passes all six.** Proceeding to Task 2.

## Why K8up was rejected, in detail

K8up deserves the detail because it is genuinely close, and because the reasons
it fails are the reasons this design exists at all.

**What it does well.** Its application-aware backup runs a command inside the
container and captures stdout — *"tested with MariaDB, MongoDB, PostgreSQL, and
tar to stdout"*. That is exactly behaviour 2, and behaviour 1 falls out of it,
since `sqlite3 .backup /dev/stdout` fits the same model. It exposes a full
Prometheus metric surface, satisfying behaviour 6, and its restic backend gives
deduplication this design does not attempt.

**Where it stops.** Command-stdout backups and PVC backups are *separate*
operations — the documentation has you exclude PVCs via annotation when using
application-aware backups. So the database and the transcripts cannot be one
coherent unit, and there is no ordering between them to configure. That is
behaviour 3, and without it behaviours 4 and 5 have nothing to attach to: there
is no single archive to promote atomically, and no pairing to verify.

The gap is not a missing feature. K8up models a backup as *either* a command's
output *or* a volume's contents. Last Light's state is irreducibly both, with a
referential dependency running between them.

**KubeStash** was checked because it advertises backup verification. That turns
out to be `RestoreOnly` — restore a KubeDB-managed database and confirm it comes
up — plus `kubectl stash check` for restic repository integrity. Both are
worth having and neither is behaviour 5, which asks whether the rows in one
store still point at files in another.

## What this means for the build

Behaviours 1, 2 and 6 are commodity, and three separate tools provide them. The
build is justified entirely by 3, 4 and 5, all of which follow from Last
Light's two-store split rather than from anything about backup in general.

That is worth remembering if this is ever revisited: should upstream collapse
the JSONL transcripts into the database, or move them to object storage
directly, the case for a bespoke agent largely evaporates and K8up would likely
do.

## Sources

- [K8up](https://github.com/k8up-io/k8up) — [application-aware backups](https://docs.k8up.io/k8up/2.11/how-tos/application-aware-backups.html), [operator config reference](https://docs.k8up.io/k8up/2.11/references/operator-config-reference.html)
- [KubeStash](https://kubestash.com) — [Introducing KubeStash](https://appscode.com/blog/post/stash-2.0/)
- [offen/docker-volume-backup](https://github.com/offen/docker-volume-backup)
