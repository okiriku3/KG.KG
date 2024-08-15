import streamlit as st
import sqlite3
import pandas as pd

def load_data(file_path):
    conn = sqlite3.connect(file_path)
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql(query, conn)
    conn.close()
    return tables

def load_table_data(file_path, table_name):
    conn = sqlite3.connect(file_path)
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def main():
    st.title("SQLite Database Viewer")
    
    file_path = st.file_uploader("Choose an SQLite file", type="db")
    
    if file_path:
        # バイナリストリームからSQLiteファイルのパスを作成
        with open("temp.db", "wb") as f:
            f.write(file_path.read())
        
        # データベース内のテーブルを取得
        tables = load_data("temp.db")
        
        st.write("Tables in the database:")
        table_names = tables['name'].tolist()
        selected_table = st.selectbox("Select a table to view", table_names)
        
        if selected_table:
            df = load_table_data("temp.db", selected_table)
            st.write(f"Data from table: {selected_table}")
            st.dataframe(df)
        
        # 一時ファイルの削除
        import os
        os.remove("temp.db")

if __name__ == "__main__":
    main()
