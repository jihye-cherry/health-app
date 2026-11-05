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
                        file_ext = uploaded_file.name.split(".")[-1]
                        saved_filename = f"req_{new_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                        saved_image_path = os.path.join(UPLOAD_DIR, saved_filename)
                        try:
                            with open(saved_image_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                        except Exception:
                            saved_image_path = ""
                    
                    new_data = {
                        "id": new_id,
                        "timestamp": now_str,
                        "type": req_type,
                        "is_secret": is_secret,
                        "writer": writer_name,
                        "password": str(password),
                        "title": title,
                        "content": content,
                        "status": "접수완료",
                        "admin_reply": "",
                        "image_path": saved_image_path,
                        "before_images_json": json.dumps([]),
                        "after_images_json": json.dumps([]),
                        "before_desc": "",
                        "after_desc": ""
                    }
                    
                    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                    save_data(df)
                    
                    st.success(f"✨ 요청이 성공적으로 접수되었습니다. (접수번호: No.{new_id})")

    with tab2:
        st.markdown("#### 📋 실시간 접수 및 조치 현황")
        st.caption("아래 표에서 항목을 클릭하시면 상세 내용과 조치 결과를 확인하실 수 있습니다.")
        
        df_list = load_data()
        if len(df_list) > 0:
            display_df = df_list[["id", "timestamp", "type", "writer", "title", "status"]].copy()
            
            for idx, row in df_list.iterrows():
                if str(row["is_secret"]) == "True" and not st.session_state["admin_logged_in"]:
                    display_df.at[idx, "writer"] = "익명 🔒"
                    display_df.at[idx, "title"] = "🔒 비밀글입니다. (권한 필요)"
            
            display_df = display_df.rename(columns={
                "id": "번호",
                "timestamp": "일시",
                "type": "문의종류",
                "writer": "작성자",
                "title": "제목",
                "status": "처리단계"
            })
            
            sorted_df = display_df.sort_values(by="번호", ascending=False).reset_index(drop=True)
            
            event = st.dataframe(
                sorted_df,
                use_container_width=True,
                selection_mode="single-row",
                on_select="rerun",
                key="clean_table_grid"
            )
            
            selected_id = None
            selection_rows = event.selection.get("rows", [])
            if len(selection_rows) > 0:
                selected_row_idx = selection_rows[0]
                selected_id = int(sorted_df.iloc[selected_row_idx]["번호"])

            st.divider()
            st.markdown("#### 🔍 상세 내용 및 피드백 확인")
            
            current_selected_id = selected_id if selected_id else st.session_state["selected_request_id"]
            
            if not current_selected_id:
                st.info("👆 위 표에서 확인할 항목의 체크박스를 선택해주세요.")
            else:
                target_rows = df_list[df_list["id"] == int(current_selected_id)]
                if len(target_rows) == 0:
                    st.warning("해당 내역을 찾을 수 없습니다.")
                else:
                    row_data = target_rows.iloc[0]
                    is_target_secret = str(row_data["is_secret"]) == "True"
                    
                    pass_check = True
                    input_pw = ""
                    if is_target_secret and not st.session_state["admin_logged_in"]:
                        input_pw = st.text_input("🔒 비밀글입니다. 비밀번호를 입력해주세요.", type="password", key=f"pw_input_{current_selected_id}")
                        if str(row_data["password"]) != str(input_pw):
                            pass_check = False
                            st.error("비밀번호가 일치하지 않습니다.")
                    elif is_target_secret and st.session_state["admin_logged_in"]:
                        st.info("🔓 [관리자 권한] 비밀글을 열람합니다.")

                    if pass_check:
                        display_writer = "익명 🔒" if is_target_secret and not st.session_state["admin_logged_in"] else row_data['writer']
                        
                        st.markdown(f"### 📌 [No.{row_data['id']}] {row_data['title']}")
                        st.caption(f"분류: {row_data['type']} | 작성자: {display_writer} | 일시: {row_data['timestamp']} | 상태: **{row_data['status']}**")
                        
                        st.markdown("##### [문의 내용]")
                        st.info(row_data['content'])
                        
                        img_path = str(row_data.get("image_path", ""))
                        if img_path != "" and os.path.exists(img_path):
                            try:
                                st.image(img_path, caption="첨부 현장 사진", width=400)
                            except Exception:
                                pass
                        
                        try:
                            b_list = json.loads(row_data.get("before_images_json", "[]"))
                        except Exception:
                            b_list = []
                        try:
                            a_list = json.loads(row_data.get("after_images_json", "[]"))
                        except Exception:
                            a_list = []
                        
                        b_desc = str(row_data.get("before_desc", ""))
                        a_desc = str(row_data.get("after_desc", ""))
                        
                        if len(b_list) > 0 or len(a_list) > 0 or b_desc != "" or a_desc != "":
                            st.markdown("---")
                            st.markdown("##### 📸 개선 전·후 비교 내역")
                            col_bi, col_ai = st.columns(2)
                            
                            with col_bi:
                                st.markdown("**[개선 전]**")
                                if len(b_list) > 0:
                                    cols_b = st.columns(min(len(b_list), 3))
                                    for idx_b, bp in enumerate(b_list):
                                        if os.path.exists(bp):
                                            with cols_b[idx_b % len(cols_b)]:
                                                try:
                                                    st.image(bp, caption=f"전-{idx_b+1}", use_container_width=True)
                                                except Exception:
                                                    pass
                                if b_desc != "":
                                    st.warning(f"💡 **조치 필요 사항:**\n{b_desc}")
                                    
                            with col_ai:
                                st.markdown("**[개선 후]**")
                                if len(a_list) > 0:
                                    cols_a = st.columns(min(len(a_list), 3))
                                    for idx_a, ap in enumerate(a_list):
                                        if os.path.exists(ap):
                                            with cols_a[idx_a % len(cols_a)]:
                                                try:
                                                    st.image(ap, caption=f"후-{idx_a+1}", use_container_width=True)
                                                except Exception:
                                                    pass
                                if a_desc != "":
                                    st.success(f"✨ **개선 조치 결과:**\n{a_desc}")

                        saved_reply = str(row_data["admin_reply"]).strip()
                        if saved_reply != "" and saved_reply != "nan":
                            st.success(f"🩺 **[보건관리자 조치 및 답변]**\n\n{saved_reply}")
                        else:
                            st.write("⏳ 현재 검토 및 조치 대기 중입니다.")
        else:
            st.write("등록된 접수 내역이 없습니다.")

# ==========================================
# [모드 2] 보건관리자 전용 모드
# ==========================================
elif menu == "🔒 보건관리자 전용 모드":
    st.title("🩺 보건관리자 전용 대시보드")

    if not st.session_state["admin_logged_in"]:
        st.markdown("#### 🔐 관리자 인증")
        admin_pw_input = st.text_input("관리자 비밀번호를 입력하세요", type="password")
        if st.button("로그인", type="primary"):
            if admin_pw_input == "dap1234%":
                st.session_state["admin_logged_in"] = True
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
    else:
        st.success("🔓 보건관리자 모드로 안전하게 접속되었습니다.")
        if st.button("로그아웃"):
            st.session_state["admin_logged_in"] = False
            st.rerun()
            
        st.divider()
        
        df_admin = load_data()
        st.markdown("#### 📊 보건 개선사례 보고서 추출")
        st.caption("안전하고 깔끔하게 정리된 엑셀(Excel) 보고서 파일을 즉시 다운로드할 수 있습니다.")
        
        if len(df_admin) > 0:
            def convert_df_to_excel(df):
                output = BytesIO()
                report_rows = []
                for _, r in df.iterrows():
                    sec_str = "공개" if str(r.get("is_secret", False)) != "True" else "비밀글"
                    report_rows.append({
                        "번호": r.get("id", 0),
                        "일시": r.get("timestamp", ""),
                        "공개여부": sec_str,
                        "문의종류": r.get("type", ""),
                        "작성자": r.get("writer", ""),
                        "제목": r.get("title", ""),
                        "내용": r.get("content", ""),
                        "처리단계": r.get("status", ""),
                        "관리자답변": r.get("admin_reply", ""),
                        "개선전설명": r.get("before_desc", ""),
                        "개선후설명": r.get("after_desc", "")
                    })
                
                df_report = pd.DataFrame(report_rows)
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_report.to_excel(writer, index=False, sheet_name='보건개선사례보고서')
                return output.getvalue()
            
            try:
                excel_data = convert_df_to_excel(df_admin)
                st.download_button(
                    label="📥 엑셀(Excel) 보고서 다운로드",
                    data=excel_data,
                    file_name=f"보건개선사례보고서_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
            except Exception as e:
                st.error(f"엑셀 생성 중 오류 발생: {e}")
            
            st.divider()
            
            st.markdown("#### 🛠️ 전체 고충 처리 및 관리")
            st.caption("표에서 항목을 선택하여 답변 작성, 처리 단계 변경, 개선 전·후 사진 등록을 진행하세요.")
            
            display_admin_df = df_admin[["id", "timestamp", "type", "writer", "title", "status"]].copy()
            display_admin_df = display_admin_df.rename(columns={
                "id": "번호",
                "timestamp": "일시",
                "type": "문의종류",
                "writer": "작성자",
                "title": "제목",
                "status": "처리단계"
            })
            
            sorted_admin_df = display_admin_df.sort_values(by="번호", ascending=False).reset_index(drop=True)
            
            admin_event = st.dataframe(
                sorted_admin_df,
                use_container_width=True,
                selection_mode="single-row",
                on_select="rerun",
                key="admin_table_grid"
            )
            
            admin_selected_id = None
            admin_selection_rows = admin_event.selection.get("rows", [])
            if len(admin_selection_rows) > 0:
                admin_selected_row_idx = admin_selection_rows[0]
                admin_selected_id = int(sorted_admin_df.iloc[admin_selected_row_idx]["번호"])
            
            current_admin_id = admin_selected_id if admin_selected_id else st.session_state["admin_selected_id"]
            
            if not current_admin_id:
                st.info("👆 위 표에서 관리할 항목의 체크박스를 선택해주세요.")
            else:
                target_rows_admin = df_admin[df_admin["id"] == int(current_admin_id)]
                if len(target_rows_admin) > 0:
                    target_row = target_rows_admin.iloc[0]
                    
                    st.markdown(f"### 📌 [No.{target_row['id']}] {target_row['title']}")
                    st.caption(f"작성자: {target_row['writer']} ({target_row['timestamp']}) | 분류: {target_row['type']}")
                    st.info(f"**[요청 내용]**\n\n{target_row['content']}")
                    
                    img_path_admin = str(target_row.get("image_path", ""))
                    if img_path_admin != "" and os.path.exists(img_path_admin):
                        try:
                            st.image(img_path_admin, caption="첨부된 현장 사진", width=400)
                        except Exception:
                            pass

                    try:
                        b_list_curr = json.loads(target_row.get("before_images_json", "[]"))
                    except Exception:
                        b_list_curr = []
                    try:
                        a_list_curr = json.loads(target_row.get("after_images_json", "[]"))
                    except Exception:
                        a_list_curr = []
                    
                    b_desc_curr = str(target_row.get("before_desc", ""))
                    a_desc_curr = str(target_row.get("after_desc", ""))

                    if len(b_list_curr) > 0 or len(a_list_curr) > 0 or b_desc_curr != "" or a_desc_curr != "":
                        st.markdown("---")
                        st.markdown("##### 📸 현재 등록된 개선 전·후 현황")
                        col_bc, col_ac = st.columns(2)
                        with col_bc:
                            st.markdown("**[개선 전]**")
                            if len(b_list_curr) > 0:
                                cb_cols = st.columns(min(len(b_list_curr), 3))
                                for i, bp in enumerate(b_list_curr):
                                    if os.path.exists(bp):
                                        with cb_cols[i % len(cb_cols)]:
                                            try:
                                                st.image(bp, caption=f"전-{i+1}", use_container_width=True)
                                            except Exception:
                                                pass
                            if b_desc_curr != "":
                                st.warning(b_desc_curr)
                        with col_ac:
                            st.markdown("**[개선 후]**")
                            if len(a_list_curr) > 0:
                                ca_cols = st.columns(min(len(a_list_curr), 3))
                                for i, ap in enumerate(a_list_curr):
                                    if os.path.exists(ap):
                                        with ca_cols[i % len(ca_cols)]:
                                            try:
                                                st.image(ap, caption=f"후-{i+1}", use_container_width=True)
                                            except Exception:
                                                pass
                            if a_desc_curr != "":
                                st.success(a_desc_curr)

                    with st.form(key=f"admin_mode_form_{current_admin_id}"):
                        current_status = target_row["status"]
                        status_list = ["접수완료", "처리중", "조치완료"]
                        status_index = status_list.index(current_status) if current_status in status_list else 0
                        
                        new_status = st.selectbox("처리 단계 변경", status_list, index=status_index)
                        existing_reply_admin = str(target_row["admin_reply"]) if pd.notna(target_row["admin_reply"]) and str(target_row["admin_reply"]) != "nan" else ""
                        new_reply = st.text_area("관리자 답변 및 조치 내용 입력", value=existing_reply_admin)
                        
                        st.divider()
                        st.markdown("##### 🛠️ 개선 전·후 사진 및 설명 등록/수정")
                        
                        col_f1, col_f2 = st.columns(2)
                        with col_f1:
                            st.markdown("**[개선 전]**")
                            before_files = st.file_uploader("개선 전 사진 다중 업로드", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"before_files_{current_admin_id}")
                            new_before_desc = st.text_area("개선 필요 사항 (문제점 입력)", value=b_desc_curr, key=f"b_desc_{current_admin_id}")
                            
                        with col_f2:
                            st.markdown("**[개선 후]**")
                            after_files = st.file_uploader("개선 후 사진 다중 업로드", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"after_files_{current_admin_id}")
                            new_after_desc = st.text_area("개선 조치 내용 (결과 입력)", value=a_desc_curr, key=f"a_desc_{current_admin_id}")

                        col_s1, col_s2 = st.columns(2)
                        with col_s1:
                            admin_save = st.form_submit_button("💾 변경사항 및 사진 저장", type="primary")
                        with col_s2:
                            admin_del = st.form_submit_button("🗑️ 이 건 삭제하기")
                            
                        if admin_save:
                            df_save_admin = load_data()
                            target_idx = df_save_admin[df_save_admin["id"] == int(current_admin_id)].index
                            if len(target_idx) > 0:
                                df_save_admin.loc[target_idx, "status"] = new_status
                                df_save_admin.loc[target_idx, "admin_reply"] = str(new_reply)
                                df_save_admin.loc[target_idx, "before_desc"] = str(new_before_desc)
                                df_save_admin.loc[target_idx, "after_desc"] = str(new_after_desc)
                                
                                try:
                                    existing_b_list = json.loads(df_save_admin.loc[target_idx, "before_images_json"].values[0])
                                except Exception:
                                    existing_b_list = []
                                try:
                                    existing_a_list = json.loads(df_save_admin.loc[target_idx, "after_images_json"].values[0])
                                except Exception:
                                    existing_a_list = []
                                
                                if before_files:
                                    for bf in before_files:
                                        b_ext = bf.name.split(".")[-1]
                                        b_filename = f"before_{current_admin_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.{b_ext}"
                                        b_path = os.path.join(UPLOAD_DIR, b_filename)
                                        try:
                                            with open(b_path, "wb") as f:
                                                f.write(bf.getbuffer())
                                            existing_b_list.append(b_path)
                                        except Exception:
                                            pass
                                
                                if after_files:
                                    for af in after_files:
                                        a_ext = af.name.split(".")[-1]
                                        a_filename = f"after_{current_admin_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.{a_ext}"
                                        a_path = os.path.join(UPLOAD_DIR, a_filename)
                                        try:
                                            with open(a_path, "wb") as f:
                                                f.write(af.getbuffer())
                                            existing_a_list.append(a_path)
                                        except Exception:
                                            pass
                                
                                df_save_admin.loc[target_idx, "before_images_json"] = json.dumps(existing_b_list)
                                df_save_admin.loc[target_idx, "after_images_json"] = json.dumps(existing_a_list)
                                
                                save_data(df_save_admin)
                                st.success("성공적으로 저장되었습니다.")
                                st.rerun()
                            
                        if admin_del:
                            df_del_admin = load_data()
                            df_del_admin = df_del_admin[df_del_admin["id"] != int(current_admin_id)]
                            save_data(df_del_admin)
                            st.warning("해당 건이 삭제되었습니다.")
                            st.rerun()
        else:
            st.write("등록된 데이터가 없습니다.")
