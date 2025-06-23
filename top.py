import streamlit as st

st.set_page_config(page_title="宝くじAI予想", layout="wide")

st.image("https://raw.githubusercontent.com/Naobro/lototop-app/main/header.png", use_container_width=True)

st.markdown("## 🎯 宝くじAI予想サイト")
st.markdown("AIで未来の当選数字を予測。高額当選者も続出中！")

st.markdown("### 💰 高額当選実績")
st.markdown("""
- **2022年4月8日** ロト7 3等　➡️ **801,300円**
- **2024年10月4日** ナンバーズ4 セットストレート　➡️ **558,000円**
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.page_link("pages/loto6_top.py", label="🔵 ロト6")
    st.page_link("pages/loto7_top.py", label="🟣 ロト7")

with col2:
    st.page_link("pages/miniloto_top.py", label="🟢 ミニロト")
    st.page_link("pages/numbers3_top.py", label="🟡 ナンバーズ3")

with col3:
    st.page_link("pages/numbers4_top.py", label="🟠 ナンバーズ4")
