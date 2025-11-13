"""
Ontology manager for NeuroStack.

This module provides the main interface for managing ontologies in NeuroStack,
integrating with agents, memory, and tools.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from .graph_adapter import NeuroStackGraphAdapter
from .loader import OWLLoader
from .excel_loader import ExcelLoader

logger = structlog.get_logger(__name__)


class OntologyManager:
    """
    Manager for ontology operations in NeuroStack.
    
    This class provides a unified interface for agents to work with ontologies,
    including loading OWL files, querying entities, and managing relationships.
    """
    
    def __init__(self, tenant_id: Optional[str] = None):
        """
        Initialize the ontology manager.
        
        Args:
            tenant_id: Optional tenant ID for multi-tenancy
        """
        self.tenant_id = tenant_id
        self.logger = logger.bind(tenant_id=tenant_id)
        
        # Initialize components
        self._graph_adapter = None
        self._owl_loader = OWLLoader()
        self._excel_loader = ExcelLoader()
        self._loaded_ontologies: Dict[str, Dict[str, Any]] = {}
        self._loaded_excel_files: Dict[str, Dict[str, Any]] = {}
    
    @property
    def graph(self) -> NeuroStackGraphAdapter:
        """Get the graph adapter instance."""
        if self._graph_adapter is None:
            self._graph_adapter = NeuroStackGraphAdapter()
        return self._graph_adapter
    
    def load_excel_annotations(self, file_path: str, excel_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Load an Excel file with ontology annotations.
        
        Args:
            file_path: Path to the Excel file
            excel_name: Optional name for the Excel file
            
        Returns:
            Dictionary with loaded annotations information
        """
        file_path = Path(file_path)
        excel_name = excel_name or file_path.stem
        
        self.logger.info("Loading Excel file", file_path=str(file_path), name=excel_name)
        
        # Load Excel file
        excel_data = self._excel_loader.load_excel_file(str(file_path))
        
        # Store loaded Excel file
        self._loaded_excel_files[excel_name] = {
            "file_path": str(file_path),
            "excel_data": excel_data,
        }
        
        annotations_count = len(excel_data.get("annotations", {}))
        self.logger.info("Excel file loaded", name=excel_name, annotations_count=annotations_count)
        
        return {
            "name": excel_name,
            "annotations_count": annotations_count,
            "sheets": excel_data.get("sheets", []),
        }
    
    def apply_excel_annotations(self, ontology_name: str, excel_name: str) -> None:
        """
        Apply Excel annotations to a loaded ontology.
        
        Args:
            ontology_name: Name of the loaded ontology
            excel_name: Name of the loaded Excel file
        """
        if ontology_name not in self._loaded_ontologies:
            raise ValueError(f"Ontology '{ontology_name}' not loaded")
        if excel_name not in self._loaded_excel_files:
            raise ValueError(f"Excel file '{excel_name}' not loaded")
        
        ontology_data = self._loaded_ontologies[ontology_name]
        excel_data = self._loaded_excel_files[excel_name]
        
        # Apply annotations to graph data
        graph_data = ontology_data["graph_data"]
        annotations = excel_data["excel_data"].get("annotations", {})
        
        updated_entities = self._excel_loader.apply_annotations_to_entities(
            annotations, graph_data.get("entities", {})
        )
        
        graph_data["entities"] = updated_entities
        
        # Re-initialize graph with updated data
        self.initialize_graph_from_ontology(ontology_name)
        
        self.logger.info("Excel annotations applied", 
                        ontology_name=ontology_name,
                        excel_name=excel_name)
    
    def load_ontology(self, file_path: str, ontology_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Load an OWL ontology file.
        
        Args:
            file_path: Path to the OWL file
            ontology_name: Optional name for the ontology
            
        Returns:
            Dictionary with loaded ontology information
        """
        file_path = Path(file_path)
        ontology_name = ontology_name or file_path.stem
        
        self.logger.info("Loading ontology", file_path=str(file_path), name=ontology_name)
        
        # Load OWL file
        owl_data = self._owl_loader.load_owl_file(str(file_path))
        
        # Convert to graph data format
        graph_data = self._owl_loader.convert_to_graph_data(owl_data)
        
        # Store loaded ontology
        self._loaded_ontologies[ontology_name] = {
            "file_path": str(file_path),
            "owl_data": owl_data,
            "graph_data": graph_data,
        }
        
        self.logger.info("Ontology loaded", name=ontology_name, 
                        entities=len(graph_data.get("entities", {})),
                        relationships=len(graph_data.get("relationships", {})))
        
        # Merge with existing graph if it exists, otherwise initialize new one
        if self._graph_adapter is None or len(self._graph_adapter.graph.entities) == 0:
            # First ontology or empty graph - initialize fresh
            self.initialize_graph_from_ontology(ontology_name)
        else:
            # Merge with existing graph
            self._merge_ontology_into_graph(graph_data)
        
        return {
            "name": ontology_name,
            "entities_count": len(graph_data.get("entities", {})),
            "relationships_count": len(graph_data.get("relationships", {})),
        }
    
    def _merge_ontology_into_graph(self, graph_data: Dict[str, Any]) -> None:
        """
        Merge ontology data into existing graph.
        
        Args:
            graph_data: Graph data to merge
        """
        from uuid import UUID
        
        # Add entities
        for entity_id_str, entity_data in graph_data.get("entities", {}).items():
            try:
                entity_id = UUID(entity_id_str)
                # Check if entity already exists
                existing = self.graph.get_entity(entity_id)
                if not existing:
                    # Add new entity
                    self.graph.add_entity(
                        entity_data["type"],
                        entity_data["name"],
                        **entity_data.get("properties", {})
                    )
            except (ValueError, TypeError):
                # Invalid UUID, create new entity
                self.graph.add_entity(
                    entity_data["type"],
                    entity_data["name"],
                    **entity_data.get("properties", {})
                )
        
        # Add relationships
        for rel_id_str, rel_data in graph_data.get("relationships", {}).items():
            try:
                source_id = UUID(rel_data["source_id"])
                target_id = UUID(rel_data["target_id"])
                
                # Check if both entities exist
                source_entity = self.graph.get_entity(source_id)
                target_entity = self.graph.get_entity(target_id)
                
                if source_entity and target_entity:
                    # Try to add relationship
                    try:
                        self.graph.add_relationship(
                            source_id,
                            target_id,
                            rel_data["type"],
                            **rel_data.get("properties", {})
                        )
                    except ValueError:
                        # Relationship might already exist or be invalid, skip
                        pass
            except (ValueError, TypeError, KeyError):
                # Invalid relationship data, skip
                pass
    
    def initialize_graph_from_ontology(self, ontology_name: str) -> None:
        """
        Initialize the graph from a loaded ontology.
        
        Args:
            ontology_name: Name of the loaded ontology
        """
        if ontology_name not in self._loaded_ontologies:
            raise ValueError(f"Ontology '{ontology_name}' not loaded")
        
        graph_data = self._loaded_ontologies[ontology_name]["graph_data"]
        
        # Create new graph adapter with the data
        # HealthcareGraph is imported in graph_adapter, so we need to use it from there
        from .graph_adapter import HealthcareGraph
        if HealthcareGraph:
            graph = HealthcareGraph.from_owl_data(graph_data)
            self._graph_adapter = NeuroStackGraphAdapter(graph)
        else:
            # If HealthcareGraph is not available, create empty graph
            self._graph_adapter = NeuroStackGraphAdapter()
        
        self.logger.info("Graph initialized from ontology", ontology_name=ontology_name)
    
    def add_entity(self, entity_type: str, name: str, **properties) -> UUID:
        """
        Add an entity to the ontology graph.
        
        Args:
            entity_type: Type of entity (Patient, Disease, Treatment)
            name: Name of the entity
            **properties: Additional properties
            
        Returns:
            The UUID of the created entity
        """
        entity_id = self.graph.add_entity(entity_type, name, **properties)
        self.logger.info("Entity added", entity_id=str(entity_id), entity_type=entity_type, name=name)
        return entity_id
    
    def get_entity(self, entity_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: The entity UUID
            
        Returns:
            Dictionary representation of the entity or None
        """
        return self.graph.get_entity(entity_id)
    
    def find_entities(self, entity_type: Optional[str] = None, **filters) -> List[Dict[str, Any]]:
        """
        Find entities by type and/or filters.
        
        Args:
            entity_type: Optional entity type filter
            **filters: Property filters
            
        Returns:
            List of entity dictionaries
        """
        return self.graph.find_entities(entity_type, **filters)
    
    def add_relationship(self, source_id: UUID, target_id: UUID,
                        relationship_type: str, **properties) -> UUID:
        """
        Add a relationship between entities.
        
        Args:
            source_id: Source entity UUID
            target_id: Target entity UUID
            relationship_type: Type of relationship
            **properties: Additional relationship properties
            
        Returns:
            The UUID of the created relationship
        """
        rel_id = self.graph.add_relationship(source_id, target_id, relationship_type, **properties)
        self.logger.info("Relationship added", relationship_id=str(rel_id), 
                        relationship_type=relationship_type)
        return rel_id
    
    def query_patient_info(self, patient_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive information about a patient.
        
        Args:
            patient_id: The patient UUID
            
        Returns:
            Dictionary with patient information including diseases and treatments
        """
        return self.graph.query_patient_info(patient_id)
    
    def search_entities(self, query: str, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for entities by name or properties.
        
        Args:
            query: Search query string
            entity_type: Optional entity type filter
            
        Returns:
            List of matching entities
        """
        entities = self.find_entities(entity_type)
        
        # Simple text search
        query_lower = query.lower()
        matches = []
        
        for entity in entities:
            if query_lower in entity["name"].lower():
                matches.append(entity)
            elif any(query_lower in str(v).lower() for v in entity.get("properties", {}).values()):
                matches.append(entity)
        
        return matches
    
    def get_entity_relationships(self, entity_id: UUID,
                                 relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all relationships for an entity.
        
        Args:
            entity_id: The entity UUID
            relationship_type: Optional relationship type filter
            
        Returns:
            List of relationship dictionaries
        """
        return self.graph.get_relationships(entity_id, relationship_type)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get ontology statistics.
        
        Returns:
            Dictionary with statistics about the ontology
        """
        graph_stats = self.graph.get_statistics()
        return {
            **graph_stats,
            "loaded_ontologies": list(self._loaded_ontologies.keys()),
            "tenant_id": self.tenant_id,
        }
    
    def check_integrity(self) -> Dict[str, Any]:
        """
        Check ontology graph integrity.
        
        Returns:
            Dictionary with integrity check results
        """
        return self.graph.check_integrity()
    
    def export_ontology(self) -> Dict[str, Any]:
        """
        Export the current ontology state.
        
        Returns:
            Dictionary representation of the ontology
        """
        return self.graph.export_graph()

