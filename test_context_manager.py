import asyncio
from datetime import datetime
from app.db.session import get_session
from app.services.llm_logging_service import log_llm_call
from app.core.auth import User

class MockUser:
    def __init__(self):
        self.id = "test-user-456"

async def test_context_manager():
    """Test the context manager logging"""
    print("Testing context manager logging...")
    
    async for db in get_session():
        try:
            mock_user = MockUser()
            
            # Test successful operation
            async with log_llm_call(
                db=db,
                user=mock_user,
                endpoint_name="test/context-manager",
                llm_operation_type="test_context_operation",
                request_data={"test": "data"}
            ) as logger:
                # Simulate some work
                await asyncio.sleep(0.1)
                
                # Log success
                await logger.log_success(
                    response_summary="Context manager test successful"
                )
                
                print("✅ Context manager logging completed")
                
            # Check if entry was created
            from sqlalchemy import select
            from app.models.llm_call_log_model import LlmCallLog
            
            result = await db.execute(
                select(LlmCallLog).where(
                    LlmCallLog.user_id == mock_user.id,
                    LlmCallLog.endpoint_name == "test/context-manager"
                )
            )
            log_entry = result.scalar_one_or_none()
            
            if log_entry:
                print(f"✅ Log entry found: Success={log_entry.success}, Duration={log_entry.duration_ms}ms")
            else:
                print("❌ No log entry found")
                
        except Exception as e:
            print(f"❌ Error during context manager test: {e}")
            import traceback
            traceback.print_exc()
        break

if __name__ == "__main__":
    asyncio.run(test_context_manager()) 