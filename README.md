# YouTube Topic-Scout - Enhanced Edition 🚀

An intelligent Python CLI tool for discovering, analyzing, and summarizing YouTube content with advanced caching, error handling, and performance optimizations.

## ✨ New Features

### 🎯 Enhanced Performance
- **Smart Caching**: Multi-level caching with TTL support
- **Database Optimization**: WAL mode, indexes, and connection pooling
- **Batch Processing**: Efficient API calls and data handling
- **Memory Management**: Streaming processing for large datasets

### 🔍 Advanced Search
- **Progress Indicators**: Rich terminal UI with progress bars
- **Comprehensive Results**: Views, duration, and engagement metrics
- **Fuzzy Search Support**: Enhanced text matching
- **Export Options**: JSON, CSV, and formatted reports

### 🧠 Intelligent Summarization
- **Multi-factor Scoring**: Frequency, position, and length analysis
- **Key Phrase Extraction**: POS-based phrase detection
- **Topic Modeling**: Automatic topic extraction
- **Quality Metrics**: Word count, sentence analysis

### 🛡️ Robust Error Handling
- **Retry Logic**: Exponential backoff for API failures
- **Graceful Degradation**: Continues processing on partial failures
- **Comprehensive Logging**: Structured logs with rotation
- **Rate Limiting**: Smart quota management

## 🚀 Quick Start (Local Only)

### Installation
```bash
# Clone and setup
git clone <repository>
cd youtube-topic-scout

# Create virtual environment
python -m venv .venv
.venv\\Scripts\\activate  # Windows PowerShell
# or: source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# (Optional) Download NLTK data if needed
python -m nltk.downloader punkt stopwords averaged_perceptron_tagger
```

### Configuration
```bash
# Copy example config
cp config.example.json config.json

# Edit with your API key
# Or set environment variable: export YOUTUBE_API_KEY="your-key-here"
```

### Run
Backend (FastAPI):
```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend (Vite):
```bash
cd frontend
npm install
npm run dev
```

## 📊 Usage Examples

### Basic Search
```bash
$ python main.py "AI ethics"
```

### With Options
```bash
$ python main.py "deep learning" --max-results 15 --verbose
```

### Database Maintenance
```bash
cd backend/app
python optimize.py stats
python optimize.py optimize
```

## 🔧 Configuration

### Environment Variables
```bash
export YOUTUBE_API_KEY="your-api-key"
export MAX_RESULTS=20
export CACHE_TTL=3600
export API_RETRY_ATTEMPTS=3
```

### Config File (config.json)
```json
{
  "YOUTUBE_API_KEY": "your-api-key-here",
  "MAX_RESULTS": 10,
  "BATCH_SIZE": 50,
  "CACHE_TTL": 3600,
  "API_RETRY_ATTEMPTS": 3,
  "API_RETRY_DELAY": 1,
  "DB_TIMEOUT": 30
}
```

## 📁 File Structure

```
youtube-topic-scout/
├── main.py              # Enhanced CLI interface
├── config.py            # Configuration management
├── logger.py            # Logging setup
├── database.py          # Optimized database layer
├── fetch.py             # YouTube API with caching
├── summarizer.py        # Advanced summarization
├── optimize.py          # Database utilities
├── config.json          # Configuration file
├── requirements.txt     # Dependencies
├── data/
│   ├── videos.db        # SQLite database
│   ├── raw/             # Cached video data
│   ├── cache/           # API response cache
│   └── results/         # Search results
└── logs/                # Application logs
```

## 🎯 Performance Improvements

| Feature | Before | After |
|---------|--------|--------|
| **Database Queries** | Basic FTS5 | Optimized with indexes |
| **API Calls** | No caching | Multi-level caching |
| **Memory Usage** | Full loading | Streaming processing |
| **Error Handling** | Basic | Comprehensive retry logic |
| **User Experience** | Simple print | Rich progress indicators |
| **Configuration** | Hardcoded | Flexible config system |

## 🔍 Advanced Features

### Rich Terminal Interface
- Progress bars during searches
- Color-coded results
- Interactive tables
- Real-time statistics

### Smart Caching
- Search result caching (1 hour TTL)
- Video details caching
- Transcript caching
- Automatic cache invalidation

### Database Enhancements
- Write-ahead logging (WAL) mode
- Performance indexes
- Automatic cleanup
- Vacuum optimization

### Enhanced Summarization
- Multi-factor sentence scoring
- Key phrase extraction
- Topic modeling
- Quality metrics

## 🛠️ Development

### Running Tests
```bash
# Install development dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/
```

### Code Quality
```bash
# Format code
black *.py

# Check types
mypy *.py

# Lint code
flake8 *.py
```

## 📈 Monitoring

### Log Files
- Application logs: `logs/youtube_scout_YYYYMMDD.log`
- Search queries and results
- Performance metrics
- Error tracking

### Database Stats
```bash
python optimize.py stats
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**API Key Issues**
```bash
# Check API key
echo $YOUTUBE_API_KEY

# Test API connection
python -c "from fetch import fetch_videos; print(fetch_videos('test', 1))"
```

**Database Issues**
```bash
# Reset database
rm data/videos.db
python main.py "test query"

# Optimize database
python optimize.py optimize
```

**Performance Issues**
```bash
# Clear cache
rm -rf data/cache/*
python optimize.py optimize
```

### Getting Help
- Check logs in `logs/` directory
- Enable verbose logging in code or via env
- Open an issue on GitHub
