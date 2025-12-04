"""
JSON Exporter
"""
import json
from typing import Union, List
from models.schemas import Movie, TVShow
from .base import BaseExporter


class JSONExporter(BaseExporter):
    """Export data to JSON format"""
    
    def export(self, data: Union[Movie, TVShow, List[Union[Movie, TVShow]]]) -> str:
        if isinstance(data, list):
            export_data = [self.prepare_data(item) for item in data]
        else:
            export_data = self.prepare_data(data)
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def get_file_extension(self) -> str:
        return "json"
    
    def get_content_type(self) -> str:
        return "application/json"
