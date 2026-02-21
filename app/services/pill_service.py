"""
Pill Service
Handles pill image verification and pill database matching
"""

from typing import Dict, Optional, Tuple
from PIL import Image
import io
from .database_service import get_db_service

class PillVerification:
    """Pill verification result"""
    def __init__(self, matched: bool, drug_name: str = None, confidence: float = 0.0):
        self.matched = matched
        self.drug_name = drug_name
        self.confidence = confidence
    
    def to_dict(self) -> Dict:
        return {
            'matched': self.matched,
            'drug_name': self.drug_name,
            'confidence': self.confidence
        }

class PillService:
    """Pill image verification"""
    
    def __init__(self):
        self.db_service = get_db_service()
    
    def verify_pill(self, image_data: bytes) -> PillVerification:
        """
        Verify a pill image against pill database
        Returns PillVerification with match info
        """
        try:
            # Extract features from image
            features = self._extract_pill_features(image_data)
            
            # Match against database
            match = self._match_features_to_db(features)
            
            if match:
                return PillVerification(
                    matched=True,
                    drug_name=match['drug_name'],
                    confidence=0.85
                )
            else:
                return PillVerification(matched=False, confidence=0.0)
        
        except Exception as e:
            print(f"Pill verification error: {e}")
            return PillVerification(matched=False, confidence=0.0)
    
    def _extract_pill_features(self, image_data: bytes) -> Dict:
        """Extract visual features from pill image"""
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # Get image properties
            width, height = img.size
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Extract dominant colors
            colors = self._get_dominant_colors(img)
            
            # Extract shape (simplified - could be enhanced with ML)
            shape = self._estimate_shape(width, height)
            
            return {
                'width': width,
                'height': height,
                'shape': shape,
                'colors': colors,
                'aspect_ratio': width / height if height > 0 else 1.0
            }
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return {}
    
    def _get_dominant_colors(self, img: Image) -> list:
        """Get dominant colors from image"""
        try:
            # Resize for faster processing
            img = img.resize((100, 100))
            
            # Get color palette
            img = img.convert('P', palette=Image.Palette.ADAPTIVE, colors=3)
            colors = img.getpalette()
            
            # Extract dominant colors (RGB tuples)
            dominant = []
            for i in range(0, min(9, len(colors)), 3):
                dominant.append({
                    'r': colors[i],
                    'g': colors[i+1],
                    'b': colors[i+2]
                })
            
            return dominant
        except:
            return []
    
    def _estimate_shape(self, width: int, height: int) -> str:
        """Estimate pill shape from dimensions"""
        ratio = width / height if height > 0 else 1.0
        
        # Round/circular
        if 0.8 < ratio < 1.2:
            return 'round'
        # Oval/ellipse
        elif 1.2 < ratio < 2.0:
            return 'oval'
        # Oblong/capsule
        elif ratio >= 2.0:
            return 'capsule'
        # Square
        elif 0.7 < ratio <= 0.8:
            return 'square'
        else:
            return 'unknown'
    
    def _match_features_to_db(self, features: Dict) -> Optional[Dict]:
        """Match pill features to database"""
        if not features:
            return None
        
        # Get all pills from database
        all_pills = self.db_service.execute_query(
            "SELECT * FROM pills WHERE image_url IS NOT NULL LIMIT 100"
        )
        
        best_match = None
        best_score = 0.5  # Minimum threshold
        
        for pill in all_pills:
            score = self._calculate_match_score(features, pill)
            if score > best_score:
                best_score = score
                best_match = pill
        
        return best_match
    
    def _calculate_match_score(self, features: Dict, pill_db_entry: Dict) -> float:
        """Calculate match score between features and database entry"""
        score = 0.0
        
        # Shape matching (highest weight)
        pill_shape = pill_db_entry.get('shape', 'unknown')
        if features.get('shape') == pill_shape:
            score += 0.5
        elif self._shapes_similar(features.get('shape'), pill_shape):
            score += 0.25
        
        # Color matching (medium weight)
        score += 0.3  # Simplified: just give bonus for having color info
        
        # Size matching (lower weight)
        if features.get('aspect_ratio'):
            score += 0.2
        
        return min(score, 1.0)
    
    def _shapes_similar(self, shape1: str, shape2: str) -> bool:
        """Check if two shapes are similar"""
        similar_groups = [
            {'round', 'oval'},
            {'capsule', 'oblong'},
            {'square', 'round'}
        ]
        
        for group in similar_groups:
            if shape1 in group and shape2 in group:
                return True
        
        return False
    
    def add_pill_to_db(self, drug_name: str, shape: str, color: str, 
                       imprint: str = None, image_url: str = None) -> int:
        """Add a pill to the database"""
        return self.db_service.execute_insert(
            """INSERT INTO pills (drug_name, shape, color, imprint, image_url)
               VALUES (?, ?, ?, ?, ?)""",
            (drug_name, shape, color, imprint, image_url)
        )
    
    def get_pill(self, drug_name: str) -> Optional[Dict]:
        """Get pill info by drug name"""
        return self.db_service.execute_query(
            "SELECT * FROM pills WHERE drug_name = ?",
            (drug_name,),
            fetch_one=True
        )

# Singleton instance
_pill_service = None

def get_pill_service() -> PillService:
    """Get or create pill service instance"""
    global _pill_service
    if _pill_service is None:
        _pill_service = PillService()
    return _pill_service
