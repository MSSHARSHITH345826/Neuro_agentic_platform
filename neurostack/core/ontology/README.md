# NeuroStack Ontology Layer

This module provides ontology management capabilities for NeuroStack agents, allowing them to work with structured knowledge graphs and semantic data.

## Overview

The ontology layer integrates with NeuroStack's agentic framework to enable:
- Loading and parsing OWL ontology files
- Managing entities and relationships in knowledge graphs
- Querying and manipulating ontology data
- Using ontology knowledge in agent reasoning

## Components

### OntologyManager

The main interface for ontology operations. Provides methods for:
- Loading OWL files
- Adding/querying entities
- Managing relationships
- Getting statistics and integrity checks

### OWLLoader

Parses OWL ontology files and extracts:
- Classes (entities)
- Object properties (relationships)
- Individuals (instances)
- Namespaces and metadata

### NeuroStackGraphAdapter

Adapts the existing HealthcareGraph structure to work seamlessly with NeuroStack's ontology layer. Provides a unified interface for:
- Entity management
- Relationship queries
- Patient information retrieval
- Graph operations

### Ontology Tools

Tools that agents can use to interact with the ontology:
- `OntologyQueryTool`: Query entities by type, name, or properties
- `OntologyGetEntityTool`: Get detailed entity information
- `OntologyGetPatientInfoTool`: Get comprehensive patient data
- `OntologyAddEntityTool`: Add new entities
- `OntologyAddRelationshipTool`: Create relationships
- `OntologyStatsTool`: Get ontology statistics

## Usage Example

```python
from neurostack.core.ontology import OntologyManager
from neurostack.core.agents.base import Agent, AgentConfig

# Initialize ontology manager
ontology_manager = OntologyManager()

# Load an OWL file
ontology_manager.load_ontology("path/to/ontology.owl")

# Create an agent with ontology tools
from neurostack.core.ontology.tools import OntologyQueryTool
agent = Agent(AgentConfig(name="MyAgent"))
agent.add_tool(OntologyQueryTool(ontology_manager))

# Use the agent to query ontology
result = await agent.execute("Find all patients")
```

## Integration with Existing Graph

The ontology layer integrates with the existing `HealthcareGraph` from the `ontology 1/ontology` folder, adapting it to work with NeuroStack's architecture while preserving all existing functionality.

## Architecture

```
OntologyManager
    ├── OWLLoader (parses OWL files)
    ├── NeuroStackGraphAdapter (wraps HealthcareGraph)
    └── Ontology Tools (for agent use)
```

## Future Enhancements

- Support for more OWL constructs (data properties, restrictions, etc.)
- SPARQL query support
- Ontology versioning
- Multi-ontology management
- Inference capabilities
- Integration with external ontology repositories

