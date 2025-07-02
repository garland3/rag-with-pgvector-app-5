#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Starting environment setup ---"

# Install system dependencies for PostgreSQL client
echo "Updating package lists and installing postgresql-client..."
sudo apt-get update && sudo apt-get install -y postgresql-client

# Install Python dependencies
echo "Installing Python packages from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Installing additional Python packages for RAG..."
pip install pgvector langchain langchain-openai

# Wait for the PostgreSQL container to be ready
echo "Waiting for PostgreSQL to become available..."
until PGPASSWORD=password psql -h localhost -U postgres -d your_app_db -c '\q' &>/dev/null; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
>&2 echo "Postgres is up - continuing setup."

# Connect to the database and enable the pgvector extension
echo "Enabling the 'vector' extension in the database..."
PGPASSWORD=password psql -h localhost -U postgres -d your_app_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "--- Environment setup complete ---"
