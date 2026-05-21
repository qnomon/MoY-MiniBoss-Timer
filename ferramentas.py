import streamlit as st

import utils

st.title("Ferramentas")

col_esq, col_dir = st.columns(2)

with col_esq:
    with st.container(border=True):
        st.subheader("Calculadora de VCT")

        col1, col2, col3 = st.columns(3)

        with col1:
            base = st.number_input("VCT Base", min_value=0)
            vct_flat = st.number_input("VCT Flat", min_value=0.0, step=0.1, format="%.2f")

        with col2:
            vct_percent = st.number_input("VCT Percentual (%)", min_value=0, step=1)
            int_val = st.number_input("INT", min_value=0, step=1)

        with col3:
            dex = st.number_input("Dex", min_value=0, step=1)
            calcular_vct = st.button("Calcular VCT", key="btn_vct", type="primary")

        if calcular_vct:
            vct = utils.variable_cast(base, vct_flat, vct_percent, int_val, dex)
            st.success(f"VCT restante: **{max(vct, 0):.2f}**")

with col_dir:
    with st.container(border=True):
        st.subheader("🛡️ Calculadora de Hard Def")

        col_a, col_b = st.columns(2)

        with col_a:
            base_dmg = st.number_input("Dano Base", min_value=0, step=1)
            h_def = st.number_input("Hard DEF do Alvo", min_value=0, step=1)

        with col_b:
            reducao_flat = st.number_input("Redução Flat", min_value=0, step=1)
            reducao_percent = st.number_input("Redução Percentual (%)", min_value=0, step=1)

        calcular_def = st.button("Calcular Dano", key="btn_def", type="primary")

        if calcular_def:
            dmg = utils.hard_def(base_dmg, h_def, reducao_flat, reducao_percent)
            st.success(f"Dano causado: **{dmg:.2f}**")

with col_esq:
    with st.container(border=True):
        st.subheader("🛡️🪄 Calculadora de Hard MDef")

        col_a1, col_b1 = st.columns(2)

        with col_a1:
            base_mdmg = st.number_input("Dano Base", min_value=0, step=1, key="magical")
            h_mdef = st.number_input("Hard MDEF do Alvo", min_value=0, step=1)

        with col_b1:
            reducao_mflat = st.number_input("Redução Flat", min_value=0, step=1, key="reducao")
            reducao_mpercent = st.number_input("Redução Percentual (%)", min_value=0, step=1, key="reducao_percent")

        calcular_mdef = st.button("Calcular Dano", key="btn_mdef", type="primary")

        if calcular_mdef:
            mdmg = utils.hard_mdef(base_mdmg, h_mdef, reducao_mflat, reducao_mpercent)
            st.success(f"Dano causado: **{mdmg:.2f}**")
