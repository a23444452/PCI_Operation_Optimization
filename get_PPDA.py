import sqlalchemy
import pandas as pd
import oracledb

user_account = 'training'
user_password = 'training'
service_name = f"TC_PPDA"

connection_string = f"oracle+oracledb://{user_account}:{user_password}@{service_name}"

# print(connection_string)
engine = sqlalchemy.create_engine(connection_string, thick_mode=True)

# Define your SQL query
query = """
    SELECT
        SAMPLE_TS, BATCH_ID, SHEET_ID
    FROM
        ONEMES.PPT_QC_CRBIS_SUMM
    WHERE
        ROWNUM <= 5
"""

# Execute the query and load the data into a DataFrame
df = pd.read_sql(query, engine)


pd.options.display.max_columns = None # show all columns set

# Display the DataFrame
print(df.head())