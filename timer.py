import html

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from constants import favorite_list
from notifications import check_and_send_alerts
from timer_logic import build_slots, get_current_minute, get_ordered_slots, load_mobs

st.set_page_config(layout="wide")
st_autorefresh(interval=60000, key="refresh")

webhook_url = st.secrets.get("discord_webhook_url", "")

st.markdown(
    """
<style>
    .slot-current {
        background-color: #8ef5a7;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .slot-past {
        background-color: #ff96a0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .slot-past2 {
        background-color: #fcf492;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .slot-future {
        background-color: #8daaf2;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .mobs-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
    }
    .mob-card {
        background: linear-gradient(135deg, #1b1e29 0%, #36485c 100%);
        border-radius: 10px;
        padding: 8px;
        width: 190px;
        color: white;
        font-size: 14px;
        display: flex;
        align-items: center;
    }
    .mob-card-gold {
        background-image: url('https://i.imgur.com/WNEp9aQ.png');
        background-size: cover;
        border-radius: 10px;
        padding: 8px;
        width: 190px;
        color: white;
        font-size: 14px;
        display: flex;
        align-items: center;
    }
    .mob-card img, .mob-card-gold img {
        max-width: 45px;
        max-height: 45px;
        object-fit: contain;
        margin-right: 10px;
    }
    .mob-name {
        color: #f2cb07;
        font-weight: bold;
    }
    .mob-name-especial {
        color: #cc08cc;
        font-weight: bold;
    }
    .mob-map {
        color: #888888;
        font-size: 12px;
    }
    details.mob-details {
        cursor: pointer;
    }
    details.mob-details summary {
        list-style: none;
    }
    details.mob-details summary::-webkit-details-marker {
        display: none;
    }
    .mob-info {
        background: rgba(0,0,0,0.7);
        border-radius: 6px;
        padding: 6px;
        margin-top: 6px;
        font-size: 13px;
    }
    .header_image {
        width: 100%;
        aspect-ratio: 16 / 6;
        background-image: url('https://i.imgur.com/Ad4ogYX.png');
        background-size: cover;
        background-position: center 40%;
        background-repeat: no-repeat;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""",
    unsafe_allow_html=True,
)

st.html("""<div class="header_image"></div>""")
st.title("Agenda de Mobs (UTC-3)")

try:
    mobs_list = load_mobs("table.csv")
except FileNotFoundError:
    st.error("Arquivo 'table.csv' não encontrado. Coloque-o no mesmo diretório do script.")
    st.stop()
except ValueError as e:
    st.error(str(e))
    st.stop()

# Notificações Discord
check_and_send_alerts(mobs_list, favorite_list, webhook_url)

# Constrói slots e obtém horário atual
slots_dict = build_slots(mobs_list)
now_local, curr_min = get_current_minute()
ordered_slots, current_slot_min, past1_min, past2_min = get_ordered_slots(slots_dict, curr_min)

# Botão expandir/colapsar todos
if "all_expanded" not in st.session_state:
    st.session_state.all_expanded = True
if st.button("Abrir/Fechar todos os horários"):
    st.session_state.all_expanded = not st.session_state.all_expanded

# Exibição dos slots
for slot_min, slot_str in ordered_slots:
    mobs = slots_dict[slot_min]

    if current_slot_min is not None and slot_min == current_slot_min:
        css_class = "slot-current"
    elif slot_min == past2_min:
        css_class = "slot-past"
    elif slot_min == past1_min:
        css_class = "slot-past2"
    else:
        css_class = "slot-future"

    with st.expander(f"{slot_str} — {len(mobs)} mob(s)", expanded=st.session_state.all_expanded):
        if not mobs:
            slot_html = f'<div class="{css_class}">Nenhum mob nesse horário.</div>'
        else:
            cards_html = ""
            for mob in mobs:
                if mob["name"] in favorite_list:
                    card_class = "mob-card-gold"
                    name_class = "mob-name-especial"
                else:
                    card_class = "mob-card"
                    name_class = "mob-name"

                card = f"""
                    <details class="mob-details">
                        <summary>
                            <div class="{html.escape(card_class)}"
                                 title="Elemento: {html.escape(mob["element"])} | Raça: {html.escape(mob["race"])} | Tamanho: {html.escape(mob["size"])}">
                                <img src="{html.escape(mob["thumb"])}"
                                     onerror="this.style.display='none'"
                                     alt="miniatura">
                                <div style="display:flex; flex-direction:column;">
                                    <span class="{html.escape(name_class)}">{html.escape(mob["name"])}</span>
                                    <span class="mob-map">{html.escape(mob["mapa"])}</span>
                                </div>
                            </div>
                        </summary>
                        <div class="mob-info">
                            🔥 <b>Elemento:</b> {html.escape(mob["element"])}<br>
                            🧬 <b>Raça:</b> {html.escape(mob["race"])}<br>
                            📏 <b>Tamanho:</b> {html.escape(mob["size"])}
                        </div>
                    </details>
                """
                cards_html += card.strip()

            slot_html = f'<div class="{css_class}"><div class="mobs-grid">{cards_html}</div></div>'

        st.markdown(slot_html, unsafe_allow_html=True)
