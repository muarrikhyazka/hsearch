# HSSearch - Intelligent HS Code Search Engine

🔍 **Smart search system for Harmonized System (HS) codes with AI-powered features**

HSSearch is a comprehensive search engine designed to help users quickly find and identify HS (Harmonized System) codes with intelligent search capabilities, bilingual support, and modern web interface.

## ✨ Features

### 🤖 AI-Powered Search
- **Smart Search Algorithm**: Fuzzy matching with advanced scoring system
- **Semantic Search**: TF-IDF vectorization with cosine similarity
- **Typo Correction**: Levenshtein distance-based error detection
- **Auto-suggestions**: Intelligent query completion and recommendations
- **Synonym Recognition**: Comprehensive bilingual synonym dictionary

### 🌐 Bilingual Support
- **English & Indonesian**: Full support for both languages
- **Cross-language Search**: Query in one language, find results in both
- **Smart Translation**: Context-aware bilingual matching

### 📊 Advanced Features
- **Category Filtering**: Search within specific product categories
- **Multi-field Search**: Search across codes, descriptions, and hierarchies
- **Real-time Results**: Instant search with live suggestions
- **Responsive Design**: Modern, mobile-friendly interface
- **Performance Optimized**: Fast search with caching and indexing

### 🔧 Technical Features
- **Vector Search**: Text embedding with similarity matching
- **Fuzzy Matching**: Handles typos and variations
- **Database Integration**: PostgreSQL with full-text search
- **Redis Caching**: High-performance result caching
- **REST API**: Complete API for integration
- **Docker Deployment**: Easy containerized deployment

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- 4GB+ RAM recommended

### Installation
```bash
# Clone repository
git clone https://github.com/muarrikhyazka/hsearch.git
cd hsearch

# Deploy with one command
chmod +x deploy.sh
./deploy.sh
```

### Access
- **Web Interface**: http://localhost
- **API Endpoint**: http://localhost/api/
- **Health Check**: http://localhost/api/health

## 📖 Documentation

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[API Documentation](#api-endpoints)** - REST API reference

## 🏗️ Architecture

### Tech Stack
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python Flask with AI/ML libraries
- **Database**: PostgreSQL with pgvector extension
- **Cache**: Redis for performance optimization
- **Web Server**: Nginx reverse proxy
- **Containerization**: Docker & Docker Compose

### Services
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Nginx     │────│   Backend   │────│ PostgreSQL  │
│ (Port 80)   │    │ (Flask API) │    │ (Database)  │
└─────────────┘    └─────────────┘    └─────────────┘
                            │
                   ┌─────────────┐
                   │    Redis    │
                   │   (Cache)   │
                   └─────────────┘
```

## 🔌 API Endpoints

### Search
```bash
POST /api/search
Content-Type: application/json

{
  "query": "computer",
  "category": "electronics",
  "ai_enabled": true,
  "limit": 20
}
```

### Health Check
```bash
GET /api/health
```

### System Status
```bash
GET /api/status
```

### Auto-suggestions
```bash
GET /api/suggestions?q=compu&limit=5
```

## 📊 Dataset

- **Total Records**: 11,554 HS codes
- **Languages**: English & Indonesian descriptions
- **Hierarchical Structure**: Section → Chapter → Heading → Subheading
- **Categories**: Auto-categorized into 10+ product categories
- **Coverage**: Complete HS code classification system

## 🛠️ Development

### Project Structure
```
hsearch/
├── backend/           # Flask API application
├── frontend/          # Web interface
├── database/          # Database initialization
├── nginx/             # Web server configuration
├── data/              # HS code dataset
├── scripts/           # Deployment & maintenance scripts
├── docker-compose.yml # Container orchestration
└── deploy.sh          # One-click deployment
```

### Local Development
```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f

# Access database
docker-compose exec postgres psql -U hsearch_user -d hsearch_db
```

### Useful Scripts
- `./deploy.sh` - Full deployment
- `./scripts/backup.sh` - Database backup
- `./scripts/update.sh` - Update application
- `./scripts/monitor.sh` - System monitoring

## 🔍 Search Examples

### Basic Search
- **Query**: "computer" → Finds computers, laptops, PCs
- **Query**: "komputer" → Same results (bilingual)
- **Query**: "live animals" → Animal-related HS codes

### Advanced Search
- **Typo Handling**: "compter" → "computer" suggestions
- **Category Filter**: Search within "electronics" category
- **Fuzzy Matching**: Handles variations and abbreviations

### AI Features
- **Smart Suggestions**: Auto-complete as you type
- **Semantic Search**: Finds related terms and concepts
- **Relevance Scoring**: Best matches ranked first

## 📈 Performance

- **Search Speed**: < 100ms average response time
- **Memory Usage**: ~1GB RAM for full deployment
- **Concurrent Users**: Supports 100+ simultaneous searches
- **Uptime**: 99%+ availability with proper deployment

## 🔒 Security

- **CORS Protection**: Configured for web security
- **Input Validation**: SQL injection prevention
- **Rate Limiting**: API abuse protection
- **Secure Headers**: XSS and clickjacking protection

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Muarrikhy Azka**
- GitHub: [@muarrikhyazka](https://github.com/muarrikhyazka)

## 🙏 Acknowledgments

- Harmonized System codes from World Customs Organization
- AI/ML libraries: scikit-learn, NLTK, fuzzywuzzy
- Open source community for amazing tools and libraries

## 🐛 Troubleshooting

### Common Issues

**Port 80 in use:**
```bash
sudo netstat -tulpn | grep :80
# Stop conflicting service
```

**Database connection failed:**
```bash
docker-compose logs postgres
docker-compose restart postgres
```

**Out of memory:**
```bash
docker system prune -f
free -h
```

### Support

- 📖 Check [Deployment Guide](DEPLOYMENT_GUIDE.md)
- 🐛 Report issues on GitHub
- 📧 Contact: [Create an issue](https://github.com/muarrikhyazka/hsearch/issues)

---

⭐ **Star this repository if you find it helpful!**

**Made with ❤️ for better international trade classification**