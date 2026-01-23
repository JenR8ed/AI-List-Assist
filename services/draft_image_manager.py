import os
import shutil
from pathlib import Path
from typing import List

class DraftImageManager:
    def __init__(self, drafts_folder: str = "drafts"):
        self.drafts_folder = Path(drafts_folder)
        self.drafts_folder.mkdir(exist_ok=True)
    
    def save_draft_images(self, listing_id: str, source_images: List[str]) -> List[str]:
        draft_dir = self.drafts_folder / listing_id
        draft_dir.mkdir(exist_ok=True)
        
        draft_paths = []
        for i, source_path in enumerate(source_images):
            if os.path.exists(source_path):
                ext = Path(source_path).suffix
                draft_path = draft_dir / f"image_{i}{ext}"
                shutil.copy2(source_path, draft_path)
                draft_paths.append(str(draft_path))
        
        return draft_paths
    
    def cleanup_draft_images(self, listing_id: str) -> bool:
        draft_dir = self.drafts_folder / listing_id
        if draft_dir.exists():
            shutil.rmtree(draft_dir)
            return True
        return False