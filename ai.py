from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.ai_service import AIService

router = APIRouter()

class AlertDismissRequest(BaseModel):
    status: str = Field("Dismissed", description="Active, Reviewed, or Dismissed")
    notes: Optional[str] = Field(None, description="Operator review notes")

# ==============================================================================
# 1. DEMAND FORECASTING
# ==============================================================================
@router.get("/forecast", summary="AI Demand Forecasting (Linear Regression / Baseline)")
def get_demand_forecast(
    crop: str = Query("Wheat", description="Agricultural crop name"),
    days: int = Query(14, ge=7, le=60, description="Forecast horizon period in days"),
    db: Session = Depends(get_db)
):
    """
    Computes explainable statistical demand forecasts for agricultural commodities.
    Uses linear regression on historical buyer orders when sufficient data exists (>=3),
    or provides a calibrated baseline estimate with honest limitation disclosure.
    """
    return AIService.get_demand_forecast(db=db, crop_name=crop, forecast_days=days)


# ==============================================================================
# 2. PRICE INTELLIGENCE & INDICATIVE MSP
# ==============================================================================
@router.get("/price-intelligence", summary="Crop Price Distribution vs Official CACP MSP")
def get_price_intelligence(
    crop: str = Query("Wheat", description="Target crop name"),
    db: Session = Depends(get_db)
):
    """
    Returns live marketplace listing price statistics (min, max, average, median)
    and evaluates against verified official CACP Minimum Support Price (MSP) benchmarks
    for the 2024-25 season where applicable.
    """
    return AIService.get_price_intelligence(db=db, crop_name=crop)


# ==============================================================================
# 3. STATISTICAL ANOMALY DETECTION & REVIEW
# ==============================================================================
@router.get("/anomalies", summary="Statistical Anomaly Surveillance Feed")
def get_anomaly_alerts(db: Session = Depends(get_db)):
    """
    Scans live crop listings and buyer orders for price inflation spikes,
    predatory distress dumping, or hoarding volume anomalies.
    Safe against small-sample false positives.
    """
    return AIService.detect_anomalies(db=db)


@router.patch("/anomalies/{alert_id}/dismiss", summary="Dismiss or Mark Anomaly Alert as Reviewed")
def dismiss_anomaly_alert(
    alert_id: str,
    req: AlertDismissRequest = None,
    db: Session = Depends(get_db)
):
    """
    Allows operators to review or dismiss an anomaly alert.
    Persists status in database.
    """
    status_val = req.status if req else "Dismissed"
    notes_val = req.notes if req else "Reviewed via AgriLink dashboard"
    return AIService.dismiss_anomaly_alert(
        db=db,
        alert_id=alert_id,
        status=status_val,
        notes=notes_val
    )


# ==============================================================================
# 4. MULTILINGUAL CROP ADVISORY
# ==============================================================================
@router.get("/advisory", summary="Multilingual Post-Harvest Storage & Handling Advisory")
def get_crop_advisory(
    crop: str = Query("Wheat", description="Crop name"),
    lang: str = Query("en", description="Language code: en (English), hi (Hindi), pa (Punjabi)")
):
    """
    Provides curated, practical post-harvest recommendations including optimal
    moisture thresholds, storage temperatures, pest prevention, and packaging.
    """
    return AIService.get_crop_advisory(crop_name=crop, lang=lang)
