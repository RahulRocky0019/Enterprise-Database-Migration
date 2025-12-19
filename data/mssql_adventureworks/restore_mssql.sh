#!/bin/bash
# restore_mssql.sh

# 1. Wait for SQL Server to start
echo "⏳ Waiting for SQL Server to wake up..."
sleep 30

# 2. Run the Restore Command via sqlcmd tool inside the container
# Note: We use the default logical names for AW2019. Adjust if using a different version.
/opt/mssql-tools/bin/sqlcmd \
   -S localhost -U sa -P "StrongPassword123!" \
   -Q "RESTORE DATABASE AdventureWorks FROM DISK = '/var/opt/mssql/backup/AdventureWorks2022.bak' WITH MOVE 'AdventureWorks2022' TO '/var/opt/mssql/data/AdventureWorks.mdf', MOVE 'AdventureWorks2022_log' TO '/var/opt/mssql/data/AdventureWorks_log.ldf', REPLACE"

echo "✅ AdventureWorks Restored Successfully!"