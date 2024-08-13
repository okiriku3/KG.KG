import streamlit as st
from PIL import Image

st.title("Streamlit Image Viewer with Zoom and Pan")

# 画像のアップロード
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

def zoom():
    if uploaded_file is not None:
        # 画像の読み込み
        img = Image.open(uploaded_file)
        col1,col2,col3=st.columns(3)

        with col1:
            # ズームレベルをスライダーで設定
            zoom = st.slider("Zoom(times)", 0.1, 10.0, 1.0)  # 最小0.1倍から最大3倍まで
            # 画像のズーム後のサイズを計算
            width, height = img.size
            new_width = int(width * zoom)
            new_height = int(height * zoom)
            resized_img = img.resize((new_width, new_height))
    
        # スクロールバーの位置を設定（ズームが1.0以下の場合はオフセットをリセット）
        if zoom > 1.0:
            with col2:
                x_offset = st.slider("Horizontal position", 0, max(0, new_width - width), 0)
            with col3:
                y_offset = st.slider("Vertical position", 0, max(0, new_height - height), 0)
            right = min(new_width, x_offset + width)
            bottom = min(new_height, y_offset + height)
            cropped_img = resized_img.crop((x_offset, y_offset, right, bottom))
        else:
            cropped_img = resized_img  # ズームが1.0以下の場合はクロップせずにそのまま表示
    
        # 画像の表示
        coll1,coll2,coll3=st.columns(3)
        with coll1:
            st.image(cropped_img, caption="Uploaded Image", use_column_width=True)
        with coll2:
            st.image(cropped_img, caption="Uploaded Image", use_column_width=True)
        with coll3:
            st.image(cropped_img, caption="Uploaded Image", use_column_width=True)
    return "fin"

#########
def allview():
    import streamlit as st
    import matplotlib.pyplot as plt
    import numpy as np
    
    # タイトル
    st.title("Image and Graph Grid")
    
    # 4x6のグリッド作成
    rows = 4
    cols = 6
    
    # グリッドに表示する内容
    for i in range(rows):
        cols_layout = st.columns(cols)
        for j in range(cols):
            with cols_layout[j]:
                if j % 2 == 0:
                    # 画像を表示
                    st.image("https://placekitten.com/200/150", caption=f"Image {i*cols + j + 1}")
                else:
                    # グラフを表示
                    fig, ax = plt.subplots()
                    x = np.linspace(0, 10, 100)
                    y = np.sin(x) + np.random.normal(0, 0.1, x.size)
                    ax.plot(x, y)
                    ax.set_title(f"Graph {i*cols + j + 1}")
                    st.pyplot(fig)
    return "fin"

tab1,tab2 =st.tabs(["allveiw","zoom"])
with tab1:
    allview()
with tab2:
    zoom()

######
from boxsdk import JWTAuth
from boxsdk import Client
from boxsdk.exception import BoxAPIException

#jsonファイルのパス
#CONFIG_FILE = 'config.json'

#BOX APIを使う準備
auth = JWTAuth.from_settings_file("config.json")
client = Client(auth)

# ユーザー情報を取得して表示（APIテスト）
user = client.user().get()
st.write(f'UserName:{user.name}(ID:{user.id}), Email: {user.login}')


########################
# import streamlit as st
# from boxsdk import Client, OAuth2
# from boxsdk.object.file import File
# from io import BytesIO
# from PIL import Image

# # Box APIのクライアント認証情報
# CLIENT_ID = st.secrets.CLIENT_ID.key 
# CLIENT_SECRET =st.secrets.CLIENT_SECRET.key
# DEVELOPER_TOKEN = st.secrets.DEVELOPER_TOKEN.key  # またはアクセストークン

# # OAuth2認証の設定
# oauth2 = OAuth2(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, access_token=DEVELOPER_TOKEN)
# client = Client(oauth2)

# # StreamlitのUI
# st.title("Box Image Viewer")

# # 表示するBoxフォルダのID
# folder_id = '0'

# # フォルダ内のアイテムを取得
# folder = client.folder(folder_id).get()
# items = folder.get_items()

# # 画像ファイルのリストを作成
# image_files = [item for item in items if isinstance(item, File) and item.name.lower().endswith(('png', 'jpg', 'jpeg', 'gif'))]

# # 画像の選択
# selected_image = st.selectbox("Select an image", [img.name for img in image_files])

# # 選択された画像を取得して表示
# if selected_image:
#     file_id = next(img.id for img in image_files if img.name == selected_image)
#     box_file = client.file(file_id).content()
#     image = Image.open(BytesIO(box_file))
#     st.image(image, caption=selected_image)


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
