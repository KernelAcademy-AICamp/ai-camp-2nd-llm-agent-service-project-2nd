#!/bin/bash
# Create project structure for TDD-based legal system

# Source directories
mkdir -p src/{models,services,api,core,schemas,utils}
mkdir -p src/services/{ocr,rag,llm,crawler,risk}

# Test directories (mirroring source structure for TDD)
mkdir -p tests/{unit,integration,e2e}
mkdir -p tests/unit/{models,services,api,core,schemas,utils}
mkdir -p tests/unit/services/{ocr,rag,llm,crawler,risk}

# Additional directories
mkdir -p docs
mkdir -p scripts
mkdir -p data/{templates,documents}

# Create __init__.py files
touch src/__init__.py
touch src/{models,services,api,core,schemas,utils}/__init__.py
touch src/services/{ocr,rag,llm,crawler,risk}/__init__.py
touch tests/__init__.py
touch tests/{unit,integration,e2e}/__init__.py
touch tests/unit/{models,services,api,core,schemas,utils}/__init__.py
touch tests/unit/services/{ocr,rag,llm,crawler,risk}/__init__.py

echo "✅ Project structure created successfully!"