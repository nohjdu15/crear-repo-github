# Automatización para crear repositorios en GitHub

Este proyecto proporciona un script en Python y workflows de GitHub Actions
para **crear repositorios en GitHub** y **añadir múltiples colaboradores** de
forma segura, usando **tokens en secretos** (sin quemar credenciales en código).

## Estructura del proyecto

- `src/create_github_repo.py`: script principal que
   - normaliza el nombre del repositorio (minúsculas, seguro),
   - crea el repo vía API de GitHub,
   - añade N colaboradores con permisos configurables.
- `tests/`: pruebas unitarias con `pytest`.
- `requirements.txt`: dependencias necesarias para ejecutar el script.
- `.github/workflows/ci.yml`: pipeline de CI (lint, formato, tests y análisis de seguridad).
- `.github/workflows/create-repo.yml`: workflow manual para crear un repositorio
   y añadir colaboradores desde la interfaz de GitHub, además de instalar
   automáticamente los módulos BMAD (BMM y BMB) en el nuevo repo.

## Seguridad: uso de tokens

El script **no** lleva tokens hardcodeados. En su lugar, lee el token desde
una única variable de entorno dedicada:

- `REPO_CREATION_TOKEN`

En GitHub Actions, se debe usar un **Personal Access Token (PAT)** almacenado
como **secreto**.

### Paso a paso para crear el token y guardarlo como secreto

1. Inicia sesión en GitHub con tu usuario.
2. Ve a **Settings → Developer settings → Personal access tokens**.
3. Crea un nuevo token (puede ser clásico o fine-grained), con permisos que
   permitan **crear repositorios** y **gestionar colaboradores**, por ejemplo:
   - `repo`
   - `admin:repo_hook`
   - permisos de escritura en la organización si el repo se creará ahí.
4. Copia el valor del token (solo se muestra una vez).
5. Ve al repositorio donde está este proyecto (el de automatizaciones):
   - **Settings → Secrets and variables → Actions → New repository secret**.
6. Crea un secreto llamado, por ejemplo, `REPO_CREATION_TOKEN` y pega el valor
del PAT.
7. Guarda el secreto. A partir de ahora, los workflows pueden usarlo sin que el
   token quede visible en el código ni en los logs.

## Uso desde GitHub Actions: workflow interactivo

El workflow [.github/workflows/create-repo.yml](.github/workflows/create-repo.yml)
permite que **antes de la ejecución** indiques:

- el **nombre del nuevo repositorio**,
- la **descripción**,
- y la lista de **usuarios colaboradores**.

### Cómo ejecutarlo desde la UI de GitHub

1. Asegúrate de haber creado el secreto `REPO_CREATION_TOKEN` como se indica arriba.
2. Haz push de este proyecto al repositorio de GitHub.
3. Ve a la pestaña **Actions** del repo.
4. Selecciona el workflow **"Crear repositorio en GitHub"**.
5. Pulsa **"Run workflow"** (Ejecutar workflow).
6. Se abrirá un formulario con los siguientes campos:
   - `repository_name`: nombre del nuevo repo (se normalizará a minúsculas,
     espacios a guiones, etc.).
   - `description`: texto descriptivo (opcional).
   - `collaborators`: lista de usuarios GitHub separados por espacio, por
     ejemplo: `usuario1 usuario2 usuario3`.
7. Confirma la ejecución. El workflow:
   - usará `github.repository_owner` como *owner*,
   - tomará el PAT desde el secreto `REPO_CREATION_TOKEN`,
   - ejecutará el script `src/create_github_repo.py`,
   - creará el repositorio y añadirá los colaboradores indicados,
   - clonará el repositorio recién creado,
   - instalará los módulos BMAD en la raíz con:

     ```bash
     npx bmad-method install --modules bmm,bmb --yes
     ```

   - hará commit y push automático de los cambios al nuevo repo.

## Uso local (sin GitHub Actions)

1. Crea un entorno virtual de Python (recomendado) y actívalo.
2. Instala dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Exporta el token como variable de entorno (ejemplo en PowerShell):

   ```powershell
   $env:REPO_CREATION_TOKEN = "TU_TOKEN_AQUI"
   ```

4. Ejecuta el script pasándole owner, nombre de repo, descripción y usuarios:

   ```bash
   python -m src.create_github_repo miusuario "mi nuevo repo" "descripcion" usuario1 usuario2
   ```

El script normalizará el nombre del repo y añadirá los colaboradores que
indiques.

## Pipelines de GitHub Actions

En este proyecto hay **dos** workflows distintos:

1. **CI** – [.github/workflows/ci.yml](.github/workflows/ci.yml)
2. **Creación de repos + BMAD** – [.github/workflows/create-repo.yml](.github/workflows/create-repo.yml)

### Pipeline de CI (calidad y seguridad)

El workflow [.github/workflows/ci.yml](.github/workflows/ci.yml):

- instala dependencias de `requirements.txt`,
- ejecuta `flake8` para linting,
- formatea el código con `black .`,
- lanza los tests con `pytest`,
- pasa Bandit para detección de patrones de inseguridad en el código Python,
- usa `pip-audit` para detectar vulnerabilidades conocidas en dependencias.

Esto ayuda a mantener **buenas prácticas de código, estilo y seguridad**.

### Pipeline de creación de repos + instalación BMAD

El workflow [.github/workflows/create-repo.yml](.github/workflows/create-repo.yml):

- pide por formulario el nombre del nuevo repo, descripción y colaboradores,
- crea el repo en GitHub mediante la API (usando el token en `REPO_CREATION_TOKEN`),
- añade los colaboradores con el permiso configurado,
- calcula el nombre normalizado del repositorio,
- configura Node.js y clona el repo recién creado,
- ejecuta en la **raíz** del nuevo repo:

   ```bash
   npx bmad-method install --modules bmm,bmb --yes
   ```

- realiza `git add`, `git commit` y `git push` automático con el mismo token,
   dejando el repositorio ya inicializado con la estructura BMAD estándar.

## Comentario sobre el código principal

En `src/create_github_repo.py` encontrarás funciones bien separadas:

- `normalize_repo_name`: limpia y estandariza el nombre del repo.
- `create_repository`: hace la llamada autenticada a la API de GitHub para
  crear el repositorio.
- `add_collaborator`: añade un colaborador con el nivel de permiso indicado.
- `add_multiple_collaborators`: se encarga de iterar sobre una lista de usuarios
  y llamar a `add_collaborator` para cada uno.
- `main`: actúa como **entrada CLI**, leyendo argumentos y el token desde
  variables de entorno para ejecutar todo el flujo de creación + colaboradores.

De esta forma, el código es reutilizable tanto desde scripts locales como desde
GitHub Actions, manteniendo los secretos fuera del repositorio.
# crear-repo-github
