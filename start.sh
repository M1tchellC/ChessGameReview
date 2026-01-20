#!/bin/bash
# Install Stockfish
sudo apt-get update
sudo apt-get install -y stockfish

# Start the FastAPI app with uvicorn
uvicorn main:app --host 0.0.0.0 --port $PORT
