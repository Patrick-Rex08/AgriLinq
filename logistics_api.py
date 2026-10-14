from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.marketplace import LogisticsRoute, CropBatch
from app.schemas.marketplace import LogisticsRouteResponse
from app.services.logistics import LogisticsService, FLEET_SPECIFICATIONS

router = APIRouter()

# Pydantic Request Schemas
class RouteCalculateRequest(BaseModel):
    origin: str = Field(..., min_length=2, description="Origin farm or mandi location")
    destination: str = Field(..., min_length=2, description="Destination mandi or buyer depot")
    cargo_weight_kg: float = Field(..., gt=0, description="Total cargo weight in kg")

class CreateDispatchRequest(BaseModel):
    origin: str = Field(..., min_length=2)
    destination: str = Field(..., min_length=2)
    cargo_weight_kg: float = Field(..., gt=0)
    crop_name: Optional[str] = "Produce"
    batch_id: Optional[str] = None

class ConsolidateDispatchRequest(BaseModel):
    batch_ids: List[str] = Field(..., min_length=1, description="List of batch IDs to consolidate")
    destination: str = Field(..., min_length=2, description="Common destination hub")

class RouteStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="SCHEDULED, DISPATCHED, IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED")


# ==============================================================================
# LOGISTICS REST API ENDPOINTS
# ==============================================================================

@router.get("", response_model=List[LogisticsRouteResponse], summary="List all logistics delivery routes")
def list_routes(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """Retrieves all active and historical logistics delivery routes."""
    query = db.query(LogisticsRoute)
    if status_filter:
        query = query.filter(LogisticsRoute.status == status_filter.upper())
    return query.order_by(LogisticsRoute.created_at.desc()).all()


@router.get("/hubs", summary="List recognized agricultural mandi hubs")
def list_hubs():
    """Returns all coordinate-mapped Indian APMC agricultural trade hubs."""
    return LogisticsService.get_supported_hubs()


@router.get("/fleet", summary="List commercial freight fleet specifications")
def list_fleet():
    """Returns commercial vehicle capacity, rate per km, and CO2 emission matrix."""
    return FLEET_SPECIFICATIONS


@router.post("/calculate", summary="Simulate route distance, vehicle, freight cost & CO2")
def calculate_route_metrics(req: RouteCalculateRequest):
    """
    On-demand route simulation. Computes distance, vehicle matching,
    payload utilization, freight cost breakdown, and CO2 emissions without saving to DB.
    """
    return LogisticsService.calculate_freight_metrics(
        origin_str=req.origin,
        dest_str=req.destination,
        qty_kg=req.cargo_weight_kg
    )


@router.post("/dispatch", response_model=LogisticsRouteResponse, status_code=status.HTTP_201_CREATED, summary="Create & schedule dispatch run")
def create_dispatch_run(req: CreateDispatchRequest, db: Session = Depends(get_db)):
    """
    Creates and schedules an active freight delivery route in the persistent database.
    """
    route = LogisticsService.generate_delivery_plan(
        db=db,
        origin_str=req.origin,
        dest_str=req.destination,
        qty_kg=req.cargo_weight_kg,
        batch_id=req.batch_id
    )
    return route


@router.post("/consolidate", summary="Multi-Farm Order Consolidation Optimizer")
def consolidate_multi_farm(req: ConsolidateDispatchRequest, db: Session = Depends(get_db)):
    """
    Consolidates multiple farm batches into a single high-efficiency freight route.
    Returns financial savings in ₹ and green CO2 emission reductions compared to separate shipments.
    """
    try:
        return LogisticsService.consolidate_multi_farm_dispatch(
            db=db,
            batch_ids=req.batch_ids,
            destination_str=req.destination
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Consolidation optimization failed: {str(exc)}")


@router.get("/{route_id}", response_model=LogisticsRouteResponse, summary="Get route details by route_id")
def get_route_by_id(route_id: str, db: Session = Depends(get_db)):
    """Retrieves route details and transit tracking steps."""
    route = db.query(LogisticsRoute).filter(LogisticsRoute.route_id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found.")
    return route


@router.patch("/{route_id}/status", response_model=LogisticsRouteResponse, summary="Advance transit milestone status")
def update_route_status(route_id: str, req: RouteStatusUpdateRequest, db: Session = Depends(get_db)):
    """
    Advances tracking milestone status (SCHEDULED -> DISPATCHED -> IN_TRANSIT -> OUT_FOR_DELIVERY -> DELIVERED).
    """
    try:
        updated = LogisticsService.update_route_status(
            db=db,
            route_id=route_id,
            new_status=req.status
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update route status: {str(exc)}")
