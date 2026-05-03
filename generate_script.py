import random
from datetime import date
from scripts_bank import SCRIPTS

def generate_script(topic=None):
    # Usa la fecha para elegir script de forma predecible (2 por día)
    day_of_year = date.today().timetuple().tm_yday
    slot_index = (day_of_year * 2) % len(SCRIPTS)

    # Alterna entre dos scripts por día según si es mañana o tarde
    # main.py pasa "morning" o "evening" pero aquí simplemente rotamos
    script_data = SCRIPTS[slot_index % len(SCRIPTS)]

    return {
        "topic": script_data["topic"],
        "script": script_data["script"],
        "hashtags": "#automatizacion #inteligenciaartificial #ia #negocio #emprendedor #ziautomate #pymes #españa #robotia"
    }
