# import asyncio
# import os
# from datetime import datetime
# from sqlalchemy.future import select
# from ..database import AsyncSessionLocal
# from .. import models
# from pathlib import Path

# REPORT_DIR = "reports"
# os.makedirs(REPORT_DIR, exist_ok=True)


# async def cleanup_expired_reports():
#     """Background async task to delete expired reports."""
#     while True:
#         try:
#             async with AsyncSessionLocal() as session:
#                 result = await session.execute(
#                     select(models.Report).where(models.Report.expires_at < datetime.now(),
#                                                 models.Report.is_deleted == False)
#                 )
#                 expired_reports = result.scalars().all()
#                 for report in expired_reports:
#                     file = Path(report.file_path)
                    

#                     try:
#                         # ✅ Attempt file deletion first
#                         if file.exists() and file.is_file():
#                             file.unlink(missing_ok=True)
#                             print(f"Deleted expired file: {file}")
                           
                             
#                         else:
#                             print(f"File not found (already deleted?): {file}")

#                     except Exception as e:
#                         # ❌ Log the error but don’t stop the loop
#                         print(f"Error deleting file {file}: {e}")
                    
#                     # Soft delete the db record
#                     try:
#                          # ✅ Mark report as deleted in DB
#                         report.is_deleted = True
#                         report.deleted_at = datetime.now()
#                         print(f"Soft deleted DB record for report {report.id}")
#                     except Exception as e:
#                         print(f"Error updating DB record for report {report.id}: {e}")

               


#                 # Commit once at the end
#                 try:
#                     await session.commit()
#                     print("Expired report cleanup committed successfully.")
#                 except Exception as e:
#                     print(f"Error committing DB deletions: {e}")

                

#         except Exception as e:
#             print(f"[Cleanup Error] {e}")

#         # wait 60 seconds before next cleanup cycle
#         await asyncio.sleep(60)


# def register_cleanup(app):
#     """Register cleanup task with FastAPI app."""
#     @app.on_event("startup")
#     async def start_cleanup_task():
#         asyncio.create_task(cleanup_expired_reports())

import asyncio
import os
from datetime import datetime
from sqlalchemy.future import select
from ..database import AsyncSessionLocal, engine
from .. import models
from pathlib import Path

REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)

# Keep track of the cleanup task so we can cancel it
cleanup_task = None


async def cleanup_expired_reports():
    """Background async task to delete expired reports."""
    while True:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(models.Report).where(
                        models.Report.expires_at < datetime.now(),
                        models.Report.is_deleted == False
                    )
                )
                expired_reports = result.scalars().all()
                for report in expired_reports:
                    file = Path(report.file_path)

                    try:
                        if file.exists() and file.is_file():
                            file.unlink(missing_ok=True)
                            print(f"Deleted expired file: {file}")
                        else:
                            print(f"File not found (already deleted?): {file}")
                    except Exception as e:
                        print(f"Error deleting file {file}: {e}")

                    try:
                        report.is_deleted = True
                        report.deleted_at = datetime.now()
                        print(f"Soft deleted DB record for report {report.id}")
                    except Exception as e:
                        print(f"Error updating DB record for report {report.id}: {e}")

                try:
                    await session.commit()
                    print("Expired report cleanup committed successfully.")
                except Exception as e:
                    print(f"Error committing DB deletions: {e}")

        except asyncio.CancelledError:
            print("⚠️ Cleanup task cancelled.")
            break  # Exit cleanly if shutdown requested
        except Exception as e:
            print(f"[Cleanup Error] {e}")

        await asyncio.sleep(60)


def register_cleanup(app):
    """Register cleanup task with FastAPI app."""
    @app.on_event("startup")
    async def start_cleanup_task():
        global cleanup_task
        cleanup_task = asyncio.create_task(cleanup_expired_reports())

    @app.on_event("shutdown")
    async def stop_cleanup_task():
        global cleanup_task
        if cleanup_task:
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                print("Cleanup task stopped successfully.")
        await engine.dispose()  # ✅ close DB connections
