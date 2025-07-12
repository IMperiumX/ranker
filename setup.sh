#!/bin/bash

# Real-Time Leaderboard Service Setup Script
# This script helps you quickly set up and test the leaderboard system

set -e

echo "🚀 Real-Time Leaderboard Service Setup"
echo "========================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists docker; then
    echo "❌ Docker is required but not installed."
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is required but not installed."
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Build and start services
echo ""
echo "🔧 Building and starting services..."
docker-compose -f docker-compose.local.yml up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run migrations
echo ""
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.local.yml exec -T django python manage.py migrate

# Create superuser (non-interactive)
echo ""
echo "👤 Creating superuser account..."
docker-compose -f docker-compose.local.yml exec -T django python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser(
        email='admin@example.com',
        name='Admin User',
        password='admin123'
    )
    print("✅ Superuser created: admin@example.com / admin123")
else:
    print("✅ Superuser already exists")
EOF

# Set up demo data
echo ""
echo "🎮 Setting up demo data..."
docker-compose -f docker-compose.local.yml exec -T django python manage.py setup_demo_data

# Show success message
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "🌐 Your leaderboard service is now running at:"
echo "   • API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/api/docs/"
echo "   • Admin: http://localhost:8000/admin/"
echo ""
echo "🔑 Login credentials:"
echo "   • Admin: admin@example.com / admin123"
echo "   • Demo Users: demo_user_1@example.com / demopass123"
echo ""
echo "🧪 Test the API:"
echo "   1. Register a new user or login with demo credentials"
echo "   2. Get an access token from the login response"
echo "   3. Use the token to access protected endpoints"
echo ""
echo "📚 Quick API test commands:"
echo "   # Login and get token"
echo "   curl -X POST http://localhost:8000/api/auth/login/ \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\":\"demo_user_1@example.com\",\"password\":\"demopass123\"}'"
echo ""
echo "   # Get games (replace YOUR_TOKEN with actual token)"
echo "   curl -X GET http://localhost:8000/api/games/ \\"
echo "     -H 'Authorization: Bearer YOUR_TOKEN'"
echo ""
echo "   # Submit a score"
echo "   curl -X POST http://localhost:8000/api/scores/ \\"
echo "     -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"game_id\":1,\"score\":9500}'"
echo ""
echo "   # View leaderboard"
echo "   curl -X GET http://localhost:8000/api/leaderboard/1/ \\"
echo "     -H 'Authorization: Bearer YOUR_TOKEN'"
echo ""
echo "🛠️ Management commands:"
echo "   # View logs"
echo "   docker-compose -f docker-compose.local.yml logs -f django"
echo ""
echo "   # Stop services"
echo "   docker-compose -f docker-compose.local.yml down"
echo ""
echo "   # Add more demo data"
echo "   docker-compose -f docker-compose.local.yml exec django python manage.py setup_demo_data --users 100 --scores 1000"
echo ""
echo "Happy gaming! 🎮🏆"
