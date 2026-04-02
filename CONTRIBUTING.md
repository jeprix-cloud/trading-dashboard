# Contributing to TradingCore Dashboard

## Quick Links

1. **For AI Agents (Antigravity, Cline, etc.):** Read `AGENT.md` first
2. **For Human Developers:** Read `docs/SPEC.md` for full specification

---

## For AI Agents

Your primary file is **`AGENT.md`** — it contains step-by-step instructions for building the dashboard.

### To Start Working:

1. Read `AGENT.md` completely
2. Read `docs/SPEC.md` for detailed specifications
3. Read `templates/dashboard.html` to see current state
4. Execute tasks listed in AGENT.md
5. Test locally
6. Commit and push

### Workflow

```
Read AGENT.md
    ↓
Read SPEC.md  
    ↓
Read existing code
    ↓
Implement Task 1 (Dashboard)
    ↓
Implement Task 2 (Static assets)
    ↓
Implement Task 3 (Signal engine)
    ↓
Implement Task 4 (Screener)
    ↓
Add tests
    ↓
Test locally
    ↓
Commit + Push
```

---

## For Human Developers

### Setup Development Environment

```bash
# Clone the repo
git clone git@github.com:jeprix-cloud/trading-dashboard.git
cd trading-dashboard

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# Open browser
# http://localhost:5000
```

### Adding New Features

1. Read `docs/SPEC.md` for context
2. Make changes
3. Test locally
4. Commit with descriptive message
5. Push to your branch

### Frontend Guidelines

**Color Scheme:**
- Background: `#0a0e1a`
- Card bg: `#111827`
- Accent Green: `#00ff9d`
- Accent Red: `#ff4757`
- Accent Yellow: `#ffd700`
- Text: `#e2e8f0`
- Muted: `#64748b`
- Border: `#1e293b`

**API Endpoints:**
```javascript
GET  /api/market/pulse      // F&G, BTC Dom, Trending
GET  /api/signals            // Trading signals
POST /api/bot/start          // Start bot
POST /api/bot/stop           // Stop bot
GET  /api/bot/status         // Bot status
GET  /api/performance        // Win rate, trades
GET  /api/config             // Get config
POST /api/config             // Update config
```

---

## Task List

### Phase 1: Frontend (Priority)
- [x] Flask app setup
- [x] API structure
- [x] Basic dashboard HTML
- [ ] Enhanced dashboard (full spec)
- [ ] Static CSS file
- [ ] JavaScript app logic

### Phase 2: Backend
- [ ] Signal engine (RSI, EMA, ATR)
- [ ] Coin screener
- [ ] Bot start/stop integration
- [x] Market data fetching

### Phase 3: Testing & Polish
- [ ] Unit tests
- [ ] Error handling
- [ ] Loading states
- [ ] Mobile responsive

---

## Communication

- Open issues for bugs
- Open discussions for features
- Commit often with clear messages

---

**Remember:** `docs/SPEC.md` is the source of truth for all specifications.
