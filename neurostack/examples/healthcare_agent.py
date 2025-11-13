"""
Healthcare Agent Use Case

This example demonstrates how to use NeuroStack's ontology layer
with an agent to work with healthcare data.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

# Add neurostack to path - go up two levels from examples to get to project root
# File structure: project_root/neurostack/examples/healthcare_agent.py
script_file = Path(__file__).resolve()  # Get absolute path of this script
project_root = script_file.parent.parent.parent  # Go up 3 levels: examples -> neurostack -> project_root
project_root_str = str(project_root)

# Debug: Print paths (set NEUROSTACK_QUIET=1 to disable)
import os
if not os.environ.get('NEUROSTACK_QUIET'):
    print(f"[DEBUG] Script location: {script_file}")
    print(f"[DEBUG] Project root: {project_root_str}")
    print(f"[DEBUG] Neurostack dir exists: {(project_root / 'neurostack').exists()}")

# Add to path if not already there
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

# Verify the neurostack directory exists
neurostack_dir = project_root / "neurostack"
if not neurostack_dir.exists():
    raise ImportError(
        f"Cannot find neurostack directory. Expected at: {neurostack_dir}\n"
        f"Project root: {project_root_str}\n"
        f"Script location: {script_file}"
    )

# Now import
from neurostack.core.agents.base import Agent, AgentConfig, AgentContext, AgentState
from neurostack.core.ontology import OntologyManager
from neurostack.core.ontology.tools import (
    OntologyQueryTool,
    OntologyGetEntityTool,
    OntologyGetPatientInfoTool,
    OntologyAddEntityTool,
    OntologyAddRelationshipTool,
    OntologyStatsTool,
)


class HealthcareAgent(Agent):
    """
    Healthcare agent that uses the ontology layer to manage patient data.
    
    This agent can:
    - Query patient information
    - Add new patients, diseases, and treatments
    - Link patients to diseases and treatments
    - Provide medical recommendations based on ontology knowledge
    """
    
    def __init__(self, config: AgentConfig, ontology_manager: OntologyManager):
        """
        Initialize the healthcare agent.
        
        Args:
            config: Agent configuration
            ontology_manager: OntologyManager instance
        """
        super().__init__(config)
        self.ontology_manager = ontology_manager
        
        # Add ontology tools
        self.add_tool(OntologyQueryTool(ontology_manager))
        self.add_tool(OntologyGetEntityTool(ontology_manager))
        self.add_tool(OntologyGetPatientInfoTool(ontology_manager))
        self.add_tool(OntologyAddEntityTool(ontology_manager))
        self.add_tool(OntologyAddRelationshipTool(ontology_manager))
        self.add_tool(OntologyStatsTool(ontology_manager))
    
    async def execute(self, task: Any, context: Optional[AgentContext] = None) -> Any:
        """
        Execute a healthcare task.
        
        Args:
            task: The task to execute (can be a string or dict)
            context: Optional context
            
        Returns:
            The result of the task execution
        """
        self.state = AgentState.RUNNING
        self.context = context or AgentContext()
        
        try:
            self.logger.info("Executing healthcare task", task_type=type(task).__name__)
            
            # Parse task
            if isinstance(task, str):
                task_type = "query"
                task_data = {"query": task}
            elif isinstance(task, dict):
                task_type = task.get("type", "query")
                task_data = task
            else:
                task_type = "query"
                task_data = {"query": str(task)}
            
            # Execute based on task type
            if task_type == "query_patient":
                result = await self._query_patient(task_data)
            elif task_type == "add_patient":
                result = await self._add_patient(task_data)
            elif task_type == "add_disease":
                result = await self._add_disease(task_data)
            elif task_type == "add_treatment":
                result = await self._add_treatment(task_data)
            elif task_type == "link_patient_disease":
                result = await self._link_patient_disease(task_data)
            elif task_type == "link_patient_treatment":
                result = await self._link_patient_treatment(task_data)
            elif task_type == "get_recommendations":
                result = await self._get_recommendations(task_data)
            elif task_type == "stats":
                result = await self._get_stats()
            elif task_type == "query":
                result = await self._query_entities(task_data)
            else:
                # Use reasoning engine for general queries
                if self.reasoning:
                    result = await self.reasoning.process(task, self.context)
                else:
                    result = f"Task completed: {task}"
            
            # Store result in memory
            if self.memory:
                await self.memory.store_result(task, result)
            
            self.state = AgentState.COMPLETED
            return result
            
        except Exception as e:
            self.state = AgentState.ERROR
            self.logger.error("Task execution failed", error=str(e))
            raise
    
    async def _query_patient(self, task_data: dict) -> str:
        """Query patient information."""
        patient_id = task_data.get("patient_id")
        if patient_id:
            # Get specific patient
            tool = OntologyGetPatientInfoTool(self.ontology_manager)
            result = await tool.execute({"patient_id": patient_id})
            return result
        else:
            # Search for patients
            tool = OntologyQueryTool(self.ontology_manager)
            result = await tool.execute({"entity_type": "Patient"})
            return result
    
    async def _add_patient(self, task_data: dict) -> str:
        """Add a new patient."""
        name = task_data.get("name", "Unknown Patient")
        properties = task_data.get("properties", {})
        
        tool = OntologyAddEntityTool(self.ontology_manager)
        result = await tool.execute({
            "entity_type": "Patient",
            "name": name,
            "properties": properties
        })
        return result
    
    async def _add_disease(self, task_data: dict) -> str:
        """Add a new disease."""
        name = task_data.get("name", "Unknown Disease")
        properties = task_data.get("properties", {})
        
        tool = OntologyAddEntityTool(self.ontology_manager)
        result = await tool.execute({
            "entity_type": "Disease",
            "name": name,
            "properties": properties
        })
        return result
    
    async def _add_treatment(self, task_data: dict) -> str:
        """Add a new treatment."""
        name = task_data.get("name", "Unknown Treatment")
        properties = task_data.get("properties", {})
        
        tool = OntologyAddEntityTool(self.ontology_manager)
        result = await tool.execute({
            "entity_type": "Treatment",
            "name": name,
            "properties": properties
        })
        return result
    
    async def _link_patient_disease(self, task_data: dict) -> str:
        """Link a patient to a disease."""
        patient_id = task_data.get("patient_id")
        disease_id = task_data.get("disease_id")
        
        if not patient_id or not disease_id:
            return "Error: patient_id and disease_id are required"
        
        tool = OntologyAddRelationshipTool(self.ontology_manager)
        result = await tool.execute({
            "source_id": patient_id,
            "target_id": disease_id,
            "relationship_type": "hasDisease"
        })
        return result
    
    async def _link_patient_treatment(self, task_data: dict) -> str:
        """Link a patient to a treatment."""
        patient_id = task_data.get("patient_id")
        treatment_id = task_data.get("treatment_id")
        
        if not patient_id or not treatment_id:
            return "Error: patient_id and treatment_id are required"
        
        tool = OntologyAddRelationshipTool(self.ontology_manager)
        result = await tool.execute({
            "source_id": patient_id,
            "target_id": treatment_id,
            "relationship_type": "receivesTreatment"
        })
        return result
    
    async def _get_recommendations(self, task_data: dict) -> str:
        """Get treatment recommendations for a patient."""
        patient_id = task_data.get("patient_id")
        if not patient_id:
            return "Error: patient_id is required"
        
        # Get patient info
        info = self.ontology_manager.query_patient_info(UUID(patient_id))
        
        result = f"Recommendations for {info['patient']['name']}:\n\n"
        
        # Find treatments for patient's diseases
        for disease in info.get("diseases", []):
            disease_id = disease["id"]
            # Find treatments that treat this disease
            treatments = self.ontology_manager.find_entities("Treatment")
            
            result += f"For {disease['name']}:\n"
            if treatments:
                for treatment in treatments[:3]:  # Show top 3
                    result += f"  - Consider {treatment['name']}\n"
            else:
                result += "  - No specific treatments found in ontology\n"
            result += "\n"
        
        return result
    
    async def _query_entities(self, task_data: dict) -> str:
        """Query entities by type."""
        entity_type = task_data.get("entity_type")
        name = task_data.get("name")
        
        tool = OntologyQueryTool(self.ontology_manager)
        result = await tool.execute({
            "entity_type": entity_type,
            "name": name,
            "filters": task_data.get("filters", {})
        })
        return result
    
    async def _get_stats(self) -> str:
        """Get ontology statistics."""
        tool = OntologyStatsTool(self.ontology_manager)
        return await tool.execute({})


async def main():
    """Main demo function."""
    print("=" * 60)
    print("NeuroStack Healthcare Agent Demo")
    print("=" * 60)
    print()
    
    # Initialize ontology manager
    print("Initializing ontology manager...")
    ontology_manager = OntologyManager()
    
    # Try to load all OWL files if available
    ontology_path = Path(__file__).parent.parent.parent / "ontology 1" / "ontology"
    owl_files = list(ontology_path.glob("*.owl"))
    excel_files = list(ontology_path.glob("*.xlsx"))
    
    loaded_owl_count = 0
    if owl_files:
        print(f"Found {len(owl_files)} OWL file(s), loading all...")
        for owl_file in owl_files:
            try:
                load_result = ontology_manager.load_ontology(str(owl_file))
                loaded_owl_count += 1
                print(f"✓ Loaded: {owl_file.name}")
                print(f"  - Entities: {load_result['entities_count']}")
                print(f"  - Relationships: {load_result['relationships_count']}")
            except Exception as e:
                print(f"✗ Failed to load {owl_file.name}: {e}")
        
        if loaded_owl_count > 0:
            # Show some entities from loaded OWL files
            print("\nQuerying entities from loaded OWL files...")
            diseases = ontology_manager.find_entities("Disease")
            treatments = ontology_manager.find_entities("Treatment")
            patients = ontology_manager.find_entities("Patient")
            
            if diseases:
                print(f"\nFound {len(diseases)} diseases:")
                for disease in diseases[:5]:  # Show first 5
                    print(f"  - {disease['name']}")
            
            if treatments:
                print(f"\nFound {len(treatments)} treatments:")
                for treatment in treatments[:5]:  # Show first 5
                    print(f"  - {treatment['name']}")
            
            if patients:
                print(f"\nFound {len(patients)} patients:")
                for patient in patients[:3]:  # Show first 3
                    print(f"  - {patient['name']}")
    else:
        print("No OWL files found, starting with empty ontology...")
    
    # Try to load Excel file if available
    if excel_files:
        print(f"\nFound {len(excel_files)} Excel file(s), loading...")
        for excel_file in excel_files:
            try:
                excel_result = ontology_manager.load_excel_annotations(str(excel_file))
                print(f"✓ Loaded Excel: {excel_file.name}")
                print(f"  - Annotations: {excel_result['annotations_count']}")
                print(f"  - Sheets: {', '.join(excel_result.get('sheets', []))}")
                
                # Try to apply annotations to loaded ontologies
                if loaded_owl_count > 0:
                    for owl_file in owl_files[:1]:  # Apply to first ontology
                        try:
                            ontology_manager.apply_excel_annotations(owl_file.stem, excel_file.stem)
                            print(f"  - Applied annotations to {owl_file.stem}")
                        except Exception as e:
                            print(f"  - Could not apply annotations: {e}")
            except Exception as e:
                print(f"✗ Failed to load {excel_file.name}: {e}")
    
    print()
    
    # Create healthcare agent
    print("Creating healthcare agent...")
    agent_config = AgentConfig(
        name="HealthcareAgent",
        description="Agent for managing healthcare data using ontology",
        memory_enabled=True,
        reasoning_enabled=True
    )
    
    agent = HealthcareAgent(agent_config, ontology_manager)
    await agent.start()
    print("Agent created and started!")
    print()
    
    # Create context
    context = AgentContext(user_id="demo_user", tenant_id="demo_tenant")
    
    # Demo: Query existing OWL data first
    print("=" * 60)
    print("Demo: Querying OWL File Data")
    print("=" * 60)
    print()
    
    print("Querying all diseases from OWL file...")
    all_diseases = await agent.execute({
        "type": "query",
        "entity_type": "Disease"
    }, context)
    print(all_diseases)
    print()
    
    print("Querying all treatments from OWL file...")
    all_treatments = await agent.execute({
        "type": "query",
        "entity_type": "Treatment"
    }, context)
    print(all_treatments)
    print()
    
    # Demo: Add some sample data
    print("=" * 60)
    print("Demo: Adding Additional Sample Healthcare Data")
    print("=" * 60)
    print()
    
    # Add a patient
    print("1. Adding a patient...")
    patient_result = await agent.execute({
        "type": "add_patient",
        "name": "John Doe",
        "properties": {"age": 45, "gender": "Male"}
    }, context)
    print(patient_result)
    patient_id = patient_result.split("ID: ")[1].strip() if "ID: " in patient_result else None
    print()
    
    # Add a disease
    print("2. Adding a disease...")
    disease_result = await agent.execute({
        "type": "add_disease",
        "name": "Hypertension",
        "properties": {"severity": "moderate"}
    }, context)
    print(disease_result)
    disease_id = disease_result.split("ID: ")[1].strip() if "ID: " in disease_result else None
    print()
    
    # Add a treatment
    print("3. Adding a treatment...")
    treatment_result = await agent.execute({
        "type": "add_treatment",
        "name": "Lisinopril",
        "properties": {"type": "ACE inhibitor", "dosage": "10mg daily"}
    }, context)
    print(treatment_result)
    treatment_id = treatment_result.split("ID: ")[1].strip() if "ID: " in treatment_result else None
    print()
    
    # Link patient to disease
    if patient_id and disease_id:
        print("4. Linking patient to disease...")
        link_result = await agent.execute({
            "type": "link_patient_disease",
            "patient_id": patient_id,
            "disease_id": disease_id
        }, context)
        print(link_result)
        print()
    
    # Link patient to treatment
    if patient_id and treatment_id:
        print("5. Linking patient to treatment...")
        link_result = await agent.execute({
            "type": "link_patient_treatment",
            "patient_id": patient_id,
            "treatment_id": treatment_id
        }, context)
        print(link_result)
        print()
    
    # Query patient info
    if patient_id:
        print("=" * 60)
        print("Demo: Querying Patient Information")
        print("=" * 60)
        print()
        
        print("6. Getting patient information...")
        patient_info = await agent.execute({
            "type": "query_patient",
            "patient_id": patient_id
        }, context)
        print(patient_info)
        print()
    
    # Get recommendations
    if patient_id:
        print("7. Getting treatment recommendations...")
        recommendations = await agent.execute({
            "type": "get_recommendations",
            "patient_id": patient_id
        }, context)
        print(recommendations)
        print()
    
    # Get statistics
    print("=" * 60)
    print("Demo: Ontology Statistics")
    print("=" * 60)
    print()
    
    print("8. Getting ontology statistics...")
    stats = await agent.execute({"type": "stats"}, context)
    print(stats)
    print()
    
    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

