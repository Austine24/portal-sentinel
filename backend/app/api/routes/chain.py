from fastapi import APIRouter

from app.core.config import get_settings
from app.domain.incidents import ChainConfig
from app.portaldot.registry import SELECTORS

router = APIRouter(prefix="/api/chain", tags=["chain"])


@router.get("/config", response_model=ChainConfig)
def chain_config() -> ChainConfig:
    """Public chain settings the browser needs to build the wallet transaction. Nothing secret."""
    s = get_settings()
    return ChainConfig(
        chain_id=s.portaldot_chain_id,
        rpc_url=s.portaldot_evm_rpc_url,
        explorer_url=s.portaldot_explorer_url,
        registry_address=s.registry_address or None,
        native_symbol="tPOT",
        record_selector=SELECTORS["record"],
    )
