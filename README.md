# Real-Time Leaderboard Service

A production-grade, real-time leaderboard system built with Django and Redis, featuring comprehensive analytics and visualization capabilities through Apache Superset integration.

## 🚀 Features

### Core Functionality
- **Real-time Leaderboards**: Sub-100ms leaderboard queries using Redis Sorted Sets
- **Multi-game Support**: Flexible game management with different scoring types
- **User Management**: JWT-based authentication with user profiles
- **Score Tracking**: Persistent storage with Redis for speed + PostgreSQL for durability
- **Rank Calculation**: Instant rank updates and personal best tracking

### Advanced Analytics & Reporting
- **Game Analytics**: Comprehensive game performance metrics and trends
- **User Engagement**: User activity patterns and retention analytics
- **Leaderboard Trends**: Historical ranking movements and competition analysis
- **Scoring Patterns**: Behavioral analysis and peak activity identification
- **Daily Metrics**: Real-time dashboard with key performance indicators

### Data Visualization
- **Apache Superset Integration**: Rich dashboards and interactive visualizations
- **7 Specialized Database Views**: Optimized for analytics and reporting
- **Real-time Charts**: Live updating charts and metrics
- **Custom Dashboards**: Tailored visualizations for different user roles

## 🏗️ Architecture

### Technology Stack
- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL 14+ (persistent storage)
- **Cache**: Redis 7+ (leaderboards and caching)
- **Analytics**: Apache Superset 3.0+ (visualization)
- **Task Queue**: Celery with Redis broker
- **Containerization**: Docker & Docker Compose

### Performance Specifications
- **Score Submission**: < 200ms response time
- **Leaderboard Queries**: < 100ms response time
- **Concurrent Users**: 1,000+ score submissions per second
- **Scalability**: Horizontally scalable architecture

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `GET /api/users/me/` - User profile

### Games
- `GET /api/games/` - List all games
- `GET /api/games/active/` - List active games

### Scores & Leaderboards
- `POST /api/scores/` - Submit score
- `GET /api/leaderboard/{game_id}/` - Game leaderboard
- `GET /api/leaderboard/global/` - Global leaderboard
- `GET /api/leaderboard/{game_id}/my-rank/` - User's rank
- `GET /api/scores/history/` - Score history

### Basic Reporting
- `GET /api/reports/top-players/` - Top players report

### Advanced Analytics (Admin Only)
- `GET /api/reports/game-analytics/` - Game performance metrics
- `GET /api/reports/user-engagement/` - User activity analytics
- `GET /api/reports/leaderboard-trends/` - Ranking trends analysis
- `GET /api/reports/scoring-patterns/` - Behavioral patterns analysis

## 🔧 Quick Start

### Standard Setup
```bash
# Clone the repository
git clone <repository-url>
cd ranker

# Start the main application
./setup.sh

# Access the API
curl http://localhost:9000/api/docs/
```

### Advanced Setup with Superset
```bash
# Complete setup with analytics and visualization
./setup_superset.sh

# Access services
# API Documentation: http://localhost:9000/api/docs/
# Apache Superset: http://localhost:8088 (admin/admin)
```

## 📈 Analytics & Visualization

### Database Views for Analytics
The system includes 7 specialized database views optimized for analytics:

1. **superset_game_analytics** - Game performance and statistics
2. **superset_user_engagement** - User activity and retention patterns
3. **superset_leaderboard_trends** - Ranking movements and trends
4. **superset_scoring_patterns** - Behavioral analysis by time and difficulty
5. **superset_daily_metrics** - Daily activity and KPI metrics
6. **superset_user_performance** - Individual user performance analysis
7. **superset_game_popularity** - Game popularity and growth trends

### Superset Dashboard Examples
- **Executive Dashboard**: High-level KPIs and trends
- **Game Performance**: Individual game analytics and comparisons
- **User Engagement**: Activity patterns and retention metrics
- **Leaderboard Analysis**: Competition intensity and movements
- **Operational Metrics**: System health and performance

## 🛠️ Development

### Running Tests
```bash
# Run all tests
docker-compose exec django python manage.py test

# Run specific test modules
docker-compose exec django python manage.py test ranker.scores.tests
docker-compose exec django python manage.py test ranker.games.tests
```

### Development Commands
```bash
# Create database views for Superset
docker-compose exec django python manage.py setup_superset_views

# Generate demo data
docker-compose exec django python manage.py setup_demo_data

# Run migrations
docker-compose exec django python manage.py migrate

# Create superuser
docker-compose exec django python manage.py createsuperuser
```

### API Documentation
- **Swagger UI**: `http://localhost:9000/api/docs/`
- **ReDoc**: `http://localhost:9000/api/redoc/`
- **OpenAPI Schema**: `http://localhost:9000/api/schema/`

## 🔐 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Configurable rate limits on sensitive endpoints
- **Input Validation**: Comprehensive data validation
- **CORS Configuration**: Cross-origin resource sharing support
- **Admin Protection**: Role-based access control

## 📊 Performance Monitoring

### Key Metrics
- **Score Submission Rate**: Submissions per second
- **Leaderboard Query Time**: Average response time
- **Active Users**: Daily/weekly active users
- **Game Popularity**: Submissions per game
- **User Retention**: User engagement over time

### Monitoring Tools
- **Apache Superset**: Real-time dashboards and alerts
- **Django Admin**: System administration interface
- **Redis CLI**: Cache monitoring and debugging
- **PostgreSQL**: Database performance metrics

## 🚀 Production Deployment

### Environment Variables
```env
# Django Settings
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com

# Database
POSTGRES_DB=ranker
POSTGRES_USER=ranker_user
POSTGRES_PASSWORD=your-db-password

# Redis
REDIS_URL=redis://redis:6379/0

# Superset
SUPERSET_SECRET_KEY=your-superset-secret-key
```

### Scaling Considerations
- **Horizontal Scaling**: Multiple Django instances behind load balancer
- **Database Scaling**: Read replicas for analytics queries
- **Redis Clustering**: Redis Cluster for high availability
- **CDN Integration**: Static file serving optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Apache Superset Documentation](https://superset.apache.org/docs/intro)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 📞 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check the documentation
- Review the API endpoints in Swagger UI

---

**Built with ❤️ using Django, Redis, and Apache Superset**
