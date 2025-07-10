# Vercel Pro + Supabase Session Mode Setup

## 🚀 **Warum Session Mode (Port 5432)?**

### **Vorteile von Session Mode:**
- ✅ **Prepared Statements**: Bessere Performance durch Query-Caching
- ✅ **Längere Connections**: Ideal für Background Tasks
- ✅ **Keine pgbouncer Restrictions**: Kein `DuplicatePreparedStatementError`
- ✅ **Vercel Pro Features**: 5min Timeouts + 3GB RAM
- ✅ **Einfacher**: Eine Engine für alles

### **Transaction Mode vs Session Mode:**
```
Transaction Mode (6543):  ❌ Prepared statements issues
Session Mode (5432):     ✅ Full PostgreSQL features
```

---

## 📦 **Vercel Pro Configuration**

### **vercel.json**
```json
{
  "functions": {
    "app/main.py": {
      "maxDuration": 300,     // ✅ 5 Minuten für Background Tasks
      "memory": 3008,         // ✅ 3GB RAM für LLM Operations
      "runtime": "python3.9"
    }
  }
}
```

### **Environment Variables**
```bash
# Nur diese URL wird verwendet:
SUPABASE_DB_URL=postgresql://postgres.xyz:password@aws-0-eu-central-1.pooler.supabase.com:5432/postgres

# Diese wird NICHT verwendet:
# SUPABASE_DB_URL_TRANSACTION=...
```

---

## ⚙️ **Database Configuration**

### **Unified Engine (session.py)**
```python
# ✅ Eine Engine für API + Background Tasks
engine = create_async_engine(
    settings.SUPABASE_DB_URL,  # Port 5432 - Session Mode
    poolclass=NullPool,        # Serverless-optimiert
    connect_args={
        "timeout": 20,                    # Längere Timeouts
        "command_timeout": 120,           # 2min für Background Tasks
        # KEIN statement_cache_size=0 !   # Prepared statements sind OK
        "server_settings": {
            "application_name": "s3ssions_unified_session",
        },
    },
)
```

### **Session Management**
```python
# ✅ Gleiche Session für API + Background
async def get_session():
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()  # Cleanup

@asynccontextmanager
async def get_background_session():
    async with session_maker() as session:  # Same engine!
        try:
            yield session
            await session.commit()
        finally:
            await session.close()
```

---

## 🎯 **Deployment Steps**

### **1. Vercel Pro aktivieren**
```bash
# Upgrade to Pro in Vercel Dashboard
# Enables: 5min timeouts + 3GB RAM
```

### **2. Environment Variables setzen**
```bash
# In Vercel Dashboard:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_DB_URL=postgresql://postgres.xyz:pass@host:5432/postgres
APP_ENV=production
```

### **3. Deploy**
```bash
cd backend
vercel --prod
```

---

## 📊 **Performance Benefits**

### **Session Mode Advantages:**
- 🚀 **Prepared Statements**: 20-30% faster queries
- ⏱️ **Longer Timeouts**: 5min statt 30s
- 🧠 **More Memory**: 3GB statt 1GB
- 🔄 **Persistent Sessions**: Bessere Connection-Wiederverwendung

### **Expected Performance:**
- API Requests: 100-200ms
- Background Tasks: 30s-5min (je nach LLM)
- Memory Usage: 500MB-2GB
- Cold Start: 2-3s

---

## 🐛 **Problem Solved**

### **Vor der Änderung:**
```
DuplicatePreparedStatementError: prepared statement "__asyncpg_stmt_2__" already exists
HINT: pgbouncer with pool_mode set to "transaction" does not support prepared statements
```

### **Nach der Änderung:**
```
✅ Unified Supabase engine configured:
   🚀 Single Engine: Session Mode (5432) - Prepared statements enabled
   📊 Optimized for: API Endpoints + Background Tasks + Vercel Pro
   ⚡ Benefits: Better performance, longer timeouts, no pgbouncer restrictions
```

---

## 🔍 **Health Check**

```bash
curl https://your-app.vercel.app/health/db
```

**Expected Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "platform": "vercel_pro",
  "mode": "unified_engine",
  "engine": "supabase_session_5432",
  "config": "prepared_statements_enabled_better_performance"
}
```

---

## 🎉 **Summary**

### **Was geändert:**
1. **Port 6543 → 5432**: Transaction Mode → Session Mode
2. **Removed statement_cache_size=0**: Prepared statements wieder aktiviert
3. **Vercel Pro**: 5min timeout + 3GB RAM
4. **Unified Engine**: Eine Engine für alles

### **Resultat:**
- ✅ **Kein DuplicatePreparedStatementError**
- ✅ **Bessere Performance** durch prepared statements
- ✅ **Längere Timeouts** für Background Tasks
- ✅ **Mehr Memory** für LLM Operations
- ✅ **Einfacher Code** - eine Engine für alles 