# Despliegue paso a paso — InsurData (Seguro en Cifras)

Sigue estos pasos en orden. Al final tendrás el dashboard en una URL pública.

---

## Fase 1: Preparar el código y GitHub

### Paso 1.1 — Tener el proyecto listo en tu PC

- Tu dashboard está en la carpeta del proyecto (por ejemplo `sudeaseg-dashboard`).
- Debe tener al menos: `Inicio.py`, `config/`, `src/`, `pages/`, `requirements.txt`.
- El archivo `.env` **no** se sube a GitHub (debe estar en `.gitignore`).

### Paso 1.2 — Crear un repositorio en GitHub

1. Entra en [github.com](https://github.com) e inicia sesión.
2. Clic en **"+"** (arriba derecha) → **"New repository"**.
3. **Repository name:** por ejemplo `insurdata-dashboard` o `sudeaseg-dashboard`.
4. Elige **Public**.
5. No marques "Add a README" si ya tienes el proyecto en tu PC (vas a subir la carpeta).
6. Clic en **"Create repository"**.

### Paso 1.3 — Subir el código desde tu PC

Abre **PowerShell** o **Terminal** en la carpeta del dashboard (donde está `Inicio.py`):

```powershell
cd ruta\a\sudeaseg-dashboard
git init
git add .
git commit -m "Dashboard InsurData listo para despliegue"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

- Sustituye `TU_USUARIO` por tu usuario de GitHub y `TU_REPO` por el nombre del repositorio.
- Si ya tenías `git init` y `remote`, solo haz:
  ```powershell
  git add .
  git commit -m "Preparar despliegue"
  git push origin main
  ```

---

## Fase 2: Comprobar Supabase

### Paso 2.1 — Schema `anuario` expuesto en la API

1. Entra en tu proyecto en [supabase.com](https://supabase.com).
2. **Settings** (ícono engranaje) → **API**.
3. En **Exposed schemas** (o "Schema" de la API) asegúrate de que esté marcado **`anuario`** además de `public`.
4. Guarda si cambias algo.

### Paso 2.2 — Anotar URL y clave

1. En la misma pantalla de **API** verás:
   - **Project URL** (algo como `https://xxxxx.supabase.co`) → esta es tu **SUPABASE_URL**.
   - **Project API keys** → **anon public** → esta es la que usarás como **SUPABASE_KEY** en el despliegue (recomendado para solo lectura).
2. Copia y guárdalos en un lugar seguro (los usarás en el Paso 3.4).

---

## Fase 3: Desplegar en Streamlit Community Cloud

### Paso 3.1 — Entrar en Streamlit Cloud

1. Abre [https://share.streamlit.io](https://share.streamlit.io).
2. Clic en **"Sign up with GitHub"** (o "Log in" si ya tienes cuenta).
3. Autoriza a Streamlit para acceder a tu GitHub.

### Paso 3.2 — Crear una nueva app

1. En la página principal de Streamlit Cloud, clic en **"New app"**.
2. En **"Create a new app"**:
   - **Repository:** elige tu usuario y el repo (ej. `tu-usuario/insurdata-dashboard`).
   - **Branch:** `main`.
   - **Main file path:** escribe **`Inicio.py`** (porque ese es el archivo de entrada del dashboard).
3. (Opcional) En **"App URL"** puedes poner algo como: `insurdata-seguro-en-cifras` para que la URL sea `https://insurdata-seguro-en-cifras.streamlit.app`.

### Paso 3.3 — Abrir la configuración de Secrets

1. Antes de desplegar, abre **"Advanced settings"** (debajo del formulario).
2. Verás un cuadro de texto **"Secrets"**. Ahí va la configuración de Supabase.

### Paso 3.4 — Poner los Secrets (Supabase)

En el cuadro **Secrets** pega exactamente esto, **sustituyendo** por tus datos reales:

```toml
SUPABASE_URL = "https://TU_PROYECTO.supabase.co"
SUPABASE_KEY = "tu_anon_key_aqui"
```

- **SUPABASE_URL:** la Project URL que anotaste en el Paso 2.2.
- **SUPABASE_KEY:** la clave **anon public** (no la service_role en producción si solo es lectura).

Ejemplo (con valores inventados):

```toml
SUPABASE_URL = "https://abcdefgh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

No dejes espacios raros ni comillas extra. Guarda (o deja el cuadro abierto hasta pulsar Deploy).

### Paso 3.5 — Desplegar

1. Clic en **"Deploy!"** (o **"Deploy"**).
2. Espera 2–5 minutos. Verás el log de instalación (pip, etc.).
3. Si aparece **"Your app is live!"** o el estado pasa a **Running**, ya está desplegado.

### Paso 3.6 — Si algo falla

- **Build error / dependencias:** Revisa la pestaña **"Logs"** o **"Build logs"**. Si falla por una librería (por ejemplo Camelot), se puede usar un `requirements.txt` reducido solo para el dashboard; dime y lo preparamos.
- **App running pero sin datos:** Comprueba que en Secrets pusiste bien **SUPABASE_URL** y **SUPABASE_KEY** y que el schema **anuario** está expuesto en la API (Paso 2.1).
- **Cambiar Secrets después:** En tu app en share.streamlit.io → **Settings** → **Secrets** → edita, guarda; la app se reiniciará.

### Paso 3.7 — Obtener la URL pública

- Cuando la app esté en **Running**, verás un enlace tipo:
  **`https://tu-app.streamlit.app`**
- Esa es la URL pública. Puedes compartirla para que cualquiera vea el dashboard.

---

## Resumen rápido

| # | Qué hacer |
|---|-----------|
| 1 | Crear repo en GitHub y subir el código del dashboard. |
| 2 | En Supabase: exponer schema `anuario` en la API y anotar URL y anon key. |
| 3 | Ir a share.streamlit.io → New app → elegir repo, branch `main`, main file `Inicio.py`. |
| 4 | Advanced settings → Secrets: pegar `SUPABASE_URL` y `SUPABASE_KEY` en TOML. |
| 5 | Deploy → esperar y usar la URL que te den. |

---

## Si tu dashboard está dentro de otro repo (subcarpeta)

Si el repositorio es por ejemplo `cvea-platform` y el dashboard está en la carpeta `sudeaseg-dashboard`:

- **Repository:** `tu-usuario/cvea-platform`
- **Main file path:** `sudeaseg-dashboard/Inicio.py`

Streamlit usará esa ruta; asegúrate de que dentro del repo exista `sudeaseg-dashboard/requirements.txt` (o que en la raíz haya un `requirements.txt` que instale todo lo que usa el dashboard).

---

¿En qué paso estás? Si me dices (por ejemplo “estoy en 1.3” o “ya subí a GitHub”), te indico el siguiente paso concreto o revisamos juntos si algo falla.
