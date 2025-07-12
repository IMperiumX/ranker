# Apache Superset Integration Guide

This document provides detailed information about the Apache Superset integration with the Real-Time Leaderboard Service, including setup, configuration, and usage of advanced reporting features.

## 📊 Overview

The Real-Time Leaderboard Service integrates with Apache Superset to provide comprehensive analytics and visualization capabilities. This integration includes:

- **7 Specialized Database Views** optimized for analytics
- **Advanced Reporting APIs** for programmatic access
- **Real-time Dashboards** with interactive visualizations
- **Custom Color Schemes** tailored for leaderboard data
- **Automated Setup Process** for quick deployment

## 🚀 Quick Setup

### Prerequisites
- Docker and Docker Compose installed
- Main leaderboard application running
- At least 4GB RAM available for Superset services

### One-Command Setup
```bash
# Complete setup with analytics and visualization
./setup_superset.sh
```

This script will:
1. Set up database views for analytics
2. Start Apache Superset services
3. Initialize Superset database
4. Create admin user (admin/admin)
5. Configure database connections
6. Generate demo data for testing

## 📈 Database Views for Analytics

### 1. superset_game_analytics
**Purpose**: Game performance metrics and statistics

**Key Fields**:
- `game_id`, `game_name`, `score_type`
- `total_submissions`, `unique_players`
- `avg_score`, `max_score`, `min_score`, `score_range`
- `first_submission`, `last_submission`
- `submissions_per_player`, `submissions_per_day`

**Use Cases**:
- Game popularity comparison
- Performance trend analysis
- Engagement metrics per game

### 2. superset_user_engagement
**Purpose**: User activity and retention patterns

**Key Fields**:
- `user_id`, `user_email`, `user_name`
- `total_submissions`, `games_played`
- `avg_score`, `best_score`
- `activity_span_days`, `active_days`
- `user_status` (Active/Recent/Inactive)
- `days_since_last_activity`

**Use Cases**:
- User retention analysis
- Activity pattern identification
- Engagement scoring

### 3. superset_leaderboard_trends
**Purpose**: Ranking movements and competition trends

**Key Fields**:
- `game_id`, `user_id`, `score`, `submitted_at`
- `daily_rank`, `user_submission_sequence`
- `previous_score`, `score_improvement`
- `performance_trend` (Better/Worse/Same)

**Use Cases**:
- Leaderboard movement visualization
- Competition intensity analysis
- Player progress tracking

### 4. superset_scoring_patterns
**Purpose**: Behavioral analysis by time and difficulty

**Key Fields**:
- `hour_bucket`, `submission_date`, `hour_of_day`
- `day_of_week`, `time_period` (Morning/Afternoon/Evening/Night)
- `submission_count`, `unique_users`
- `easy_count`, `medium_count`, `hard_count`

**Use Cases**:
- Peak activity identification
- Difficulty preference analysis
- Time-based behavior patterns

### 5. superset_daily_metrics
**Purpose**: Daily activity and KPI metrics

**Key Fields**:
- `metric_date`, `total_submissions`
- `daily_active_users`, `games_with_activity`
- `new_users_active`, `returning_users_active`
- `day_type` (Weekend/Weekday)

**Use Cases**:
- Daily KPI monitoring
- Growth tracking
- Seasonal pattern analysis

### 6. superset_user_performance
**Purpose**: Individual user performance analysis

**Key Fields**:
- `user_id`, `game_id`, `best_score`, `avg_score`
- `score_improvement`, `improvement_trend`
- `player_type` (Beginner/Casual/Regular/Dedicated)
- `attempts_per_day`

**Use Cases**:
- Player segmentation
- Performance improvement tracking
- Skill level classification

### 7. superset_game_popularity
**Purpose**: Game popularity and growth trends

**Key Fields**:
- `game_id`, `week_start`, `weekly_submissions`
- `weekly_players`, `new_players_this_week`
- `popularity_tier` (Top/Popular/Niche)
- `submissions_per_player_per_week`

**Use Cases**:
- Game lifecycle analysis
- Growth trend identification
- Player acquisition tracking

## 🔧 Advanced API Endpoints

### Game Analytics
```bash
GET /api/reports/game-analytics/
```
**Parameters**:
- `period`: daily, weekly, monthly
- `game_id`: (optional) filter by specific game

**Response**: Comprehensive game performance metrics

### User Engagement
```bash
GET /api/reports/user-engagement/
```
**Parameters**:
- `period`: daily, weekly, monthly

**Response**: User activity patterns and retention metrics

### Leaderboard Trends
```bash
GET /api/reports/leaderboard-trends/
```
**Parameters**:
- `game_id`: (required) specific game to analyze
- `period`: daily, weekly, monthly

**Response**: Historical ranking movements and trends

### Scoring Patterns
```bash
GET /api/reports/scoring-patterns/
```
**Parameters**:
- `period`: daily, weekly, monthly
- `game_id`: (optional) filter by specific game

**Response**: Behavioral patterns and peak activity analysis

## 📊 Dashboard Examples

### Executive Dashboard
**Purpose**: High-level KPIs and business metrics

**Key Charts**:
- Daily Active Users (Line Chart)
- Total Submissions (Bar Chart)
- Game Popularity (Pie Chart)
- User Retention (Cohort Analysis)
- Revenue/Engagement Funnel

**Filters**:
- Date Range Picker
- Game Selector
- User Segment Filter

### Game Performance Dashboard
**Purpose**: Individual game analytics and comparisons

**Key Charts**:
- Score Distribution (Histogram)
- Player Count Over Time (Line Chart)
- Difficulty Level Analysis (Stacked Bar)
- Leaderboard Movement (Heatmap)
- Submission Frequency (Calendar Heatmap)

**Filters**:
- Game Multi-Select
- Score Type Filter
- Time Period Selector

### User Engagement Dashboard
**Purpose**: User behavior and retention analysis

**Key Charts**:
- Activity Patterns (Line Chart)
- Session Duration (Box Plot)
- User Segments (Treemap)
- Retention Cohort (Cohort Table)
- Engagement Score Distribution (Histogram)

**Filters**:
- User Type Filter
- Registration Date Range
- Activity Level Selector

### Operational Metrics Dashboard
**Purpose**: System health and performance monitoring

**Key Charts**:
- API Response Times (Line Chart)
- Error Rate (Gauge Chart)
- Database Performance (Multiple Metrics)
- Cache Hit Ratio (Gauge Chart)
- Server Resource Usage (Time Series)

**Filters**:
- Environment Selector
- Service Component Filter
- Alert Threshold Slider

## 🎨 Custom Visualizations

### Leaderboard Heatmap
**Purpose**: Visualize ranking changes over time
**Configuration**:
- X-axis: Time periods
- Y-axis: User ranks
- Color: Score values
- Size: Submission frequency

### Competition Intensity Chart
**Purpose**: Show competitive activity levels
**Configuration**:
- Bubble chart with:
  - X-axis: Average score
  - Y-axis: Submission frequency
  - Bubble size: Number of players
  - Color: Game category

### User Journey Flow
**Purpose**: Visualize user progression paths
**Configuration**:
- Sankey diagram showing:
  - Source: User segments
  - Target: Achievement levels
  - Flow: Transition rates

## 🔐 Security and Access Control

### Role-Based Access
- **Admin**: Full access to all dashboards and data
- **Analyst**: Read-only access to analytics dashboards
- **Game Manager**: Access to game-specific dashboards
- **Public**: Limited access to summary dashboards

### Data Security
- Database connections use encrypted passwords
- User data is anonymized where possible
- Audit logs track all dashboard access
- Row-level security filters sensitive data

## 🚀 Performance Optimization

### Database Optimization
- Materialized views for complex queries
- Indexed columns for fast filtering
- Partitioned tables for large datasets
- Query result caching

### Superset Configuration
- Redis caching for dashboard metadata
- Celery workers for background tasks
- Connection pooling for database queries
- Thumbnail generation for faster loading

## 🔧 Maintenance and Monitoring

### Regular Tasks
```bash
# Update database views
docker-compose exec django python manage.py setup_superset_views

# Clear Superset cache
docker-compose -f docker-compose.superset.yml exec superset superset cache-clear

# Update user permissions
docker-compose -f docker-compose.superset.yml exec superset superset sync-permissions
```

### Health Checks
```bash
# Check Superset health
curl http://localhost:8088/health

# Check database connection
docker-compose -f docker-compose.superset.yml exec superset superset test-db

# View service logs
docker-compose -f docker-compose.superset.yml logs superset
```

### Backup and Recovery
```bash
# Backup Superset metadata
docker-compose -f docker-compose.superset.yml exec superset superset export-dashboards

# Backup database views
pg_dump -h localhost -U ranker_user -d ranker --schema-only > views_backup.sql

# Restore from backup
docker-compose -f docker-compose.superset.yml exec superset superset import-dashboards
```

## 📚 Advanced Configuration

### Custom Color Schemes
The integration includes a custom color scheme optimized for leaderboard data:
```python
EXTRA_CATEGORICAL_COLOR_SCHEMES = [
    {
        "id": "leaderboard_colors",
        "description": "Leaderboard Color Scheme",
        "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", ...]
    }
]
```

### Feature Flags
Key features enabled for analytics:
```python
FEATURE_FLAGS = {
    'DASHBOARD_CROSS_FILTERS': True,
    'DRILL_TO_DETAIL': True,
    'ENABLE_EXPLORE_DRAG_AND_DROP': True,
    'THUMBNAILS': True,
    'DYNAMIC_PLUGINS': True,
}
```

### Email Alerts
Configure email notifications for key metrics:
```python
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'your-email@gmail.com'
SMTP_PASSWORD = 'your-app-password'
```

## 🐛 Troubleshooting

### Common Issues

**Superset won't start**:
- Check Docker resources (need 4GB+ RAM)
- Verify network connectivity
- Check port conflicts (8088)

**Database connection failed**:
- Verify PostgreSQL is running
- Check database credentials
- Ensure network connectivity between containers

**Views not updating**:
- Run `setup_superset_views` command
- Check database permissions
- Verify view dependencies

**Dashboards loading slowly**:
- Enable caching in Superset
- Optimize database queries
- Add database indexes

**Data not appearing**:
- Check time filters in dashboard
- Verify data exists in source tables
- Check user permissions

### Log Analysis
```bash
# View all Superset logs
docker-compose -f docker-compose.superset.yml logs

# Filter for errors
docker-compose -f docker-compose.superset.yml logs | grep ERROR

# Follow live logs
docker-compose -f docker-compose.superset.yml logs -f superset
```

## 📞 Support

For Superset-specific issues:
- Check the [Apache Superset Documentation](https://superset.apache.org/docs/intro)
- Review the configuration in `superset_config/superset_config.py`
- Examine the database views in the management command
- Test API endpoints independently

For integration issues:
- Verify all services are running: `docker-compose ps`
- Check network connectivity between services
- Review environment variables and secrets
- Test database connections manually

---

**Ready to explore your data? Start analyzing with Apache Superset! 📊**
