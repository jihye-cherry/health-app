import streamlit as st
import pandas as pd
import os
from datetime import datetime
import json
from io import BytesIO

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="사내 보건관리 & 고충 시스템",
    page_icon="🏥",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #F8F9FA;
    }
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = "health_requests.csv"
UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def init_csv():
    if not os.path.exists(DATA_FILE):
        df_init = pd.DataFrame(columns=[
            "id", "timestamp", "type", "is_secret", 
            "writer", "password", "title", "content", "status", "admin_reply", "image_path",
            "before_images_json", "after_images_json", "before_desc", "after_desc"
        ])
        df_init.to_csv(DATA_FILE, index=False)

init_csv()

def load_data():
    if not os.path.exists(DATA_FILE):
        init_csv()
    try:
        df = pd.read_csv(DATA_FILE)
    except Exception:
        init_csv()
        df = pd.read_csv(DATA_FILE)
    
    expected_columns = [
        "id", "timestamp", "type", "is_secret", 
        "writer", "password", "title", "content", "status", "admin_reply", "image_path",
        "before_images_json", "after_images_json", "before_desc", "after_desc"
    ]
    for col in expected_columns:
        if col not in df.columns:
            df[col] = ""
            
    if len(df) > 0:
        df["id"] = pd.to_numeric(df["id"], errors='coerce').fillna(0).astype(int)
        
    for col in ["admin_reply", "image_path", "before_images_json", "after_images_json", "before_desc", "after_desc"]:
        df[col] = df[col].fillna("").astype(str)
        
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

if "selected_request_id" not in st.session_state:
    st.session_state["selected_request_id"] = None

if "admin_selected_id" not in st.session_state:
    st.session_state["admin_selected_id"] = None

# 로고 불러오기
logo_found = False
for logo_name in ["Logo.png", "logo.jpg", "로고.png", "로고.jpg"]:
    if os.path.exists(logo_name):
        st.sidebar.image(logo_name, width=170)
        logo_found = True
        break

if not logo_found:
    st.sidebar.title("🏥 Health Portal")

st.sidebar.caption("사내 보건관리 및 개선 시스템")
st.sidebar.divider()

menu = st.sidebar.radio("메뉴 탐색", ["📝 보건 요청 접수 및 조회", "🔒 보건관리자 전용 모드"])

st.sidebar.divider()
if st.session_state["admin_logged_in"]:
    st.sidebar.success("🔓 [관리자 인증 완료]")

# ==========================================
# [모드 1] 보건 요청 접수 및 조회
# ==========================================
if menu == "📝 보건 요청 접수 및 조회":
    st.title("🏥 사내 보건 요청 & 고충 창구")
    st.markdown("임직원 여러분의 안전하고 건강한 근무 환경을 위해 언제든 의견을 남겨주세요.")
    
    st.divider()
    
    tab1, tab2 = st.tabs(["📝 새로운 요청 접수", "📋 전체 접수 및 처리 현황"])
    
    with tab1:
        st.markdown("#### ✍️ 고충 및 개선 요청 작성")
        with st.form("request_form", clear_on_submit=True):
            req_type = st.selectbox(
                "요청 유형",
                ["보호구 및 약품 신청", "작업환경 개선 요청", "건강상담 신청", "기타"]
            )
            
            is_secret = st.checkbox("🔒 비밀글 설정 (작성자 및 관리자만 열람 가능)")
            
            col1, col2 = st.columns(2)
            with col1:
                writer_name = st.text_input("작성자 성명", placeholder="예: 박지혜")
            with col2:
                password = st.text_input("비밀번호 (조회/비밀글용)", type="password", placeholder="숫자 4자리 등")

            title = st.text_input("제목", placeholder="간결하고 명확한 제목을 입력해주세요.")
            content = st.text_area("상세 내용", placeholder="현장 위치, 필요한 물품, 불편 사항 등을 상세히 적어주세요.")
            
            uploaded_file = st.file_uploader("📸 현장 사진 첨부 (선택)", type=["jpg", "jpeg", "png"])
            
            submitted = st.form_submit_button("요청 제출하기", type="primary")

            if submitted:
                if not title or not content or not writer_name:
                    st.error("성명, 제목, 상세 내용은 필수 입력 항목입니다.")
                else:
                    df = load_data()
                    new_id = int(df["id"].max()) + 1 if len(df) > 0 and not df["id"].empty else 1
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    saved_image_path = ""
                    if uploaded_file is not None:
                        file_
