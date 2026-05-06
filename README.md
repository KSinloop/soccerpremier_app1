#  Soccer Premier Juárez - Portal y Panel Administrativo

Repositorio oficial del sistema de gestión para la liga Soccer Premier Juárez.

---

##  Guía de Instalación y Ejecución 

Sigue estos pasos exactamente en orden para levantar el proyecto en tu computadora local sin errores.

### 1. Clonar el repositorio y entrar a la carpeta

```bash
git clone https://github.com/KSinloop/soccerpremier_app1.git
cd soccerpremier_app1
```
Si no especificas que se guarde en el escritorio o donde sea que te sea fácil encontrarlo, se guardara en tu user de windows

### 2. Activar el Entorno Virtual (.venv)

El entorno virtual es una "burbuja" donde instalamos las librerías del proyecto para que no choquen con otras cosas en tu compu.
Primero lo de python
```bash
python -m venv .venv
```

**En Windows:**

```bash
.\.venv\Scripts\activate
```

> **Nota:** Si PowerShell te marca un error de permisos en rojo, escribe `cmd` para cambiar de consola e intenta con `.venv\Scripts\activate.bat`.

**En Mac/Linux:**

```bash
source .venv/bin/activate
```

### 3. Instalar dependencias

Asegúrate de ver el `(.venv)` al inicio de tu terminal antes de correr esto:

```bash
pip install -r requirements.txt --no-cache-dir
```

> Si te marca errores de que faltan librerías como `dotenv`, instálalas manual:
> ```bash
> pip install python-dotenv flask-sqlalchemy flask-login
> ```

### 4. Inicializar la Base de Datos y Crear tu Usuario

Como usamos SQLAlchemy, no necesitamos importar archivos `.sql` sueltos. El código crea la base de datos automáticamente.

```bash
# 1. Crea el archivo de la base de datos (soccerpremier.db)
python -m flask init-db

# 2. Crea tu usuario administrador (cambia los datos por los tuyos)
python -m flask crear-admin tu_nombre tu_contraseña
```

### 5. Levantar el servidor en Modo Debug

Siempre utilicen este comando para trabajar. El `--debug` hace que cualquier cambio que guardes en el HTML o en Python se actualice solo, sin tener que apagar y prender la terminal:

```bash
python -m flask run --debug
```

Entra a [http://127.0.0.1:5000/](http://127.0.0.1:5000/) en tu navegador.

---

##  ¿Cómo están organizadas las carpetas?

Para que no se pierdan buscando dónde modificar el código, esta es la estructura:

| Archivo / Carpeta | Descripción |
|---|---|
| `app.py` | El corazón del proyecto. Aquí se arranca el servidor. |
| `config.py` y `db.py` | Configuraciones de seguridad y conexión a la base de datos. |
| `models.py` | **Importante** Aquí están las tablas de la base de datos escritas en código Python. Modificar esto equivale a modificar el SQL. |
| `routes/` | **(Backend)** Aquí está la lógica y las direcciones URL. |
| `routes/auth.py` | Maneja el login y las sesiones. |
| `routes/admin.py` | Lo que puede hacer el administrador (rutas protegidas). |
| `routes/public.py` | Lo que ve cualquier usuario normal. |
| `templates/` | **(Frontend - HTML)** Las pantallas visuales divididas en `admin` y `public`. |
| `static/` | **(Estilos)** Todo el CSS y JavaScript de diseño. |

---

