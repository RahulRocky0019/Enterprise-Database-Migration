#!/bin/bash
# restore_mssql.sh
# docker exec migration_source_mssql bash /var/opt/mssql/backup/restore_mssql.sh

# 1. Wait for SQL Server to start
echo "⏳ Waiting for SQL Server to wake up..."
sleep 15

# 2. RUN RESTORE
# Note: Updated path to /opt/mssql-tools18/bin/sqlcmd
# Added -C flag to trust the server certificate (Required for Tools v18)
/opt/mssql-tools18/bin/sqlcmd \
   -S localhost -U sa -P "StrongPassword123!" \
   -C \
   -b -r 1 \
   -Q "RESTORE DATABASE AdventureWorks FROM DISK = '/var/opt/mssql/backup/AdventureWorks2022.bak' WITH MOVE 'AdventureWorks2022' TO '/var/opt/mssql/data/AdventureWorks.mdf', MOVE 'AdventureWorks2022_log' TO '/var/opt/mssql/data/AdventureWorks_log.ldf', REPLACE, STATS=5"

if [ $? -eq 0 ]; then
    echo "✅ AdventureWorks Restored Successfully!"
else
    echo "❌ Restore Failed! Check the error message above."
    # Inspection command also needs the new path and -C flag
    echo "🔍 Inspecting Backup File Contents:"
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "StrongPassword123!" -C -Q "RESTORE FILELISTONLY FROM DISK = '/var/opt/mssql/backup/AdventureWorks2022.bak'"
fi