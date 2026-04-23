import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")
st.title("Tabela elemental")


@st.cache_data
def load_data():
    return pd.read_csv("table.csv")


df = load_data()

# Mapeamento de emojis para elementos
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

# Criar coluna com emoji + nome (para exibição) e manter a original para filtros
df["Elemento"] = df["Element"].map(element_emojis).fillna("") + " " + df["Element"]

# ---------- FILTROS ACIMA DA TABELA ----------
st.subheader("Filtros")

col1, col2, col3 = st.columns(3)

with col1:
    elementos = sorted(df["Element"].dropna().unique())
    selected_elementos = st.multiselect(
        "Elemento",
        options=elementos,
        default=[],
        help="Filtrar por elemento (múltiplos permitidos)",
    )

with col2:
    racas = sorted(df["Race"].dropna().unique())
    selected_racas = st.multiselect(
        "Raça", options=racas, default=[], help="Filtrar por raça"
    )

with col3:
    tamanhos = sorted(df["Size"].dropna().unique())
    selected_tamanhos = st.multiselect(
        "Tamanho", options=tamanhos, default=[], help="Filtrar por tamanho"
    )

# Aplicar filtros
df_filtrado = df.copy()
if selected_elementos:
    df_filtrado = df_filtrado[df_filtrado["Element"].isin(selected_elementos)]
if selected_racas:
    df_filtrado = df_filtrado[df_filtrado["Race"].isin(selected_racas)]
if selected_tamanhos:
    df_filtrado = df_filtrado[df_filtrado["Size"].isin(selected_tamanhos)]

# Mostrar contagem de resultados
st.caption(f"**Resultados: {len(df_filtrado)} monstros**")

# ---------- TABELA PRINCIPAL ----------
st.data_editor(
    df_filtrado,
    column_config={
        "Miniatura": st.column_config.ImageColumn("Miniatura"),
        "Elemento": st.column_config.Column("Elemento", help="Elemento com emoji"),
        "Size": st.column_config.Column("Tamanho", help="Tamanho do monstro"),
        "Element": None,  # oculta a coluna original
        "Horarios": None,
    },
    use_container_width=True,
    height=600,
    hide_index=True,
)
