#!/bin/bash

# Ensure ~/.local/bin is in PATH for streamlit
export PATH=$HOME/.local/bin:$PATH
python3 -m streamlit run streamlit/app.py --server.address=0.0.0.0 --server.port=8501
