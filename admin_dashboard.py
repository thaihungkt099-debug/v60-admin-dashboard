import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import json

st.set_page_config(page_title="V60 MagnaRise - Admin", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .main-title {font-size: 32px; font-weight: bold; color: #008080;}
    .sub-title {font-size: 16px; color: #555555; margin-bottom: 25px;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 V60 MAGNARISE - TRẠM CHỈ HUY QUẢN TRỊ</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Hệ thống quản lý người dùng, phân quyền Premium và giám sát dữ liệu</div>', unsafe_allow_html=True)

@st.cache_resource
def init_firebase():
    try:
        # Hệ thống sẽ đọc chìa khóa bảo mật từ Két sắt (Secrets) của Streamlit
        key_dict = json.loads(st.secrets["firebase_key"])
        cred = credentials.Certificate(key_dict)
        return firebase_admin.initialize_app(cred)
    except ValueError:
        return firebase_admin.get_app()
    except Exception as e:
        st.error(f"Lỗi khởi tạo Firebase: {e}")
        return None

app = init_firebase()

if app:
    db = firestore.client()
    
    def load_users():
        users_ref = db.collection('users')
        docs = users_ref.stream()
        user_list = []
        for doc in docs:
            data = doc.to_dict()
            uid = doc.id
            email = data.get('email', 'Chưa cung cấp')
            account_type = data.get('account_type', 'free')
            monthly_budget = data.get('monthly_budget', 0)
            user_list.append({
                "User UID": uid,
                "Email": email,
                "Loại tài khoản": account_type.upper(),
                "Hạn mức tháng": monthly_budget
            })
        return pd.DataFrame(user_list)
        
    df_users = load_users()
    
    if not df_users.empty:
        col1, col2, col3 = st.columns(3)
        total = len(df_users)
        premium = len(df_users[df_users["Loại tài khoản"] == "PREMIUM"])
        col1.metric("👥 Tổng người dùng", f"{total}")
        col2.metric("⭐ Tài khoản PREMIUM", f"{premium}")
        col3.metric("🌱 Tài khoản FREE", f"{total - premium}")
        
        st.markdown("---")
        st.subheader("📝 Danh sách tài khoản hệ thống")
        st.dataframe(df_users, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🔐 Kích hoạt gói Premium (Thu phí)")
        
        with st.form("activation_form"):
            col_user, col_role = st.columns([2, 1])
            with col_user:
                options = {f"{r['Email']} ({r['User UID']})": r['User UID'] for _, r in df_users.iterrows()}
                selected_label = st.selectbox("Chọn tài khoản:", list(options.keys()))
                selected_uid = options[selected_label]
            with col_role:
                selected_role = st.selectbox("Cấp quyền:", ["free", "premium"])
                
            if st.form_submit_button("⚡ Xác nhận"):
                db.collection('users').document(selected_uid).set({'account_type': selected_role}, merge=True)
                st.success(f"Cập nhật tài khoản sang {selected_role.upper()} thành công! Vui lòng tải lại trang.")
    else:
        st.warning("Chưa có dữ liệu người dùng.")
