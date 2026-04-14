APP_NAME = "Sky"


def configure_settings(settings, env):
    db_url = env("DB_URL")
    # increase pool size to 10 (overrides tortoise default which is 5)
    db_url += "?max_size=10"

    settings["TORTOISE_ORM"] = {
        "connections": {
            "default": db_url,
        },
        "apps": {
            "core": {
                "models": ["core.models"],
                "default_connection": "default",
                "migrations": "core.migrations",
            },
        },
    }

    alchemy_rpc_key = env("ALCHEMY_RPC_KEY", "")
    settings["ALCHEMY_RPC_KEY"] = alchemy_rpc_key

    settings["HYPERSYNC_API_KEY"] = env("ENVIO_API_KEY", default="")
    settings["USE_HYPERSYNC"] = env.bool("USE_HYPERSYNC", default=True)

    settings["RPC_NODES"] = {
        "ethereum": {
            "mainnet": f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_rpc_key}",
        },
        "base": {
            "mainnet": f"https://base-mainnet.g.alchemy.com/v2/{alchemy_rpc_key}",
        },
        "arbitrum": {
            "mainnet": f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_rpc_key}",
        },
        "optimism": {
            "mainnet": f"https://opt-mainnet.g.alchemy.com/v2/{alchemy_rpc_key}",
        },
        "unichain": {
            "mainnet": f"https://unichain-mainnet.g.alchemy.com/v2/{alchemy_rpc_key}",
        },
        "avalanche": {
            "mainnet": f"https://avax-mainnet.g.alchemy.com/v2/{alchemy_rpc_key}",
        },
        "plasma": {
            "mainnet": f"https://plasma-mainnet.g.alchemy.com/v2/{alchemy_rpc_key}",
        },
        "plume": {
            "mainnet": "https://rpc.plume.org",
        },
        "monad": {
            "mainnet": f"https://monad-mainnet.g.alchemy.com/v2/{alchemy_rpc_key}",
        },
        "hyperliquid": {
            "mainnet": env("HYPERLIQUID_RPC", default=""),
        },
    }

    settings["ETHERSCAN_API_KEY"] = env("ETHERSCAN_API_KEY", "")

    settings["ETHEREUM_RPC_STEP"] = env.int("ETHEREUM_RPC_STEP", 10_000)
    settings["BASE_RPC_STEP"] = env.int("BASE_RPC_STEP", 10_000)
    settings["ARBITRUM_RPC_STEP"] = env.int("ARBITRUM_RPC_STEP", 10_000)
    settings["OPTIMISM_RPC_STEP"] = env.int("OPTIMISM_RPC_STEP", 10_000)
    settings["UNICHAIN_RPC_STEP"] = env.int("UNICHAIN_RPC_STEP", 10_000)
    settings["AVALANCHE_RPC_STEP"] = env.int("AVALANCHE_RPC_STEP", 10_000)
    settings["PLASMA_RPC_STEP"] = env.int("PLASMA_RPC_STEP", 10_000)
    settings["PLUME_RPC_STEP"] = env.int("PLUME_RPC_STEP", 10_000)
    settings["MONAD_RPC_STEP"] = env.int("MONAD_RPC_STEP", 1_000)
    settings["HYPERLIQUID_RPC_STEP"] = env.int("HYPERLIQUID_RPC_STEP", 10_000)

    settings["ARQ_REDIS_HOST"] = env("ARQ_REDIS_HOST", "")
    settings["ARQ_REDIS_PORT"] = env.int("ARQ_REDIS_PORT", 6379)
    settings["ARQ_REDIS_DB"] = env.int("ARQ_REDIS_DB", 0)
    settings["ARQ_HEARTBEAT_URL"] = env("ARQ_HEARTBEAT_URL", "")

    settings["S3_BUCKET_NAME"] = "abis-787309967787"

    settings["IS_ONE_OFF_CMD"] = env.bool("IS_ONE_OFF_CMD", default=False)

    settings["CHAIN_HARVESTER_LOG_LEVEL"] = env("CHAIN_HARVESTER_LOG_LEVEL", default="INFO")

    settings["LOGGING_CONFIG"]["loggers"].update(
        {
            "chain_harvester": {
                "propagate": True,
                "level": settings["CHAIN_HARVESTER_LOG_LEVEL"],
            },
            "events": {
                "propagate": True,
                "level": settings["APP_LOG_LEVEL"],
            },
            "agents": {
                "propagate": True,
                "level": settings["APP_LOG_LEVEL"],
            },
            "msc": {
                "propagate": True,
                "level": settings["APP_LOG_LEVEL"],
            },
            "core": {
                "propagate": True,
                "level": settings["APP_LOG_LEVEL"],
            },
        }
    )
    return settings
