import streamlit as st
import os
import random
import re
from io import BytesIO
import requests
import numpy as np
import pandas as pd
from PIL import Image, ImageFilter
import exifread
import pdfplumber
from docx import Document
from google.oauth2 import service_account
from google.cloud import texttospeech
import plotly.express as px
import plotly.graph_objs as go
import streamlit.components.v1 as components
from pydub import AudioSegment
import openai
import json
import tempfile
from textblob import TextBlob
import nltk
import bcrypt
import base64
import sqlite3
import threading

# 必要なNLTKリソースのダウンロード
nltk.download('punkt')

# 初期設定
st.set_page_config(page_title="究極融合アプリ", page_icon="✨", layout="wide")

# カスタムCSSを追加（洗練されたUI）
custom_css = """
<style>
body {
    background: #121212;
    color: #ffffff;
    font-family: 'Helvetica', sans-serif;
}
h1, h2, h3, h4, h5, h6 {
    color: #ffffff;
}
.block-container {
    padding: 1rem 2rem;
}
.sidebar .sidebar-content {
    background: #1e1e1e;
    color: #ffffff;
}
.stTextInput > div {
    color:#ffffff;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 以下、前回までのコードを省略

# ユーティリティ関数群
def clear_url():
    st.session_state["image_url"] = ""

def clear_files():
    st.session_state["uploaded_files"] = None
    st.session_state["file_uploader_key"] = not st.session_state.get("file_uploader_key", False)

def clear_chat_history():
    st.session_state["messages"] = [{
        "role":"assistant",
        "content":"チャット履歴をクリアしました。再び新たなる時代へ踏み出そう。"
    }]
    st.session_state["exif_df"] = pd.DataFrame()
    st.session_state["uploaded_files"] = None
    st.session_state["image_url"] = ""
    st.session_state["user_preferences"] = {
        "theme": "ダークモード",
        "notifications": True
    }
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
        label="⇩ EXIF除去後の画像ダウンロード",
        data=data,
        file_name="image_no_exif.jpg",
        mime="image/jpeg",
    )

def detect_language(text):
    if re.search('[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]', text):
        return 'ja-JP'
    return 'en-US'

def synthesize_speech_chunk(text, lang_code, gender='neutral', rate=1.0, pitch=0.0):
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
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=rate,
            pitch=pitch
        )
        response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

        segment = AudioSegment.from_file(BytesIO(response.audio_content), format="mp3")
        combined_audio += segment

    output_buffer = BytesIO()
    combined_audio.export(output_buffer, format="mp3")
    output_buffer.seek(0)
    return output_buffer

def summarize_text(text, language='ja'):
    # 簡単な要約を行う関数（TextBlobを使用）
    if language == 'ja':
        # 日本語の要約はTextBlobでは対応していないため、簡易的に文を抽出
        sentences = re.split('。|\n', text)
        summary = '。'.join(sentences[:3]) + '。' if len(sentences) > 3 else text
    else:
        blob = TextBlob(text)
        summary = blob.noun_phrases
        summary = ', '.join(summary[:5]) if summary else text
    return summary

def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    if sentiment > 0.1:
        return 'ポジティブ'
    elif sentiment < -0.1:
        return 'ネガティブ'
    else:
        return 'ニュートラル'

def extract_keywords(text, num_keywords=5):
    blob = TextBlob(text)
    keywords = blob.noun_phrases
    return ', '.join(keywords[:num_keywords]) if keywords else 'なし'

def load_users():
    return load_users()

def save_users(users):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('DELETE FROM users')
    for username, password in users.items():
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

########################################################
# サイドバー
########################################################
with st.sidebar:
    st.markdown("<h1 style='color:white;'>融合</h1>",unsafe_allow_html=True)
    st.markdown("#### EXIF解析 & 超大規模TTS & GPT対話")
    expander = st.expander("🗀 ファイル入力")
    with expander:
        st.text("長大テキスト/画像/URL分析対応")
        image_url = st.text_input("EXIF解析用画像URL:", key="image_url", on_change=clear_files, value=st.session_state["image_url"])
        file_uploader_key = "file_uploader_{}".format(st.session_state.get("file_uploader_key", False))
        uploaded_files = st.file_uploader(
            "ファイルアップロード:",
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
    st.caption("© Exifa.net (Sahir Maharaj,2024), CC-BY 4.0")

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
        st.warning("URLから画像取得失敗")

########################################################
# メインUI構築
########################################################
st.markdown("<h1 style='text-align:center;color:white;'>究極融合: EXIF & TTS & GPT</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#cccccc;'>300ページ超テキスト音声化、EXIF解析、カラー可視化、GPT対話</p>",unsafe_allow_html=True)

# 新しいタブ構成に更新
tabs = st.tabs([
    "📜 テキスト音声合成",
    "🖼 EXIF解析＆ビジュアル",
    "💬 GPT対話",
    "📈 データダッシュボード",
    "⚙️ ユーザー設定",
    "📖 テキスト分析",
    "🖌 画像強化"
])

# 音声合成タブ
with tabs[0]:
    st.subheader("超大規模テキスト音声化")
    input_option = st.selectbox("入力方法",("直接入力","アップロードテキスト利用"))
    tts_text = ""
    if input_option == "直接入力":
        tts_text = st.text_area("音声合成するテキストを貼り付け","ここに膨大なテキスト(例:書籍全文)を入力")
    else:
        if file_text:
            st.write("抽出テキスト(一部):")
            st.write(file_text[:500]+"...")
            tts_text = file_text
        else:
            st.write("アップロードテキストがありません")

    selected_gender = st.selectbox("話者の性別",('default','male','female','neutral'))
    speech_rate = st.slider("話速", 0.5, 2.0, 1.0, 0.1)
    speech_pitch = st.slider("ピッチ", -20.0, 20.0, 0.0, 1.0)
    if tts_text and st.button("音声合成実行"):
        with st.spinner("音声合成中...長文は時間要"):
            lang_code = detect_language(tts_text)
            final_mp3 = synthesize_speech_chunk(tts_text, lang_code, gender=selected_gender, rate=speech_rate, pitch=speech_pitch)
        st.success("音声合成完了！")
        st.download_button("MP3ダウンロード", data=final_mp3, file_name="converted_book.mp3", mime="audio/mpeg")
        st.audio(final_mp3, format="audio/mp3")

# 以下、他のタブのコードを省略

########################################################
# その他のタブのコード
########################################################

# 完全なコードは省略していますが、他のタブも同様に `requirements.txt` に必要なライブラリを追加し、依存関係がすべて正しくインストールされることを確認してください。

# 最後に
st.markdown("---")
st.caption("© Exifa.net (Sahir Maharaj,2024), CC-BY 4.0. これは全てを統合した世界初の究極アプリ。")

