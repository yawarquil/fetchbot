"""
XML Exporter
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Union, List
from models.schemas import Movie, TVShow
from .base import BaseExporter


class XMLExporter(BaseExporter):
    """Export data to XML format"""
    
    def _dict_to_xml(self, parent: ET.Element, data: dict):
        """Convert dictionary to XML elements"""
        for key, value in data.items():
            if value is None:
                continue
            
            if isinstance(value, list):
                list_elem = ET.SubElement(parent, key)
                item_tag = key[:-1] if key.endswith('s') else 'item'
                for item in value:
                    if isinstance(item, dict):
                        item_elem = ET.SubElement(list_elem, item_tag)
                        self._dict_to_xml(item_elem, item)
                    else:
                        item_elem = ET.SubElement(list_elem, item_tag)
                        item_elem.text = str(item)
            elif isinstance(value, dict):
                child = ET.SubElement(parent, key)
                self._dict_to_xml(child, value)
            else:
                child = ET.SubElement(parent, key)
                child.text = str(value)
    
    def _prettify(self, elem: ET.Element) -> str:
        """Return a pretty-printed XML string"""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def export(self, data: Union[Movie, TVShow, List[Union[Movie, TVShow]]]) -> str:
        root = ET.Element("data")
        root.set("generator", "MovieFetchBot")
        
        if isinstance(data, list):
            for item in data:
                prepared = self.prepare_data(item)
                is_movie = 'title' in prepared
                item_elem = ET.SubElement(root, "movie" if is_movie else "tv_show")
                self._dict_to_xml(item_elem, prepared)
        else:
            prepared = self.prepare_data(data)
            is_movie = hasattr(data, 'title')
            item_elem = ET.SubElement(root, "movie" if is_movie else "tv_show")
            self._dict_to_xml(item_elem, prepared)
        
        return self._prettify(root)
    
    def get_file_extension(self) -> str:
        return "xml"
    
    def get_content_type(self) -> str:
        return "application/xml"
