import time
from datetime import datetime, timedelta, timezone

import requests
import streamlit as st


@st.cache_resource
def get_sent_alerts():
    """Dicionário compartilhado entre sessões para rastrear alertas enviados."""
    return {}


def check_and_send_alerts(mobs_list, favorite_list, webhook_url):
    """Verifica monstros favoritos prestes a nascer e envia alerta no Discord."""
    if not webhook_url:
        return

    sent_alerts = get_sent_alerts()
    tz_brasilia = timezone(timedelta(hours=-3))
    now_local = datetime.now(tz_brasilia)
    curr_min = now_local.hour * 60 + now_local.minute

    # Limpa alertas antigos (>2 dias)
    now_ts = time.time()
    to_delete = [k for k, ts in sent_alerts.items() if now_ts - ts > 2 * 24 * 3600]
    for k in to_delete:
        del sent_alerts[k]

    for mob in mobs_list:
        if mob["name"] not in favorite_list:
            continue

        times_min = []
        for t_str in mob["times"]:
            try:
                h, m = map(int, t_str.split(":"))
                times_min.append(h * 60 + m)
            except ValueError:
                continue

        if not times_min:
            continue

        # Próximo spawn a partir de agora
        future_times = [t for t in times_min if t >= curr_min]
        if future_times:
            next_spawn_min = min(future_times)
            spawn_date = now_local.date()
        else:
            next_spawn_min = min(times_min)
            spawn_date = now_local.date() + timedelta(days=1)

        spawn_h = next_spawn_min // 60
        spawn_m = next_spawn_min % 60
        spawn_dt = datetime(
            spawn_date.year, spawn_date.month, spawn_date.day,
            spawn_h, spawn_m, tzinfo=tz_brasilia,
        )

        time_until = int((spawn_dt - now_local).total_seconds() / 60)

        if 0 <= time_until <= 10:
            alert_key = f"{mob['name']}_{spawn_dt.isoformat()}"

            if alert_key not in sent_alerts:
                spawn_time_str = f"{spawn_h:02d}:{spawn_m:02d}"
                embed = {
                    "title": f"⚠️ {mob['name']} vai nascer em {time_until} min!",
                    "description": (
                        f"**Mapa:** {mob['mapa']}\n"
                        f"**Horário:** {spawn_time_str} (UTC-3)\n"
                        f"**Data:** {spawn_date.strftime('%d/%m/%Y')}"
                    ),
                    "color": 0xF2CB07,
                    "thumbnail": {"url": mob["thumb"]},
                    "fields": [
                        {"name": "🔥 Elemento", "value": mob["element"], "inline": True},
                        {"name": "🧬 Raça", "value": mob["race"], "inline": True},
                        {"name": "📏 Tamanho", "value": mob["size"], "inline": True},
                    ],
                }
                payload = {"embeds": [embed]}

                try:
                    response = requests.post(webhook_url, json=payload)
                    if response.status_code == 204:
                        sent_alerts[alert_key] = time.time()
                    else:
                        st.warning(f"Erro ao enviar alerta: {response.status_code}")
                except Exception as e:
                    st.warning(f"Falha na conexão com Discord: {e}")
