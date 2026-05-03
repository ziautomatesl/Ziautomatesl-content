import os
import random
import time
from groq import Groq
from topics import TEMAS

def generate_script(topic=None, max_retries=3):
    if not topic:
        topic = random.choice(TEMAS)

    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": f"""Eres ZIA, el robot asistente de ZIAutomate, agencia de automatización con IA para pequeños negocios en España.

Crea un guión de 40-50 segundos para un video de Instagram Reels sobre: "{topic}"

Reglas estrictas:
- Habla en primera persona como ZIA el robot, tono cercano y directo
- Explica el tema de forma que cualquier empresario lo entienda sin tecnicismos
- Usa un ejemplo concreto real
- Termina con: "Escríbeme por WhatsApp o entra en ziautomate.netlify.app"
- Solo el texto que se va a decir, sin corchetes ni indicaciones de escena
- Máximo 100 palabras

Tema: {topic}"""
                }]
            )
            script = response.choices[0].message.content.strip()
            return {
                "topic": topic,
                "script": script,
                "hashtags": "#automatizacion #inteligenciaartificial #ia #negocio #emprendedor #ziautomate #pymes #españa #robotia"
            }
        except Exception as e:
            print(f"Intento {attempt + 1} fallido: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise
