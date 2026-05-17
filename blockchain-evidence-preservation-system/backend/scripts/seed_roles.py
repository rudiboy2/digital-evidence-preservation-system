import asyncio
from sqlalchemy import select

from core.infrastructure.database import AsyncSessionLocal, engine, Base
from core.infrastructure.database.models.role import Role, DEFAULT_ROLES


async def seed_roles():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        for role_data in DEFAULT_ROLES:
            result = await db.execute(
                select(Role).where(Role.name == role_data["name"])
            )

            existing_role = result.scalar_one_or_none()

            if not existing_role:
                db.add(Role(**role_data))

        await db.commit()
        print("✅ Roles seeded successfully")


if __name__ == "__main__":
    asyncio.run(seed_roles())