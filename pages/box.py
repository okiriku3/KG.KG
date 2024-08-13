import streamlit as st
import requests

# OAuth 2.0設定
client_id = st.secrets["CLIENT_ID"]
client_secret = st.secrets["CLIENT_SECRET"]
redirect_uri = 'https://kgkgkg.streamlit.app/'

auth_url = 'https://account.box.com/api/oauth2/authorize'
token_url = 'https://api.box.com/oauth2/token'
files_url = 'https://api.box.com/2.0/folders/0/items'  # ルートフォルダーのURL

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
    return response.json().get('access_token')

# Box内のファイルを取得
def get_files(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(files_url, headers=headers)
    if response.status_code == 200:
        return response.json().get('entries', [])
    else:
        st.write("ファイルの取得に失敗しました。")
        return []

# 画像ファイルをフィルタリング
def filter_images(files):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    return [file for file in files if any(file['name'].lower().endswith(ext) for ext in image_extensions)]

# テキストファイルをフィルタリング
def filter_text_files(files):
    text_extensions = ['.txt']
    return [file for file in files if any(file['name'].lower().endswith(ext) for ext in text_extensions)]

# Box内の画像を取得して表示
def display_images(access_token, images):
    for image in images:
        file_id = image['id']
        file_name = image['name']
        download_url = f"https://api.box.com/2.0/files/{file_id}/content"
        
        # 画像を取得して表示
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(download_url, headers=headers)
        if response.status_code == 200:
            st.image(response.content, caption=file_name)
        else:
            st.write(f"{file_name} の取得に失敗しました。")

# Box内のテキストファイルを取得して表示
def display_text_files(access_token, text_files):
    for text_file in text_files:
        file_id = text_file['id']
        file_name = text_file['name']
        download_url = f"https://api.box.com/2.0/files/{file_id}/content"
        
        # テキストファイルを取得して表示
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(download_url, headers=headers)
        if response.status_code == 200:
            st.write(f"### {file_name}")
            st.text(response.text)
        else:
            st.write(f"{file_name} の取得に失敗しました。")

def main():
    st.title("Boxからファイルを取得して表示")

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

            # ファイルを取得
            files = get_files(access_token)

            # 画像ファイルを表示
            images = filter_images(files)
            if images:
                st.write("### 画像ファイル")
                display_images(access_token, images)
            else:
                st.write("画像ファイルが見つかりませんでした。")

            # テキストファイルを表示
            text_files = filter_text_files(files)
            if text_files:
                st.write("### テキストファイル")
                display_text_files(access_token, text_files)
            else:
                st.write("テキストファイルが見つかりませんでした。")
        else:
            st.write("アクセストークンの取得に失敗しました。")
    
if __name__ == "__main__":
    main()
