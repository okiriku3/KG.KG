
# # OAuth 2.0設定
# client_id = st.secrets["CLIENT_ID"]
# client_secret = st.secrets["CLIENT_SECRET"]
# redirect_uri = 'https://kgkgkg.streamlit.app/'  # あなたのStreamlitアプリのリダイレクトURIを指定

import streamlit as st
import requests
import sqlite3
from datetime import datetime

# OAuth 2.0設定
client_id = st.secrets["CLIENT_ID"]
client_secret = st.secrets["CLIENT_SECRET"]
redirect_uri = 'https://kgkgkg.streamlit.app/'  # あなたのStreamlitアプリのリダイレクトURIを指定

auth_url = 'https://account.box.com/api/oauth2/authorize'
token_url = 'https://api.box.com/oauth2/token'
root_folder_id = '0'  # ルートフォルダのID（「0」はルートフォルダを意味する）

# SQLiteデータベース接続
db_path = 'box_files.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# テーブル作成
def create_table():
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

# 認証URLを生成
def get_auth_url():
    return (
        f"{auth_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
    )

# アクセストークン取得
def get_access_token(auth_code):
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri
    }
    response = requests.post(token_url, data=data)
    
    if response.status_code != 200:
        st.write("アクセストークンの取得に失敗しました。")
        st.write(f"エラーメッセージ: {response.json().get('error_description')}")
        return None
    
    return response.json().get('access_token')

# Box内のフォルダのすべてのファイルを再帰的に取得
def get_all_files(access_token, folder_id='0'):
    files = []
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    url = f'https://api.box.com/2.0/folders/{folder_id}/items'
    params = {'limit': 1000}  # BoxのAPIは最大1000アイテムを一度に返します
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        items = response.json().get('entries', [])
        for item in items:
            if item['type'] == 'file':
                # 各ファイルの詳細情報を取得
                file_info = get_file_info(access_token, item['id'])
                if file_info:
                    files.append(file_info)
            elif item['type'] == 'folder':
                # サブフォルダ内のファイルを再帰的に取得
                files.extend(get_all_files(access_token, item['id']))
    else:
        st.write("ファイルの取得に失敗しました。")
    
    return files

# ファイルの詳細情報を取得
def get_file_info(access_token, file_id):
    url = f'https://api.box.com/2.0/files/{file_id}'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.write(f"ファイル情報の取得に失敗しました。ファイルID: {file_id}")
        return None

# 画像ファイルをフィルタリング
def filter_images(files):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    return [file for file in files if any(file['name'].lower().endswith(ext) for ext in image_extensions)]

# 共有リンクを生成
def create_shared_link(access_token, file_id):
    url = f"https://api.box.com/2.0/files/{file_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "shared_link": {
            "access": "open"
        }
    }
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()['shared_link']['url']
    else:
        st.write(f"共有リンクの作成に失敗しました。ファイルID: {file_id}")
        return None

# ファイル情報をデータベースに保存
def save_to_db(files):
    for file in files:
        cursor.execute('''
            INSERT OR REPLACE INTO box_files (id, name, folder_id, created_at, shared_link)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            file['id'],
            file['name'],
            file['parent']['id'],
            file['created_at'],
            file.get('shared_link', '')
        ))
    conn.commit()

def main():
    st.title("Box内の画像ファイルをSQLiteに保存")

    # 認証URLを表示
    auth_url = get_auth_url()
    st.markdown(f"[Boxで認証するにはここをクリックしてください]({auth_url})")

    # 現在のURLを取得し、認証コードを取得
    query_params = st.experimental_get_query_params()
    auth_code = query_params.get('code', [None])[0]

    if auth_code:
        # アクセストークンの取得
        access_token = get_access_token(auth_code)

        if access_token:
            st.write("認証成功！")

            # テーブルを作成
            create_table()

            # すべてのファイルを取得
            files = get_all_files(access_token, root_folder_id)

            # 画像ファイルをフィルタリング
            images = filter_images(files)
            
            # 共有リンクを作成し、データベースに保存
            for image in images:
                shared_link = create_shared_link(access_token, image['id'])
                if shared_link:
                    image['shared_link'] = shared_link
                else:
                    image['shared_link'] = 'リンク作成失敗'
            save_to_db(images)
            
            st.write("画像ファイルの情報をデータベースに保存しました。")
        else:
            st.write("アクセストークンの取得に失敗しました。")
    
if __name__ == "__main__":
    main()
