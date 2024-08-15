
# # OAuth 2.0設定
# client_id = st.secrets["CLIENT_ID"]
# client_secret = st.secrets["CLIENT_SECRET"]
# redirect_uri = 'https://kgkgkg.streamlit.app/'  # あなたのStreamlitアプリのリダイレクトURIを指定

import streamlit as st
import requests
import sqlite3
from io import BytesIO
import pandas as pd

# OAuth 2.0設定
client_id = st.secrets["CLIENT_ID"]
client_secret = st.secrets["CLIENT_SECRET"]
redirect_uri = 'https://kgkgkg.streamlit.app/'  # あなたのStreamlitアプリのリダイレクトURIを指定

auth_url = 'https://account.box.com/api/oauth2/authorize'
token_url = 'https://api.box.com/oauth2/token'
root_folder_id = '0'  # ルートフォルダのID（「0」はルートフォルダを意味する）

db_file_name = 'box_files.db'  # Box内でのSQLiteデータベースファイル名

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

# Box内のファイルを検索
def search_box_files(access_token, query):
    url = f'https://api.box.com/2.0/search?query={query}&file_extensions=db'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('entries', [])
    else:
        st.write("Boxファイルの検索に失敗しました。")
        return []

# Box内のフォルダのすべてのファイルを再帰的に取得
def get_all_files(access_token, folder_id='0'):
    files = []
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    url = f'https://api.box.com/2.0/folders/{folder_id}/items'
    params = {'limit': 1000}
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        items = response.json().get('entries', [])
        for item in items:
            if item['type'] == 'file':
                file_info = get_file_info(access_token, item['id'])
                if file_info:
                    files.append(file_info)
            elif item['type'] == 'folder':
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

# Box内にSQLite DBファイルが存在するか確認
def box_db_exists(access_token, db_file_name):
    files = search_box_files(access_token, db_file_name)
    return files[0] if files else None

# Box内にDBファイルをアップロード
def upload_db_to_box(access_token, folder_id, file_stream):
    url = f'https://upload.box.com/api/2.0/files/content'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    files = {
        'attributes': (None, '{"name":"' + db_file_name + '","parent":{"id":"' + folder_id + '"}}'),
        'file': (db_file_name, file_stream)
    }
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 201:
        st.write("データベースファイルがBoxにアップロードされました。")
    else:
        st.write("データベースファイルのアップロードに失敗しました。")

# Box内の既存のDBファイルを更新
def update_box_db_file(access_token, file_id, file_stream):
    url = f'https://upload.box.com/api/2.0/files/{file_id}/content'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    files = {
        'file': (db_file_name, file_stream)
    }
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 201:
        st.write("データベースファイルがBoxで更新されました。")
    else:
        st.write("データベースファイルの更新に失敗しました。")

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

            # Box内のDBファイルの存在確認
            db_file = box_db_exists(access_token, db_file_name)

            # DB接続
            if db_file:
                # Boxから既存のDBファイルをダウンロードして接続
                st.write("既存のデータベースを更新します。")
                url = f'https://api.box.com/2.0/files/{db_file["id"]}/content'
                headers = {
                    'Authorization': f'Bearer {access_token}'
                }
                response = requests.get(url, headers=headers)
                db_stream = BytesIO(response.content)
                conn = sqlite3.connect(db_stream)
                cursor = conn.cursor()
            else:
                # 新規にDBファイルを作成
                st.write("新しいデータベースを作成します。")
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

            # ファイル情報をDBに保存
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

            # データベースファイルをBoxにアップロードまたは更新
            with open(db_file_name, 'rb') as f:
                db_stream = BytesIO(f.read())
            if db_file:
                update_box_db_file(access_token, db_file['id'], db_stream)
            else:
                upload_db_to_box(access_token, root_folder_id, db_stream)

            st.write("画像ファイルの情報をデータベースに保存しました。")

            # DBの内容を表示するボタンを作成
            if st.button('Show Box Files DB'):
                st.write("データベースの内容を表示します。")
                
                # データベースファイルをBoxから取得
                url = f'https://api.box.com/2.0/files/{db_file["id"]}/content'
                headers = {
                    'Authorization': f'Bearer {access_token}'
                }
                response = requests.get(url, headers=headers)
                
                # DBを読み込み
                with BytesIO(response.content) as db_stream:
                    conn = sqlite3.connect(db_stream)
                    query = "SELECT name, id, folder_id, created_at, shared_link FROM box_files"
                    df = pd.read_sql_query(query, conn)
                    st.write(df)

if __name__ == "__main__":
    main()
