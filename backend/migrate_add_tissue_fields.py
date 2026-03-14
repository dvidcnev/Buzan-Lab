"""
Migration script to add tissue_type and tissue_subtype columns to storage table
Run this once to update your existing database schema
"""
import asyncio
import asyncpg
from db_config import DATABASE_URL

async def migrate():
    # Convert SQLAlchemy URL to asyncpg format
    # From: postgresql+asyncpg://user:pass@host:port/db
    # To: postgresql://user:pass@host:port/db
    asyncpg_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(asyncpg_url)
    
    try:
        # Check if columns already exist
        check_tissue_type = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'storage' AND column_name = 'tissue_type'
            );
        """)
        
        check_tissue_subtype = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'storage' AND column_name = 'tissue_subtype'
            );
        """)
        
        # Add tissue_type column if it doesn't exist
        if not check_tissue_type:
            print("Adding tissue_type column...")
            await conn.execute("""
                ALTER TABLE storage 
                ADD COLUMN tissue_type VARCHAR(100);
            """)
            print("✓ tissue_type column added successfully")
        else:
            print("✓ tissue_type column already exists")
        
        # Add tissue_subtype column if it doesn't exist
        if not check_tissue_subtype:
            print("Adding tissue_subtype column...")
            await conn.execute("""
                ALTER TABLE storage 
                ADD COLUMN tissue_subtype VARCHAR(255);
            """)
            print("✓ tissue_subtype column added successfully")
        else:
            print("✓ tissue_subtype column already exists")
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    print("Starting migration to add tissue fields...")
    asyncio.run(migrate())
