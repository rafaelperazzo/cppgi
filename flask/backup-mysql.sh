mysqldump -u cppgi -pTnd9JpHkJ76qV7 --databases cppgi --single-transaction --quick --lock-tables=false > /home/perazzo/cppgi/backup/db-cppgi-backup-"$(date "+%d-%m-%Y-%H-%M-%S")".sql
tar -cjvf /home/perazzo/cppgi/backup/db-cppgi-backup-"$(date "+%d-%m-%Y-%H-%M-%S")".tar.bz2 /home/perazzo/cppgi/backup/*.sql
rm -f /home/perazzo/cppgi/backup/*.sql
