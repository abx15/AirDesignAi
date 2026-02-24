import base64
import io
import re
from typing import Tuple, Optional

import pytesseract
from PIL import Image
import numpy as np


class OCRService:
    def __init__(self):
        # Configure Tesseract for math recognition
        self.tesseract_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789+-×÷=()[]{}^√π∫∑∂∆∇abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.,'
    
    async def extract_math_from_image(self, image_base64: str) -> Tuple[str, float]:
        """
        Extract mathematical expression from base64 image using Tesseract OCR
        """
        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64.split(',')[1] if ',' in image_base64 else image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to grayscale and enhance contrast
            image = image.convert('L')
            image = self._enhance_image(image)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            
            # Clean and normalize the extracted text
            cleaned_text = self._clean_math_text(text)
            
            # Calculate confidence (simplified)
            confidence = self._calculate_confidence(text, cleaned_text)
            
            return cleaned_text, confidence
            
        except Exception as e:
            print(f"OCR Error: {e}")
            return "", 0.0
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Enhance image for better OCR results"""
        # Convert to numpy array
        img_array = np.array(image)
        
        # Apply threshold to make text more clear
        threshold = 128
        img_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
        
        # Convert back to PIL Image
        return Image.fromarray(img_array)
    
    def _clean_math_text(self, text: str) -> str:
        """Clean and normalize extracted math text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', '', text)
        
        # Replace common OCR mistakes
        replacements = {
            'x': '*',
            '×': '*',
            '÷': '/',
            '−': '-',
            '–': '-',
            '=': '=',
            '(': '(',
            ')': ')',
            '[': '(',
            ']': ')',
            '{': '(',
            '}': ')',
            'sqrt': '√',
            'pi': 'π',
            'int': '∫',
            'sum': '∑',
            'partial': '∂',
            'delta': '∆',
            'nabla': '∇',
            'ln': 'log',
            'log10': 'log',
            'sin': 'sin',
            'cos': 'cos',
            'tan': 'tan',
            'arcsin': 'asin',
            'arccos': 'acos',
            'arctan': 'atan',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove any non-math characters
        text = re.sub(r'[^0-9+\-*/=()[]{}^√π∫∑∂∆∇abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.,]', '', text)
        
        return text.strip()
    
    def _calculate_confidence(self, original_text: str, cleaned_text: str) -> float:
        """Calculate confidence score for OCR result"""
        if not cleaned_text:
            return 0.0
        
        # Simple confidence based on length and character recognition
        length_ratio = len(cleaned_text) / max(len(original_text), 1)
        math_chars = len(re.findall(r'[0-9+\-*/=()[]{}^√π∫∑∂∆∇]', cleaned_text))
        math_ratio = math_chars / max(len(cleaned_text), 1)
        
        confidence = (length_ratio * 0.4 + math_ratio * 0.6) * 100
        return min(confidence, 100.0)

    # Keep the old interface for compatibility
    async def call_mathpix(self, image_base64: str) -> Tuple[str, float]:
        return await self.extract_math_from_image(image_base64)


# Singleton instance
ocr_service = OCRService()

