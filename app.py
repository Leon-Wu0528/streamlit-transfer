import streamlit as st
import os
import random
import string
import time
import shutil
from datetime import datetime

# --- Configuration ---
DATA_DIR = "temp_data"
EXPIRATION_HOURS = 24 # Extended to 24 hours since it's an inbox

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- Helper Functions ---
def cleanup_old_data():
    """Deletes old data based on expiration time to save server space."""
    now = time.time()
    for device_id in os.listdir(DATA_DIR):
        device_dir = os.path.join(DATA_DIR, device_id)
        if os.path.isdir(device_dir):
            for transfer_id in os.listdir(device_dir):
                transfer_dir = os.path.join(device_dir, transfer_id)
                if os.path.isdir(transfer_dir):
                    folder_time = os.path.getmtime(transfer_dir)
                    if (now - folder_time) > (EXPIRATION_HOURS * 3600):
                        try:
                            shutil.rmtree(transfer_dir)
                        except Exception:
                            pass

cleanup_old_data()

def generate_device_id():
    """Generates a random ID like Device-XXXX"""
    return f"Device-{''.join(random.choices(string.digits, k=4))}"

def generate_transfer_id():
    return f"T-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

# --- UI Setup ---
st.set_page_config(page_title="資料傳輸助手 (專屬信箱版)", page_icon="📫", layout="centered")

# --- Authentication / Session State ---
if 'device_id' not in st.session_state:
    st.title("📫 歡迎使用資料傳輸助手")
    st.write("這是一個基於「設備專屬 ID」的傳輸系統。認證一次後，其他人就可以一直把檔案傳到您的專屬信箱。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🆕 新用戶")
        if st.button("創建新設備 ID", type="primary", use_container_width=True):
            st.session_state.device_id = generate_device_id()
            st.rerun()
            
    with col2:
        st.subheader("🔑 現有用戶")
        existing_id = st.text_input("輸入您的設備 ID (例如 Device-1234):")
        if st.button("登入", use_container_width=True):
            if existing_id.strip():
                st.session_state.device_id = existing_id.strip()
                st.rerun()
            else:
                st.error("請輸入 ID！")
    st.stop() # Stop execution here if not logged in

# --- Main Application ---
current_id = st.session_state.device_id

# Header Info
st.success(f"✅ 您已登入。您的專屬設備 ID 是： **{current_id}**")
st.caption("您可以把這個 ID 告訴其他設備（例如電腦 A 告訴電腦 B）。之後只要將資料發送到這個 ID，您就會在收件匣收到。")
st.divider()

# Tabs
tab_send, tab_inbox = st.tabs(["📤 發送資料給別人", f"📥 我的收件匣 (給 {current_id})"])

# --- Tab 1: Send Data ---
with tab_send:
    st.header("📤 發送資料")
    target_id = st.text_input("要發送給誰？ (請輸入對方的設備 ID，例如 Device-1234):")
    
    text_input = st.text_area("在這裡粘貼文字:", height=150)
    uploaded_files = st.file_uploader("上傳文件:", accept_multiple_files=True)
    
    if st.button("🚀 發送", type="primary"):
        if not target_id.strip():
            st.error("請輸入目標設備 ID！")
        elif not text_input and not uploaded_files:
            st.warning("請輸入文字或上傳文件！")
        else:
            t_id = generate_transfer_id()
            # Path: temp_data / target_id / transfer_id
            target_dir = os.path.join(DATA_DIR, target_id.strip(), t_id)
            os.makedirs(target_dir, exist_ok=True)
            
            # Save Timestamp
            with open(os.path.join(target_dir, "meta.txt"), "w") as f:
                f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # Save Text
            if text_input:
                with open(os.path.join(target_dir, "text_data.txt"), "w", encoding="utf-8") as f:
                    f.write(text_input)
            
            # Save Files
            if uploaded_files:
                files_dir = os.path.join(target_dir, "files")
                os.makedirs(files_dir)
                for file in uploaded_files:
                    with open(os.path.join(files_dir, file.name), "wb") as f:
                        f.write(file.getbuffer())
                        
            st.success(f"✅ 成功發送至 {target_id} 的信箱！")

# --- Tab 2: Inbox ---
with tab_inbox:
    st.header("📥 我的收件匣")
    st.write("別人發送給您的資料會出現在這裡。")
    
    col_refresh, _ = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 刷新收件匣"):
            st.rerun()
            
    my_dir = os.path.join(DATA_DIR, current_id)
    
    if not os.path.exists(my_dir) or not os.listdir(my_dir):
        st.info("📭 目前信箱是空的。")
    else:
        # Sort folders by creation time (newest first)
        transfers = []
        for t_folder in os.listdir(my_dir):
            t_path = os.path.join(my_dir, t_folder)
            if os.path.isdir(t_path):
                transfers.append((t_folder, os.path.getctime(t_path)))
        
        transfers.sort(key=lambda x: x[1], reverse=True)
        
        for t_id, _ in transfers:
            t_path = os.path.join(my_dir, t_id)
            
            # Read meta timestamp
            timestamp = "未知時間"
            meta_path = os.path.join(t_path, "meta.txt")
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    timestamp = f.read()
                    
            with st.expander(f"📦 收到包裹 - 時間: {timestamp}", expanded=True):
                # Retrieve Text
                text_file_path = os.path.join(t_path, "text_data.txt")
                if os.path.exists(text_file_path):
                    with open(text_file_path, "r", encoding="utf-8") as f:
                        text_content = f.read()
                    st.markdown("**📝 文字內容:**")
                    st.code(text_content, language="text")
                
                # Retrieve Files
                files_dir = os.path.join(t_path, "files")
                if os.path.exists(files_dir) and os.path.isdir(files_dir):
                    st.markdown("**📎 夾帶文件:**")
                    for file_name in os.listdir(files_dir):
                        file_path = os.path.join(files_dir, file_name)
                        with open(file_path, "rb") as f:
                            file_data = f.read()
                        
                        st.download_button(
                            label=f"⬇️ 下載 {file_name}",
                            data=file_data,
                            file_name=file_name,
                            mime="application/octet-stream",
                            key=f"{t_id}_{file_name}" # Unique key required for Streamlit buttons
                        )
                
                # Delete Button for this transfer
                if st.button("🗑️ 刪除此包裹", key=f"del_{t_id}"):
                    shutil.rmtree(t_path)
                    st.rerun()

# --- Logout ---
st.sidebar.title("設定")
if st.sidebar.button("登出 / 換一個設備 ID"):
    del st.session_state['device_id']
    st.rerun()
