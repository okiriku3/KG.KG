
# # OAuth 2.0設定
# client_id = st.secrets["CLIENT_ID"]
# client_secret = st.secrets["CLIENT_SECRET"]
# redirect_uri = 'https://kgkgkg.streamlit.app/'  # あなたのStreamlitアプリのリダイレクトURIを指定


import streamlit as st
import requests
import sqlite3
from io import BytesIO
import pandas as pd
import tempfile
from datetime import datetime

# OAuth 2.0設定
client_id = st.secrets["CLIENT_ID"]
client_secret = st.secrets["CLIENT_SECRET"]
redirect_uri = 'https://kgkgkg.streamlit.app/'  # あなたのStreamlitアプリのリダイレクトURIを指定

auth_url = 'https://account.box.com/api/oauth2/authorize'
token_url = 'https://api.box.com/oauth2/token'
root_folder_id = '0'  # ルートフォルダのID（「0」はルートフォルダを意味する）

# ファイル名生成
def generate_db_file_name(base_name='box_files', extension='db', counter=1):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_{timestamp}_{counter:02d}.{extension}"

def find_existing_files(access_token, base_file_name):
    url = f'https://api.box.com/2.0/search'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'query': base_file_name,
        'file_extensions': 'db'
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('entries', [])
    else:
        st.write("ファイルの検索に失敗しました。")
        return []

def get_new_db_file_name(access_token, base_file_name):
    existing_files = find_existing_files(access_token, base_file_name)
    if not existing_files:
        return base_file_name

    counter = 1
    while True:
        new_file_name = generate_db_file_name(base_name=base_file_name.split('.')[0], extension='db', counter=counter)
        if not any(file['name'] == new_file_name for file in existing_files):
            return new_file_name
        counter += 1

def upload_db_file(access_token, folder_id, file_stream, file_name):
    url = f'https://upload.box.com/api/2.0/files/content'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    files = {
        'attributes': (None, '{"name":"' + file_name + '","parent":{"id":"' + folder_id + '"}}'),
        'file': (file_name, file_stream)
    }
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 201:
        st.write("データベースファイルがBoxにアップロードされました。")
    else:
        st.write("データベースファイルのアップロードに失敗しました。")

def main():
    st.title("Box内の画像ファイルをSQLiteに保存")

    auth_url = get_auth_url()
    st.markdown(f"[Boxで認証するにはここをクリックしてください]({auth_url})")

    query_params = st.experimental_get_query_params()
    auth_code = query_params.get('code', [None])[0]

    if auth_code:
        access_token = get_access_token(auth_code)

        if access_token:
            st.write("認証成功！")

            files = get_all_files(access_token, root_folder_id)
            images = filter_images(files)

            for image in images:
                shared_link = create_shared_link(access_token, image['id'])
                if shared_link:
                    image['shared_link'] = shared_link
                else:
                    image['shared_link'] = 'リンク作成失敗'

            base_db_file_name = 'box_files.db'
            db_file_name = get_new_db_file_name(access_token, base_db_file_name)

            conn = sqlite3.connect(db_file_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS box_files (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    folder_id TEXT,
                    created_at TEXT,
                    shared_link TEXT
                )
            ''')
            conn.commit()

            for image in images:
                cursor.execute('''
                    INSERT OR REPLACE INTO box_files (id, name, folder_id, created_at, shared_link)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    image['id'],
                    image['name'],
                    image['parent']['id'],
                    image['created_at'],
                    image['shared_link']
                ))
            conn.commit()

            with open(db_file_name, 'rb') as f:
                db_stream = BytesIO(f.read())

            upload_db_file(access_token, root_folder_id, db_stream, db_file_name)

            st.write("画像ファイルの情報をデータベースに保存しました。")
            df = show_db_content(db_file_name)
            st.dataframe(df)

        else:
            st.write("アクセストークンの取得に失敗しました。")
    else:
        st.write("認証コードが見つかりません。")

if __name__ == "__main__":
    main()
