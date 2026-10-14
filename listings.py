from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.models.marketplace import CropBatch, BuyerOrder, TradeMatch
from app.schemas.marketplace import (
    ListingCreate,
    ListingUpdate,
    ListingResponse,
    OrderCreate,
    OrderStatusUpdate,
    OrderResponse,
)
from app.services.blockchain import BlockchainService
from app.services.logistics import LogisticsService

router = APIRouter()

# Helper to find crop batch by either integer ID or string batch_id
def get_crop_batch_or_404(identifier: str, db: Session) -> CropBatch:
    batch = None
    if identifier.isdigit():
        batch = db.query(CropBatch).filter(CropBatch.id == int(identifier)).first()
    if not batch:
        batch = db.query(CropBatch).filter(CropBatch.batch_id == identifier).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop listing with ID/Batch '{identifier}' not found."
        )
    return batch


# Helper to find buyer order by either integer ID or string order_id
def get_order_or_404(identifier: str, db: Session) -> BuyerOrder:
    order = None
    if identifier.isdigit():
        order = db.query(BuyerOrder).filter(BuyerOrder.id == int(identifier)).first()
    if not order:
        order = db.query(BuyerOrder).filter(BuyerOrder.order_id == identifier).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID '{identifier}' not found."
        )
    return order


# ==============================================================================
# CROP LISTINGS ENDPOINTS
# ==============================================================================

@router.get("/listings", response_model=List[ListingResponse], summary="Retrieve and filter crop listings")
def get_listings(
    crop_name: Optional[str] = Query(None, description="Filter by crop name (case-insensitive substring)"),
    location: Optional[str] = Query(None, description="Filter by farm location"),
    category: Optional[str] = Query(None, description="Filter by crop category"),
    max_price: Optional[float] = Query(None, gt=0, description="Filter by maximum asking price per kg"),
    sort_by: Optional[str] = Query(None, description="Sort order: price_asc, price_desc, qty_asc, qty_desc"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all crop listings from persistent database storage with optional filtering and sorting.
    """
    query = db.query(CropBatch)

    if crop_name and crop_name.strip():
        query = query.filter(CropBatch.crop_name.ilike(f"%{crop_name.strip()}%"))
    if location and location.strip():
        query = query.filter(CropBatch.farm_location.ilike(f"%{location.strip()}%"))
    if category and category.strip() and category.lower() != "all":
        query = query.filter(CropBatch.category.ilike(category.strip()))
    if max_price is not None:
        query = query.filter(CropBatch.price_per_kg <= max_price)

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(CropBatch.price_per_kg.asc())
    elif sort_by == "price_desc":
        query = query.order_by(CropBatch.price_per_kg.desc())
    elif sort_by == "qty_asc":
        query = query.order_by(CropBatch.available_qty_kg.asc())
    elif sort_by == "qty_desc":
        query = query.order_by(CropBatch.available_qty_kg.desc())
    else:
        query = query.order_by(CropBatch.created_at.desc())

    return query.all()


@router.get("/listings/{identifier}", response_model=ListingResponse, summary="Retrieve a single listing")
def get_single_listing(identifier: str, db: Session = Depends(get_db)):
    """
    Retrieve listing by numeric database ID or string batch_id.
    """
    return get_crop_batch_or_404(identifier, db)


@router.post("/listings", response_model=ListingResponse, status_code=status.HTTP_201_CREATED, summary="Create a new listing")
def create_listing(listing_in: ListingCreate, db: Session = Depends(get_db)):
    """
    Farmer lists agricultural produce with verified positive quantity and price.
    Persists to database and creates initial provenance blockchain event.
    """
    if listing_in.quantity_kg <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0 kg.")
    if listing_in.price_per_kg <= 0:
        raise HTTPException(status_code=400, detail="Price per kg must be greater than 0.")

    clean_crop = listing_in.crop_name.strip()
    batch_id = listing_in.batch_id or f"BATCH-{clean_crop[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"

    # Check for existing batch_id to prevent duplicates
    existing = db.query(CropBatch).filter(CropBatch.batch_id == batch_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Batch ID '{batch_id}' already exists.")

    new_batch = CropBatch(
        batch_id=batch_id,
        farmer_name=listing_in.farmer_name.strip(),
        farmer_phone=listing_in.farmer_phone or "9876543210",
        crop_name=clean_crop,
        variety=listing_in.variety.strip() if listing_in.variety else None,
        category=listing_in.category or "Grains",
        quantity_kg=listing_in.quantity_kg,
        available_qty_kg=listing_in.quantity_kg,
        price_per_kg=listing_in.price_per_kg,
        farm_location=listing_in.farm_location.strip(),
        mandi_name=listing_in.mandi_name,
        harvest_date=listing_in.harvest_date.strip(),
        quality_grade=listing_in.quality_grade or "Grade A",
        status="LISTED"
    )

    try:
        db.add(new_batch)
        db.commit()
        db.refresh(new_batch)

        # Record provenance block on blockchain ledger
        BlockchainService.record_event(
            db=db,
            batch_id=new_batch.batch_id,
            event_type="HARVEST_AND_LISTED",
            actor=f"Farmer: {new_batch.farmer_name}",
            location=new_batch.farm_location,
            details={
                "crop": new_batch.crop_name,
                "variety": new_batch.variety,
                "quantity_kg": new_batch.quantity_kg,
                "price_per_kg": new_batch.price_per_kg,
                "harvest_date": new_batch.harvest_date,
                "quality_grade": new_batch.quality_grade
            }
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create listing: {str(exc)}")

    return new_batch


@router.put("/listings/{identifier}", response_model=ListingResponse, summary="Update an existing listing")
def update_listing(identifier: str, listing_in: ListingUpdate, db: Session = Depends(get_db)):
    """
    Update listing attributes (quantity, price, location, harvest date, grade, status).
    """
    batch = get_crop_batch_or_404(identifier, db)

    try:
        if listing_in.quantity_kg is not None:
            if listing_in.quantity_kg <= 0:
                raise HTTPException(status_code=400, detail="Quantity must be greater than 0 kg.")
            diff = listing_in.quantity_kg - batch.quantity_kg
            batch.quantity_kg = listing_in.quantity_kg
            batch.available_qty_kg = max(0.0, batch.available_qty_kg + diff)

        if listing_in.price_per_kg is not None:
            if listing_in.price_per_kg <= 0:
                raise HTTPException(status_code=400, detail="Price per kg must be greater than 0.")
            batch.price_per_kg = listing_in.price_per_kg

        if listing_in.farmer_name is not None:
            batch.farmer_name = listing_in.farmer_name.strip()
        if listing_in.farmer_phone is not None:
            batch.farmer_phone = listing_in.farmer_phone.strip()
        if listing_in.crop_name is not None:
            batch.crop_name = listing_in.crop_name.strip()
        if listing_in.variety is not None:
            batch.variety = listing_in.variety.strip()
        if listing_in.category is not None:
            batch.category = listing_in.category.strip()
        if listing_in.farm_location is not None:
            batch.farm_location = listing_in.farm_location.strip()
        if listing_in.harvest_date is not None:
            batch.harvest_date = listing_in.harvest_date.strip()
        if listing_in.quality_grade is not None:
            batch.quality_grade = listing_in.quality_grade.strip()
        if listing_in.status is not None:
            batch.status = listing_in.status.strip()

        db.commit()
        db.refresh(batch)
        return batch
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update listing: {str(exc)}")


@router.delete("/listings/{identifier}", summary="Delete an existing listing")
def delete_listing(identifier: str, db: Session = Depends(get_db)):
    """
    Delete a listing from the persistent database.
    """
    batch = get_crop_batch_or_404(identifier, db)
    batch_id = batch.batch_id
    try:
        db.delete(batch)
        db.commit()
        return {"status": "success", "message": f"Listing {batch_id} removed successfully."}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete listing: {str(exc)}")


# ==============================================================================
# BUYER ORDERS ENDPOINTS (ACID TRANSACTION GUARANTEED)
# ==============================================================================

@router.get("/orders", response_model=List[OrderResponse], summary="Retrieve all buyer orders")
def get_orders(db: Session = Depends(get_db)):
    """
    Retrieve all buyer procurement orders stored in the persistent database.
    """
    return db.query(BuyerOrder).order_by(BuyerOrder.created_at.desc()).all()


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, summary="Place buyer order with stock deduction")
def place_order(order_in: OrderCreate, db: Session = Depends(get_db)):
    """
    Places an order.
    - If batch_id or listing_id is provided: performs atomic stock verification and deduction
      within a single database transaction. If requested quantity exceeds stock or any step fails,
      the transaction is rolled back immediately.
    - If neither is provided: creates an open procurement demand order.
    """
    qty = order_in.quantity_kg or order_in.required_qty_kg
    if not qty or qty <= 0:
        raise HTTPException(status_code=400, detail="Order quantity must be a positive number greater than 0 kg.")

    target_batch = None
    if order_in.batch_id:
        target_batch = db.query(CropBatch).filter(CropBatch.batch_id == order_in.batch_id).first()
    elif order_in.listing_id:
        target_batch = db.query(CropBatch).filter(CropBatch.id == order_in.listing_id).first()

    order_id = order_in.order_id or f"ORD-{uuid.uuid4().hex[:6].upper()}"

    try:
        if target_batch:
            # DIRECT PURCHASE FROM LISTING
            if qty > target_batch.available_qty_kg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Requested quantity of {qty:,.0f} kg exceeds available stock of {target_batch.available_qty_kg:,.0f} kg."
                )

            unit_price = target_batch.price_per_kg
            total_price = round(qty * unit_price, 2)

            # Deduct inventory stock
            target_batch.available_qty_kg -= qty
            if target_batch.available_qty_kg <= 0:
                target_batch.available_qty_kg = 0.0
                target_batch.status = "MATCHED"

            new_order = BuyerOrder(
                order_id=order_id,
                batch_id=target_batch.batch_id,
                buyer_name=order_in.buyer_name.strip(),
                buyer_phone=order_in.buyer_phone.strip() if order_in.buyer_phone else None,
                crop_name=target_batch.crop_name,
                required_qty_kg=qty,
                fulfilled_qty_kg=qty,
                max_price_per_kg=unit_price,
                total_price=total_price,
                delivery_location=order_in.delivery_location.strip(),
                status="Confirmed"
            )
            db.add(new_order)

            # Also record matched trade for complete system traceability
            match_id = f"MTH-{uuid.uuid4().hex[:8].upper()}"
            trade_match = TradeMatch(
                match_id=match_id,
                batch_id=target_batch.batch_id,
                order_id=order_id,
                crop_name=target_batch.crop_name,
                matched_qty_kg=qty,
                agreed_price_per_kg=unit_price,
                total_value=total_price,
                status="CONFIRMED",
                is_anomaly=False,
                anomaly_score=0.0
            )
            db.add(trade_match)

            # Commit the atomic transaction
            db.commit()
            db.refresh(new_order)
            db.refresh(target_batch)

            # Asynchronously / post-commit record logistics plan and blockchain provenance
            try:
                LogisticsService.generate_delivery_plan(
                    db=db,
                    match=trade_match,
                    origin_str=target_batch.farm_location,
                    dest_str=order_in.delivery_location.strip()
                )
                BlockchainService.record_event(
                    db=db,
                    batch_id=target_batch.batch_id,
                    event_type="ORDER_CONFIRMED",
                    actor=f"Buyer: {new_order.buyer_name}",
                    location=order_in.delivery_location.strip(),
                    details={
                        "order_id": order_id,
                        "quantity_kg": qty,
                        "agreed_price": unit_price,
                        "total_value": total_price
                    }
                )
            except Exception:
                # Supplementary services should not break the committed order
                pass

            return new_order

        else:
            # OPEN DEMAND ORDER
            if not order_in.crop_name:
                raise HTTPException(status_code=400, detail="crop_name is required when not purchasing from a specific listing.")
            price = order_in.price_per_kg or order_in.max_price_per_kg
            if not price or price <= 0:
                raise HTTPException(status_code=400, detail="Price per kg must be greater than 0.")

            total_price = round(qty * price, 2)
            new_order = BuyerOrder(
                order_id=order_id,
                batch_id=None,
                buyer_name=order_in.buyer_name.strip(),
                buyer_phone=order_in.buyer_phone.strip() if order_in.buyer_phone else None,
                crop_name=order_in.crop_name.strip(),
                required_qty_kg=qty,
                fulfilled_qty_kg=0.0,
                max_price_per_kg=price,
                total_price=total_price,
                delivery_location=order_in.delivery_location.strip(),
                status="Pending"
            )
            db.add(new_order)
            db.commit()
            db.refresh(new_order)
            return new_order

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order transaction rolled back due to error: {str(exc)}"
        )


@router.patch("/orders/{identifier}/status", response_model=OrderResponse, summary="Update order status")
def update_order_status(identifier: str, status_in: OrderStatusUpdate, db: Session = Depends(get_db)):
    """
    Update an order's fulfillment status (Pending, Confirmed, In Transit, Delivered).
    """
    valid_statuses = ["Pending", "Confirmed", "In Transit", "Delivered", "Cancelled"]
    if status_in.status not in valid_statuses:
        # Check case-insensitive match
        matched_status = next((s for s in valid_statuses if s.lower() == status_in.status.lower()), None)
        if not matched_status:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{status_in.status}'. Allowed: {', '.join(valid_statuses)}"
            )
        status_to_set = matched_status
    else:
        status_to_set = status_in.status

    order = get_order_or_404(identifier, db)
    order.status = status_to_set
    db.commit()
    db.refresh(order)
    return order


# ==============================================================================
# DEMO SEED ENDPOINT
# ==============================================================================

SAMPLE_DEMO_BATCHES = [
    {
        "batch_id": "BATCH-DEMO-WHT-001",
        "farmer_name": "[Demo] Ramesh Kumar (Punjab FPO)",
        "farmer_phone": "9876543210",
        "crop_name": "Wheat",
        "variety": "Sharbati Premium",
        "category": "Grains",
        "quantity_kg": 5000.0,
        "price_per_kg": 26.50,
        "farm_location": "Khanna, Punjab",
        "harvest_date": "2026-10-05",
        "quality_grade": "Grade A"
    },
    {
        "batch_id": "BATCH-DEMO-RIC-002",
        "farmer_name": "[Demo] Gurpreet Singh (Kisan Producer)",
        "farmer_phone": "9812345678",
        "crop_name": "Basmati Rice",
        "variety": "1121 Extra Long",
        "category": "Grains",
        "quantity_kg": 3500.0,
        "price_per_kg": 62.00,
        "farm_location": "Karnal, Haryana",
        "harvest_date": "2026-10-08",
        "quality_grade": "Export Quality"
    },
    {
        "batch_id": "BATCH-DEMO-SOY-003",
        "farmer_name": "[Demo] Suresh Patel (Malwa Agro)",
        "farmer_phone": "9765432109",
        "crop_name": "Soybean",
        "variety": "JS-335 Organic",
        "category": "Oilseeds",
        "quantity_kg": 4200.0,
        "price_per_kg": 48.00,
        "farm_location": "Indore, Madhya Pradesh",
        "harvest_date": "2026-10-02",
        "quality_grade": "Grade A"
    },
    {
        "batch_id": "BATCH-DEMO-CHL-004",
        "farmer_name": "[Demo] Ananya Sharma (GreenRoots)",
        "farmer_phone": "9988776655",
        "crop_name": "Red Chilli",
        "variety": "Guntur Sannam",
        "category": "Spices",
        "quantity_kg": 1200.0,
        "price_per_kg": 140.00,
        "farm_location": "Guntur, Andhra Pradesh",
        "harvest_date": "2026-10-06",
        "quality_grade": "Export Quality"
    },
    {
        "batch_id": "BATCH-DEMO-POT-005",
        "farmer_name": "[Demo] Mohan Lal (Agra Potato Union)",
        "farmer_phone": "9823456789",
        "crop_name": "Potato",
        "variety": "Kufri Jyoti",
        "category": "Vegetables",
        "quantity_kg": 6000.0,
        "price_per_kg": 16.50,
        "farm_location": "Agra, Uttar Pradesh",
        "harvest_date": "2026-10-09",
        "quality_grade": "Grade B"
    }
]

@router.post("/seed", summary="Safely seed demonstration sample listings and orders")
def seed_demo_data(force: bool = False, db: Session = Depends(get_db)):
    """
    Safely seeds initial demonstration crop listings and sample orders.
    Identifiable by '[Demo]' prefixes.
    Does NOT overwrite or delete existing user data.
    """
    existing_count = db.query(CropBatch).count()
    if existing_count > 0 and not force:
        return {
            "status": "skipped",
            "message": f"Database already contains {existing_count} listings. Pass ?force=true to insert demo records.",
            "total_listings": existing_count
        }

    seeded_batches = 0
    for item in SAMPLE_DEMO_BATCHES:
        exists = db.query(CropBatch).filter(CropBatch.batch_id == item["batch_id"]).first()
        if not exists:
            b = CropBatch(
                batch_id=item["batch_id"],
                farmer_name=item["farmer_name"],
                farmer_phone=item["farmer_phone"],
                crop_name=item["crop_name"],
                variety=item["variety"],
                category=item["category"],
                quantity_kg=item["quantity_kg"],
                available_qty_kg=item["quantity_kg"],
                price_per_kg=item["price_per_kg"],
                farm_location=item["farm_location"],
                harvest_date=item["harvest_date"],
                quality_grade=item["quality_grade"],
                status="LISTED"
            )
            db.add(b)
            seeded_batches += 1

    db.commit()

    # Seed 1-2 demo orders if none exist
    order_count = db.query(BuyerOrder).count()
    seeded_orders = 0
    if order_count == 0 or force:
        demo_order = BuyerOrder(
            order_id="ORD-DEMO-001",
            batch_id="BATCH-DEMO-WHT-001",
            buyer_name="[Demo] AgroMarts Wholesale",
            buyer_phone="9876501234",
            crop_name="Wheat",
            required_qty_kg=1000.0,
            fulfilled_qty_kg=1000.0,
            max_price_per_kg=26.50,
            total_price=26500.0,
            delivery_location="Azadpur Mandi, Delhi",
            status="In Transit"
        )
        db.add(demo_order)
        # Deduct from batch
        target_b = db.query(CropBatch).filter(CropBatch.batch_id == "BATCH-DEMO-WHT-001").first()
        if target_b:
            target_b.available_qty_kg = max(0.0, target_b.available_qty_kg - 1000.0)
        seeded_orders += 1
        db.commit()

    return {
        "status": "success",
        "message": f"Seeded {seeded_batches} sample listings and {seeded_orders} sample orders.",
        "total_listings": db.query(CropBatch).count(),
        "total_orders": db.query(BuyerOrder).count()
    }
