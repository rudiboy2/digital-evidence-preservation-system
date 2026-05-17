import asyncio, sys
sys.path.insert(0, '/app/backend')
from core.infrastructure.database import AsyncSessionLocal, engine, Base
from core.infrastructure.database.models.role import Role, DEFAULT_ROLES
from sqlalchemy import select

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        for r in DEFAULT_ROLES:
            res = await db.execute(select(Role).where(Role.name == r['name']))
            if not res.scalar_one_or_none():
                db.add(Role(**r))
        await db.commit()
        print('Roles seeded successfully')

asyncio.run(seed())
