import html
import json
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh


@st.cache_resource
def get_sent_alerts():
    """
    Retorna um dicionário compartilhado entre todas as sessões.
    Chave:  "NomeDoMob_2026-04-28T01:40:00-03:00"
    Valor:  timestamp UNIX de quando o alerta foi enviado.
    """
    return {}


SENT_ALERTS = get_sent_alerts()

st.set_page_config(layout="wide")
st_autorefresh(interval=60000, key="refresh")
webhook_url = "https://discord.com/api/webhooks/1498535746082967753/GLW1cUAzjNHCgjYJBRfJ_Qojl3Ayw9oBerPLLRJLvSWaPGhtCubegOSPBuC2IEg4qbNR"
favoriteList = [
    "Ju-On",
    "Tiki Kanaloa",
    "Shiosen",
    "Byrogue",
    "Vodyanoy",
    "Vagabond Wolf",
    "Sludge Abomination",
    "Iskralisa",
    "Twisted Twilight",
    "Silver Thief Bug",
    "Vocal",
    "Angeling",
    "Blightwalker",
]

# 🎨 Estilos CSS
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
        /*background: linear-gradient(135deg, #7700ff 0%, #05d3fc 100%);*/
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
        list-style: none; /* remove o triângulo padrão */
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
        background-position: center 40%;  /* Ajuste para o texto da sua imagem */
        background-repeat: no-repeat;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""",
    unsafe_allow_html=True,
)

st.html("""<div class="header_image">

</div>
""")
# with st.container(horizontal_alignment="center"):
#    st.image("https://i.imgur.com/Ad4ogYX.png", width=600)
st.title("Agenda de Mobs (UTC-3)")

uploaded_file = "table.csv"

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except FileNotFoundError:
        st.error(
            f"Arquivo '{uploaded_file}' não encontrado. Coloque-o no mesmo diretório do script."
        )
        st.stop()
    element_emojis = {
        "Fire": "🔥",
        "Water": "💧",
        "Earth": "🌱",
        "Wind": "💨",
        "Holy": "✨",
        "Shadow": "🌑",
        "Corrupt": "💀",
        "Neutral": "⚪",
        "Ghost": "👻",
        "Poison": "🟪",
    }

    race_emojis = {
        "DemiHuman": "👤",
        "Angel": "😇",
        "Insect": "🐛",
        "Plant": "🌱",
        "Demon": "😈",
        "Brute": "🐻",
        "Undead": "💀",
        "Dragon": "🐲",
        "Fish": "🐟",
        "Formless": "⚪",
    }

    # Criar coluna com emoji + nome (para exibição) e manter a original para filtros
    df["Elemento"] = (
        df["Element"].map(element_emojis).fillna("")
        + " "
        + df["Element"]
        + " "
        + df["Element"].map(element_emojis)
    )
    df["Races"] = (
        df["Race"].map(race_emojis).fillna("")
        + " "
        + df["Race"]
        + " "
        + df["Race"].map(race_emojis)
    )

    df.columns = [col.strip().lower() for col in df.columns]
    required_cols = {
        "mob",
        "miniatura",
        "mapa",
        "horarios",
        "class",
        "element",
        "race",
        "size",
    }
    if not required_cols.issubset(set(df.columns)):
        st.error(
            f"Colunas obrigatórias: Mob, Miniatura, Mapa, Horarios, Class, Element, Race, Size.\n"
            f"Encontradas: {', '.join(df.columns)}"
        )
    else:
        # Processa dados
        mobs_list = []
        for _, row in df.iterrows():
            if str(row["class"]).strip().lower() == "mini-boss":
                mob_name = str(row["mob"])
                thumb = str(row["miniatura"])
                mapa = str(row["mapa"])
                horarios_str = str(row["horarios"])
                element = str(row["elemento"])
                size = str(row["size"])
                race = str(row["races"])

                # UTC → UTC-3
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
                    {
                        "name": mob_name,
                        "thumb": thumb,
                        "mapa": mapa,
                        "times": converted,
                        "element": element,
                        "size": size,
                        "race": race,
                    }
                )

        # Cria slots de 10 min
        slots_dict_min = {
            h * 60 + m: [] for h in range(24) for m in (0, 10, 20, 30, 40, 50)
        }
        for mob in mobs_list:
            for t_str in mob["times"]:
                h, m = map(int, t_str.split(":"))
                min_of_day = h * 60 + m
                if min_of_day in slots_dict_min:
                    slots_dict_min[min_of_day].append(mob)

        # Horário atual (UTC-3) - faça ASSIM:
        tz_brasilia = timezone(timedelta(hours=-3))
        now_local = datetime.now(tz_brasilia)
        curr_min = now_local.hour * 60 + now_local.minute
        # Inicializa memória de alertas enviados (sessão atual)

        # Verifica monstros favoritos que estão prestes a nascer
        if webhook_url:  # só envia se a URL foi configurada
            now_ts = time.time()
            to_delete = [
                k for k, ts in SENT_ALERTS.items() if now_ts - ts > 2 * 24 * 3600
            ]
            for k in to_delete:
                del SENT_ALERTS[k]

            for mob in mobs_list:
                if mob["name"] not in favoriteList:
                    continue

                # Converte os horários locais (UTC-3) para minutos do dia
                times_min = []
                for t_str in mob["times"]:
                    try:
                        h, m = map(int, t_str.split(":"))
                        times_min.append(h * 60 + m)
                    except:
                        continue

                if not times_min:
                    continue

                # Próximo spawn a partir de agora (considera virada de dia)
                future_times = [t for t in times_min if t >= curr_min]
                if future_times:
                    next_spawn_min = min(future_times)
                    spawn_date = now_local.date()
                else:
                    next_spawn_min = min(times_min)  # primeiro do dia seguinte
                    spawn_date = now_local.date() + timedelta(days=1)

                # Monta a data/hora exata do spawn (UTC-3)
                spawn_h = next_spawn_min // 60
                spawn_m = next_spawn_min % 60
                spawn_dt = datetime(
                    spawn_date.year,
                    spawn_date.month,
                    spawn_date.day,
                    spawn_h,
                    spawn_m,
                    tzinfo=timezone(timedelta(hours=-3)),
                )

                # Minutos até o spawn
                time_until = int((spawn_dt - now_local).total_seconds() / 60)

                # Se estiver dentro da janela de 0 a 10 minutos
                if 0 <= time_until <= 10:
                    # Chave única por spawn (monstro + data/hora exata)
                    alert_key = f"{mob['name']}_{spawn_dt.isoformat()}"

                    if alert_key not in SENT_ALERTS:
                        # Monta mensagem para o Discord
                        spawn_time_str = f"{spawn_h:02d}:{spawn_m:02d}"

                        embed = {
                            "title": f"⚠️ {mob['name']} vai nascer em {time_until} min!",
                            "description": (
                                f"**Mapa:** {mob['mapa']}\n"
                                f"**Horário:** {spawn_time_str} (UTC-3)\n"
                                f"**Data:** {spawn_date.strftime('%d/%m/%Y')}"
                            ),
                            "color": 0xF2CB07,  # dourado
                            "thumbnail": {"url": mob["thumb"]},
                            "fields": [
                                {
                                    "name": "🔥 Elemento",
                                    "value": mob["element"],
                                    "inline": True,
                                },
                                {
                                    "name": "🧬 Raça",
                                    "value": mob["race"],
                                    "inline": True,
                                },
                                {
                                    "name": "📏 Tamanho",
                                    "value": mob["size"],
                                    "inline": True,
                                },
                            ],
                        }
                        payload = {"embeds": [embed]}

                        try:
                            response = requests.post(webhook_url, json=payload)
                            if response.status_code == 204:
                                SENT_ALERTS[alert_key] = time.time()
                            else:
                                st.warning(
                                    f"Erro ao enviar alerta: {response.status_code}"
                                )
                        except Exception as e:
                            st.warning(f"Falha na conexão com Discord: {e}")

        # 1) Encontra o próximo slot (>= curr_min)
        all_slot_minutes = sorted(slots_dict_min.keys())  # 0, 10, 20, ..., 1430
        current_slot_min = None
        for s in all_slot_minutes:
            if s >= curr_min:
                current_slot_min = s
                break

        # 2) Define os dois slots passados mais recentes
        if current_slot_min is not None:
            base = current_slot_min
        else:
            # curr_min está após 23:50 → base virtual = 1440 (00:00 do dia seguinte)
            base = 1440

        past1_min = (base - 10) % 1440
        past2_min = (base - 20) % 1440

        # 3) Constrói a lista ordenada
        ordered_slots = []
        past_slots = []
        for s in (past1_min, past2_min):
            if s in slots_dict_min:  # sempre estará
                slot_str = f"{s // 60:02d}:{s % 60:02d}"
                past_slots.append((s, slot_str))
        past_slots.reverse()
        ordered_slots.extend(past_slots)

        # Slot atual (se existir no dia)
        if current_slot_min is not None:
            slot_str = f"{current_slot_min // 60:02d}:{current_slot_min % 60:02d}"
            ordered_slots.append((current_slot_min, slot_str))

        # Slots futuros (todos > current_slot_min, exceto os que já são passados)
        future_slots = []
        if current_slot_min is not None:
            future_min = current_slot_min
        else:
            future_min = (
                -1
            )  # para incluir todos os slots do dia como futuros (se não há atual)

        for s in all_slot_minutes:
            if s > future_min and s not in (past1_min, past2_min):
                slot_str = f"{s // 60:02d}:{s % 60:02d}"
                future_slots.append((s, slot_str))

        future_slots.sort(key=lambda x: x[0])  # ordem crescente

        # Slots passados (apenas os dois mais recentes)

        # past1 é o mais recente, portanto deve vir primeiro
        # Como inserimos na ordem (past1, past2), já está correto.

        ordered_slots.extend(future_slots)

        # Botão expandir todos
        if "all_expanded" not in st.session_state:
            st.session_state.all_expanded = True
        if st.button("Abrir/Fechar todos os horários"):
            st.session_state.all_expanded = not st.session_state.all_expanded

        # Exibição dos slots
        for slot_min, slot_str in ordered_slots:
            mobs = slots_dict_min[slot_min]
            favorite = ""
            text = ""

            # Define classe do container
            if current_slot_min is not None and slot_min == current_slot_min:
                css_class = "slot-current"
            elif slot_min == (past2_min):
                css_class = "slot-past"
            elif slot_min == (past1_min):
                css_class = "slot-past2"
            else:
                css_class = "slot-future"

            with st.expander(
                f"{slot_str} — {len(mobs)} mob(s)",
                expanded=st.session_state.all_expanded,
            ):
                if not mobs:
                    slot_html = (
                        f'<div class="{css_class}">Nenhum mob nesse horário.</div>'
                    )
                else:
                    cards_html = ""
                    for mob in mobs:
                        if mob["name"] in favoriteList:
                            favorite = "mob-card-gold"
                            text = "mob-name-especial"
                        else:
                            favorite = "mob-card"
                            text = "mob-name"
                        card = f"""
                                <details class="mob-details">
                                    <summary>
                                        <div class={html.escape(favorite)}
                                             title="Elemento: {html.escape(mob["element"])} | Raça: {html.escape(mob["race"])} | Tamanho: {html.escape(mob["size"])}">
                                            <img src="{html.escape(mob["thumb"])}"
                                                 onerror="this.style.display='none'"
                                                 alt="miniatura">
                                            <div style="display:flex; flex-direction:column;">
                                                <span class={html.escape(text)}>{html.escape(mob["name"])}</span>
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
                        cards_html += card.strip()  # remove espaços extras de cada card

                    # Container em linha única (sem quebra antes do <div>)
                    slot_html = f'<div class="{css_class}"><div class="mobs-grid">{cards_html}</div></div>'

                st.markdown(slot_html, unsafe_allow_html=True)

else:
    st.info(
        "Faça upload de um arquivo CSV com as colunas: Mob, Miniatura, Mapa, Horarios, Class, Element, Race, Size."
    )
