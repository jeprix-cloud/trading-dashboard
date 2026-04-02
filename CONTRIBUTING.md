# Contributing to TradingCore

## Quick Start for Cursor

1. Baca `docs/SPEC.md` untuk pemahaman lengkap
2. Baca `docs/SPEC.md` section "File Structure"
3. Check API endpoints di SPEC.md
4. Start building sesuai task yang tersedia

## Task List

### Phase 1: Foundation (OpenClaw)
- [x] Flask app setup
- [x] API endpoints structure
- [x] Signal engine pipeline
- [x] Config system
- [ ] Bot start/stop cron integration

### Phase 2: Frontend (Cursor)
- [ ] Dashboard HTML — dark theme sesuai spec
- [ ] Market Pulse panel UI
- [ ] Live Signals cards
- [ ] Bot Controls dropdowns
- [ ] Performance Tracker stats
- [ ] Start/Stop buttons

### Phase 3: Integration
- [ ] Connect dashboard to API endpoints
- [ ] Real-time data fetching
- [ ] Bot control handlers
- [ ] Configuration form submission

### Phase 4: Advanced
- [ ] Performance history chart
- [ ] Backtest interface
- [ ] Lesson system UI
- [ ] Custom strategy builder

## Frontend Instructions

### Dashboard HTML Structure

```html
<!-- Main container - dark theme -->
<div class="dashboard">
  <!-- Header with bot status -->
  <header class="header">
    <span class="status-dot active"></span>
    <span>TradingCore Dashboard</span>
    <button id="stop-btn">■ STOP BOT</button>
  </header>

  <!-- 3-column layout -->
  <div class="panels">
    <div class="panel market-pulse"><!-- Market Pulse --></div>
    <div class="panel live-signals"><!-- Signals cards --></div>
    <div class="panel bot-controls"><!-- Dropdowns --></div>
  </div>

  <!-- Performance tracker footer -->
  <footer class="performance">
    <!-- Stats + buttons -->
  </footer>
</div>
```

### Color Reference
- Background: `#0a0e1a`
- Card bg: `#111827`
- Green: `#00ff9d`
- Red: `#ff4757`
- Yellow: `#ffd700`
- Text: `#e2e8f0`
- Muted: `#64748b`
- Border: `#1e293b`

### API Calls
```javascript
// Fetch market pulse
fetch('/api/market/pulse')

// Fetch signals
fetch('/api/signals')

// Start bot
fetch('/api/bot/start', {method: 'POST'})

// Stop bot
fetch('/api/bot/stop', {method: 'POST'})

// Get config
fetch('/api/config')

// Update config
fetch('/api/config', {method: 'POST', body: {...}})
```

## Backend Instructions

### Adding New Signal Factor

1. Edit `strategies/signal_engine.py`
2. Add calculation in `analyze_coin()`
3. Add factor to confidence scoring
4. Update API response if needed

### Adding New Parameter

1. Edit `config/bot_config.json`
2. Add parameter with default value
3. Update `routes/config.py` to handle
4. Update frontend dropdown options

## Communication

- Commit often — push to GitHub
- Add meaningful commit messages
- Update this file when task completed

## Questions?

Baca SPEC.md dulu. Kalau masih bingung, add comment di code.
