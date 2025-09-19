import sys
import os
import uvicorn

# Voeg de project-root toe aan het Python-pad
# Dit zorgt ervoor dat imports zoals 'from src.core...' werken
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Start uvicorn programmatisch
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)