import streamlit as st

# st.caption(f"by: _Qnomon_")
pg = st.navigation(
    [
        st.Page("timer.py", title="Timer", icon="⏱️"),
        st.Page("elements.py", title="Elementos", icon="🔥"),
        st.Page("ferramentas.py", title="Ferramentas", icon="🛠️"),
        st.Page("drops.py", title="Drops", icon="📦"),
    ]
)
pg.run()
