# Sky

Blockchain data indexing and analytics pipeline for the Sky protocol (formerly MakerDAO). Tracks on-chain vault positions, rate events, and computes daily debt snapshots with interest calculations for Sky allocator agents.

## Overview

The pipeline runs in three stages:

1. **Events** — fetches raw on-chain logs from Ethereum and indexes them into the database.
2. **Agents** — replays indexed events to derive per-urn position states and cumulative ilk rates.
3. **MSC** — computes daily debt balance snapshots with APR and accrued interest for each agent.

### Tracked agents

| Slug    | Name  | Ilk                  |
|---------|-------|----------------------|
| `spark` | Spark | `ALLOCATOR-SPARK-A`  |
| `grove` | Grove | `ALLOCATOR-BLOOM-A`  |
| `obex`  | Obex  | `ALLOCATOR-OBEX-A`   |

## Architecture

```
events/
  EventVatProcessor   – indexes Vat frob/fork/fold/grab logs (from block 8928150)
  EventSSRProcessor   – indexes sUSDS `file` (ssr) logs for rate changes

agents/
  AgentUrnStatesProcessor – replays Vat events into per-urn ink/art/debt snapshots
                            with cumulative ilk rate tracking

msc/
  MSCDebtSnapshotManager – produces daily MSCItemSnapshot records:
                           balance, APR, daily interest, cumulative interest
                           Rate = SSR + 0.3% APY premium
```

## Tech stack

- **Python 3.13+** with `uv` for dependency management
- **Tortoise ORM** + **PostgreSQL** for persistence
- **Valkey** (Redis-compatible) for block-progress checkpoints and the ARQ job queue
- **chain-harvester** for Ethereum RPC and HyperSync data access
- **ARQ** for async background workers
- **Docker / docker-compose** for local development

## Requirements

- Docker and Docker Compose
- An [Alchemy](https://www.alchemy.com/) API key (primary RPC)
- An [Envio HyperSync](https://envio.dev/) API key (optional, enabled by default)

## Setup

1. Copy the example env file and fill in your keys:

   ```bash
   cp .env.example .env
   # set ALCHEMY_RPC_KEY, ENVIO_API_KEY, DB_URL, etc.
   ```

2. Start the services:

   ```bash
   docker compose up -d
   ```

3. Run migrations:

   ```bash
   docker compose exec web aerich upgrade
   ```

## Running the sync

Run all pipeline stages in order:

```bash
python src/cli.py core sync-all
```

Or run each stage individually:

```bash
# Stage 1 – index raw events
python src/cli.py events vat
python src/cli.py events ssr

# Stage 2 – derive urn position states
python src/cli.py agents urns

# Stage 3 – compute daily debt snapshots
python src/cli.py msc debt
```

The `sync-all` command accepts `--delete` to wipe all model data before re-syncing from scratch.

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `DB_URL` | PostgreSQL connection string | required |
| `ALCHEMY_RPC_KEY` | Alchemy API key for RPC access | required |
| `ENVIO_API_KEY` | Envio HyperSync API key | `""` |
| `USE_HYPERSYNC` | Use HyperSync instead of direct RPC | `true` |
| `ARQ_REDIS_HOST` | Valkey/Redis host | `""` |
| `ARQ_REDIS_PORT` | Valkey/Redis port | `6379` |
| `ARQ_REDIS_DB` | Valkey/Redis database index | `0` |
| `ETHEREUM_RPC_STEP` | Block range per RPC batch (Ethereum) | `10000` |
| `CHAIN_HARVESTER_LOG_LEVEL` | Log level for chain-harvester | `INFO` |

## Development

```bash
# Format and lint
make format

# Open an interactive shell with the app context loaded
make shell
```

## Database utilities

```bash
# Dump the database via ECS task
make dbdump DB_NAME=sky PREFIX=pre-migration

# Download a dump from S3
make download_dump DB_NAME=sky FILE=sky-pre-migration.dump

# Restore locally
make dbrestore FILE=sky-pre-migration.dump
```
