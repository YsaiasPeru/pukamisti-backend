import os
import sys

# Añadir el backend al path para poder importar
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database.connection import engine, SessionLocal
from app.database.models import PukaCard

cards_data = [
    {"name": "Sol", "category": "NATURALEZA", "rarity": "EPIC", "description": "Fuente de luz y energía para el mundo andino."},
    {"name": "Agua", "category": "NATURALEZA", "rarity": "COMMON", "description": "Elemento vital para la vida y los cultivos."},
    {"name": "Montaña", "category": "NATURALEZA", "rarity": "RARE", "description": "Los Apus, guardianes sagrados de las alturas."},
    {"name": "Árbol", "category": "NATURALEZA", "rarity": "COMMON", "description": "Pulmón de la tierra y refugio de aves."},
    {"name": "Llama", "category": "NATURALEZA", "rarity": "RARE", "description": "Compañera fiel y símbolo de los Andes."},
    {"name": "Cóndor", "category": "NATURALEZA", "rarity": "LEGENDARY", "description": "El rey de los cielos andinos, símbolo de libertad."},
    {"name": "Flor Andina", "category": "NATURALEZA", "rarity": "COMMON", "description": "Llena de color los paisajes fríos."},
    {"name": "Papa", "category": "NATURALEZA", "rarity": "COMMON", "description": "Alimento ancestral que nutre a nuestra gente."},
    
    {"name": "Respeto", "category": "VALORES", "rarity": "COMMON", "description": "Tratar a los demás y a la naturaleza con amor."},
    {"name": "Amistad", "category": "VALORES", "rarity": "COMMON", "description": "Compañerismo puro y sincero."},
    {"name": "Honestidad", "category": "VALORES", "rarity": "RARE", "description": "Decir la verdad siempre ilumina el camino."},
    {"name": "Solidaridad", "category": "VALORES", "rarity": "EPIC", "description": "Ayudar a quien lo necesita sin pedir nada a cambio."},
    {"name": "Gratitud", "category": "VALORES", "rarity": "COMMON", "description": "Decir gracias con el corazón."},
    {"name": "Paciencia", "category": "VALORES", "rarity": "RARE", "description": "Saber esperar el momento adecuado, como la cosecha."},
    {"name": "Empatía", "category": "VALORES", "rarity": "RARE", "description": "Comprender los sentimientos de los demás."},
    {"name": "Perseverancia", "category": "VALORES", "rarity": "EPIC", "description": "Nunca rendirse, incluso en la subida más empinada."},

    {"name": "Historia Andina", "category": "CONOCIMIENTOS", "rarity": "RARE", "description": "Las raíces de nuestra gran cultura."},
    {"name": "Cusco", "category": "CONOCIMIENTOS", "rarity": "EPIC", "description": "El ombligo del mundo y capital histórica."},
    {"name": "Machu Picchu", "category": "CONOCIMIENTOS", "rarity": "LEGENDARY", "description": "La maravilla del mundo, joya de la ingeniería Inca."},
    {"name": "Tejido Andino", "category": "CONOCIMIENTOS", "rarity": "RARE", "description": "Colores e historias entrelazadas con habilidad."},
    {"name": "Cerámica", "category": "CONOCIMIENTOS", "rarity": "COMMON", "description": "Arte moldeado con tierra y fuego."},
    {"name": "Música Andina", "category": "CONOCIMIENTOS", "rarity": "COMMON", "description": "El sonido del viento a través de la quena."},
    {"name": "Calendario Andino", "category": "CONOCIMIENTOS", "rarity": "RARE", "description": "La sabiduría de medir el tiempo por el sol y la luna."},
    {"name": "Idioma Quechua", "category": "CONOCIMIENTOS", "rarity": "COMMON", "description": "El idioma de nuestros ancestros: ¡Allin Kausay!"},

    {"name": "Creatividad", "category": "HABILIDADES", "rarity": "RARE", "description": "Crear mundos nuevos con tu mente."},
    {"name": "Pensamiento Crítico", "category": "HABILIDADES", "rarity": "EPIC", "description": "Cuestionar y aprender a pensar por ti mismo."},
    {"name": "Comunicación", "category": "HABILIDADES", "rarity": "COMMON", "description": "Expresar tus ideas claramente y escuchar."},
    {"name": "Trabajo en Equipo", "category": "HABILIDADES", "rarity": "COMMON", "description": "Juntos logramos metas más grandes."},
    {"name": "Liderazgo", "category": "HABILIDADES", "rarity": "EPIC", "description": "Inspirar a otros a hacer el bien."},
    {"name": "Organización", "category": "HABILIDADES", "rarity": "COMMON", "description": "Mantener el orden para avanzar mejor."},
    {"name": "Resolución de Problemas", "category": "HABILIDADES", "rarity": "RARE", "description": "Encontrar la solución incluso en la tormenta."},
    {"name": "Autocuidado", "category": "HABILIDADES", "rarity": "COMMON", "description": "Amar y cuidar de tu propio cuerpo y mente."},

    {"name": "Semilla", "category": "NATURALEZA", "rarity": "COMMON", "description": "El inicio de una nueva vida."},
    {"name": "Energía Solar", "category": "NATURALEZA", "rarity": "RARE", "description": "El poder renovable del dios Inti."},
    {"name": "Reciclaje", "category": "NATURALEZA", "rarity": "COMMON", "description": "Dar una segunda vida a las cosas."},
    {"name": "Biodiversidad", "category": "NATURALEZA", "rarity": "EPIC", "description": "La riqueza de nuestra flora y fauna."},
    
    {"name": "Ritual Andino", "category": "CONOCIMIENTOS", "rarity": "EPIC", "description": "Nuestra ofrenda a la Pachamama."},
    {"name": "Mi Comunidad", "category": "VALORES", "rarity": "COMMON", "description": "La fuerza del ayllu unido."},
    {"name": "Sueños", "category": "HABILIDADES", "rarity": "RARE", "description": "Imaginar un futuro sin límites."},
    {"name": "Futuro Sostenible", "category": "NATURALEZA", "rarity": "LEGENDARY", "description": "Proteger nuestro hogar para las próximas generaciones."}
]

def run_seed():
    print("Conectando a la base de datos...")
    
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE puka_cards ADD COLUMN category VARCHAR DEFAULT 'NATURALEZA';"))
            print("Columna 'category' añadida a puka_cards.")
        except Exception as e:
            if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                print("La columna 'category' ya existe, omitiendo ALTER TABLE.")
            else:
                print("Error al alterar la tabla (quizá ya tenga la columna):", e)

    db = SessionLocal()
    try:
        print("Borrando cartas existentes (si hay) para cargar la Colección de 40...")
        db.query(PukaCard).delete()
        db.commit()

        print(f"Insertando {len(cards_data)} cartas...")
        for i, c_data in enumerate(cards_data):
            # El código será algo como CARD-001
            code = f"CARD-{str(i+1).zfill(3)}"
            card = PukaCard(
                code=code,
                name=c_data["name"],
                description=c_data["description"],
                rarity=c_data["rarity"],
                category=c_data["category"]
            )
            db.add(card)
        db.commit()
        print("¡Colección completa insertada exitosamente!")
    except Exception as e:
        print("Hubo un error:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
