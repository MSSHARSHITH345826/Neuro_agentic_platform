"""
Graph adapter for integrating existing graph structures with NeuroStack.

This adapter wraps the existing HealthcareGraph from the ontology folder
and makes it compatible with NeuroStack's ontology layer.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)

# Add the ontology folder to the path to import the graph
# Calculate path: neurostack/core/ontology/graph_adapter.py -> project_root/ontology 1/ontology
ontology_folder = Path(__file__).parent.parent.parent.parent / "ontology 1" / "ontology"
ontology_parent = ontology_folder.parent  # "ontology 1"

# Add parent directory to path so we can import from "ontology" module
if str(ontology_parent) not in sys.path:
    sys.path.insert(0, str(ontology_parent))

# Try importing - the folder name has a space, so we need to handle it carefully
try:
    # Import directly from the graph module file
    import importlib.util
    graph_file_path = ontology_folder / "graph.py"
    if graph_file_path.exists():
        spec = importlib.util.spec_from_file_location("ontology_graph", graph_file_path)
        ontology_graph = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ontology_graph)
        
        # Extract classes from the module
        HealthcareGraph = getattr(ontology_graph, "HealthcareGraph", None)
        MedicalEntity = getattr(ontology_graph, "MedicalEntity", None)
        Patient = getattr(ontology_graph, "Patient", None)
        Disease = getattr(ontology_graph, "Disease", None)
        Treatment = getattr(ontology_graph, "Treatment", None)
        EntityType = getattr(ontology_graph, "EntityType", None)
        RelationshipType = getattr(ontology_graph, "RelationshipType", None)
        Relationship = getattr(ontology_graph, "Relationship", None)
        
        if HealthcareGraph is None:
            raise ImportError("HealthcareGraph class not found in graph.py")
    else:
        raise ImportError(f"Graph file not found at {graph_file_path}")
except Exception as e:
    # Fallback if import fails
    logger.warning(f"Could not import HealthcareGraph: {e}")
    HealthcareGraph = None
    MedicalEntity = None
    Patient = None
    Disease = None
    Treatment = None
    EntityType = None
    RelationshipType = None
    Relationship = None


class NeuroStackGraphAdapter:
    """
    Adapter that wraps the HealthcareGraph to work with NeuroStack.
    
    This class provides a unified interface for ontology operations
    that agents can use.
    """
    
    def __init__(self, graph: Optional[HealthcareGraph] = None):
        """
        Initialize the adapter.
        
        Args:
            graph: Optional existing HealthcareGraph instance
        """
        if HealthcareGraph is None:
            raise ImportError("Could not import HealthcareGraph from ontology.graph")
        
        self.graph = graph or HealthcareGraph()
        self.logger = logger.bind(component="GraphAdapter")
    
    def add_entity(self, entity_type: str, name: str, **properties) -> UUID:
        """
        Add an entity to the graph.
        
        Args:
            entity_type: Type of entity (Patient, Disease, Treatment)
            name: Name of the entity
            **properties: Additional properties
            
        Returns:
            The UUID of the created entity
        """
        if entity_type == "Patient":
            entity = Patient(name=name, properties=properties)
        elif entity_type == "Disease":
            entity = Disease(name=name, properties=properties)
        elif entity_type == "Treatment":
            entity = Treatment(name=name, properties=properties)
        else:
            # Generic entity
            entity = MedicalEntity(
                entity_type=EntityType(entity_type),
                name=name,
                properties=properties
            )
        
        return self.graph.add_entity(entity)
    
    def get_entity(self, entity_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: The entity UUID
            
        Returns:
            Dictionary representation of the entity or None
        """
        entity = self.graph.get_entity(entity_id)
        if entity:
            return self._entity_to_dict(entity)
        return None
    
    def find_entities(self, entity_type: Optional[str] = None, **filters) -> List[Dict[str, Any]]:
        """
        Find entities by type and/or filters.
        
        Args:
            entity_type: Optional entity type filter
            **filters: Property filters
            
        Returns:
            List of entity dictionaries
        """
        entity_type_enum = None
        if entity_type:
            entity_type_enum = EntityType(entity_type)
        
        entities = self.graph.find_entities(entity_type_enum, **filters)
        return [self._entity_to_dict(e) for e in entities]
    
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
        rel_type = RelationshipType(relationship_type)
        return self.graph.add_relationship(source_id, target_id, rel_type, **properties)
    
    def get_relationships(self, entity_id: UUID, 
                         relationship_type: Optional[str] = None,
                         direction: str = "both") -> List[Dict[str, Any]]:
        """
        Get relationships for an entity.
        
        Args:
            entity_id: The entity UUID
            relationship_type: Optional relationship type filter
            direction: "incoming", "outgoing", or "both"
            
        Returns:
            List of relationship dictionaries
        """
        rel_type = None
        if relationship_type:
            rel_type = RelationshipType(relationship_type)
        
        relationships = self.graph.get_relationships(entity_id, rel_type, direction)
        return [self._relationship_to_dict(r) for r in relationships]
    
    def get_neighbors(self, entity_id: UUID,
                     relationship_type: Optional[str] = None,
                     direction: str = "both") -> List[Dict[str, Any]]:
        """
        Get neighboring entities.
        
        Args:
            entity_id: The entity UUID
            relationship_type: Optional relationship type filter
            direction: "incoming", "outgoing", or "both"
            
        Returns:
            List of neighboring entity dictionaries
        """
        rel_type = None
        if relationship_type:
            rel_type = RelationshipType(relationship_type)
        
        neighbors = self.graph.get_neighbors(entity_id, rel_type, direction)
        return [self._entity_to_dict(n) for n in neighbors]
    
    def query_patient_info(self, patient_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive information about a patient.
        
        Args:
            patient_id: The patient UUID
            
        Returns:
            Dictionary with patient information including diseases and treatments
        """
        info = self.graph.get_patient_medical_info(patient_id)
        return {
            "patient": self._entity_to_dict(info["patient"]),
            "diseases": [self._entity_to_dict(d) for d in info["diseases"]],
            "treatments": [self._entity_to_dict(t) for t in info["treatments"]],
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return self.graph.get_statistics()
    
    def check_integrity(self) -> Dict[str, Any]:
        """Check graph integrity."""
        return self.graph.check_integrity()
    
    def _entity_to_dict(self, entity: MedicalEntity) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return {
            "id": str(entity.id),
            "type": entity.entity_type.value,
            "name": entity.name,
            "properties": entity.properties,
            "created_at": entity.created_at.isoformat(),
            "updated_at": entity.updated_at.isoformat(),
        }
    
    def _relationship_to_dict(self, rel: Relationship) -> Dict[str, Any]:
        """Convert relationship to dictionary."""
        return {
            "id": str(rel.id),
            "source_id": str(rel.source_id),
            "target_id": str(rel.target_id),
            "type": rel.relationship_type.value,
            "properties": rel.properties,
            "created_at": rel.created_at.isoformat(),
        }
    
    def export_graph(self) -> Dict[str, Any]:
        """Export the entire graph."""
        return self.graph.export_graph()

