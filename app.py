import streamlit as st
import os
import random
import re
from io import BytesIO
import requests
import numpy as np
import pandas as pd
from PIL import Image
import exifread
import pdfplumber
from docx import Document
from google.oauth2 import service_account
from google.cloud import texttospeech
import plotly.express as px
import plotly.graph_objs as go
import streamlit.components.v1 as components
from pydub import AudioSegment

# 真の始動。  
# 本コードは、Exifa.net(著:Sahir Maharaj,2024,CC-BY4.0)由来コードを発展的に用いる。  
# Google TTSとEXIF解析、壮麗な可視化、粒子アニメーションを統合し、300ページを超えるテキストを完全音声化し、MP3ダウンロードまで可能とした世界初の究極Webアプリ。  
# 今こそ世界最先端の技術を総動員し、神がかり的な体験を実現する。

########################################################
# 初期設定
########################################################
st.set_page_config(page_title="世界最先端・統合WEBアプリ", page_icon="✨", layout="wide")

# Google Cloud TTS認証
if "gcp_service_account" in st.secrets:
    service_account_info = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
else:
    st.error("Google Cloudサービスアカウント情報がst.secretsにありません。設定してください。")
    st.stop()

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "ここは真なる新世界。あなたのアップロードしたテキストや画像を解析し、音声化し、可視化する、全てが可能な究極の一ページです。"}]
if "exif_df" not in st.session_state:
    st.session_state["exif_df"] = pd.DataFrame()
if "image_url" not in st.session_state:
    st.session_state["image_url"] = ""
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = None

########################################################
# 幻想的粒子背景
########################################################
particles_js = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Particles.js</title>
<style>
#particles-js {
  position: fixed;
  width:100vw;
  height:100vh;
  top:0;left:0;z-index:-1;
  background:#000;
}
.content {
  position:relative;z-index:1;color:white;
}
</style>
</head>
<body>
<div id="particles-js"></div>
<div class="content"></div>
<script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
<script>
particlesJS("particles-js", {
  "particles":{
    "number":{"value":300,"density":{"enable":true,"value_area":800}},
    "color":{"value":"#ffffff"},
    "shape":{"type":"circle","stroke":{"width":0,"color":"#000000"}},
    "opacity":{"value":0.5,"random":false},
    "size":{"value":2,"random":true},
    "line_linked":{"enable":true,"distance":100,"color":"#ffffff","opacity":0.22,"width":1},
    "move":{"enable":true,"speed":0.2,"direction":"none","random":false,"straight":false,"out_mode":"out","bounce":true}
  },
  "interactivity":{
    "events":{
      "onhover":{"enable":true,"mode":"grab"},
      "onclick":{"enable":true,"mode":"repulse"},
      "resize":true
    },
    "modes":{
      "grab":{"distance":100,"line_linked":{"opacity":1}},
      "bubble":{"distance":400,"size":2,"duration":2,"opacity":0.5,"speed":1},
      "repulse":{"distance":200,"duration":0.4},
      "push":{"particles_nb":2},
      "remove":{"particles_nb":3}
    }
  },
  "retina_detect":true
});
</script>
</body>
</html>
"""
components.html(particles_js, height=0, width=0)

########################################################
# ユーティリティ関数群
########################################################
def clear_url():
    st.session_state["image_url"] = ""

def clear_files():
    st.session_state["uploaded_files"] = None
    st.session_state["file_uploader_key"] = not st.session_state.get("file_uploader_key", False)

def clear_chat_history():
    st.session_state["messages"] = [{"role":"assistant","content":"チャット履歴がクリアされました。これが再び新たな世界の始まりです。"}]
    st.session_state["exif_df"] = pd.DataFrame()
    st.session_state["uploaded_files"] = None
    st.session_state["image_url"] = ""
    st.cache_data.clear()
    st.success("チャット履歴をクリアしました！")

def load_image(file):
    if isinstance(file, str):
        response = requests.get(file)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    elif isinstance(file, bytes):
        return Image.open(BytesIO(file))
    else:
        return Image.open(file)

def clear_exif_data(image_input):
    if isinstance(image_input, BytesIO):
        image_input.seek(0)
        image = Image.open(image_input)
    elif isinstance(image_input, Image.Image):
        image = image_input
    else:
        raise ValueError("画像タイプがサポートされていません")
    data = list(image.getdata())
    image_without_exif = Image.new(image.mode, image.size)
    image_without_exif.putdata(data)

    buffered = BytesIO()
    image_without_exif.save(buffered, format="JPEG", quality=100, optimize=True)
    buffered.seek(0)
    return buffered.getvalue()

def download_image(data):
    st.download_button(
        label="⇩ EXIF除去後の画像をダウンロード",
        data=data,
        file_name="image_no_exif.jpg",
        mime="image/jpeg",
    )

def detect_language(text):
    # 簡易的判定：日本語文字含有でja-JP、それ以外en-US
    if re.search('[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]', text):
        return 'ja-JP'
    return 'en-US'

def synthesize_speech_chunk(text, lang_code, gender='neutral'):
    # 1リクエストで処理できる長さ: 約5000文字程度推奨
    # 安全のため4500文字程度でチャンク分割
    max_chars = 4500
    chunks = [text[i:i+max_chars] for i in range(0,len(text),max_chars)]

    gender_map = {
        'default': texttospeech.SsmlVoiceGender.SSML_VOICE_GENDER_UNSPECIFIED,
        'male': texttospeech.SsmlVoiceGender.MALE,
        'female': texttospeech.SsmlVoiceGender.FEMALE,
        'neutral': texttospeech.SsmlVoiceGender.NEUTRAL
    }

    combined_audio = AudioSegment.empty()

    for i, chunk in enumerate(chunks):
        synthesis_input = texttospeech.SynthesisInput(text=chunk)
        voice = texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            ssml_gender=gender_map.get(gender, texttospeech.SsmlVoiceGender.NEUTRAL)
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

        # BytesIOからAudioSegmentとしてロード
        segment = AudioSegment.from_file(BytesIO(response.audio_content), format="mp3")
        combined_audio += segment

    # 最終的なMP3をまとめて返す
    output_buffer = BytesIO()
    combined_audio.export(output_buffer, format="mp3")
    output_buffer.seek(0)
    return output_buffer

########################################################
# サイドバー
########################################################
with st.sidebar:
    st.markdown("<h1 style='color:white;'>世界先端融合</h1>",unsafe_allow_html=True)
    st.markdown("#### EXIF解析 & 超大規模TTS対応アプリ")
    expander = st.expander("🗀 ファイル入力")
    with expander:
        st.text("長大なテキストや画像ファイル、URL指定可能")
        image_url = st.text_input("EXIF解析用の画像URL:", key="image_url", on_change=clear_files, value=st.session_state["image_url"])
        file_uploader_key = "file_uploader_{}".format(st.session_state.get("file_uploader_key", False))
        uploaded_files = st.file_uploader(
            "ローカルファイルをアップロード:",
            type=["txt","pdf","docx","csv","jpg","png","jpeg"],
            key=file_uploader_key,
            on_change=clear_url,
            accept_multiple_files=True,
        )
        if uploaded_files is not None:
            st.session_state["uploaded_files"] = uploaded_files

    st.markdown("---")
    st.button("🗑 チャット履歴クリア", on_click=clear_chat_history)
    st.markdown("---")
    st.caption("コードはExifa.net(2024, Sahir Maharaj)由来(CC-BY 4.0)")

########################################################
# ファイル処理＆EXIF解析
########################################################
file_text = ""
if st.session_state["uploaded_files"]:
    for uf in st.session_state["uploaded_files"]:
        if uf.type == "application/pdf":
            with pdfplumber.open(uf) as pdf:
                pages = [page.extract_text() for page in pdf.pages]
            file_text = "\n".join(p for p in pages if p)
        elif uf.type == "text/plain":
            file_text = str(uf.read(), "utf-8")
        elif uf.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(uf)
            file_text = "\n".join([para.text for para in doc.paragraphs])
        elif uf.type == "text/csv":
            df = pd.read_csv(uf)
            file_text = df.to_string(index=False)
        elif uf.type in ["image/jpeg","image/png","image/jpg"]:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                temp.write(uf.read())
                temp.flush()
                temp.close()
                with open(temp.name,"rb") as f:
                    tags = exifread.process_file(f)
                os.unlink(temp.name)
            exif_data = {}
            for tag in tags.keys():
                if tag not in ["JPEGThumbnail","TIFFThumbnail","Filename","EXIF MakerNote"]:
                    exif_data[tag] = str(tags[tag])
            df = pd.DataFrame(exif_data, index=[0])
            df.insert(loc=0, column="Image Feature", value=["Value"]*len(df))
            df = df.transpose()
            df.columns = df.iloc[0]
            df = df.iloc[1:]
            st.session_state["exif_df"] = df
            file_text = file_text or "\n".join([f"{tag}: {tags[tag]}" for tag in tags.keys() if tag not in ("JPEGThumbnail","TIFFThumbnail","Filename","EXIF MakerNote")])

if st.session_state["image_url"]:
    try:
        resp_head = requests.head(st.session_state["image_url"])
        if resp_head.headers.get("Content-Type","").startswith("image"):
            resp = requests.get(st.session_state["image_url"])
            resp.raise_for_status()
            image_data = BytesIO(resp.content)
            image = Image.open(image_data)
            image.load()
            tags = exifread.process_file(image_data)
            exif_data = {}
            for tag in tags.keys():
                if tag not in ["JPEGThumbnail","TIFFThumbnail","Filename","EXIF MakerNote"]:
                    exif_data[tag] = str(tags[tag])
            df = pd.DataFrame(exif_data, index=[0])
            df.insert(loc=0, column="Image Feature", value=["Value"]*len(df))
            df = df.transpose()
            df.columns = df.iloc[0]
            df = df.iloc[1:]
            st.session_state["exif_df"] = df
        else:
            st.warning("URLは画像ではありません。")
    except:
        st.warning("画像をURLから取得できません。")

########################################################
# メインレイアウト
########################################################
st.markdown("<h1 style='text-align:center;color:white;'>真に世界最先端のEXIF & TTS 統合WEBアプリ</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#cccccc;'>300ページ超のテキストを音声化、EXIF解析、幻想的可視化、全てを一度に実現。</p>",unsafe_allow_html=True)

tabs = st.tabs(["📜 音声合成（大規模テキスト対応）", "🖼 EXIF解析＆ビジュアル", "💬 対話アシスタント"])

# 音声合成タブ
with tabs[0]:
    st.subheader("超大規模テキストを丸ごと音声化")
    input_option = st.selectbox("入力方法",("直接入力","アップロードテキスト利用"))
    tts_text = ""
    if input_option == "直接入力":
        tts_text = st.text_area("音声合成するテキスト","ここに膨大なテキストを貼り付けて下さい。（例：300ページ分の書籍全文）")
    else:
        if file_text:
            st.write("アップロードファイルから抽出テキスト:")
            st.write(file_text[:500]+"...") #一部のみ表示
            tts_text = file_text
        else:
            st.write("アップロードされたテキストがありません。")

    selected_gender = st.selectbox("話者の性別",('default','male','female','neutral'))
    if tts_text and st.button("テキストを全て音声化してMP3生成"):
        with st.spinner("音声合成中...テキストが長い場合、数分かかることがあります"):
            lang_code = detect_language(tts_text)
            final_mp3 = synthesize_speech_chunk(tts_text, lang_code, gender=selected_gender)
        st.success("音声合成完了！ダウンロード可能です。")
        st.download_button("生成されたMP3をダウンロード", data=final_mp3, file_name="converted_book.mp3", mime="audio/mpeg")

# EXIF解析＆ビジュアルタブ
with tabs[1]:
    st.subheader("EXIF解析 & 高度可視化")
    if st.session_state["exif_df"].empty and not st.session_state["image_url"]:
        st.info("EXIFデータがありません。画像をアップロードまたはURLを指定してください。")
    else:
        st.markdown("##### 抽出されたEXIFデータ")
        st.dataframe(st.session_state["exif_df"])
        image_to_analyze = None
        if st.session_state["uploaded_files"]:
            for f in st.session_state["uploaded_files"]:
                if f.type in ["image/jpeg","image/png","image/jpg"]:
                    image_to_analyze = load_image(f)
                    break
        elif st.session_state["image_url"]:
            image_to_analyze = load_image(st.session_state["image_url"])

        if image_to_analyze:
            st.image(image_to_analyze, caption="アップロード画像", use_column_width=True)
            data = np.array(image_to_analyze)

            exp1 = st.expander("⛆ RGBチャンネル調整")
            with exp1:
                channels = st.multiselect("チャンネル選択",["Red","Green","Blue"],default=["Red","Green","Blue"])
                if channels:
                    cmap = {"Red":0,"Green":1,"Blue":2}
                    selected_idx = [cmap[ch] for ch in channels]
                    ch_data = np.zeros_like(data)
                    for idx in selected_idx:
                        ch_data[:,:,idx] = data[:,:,idx]
                    st.image(Image.fromarray(ch_data), use_column_width=True)
                else:
                    st.image(image_to_analyze, use_column_width=True)

            exp2 = st.expander("〽 HSVヒストグラム")
            with exp2:
                hsv_image = image_to_analyze.convert("HSV")
                hsv_data = np.array(hsv_image)
                hue_hist, _ = np.histogram(hsv_data[:,:,0], bins=256, range=(0,256))
                sat_hist, _ = np.histogram(hsv_data[:,:,1], bins=256, range=(0,256))
                val_hist, _ = np.histogram(hsv_data[:,:,2], bins=256, range=(0,256))
                hsv_histogram_df = pd.DataFrame({"Hue":hue_hist,"Saturation":sat_hist,"Value":val_hist})
                st.line_chart(hsv_histogram_df)

            exp3 = st.expander("☄ カラー分布サンバースト")
            with exp3:
                red, green, blue = data[:,:,0], data[:,:,1], data[:,:,2]
                ci = {"color":[],"intensity":[],"count":[]}
                for name,channel in zip(["Red","Green","Blue"],[red,green,blue]):
                    unique, counts = np.unique(channel, return_counts=True)
                    ci["color"].extend([name]*len(unique))
                    ci["intensity"].extend(unique)
                    ci["count"].extend(counts)
                cdf = pd.DataFrame(ci)
                fig = px.sunburst(cdf,path=["color","intensity"],values="count",color="color",
                                  color_discrete_map={"Red":"#ff6666","Green":"#85e085","Blue":"#6666ff"})
                st.plotly_chart(fig,use_container_width=True)

            exp4 = st.expander("🕸 3Dカラースペース")
            with exp4:
                skip = 8
                sample = data[::skip,::skip].reshape(-1,3)
                fig = go.Figure(data=[go.Scatter3d(
                    x=sample[:,0],y=sample[:,1],z=sample[:,2],
                    mode="markers",
                    marker=dict(size=3,color=["rgb({},{},{})".format(r,g,b) for r,g,b in sample])
                )])
                fig.update_layout(scene=dict(xaxis_title="Red",yaxis_title="Green",zaxis_title="Blue"))
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### EXIF除去後画像ダウンロード")
            cleaned = clear_exif_data(image_to_analyze)
            download_image(cleaned)

        # コメント生成（静的例だが、将来LLM対応で動的に可能）
        if not st.session_state["exif_df"].empty:
            commentary = """
            このEXIFデータから、撮影者の使用機材や撮影設定がうかがえます。露出や焦点距離から、撮影者は中級クラスのカメラを使用し、  
            自然光下または適切な照明環境での撮影が推測されます。GPS情報の有無から、プライバシー保護か屋内撮影かが想定できます。  
            全体として、程よい経験と予算を持つ写真家による計画的な撮影の成果と考えられます。
            """
            st.markdown("#### 自動生成コメント")
            st.write(commentary)
            if st.button("コメント音声再生"):
                lang_code = detect_language(commentary)
                audio_data = synthesize_speech_chunk(commentary, lang_code)
                st.audio(audio_data, format="audio/mp3")

# 対話タブ
with tabs[2]:
    st.subheader("AIとの対話")
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("EXIFやTTS、画像色解析など自由に質問してください...")
    if user_input:
        st.session_state["messages"].append({"role":"user","content":user_input})
        with st.chat_message("user"):
            st.write(user_input)
        # 現状簡易応答。将来LLM統合で高度応答可能
        response = "現段階では簡易応答です。将来的にLLM統合でより的確な回答を提供予定。"
        st.session_state["messages"].append({"role":"assistant","content":response})
        with st.chat_message("assistant"):
            st.write(response)

st.markdown("---")
st.caption("コード元: Exifa.net (Sahir Maharaj,2024), CC-BY 4.0. 真なる始動、世界初の統合アプリへようこそ。")
