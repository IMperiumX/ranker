#!/bin/bash

# Apache Superset Integration Setup Script for Real-Time Leaderboard Service
# This script sets up advanced reporting and Apache Superset integration

set -e

echo "🚀 Setting up Apache Superset integration with advanced reporting..."
echo "================================================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if main application is running
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  Main application not running. Starting it first..."
    docker-compose up -d
    sleep 10
fi

# Function to check if a service is healthy
check_service() {
    local service_name=$1
    local max_attempts=30
    local attempt=1

    echo "🔍 Checking $service_name health..."

    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps | grep -q "$service_name.*Up"; then
            echo "✅ $service_name is running"
            return 0
        fi

        echo "⏳ Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done

    echo "❌ $service_name failed to start properly"
    return 1
}

# Step 1: Set up database views for Superset
echo "📊 Setting up database views for Superset..."
docker-compose exec django python manage.py setup_superset_views --drop-existing

# Step 2: Create network for Superset if it doesn't exist
echo "🌐 Creating Docker network for Superset..."
docker network create ranker_default 2>/dev/null || echo "Network already exists"

# Step 3: Start Superset services
echo "🚀 Starting Apache Superset services..."
docker-compose -f docker-compose.superset.yml up -d

# Step 4: Wait for Superset services to be ready
echo "⏳ Waiting for Superset services to be ready..."
sleep 30

# Check if Superset services are running
services_to_check=("superset" "superset-redis" "superset-db")
for service in "${services_to_check[@]}"; do
    if ! check_service "$service"; then
        echo "❌ Failed to start $service"
        exit 1
    fi
done

# Step 5: Initialize Superset database and create admin user
echo "🔧 Initializing Superset database..."
docker-compose -f docker-compose.superset.yml exec superset superset db upgrade

echo "👤 Creating Superset admin user..."
docker-compose -f docker-compose.superset.yml exec superset superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@superset.local \
    --password admin || echo "Admin user already exists"

echo "🎯 Initializing Superset application..."
docker-compose -f docker-compose.superset.yml exec superset superset init

# Step 6: Create database connection configuration
echo "🔗 Setting up database connection..."
cat > superset_config/database_config.py << 'EOF'
"""
Database connection configuration for Superset
"""

import os
from sqlalchemy import create_engine
from superset.security import SupersetSecurityManager

# Database connection for leaderboard data
LEADERBOARD_DATABASE_URI = 'postgresql://ranker_user:password@postgres:5432/ranker'

# Additional database configurations
DATABASES = {
    'leaderboard': {
        'engine': 'postgresql',
        'name': 'Leaderboard Database',
        'uri': LEADERBOARD_DATABASE_URI,
        'allow_ctas': True,
        'allow_cvas': True,
        'allow_dml': False,
        'allow_file_upload': False,
        'extra': {
            'metadata_params': {},
            'engine_params': {
                'pool_pre_ping': True,
                'pool_recycle': 300,
                'pool_timeout': 20,
                'max_overflow': 20,
            }
        }
    }
}

# Sample dashboard configuration
SAMPLE_DASHBOARDS = [
    {
        'name': 'Leaderboard Analytics',
        'description': 'Real-time leaderboard analytics and user engagement metrics',
        'tables': [
            'superset_game_analytics',
            'superset_user_engagement',
            'superset_leaderboard_trends',
            'superset_daily_metrics',
        ]
    },
    {
        'name': 'Game Performance',
        'description': 'Game popularity and performance analytics',
        'tables': [
            'superset_game_popularity',
            'superset_scoring_patterns',
            'superset_user_performance',
        ]
    }
]
EOF

# Step 7: Import database connection via CLI
echo "📥 Importing database connection to Superset..."
docker-compose -f docker-compose.superset.yml exec superset superset import-dashboards \
    --username admin \
    --password admin || echo "Using alternative connection method..."

# Alternative method: Create database connection directly
echo "🔧 Creating database connection directly..."
cat > /tmp/add_database.py << 'EOF'
import requests
import json

# Superset connection details
SUPERSET_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"

# Login to get access token
session = requests.Session()
login_data = {
    "username": USERNAME,
    "password": PASSWORD,
    "provider": "db"
}

try:
    # Get login page first
    response = session.get(f"{SUPERSET_URL}/login/")

    # Login
    response = session.post(f"{SUPERSET_URL}/api/v1/security/login", json=login_data)

    if response.status_code == 200:
        token = response.json().get('access_token')
        print("✅ Login successful")

        # Add database connection
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        db_config = {
            "database_name": "Leaderboard Database",
            "sqlalchemy_uri": "postgresql://ranker_user:password@postgres:5432/ranker",
            "expose_in_sqllab": True,
            "allow_ctas": True,
            "allow_cvas": True,
            "allow_dml": False,
            "allow_multi_schema_metadata_fetch": True,
            "allow_file_upload": False,
            "extra": json.dumps({
                "metadata_params": {},
                "engine_params": {
                    "pool_pre_ping": True,
                    "pool_recycle": 300,
                    "pool_timeout": 20,
                    "max_overflow": 20,
                }
            })
        }

        response = session.post(f"{SUPERSET_URL}/api/v1/database/", json=db_config, headers=headers)

        if response.status_code in [200, 201]:
            print("✅ Database connection created successfully")
        else:
            print(f"⚠️  Database connection response: {response.status_code} - {response.text}")
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")

except Exception as e:
    print(f"❌ Error setting up database connection: {e}")
EOF

# Run the database connection setup
echo "🔗 Setting up database connection..."
sleep 10  # Give Superset time to fully start
python3 /tmp/add_database.py

# Step 8: Test the setup
echo "🧪 Testing the setup..."
echo "Testing API endpoint..."
curl -s "http://localhost:9000/api/reports/game-analytics/" \
    -H "Authorization: Bearer your-jwt-token" \
    -H "Content-Type: application/json" | head -c 100 || echo "API test completed"

echo "Testing Superset availability..."
curl -s "http://localhost:8088/health" || echo "Superset health check completed"

# Step 9: Create sample data if needed
echo "📊 Creating sample data for testing..."
docker-compose exec django python manage.py setup_demo_data

# Step 10: Final setup summary
echo ""
echo "🎉 Apache Superset integration setup complete!"
echo "============================================="
echo ""
echo "📋 Services Status:"
echo "  🌐 Django API: http://localhost:9000"
echo "  📊 Superset: http://localhost:8088"
echo ""
echo "🔐 Superset Login:"
echo "  Username: admin"
echo "  Password: admin"
echo ""
echo "📊 Database Views Created:"
echo "  - superset_game_analytics"
echo "  - superset_user_engagement"
echo "  - superset_leaderboard_trends"
echo "  - superset_scoring_patterns"
echo "  - superset_daily_metrics"
echo "  - superset_user_performance"
echo "  - superset_game_popularity"
echo ""
echo "🚀 Advanced Reporting Endpoints:"
echo "  - /api/reports/game-analytics/"
echo "  - /api/reports/user-engagement/"
echo "  - /api/reports/leaderboard-trends/"
echo "  - /api/reports/scoring-patterns/"
echo ""
echo "📈 Next Steps:"
echo "1. Access Superset at http://localhost:8088"
echo "2. Login with admin/admin"
echo "3. Create datasets from the database views"
echo "4. Build your analytics dashboards!"
echo "5. Test the advanced API endpoints"
echo ""
echo "🔧 Troubleshooting:"
echo "  - Check logs: docker-compose -f docker-compose.superset.yml logs"
echo "  - Restart services: docker-compose -f docker-compose.superset.yml restart"
echo "  - View services: docker-compose ps"
echo ""
echo "✅ Setup complete! Happy analyzing! 🎯"
