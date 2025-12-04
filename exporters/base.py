"""
Base exporter class
"""
from abc import ABC, abstractmethod
from typing import Union, List
from models.schemas import Movie, TVShow, ExportConfig


class BaseExporter(ABC):
    """Abstract base class for exporters"""
    
    def __init__(self, config: ExportConfig):
        self.config = config
    
    @abstractmethod
    def export(self, data: Union[Movie, TVShow, List[Union[Movie, TVShow]]]) -> str:
        """Export data to string format"""
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get file extension for this format"""
        pass
    
    @abstractmethod
    def get_content_type(self) -> str:
        """Get MIME content type"""
        pass
    
    def prepare_data(self, item: Union[Movie, TVShow]) -> dict:
        """Prepare data based on export config"""
        data = item.model_dump()
        
        if not self.config.include_cast:
            data.pop("cast", None)
        elif self.config.max_cast:
            data["cast"] = data.get("cast", [])[:self.config.max_cast]
        
        if not self.config.include_episodes:
            data.pop("episodes", None)
        
        if not self.config.include_images:
            data.pop("poster_path", None)
            data.pop("backdrop_path", None)
            data.pop("still_path", None)
            for ep in data.get("episodes", []):
                ep.pop("still_path", None)
        
        return data
