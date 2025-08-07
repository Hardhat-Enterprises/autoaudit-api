# AutoAudit API

Automated Microsoft 365 compliance assessment tool built with FastAPI. This API provides authentication and compliance assessment capabilities for Microsoft 365 environments.

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Azure AD application registration

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Hardhat-Enterprises/autoaudit-api.git
   cd autoaudit-api
   ```

2. **Install dependencies using uv**

   ```bash
   uv sync
   ```

3. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the development server**

   ```bash
   uv run uvicorn app.main:app --reload --port 3000
   ```

5. **Access the API**
   - API Documentation: http://localhost:3000/docs
   - Health Check: http://localhost:3000/health
   - Root Endpoint: http://localhost:3000/

## 📁 Project Structure (not final)

```
autoaudit-api/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── middleware/               # Custom middleware
│   │   │   ├── __init__.py
│   │   │   ├── rate_limiting.py      # Rate limiting middleware
│   │   │   ├── req_logging.py        # Request logging middleware
│   │   │   └── security.py           # Security headers middleware
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py               # Authentication endpoints
│   │       ├── compliance.py         # Compliance data endpoints
│   │       ├── health.py             # Health check endpoints
│   │       ├── monitoring.py         # Monitoring and metrics endpoints
│   │       └── intergration.py       # Cross-team integration endpoints
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                 # Environment configuration
│   │   ├── security.py               # Authentication and authorization
│   │   └── exceptions.py             # Custom exception handling
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── auth_model.py             # Authentication models
│   │   ├── compliance_model.py       # Compliance data models
│   │   └── monitoring_model.py       # Monitoring and metrics models
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py           # Azure AD authentication service
│   │   ├── graph_service.py          # Microsoft Graph API integration
│   │   ├── compliance_service.py     # Compliance data collection
│   │   ├── cache_service.py          # Redis caching service
│   │   ├── monitoring_service.py     # Performance monitoring service
│   │   └── notification_service.py   # Alert and notification service
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logger.py                 # Logging utilities
│   │
│   ├── workers/                      # Background task workers
│   │   ├── __init__.py
│   │   ├── compliance_scanner.py     # Background compliance scanning
│   │   ├── data_collector.py         # Scheduled data collection
│   │   └── report_generator.py       # Automated report generation
│   │
│   └── main.py                       # FastAPI application entry point
│
├── tests/                            # Test scripts
│
├── .env.example                      # Environment variables template
├── pyproject.toml                    # Project dependencies and metadata
├── README.md
└── uv.lock                           # Lock file for reproducible builds
```

## 🧪 Microsoft Graph Sandbox Simulation

This project uses the [Microsoft Graph Sandbox Mocks](https://github.com/pnp/proxy-samples/tree/main/samples/microsoft-graph-sandbox-mocks) to simulate Microsoft Graph API locally for development and testing purposes.

The sandbox provides mock responses for common Microsoft Graph endpoints, allowing you to develop and test your compliance assessment features without requiring a full Microsoft 365 environment.

## 🚀 Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black .
uv run isort .
```

### Type Checking

```bash
uv run mypy app/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b your-name/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`). Please follow [Conventional Commits](https://www.conventionalcommits.org)
4. Push to the branch (`git push origin your-name/amazing-feature`)
5. Open a Pull Request
