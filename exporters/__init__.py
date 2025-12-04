"""
Exporters package
"""
from .base import BaseExporter
from .json_exporter import JSONExporter
from .txt_exporter import TXTExporter
from .sql_exporter import SQLExporter
from .csv_exporter import CSVExporter
from .xml_exporter import XMLExporter
from models.schemas import ExportFormat, ExportConfig


def get_exporter(format: ExportFormat, config: ExportConfig = None) -> BaseExporter:
    """Factory function to get the appropriate exporter"""
    config = config or ExportConfig()
    
    exporters = {
        ExportFormat.JSON: JSONExporter,
        ExportFormat.TXT: TXTExporter,
        ExportFormat.SQL: SQLExporter,
        ExportFormat.CSV: CSVExporter,
        ExportFormat.XML: XMLExporter,
    }
    
    exporter_class = exporters.get(format, JSONExporter)
    return exporter_class(config)


__all__ = [
    "BaseExporter",
    "JSONExporter",
    "TXTExporter",
    "SQLExporter",
    "CSVExporter",
    "XMLExporter",
    "get_exporter",
]
