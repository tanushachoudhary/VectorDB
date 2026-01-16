from typing import Optional, List
import io
from pathlib import Path
from PIL import Image
import pytesseract
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing uploaded documents and extracting text."""
    
    def __init__(self):
        """Initialize document processor."""
        # Set tesseract path if needed (Windows)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    def extract_text_from_pdf(self, file_content: bytes) -> dict:
        """
        Extract text from PDF file.
        
        Args:
            file_content: PDF file content as bytes
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PdfReader(pdf_file)
            
            pages = []
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                text = page.extract_text()
                if text.strip():
                    pages.append({
                        "page_number": page_num,
                        "text": text,
                        "char_count": len(text)
                    })
            
            total_text = "\n\n".join(p["text"] for p in pages)
            
            logger.info(f"Extracted text from {len(pages)} PDF pages")
            
            return {
                "text": total_text,
                "pages": pages,
                "total_pages": len(pdf_reader.pages),
                "extracted_pages": len(pages),
                "source": "pdf"
            }
        
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_text_from_image(self, file_content: bytes) -> dict:
        """
        Extract text from image using OCR.
        
        Args:
            file_content: Image file content as bytes
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            image = Image.open(io.BytesIO(file_content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR
            text = pytesseract.image_to_string(image)
            
            if not text.strip():
                raise ValueError("No text detected in image")
            
            logger.info(f"Extracted {len(text)} characters from image via OCR")
            
            return {
                "text": text,
                "pages": [{
                    "page_number": 1,
                    "text": text,
                    "char_count": len(text)
                }],
                "total_pages": 1,
                "extracted_pages": 1,
                "source": "ocr",
                "image_size": image.size
            }
        
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            raise ValueError(f"Failed to extract text from image: {str(e)}")
    
    def extract_text_from_file(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: str
    ) -> dict:
        """
        Extract text from uploaded file based on content type.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            content_type: MIME content type
            
        Returns:
            Dictionary with extracted text and metadata
        """
        file_ext = Path(filename).suffix.lower()
        
        # Determine source type
        if content_type == "application/pdf" or file_ext == ".pdf":
            return self.extract_text_from_pdf(file_content)
        
        elif content_type.startswith("image/") or file_ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"]:
            return self.extract_text_from_image(file_content)
        
        elif content_type == "text/plain" or file_ext == ".txt":
            text = file_content.decode('utf-8', errors='ignore')
            return {
                "text": text,
                "pages": [{
                    "page_number": 1,
                    "text": text,
                    "char_count": len(text)
                }],
                "total_pages": 1,
                "extracted_pages": 1,
                "source": "text"
            }
        
        else:
            raise ValueError(
                f"Unsupported file type: {content_type}. "
                f"Supported types: PDF, images (JPG, PNG, etc.), and text files."
            )
    
    def validate_file(
        self, 
        file_content: bytes, 
        max_size_mb: int = 10
    ) -> bool:
        """
        Validate uploaded file.
        
        Args:
            file_content: File content as bytes
            max_size_mb: Maximum file size in MB
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        file_size_mb = len(file_content) / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            raise ValueError(
                f"File too large: {file_size_mb:.2f}MB. "
                f"Maximum allowed: {max_size_mb}MB"
            )
        
        if len(file_content) == 0:
            raise ValueError("File is empty")
        
        return True
