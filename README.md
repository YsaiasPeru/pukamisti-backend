# Puka Miski Backend

Este es el backend de Puka Miski construido con FastAPI y conectado a una base de datos PostgreSQL en Neon.

## 🐛 Registro de Errores Comunes y Soluciones (Troubleshooting)
Para evitar problemas en el futuro o en otros entornos, aquí documentamos los errores encontrados durante el setup inicial:

1. **Problemas con psycopg2 en Python recientes (ej. 3.14)**
   - **Error**: `Failed building wheel for psycopg2-binary`.
   - **Solución**: Usar la versión más moderna `psycopg[binary]` (psycopg3). Para que SQLAlchemy lo reconozca automáticamente, el string de conexión debe empezar con `postgresql+psycopg://` en lugar de sólo `postgresql://`.

2. **Conflictos de nombres al usar __init__.py en carpetas**
   - **Error**: `ImportError: cannot import name 'User' from 'app.database.models'`.
   - **Causa**: Crear por accidente una carpeta llamada `models/` justo al lado del archivo `models.py`. Python intenta importar la carpeta vacía en lugar del archivo.
   - **Solución**: Asegurarse de no tener carpetas y archivos con el mismo nombre en el mismo nivel si ambos actúan como módulos.

3. **Pydantic y EmailStr**
   - **Error**: `ImportError: email-validator is not installed, run pip install 'pydantic[email]'`.
   - **Solución**: El uso de `EmailStr` en los esquemas requiere que se instale `email-validator`. Se soluciona ejecutando `pip install email-validator`.
