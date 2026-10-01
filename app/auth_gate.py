import os,streamlit as st
from .services.security import verify_master_password
def require_unlock():
    if st.session_state.get('unlocked'): return True
    st.title('🔒 Personal Notes'); st.caption('Enter your master password to unlock the workspace.')
    p=st.text_input('Master password',type='password')
    if st.button('Unlock',type='primary',use_container_width=True):
        if not os.getenv('APP_PASSWORD_HASH'): st.error('APP_PASSWORD_HASH is not configured.')
        elif verify_master_password(p,os.getenv('APP_PASSWORD_HASH')):
            st.session_state.unlocked=True; st.session_state.master_password=p; st.rerun()
        else: st.error('Incorrect master password.')
    return False
