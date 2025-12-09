import pandas as pd
from sqlalchemy import create_engine

# Define connection strings for both databases (PostgreSQL)
source_db = 'postgresql+psycopg2://postgres:root@localhost/motohub_db'
target_db = 'postgresql+psycopg2://postgres:root@localhost/motohubcopy_db'

# Create engines for source and target PostgreSQL databases
source_engine = create_engine(source_db)
target_engine = create_engine(target_db)

# Define the table name to copy
table_name = 'svc_item'

# Read the data from the source PostgreSQL database
df = pd.read_sql_table(table_name, source_engine)

# Write the data into the target PostgreSQL database
df.to_sql(table_name, target_engine, if_exists='append', index=False)

print(f"Data copied from {source_db} to {target_db} for table {table_name}")
