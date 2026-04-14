from bakit import settings
from chain_harvester_async.networks import (
    ArbitrumMainnetChain,
    AvalancheMainnetChain,
    BaseMainnetChain,
    EthereumMainnetChain,
    HyperliquidMainnetChain,
    MonadMainnetChain,
    OptimismMainnetChain,
    PlasmaMainnetChain,
    PlumeMainnetChain,
    UnichainMainnetChain,
)

from events.block_store import SkyBlockStore


def get_chain_async(network):
    default_settings = {
        "rpc_nodes": settings.RPC_NODES,
        "etherscan_api_key": settings.ETHERSCAN_API_KEY,
        "s3": {
            "bucket_name": settings.S3_BUCKET_NAME,
            "dir": settings.APP_NAME,
        },
        "block_store": SkyBlockStore(),
        "hypersync_api_key": settings.HYPERSYNC_API_KEY,
        "use_hypersync": settings.USE_HYPERSYNC,
    }
    match network:
        case "ethereum_core" | "ethereum_prime" | "ethereum_horizon" | "ethereum":
            return EthereumMainnetChain(step=settings.ETHEREUM_RPC_STEP, **default_settings)
        case "base":
            return BaseMainnetChain(step=settings.BASE_RPC_STEP, **default_settings)
        case "arbitrum":
            return ArbitrumMainnetChain(step=settings.ARBITRUM_RPC_STEP, **default_settings)
        case "optimism":
            return OptimismMainnetChain(step=settings.OPTIMISM_RPC_STEP, **default_settings)
        case "unichain":
            return UnichainMainnetChain(step=settings.UNICHAIN_RPC_STEP, **default_settings)
        case "avalanche":
            default_settings.pop("etherscan_api_key")
            return AvalancheMainnetChain(step=settings.AVALANCHE_RPC_STEP, **default_settings)
        case "plasma":
            default_settings.pop("etherscan_api_key")
            return PlasmaMainnetChain(step=settings.PLASMA_RPC_STEP, **default_settings)
        case "plume":
            default_settings.pop("etherscan_api_key")
            return PlumeMainnetChain(step=settings.PLUME_RPC_STEP, **default_settings)
        case "monad":
            return MonadMainnetChain(step=settings.MONAD_RPC_STEP, **default_settings)
        case "hyperliquid":
            default_settings.pop("etherscan_api_key")
            return HyperliquidMainnetChain(step=settings.HYPERLIQUID_RPC_STEP, **default_settings)
        case _:
            raise ValueError(f"Unknown network: {network}")
