import os
import re
import sys
from typing import List

import requests

# URL base de la API pública de GitHub
GITHUB_API_URL = "https://api.github.com"


def normalize_repo_name(name: str) -> str:
    """Normaliza el nombre del repositorio para cumplir buenas prácticas.

    - Convierte todo a minúsculas.
    - Sustituye espacios por guiones.
    - Elimina cualquier carácter que no sea letra, número, guion o guion bajo.
    """
    if not isinstance(name, str):
        raise TypeError(
            "El nombre del repositorio debe ser una cadena."
        )

    normalized = name.strip().lower().replace(" ", "-")
    normalized = re.sub(r"[^a-z0-9_\-]", "", normalized)

    if not normalized:
        raise ValueError(
            "Nombre de repositorio inválido después de normalizar."
        )

    return normalized


def create_repository(
    token: str,
    owner: str,
    repo_name: str,
    description: str = "",
    private: bool = True,
) -> dict:
    """Crea un repositorio en GitHub usando la API oficial.

    Este helper hace una llamada autenticada a la API REST de GitHub
    para crear un nuevo repositorio bajo el usuario/organización que
    corresponda al token utilizado.

    NOTA: aquí se usa el endpoint ``/user/repos``, que crea el
    repositorio bajo la identidad asociada al token.
    """

    if not token:
        raise ValueError("El token de GitHub no puede estar vacío.")

    normalized_name = normalize_repo_name(repo_name)

    # Endpoint para crear repos bajo el usuario autenticado
    url = f"{GITHUB_API_URL}/user/repos"
    payload = {
        "name": normalized_name,
        "description": description,
        "private": private,
        "auto_init": True,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    if response.status_code >= 300:
        raise RuntimeError(
            f"Error creando repo ({response.status_code}): {response.text}"
        )

    return response.json()


def add_collaborator(
    token: str,
    owner: str,
    repo: str,
    username: str,
    permission: str = "push",
) -> None:
    """Agrega un colaborador con un nivel de permiso concreto.

    ``permission`` puede ser: ``pull``, ``triage``, ``push``,
    ``maintain`` o ``admin`` según la granularidad deseada.
    """

    if not username:
        raise ValueError(
            "El nombre de usuario del colaborador no puede estar vacío."
        )

    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/collaborators/{username}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"permission": permission}

    response = requests.put(url, json=payload, headers=headers, timeout=30)

    if response.status_code not in (201, 202, 204):
        raise RuntimeError(
            f"Error añadiendo colaborador {username} "
            f"({response.status_code}): {response.text}"
        )


def add_multiple_collaborators(
    token: str,
    owner: str,
    repo: str,
    users: List[str],
    permission: str = "push",
) -> None:
    """Agrega múltiples colaboradores iterando sobre la lista de usuarios.

    Se ignoran entradas vacías o con solo espacios en blanco.
    """

    for user in users:
        user = user.strip()
        if not user:
            continue
        print(f"Añadiendo colaborador: {user}...")
        add_collaborator(token, owner, repo, user, permission)
    print("Todos los colaboradores fueron procesados.")


def main() -> None:
    """Punto de entrada del script cuando se ejecuta como CLI.

    Dos modos de uso principales:

    1) Desde línea de comandos (local):

        python -m src.create_github_repo \
            <owner> "<nombre_repo>" "<descripcion>" user1 user2 ...

    En este caso el token se obtiene **únicamente** de la variable
    de entorno ``REPO_CREATION_TOKEN``.

    2) Desde GitHub Actions (workflow_dispatch):

       El workflow pasa los argumentos de la misma forma y expone el
       token seguro mediante un secreto de GitHub que se inyecta en
       ``REPO_CREATION_TOKEN``.
    """

    if len(sys.argv) < 4:
        print(
            "Uso: python -m src.create_github_repo "
            "<owner> \"<nombre_repo>\" \"<descripcion>\" user1 user2 ..."
        )
        raise SystemExit(1)

    # Leemos el token desde una variable de entorno específica para
    # creación de repos. No hay fallback a GITHUB_TOKEN para endurecer
    # el modelo de seguridad.
    token = os.getenv("REPO_CREATION_TOKEN")
    if not token:
        print(
            "ERROR: Debes definir la variable de entorno "
            "REPO_CREATION_TOKEN con un token válido."
        )
        raise SystemExit(1)

    owner = sys.argv[1]
    repo_name = sys.argv[2]
    description = sys.argv[3]
    collaborators = sys.argv[4:]

    repo_info = create_repository(
        token=token,
        owner=owner,
        repo_name=repo_name,
        description=description,
        private=True,
    )

    normalized_name = repo_info["name"]
    print(f"Repositorio creado: {repo_info['html_url']}")

    if collaborators:
        add_multiple_collaborators(
            token=token,
            owner=owner,
            repo=normalized_name,
            users=collaborators,
            permission="push",
        )


if __name__ == "__main__":
    main()
