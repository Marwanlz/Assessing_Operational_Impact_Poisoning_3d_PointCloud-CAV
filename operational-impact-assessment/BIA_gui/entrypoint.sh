#!/bin/bash
python3 write_js_config.py
python3 -m http.server --bind 0.0.0.0 80 --directory /app
