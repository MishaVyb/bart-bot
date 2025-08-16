# 🐈‍⬛ Bart Bot

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Test workflow](https://github.com/MishaVyb/bart-bot/actions/workflows/tests.yml/badge.svg)](https://github.com/MishaVyb/bart-bot/actions/workflows/tests.yml)
[![Deploy workflow](https://github.com/MishaVyb/bart-bot/actions/workflows/deploy.yml/badge.svg)](https://github.com/MishaVyb/bart-bot/actions/workflows/deploy.yml)
[![PTB](https://img.shields.io/badge/PTB-20.1-blue)](https://python-telegram-bot.org/)
[![Pyrogram](https://img.shields.io/badge/Pyrogram-2.0.1-blue)](https://pyrogram.org/)
[![Anyio](https://img.shields.io/badge/Anyio-3.6.2-blue)](https://anyio.readthedocs.io/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.4-blue)](https://www.sqlalchemy.org/)

> 🥛🍥🥟🍚🥓🍙🥖☕️🍣 <--- 🐈‍⬛

A delightful Telegram bot that behaves like your real pet! Send photos to build a collection, then feed your virtual pet with emoji food to receive random photos from your gallery.

## ✨ Features

### 🐾 Pet-like Behavior
- **Unique Responses**: Every interaction gets a different pre-defined message, just like a real pet
- **Flexible Storage**: Each participant has their own photo storage that can be shared with family members
- **Unpredictable**: Randomly selects images to reply after feeding, keeping interactions exciting

### 🏗️ Technical Excellence
- **Asynchronous Architecture**: Built with modern async/await patterns for optimal performance
- **Persistent Storage**: All chat history and photos stored in PostgreSQL database
- **Custom Middleware System**: Familiar middleware pattern similar to web frameworks
- **Comprehensive Testing**: Automated E2E tests running in Telegram's test environment

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 13+
- Telegram Bot Token

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/MishaVyb/bart-bot.git
   cd bart-bot
   ```

2. **Set up virtual environment**
   ```bash
   make venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   make install
   ```

4. **Configure environment**
   ```bash
   cp build.env.example build.env
   # Edit build.env with your configuration
   ```

5. **Set up database**
   ```bash
   make database
   ```

6. **Run the bot**
   ```bash
   python -m src.polling
   ```

### Docker Deployment

For production deployment using Docker:

```bash
# Build and run with Docker Compose
make build_run
```

## 📖 Usage

### Basic Interaction
1. **Start the bot**: Send `/start` to begin
2. **Upload photos**: Send any photo to build your pet's photo collection
3. **Feed your pet**: Use the emoji food buttons (🥛🍥🥟🍚🥓🍙🥖☕️🍣) to feed your virtual pet
4. **Get responses**: Your pet will reply with random photos from your collection

### Family Sharing
- **Forward messages** from other users to share their photo storage
- **Request permission** from storage owners to join their family
- **Collaborative feeding** with family members

### Admin Commands
- `/admin_loaddata` - Load data from dump file (admin only)
- `/count` - Check total media count in your storage

## 🛠️ Development

### Project Structure
```
bart-bot/
├── src/
│   ├── application/          # Bot application logic
│   │   ├── handlers.py       # Message handlers
│   │   ├── middlewares.py    # Custom middleware
│   │   └── tasks.py          # Background tasks
│   ├── database/             # Database models and engine
│   ├── content.py            # Bot content and messages
│   └── configurations.py     # Configuration management
├── tests/                    # Test suite
├── alembic/                  # Database migrations
└── data/                     # Data storage
```

### Code Quality
The project uses several tools to maintain code quality:

```bash
# Run all code quality checks
make ci

# Format code
black .
isort .

# Type checking
mypy .

# Linting
flake8 .
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src
```

### Database Management
```bash
# Reset database and migrations
make database

# Create new migration
alembic revision --autogenerate

# Apply migrations
alembic upgrade head
```

## 🔧 Configuration

Key configuration options in `build.env`:

```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id

# Database
DATABASE_URL=postgresql://user:password@localhost/bart_bot

# Content
CONTENT_FILEPATH=bart-bot.content.yaml

# Scheduling
SEND_FEED_ME_MESSAGE_CRONS=["0 9 * * *"]  # Daily at 9 AM
```

## 🐳 Docker

### Production Deployment
```bash
# Build image
docker build -t vybornyy/bart-bot .

# Run with Docker Compose
docker-compose up -d
```

### Services
- **polling**: Main bot application
- **db**: PostgreSQL database

## 📊 Monitoring

The bot includes comprehensive logging and monitoring:
- Structured logging with configurable levels
- Database query monitoring
- Error tracking and reporting
- Performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow the existing code style (Black, isort, flake8)
- Add tests for new features
- Update documentation as needed
- Use type hints throughout

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [python-telegram-bot](https://python-telegram-bot.org/)
- Database powered by [SQLAlchemy](https://www.sqlalchemy.org/)
- Testing with [pytest](https://pytest.org/)
- Containerized with [Docker](https://www.docker.com/)

---

**Made with ❤️ for pet lovers everywhere** 🐾

