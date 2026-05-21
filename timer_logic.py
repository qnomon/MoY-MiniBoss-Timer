from datetime import datetime, timedelta, timezone

import pandas as pd

from constants import element_emojis, race_emojis


def load_mobs(csv_path="table.csv"):
    """Carrega CSV e retorna lista de mobs com horários convertidos para UTC-3."""
    df = pd.read_csv(csv_path)

    df.columns = [col.strip().lower() for col in df.columns]

    required_cols = {"mob", "miniatura", "mapa", "horarios", "class", "element", "race", "size"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError(
            f"Colunas obrigatórias: {', '.join(sorted(required_cols))}. "
            f"Encontradas: {', '.join(df.columns)}"
        )

    # Adiciona colunas com emojis
    df["elemento"] = df["element"].map(element_emojis).fillna("") + " " + df["element"] + " " + df["element"].map(element_emojis)
    df["races"] = df["race"].map(race_emojis).fillna("") + " " + df["race"] + " " + df["race"].map(race_emojis)

    mobs_list = []
    for _, row in df.iterrows():
        if str(row["class"]).strip().lower() != "mini-boss":
            continue

        horarios_str = str(row["horarios"])
        times = convert_times_to_utc3(horarios_str)

        mobs_list.append({
            "name": str(row["mob"]),
            "thumb": str(row["miniatura"]),
            "mapa": str(row["mapa"]),
            "times": times,
            "element": str(row["elemento"]),
            "size": str(row["size"]),
            "race": str(row["races"]),
        })

    return mobs_list


def convert_times_to_utc3(horarios_str):
    """Converte horários UTC para UTC-3."""
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
    return converted


def build_slots(mobs_list):
    """Cria dicionário de slots de 10 minutos com mobs associados."""
    slots = {h * 60 + m: [] for h in range(24) for m in (0, 10, 20, 30, 40, 50)}
    for mob in mobs_list:
        for t_str in mob["times"]:
            h, m = map(int, t_str.split(":"))
            min_of_day = h * 60 + m
            if min_of_day in slots:
                slots[min_of_day].append(mob)
    return slots


def get_ordered_slots(slots_dict, curr_min):
    """Retorna lista ordenada de slots: 2 passados, atual, e futuros."""
    all_slot_minutes = sorted(slots_dict.keys())

    # Encontra o slot atual (>= curr_min)
    current_slot_min = None
    for s in all_slot_minutes:
        if s >= curr_min:
            current_slot_min = s
            break

    base = current_slot_min if current_slot_min is not None else 1440

    past1_min = (base - 10) % 1440
    past2_min = (base - 20) % 1440

    # Slots passados (2 mais recentes)
    past_slots = []
    for s in (past1_min, past2_min):
        slot_str = f"{s // 60:02d}:{s % 60:02d}"
        past_slots.append((s, slot_str))
    past_slots.reverse()

    ordered_slots = list(past_slots)

    # Slot atual
    if current_slot_min is not None:
        slot_str = f"{current_slot_min // 60:02d}:{current_slot_min % 60:02d}"
        ordered_slots.append((current_slot_min, slot_str))

    # Slots futuros
    future_min = current_slot_min if current_slot_min is not None else -1
    future_slots = []
    for s in all_slot_minutes:
        if s > future_min and s not in (past1_min, past2_min):
            slot_str = f"{s // 60:02d}:{s % 60:02d}"
            future_slots.append((s, slot_str))
    future_slots.sort(key=lambda x: x[0])

    ordered_slots.extend(future_slots)

    return ordered_slots, current_slot_min, past1_min, past2_min


def get_current_minute():
    """Retorna minuto atual do dia no fuso UTC-3."""
    tz_brasilia = timezone(timedelta(hours=-3))
    now_local = datetime.now(tz_brasilia)
    return now_local, now_local.hour * 60 + now_local.minute
