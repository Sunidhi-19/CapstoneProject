# Loan Approval System - Capstone Project

A modern, AI-powered loan approval system built with LangGraph, FastAPI, and Streamlit. This system leverages large language models and orchestrated multi-agent workflows to automate and streamline the loan approval process.

## Features

- **AI-Powered Decision Making**: Uses Claude AI models with LangGraph for intelligent loan approval workflows
- **Microservices Architecture**: Modular MCP (Model Context Protocol) servers for scalability
- **Multi-Agent Orchestration**: Distributed processing with specialized agents:
  - Applicant Database (ApplicantDB)
  - Risk Rules Engine (RiskRulesDB)
  - Decision Synthesis
  - Notification System
- **FastAPI Backend**: High-performance REST API gateway
- **Streamlit Frontend**: Interactive user interface for loan applications
- **Production & Development Modes**: Flexible deployment options

## Project Structure

```
├── main.py                    # Entry point for running services
├── frontend.py                # Streamlit web interface
├── gateway.py                 # FastAPI gateway and routing
├── orchestrator.py            # LangGraph workflow orchestration
├── requirements.txt           # Python dependencies
├── src/
│   └── mcps/
│       ├── applicant_db/       # Applicant database MCP
│       ├── risk_rules_db/      # Risk rules MCP
│       ├── notification_system/ # Notification MCP
│       └── decision_synthesis/ # Decision synthesis MCP
└── .env                       # Environment variables
```

## Installation

### Prerequisites
- Python 3.12+
- pip or conda

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CapstoneProject
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Usage

### Development Mode (In-Process MCP)

```bash
# Terminal 1: Start the backend
python main.py backend

# Terminal 2: Start the frontend
python main.py frontend
```

The frontend will be available at `http://localhost:8501`

### Production Mode (Standalone MCP Microservices)

```bash
# Terminal 1: ApplicantDB MCP (port 8001)
python main.py mcp-applicant

# Terminal 2: RiskRulesDB MCP (port 8002)
python main.py mcp-risk

# Terminal 3: DecisionSynthesis MCP (port 8003)
python main.py mcp-decision

# Terminal 4: NotificationSystem MCP (port 8004)
python main.py mcp-notification

# Terminal 5: Backend API (port 8000)
python main.py backend

# Terminal 6: Frontend (port 8501)
python main.py frontend
```

## API Endpoints

### Loan Approval Endpoint
- **POST** `/loan_approval/process`
  - Submits a loan application for processing
  - Returns decision with recommendation

### Status and Health
- **GET** `/health` - System health check
- **GET** `/status` - System status information

## Architecture

### LangGraph Workflow
The system uses LangGraph to orchestrate a multi-state workflow:
1. **Input Validation** - Validate applicant information
2. **Risk Assessment** - Evaluate risk profile
3. **Rule Engine** - Apply business rules
4. **Decision Synthesis** - Generate final decision
5. **Notification** - Send approval/rejection notification

### MCP Servers
- **ApplicantDB**: Manages applicant information and retrieval
- **RiskRulesDB**: Evaluates risk factors and applies rules
- **DecisionSynthesis**: Synthesizes final loan decisions
- **NotificationSystem**: Handles notifications and communications

## Technologies Used

- **Backend Framework**: FastAPI
- **Frontend Framework**: Streamlit
- **Orchestration**: LangGraph
- **AI Models**: Anthropic Claude API
- **Protocol**: Model Context Protocol (MCP)
- **Server**: Uvicorn
- **Data**: Pydantic models

## Configuration

Key configuration options in `src/config.py`:

```python
API_HOST = "127.0.0.1"
API_PORT = 8000
MCP_APPLICANT_DB_PORT = 8001
MCP_RISK_RULES_DB_PORT = 8002
MCP_DECISION_SYNTHESIS_PORT = 8003
MCP_NOTIFICATION_SYSTEM_PORT = 8004
```

## Environment Variables

Configure these in your `.env` file:

```
ANTHROPIC_API_KEY=your_api_key_here
LOG_LEVEL=INFO
DEBUG=False
```

## Testing

Run the evaluation suite:

```bash
python -m pytest tests/
```

Check evaluation reports in:
- `EVALUATION_REPORT_SUNIDHI_KUMARI.md` - Detailed evaluation
- `EVALUATION_SUMMARY_JSON.json` - Summary metrics

## Performance & Evaluation

The system has been evaluated on:
- Decision accuracy and consistency
- Processing time and latency
- System reliability and error handling
- Integration with AI models

See evaluation reports for detailed metrics.

## Development

### Running with Hot Reload

```bash
# Backend with auto-reload
uvicorn gateway:app --reload

# Frontend with auto-reload
streamlit run frontend.py
```

### Logging

Logs are configured in `src/logger.py`. Adjust `LOG_LEVEL` in `.env` to control verbosity.

## Troubleshooting

### Port Already in Use
If a port is already in use, update the corresponding port number in `.env` or `src/config.py`.

### MCP Connection Issues
Ensure all MCP servers are running in production mode. Check logs for connection errors.

### API Timeout
Increase timeout values in gateway configuration if processing takes longer.

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests to ensure nothing breaks
4. Submit a pull request

## License

This project is part of a capstone assignment.

## Contact & Support

For issues or questions, please open an issue on GitHub or contact the development team.

---

**Last Updated**: June 2026
