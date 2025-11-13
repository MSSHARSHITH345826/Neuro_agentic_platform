"""
OWL file loader for parsing ontology files.

This module provides functionality to load and parse OWL ontology files
and convert them into graph structures that NeuroStack can use.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger(__name__)


class OWLLoader:
    """
    Loader for OWL ontology files.
    
    This class can parse OWL files and extract entities and relationships
    for use in NeuroStack's ontology layer.
    """
    
    def __init__(self):
        self.logger = logger.bind(component="OWLLoader")
    
    def load_owl_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load an OWL file and extract entities and relationships.
        
        Args:
            file_path: Path to the OWL file
            
        Returns:
            Dictionary with 'entities' and 'relationships' keys
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"OWL file not found: {file_path}")
        
        self.logger.info("Loading OWL file", file_path=str(file_path))
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract namespace
            namespaces = self._extract_namespaces(root)
            
            # Extract classes (entities)
            entities = self._extract_classes(root, namespaces)
            
            # Extract object properties (relationships)
            relationships = self._extract_object_properties(root, namespaces)
            
            # Extract individuals (instances)
            individuals = self._extract_individuals(root, namespaces)
            
            result = {
                "entities": entities,
                "relationships": relationships,
                "individuals": individuals,
                "namespaces": namespaces,
            }
            
            self.logger.info("OWL file loaded", 
                           entities_count=len(entities),
                           relationships_count=len(relationships),
                           individuals_count=len(individuals))
            
            return result
            
        except Exception as e:
            self.logger.error("Failed to load OWL file", error=str(e))
            raise
    
    def _extract_namespaces(self, root: ET.Element) -> Dict[str, str]:
        """Extract namespaces from the root element."""
        namespaces = {}
        for prefix, uri in root.attrib.items():
            if prefix.startswith('{') and prefix.endswith('}'):
                # This is a namespace declaration
                ns_uri = prefix[1:-1]
                # Try to extract prefix from URI or use default
                if '#' in ns_uri:
                    prefix_name = ns_uri.split('#')[-1]
                else:
                    prefix_name = 'default'
                namespaces[prefix_name] = ns_uri
        return namespaces
    
    def _extract_classes(self, root: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Extract OWL classes as entities."""
        entities = {}
        
        # Find all Class elements
        for cls in root.findall('.//{http://www.w3.org/2002/07/owl#}Class'):
            about = cls.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
            if about:
                # Extract class name
                class_name = about.split('#')[-1] if '#' in about else about.split('/')[-1]
                
                # Try to determine entity type from name
                entity_type = self._infer_entity_type(class_name)
                
                entity_id = str(uuid4())
                entities[entity_id] = {
                    "id": entity_id,
                    "type": entity_type,
                    "name": class_name,
                    "properties": {
                        "owl_uri": about,
                        "is_class": True,
                    }
                }
        
        return entities
    
    def _extract_object_properties(self, root: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Extract OWL object properties as relationships."""
        relationships = {}
        
        # Find all ObjectProperty elements
        for prop in root.findall('.//{http://www.w3.org/2002/07/owl#}ObjectProperty'):
            about = prop.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
            if about:
                prop_name = about.split('#')[-1] if '#' in about else about.split('/')[-1]
                
                # Extract domain and range
                domain = None
                range_elem = None
                
                for domain_elem in prop.findall('.//{http://www.w3.org/2000/01/rdf-schema#}domain'):
                    resource = domain_elem.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                    if resource:
                        domain = resource.split('#')[-1] if '#' in resource else resource.split('/')[-1]
                
                for range_elem in prop.findall('.//{http://www.w3.org/2000/01/rdf-schema#}range'):
                    resource = range_elem.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                    if resource:
                        range_elem = resource.split('#')[-1] if '#' in resource else resource.split('/')[-1]
                
                rel_id = str(uuid4())
                relationships[rel_id] = {
                    "id": rel_id,
                    "type": prop_name,
                    "domain": domain,
                    "range": range_elem,
                    "properties": {
                        "owl_uri": about,
                    }
                }
        
        return relationships
    
    def _extract_individuals(self, root: ET.Element, namespaces: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract OWL individuals (instances) with their property assertions."""
        individuals = []
        
        # Find all NamedIndividual elements
        for individual in root.findall('.//{http://www.w3.org/2002/07/owl#}NamedIndividual'):
            about = individual.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
            if about:
                individual_name = about.split('#')[-1] if '#' in about else about.split('/')[-1]
                
                # Find type
                entity_type = None
                for type_elem in individual.findall('.//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}type'):
                    resource = type_elem.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                    if resource:
                        entity_type = resource.split('#')[-1] if '#' in resource else resource.split('/')[-1]
                
                # Extract property assertions (relationships)
                property_assertions = {}
                for child in individual:
                    # Check if this is a property assertion (not rdf:type)
                    if child.tag != '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}type':
                        # This is likely a property assertion
                        # Handle both namespaced and non-namespaced properties
                        prop_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                        # Remove namespace prefix if present
                        if prop_name.startswith('{'):
                            prop_name = prop_name.split('}')[-1]
                        
                        resource = child.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                        if not resource:
                            # Try without namespace
                            resource = child.get('resource')
                        
                        if resource:
                            target_name = resource.split('#')[-1] if '#' in resource else resource.split('/')[-1]
                            if prop_name not in property_assertions:
                                property_assertions[prop_name] = []
                            property_assertions[prop_name].append(target_name)
                
                individuals.append({
                    "name": individual_name,
                    "type": entity_type or "Entity",
                    "owl_uri": about,
                    "property_assertions": property_assertions,
                })
        
        return individuals
    
    def _infer_entity_type(self, class_name: str) -> str:
        """Infer entity type from class name."""
        class_name_lower = class_name.lower()
        
        if "patient" in class_name_lower:
            return "Patient"
        elif "disease" in class_name_lower or "diagnosis" in class_name_lower:
            return "Disease"
        elif "treatment" in class_name_lower or "therapy" in class_name_lower or "medication" in class_name_lower:
            return "Treatment"
        elif "doctor" in class_name_lower or "physician" in class_name_lower:
            return "Doctor"
        elif "facility" in class_name_lower or "hospital" in class_name_lower:
            return "Facility"
        else:
            return "Entity"
    
    def convert_to_graph_data(self, owl_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert OWL data to graph data format compatible with HealthcareGraph.
        
        This method converts OWL individuals to entities and property assertions to relationships.
        
        Args:
            owl_data: Dictionary from load_owl_file
            
        Returns:
            Dictionary in format expected by HealthcareGraph.from_owl_data
        """
        from uuid import uuid4
        
        graph_entities = {}
        graph_relationships = {}
        
        # Create a mapping from individual names to entity IDs
        individual_to_entity_id = {}
        
        # First, convert individuals to entities (these are the actual instances)
        individuals = owl_data.get("individuals", [])
        for individual in individuals:
            entity_id = str(uuid4())
            individual_name = individual["name"]
            individual_to_entity_id[individual_name] = entity_id
            
            # Infer entity type
            entity_type = self._infer_entity_type(individual.get("type", individual_name))
            
            graph_entities[entity_id] = {
                "type": entity_type,
                "name": individual_name,
                "properties": {
                    "owl_uri": individual.get("owl_uri", ""),
                    "source": "owl_individual",
                },
            }
        
        # Also add classes as entity type definitions (optional, for reference)
        for entity_id, entity_data in owl_data.get("entities", {}).items():
            # Only add if not already added as individual
            class_name = entity_data["name"]
            if class_name not in individual_to_entity_id:
                graph_entities[entity_id] = {
                    "type": entity_data["type"],
                    "name": entity_data["name"],
                    "properties": {
                        **entity_data.get("properties", {}),
                        "is_class": True,
                    },
                }
        
        # Now convert property assertions to relationships
        for individual in individuals:
            source_name = individual["name"]
            source_id = individual_to_entity_id.get(source_name)
            
            if not source_id:
                continue
            
            # Process property assertions
            property_assertions = individual.get("property_assertions", {})
            for prop_name, target_names in property_assertions.items():
                # Map property name to relationship type
                relationship_type = self._map_property_to_relationship_type(prop_name)
                
                for target_name in target_names:
                    target_id = individual_to_entity_id.get(target_name)
                    
                    if target_id:
                        # Create relationship
                        rel_id = str(uuid4())
                        graph_relationships[rel_id] = {
                            "source_id": source_id,
                            "target_id": target_id,
                            "type": relationship_type,
                            "properties": {
                                "owl_property": prop_name,
                                "source": "owl_assertion",
                            },
                        }
        
        return {
            "entities": graph_entities,
            "relationships": graph_relationships,
        }
    
    def _map_property_to_relationship_type(self, prop_name: str) -> str:
        """
        Map OWL property name to HealthcareGraph relationship type.
        
        Args:
            prop_name: OWL property name
            
        Returns:
            Relationship type string
        """
        prop_lower = prop_name.lower()
        
        # Map common property names to relationship types
        if "hasdisease" in prop_lower or "has_disease" in prop_lower:
            return "hasDisease"
        elif "receivestreatment" in prop_lower or "receives_treatment" in prop_lower:
            return "receivesTreatment"
        elif "treatsdisease" in prop_lower or "treats_disease" in prop_lower:
            return "treatsDisease"
        else:
            # Return as-is, might need to be added to RelationshipType enum
            return prop_name

