#!/bin/bash
echo "Installing NeuroStack dependencies..."
pip install structlog pydantic
echo ""
echo "For Excel support (optional), run:"
echo "  pip install pandas openpyxl"
echo ""
echo "Dependencies installed! You can now run:"
echo "  cd neurostack/examples"
echo "  python healthcare_agent.py"

