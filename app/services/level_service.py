def calculate_level(total_points: int) -> str:
    if total_points < 100:
        return "🌱 Semilla Saludable"
    elif total_points < 300:
        return "🩸 Aprendiz del Hierro"
    elif total_points < 600:
        return "⚔️ Guerrero del Hierro"
    elif total_points < 1000:
        return "🏔️ Guardián de los Andes"
    else:
        return "👑 Maestro Puka"
