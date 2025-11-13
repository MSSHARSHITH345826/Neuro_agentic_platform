# NeuroStack Healthcare Agent Demo

This demo showcases the integration of the ontology layer with NeuroStack's agentic framework.

## Overview

The healthcare agent demonstrates how agents can:
- Use the ontology layer to manage structured healthcare data
- Query patient information, diseases, and treatments
- Add new entities and relationships to the ontology
- Get treatment recommendations based on ontology knowledge

## Installation

### Quick Install (Windows)
```bash
# From the project root directory
setup.bat
```

### Quick Install (Linux/Mac)
```bash
# From the project root directory
chmod +x setup.sh
./setup.sh
```

### Manual Install

First, install the required dependencies:

```bash
# From the project root directory
pip install -r requirements.txt
```

Or install minimal dependencies:
```bash
pip install structlog pydantic
```

For Excel file support (optional):
```bash
pip install pandas openpyxl
```

**Note:** The import path issue has been fixed. If you still see `ModuleNotFoundError: No module named 'neurostack'`, make sure you're running from the `neurostack/examples` directory.

## Running the Demo

```bash
# From the project root directory
cd neurostack/examples
python healthcare_agent.py
```

Or from the project root:
```bash
python -m neurostack.examples.healthcare_agent
```

## What the Demo Does

1. **Initializes the Ontology Manager**: Sets up the ontology layer
2. **Loads OWL Files** (if available): Attempts to load ontology files from the `ontology 1/ontology` folder
3. **Creates a Healthcare Agent**: Instantiates an agent with ontology tools
4. **Adds Sample Data**:
   - Creates a patient (John Doe)
   - Adds a disease (Hypertension)
   - Adds a treatment (Lisinopril)
5. **Links Entities**: Creates relationships between patient, disease, and treatment
6. **Queries Information**: Retrieves comprehensive patient information
7. **Gets Recommendations**: Provides treatment recommendations based on ontology knowledge
8. **Shows Statistics**: Displays ontology statistics

## Architecture

### Ontology Layer Components

- **OntologyManager**: Main interface for ontology operations
- **OWLLoader**: Parses OWL ontology files
- **NeuroStackGraphAdapter**: Adapts the HealthcareGraph to work with NeuroStack
- **Ontology Tools**: Tools that agents can use to interact with the ontology

### Agent Integration

The HealthcareAgent extends the base Agent class and:
- Uses ontology tools for querying and manipulation
- Integrates with NeuroStack's memory system
- Can use the reasoning engine for complex tasks
- Maintains state and context throughout execution

## Extending the Demo

You can extend this demo by:
- Loading your own OWL files
- Adding more entity types
- Creating custom relationship types
- Building more complex query patterns
- Integrating with external healthcare systems

