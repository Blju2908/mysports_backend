import asyncio
from datetime import datetime
from app.db.session import get_session
from app.models.llm_call_log_model import LlmCallLog

async def test_manual_logging():
    """Test manual creation of a log entry"""
    print("Testing manual LLM logging...")
    
    async for db in get_session():
        try:
            # Create a test log entry
            test_log = LlmCallLog(
                user_id="test-user-123",
                endpoint_name="test/endpoint",
                method="POST",
                timestamp=datetime.utcnow(),
                success=True,
                http_status_code=200,
                duration_ms=1500,
                llm_operation_type="test_operation",
                response_summary="Manual test successful"
            )
            
            db.add(test_log)
            await db.commit()
            await db.refresh(test_log)
            
            print(f"✅ Manual log entry created successfully with ID: {test_log.id}")
            
            # Query it back
            from sqlalchemy import select
            result = await db.execute(select(LlmCallLog).where(LlmCallLog.id == test_log.id))
            retrieved_log = result.scalar_one_or_none()
            
            if retrieved_log:
                print(f"✅ Log entry retrieved successfully: {retrieved_log.endpoint_name}")
            else:
                print("❌ Could not retrieve the log entry")
                
        except Exception as e:
            print(f"❌ Error during manual logging test: {e}")
            await db.rollback()
        break

if __name__ == "__main__":
    asyncio.run(test_manual_logging()) 