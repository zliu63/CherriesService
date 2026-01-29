#!/bin/bash

# Initialize pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Activate cherries-service virtualenv
pyenv activate cherries-service

# Run the FastAPI application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
