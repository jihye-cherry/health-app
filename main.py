import streamlit as st
import pandas as pd
import os
from datetime import datetime
import json
from io import BytesIO

st.set_page_config(
    page_title="사내 보건관리 & 고충 시스템",
    page_icon="🏥",
    layout="wide"
)

DATA_FILE = "health_requests.csv"
UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def load_data():
    if not os.path.exists(DATA_FILE):
        df_init = pd.DataFrame(columns=[
            "id", "timestamp", "type", "is_secret", 
            "writer", "password", "title", "content", "status", "admin_reply", "image_path",
            "before_images_json", "after_images_json", "before_desc", "after_desc"
        ])
        df_init.to_csv(DATA_FILE, index=False)
        return df_init
    
    try:
        df = pd.read_csv(DATA_FILE)
    except Exception:
        df = pd.DataFrame(columns=[
            "id", "timestamp", "type", "is_secret", 
            "writer", "password", "title", "content", "status", "admin_reply", "image_path",
            "before_images_json", "after_images_json", "before_desc", "after_desc"
        ])
    
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

# 사이드바 메뉴
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

if st.sidebar.get("admin_logged_in", False) or st.session_state["admin_logged_in"]:
    st.sidebar.success("🔓 [관리자 인증됨]")

# ==========================================
# [모드 1] 접수 및 조회
# ==========================================
if menu == "📝 보건 요청 접수 및 조회":
    st.title("🏥 사내 보건 요청 & 고충 창구")
    st.markdown("임직원 여러분의 안전하고 건강한 근무 환경을 위해 의견을 남겨주세요.")
    st.divider()
    
    tab1, tab2 = st.tabs(["📝 새로운 요청 접수", "📋 전체 접수 및 처리 현황"])
    
    with tab1:
        st.markdown("#### ✍️ 고충 및 개선 요청 작성")
        with st.form("request_form", clear_on_submit=True):
            req_type = st.selectbox("요청 유형", ["보호구 및 약품 신청", "작업환경 개선 요청", "건강상담 신청", "기타"])
            is_secret = st.checkbox("🔒 비밀글 설정")
            
            col1, col2 = st.columns(2)
            with col1:
                writer_name = st.text_input("작성자 성명", placeholder="예: 박지혜")
            with col2:
                password = st.text_input("비밀번호", type="password")

            title = st.text_input("제목")
            content = st.text_area("상세 내용")
            uploaded_file = st.file_uploader("📸 사진 첨부 (선택)", type=["jpg", "jpeg", "png"])
            
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
                        try:
                            file_ext = uploaded_file.name.split(".")[-1]
                            saved_filename = f"req_{new_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                            saved_image_path = os.path.join(UPLOAD_DIR, saved_filename)
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
                    st.success(f"✨ 요청이 접수되었습니다. (접수번호: No.{new_id})")

    with tab2:
        st.markdown("#### 📋 실시간 접수 및 조치 현황")
        df_list = load_data()
        
        if len(df_list) > 0:
            display_df = df_list[["id", "timestamp", "type", "writer", "title", "status"]].copy()
            
            for idx, row in df_list.iterrows():
                if str(row["is_secret"]) == "True" and not st.session_state["admin_logged_in"]:
                    display_df.at[idx, "writer"] = "익명 🔒"
                    display_df.at[idx, "title"] = "🔒 비밀글입니다."
            
            display_df = display_df.rename(columns={
                "id": "번호", "timestamp": "일시", "type": "문의종류", 
                "writer": "작성자", "title": "제목", "status": "처리단계"
            })
            
            sorted_df = display_df.sort_values(by="번호", ascending=False).reset_index(drop=True)
            
            event = st.dataframe(sorted_df, use_container_width=True, selection_mode="single-row", on_select="rerun", key="grid_1")
            
            selected_id = None
            rows = event.selection.get("rows", [])
            if len(rows) > 0:
                selected_id = int(sorted_df.iloc[rows[0]]["번호"])

            st.divider()
            st.markdown("#### 🔍 상세 내용 확인")
            
            if not selected_id:
                st.info("👆 위 표에서 확인할 항목을 클릭해주세요.")
            else:
                target = df_list[df_list["id"] == int(selected_id)]
                if len(target) > 0:
                    r = target.iloc[0]
                    is_sec = str(r["is_secret"]) == "True"
                    
                    pass_ok = True
                    if is_sec and not st.session_state["admin_logged_in"]:
                        pw_in = st.text_input("🔒 비밀번호 입력", type="password", key="pwd_check")
                        if str(r["password"]) != str(pw_in):
                            pass_ok = False
                            st.error("비밀번호가 틀렸습니다.")
                    
                    if pass_ok:
                        st.markdown(f"### 📌 [No.{r['id']}] {r['title']}")
                        st.caption(f"분류: {r['type']} | 작성자: {r['writer']} | 상태: **{r['status']}**")
                        st.info(r['content'])
                        
                        if r['image_path'] and os.path.exists(str(r['image_path'])):
                            try:
                                st.image(r['image_path'], width=400)
                            except Exception:
                                pass
                                
                        if str(r['admin_reply']).strip() and str(r['admin_reply']) != "nan":
                            st.success(f"🩺 **[관리자 답변]**\n\n{r['admin_reply']}")
                        else:
                            st.write("⏳ 검토 대기 중입니다.")
        else:
            st.write("등록된 접수 내역이 없습니다.")

# ==========================================
# [모드 2] 관리자 모드
# ==========================================
elif menu == "🔒 보건관리자 전용 모드":
    st.title("🩺 보건관리자 전용 대시보드")

    if not st.session_state["admin_logged_in"]:
        pw = st.text_input("관리자 비밀번호", type="password")
        if st.button("로그인", type="primary"):
            if pw == "dap1234%":
                st.session_state["admin_logged_in"] = True
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("비밀번호 오류")
    else:
        if st.button("로그아웃"):
            st.session_state["admin_logged_in"] = False
            st.rerun()
            
        st.divider()
        df_admin = load_data()
        
        if len(df_admin) > 0:
            def make_excel(df):
                output = BytesIO()
                rep = []
                for _, r in df.iterrows():
                    rep.append({
                        "번호": r.get("id", 0), "일시": r.get("timestamp", ""),
                        "문의종류": r.get("type", ""), "작성자": r.get("writer", ""),
                        "제목": r.get("title", ""), "내용": r.get("content", ""),
                        "처리단계": r.get("status", ""), "관리자답변": r.get("admin_reply", "")
                    })
                dfr = pd.DataFrame(rep)
                with pd.ExcelWriter(output, engine='openpyxl') as w:
                    dfr.to_excel(w, index=False, sheet_name='보고서')
                return output.getvalue()
            
            try:
                st.download_button(
                    "📥 엑셀(Excel) 보고서 다운로드",
                    data=make_excel(df_admin),
                    file_name=f"보건보고서_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
            except Exception as e:
                st.error(f"엑셀 다운로드 오류: {e}")
                
            st.divider()
            st.markdown("#### 🛠️ 고충 처리 및 관리")
            
            adm_display = df_admin[["id", "timestamp", "type", "writer", "title", "status"]].rename(columns={
                "id": "번호", "timestamp": "일시", "type": "문의종류", "writer": "작성자", "title": "제목", "status": "처리단계"
            }).sort_values(by="번호", ascending=False).reset_index(drop=True)
            
            ev = st.dataframe(adm_display, use_container_width=True, selection_mode="single-row", on_select="rerun", key="grid_2")
            
            sel_id = None
            rows2 = ev.selection.get("rows", [])
            if len(rows2) > 0:
                sel_id = int(adm_display.iloc[rows2[0]]["번호"])
                
            if sel_id:
                row_target = df_admin[df_admin["id"] == int(sel_id)]
                if len(row_target) > 0:
                    rt = row_target.iloc[0]
                    st.markdown(f"### 📌 [No.{rt['id']}] {rt['title']}")
                    st.info(rt['content'])
                    
                    with st.form(key=f"form_{sel_id}"):
                        st_list = ["접수완료", "처리중", "조치완료"]
                        curr_st = rt["status"]
                        idx = st_list.index(curr_st) if curr_st in st_list else 0
                        
                        new_st = st.selectbox("처리 단계", st_list, index=idx)
                        reply_txt = st.text_area("관리자 답변", value=str(rt["admin_reply"]) if pd.notna(rt["admin_reply"]) and str(rt["admin_reply"]) != "nan" else "")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            save_btn = st.form_submit_button("💾 저장하기", type="primary")
                        with col_b:
                            del_btn = st.form_submit_button("🗑️ 삭제하기")
                            
                        if save_btn:
                            df_s = load_data()
                            idx_s = df_s[df_s["id"] == int(sel_id)].index
                            if len(idx_s) > 0:
                                df_s.loc[idx_s, "status"] = new_st
                                df_s.loc[idx_s, "admin_reply"] = reply_txt
                                save_data(df_s)
                                st.success("저장 완료!")
                                st.rerun()
                                
                        if del_btn:
                            df_d = load_data()
                            df_d = df_d[df_d["id"] != int(sel_id)]
                            save_data(df_d)
                            st.warning("삭제되었습니다.")
                            st.rerun()
        else:
            st.write("등록된 데이터가 없습니다.")
