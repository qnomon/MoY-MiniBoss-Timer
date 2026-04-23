import html
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Atualiza automaticamente a cada 60 segundos
st_autorefresh(interval=60000, key="refresh")

st.set_page_config(layout="wide")

# Estilos CSS customizados
st.markdown(
    """
<style>
    .mob-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 8px;
        margin: 5px 0;
        display: flex;
        align-items: center;
        color: white;
        font-size: 14px;
    }
    .mob-card img {
        max-width: 45px;
        max-height: 45px;
        object-fit: contain;
        margin-right: 10px;
    }
    .mob-name {
        color: #ffd500;
        font-weight: bold;
    }
    .mob-map {
        color: #FFD700;
        font-size: 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title("Agenda de Mobs")

uploaded_file = "table.csv"

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = [col.strip().lower() for col in df.columns]

    required_cols = {"mob", "miniatura", "mapa", "horarios"}
    if not required_cols.issubset(set(df.columns)):
        st.error(
            f"Colunas obrigatórias: Mob, Miniatura, Mapa, Horarios. Encontradas: {', '.join(df.columns)}"
        )
    else:
        # Processa os dados
        mobs_list = []
        for _, row in df.iterrows():
            mob_name = str(row["mob"])
            thumb = str(row["miniatura"])
            mapa = str(row["mapa"])
            horarios_str = str(row["horarios"])

            # Converte UTC → UTC-3
            times_utc = [t.strip() for t in horarios_str.split(",") if t.strip()]
            converted = []
            for t in times_utc:
                try:
                    h, m = map(int, t.split(":"))
                    total_min = (h * 60 + m - 3 * 60) % (24 * 60)
                    new_h = total_min // 60
                    new_m = total_min % 60
                    converted.append(f"{new_h:02d}:{new_m:02d}")
                except ValueError:
                    continue
            mobs_list.append(
                {"name": mob_name, "thumb": thumb, "mapa": mapa, "times": converted}
            )

        # Cria slots de 10 em 10 min
        all_slots = []
        slots_dict = {}
        for h in range(24):
            for m in (0, 10, 20, 30, 40, 50):
                slot = f"{h:02d}:{m:02d}"
                all_slots.append(slot)
                slots_dict[slot] = []

        for mob in mobs_list:
            for t in mob["times"]:
                if t in slots_dict:
                    slots_dict[t].append(mob)

        # Horário atual (UTC-3) e cálculo do slot corrente
        now_utc = datetime.now(timezone.utc)
        now_local = now_utc - timedelta(hours=3)
        current_min = now_local.hour * 60 + now_local.minute
        current_slot_min = (current_min // 10) * 10
        current_slot = f"{current_slot_min // 60:02d}:{current_slot_min % 60:02d}"

        # Ordena os slots: slot atual primeiro, depois futuros (a partir do próximo), depois passados
        upcoming = []
        past = []
        for slot in all_slots:
            if slot == current_slot:
                continue  # será inserido manualmente no topo
            h, m = map(int, slot.split(":"))
            slot_min = h * 60 + m
            if slot_min >= current_slot_min + 10:  # próximos horários
                upcoming.append(slot)
            else:  # horários já passados
                past.append(slot)

        upcoming.sort()  # mais próximo primeiro
        past.sort(reverse=True)  # passado mais recente primeiro
        sorted_slots = [current_slot] + upcoming + past

        # Inicializa o estado do botão "expandir todos"
        if "all_expanded" not in st.session_state:
            st.session_state.all_expanded = False

        # Botão para abrir/fechar todos os dropdowns
        if st.button("Abrir/Fechar todos os horários"):
            st.session_state.all_expanded = not st.session_state.all_expanded

        # Exibe cada slot em um expander
        for slot in sorted_slots:
            mobs = slots_dict[slot]
            with st.expander(
                f"{slot} — {len(mobs)} mob(s)",
                expanded=st.session_state.all_expanded,
            ):
                if not mobs:
                    st.write("Nenhum mob nesse horário.")
                else:
                    # Linhas de até 4 cards
                    for i in range(0, len(mobs), 4):
                        cols = st.columns(4)
                        for j in range(4):
                            idx = i + j
                            if idx < len(mobs):
                                mob = mobs[idx]
                                card_html = f"""
                                <div class="mob-card">
                                    <img src="{html.escape(mob["thumb"])}"
                                         onerror="this.style.display='none'"
                                         alt="miniatura">
                                    <div style="display:flex; flex-direction:column;">
                                        <span class="mob-name">{html.escape(mob["name"])}</span>
                                        <span class="mob-map">{html.escape(mob["mapa"])}</span>
                                    </div>
                                </div>
                                """
                                with cols[j]:
                                    st.markdown(card_html, unsafe_allow_html=True)
else:
    st.info(
        "Faça upload de um arquivo CSV com as colunas: Mob, Miniatura, Mapa, Horarios."
    )
