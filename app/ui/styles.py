import streamlit as st
def inject_css():
    st.markdown('''<style>
    .block-container{max-width:1250px;padding-top:1.2rem}.muted{opacity:.68;font-size:.88rem}
    @media(max-width:700px){.block-container{padding:.7rem .7rem 4rem}}
    </style>''',unsafe_allow_html=True)
