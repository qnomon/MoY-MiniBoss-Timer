def hard_def(base_dmg, h_def, reducao_flat=0, reducao_percent=0):
    final_hdef = (h_def - reducao_flat) * (1 - reducao_percent / 100)
    dano_final = base_dmg * ((4000 + final_hdef) / (4000 + final_hdef * 10))
    return dano_final


def hard_mdef(base_dmg, m_def, reducao_flat=0, reducao_percent=0):
    final_mdef = (m_def - reducao_flat) * (1 - reducao_percent / 100)
    dano_final = base_dmg * ((1000 + final_mdef) / (1000 + final_mdef * 10))
    return dano_final


def variable_cast(base, reducao_flat, reducao_percent, int_val, dex):
    stat = 1 - (((dex * 2) + int_val) / 470)
    rate = 1 - (reducao_percent / 100)
    vct_final = (base * stat * rate) - reducao_flat
    return max(vct_final, 0)


def blitz_beat(base_dmg, skill_lvl, base_lvl):
    dmg = 100 + (skill_lvl * 30) + (base_lvl * 3)
    dmg = base_dmg * (dmg / 100)
    return dmg
