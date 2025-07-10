# Vercel Serverless Deployment für S3SSIONS API

## 🚀 **Vercel + FastAPI + Supabase Setup**

### **Architektur**
- ✅ **FastAPI Backend** als Vercel Serverless Functions
- ✅ **Supabase PostgreSQL** mit pgbouncer Transaction Mode (Port 6543)
- ✅ **Unified Engine**: Eine einfache Engine für API + Background Tasks
- ✅ **Optimiert für AWS Lambda** (Vercel's Infrastructure)
- ✅ **statement_cache_size=0**: Löst DuplicatePreparedStatementError

---

## 📦 **Deployment Commands**

### **1. Lokaler Test**
```bash
cd backend
make run-prod
```

### **2. Vercel Deploy**
```bash
# Development
vercel

# Production
vercel --prod
```

### **3. Environment Variables**
Setze diese in Vercel Dashboard:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_DB_URL=postgresql://user:pass@host:5432/db
SUPABASE_DB_URL_TRANSACTION=postgresql://user:pass@host:6543/db
APP_ENV=production

# ⚠️ WICHTIG: Nur SUPABASE_DB_URL_TRANSACTION wird verwendet (Port 6543)
```

---

## ⚙️ **Serverless Optimierungen**

### **Database Engine**
```python
# ✅ Unified Engine für API + Background Tasks
engine = create_async_engine(
    settings.SUPABASE_DB_URL_TRANSACTION,  # Port 6543 - Transaction Mode
    poolclass=NullPool,                    # Keine Connection Pools für Serverless
    connect_args={
        "statement_cache_size": 0,         # CRITICAL: Löst DuplicatePreparedStatementError
        "timeout": 15,                     # Sufficient für alle Operations
        "command_timeout": 60,             # Moderate timeout für API + Background
        "server_settings": {
            "application_name": "s3ssions_unified",
        },
    },
)
```

### **Session Management**
```python
# ✅ Explicit cleanup für Lambda Memory
async def get_session():
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()  # Memory cleanup
```

### **Lifespan Management**
```python
# ✅ Non-blocking startup - keine Crashes bei DB-Fehlern
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Test DB connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        # Log but don't crash - Vercel kann trotzdem starten
        logger.error(f"DB test failed: {e}")
    
    yield
    await close_engine()
```

---

## 🔧 **Vercel Configuration**

### **vercel.json**
```json
{
  "functions": {
    "app/main.py": {
      "maxDuration": 30,
      "memory": 1024,
      "runtime": "python3.9"
    }
  }
}
```

### **Performance Limits**
- ✅ **Max Duration**: 30s (Vercel Pro)
- ✅ **Memory**: 1024MB
- ✅ **Cold Start**: ~2-3s
- ✅ **Warm Requests**: ~100-200ms

---

## 🐛 **Troubleshooting**

### **DuplicatePreparedStatementError**
```bash
# ✅ GELÖST: statement_cache_size=0 in connect_args
# pgbouncer Transaction Mode kompatibel
```

### **Lambda Timeouts**
```bash
# ✅ OPTIMIERT: 
# - NullPool (keine persistent connections)
# - Kurze Timeouts (10s connection, 30s command)
# - Explicit session cleanup
```

### **Memory Issues**
```bash
# ✅ OPTIMIERT:
# - autoflush=False (manuelle Kontrolle)
# - Explicit session.close()
# - 1024MB Lambda Memory
```

---

## 📊 **Health Checks**

### **Basic Health**
```bash
curl https://your-app.vercel.app/health
```

### **Database Health**
```bash
curl https://your-app.vercel.app/health/db
```

**Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "platform": "vercel_serverless",
  "mode": "unified_engine",
  "engine": "supabase_transaction_6543",
  "config": "statement_cache_size_0_pgbouncer_optimized"
}
```

---

## 🎯 **Best Practices**

### **✅ DO**
- NullPool für Serverless
- statement_cache_size=0 für pgbouncer
- Explicit session cleanup
- Non-blocking startup
- Kurze Timeouts
- Error logging ohne Crashes

### **❌ DON'T**
- Connection Pools in Serverless
- Prepared statements mit pgbouncer Transaction Mode
- Blocking startup bei DB-Fehlern
- Lange Query Timeouts
- Memory Leaks durch fehlende session.close()

---

## 🚀 **Performance Monitoring**

Nutze Vercel Analytics:
- Function Duration
- Memory Usage
- Cold Start Frequency
- Error Rates

**Ideal Metrics:**
- Cold Start: <3s
- Warm Request: <200ms
- Memory: <50% (512MB used von 1024MB)
- Error Rate: <1% 