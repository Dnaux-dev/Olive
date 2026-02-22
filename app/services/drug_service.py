"""
Drug Service
Handles drug matching, generic finding, and Emdex API integration
"""

import requests
import json
import logging
from typing import List, Dict, Optional, Tuple
from config import get_settings
from .database_service import get_db_service
from .ai_service import get_ai_service
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Generic:
    """Generic drug information"""
    def __init__(self, name: str, price_naira: float, manufacturer: str, savings: float = 0):
        self.name = name
        self.price_naira = price_naira
        self.manufacturer = manufacturer
        self.savings = savings
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'price_naira': self.price_naira,
            'manufacturer': self.manufacturer,
            'savings': self.savings
        }

class DrugMatch:
    """Drug matching result"""
    def __init__(self, emdex_id: str, name: str, generic_name: str, 
                 price_naira: float, manufacturer: str):
        self.emdex_id = emdex_id
        self.name = name
        self.generic_name = generic_name
        self.price_naira = price_naira
        self.manufacturer = manufacturer
        self.generics: List[Generic] = []
    
    def to_dict(self) -> Dict:
        return {
            'emdex_id': self.emdex_id,
            'name': self.name,
            'generic_name': self.generic_name,
            'price_naira': self.price_naira,
            'manufacturer': self.manufacturer,
            'generics': [g.to_dict() for g in self.generics]
        }

class DrugService:
    """Drug matching and generics lookup"""
    
    def __init__(self):
        settings = get_settings()
        self.emdex_api_key = settings.emdex_api_key
        self.emdex_api_url = settings.emdex_api_url
        self.db_service = get_db_service()
        self.ai_service = get_ai_service()
    
    async def match_drug_emdex(self, drug_name: str, dosage: str = None) -> Optional[DrugMatch]:
        """
        Match drug against Emdex database.
        Fallback order: local cache -> Emdex API -> Gemini AI -> basic mock.
        """
        # First check local cache
        cached = self._search_local_drugs(drug_name)
        if cached:
            return self._dict_to_drug_match(cached)
        
        # Try Emdex API
        if self.emdex_api_key:
            emdex_result = self._search_emdex(drug_name)
            if emdex_result:
                # Cache the result
                self.db_service.create_drug(emdex_result)
                return self._dict_to_drug_match(emdex_result)
        
        # Fallback: Try Gemini AI
        ai_match = await self._search_via_ai(drug_name)
        if ai_match:
            return ai_match
        
        # Final fallback: create basic match with mock data
        return self._mock_drug_match(drug_name)

    async def _search_via_ai(self, drug_name: str) -> Optional[DrugMatch]:
        """Search for drug details using AI fallback"""
        logger.info(f"Using AI fallback for drug lookup: {drug_name}")
        ai_data = await self.ai_service.lookup_drug_details(drug_name)
        
        if not ai_data or not ai_data.get('name'):
            return None
        
        # Cache the AI result for future use
        drug_dict = {
            'emdex_id': f"AI-{drug_name[:3].upper()}",
            'name': ai_data.get('name'),
            'generic_name': ai_data.get('generic_name'),
            'price_naira': ai_data.get('price_naira', 2000),
            'manufacturer': ai_data.get('manufacturer', 'Unknown'),
            'therapeutic_class': ai_data.get('therapeutic_class'),
            'warnings': json.dumps(ai_data.get('warnings', [])),
            'generics': json.dumps(ai_data.get('generics', []))
        }
        
        self.db_service.create_drug(drug_dict)
        return self._dict_to_drug_match(drug_dict)
    
    def _search_emdex(self, drug_name: str) -> Optional[Dict]:
        """Search Emdex API for drug"""
        try:
            headers = {
                'Authorization': f'Bearer {self.emdex_api_key}',
                'Content-Type': 'application/json'
            }
            
            params = {'search': drug_name, 'limit': 1}
            
            response = requests.get(
                f'{self.emdex_api_url}/drugs/search',
                headers=headers,
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    drug = data['results'][0]
                    return {
                        'emdex_id': drug.get('id'),
                        'name': drug.get('name'),
                        'generic_name': drug.get('generic_name'),
                        'price_naira': drug.get('price', 0),
                        'manufacturer': drug.get('manufacturer'),
                        'therapeutic_class': drug.get('therapeutic_class'),
                        'warnings': json.dumps(drug.get('warnings', [])),
                        'nafdac_verified': drug.get('nafdac_verified', False)
                    }
        except Exception as e:
            print(f"Emdex API error: {e}")
        
        return None
    
    def _search_local_drugs(self, drug_name: str) -> Optional[Dict]:
        """Search local SQLite drug database"""
        return self.db_service.search_drugs(drug_name)[0] if self.db_service.search_drugs(drug_name) else None
    
    def _dict_to_drug_match(self, drug_dict: Dict) -> DrugMatch:
        """Convert database dict to DrugMatch object"""
        match = DrugMatch(
            emdex_id=drug_dict.get('emdex_id'),
            name=drug_dict.get('name'),
            generic_name=drug_dict.get('generic_name', drug_dict.get('name')),
            price_naira=drug_dict.get('price_naira', 0),
            manufacturer=drug_dict.get('manufacturer', 'Unknown')
        )
        
        # Parse generics if stored as JSON
        generics_str = drug_dict.get('generics')
        if generics_str:
            try:
                generics_list = json.loads(generics_str)
                for generic in generics_list:
                    match.generics.append(Generic(
                        name=generic.get('name'),
                        price_naira=generic.get('price_naira', 0),
                        manufacturer=generic.get('manufacturer'),
                        savings=generic.get('savings', 0)
                    ))
            except:
                pass
        
        return match
    
    def _mock_drug_match(self, drug_name: str) -> DrugMatch:
        """Create mock drug match for development"""
        mock_drugs = {
            'amoxicillin': {
                'emdex_id': 'AMX001',
                'name': 'Amoxicillin',
                'generic_name': 'Amoxicillin trihydrate',
                'price_naira': 2500,
                'manufacturer': 'Cipla',
                'generics': [
                    {'name': 'Amoxil', 'price_naira': 2500, 'manufacturer': 'GSK', 'savings': 0},
                    {'name': 'Amoxin', 'price_naira': 1800, 'manufacturer': 'Fidson', 'savings': 700}
                ]
            },
            'paracetamol': {
                'emdex_id': 'PAR001',
                'name': 'Paracetamol',
                'generic_name': 'Acetaminophen',
                'price_naira': 500,
                'manufacturer': 'Emzor',
                'generics': [
                    {'name': 'Tylenol', 'price_naira': 800, 'manufacturer': 'Johnson & Johnson', 'savings': 0},
                    {'name': 'Paramol', 'price_naira': 450, 'manufacturer': 'Juhel', 'savings': 350}
                ]
            }
        }
        
        drug_key = drug_name.lower().strip()
        if drug_key in mock_drugs:
            data = mock_drugs[drug_key]
        else:
            # Generic fallback
            data = {
                'emdex_id': f'{drug_name[:3].upper()}001',
                'name': drug_name,
                'generic_name': drug_name,
                'price_naira': 2000,
                'manufacturer': 'Unknown',
                'generics': []
            }
        
        match = DrugMatch(
            emdex_id=data['emdex_id'],
            name=data['name'],
            generic_name=data['generic_name'],
            price_naira=data['price_naira'],
            manufacturer=data['manufacturer']
        )
        
        for generic in data.get('generics', []):
            match.generics.append(Generic(
                name=generic['name'],
                price_naira=generic['price_naira'],
                manufacturer=generic['manufacturer'],
                savings=generic.get('savings', 0)
            ))
        
        return match
    
    async def get_generics(self, drug_name: str) -> List[Generic]:
        """Get generic alternatives for a drug"""
        match = await self.match_drug_emdex(drug_name)
        return match.generics if match else []
    
    def sync_emdex_cache(self, force: bool = False) -> int:
        """
        Sync Emdex database to local cache
        Returns number of drugs synced
        """
        if not self.emdex_api_key:
            print("Emdex API key not configured, skipping sync")
            return 0
        
        try:
            headers = {
                'Authorization': f'Bearer {self.emdex_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Fetch all drugs (paginated)
            synced_count = 0
            page = 1
            
            while True:
                response = requests.get(
                    f'{self.emdex_api_url}/drugs',
                    headers=headers,
                    params={'page': page, 'limit': 100},
                    timeout=10
                )
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                if not data.get('results'):
                    break
                
                for drug in data['results']:
                    try:
                        self.db_service.create_drug({
                            'emdex_id': drug.get('id'),
                            'name': drug.get('name'),
                            'generic_name': drug.get('generic_name'),
                            'therapeutic_class': drug.get('therapeutic_class'),
                            'price_naira': drug.get('price', 0),
                            'manufacturer': drug.get('manufacturer'),
                            'generics': json.dumps(drug.get('generics', [])),
                            'warnings': json.dumps(drug.get('warnings', [])),
                            'nafdac_verified': drug.get('nafdac_verified', False)
                        })
                        synced_count += 1
                    except Exception as e:
                        print(f"Error caching drug {drug.get('name')}: {e}")
                
                page += 1
            
            print(f"Synced {synced_count} drugs to local cache")
            return synced_count
        
        except Exception as e:
            print(f"Error syncing Emdex cache: {e}")
            return 0

# Singleton instance
_drug_service = None

def get_drug_service() -> DrugService:
    """Get or create drug service instance"""
    global _drug_service
    if _drug_service is None:
        _drug_service = DrugService()
    return _drug_service
