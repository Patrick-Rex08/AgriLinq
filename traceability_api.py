from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.marketplace import CropBatch, BlockchainBlock
from app.schemas.marketplace import (
    CropBatchResponse,
    BlockchainBlockResponse,
    BlockchainVerifyResponse,
    TraceabilityTimelineResponse,
)
from app.services.blockchain import BlockchainService

router = APIRouter()

class ProvenanceEventCreate(BaseModel):
    batch_id: str = Field(..., min_length=2, description="Target crop batch ID")
    event_type: str = Field(..., min_length=2, description="QUALITY_INSPECTION, COLD_STORAGE, DISPATCH, DELIVERY_HANDOVER")
    actor: str = Field(..., min_length=2, description="Actor name and role (e.g., APMC Quality Inspector)")
    location: str = Field(..., min_length=2, description="Inspection or transit location")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured event payload metadata")


# ==============================================================================
# TRACEABILITY & BLOCKCHAIN REST API ENDPOINTS
# ==============================================================================

@router.get("/traceability/{batch_id}", summary="Get complete cryptographic batch provenance timeline")
def get_batch_traceability(batch_id: str, db: Session = Depends(get_db)):
    """
    Returns the complete soil-to-sale lifecycle provenance timeline for a specific batch,
    including all SHA-256 mined blocks, QR code payload, and cryptographic chain audit.
    """
    batch = db.query(CropBatch).filter(CropBatch.batch_id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail=f"Crop batch '{batch_id}' not found.")

    events = BlockchainService.get_batch_events(db, batch_id)
    verification = BlockchainService.verify_ledger(db)

    qr_payload = f"https://agrilink.in/traceability/{batch_id}"

    return {
        "batch": batch,
        "events": events,
        "qr_code_payload": qr_payload,
        "verification_status": "CRYPTOGRAPHICALLY_VERIFIED" if verification["chain_valid"] else "TAMPER_DETECTED",
        "chain_audit": verification
    }


@router.post("/traceability/record-event", response_model=BlockchainBlockResponse, status_code=status.HTTP_201_CREATED, summary="Append verifiable provenance event")
def record_provenance_event(event_in: ProvenanceEventCreate, db: Session = Depends(get_db)):
    """
    Appends a new immutable provenance block to the blockchain ledger.
    Mines block with SHA-256 and mathematical hash chaining.
    """
    batch = db.query(CropBatch).filter(CropBatch.batch_id == event_in.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail=f"Crop batch '{event_in.batch_id}' not found.")

    new_block = BlockchainService.record_event(
        db=db,
        batch_id=event_in.batch_id,
        event_type=event_in.event_type.upper().strip(),
        actor=event_in.actor.strip(),
        location=event_in.location.strip(),
        details=event_in.details
    )
    return new_block


@router.get("/blockchain/blocks", response_model=List[BlockchainBlockResponse], summary="Inspect blockchain ledger blocks")
def get_all_blocks(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """
    Retrieves all mined blocks on the AgriLink blockchain ledger in chronological order.
    """
    return db.query(BlockchainBlock).order_by(BlockchainBlock.index.asc()).limit(limit).all()


@router.get("/blockchain/verify", response_model=BlockchainVerifyResponse, summary="Cryptographically audit the ledger")
def audit_ledger(db: Session = Depends(get_db)):
    """
    Recomputes SHA-256 hashes and verifies previous-hash chaining for every block
    from Genesis to chain tip. Confirms zero tampering.
    """
    return BlockchainService.verify_ledger(db)
