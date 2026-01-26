#!/bin/bash
# Install Stockfish

# Start the FastAPI app with uvicorn
uvicorn main:app --host 0.0.0.0 --port $PORT
