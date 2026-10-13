# PowerShell script to backup the BioForge MySQL database and restore for verification
# Adjust paths if MySQL is installed elsewhere
$mysqlPath = "C:\Program Files\MySQL\MySQL Server 8.4\bin"
$mysqldump = Join-Path $mysqlPath "mysqldump.exe"
$mysql = Join-Path $mysqlPath "mysql.exe"
$backupFile = "C:\BioForge\scripts\bioforge_backup.sql"
$restoreDb = "bioforge_restore"

# ---- Backup ----
Write-Host "Backing up database 'bioforge' to $backupFile ..."
& $mysqldump -uroot -p1234 --single-transaction --routines --triggers --databases bioforge > $backupFile
if ($LASTEXITCODE -ne 0) { Write-Error "mysqldump failed"; exit 1 }
Write-Host "Backup completed."

# ---- Restore into a fresh database ----
Write-Host "Creating restore database $restoreDb ..."
& $mysql -uroot -p1234 -e "DROP DATABASE IF EXISTS $restoreDb; CREATE DATABASE $restoreDb;"
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to create restore database"; exit 1 }

Write-Host "Restoring backup into $restoreDb ..."
& $mysql -uroot -p1234 $restoreDb < $backupFile
if ($LASTEXITCODE -ne 0) { Write-Error "Restore failed"; exit 1 }
Write-Host "Restore completed."

# ---- Verification: compare row counts ----
$tables = @('hospital','antibiotic','strain','mutation','strain_mutation','treatment','outcome','resistance_phenotype','mutation_antibiotic_assoc','audit_log')
Write-Host "\nRow count comparison between original and restored database:"
foreach ($t in $tables) {
    $orig = & $mysql -uroot -p1234 -Nse "SELECT COUNT(*) FROM bioforge.$t;"
    $rest = & $mysql -uroot -p1234 -Nse "SELECT COUNT(*) FROM $restoreDb.$t;"
    Write-Host "{0}: original={1}, restored={2}, match={3}" -f $t,$orig,$rest,($orig -eq $rest)
}

Write-Host "Verification complete."
