import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import webbrowser

# OAuth 2.0設定
client_id = '4iyp4sdhqhfoytegk1rvy9yv68enprrg'
client_secret = 'nw88rBDZ3jxxJqthW8OBiejfm5ACmWtN'
redirect_uri = 'http://localhost:8501/'
auth_url = 'https://account.box.com/api/oauth2/authorize'
token_url = 'https://api.box.com/oauth2/token'

# 認証コード取得
def get_auth_code():
    auth_request_url = (
        f"{auth_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
    )
    webbrowser.open(auth_request_url)
    return st.text_input("Boxから取得した認証コードを入力してください:")

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

# Box内の画像を取得して表示
def display_box_image(file_id, access_token):
    file_url = f"https://api.box.com/2.0/files/{file_id}/content"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        st.image(response.content)
    else:
        st.write("画像の取得に失敗しました。")

def main():
    st.title("Boxから画像を取得して表示")

    # 認証コードの取得
    auth_code = get_auth_code()

    if auth_code:
        # アクセストークンの取得
        access_token = get_access_token(auth_code)

        if access_token:
            st.write("認証成功！")

            # BoxのファイルIDを入力
            file_id = st.text_input("表示したい画像のBoxファイルIDを入力してください:")

            if file_id:
                # 画像を表示
                display_box_image(file_id, access_token)
        else:
            st.write("アクセストークンの取得に失敗しました。")
    
if __name__ == "__main__":
    main()
