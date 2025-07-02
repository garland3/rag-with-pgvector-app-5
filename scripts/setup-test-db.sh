#!/bin/bash

set -e

echo "🧪 Setting up test database..."

# Database connection details
DB_HOST="localhost"
DB_PORT="5432"
DB_USER="postgres"
DB_PASSWORD="password"
TEST_DB_NAME="test_app_db"

# Function to run SQL commands
run_sql() {
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "$1"
}

# Check if PostgreSQL is running
if ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running on $DB_HOST:$DB_PORT"
    echo "Please start PostgreSQL first: docker compose up -d postgres"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Drop test database if it exists
echo "🗑️  Dropping test database if it exists..."
run_sql "DROP DATABASE IF EXISTS $TEST_DB_NAME;" || true

# Create test database
echo "🏗️  Creating test database: $TEST_DB_NAME"
run_sql "CREATE DATABASE $TEST_DB_NAME;"

# Enable pgvector extension
echo "🔗 Enabling pgvector extension..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TEST_DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "✅ Test database setup complete!"
echo "📋 Test database details:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT" 
echo "   Database: $TEST_DB_NAME"
echo "   User: $DB_USER"
echo "   Connection: postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$TEST_DB_NAME"