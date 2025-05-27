#!/usr/bin/env python3

import asyncio
from app.db.session import get_session
from app.models.user_activity_log_model import UserActivityLog
from sqlmodel import select

async def check_logs():
    async for db in get_session():
        try:
            result = await db.exec(select(UserActivityLog).order_by(UserActivityLog.timestamp.desc()).limit(5))
            logs = result.all()
            print(f'Found {len(logs)} recent activity logs:')
            for log in logs:
                print(f'- ID: {log.id}, Action: {log.action_type}, Time: {log.timestamp}, User: {log.user_id_hash[:10]}...')
            break
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
            break

if __name__ == "__main__":
    asyncio.run(check_logs()) 