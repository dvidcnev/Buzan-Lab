"""
Migration script to swap specimen_id and tube_id columns
This fixes the critical issue where the columns were named backwards.

BEFORE:
- tube_or_well_id = Specimen ID (LME####)
- specimen_id = Tube ID (LME####-##)

AFTER:
- specimen_id = Specimen ID (LME####)
- tube_id = Tube ID (LME####-##)
"""
import asyncio
import asyncpg
from db_config import DATABASE_URL

async def migrate():
    # Convert SQLAlchemy URL to asyncpg format
    asyncpg_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(asyncpg_url)
    
    try:
        print("Starting column swap migration...")
        
        # Check if columns already swapped
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'storage' AND column_name IN ('tube_or_well_id', 'specimen_id', 'tube_id');
        """
        existing_columns = await conn.fetch(check_query)
        column_names = [row['column_name'] for row in existing_columns]
        
        print(f"Current columns: {column_names}")
        
        if 'tube_id' in column_names and 'tube_or_well_id' not in column_names:
            print("✓ Columns already swapped. Migration not needed.")
            return
        
        # Step 1: Rename tube_or_well_id to specimen_id and specimen_id to tube_id
        print("\n1. Renaming columns in storage table...")
        await conn.execute("ALTER TABLE storage RENAME COLUMN tube_or_well_id TO specimen_id_new;")
        await conn.execute("ALTER TABLE storage RENAME COLUMN specimen_id TO tube_id;")
        await conn.execute("ALTER TABLE storage RENAME COLUMN specimen_id_new TO specimen_id;")
        print("✓ Storage table columns renamed")
        
        # Step 2: Do the same for audit_logs table
        print("\n2. Renaming columns in audit_logs table...")
        audit_columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'audit_logs' AND column_name IN ('tube_or_well_id', 'specimen_id', 'tube_id');
        """)
        audit_column_names = [row['column_name'] for row in audit_columns]
        
        if 'tube_or_well_id' in audit_column_names:
            await conn.execute("ALTER TABLE audit_logs RENAME COLUMN tube_or_well_id TO specimen_id_new;")
            if 'specimen_id' in audit_column_names:
                await conn.execute("ALTER TABLE audit_logs RENAME COLUMN specimen_id TO tube_id;")
            await conn.execute("ALTER TABLE audit_logs RENAME COLUMN specimen_id_new TO specimen_id;")
            print("✓ Audit_logs table columns renamed")
        else:
            print("✓ Audit_logs already has correct column names")
        
        # Step 3: Update indexes
        print("\n3. Recreating indexes...")
        await conn.execute("DROP INDEX IF EXISTS ix_storage_tube_or_well_id;")
        await conn.execute("DROP INDEX IF EXISTS ix_storage_specimen_id;")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_storage_specimen_id ON storage(specimen_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_storage_tube_id ON storage(tube_id);")
        print("✓ Indexes recreated")
        
        # Step 4: Update unique constraint
        print("\n4. Updating unique constraint...")
        await conn.execute("ALTER TABLE storage DROP CONSTRAINT IF EXISTS storage_tube_or_well_id_key;")
        await conn.execute("ALTER TABLE storage DROP CONSTRAINT IF EXISTS storage_specimen_id_key;")
        await conn.execute("ALTER TABLE storage ADD CONSTRAINT storage_specimen_id_key UNIQUE (specimen_id);")
        print("✓ Unique constraint updated")
        
        print("\n✅ Migration completed successfully!")
        print("\nSummary:")
        print("  - specimen_id now contains LME#### (Specimen ID)")
        print("  - tube_id now contains LME####-## (Tube ID)")
        print("\nPlease restart your backend server for changes to take effect.")
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("COLUMN SWAP MIGRATION")
    print("=" * 60)
    asyncio.run(migrate())
