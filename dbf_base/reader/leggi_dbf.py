from dbfread import DBF
import os

dbf_root_path = '.'
table = 'ARTICO.dbf'
filename = os.path.join(dbf_root_path, table)

# Read parameter:    
dbf_ignorecase = True
dbf_memofile = False
dbf_encoding = 'LATIN'

db = DBF(
    filename, 
    ignorecase=dbf_ignorecase,
    ignore_missing_memofile=dbf_memofile,
    encoding=dbf_encoding,
    )
    
for record in db:
    print record



