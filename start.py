
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


# OAuth 2.0設定
client_id = st.secrets["CLIENT_ID"]
client_secret = st.secrets["CLIENT_SECRET"]
redirect_uri = 'https://kgkgkg.streamlit.app/'  # あなたのStreamlitアプリのリダイレクトURIを指定

auth_url = 'https://account.box.com/api/oauth2/authorize'
token_url = 'https://api.box.com/oauth2/token'
root_folder_id = '0'  # ルートフォルダのID（「0」はルートフォルダを意味する）

db_file_name = 'box_files.db'  # Box内でのSQLiteデータベースファイル名

def get_auth_url():
    return f"{auth_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"

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

def filter_images(files):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    return [file for file in files if any(file['name'].lower().endswith(ext) for ext in image_extensions)]

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

def box_db_exists(access_token, db_file_name):
    url = f'https://api.box.com/2.0/search?query={db_file_name}&file_extensions=db'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        files = response.json().get('entries', [])
        return files[0] if files else None
    else:
        st.write("Box内のデータベースファイルの検索に失敗しました。")
        return None

def upload_or_update_db_file(access_token, folder_id, file_stream):
    existing_db_file = box_db_exists(access_token, db_file_name)
    if existing_db_file:
        # 更新
        url = f'https://upload.box.com/api/2.0/files/{existing_db_file["id"]}/content'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        files = {
            'file': (db_file_name, file_stream)
        }
        response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            st.write("データベースファイルがBoxで更新されました。")
        else:
            st.write(f"データベースファイルの更新に失敗しました。ステータスコード: {response.status_code}, レスポンス: {response.text}")
    else:
        # アップロード
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
            st.write(f"データベースファイルのアップロードに失敗しました。ステータスコード: {response.status_code}, レスポンス: {response.text}")

def get_temp_db_file(db_stream):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
        temp_db.write(db_stream.getvalue())
        temp_db.flush()
        return temp_db.name

def show_db_content(db_file_path):
    conn = sqlite3.connect(db_file_path)
    query = "SELECT name, id, folder_id, created_at, shared_link FROM box_files"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

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

            db_file = box_db_exists(access_token, db_file_name)

            if db_file:
                st.write("既存のデータベースを更新します。")
                url = f'https://api.box.com/2.0/files/{db_file["id"]}/content'
                headers = {
                    'Authorization': f'Bearer {access_token}'
                }
                response = requests.get(url, headers=headers)
                db_stream = BytesIO(response.content)
                db_file_path = get_temp_db_file(db_stream)
            else:
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
                db_file_path = get_temp_db_file(BytesIO(open(db_file_name, 'rb').read()))

            with sqlite3.connect(db_file_path) as conn:
                cursor = conn.cursor()
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

            with open(db_file_path, 'rb') as f:
                db_stream = BytesIO(f.read())
            upload_or_update_db_file(access_token, root_folder_id, db_stream)

            st.write("画像ファイルの情報をデータベースに保存しました。")

            df = show_db_content(db_file_path)
            st.write(df)

if __name__ == "__main__":
    main()
