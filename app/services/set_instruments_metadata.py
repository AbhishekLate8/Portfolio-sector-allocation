# upstox_basic_fetch.py
from upstox_client import Configuration, ApiClient
import requests
import gzip
import json
import pandas as pd
from io import BytesIO
from tabulate import tabulate
from .. import models,schemas
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from sqlalchemy import text
from .. config import BASE_URL
import re



async def set_instruments_metadata(db: AsyncSession):
   
    # ✅ Check if any row exists
    result = await db.execute(select(models.Instruments))
    existing_instrument = result.fetchone()
    if existing_instrument:
        print("✅ Instrument metadata already exists in DB. Skipping insert.")
        return
    csv_file_path = BASE_URL / "data/Equity.csv"
    df = pd.read_csv(csv_file_path)
    # display(df)
    # display(df.info())

    cols_to_convert = df.columns.difference(['Security Code','Face Value'])
    print((cols_to_convert))

    df[cols_to_convert] = df[cols_to_convert].astype("string[python]")
    # display(df.info())
    # df

    # df_clean_check = df.replace('',pd.NA)
    # blank_rows = df_clean_check[df_clean_check.isna().any(axis=1)]
    # display(blank_rows)

    # Step 1: Define "bad values" that should be treated as null
    null_like_values = ['-','--','N/A','n/a','null','NULL','',' ']

    #step 2: replace them with actual nulls in the entire dataframe
    df = df.replace(null_like_values, pd.NA)

    # Step 3: Now, to view rows where there are blank rows
    # blank_rows = df[df.isna().any(axis=1)]
    # blank_rows
    # df


    # df = df[df['ISIN No'].notna()]
    # df

    # df.columns

    # import pandas as pd
    # import re

    def to_snake_case(name):
        # Replace spaces with underscores, lowercase everything, and remove non-alphanumeric characters
        name = re.sub(r'[^\w\s]', '', name)         # Remove special chars
        name = re.sub(r'[\s]+', '_', name)          # Replace spaces with _
        return name.strip().lower()


    df.columns = [to_snake_case(col) for col in df.columns]

    # print(df.columns)

    # Replace nulls in specific columns to 'Unknown'
    col_list = df.columns.tolist()
    columns_to_fill = col_list[-6:]
    replacement_value = 'Unknown'

    # Remove rows where 'isin_Number' is NaN
    df = df.dropna(subset=['isin_no'])

    df.loc[:, columns_to_fill] = df.loc[:, columns_to_fill].fillna('Unknown')
    # df
    df = df.rename(columns = {
        "issuer_name": "name",
        "security_id": "trading_symbol"
    })

    df = df[["isin_no","trading_symbol","name",'sector_name', 'industry_new_name', 'igroup_name', 'isubgroup_name']]
     # Step 3: Convert DataFrame to list of dicts for executemany
    rows_to_insert = df.to_dict(orient="records")

    
    # Step 2: Prepare raw SQL INSERT
    insert_query = text("""
        INSERT INTO instruments (
            isin_no,
            trading_symbol,
            name,
            sector_name,
            industry_new_name,
            igroup_name,
            isubgroup_name   
        )
        VALUES (
            :isin_no,
            :trading_symbol,
            :name,
            :sector_name,
            :industry_new_name,
            :igroup_name,
            :isubgroup_name  
        )
    """)

   
    # # Print first 5 records
    # for row in rows_to_insert[:5]:
    #     print(row)

    # Step 4: Execute as bulk insert
    await db.execute(insert_query, rows_to_insert)  # asyncpg supports list of dicts
    await db.commit()
    print(f"✅ Inserted {len(rows_to_insert)} instruments.")