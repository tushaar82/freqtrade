# Database Clean Flag - Usage Guide

## ✅ New Feature: `--clean-db` Flag

You now have **full control** over when to clean the database!

---

## 📋 Usage Options

### Option 1: Start WITHOUT Cleaning Database
```bash
./freqtrade.sh run
# OR
./freqtrade.sh restart
```
**Result:** 
- Preserves existing trades
- Keeps trade history
- Maintains current balance

**Use When:**
- Real trading with OpenAlgo/SmartAPI
- You want to preserve trade history
- Continuing from previous session

---

### Option 2: Start WITH Clean Database
```bash
./freqtrade.sh run --clean-db
# OR
./freqtrade.sh restart --clean-db
```
**Result:**
- ✅ Deletes all database files
- ✅ Fresh ₹100,000 balance
- ✅ No old trades

**Use When:**
- Testing with PaperBroker
- Starting fresh strategy tests
- Want clean slate

---

## 🎯 Examples

### Testing Strategy Changes (PaperBroker)
```bash
# Always start fresh for consistent testing
./freqtrade.sh run --clean-db
```

### Real Trading (OpenAlgo/SmartAPI)
```bash
# Preserve trade history
./freqtrade.sh run
# OR restart without losing data
./freqtrade.sh restart
```

### Custom Strategy Testing
```bash
# Test with clean database
./freqtrade.sh run MyCustomStrategy --clean-db

# Test preserving previous results
./freqtrade.sh run MyCustomStrategy
```

---

## 📊 Comparison

| Command | Database Cleaned? | Use Case |
|---------|------------------|----------|
| `./freqtrade.sh run` | ❌ No | Real trading, preserve history |
| `./freqtrade.sh run --clean-db` | ✅ Yes | Fresh start, testing |
| `./freqtrade.sh restart` | ❌ No | Quick restart, keep data |
| `./freqtrade.sh restart --clean-db` | ✅ Yes | Fresh restart |

---

## 🔧 Additional Commands

```bash
# View current status
./freqtrade.sh status

# View live logs
./freqtrade.sh logs

# Stop bot
./freqtrade.sh stop

# Manually clean database (while bot is stopped)
./freqtrade.sh clean-db
```

---

## 💡 Recommended Workflow

### For PaperBroker Testing:
```bash
# Edit your strategy
nano user_data/strategies/NSESampleStrategy.py

# Test with fresh database
./freqtrade.sh run --clean-db

# Watch logs
./freqtrade.sh logs
```

### For Real Trading:
```bash
# Start (keeps previous trades)
./freqtrade.sh run

# Monitor
./freqtrade.sh status

# Restart if needed (preserves data)
./freqtrade.sh restart
```

---

## ⚠️ Important Notes

1. **Data Loss Warning:** `--clean-db` permanently deletes:
   - All trade history
   - All order records
   - Balance resets to initial amount

2. **Cannot Undo:** Once cleaned, data cannot be recovered

3. **Backup Option:** To manually backup before cleaning:
   ```bash
   cp tradesv3.dryrun.sqlite backup_$(date +%Y%m%d_%H%M%S).sqlite
   ```

---

## 🎉 Summary

✅ **Default behavior:** Database is preserved  
✅ **Clean when needed:** Add `--clean-db` flag  
✅ **Flexible:** Works with run and restart  
✅ **Safe:** Won't accidentally delete data

**You're in control!**

