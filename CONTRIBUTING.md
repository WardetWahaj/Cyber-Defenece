# Contributing to Cyber Defence

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/Cyber-Defence.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Install dependencies:
   - Backend: `pip install -r requirements.txt`
   - Frontend: `cd frontend && npm install`

## Development Setup

1. Copy `.env.example` to `.env` and fill in your values
2. Start the backend: `uvicorn frontend.backend.api:app --reload`
3. Start the frontend: `cd frontend && npm run dev`
4. Or use Docker: `docker-compose up`

## Code Standards

- **Python**: Follow PEP 8. Run `ruff check` before committing.
- **JavaScript/React**: Run `npm run lint` in the frontend directory.
- **Commits**: Use conventional commit messages (e.g., `feat:`, `fix:`, `chore:`)
- **Tests**: Add tests for new features. Run `pytest tests/` for backend.

## Pull Request Process

1. Update documentation if you change any API endpoints
2. Make sure CI passes (linting + frontend build + tests)
3. Request review from a maintainer

## Reporting Issues

Open a GitHub Issue with:
- Description of the bug or feature request
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Screenshots if applicable
