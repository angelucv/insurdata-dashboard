# Despliegue público del dashboard — InsurData (Seguro en Cifras)

Para que el aplicativo se vea **en público**, la opción más sencilla es **Streamlit Community Cloud** (gratuito).

---

## Requisitos previos

1. **Código en GitHub**  
   Sube el proyecto a un repositorio (público o privado). Si el dashboard está dentro de una carpeta (por ejemplo `sudeaseg-dashboard`), el repositorio puede ser solo esa carpeta o el monorepo; en el segundo caso indicarás la ruta del archivo principal.

2. **Cuenta en Streamlit**  
   Regístrate en [share.streamlit.io](https://share.streamlit.io) con tu cuenta de GitHub.

3. **Supabase ya configurado**  
   El dashboard lee datos del schema `anuario` en Supabase. Las tablas deben existir y tener datos (ETL ejecutado). En Supabase, el schema `anuario` debe estar **expuesto en la Data API** (Settings → API → Exposed schemas).

---

## Pasos para desplegar en Streamlit Community Cloud

### 1. Ir a Streamlit Community Cloud

- Entra en **[https://share.streamlit.io](https://share.streamlit.io)**.
- Inicia sesión con GitHub si no lo has hecho.

### 2. Crear la app

- Pulsa **"New app"** (o "Create app").
- Elige **"Deploy an existing app"** (o equivalente).
- Configura:
  - **Repository:** tu usuario/repo (ej. `tu-usuario/sudeaseg-dashboard`).
  - **Branch:** `main` (o la rama que uses).
  - **Main file path:** `Inicio.py`  
    Si el repo es el monorepo y el dashboard está en una subcarpeta, usa por ejemplo: `sudeaseg-dashboard/Inicio.py`.
- (Opcional) **App URL:** puedes elegir un subdominio, por ejemplo `insurdata-seguro-en-cifras`.

### 3. Configurar los secrets (Supabase)

El dashboard necesita `SUPABASE_URL` y `SUPABASE_KEY` para conectarse a Supabase. En Cloud no se usa el `.env` local; se usan los **Secrets** de la app.

- En la pantalla de creación (o después, en **Settings** de la app), abre **"Advanced settings"**.
- En **"Secrets"** pega un bloque TOML como el siguiente (con tus valores reales):

```toml
SUPABASE_URL = "https://TU_PROYECTO.supabase.co"
SUPABASE_KEY = "tu_clave_anon_o_service_role_aqui"
```

- **Recomendación:** usa la **anon key** (publishable) de Supabase si las políticas RLS permiten solo lectura para el dashboard. Si el ETL no se ejecuta desde Cloud, no hace falta la service role key.
- No subas nunca este bloque al repositorio (no crear `secrets.toml` en el repo).

### 4. Desplegar

- Pulsa **"Deploy"**.
- Espera a que termine el build (unos minutos). Si hay errores, revisa el log en la pestaña "Logs" / "Build logs".

### 5. URL pública

- Cuando el estado sea "Running", la app tendrá una URL como:  
  `https://tu-app.streamlit.app`  
  o la personalizada que hayas elegido.
- Esa URL se puede compartir para acceso público (si no activas autenticación adicional).

---

## Opciones adicionales

- **Autenticación:** Por defecto el dashboard no exige login (`REQUIRE_AUTH` en false). Si en el futuro quieres exigir inicio de sesión, tendrías que configurar Supabase Auth y poner en secrets `REQUIRE_AUTH = "true"` (y que el código lo lea desde `st.secrets` o env).
- **Python:** En "Advanced settings" puedes fijar la versión de Python (por ejemplo 3.10 o 3.11) si lo necesitas.
- **Re-deploy:** Cada push a la rama configurada puede re-desplegar la app automáticamente (según la configuración del workspace).

---

## Si el dashboard está en una subcarpeta

Si el repositorio es, por ejemplo, `cvea-platform` y el dashboard está en `sudeaseg-dashboard/`:

- **Main file path:** `sudeaseg-dashboard/Inicio.py`
- **Working directory:** En algunos casos hay que indicar que la raíz de la app es `sudeaseg-dashboard` (depende de cómo Streamlit resuelva los imports). Si los imports fallan, comprueba que en el repo exista `sudeaseg-dashboard/requirements.txt` y que la ruta base para `config`, `src`, etc. sea esa carpeta.

---

## Resumen rápido

| Paso | Acción |
|------|--------|
| 1 | Código en GitHub |
| 2 | [share.streamlit.io](https://share.streamlit.io) → New app |
| 3 | Repo, branch, main file: `Inicio.py` (o `sudeaseg-dashboard/Inicio.py`) |
| 4 | Advanced settings → Secrets: `SUPABASE_URL` y `SUPABASE_KEY` en TOML |
| 5 | Deploy → usar la URL que te asignen |

Con eso el aplicativo quedará desplegado y visible públicamente (salvo que añadas autenticación).
