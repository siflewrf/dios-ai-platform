# DIOS – Decision Intelligence Operating System

A production-ready enterprise decision engine that converts operational situations into immediate, executable decisions.

## 🧠 What is DIOS?

DIOS is **not a chatbot**. It's an internal enterprise decision-making platform that:

- Accepts operational situations
- Generates structured, SOP-aligned decisions
- Provides step-by-step execution plans
- Identifies risks and fallback strategies
- Stores all decisions for learning and improvement
- Reduces decision time from minutes to seconds

## 🏗️ Architecture

```
dios-ai-platform/
├── app.py              # Flask application (REST API + UI)
├── ai_engine.py        # OpenRouter API client + decision parser
├── database.py         # SQLite decision storage
├── config.py           # Environment configuration
├── logger.py           # Structured logging
├── prompt.py           # DIOS system prompt
├── requirements.txt    # Python dependencies
├── templates/index.html    # Web UI
└── static/style.css    # Enterprise styling
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:

```
OPENROUTER_API_KEY=your_key_here
```

### 3. Run the Application

```bash
python app.py
```

Access the UI at: **http://localhost:5000**

## 📤 API Endpoints

### Generate Decision

**POST** `/api/decision`

```json
{
  "situation": "Customer support team overwhelmed, response time exceeding SLA",
  "sop": "Maximum 4 hour response time for urgent tickets"
}
```

**Response:**

```json
{
  "success": true,
  "decision_id": 1,
  "data": {
    "core_problem": "Support team unable to meet SLA commitments",
    "decision": "Activate overflow support protocol and redirect non-urgent tickets to knowledge base",
    "steps": [
      "Step 1: Activate overflow team immediately",
      "Step 2: Route new tickets to knowledge base first",
      "Step 3: Notify customer of estimated response time",
      "Step 4: Confirm all urgent tickets resolved within SLA"
    ],
    "risks": [
      "Customer dissatisfaction if SLA still breached",
      "Knowledge base might not resolve issues fully",
      "Overflow team cost impact"
    ],
    "fallback": "Temporarily close intake and focus on existing queue",
    "confidence": 85
  }
}
```

### Get Decision History

**GET** `/api/history?limit=10`

Returns the 10 most recent decisions.

### Get Specific Decision

**GET** `/api/decision/1`

Returns decision with ID=1 and full details.

### Get Statistics

**GET** `/api/stats`

Returns aggregate statistics:

```json
{
  "success": true,
  "data": {
    "total_decisions": 42,
    "avg_confidence": 82.5,
    "min_confidence": 65,
    "max_confidence": 95
  }
}
```

## 🗄️ Database

Decisions are stored in SQLite (`decisions.db`) with the following schema:

```sql
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    situation TEXT NOT NULL,
    sop TEXT,
    output_json TEXT NOT NULL,
    core_problem TEXT,
    decision TEXT,
    confidence INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Database Functions

- `save_decision(situation, output_json, sop)` - Store a decision
- `get_decision(id)` - Retrieve a specific decision
- `get_recent_decisions(limit=10)` - Get recent decisions
- `get_decisions_by_confidence(min, max, limit)` - Filter by confidence
- `get_statistics()` - Aggregate stats
- `delete_old_decisions(days=30)` - Cleanup old records

## 🔑 Configuration

Edit `.env` to customize:

```bash
# API Configuration
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=openai/gpt-4o-mini  # Can change model

# Request Configuration
REQUEST_TIMEOUT=30          # Timeout in seconds
MAX_RETRIES=3              # Retry attempts on failure
RETRY_DELAY=2              # Delay between retries

# Environment
ENVIRONMENT=production     # development or production
LOG_LEVEL=INFO             # DEBUG, INFO, WARNING, ERROR
```

## 🛡️ Error Handling

The API client includes production-ready error handling:

- **Timeouts**: Automatic retries with exponential backoff
- **Rate Limiting (429)**: Backs off and retries
- **Server Errors (5xx)**: Automatic retry
- **Authentication (401)**: Fails immediately with clear error
- **Network Errors**: Connection retry with delay

## 📊 Output Format

Every decision follows the DIOS structure:

```json
{
  "core_problem": "1-sentence business problem",
  "decision": "Single executable instruction",
  "steps": ["Step 1", "Step 2", ...],
  "risks": ["Risk 1", "Risk 2", "Risk 3"],
  "fallback": "Emergency action if execution fails",
  "confidence": 75
}
```

## 🧪 Testing

### Web UI

Go to http://localhost:5000 and enter an operational situation.

### API Test

```bash
curl -X POST http://localhost:5000/api/decision \
  -H "Content-Type: application/json" \
  -d '{
    "situation": "Database connection pool exhausted",
    "sop": "Maximum 100 concurrent connections"
  }'
```

## 🚢 Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker

```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 📝 Logging

All events are logged with timestamps:

```
[INFO] 2025-01-14 14:32:15 - DIOS - Starting decision generation
[INFO] 2025-01-14 14:32:15 - DIOS - API call attempt 1/3
[INFO] 2025-01-14 14:32:18 - DIOS - API call successful
[INFO] 2025-01-14 14:32:18 - DIOS - Parsing LLM response to JSON
[INFO] 2025-01-14 14:32:18 - DIOS - Parsing successful - Confidence: 85%
[INFO] 2025-01-14 14:32:18 - DIOS - Decision saved - ID: 42, Confidence: 85%
```

## 🧠 System Intelligence

Over time, DIOS builds a decision memory:

- Identifies recurring decision patterns
- Learns from high-confidence decisions
- Detects missing SOP rules
- Tracks decision outcomes
- Improves recommendation accuracy

## 📜 License

Proprietary Enterprise Software

## 📧 Support

For issues or questions, contact the DIOS development team.
