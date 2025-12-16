from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from auth_models import User
from config import get_password_hash

async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def create_default_users(db: AsyncSession):
    """Create default admin and viewer users if they don't exist"""
    from auth_models import RoleEnum
    
    # Check if admin user exists
    admin = await get_user_by_username(db, "admin")
    if not admin:
        admin_user = User(
            username="admin",
            email="admin@buzanlab.local",
            hashed_password=get_password_hash("admin123"),
            role=RoleEnum.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        await db.commit()
        print("Admin user created: username=admin, password=admin123")
    
    # Check if viewer user exists
    viewer = await get_user_by_username(db, "viewer")
    if not viewer:
        viewer_user = User(
            username="viewer",
            email="viewer@buzanlab.local",
            hashed_password=get_password_hash("viewer123"),
            role=RoleEnum.VIEWER,
            is_active=True
        )
        db.add(viewer_user)
        await db.commit()
        print("Viewer user created: username=viewer, password=viewer123")
    
    # Check if editor user exists
    editor = await get_user_by_username(db, "editor")
    if not editor:
        editor_user = User(
            username="editor",
            email="editor@buzanlab.local",
            hashed_password=get_password_hash("editor123"),
            role=RoleEnum.EDITOR,
            is_active=True
        )
        db.add(editor_user)
        await db.commit()
        print("Editor user created: username=editor, password=editor123")
