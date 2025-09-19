"""
File Handler for Drawing Analysis
Handles DXF text extraction and file operations.
"""
import os
from pathlib import Path
from typing import List

try:
    import ezdxf
    DXF_AVAILABLE = True
except ImportError:
    DXF_AVAILABLE = False


class DrawingFileHandler:
    """Handles file operations for drawing analysis."""
    
    def __init__(self):
        self.dxf_available = DXF_AVAILABLE
        if not DXF_AVAILABLE:
            print("[WARNING] ezdxf not available - DXF text extraction disabled")
    
    def get_file_summary(self, drawing_files: List) -> dict:
        """Get summary information about uploaded drawing files."""
        jpg_png_count = len([f for f in drawing_files 
                            if f.name.lower().endswith(('.jpg', '.jpeg', '.png'))])
        dxf_count = len([f for f in drawing_files 
                        if f.name.lower().endswith('.dxf')])
        
        return {
            'total_files': len(drawing_files),
            'image_files': jpg_png_count,
            'dxf_files': dxf_count,
            'file_names': [f.name for f in drawing_files]
        }
    
    def save_uploaded_files(self, drawing_files: List, upload_dir: str = "uploads") -> List[str]:
        """Save uploaded files to local directory and return file paths."""
        os.makedirs(upload_dir, exist_ok=True)
        file_paths = []
        
        for file in drawing_files:
            file_path = os.path.join(upload_dir, file.name)
            with open(file_path, "wb") as file_handle:
                file_handle.write(file.getvalue())
            file_paths.append(file_path)
        
        return file_paths
    
    def extract_dxf_text(self, dxf_file_path: str) -> str:
        """Extract text content from DXF files using ezdxf."""
        if not self.dxf_available:
            return "DXF text extraction not available (ezdxf not installed)"
        
        try:
            doc = ezdxf.readfile(dxf_file_path)
            extracted_text = []
            
            for layout in doc.layouts:
                layout_name = layout.name
                extracted_text.append(f"=== LAYOUT: {layout_name} ===")
                
                # Extract different types of text entities
                self._extract_text_entities(layout, extracted_text)
                self._extract_mtext_entities(layout, extracted_text)
                self._extract_dimension_entities(layout, extracted_text)
                self._extract_attribute_entities(layout, extracted_text)
                self._extract_block_entities(layout, extracted_text)
                
                extracted_text.append("")  # Blank line between layouts
            
            result = "\n".join(extracted_text)
            
            if result.strip():
                print(f"[DEBUG] Extracted {len(extracted_text)} text elements from "
                      f"{os.path.basename(dxf_file_path)}")
                return result
            else:
                return f"No text content found in DXF file: {os.path.basename(dxf_file_path)}"
                
        except Exception as exception:
            error_msg = (f"Error extracting text from DXF {os.path.basename(dxf_file_path)}: "
                        f"{str(exception)}")
            print(f"[ERROR] {error_msg}")
            return error_msg
    
    def _extract_text_entities(self, layout, extracted_text: List[str]):
        """Extract TEXT entities from layout."""
        for entity in layout.query('TEXT'):
            if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'text'):
                text_content = entity.dxf.text.strip()
                if text_content:
                    layer = getattr(entity.dxf, 'layer', 'UNKNOWN')
                    height = getattr(entity.dxf, 'height', 0)
                    extracted_text.append(f"TEXT[{layer}|H:{height:.1f}]: {text_content}")
    
    def _extract_mtext_entities(self, layout, extracted_text: List[str]):
        """Extract MTEXT entities from layout."""
        import re
        for entity in layout.query('MTEXT'):
            if hasattr(entity, 'text'):
                text_content = entity.text.strip()
                if text_content:
                    # Clean up MTEXT formatting codes
                    cleaned_text = re.sub(r'\\[A-Za-z][0-9]*;?', '', text_content)
                    cleaned_text = re.sub(r'\{[^}]*\}', '', cleaned_text)
                    if cleaned_text.strip():
                        layer = getattr(entity.dxf, 'layer', 'UNKNOWN')
                        extracted_text.append(f"MTEXT[{layer}]: {cleaned_text.strip()}")
    
    def _extract_dimension_entities(self, layout, extracted_text: List[str]):
        """Extract DIMENSION entities from layout."""
        for entity in layout.query('DIMENSION'):
            if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'text'):
                text_content = entity.dxf.text.strip()
                if text_content:
                    layer = getattr(entity.dxf, 'layer', 'UNKNOWN')
                    extracted_text.append(f"DIM[{layer}]: {text_content}")
    
    def _extract_attribute_entities(self, layout, extracted_text: List[str]):
        """Extract ATTRIB entities from layout."""
        for entity in layout.query('ATTRIB'):
            if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'text'):
                text_content = entity.dxf.text.strip()
                if text_content:
                    tag = getattr(entity.dxf, 'tag', 'UNKNOWN')
                    layer = getattr(entity.dxf, 'layer', 'UNKNOWN')
                    extracted_text.append(f"ATTRIB[{tag}|{layer}]: {text_content}")
    
    def _extract_block_entities(self, layout, extracted_text: List[str]):
        """Extract INSERT entities with attributes from layout."""
        for entity in layout.query('INSERT'):
            if entity.has_attrib:
                block_name = entity.dxf.name
                layer = getattr(entity.dxf, 'layer', 'UNKNOWN')
                extracted_text.append(f"BLOCK[{layer}]: {block_name}")
                for attrib in entity.attribs:
                    if hasattr(attrib, 'dxf') and hasattr(attrib.dxf, 'text'):
                        text_content = attrib.dxf.text.strip()
                        tag = getattr(attrib.dxf, 'tag', 'UNKNOWN')
                        if text_content:
                            extracted_text.append(f"  {tag}: {text_content}")