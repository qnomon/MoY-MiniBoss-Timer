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
    .slot-current {
        background-color: #d4edda;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    .slot-past {
        background-color: #f8d7da;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    .slot-future {
        /* fundo padrão do Streamlit */
    }
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
        color: #f2cb07;
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

st.title("Agenda de Mobs (UTC-3)")

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
            if row["class"] == "Mini-Boss":
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

        # Cria slots de 10 em 10 min (00:00 a 23:50)
        all_slots = []  # lista de strings
        slots_dict_min = {}  # chave = minutos do dia (0-1430)
        for h in range(24):
            for m in (0, 10, 20, 30, 40, 50):
                slot_str = f"{h:02d}:{m:02d}"
                all_slots.append(slot_str)
                slots_dict_min[h * 60 + m] = []

        # Preenche os slots com os mobs
        for mob in mobs_list:
            for t_str in mob["times"]:
                h, m = map(int, t_str.split(":"))
                min_of_day = h * 60 + m
                if min_of_day in slots_dict_min:
                    slots_dict_min[min_of_day].append(mob)

        # Horário atual (UTC-3) em minutos
        now_utc = datetime.now(timezone.utc)
        now_local = now_utc - timedelta(hours=3)
        curr_min = now_local.hour * 60 + now_local.minute

        # Início da janela de 20 minutos (slot que será destacado)
        if curr_min < 10:
            bucket_start = 1430  # 23:50 (final do dia anterior)
        else:
            bucket_start = ((curr_min - 10) // 20) * 20 + 10

        # Classifica e ordena os slots
        current_slot = None
        future_slots = []  # (minutos, string)
        past_slots = []  # (minutos, string)

        for slot_min in sorted(slots_dict_min.keys()):
            if slot_min == bucket_start:
                current_slot = (slot_min, f"{slot_min // 60:02d}:{slot_min % 60:02d}")
            elif slot_min > bucket_start:
                future_slots.append(
                    (slot_min, f"{slot_min // 60:02d}:{slot_min % 60:02d}")
                )
            else:  # slot_min < bucket_start
                past_slots.append(
                    (slot_min, f"{slot_min // 60:02d}:{slot_min % 60:02d}")
                )

        # Ordena: futuro → crescente, passado → decrescente
        future_slots.sort(key=lambda x: x[0])
        past_slots.sort(key=lambda x: x[0], reverse=True)

        # Monta a lista final: atual, futuros, passados
        ordered_slots = []
        if current_slot:
            ordered_slots.append(current_slot)
        ordered_slots.extend(future_slots)
        ordered_slots.extend(past_slots)

        # Botão expandir/colapsar
        if "all_expanded" not in st.session_state:
            st.session_state.all_expanded = False

        if st.button("Abrir/Fechar todos os horários"):
            st.session_state.all_expanded = not st.session_state.all_expanded

        # Exibe cada slot
        for slot_min, slot_str in ordered_slots:
            mobs = slots_dict_min[slot_min]

            # Define a classe CSS
            if slot_min == bucket_start:
                css_class = "slot-current"
            elif slot_min < bucket_start:
                css_class = "slot-past"
            else:
                css_class = "slot-future"

            with st.expander(
                f"{slot_str} — {len(mobs)} mob(s)",
                expanded=st.session_state.all_expanded,
            ):
                with st.markdown(
                    f"<div class={html.escape(css_class)}>", unsafe_allow_html=True
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
                st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info(
        "Faça upload de um arquivo CSV com as colunas: Mob, Miniatura, Mapa, Horarios."
    )
