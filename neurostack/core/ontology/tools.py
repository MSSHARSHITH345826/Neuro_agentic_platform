"""
Ontology tools for NeuroStack agents.

This module provides tools that agents can use to interact with the ontology layer.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from ..tools.base import SimpleTool, ToolResult

logger = structlog.get_logger(__name__)


class OntologyQueryTool(SimpleTool):
    """Tool for querying ontology entities."""
    
    def __init__(self, ontology_manager):
        """
        Initialize the ontology query tool.
        
        Args:
            ontology_manager: OntologyManager instance
        """
        self.ontology_manager = ontology_manager
        super().__init__(
            name="ontology_query",
            description="Query entities in the ontology by type, name, or properties",
            execute_func=self._query,
            arguments_schema={
                "entity_type": {
                    "type": "string",
                    "description": "Type of entity to find (Patient, Disease, Treatment, or None for all)",
                    "required": False
                },
                "name": {
                    "type": "string",
                    "description": "Name to search for",
                    "required": False
                },
                "filters": {
                    "type": "object",
                    "description": "Additional property filters",
                    "required": False
                }
            }
        )
    
    async def _query(self, arguments: Dict[str, Any]) -> str:
        """Execute ontology query."""
        entity_type = arguments.get("entity_type")
        name = arguments.get("name")
        filters = arguments.get("filters", {})
        
        if name:
            # Search by name
            results = self.ontology_manager.search_entities(name, entity_type)
        else:
            # Find by type and filters
            if name:
                filters["name"] = name
            results = self.ontology_manager.find_entities(entity_type, **filters)
        
        if not results:
            return f"No entities found matching the query."
        
        result_str = f"Found {len(results)} entities:\n"
        for entity in results[:10]:  # Limit to 10 results
            result_str += f"- {entity['type']}: {entity['name']} (ID: {entity['id']})\n"
        
        if len(results) > 10:
            result_str += f"... and {len(results) - 10} more\n"
        
        return result_str


class OntologyGetEntityTool(SimpleTool):
    """Tool for getting a specific entity by ID."""
    
    def __init__(self, ontology_manager):
        """
        Initialize the get entity tool.
        
        Args:
            ontology_manager: OntologyManager instance
        """
        self.ontology_manager = ontology_manager
        super().__init__(
            name="ontology_get_entity",
            description="Get detailed information about a specific entity by ID",
            execute_func=self._get_entity,
            arguments_schema={
                "entity_id": {
                    "type": "string",
                    "description": "UUID of the entity to retrieve",
                    "required": True
                }
            }
        )
    
    async def _get_entity(self, arguments: Dict[str, Any]) -> str:
        """Get entity by ID."""
        entity_id_str = arguments.get("entity_id")
        if not entity_id_str:
            return "Error: entity_id is required"
        
        try:
            entity_id = UUID(entity_id_str)
            entity = self.ontology_manager.get_entity(entity_id)
            
            if not entity:
                return f"Entity with ID {entity_id_str} not found."
            
            result = f"Entity: {entity['name']}\n"
            result += f"Type: {entity['type']}\n"
            result += f"ID: {entity['id']}\n"
            
            if entity.get("properties"):
                result += "Properties:\n"
                for key, value in entity["properties"].items():
                    result += f"  - {key}: {value}\n"
            
            return result
            
        except ValueError as e:
            return f"Error: Invalid entity ID format - {str(e)}"


class OntologyGetPatientInfoTool(SimpleTool):
    """Tool for getting comprehensive patient information."""
    
    def __init__(self, ontology_manager):
        """
        Initialize the get patient info tool.
        
        Args:
            ontology_manager: OntologyManager instance
        """
        self.ontology_manager = ontology_manager
        super().__init__(
            name="ontology_get_patient_info",
            description="Get comprehensive medical information for a patient including diseases and treatments",
            execute_func=self._get_patient_info,
            arguments_schema={
                "patient_id": {
                    "type": "string",
                    "description": "UUID of the patient",
                    "required": True
                }
            }
        )
    
    async def _get_patient_info(self, arguments: Dict[str, Any]) -> str:
        """Get patient information."""
        patient_id_str = arguments.get("patient_id")
        if not patient_id_str:
            return "Error: patient_id is required"
        
        try:
            patient_id = UUID(patient_id_str)
            info = self.ontology_manager.query_patient_info(patient_id)
            
            result = f"Patient: {info['patient']['name']}\n"
            result += f"ID: {info['patient']['id']}\n\n"
            
            if info.get("diseases"):
                result += "Diseases:\n"
                for disease in info["diseases"]:
                    result += f"  - {disease['name']} (ID: {disease['id']})\n"
            else:
                result += "Diseases: None\n"
            
            result += "\n"
            
            if info.get("treatments"):
                result += "Treatments:\n"
                for treatment in info["treatments"]:
                    result += f"  - {treatment['name']} (ID: {treatment['id']})\n"
            else:
                result += "Treatments: None\n"
            
            return result
            
        except ValueError as e:
            return f"Error: Invalid patient ID format - {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


class OntologyAddEntityTool(SimpleTool):
    """Tool for adding entities to the ontology."""
    
    def __init__(self, ontology_manager):
        """
        Initialize the add entity tool.
        
        Args:
            ontology_manager: OntologyManager instance
        """
        self.ontology_manager = ontology_manager
        super().__init__(
            name="ontology_add_entity",
            description="Add a new entity to the ontology",
            execute_func=self._add_entity,
            arguments_schema={
                "entity_type": {
                    "type": "string",
                    "description": "Type of entity (Patient, Disease, Treatment)",
                    "required": True
                },
                "name": {
                    "type": "string",
                    "description": "Name of the entity",
                    "required": True
                },
                "properties": {
                    "type": "object",
                    "description": "Additional properties for the entity",
                    "required": False
                }
            }
        )
    
    async def _add_entity(self, arguments: Dict[str, Any]) -> str:
        """Add entity to ontology."""
        entity_type = arguments.get("entity_type")
        name = arguments.get("name")
        properties = arguments.get("properties", {})
        
        if not entity_type or not name:
            return "Error: entity_type and name are required"
        
        try:
            entity_id = self.ontology_manager.add_entity(entity_type, name, **properties)
            return f"Entity added successfully. ID: {entity_id}"
        except Exception as e:
            return f"Error adding entity: {str(e)}"


class OntologyAddRelationshipTool(SimpleTool):
    """Tool for adding relationships between entities."""
    
    def __init__(self, ontology_manager):
        """
        Initialize the add relationship tool.
        
        Args:
            ontology_manager: OntologyManager instance
        """
        self.ontology_manager = ontology_manager
        super().__init__(
            name="ontology_add_relationship",
            description="Add a relationship between two entities",
            execute_func=self._add_relationship,
            arguments_schema={
                "source_id": {
                    "type": "string",
                    "description": "UUID of the source entity",
                    "required": True
                },
                "target_id": {
                    "type": "string",
                    "description": "UUID of the target entity",
                    "required": True
                },
                "relationship_type": {
                    "type": "string",
                    "description": "Type of relationship (hasDisease, receivesTreatment, treatsDisease)",
                    "required": True
                },
                "properties": {
                    "type": "object",
                    "description": "Additional properties for the relationship",
                    "required": False
                }
            }
        )
    
    async def _add_relationship(self, arguments: Dict[str, Any]) -> str:
        """Add relationship to ontology."""
        source_id_str = arguments.get("source_id")
        target_id_str = arguments.get("target_id")
        relationship_type = arguments.get("relationship_type")
        properties = arguments.get("properties", {})
        
        if not all([source_id_str, target_id_str, relationship_type]):
            return "Error: source_id, target_id, and relationship_type are required"
        
        try:
            source_id = UUID(source_id_str)
            target_id = UUID(target_id_str)
            
            rel_id = self.ontology_manager.add_relationship(
                source_id, target_id, relationship_type, **properties
            )
            return f"Relationship added successfully. ID: {rel_id}"
        except ValueError as e:
            return f"Error: Invalid UUID format - {str(e)}"
        except Exception as e:
            return f"Error adding relationship: {str(e)}"


class OntologyStatsTool(SimpleTool):
    """Tool for getting ontology statistics."""
    
    def __init__(self, ontology_manager):
        """
        Initialize the stats tool.
        
        Args:
            ontology_manager: OntologyManager instance
        """
        self.ontology_manager = ontology_manager
        super().__init__(
            name="ontology_stats",
            description="Get statistics about the ontology",
            execute_func=self._get_stats,
            arguments_schema={}
        )
    
    async def _get_stats(self, arguments: Dict[str, Any]) -> str:
        """Get ontology statistics."""
        stats = self.ontology_manager.get_statistics()
        
        result = "Ontology Statistics:\n"
        result += f"Total entities: {stats.get('total_entities', 0)}\n"
        result += f"Total relationships: {stats.get('total_relationships', 0)}\n"
        
        if stats.get("entities_by_type"):
            result += "\nEntities by type:\n"
            for entity_type, count in stats["entities_by_type"].items():
                result += f"  - {entity_type}: {count}\n"
        
        if stats.get("loaded_ontologies"):
            result += f"\nLoaded ontologies: {', '.join(stats['loaded_ontologies'])}\n"
        
        return result

