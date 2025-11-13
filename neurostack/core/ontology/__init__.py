"""
Ontology layer for NeuroStack.

This module provides ontology management capabilities, allowing agents
to work with structured knowledge graphs and semantic data.
"""

from .manager import OntologyManager
from .loader import OWLLoader
from .excel_loader import ExcelLoader
from .graph_adapter import NeuroStackGraphAdapter

__all__ = [
    "OntologyManager",
    "OWLLoader",
    "ExcelLoader",
    "NeuroStackGraphAdapter",
]

