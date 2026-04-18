#!/bin/bash
set -e
echo "Starting CDD Orchestrator Environment Setup..."
mkdir -p cdd/llm cdd/orchestrator/activities cdd/parsers cdd/sandbox/templates cdd/state tests .cdd/context
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .
docker-compose -f docker-compose.temporal.yml up -d
if [ ! -f .env ]; then
  echo "OPENAI_API_KEY=your_key_here" >> .env
  echo "ANTHROPIC_API_KEY=your_key_here" >> .env
  echo "CREATED .env placeholder. Update with real keys."
fi
echo "Setup complete. Run 'temporal server-ui' to check orchestrator status."
