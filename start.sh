#!/bin/bash

# Render provides the port to listen on in the PORT environment variable.
# We use a default of 10000 if it's not set.
PORT=${PORT:-10000}

# Start the Uvicorn server using the determined port.
exec uvicorn main:app --host=0.0.0.0 --port=${PORT}
