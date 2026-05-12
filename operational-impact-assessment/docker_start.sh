#!/bin/bash

# Start the BIA backend
uvicorn BIA_api.app.main:app --host 0.0.0.0 --port 8000 &

# Start the BIA graphical user interface
python3 -m http.server --bind 0.0.0.0 80 --directory ./BIA_gui

