"""
Drug Database API Endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List
from ..models import (
    DrugResponse, DrugSearchResponse, GenericResponse, SuccessResponse,
    DrugVerificationRequest, DrugVerificationResponse
)
from ..services.drug_service import get_drug_service
from ..services.database_service import get_db_service
from ..services.verification_service import get_verification_service

router = APIRouter(prefix="/api/drugs", tags=["drugs"])

@router.post("/verify", response_model=DrugVerificationResponse)
def verify_drug(request: DrugVerificationRequest):
    """Verify a drug by its NAFDAC registration number"""
    verification_service = get_verification_service()
    result = verification_service.verify_drug(request.reg_number)
    return DrugVerificationResponse(**result)

@router.get("/search", response_model=DrugSearchResponse)
async def search_drugs(query: str):
    """Search drugs by name"""
    if not query or len(query) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    
    db_service = get_db_service()
    drug_service = get_drug_service()
    
    try:
        # Search local database first
        results = db_service.search_drugs(query)
        
        # If no results, try Emdex API
        if not results:
            match = await drug_service.match_drug_emdex(query)
            if match:
                results = [match.to_dict()]
        
        drugs = [DrugResponse(**d) for d in results] if results else []
        return DrugSearchResponse(results=drugs)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{emdex_id}", response_model=DrugResponse)
def get_drug(emdex_id: str):
    """Get drug by Emdex ID"""
    db_service = get_db_service()
    drug_service = get_drug_service()
    
    # Search local cache
    drug = db_service.get_drug(emdex_id)
    
    if not drug:
        # Not in cache
        raise HTTPException(status_code=404, detail="Drug not found")
    
    from app.services.drug_service import DrugMatch
    match = DrugMatch(
        emdex_id=drug.get('emdex_id'),
        name=drug.get('name'),
        generic_name=drug.get('generic_name'),
        price_naira=drug.get('price_naira', 0),
        manufacturer=drug.get('manufacturer')
    )
    
    # Parse generics
    import json
    generics_str = drug.get('generics')
    if generics_str:
        try:
            generics_list = json.loads(generics_str)
            for generic in generics_list:
                from app.services.drug_service import Generic
                match.generics.append(Generic(
                    name=generic.get('name'),
                    price_naira=generic.get('price_naira', 0),
                    manufacturer=generic.get('manufacturer'),
                    savings=generic.get('savings', 0)
                ))
        except:
            pass
    
    return DrugResponse(**match.to_dict())

@router.get("/{drug_name}/generics", response_model=List[GenericResponse])
async def get_drug_generics(drug_name: str):
    """Get generic alternatives for a drug"""
    drug_service = get_drug_service()
    
    try:
        generics = await drug_service.get_generics(drug_name)
        return [GenericResponse(**g.to_dict()) for g in generics]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-emdex", response_model=SuccessResponse)
def sync_emdex_database(force: bool = False):
    """Sync Emdex drug database to local cache"""
    drug_service = get_drug_service()
    
    try:
        synced_count = drug_service.sync_emdex_cache(force=force)
        
        return SuccessResponse(
            success=True,
            message=f"Synced {synced_count} drugs from Emdex",
            data={'synced_count': synced_count}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prices/compare", response_model=SuccessResponse)
async def compare_drug_prices(drug_name: str):
    """Compare prices for drug and its generics"""
    drug_service = get_drug_service()
    
    try:
        match = await drug_service.match_drug_emdex(drug_name)
        
        if not match:
            raise HTTPException(status_code=404, detail="Drug not found")
        
        prices = {
            'original': {
                'name': match.name,
                'price': match.price_naira,
                'manufacturer': match.manufacturer
            },
            'generics': [
                {
                    'name': g.name,
                    'price': g.price_naira,
                    'manufacturer': g.manufacturer,
                    'savings': g.savings
                }
                for g in match.generics
            ]
        }
        
        return SuccessResponse(
            success=True,
            message="Price comparison",
            data=prices
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
