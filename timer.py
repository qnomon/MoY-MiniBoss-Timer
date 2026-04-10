import time as tm
from datetime import datetime, time, timedelta, timezone

import gspread
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ID da sua planilha Google Sheets
SPREADSHEET_ID = "1jn2HHMZd3SPOwbVnOARqTqoP5OrtdDw5VvYmdcY2WT8"
WORKSHEET_NAME = "minis"

# Configuração do fuso horário (GMT-3 para Brasil)
BRASIL_TIMEZONE = timezone(timedelta(hours=-3))

# Cache da última leitura
last_read_time = None
cached_data = None
if "time_versions" not in st.session_state:
    st.session_state.time_versions = {}


@st.cache_resource
def get_google_sheets_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(credentials)
    return gc


def load_data(force_reload=False):
    """Carrega dados do Google Sheets com cache"""
    global last_read_time, cached_data

    if not force_reload and cached_data is not None and last_read_time:
        time_since_last_read = (datetime.now() - last_read_time).total_seconds()
        if time_since_last_read < 300:
            return cached_data

    try:
        gc = get_google_sheets_client()
        sh = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sh.worksheet(WORKSHEET_NAME)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        time_columns = ["Nasce às", "Timer", "Prox."]
        for col in time_columns:
            if col in df.columns:
                df[col] = df[col].replace(["", "None", "null", "Null", "NONE"], None)

                def convert_to_time(x):
                    if pd.isna(x) or x is None:
                        return None
                    try:
                        if isinstance(x, str):
                            x = x.strip()
                            if ":" in x:
                                parts = x.split(":")
                                if len(parts) >= 2:
                                    hour = int(parts[0])
                                    minute = int(parts[1])
                                    if 0 <= hour < 24 and 0 <= minute < 60:
                                        return time(hour, minute)
                        elif isinstance(x, datetime):
                            return x.time()
                    except:
                        return None
                    return None

                df[col] = df[col].apply(convert_to_time)

        cached_data = df
        last_read_time = datetime.now()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()


def save_data(df):
    """Salva dados no Google Sheets apenas quando necessário"""
    try:
        gc = get_google_sheets_client()
        sh = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sh.worksheet(WORKSHEET_NAME)

        df_to_save = df.copy()
        time_columns = ["Nasce às", "Timer", "Prox."]

        for col in time_columns:
            if col in df_to_save.columns:
                if isinstance(df_to_save[col].iloc[0], str) and "min" in str(
                    df_to_save[col].iloc[0]
                ):
                    pass
                else:
                    df_to_save[col] = df_to_save[col].apply(
                        lambda x: (
                            x.strftime("%H:%M")
                            if isinstance(x, time) and pd.notnull(x)
                            else x
                            if pd.notnull(x)
                            else ""
                        )
                    )

        df_to_save = df_to_save.fillna("")
        data = [df_to_save.columns.tolist()] + df_to_save.values.tolist()
        worksheet.update(data, value_input_option="USER_ENTERED")
        st.success("✅ Alterações salvas com sucesso!")

        global cached_data
        cached_data = df.copy()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")
        return False


def calcular_segundos_restantes(nasce_as):
    """Calcula segundos restantes para ordenação"""
    if not nasce_as or not isinstance(nasce_as, time):
        return 10800  # 3 horas em segundos

    try:
        agora_utc = datetime.now(timezone.utc)
        agora_local = datetime.now(BRASIL_TIMEZONE)

        morte_gmt0 = datetime.combine(agora_utc.date(), nasce_as).replace(
            tzinfo=timezone.utc
        )

        if morte_gmt0 > agora_utc:
            morte_gmt0 = morte_gmt0 - timedelta(days=1)

        respawn_gmt0 = morte_gmt0 + timedelta(hours=3)
        respawn_local = respawn_gmt0.astimezone(BRASIL_TIMEZONE)
        diferenca = respawn_local - agora_local

        segundos = int(diferenca.total_seconds())
        return segundos if segundos > 0 else 0
    except Exception as e:
        return 10800


def calcular_tempo_restante_ajustado(nasce_as):
    """Calcula o tempo restante considerando GMT 0 do jogo e GMT-3 do usuário"""
    segundos = calcular_segundos_restantes(nasce_as)

    if segundos <= 0:
        return "VIVO"  # Retorna "VIVO" quando o tempo acaba

    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segundos_rest = segundos % 60

    return f"{horas:02d}:{minutos:02d}:{segundos_rest:02d}"


def calcular_horario_respawn_local(nasce_as):
    """Calcula o horário do respawn no horário local"""
    if not nasce_as or not isinstance(nasce_as, time):
        return "--:--"

    try:
        agora_utc = datetime.now(timezone.utc)
        morte_gmt0 = datetime.combine(agora_utc.date(), nasce_as).replace(
            tzinfo=timezone.utc
        )

        if morte_gmt0 > agora_utc:
            morte_gmt0 = morte_gmt0 - timedelta(days=1)

        respawn_gmt0 = morte_gmt0 + timedelta(hours=3)
        respawn_local = respawn_gmt0.astimezone(BRASIL_TIMEZONE)
        return respawn_local.strftime("%H:%M")
    except:
        return "--:--"


# Configuração da página
st.set_page_config(page_title="Mini-Boss Timer - Myth of Yggdrasil", layout="wide")
st.title("Mini-Boss Timer :blue[MoY]")
st.divider()

# CSS Global
st.markdown(
    """
<style>
    /* Container principal do card */
    .card-container {
        width: 100%;
        margin-bottom: 15px;
    }

    /* Card em si */
    .mini-card {
        border: 1px solid #444;
        border-radius: 8px;
        padding: 12px;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        height: 200px;
        display: flex;
        flex-direction: column;
        position: relative;
    }

    /* Cabeçalho do mob */
    .mob-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
        height: 45px;
    }

    /* Imagem do mob */
    .mob-image {
        width: 45px;
        height: 45px;
        border-radius: 4px;
        border: 1px solid #666;
        object-fit: cover;
        flex-shrink: 0;
    }

    /* Nome do mob */
    .mob-name {
        font-size: 0.85em;
        font-weight: bold;
        color: #4fc3f7;
        line-height: 1.2;
        flex-grow: 1;
        overflow: hidden;
    }

    .mob-name-main {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: block;
    }

    .mob-id {
        font-size: 0.7em;
        color: #888;
        display: block;
        margin-top: 2px;
    }

    /* Container do timer */
    .timer-container {
        text-align: center;
        margin: 5px 0;
        padding: 6px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 5px;
        height: 50px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .timer-label {
        font-size: 0.75em;
        color: #aaa;
        margin-bottom: 2px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .timer-value {
        font-size: 1.3em;
        font-weight: bold;
        font-family: 'Courier New', monospace;
        letter-spacing: 1px;
        line-height: 1.2;
    }

    .timer-vivo {
        color: #4CAF50;
        font-size: 1.4em;
        font-weight: bold;
        text-transform: uppercase;
    }

    .timer-green { color: #4CAF50; }
    .timer-yellow { color: #FFC107; }
    .timer-red { color: #F44336; }

    /* Informações do mapa */
    .mapa-info {
        font-size: 0.7em;
        color: #aaa;
        text-align: center;
        padding: 4px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 3px;
        margin-top: 3px;
        height: 25px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Próximo respawn */
    .next-info {
        font-size: 0.65em;
        color: #888;
        text-align: center;
        margin-top: 3px;
        height: 15px;
    }

    /* Controles abaixo do card */
    .card-controls {
        margin-top: 8px;
        width: 100%;
    }
    div.stButton > button {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
        }

        /* Ajuste específico para botões com apenas ícone (sem texto) */
        div.stButton > button > div {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Remove qualquer padding extra que desalinhe */
        div.stButton > button > div > p {
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1;
        }
</style>
""",
    unsafe_allow_html=True,
)

# Inicializar session_state para dados locais
if "dados_locais" not in st.session_state:
    df_original = load_data(force_reload=False)

    st.session_state.dados_locais = df_original.copy()

# Sidebar com controles
with st.sidebar:
    st.header("⚙️ Configurações")

    # Opções de atualização
    update_options = st.radio(
        "Atualização automática",
        ["Desligado", "1 segundo", "5 segundos", "30 segundos"],
        index=0,
    )

    update_interval = {
        "Desligado": 0,
        "1 segundo": 1,
        "5 segundos": 5,
        "30 segundos": 30,
    }[update_options]

    st.divider()

    if st.button("🗑️ Limpar todos os horários", use_container_width=True):
        for idx in range(len(st.session_state.dados_locais)):
            st.session_state.dados_locais.at[idx, "Nasce às"] = None
            st.session_state.time_versions[idx] = (
                st.session_state.time_versions.get(idx, 0) + 1
            )
        st.rerun()

    if st.button("🔄 Recarregar do Google", use_container_width=True):
        df_novo = load_data(force_reload=True)
        st.session_state.dados_locais = df_novo.copy()
        st.success("Dados recarregados do Google Sheets!")
        st.rerun()

    st.divider()

    if st.button(
        "💾 Salvar no Google Sheets", type="primary", use_container_width=True
    ):
        df_para_salvar = st.session_state.dados_locais.copy()

        for idx, row in df_para_salvar.iterrows():
            nasce_as = row.get("Nasce às")
            if nasce_as and isinstance(nasce_as, time):
                agora_utc = datetime.now(timezone.utc)
                morte_gmt0 = datetime.combine(agora_utc.date(), nasce_as).replace(
                    tzinfo=timezone.utc
                )

                if morte_gmt0 > agora_utc:
                    morte_gmt0 = morte_gmt0 - timedelta(days=1)

                timer_gmt0 = morte_gmt0 + timedelta(hours=3)
                df_para_salvar.at[idx, "Timer"] = timer_gmt0.time()

                respawn_local = timer_gmt0.astimezone(BRASIL_TIMEZONE)
                agora_local = datetime.now(BRASIL_TIMEZONE)

                if respawn_local > agora_local:
                    minutos_restantes = int(
                        (respawn_local - agora_local).total_seconds() / 60
                    )
                    df_para_salvar.at[idx, "Prox."] = f"{minutos_restantes}"
                else:
                    df_para_salvar.at[idx, "Prox."] = "0"

        if save_data(df_para_salvar):
            st.success("Dados salvos no Google Sheets!")
            st.rerun()

# Layout principal
st.markdown("### ⌚ Status dos Mini-Bosses")

# Preparar e ordenar dados
mobs_data = []
for idx, row in st.session_state.dados_locais.iterrows():
    mob = row.to_dict()
    mob["index"] = idx
    mob["segundos_restantes"] = calcular_segundos_restantes(mob.get("Nasce às"))
    mobs_data.append(mob)

# Ordenar por tempo de respawn (mais próximo primeiro, depois os vivos no final)
mobs_nao_vivos = [m for m in mobs_data if m["segundos_restantes"] > 0]
mobs_vivos = [m for m in mobs_data if m["segundos_restantes"] <= 0]
mobs_nao_vivos.sort(key=lambda x: x["Mob"])
mobs_nao_vivos.sort(key=lambda x: x["segundos_restantes"])
mobs_vivos.sort(key=lambda x: x["Mob"])
mobs_data = mobs_vivos + mobs_nao_vivos

# Layout responsivo com 4 colunas
mobs_por_linha = 6

# Organizar mobs em grid
for i in range(0, len(mobs_data), mobs_por_linha):
    cols = st.columns(mobs_por_linha)

    for j, col in enumerate(cols):
        mob_index = i + j
        if mob_index < len(mobs_data):
            mob = mobs_data[mob_index]
            idx = mob["index"]
            version = st.session_state.time_versions.get(idx, 0)

            with col:
                # Dados do mob
                mob_name = mob.get("Mob", "") or ""
                mapa = mob.get("Mapa", "") or ""
                miniatura = (
                    mob.get("Miniatura", "")
                    or "https://via.placeholder.com/45x45/333/666?text=?"
                )
                nasce_as = mob.get("Nasce às")

                # Calcular tempo restante
                tempo_restante = calcular_tempo_restante_ajustado(nasce_as)

                # Determinar cor do timer
                segundos = mob["segundos_restantes"]
                if tempo_restante == "VIVO":
                    timer_class = "timer-vivo"
                    timer_text = "VIVO"
                elif segundos < 3600:  # Menos de 1 hora
                    timer_class = "timer-red"
                    timer_text = tempo_restante
                elif segundos < 7200:  # Menos de 2 horas
                    timer_class = "timer-yellow"
                    timer_text = tempo_restante
                else:
                    timer_class = "timer-green"
                    timer_text = tempo_restante

                # Calcular próximo respawn
                next_respawn = calcular_horario_respawn_local(nasce_as)

                # Construir HTML do card em UMA ÚNICA STRING
                card_html = f"""
                <div class="card-container">
                    <div class="mini-card">
                        <div class="mob-header">
                            <img src="{miniatura}" class="mob-image" onerror="this.src='https://via.placeholder.com/45x45/333/666?text=?'">
                            <div class="mob-name">
                                <span class="mob-name-main" title="{mob_name}">{mob_name[:15]}{"..." if len(mob_name) > 15 else ""}</span>
                            </div>
                        </div>
                        <div class="timer-container">
                            <div class="timer-label">RESPAWN IN</div>
                            <div class="{timer_class}">{timer_text}</div>
                        </div>
                        <div class="mapa-info">
                            <strong>Map:</strong> {mapa[:12]}{"..." if len(mapa) > 12 else ""}
                        </div>
                        {f'<div class="next-info">Next: {next_respawn}</div>' if tempo_restante != "VIVO</div>" else ""}
                    </div>
                </div>
                """

                # Exibir card em UM ÚNICO st.markdown
                st.markdown(card_html, unsafe_allow_html=True)

                # Controles abaixo do card (fora do HTML)
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    horario_atual = nasce_as if nasce_as else time(0, 0)
                    novo_horario = st.time_input(
                        "Morreu às",
                        value=horario_atual,
                        key=f"time_input_{idx}_{version}",
                        label_visibility="collapsed",
                        step=60,
                        help="Horário da morte (GMT 0 do jogo)",
                    )

                    if novo_horario != horario_atual:
                        st.session_state.dados_locais.at[idx, "Nasce às"] = novo_horario
                        st.rerun()

                with col2:
                    if st.button(
                        "⏱️",  # ícone de relógio
                        key=f"now_{idx}_{version}",  # usa versão para evitar conflitos
                        help="Definir horário de morte para AGORA (GMT 0)",
                        use_container_width=True,
                    ):
                        # Obtém a hora atual em GMT 0 (UTC)
                        agora_utc = datetime.now(timezone.utc).time()
                        st.session_state.dados_locais.at[idx, "Nasce às"] = agora_utc

                        # Incrementa a versão para forçar o time_input a exibir o novo valor
                        st.session_state.time_versions[idx] = (
                            st.session_state.time_versions.get(idx, 0) + 1
                        )
                        st.rerun()

                with col3:
                    if st.button(
                        "🗑️",
                        key=f"clear_{idx}",
                        help="Limpar horário",
                        use_container_width=True,
                    ):
                        st.session_state.dados_locais.at[idx, "Nasce às"] = None
                        st.session_state.time_versions[idx] = (
                            st.session_state.time_versions.get(idx, 0) + 1
                        )
                        st.rerun()

# Rodapé com estatísticas
st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    mobs_ativos = sum(1 for mob in mobs_data if mob.get("Nasce às") is not None)
    st.metric("🎯 Ativos", f"{mobs_ativos}/{len(mobs_data)}")

with col2:
    count_proximos = sum(
        1
        for mob in mobs_data
        if mob["segundos_restantes"] < 3600 and mob["segundos_restantes"] > 0
    )
    st.metric("⏰ < 1h", f"{count_proximos} mobs")

with col3:
    count_vivos = sum(
        1
        for mob in mobs_data
        if mob["segundos_restantes"] <= 0 and mob.get("Nasce às") is not None
    )
    st.metric("✅ Vivos", f"{count_vivos} mobs")

with col4:
    # Status das alterações
    has_changes = any(mob.get("Nasce às") is not None for mob in mobs_data)

    if has_changes:
        st.metric("💾 Alterações", "⚠️ Não salvas")
    else:
        st.metric("💾 Alterações", "✓ Salvas")

# Informações sobre fuso horário
st.info("""
**Nota sobre fuso horário:**
- Horários são registrados em GMT 0 (horário do servidor do jogo)
- O contador ajusta automaticamente para GMT-3 (Brasil)
- 3 horas de respawn = 3 horas reais do jogo
- Quando o timer chega a 00:00:00, mostra "VIVO" em verde
""")

# Atualização automática
if update_interval > 0:
    # Mostrar quando será a próxima atualização
    next_update = datetime.now() + timedelta(seconds=update_interval)
    st.caption(f"⏰ Próxima atualização: {next_update.strftime('%H:%M:%S')}")

    # Usar time.sleep e rerun para atualizar
    tm.sleep(update_interval)
    st.rerun()
