# NeuroStack Installation Guide

## Quick Start

1. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Demo**

   ```bash
   cd neurostack/examples
   python healthcare_agent.py
   ```

## Required Dependencies

### Core Dependencies (Required)
- `structlog>=23.0.0` - Structured logging
- `pydantic>=2.0.0` - Data validation

### Optional Dependencies

**For Excel File Support:**
- `pandas>=2.0.0` - Data analysis (recommended)
- `openpyxl>=3.1.0` - Excel file reading (alternative to pandas)

**For LLM Integrations:**
- `openai>=1.0.0` - OpenAI API
- `anthropic>=0.7.0` - Anthropic Claude API
- `httpx>=0.24.0` - HTTP client for Azure OpenAI

## Installation Options

### Option 1: Install All Dependencies
```bash
pip install -r requirements.txt
```

### Option 2: Install Only Core Dependencies
```bash
pip install structlog pydantic
```

### Option 3: Install Core + Excel Support
```bash
pip install structlog pydantic pandas openpyxl
```

## Troubleshooting

### ModuleNotFoundError: No module named 'structlog'

**Solution:** Install dependencies:
```bash
pip install structlog pydantic
```

### ModuleNotFoundError: No module named 'neurostack'

**Solution:** Make sure you're running from the correct directory. The script automatically adds the project root to Python path, but if issues persist:

```bash
# From project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python neurostack/examples/healthcare_agent.py
```

### Excel File Not Loading

**Solution:** Install Excel support libraries:
```bash
pip install pandas openpyxl
```

## Development Setup

For development, you may want to install in editable mode:

```bash
pip install -e .
```

This allows you to modify the code without reinstalling.

