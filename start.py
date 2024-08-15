
# # OAuth 2.0設定
# client_id = st.secrets["CLIENT_ID"]
# client_secret = st.secrets["CLIENT_SECRET"]
# redirect_uri = 'https://kgkgkg.streamlit.app/'  # あなたのStreamlitアプリのリダイレクトURIを指定

import streamlit as st
import requests
from io import BytesIO
from PIL import Image

# OAuth 2.0設定
client_id = st.secrets["CLIENT_ID"]
client_secret = st.secrets["CLIENT_SECRET"]
redirect_uri = 'https://kgkgkg.streamlit.app/'  # あなたのStreamlitアプリのリダイレクトURIを指定

auth_url = 'https://account.box.com/api/oauth2/authorize'
token_url = 'https://api.box.com/oauth2/token'
root_folder_id = '0'  # ルートフォルダのID（「0」はルートフォルダを意味する）

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

# 画像を取得し、PIL形式に変換
def get_image_pil(access_token, file_id):
    download_url = f"https://api.box.com/2.0/files/{file_id}/content"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(download_url, headers=headers)
    
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        st.write(f"画像の取得に失敗しました。ファイルID: {file_id}")
        return None

def main():
    st.title("Box内の画像ファイル一覧")

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

            # 画像ファイルをフィルタリングして表示
            images = filter_images(files)
            if images:
                st.write("### 画像ファイル一覧")
                
                # 表のヘッダーを表示
                cols = st.columns([2, 2, 2, 2, 3])
                cols[0].write("**ファイル名**")
                cols[1].write("**ファイルID**")
                cols[2].write("**フォルダID**")
                cols[3].write("**ファイル作成日**")
                cols[4].write("**画像プレビュー**")
                
                # 各画像ファイルを表に表示
                for image in images:
                    cols = st.columns([2, 2, 2, 2, 3])
                    cols[0].write(image['name'])
                    cols[1].write(image['id'])
                    cols[2].write(image['parent']['id'])  # フォルダIDを表示
                    cols[3].write(image['created_at'])  # ファイル作成日を表示
                    image_pil = get_image_pil(access_token, image['id'])
                    if image_pil:
                        cols[4].image(image_pil, caption=image['name'], use_column_width=True)
            else:
                st.write("画像ファイルが見つかりませんでした。")
        else:
            st.write("アクセストークンの取得に失敗しました。")
    
if __name__ == "__main__":
    main()
