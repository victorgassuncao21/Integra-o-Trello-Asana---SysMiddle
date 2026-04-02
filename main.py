import os
import requests
from dotenv import load_dotenv

load_dotenv()

TRELLO_KEY = os.getenv("TRELLO_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID")
ASANA_PAT = os.getenv("ASANA_PAT")
ASANA_WORKSPACE_GID = os.getenv("ASANA_WORKSPACE_GID")
ASANA_TEAM_GID = os.getenv("ASANA_TEAM_GID")
TRELLO_BASE_URL = "https://api.trello.com/1"
ASANA_BASE_URL = "https://app.asana.com/api/1.0"


def trello_get(endpoint: str, params: dict | None = None):
    params = params or {}
    params["key"] = TRELLO_KEY
    params["token"] = TRELLO_TOKEN

    response = requests.get(f"{TRELLO_BASE_URL}{endpoint}", params=params)
    response.raise_for_status()
    return response.json()
def asana_post(endpoint: str, data: dict):
    headers = {
        "Authorization": f"Bearer {ASANA_PAT}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{ASANA_BASE_URL}{endpoint}",
        headers=headers,
        json={"data": data},
    )
    response.raise_for_status()
    return response.json()


def get_trello_board():
    return trello_get(f"/boards/{TRELLO_BOARD_ID}")

def get_trello_lists():
    return trello_get(
        f"/boards/{TRELLO_BOARD_ID}/lists",
        {"fields": "id,name,pos,closed", "filter": "open"},
    )

def get_trello_cards():
    return trello_get(
        f"/boards/{TRELLO_BOARD_ID}/cards",
        {
            "fields": "id,name,desc,due,dueComplete,idList,pos,url,closed",
            "filter": "open",
        },
    )

def create_asana_project(project_name: str):
    data = {"name": project_name}

    if ASANA_TEAM_GID:
        data["team"] = ASANA_TEAM_GID

    return asana_post(f"/workspaces/{ASANA_WORKSPACE_GID}/projects", data)

def create_asana_section(project_gid: str, section_name: str):
    return asana_post(f"/projects/{project_gid}/sections", {"name": section_name})

def create_asana_task(name: str, notes: str = "", due_on: str | None = None):
    data = {
        "workspace": ASANA_WORKSPACE_GID,
        "name": name,
        "notes": notes,
    }

    if due_on:
        data["due_on"] = due_on

    return asana_post("/tasks", data)

def add_task_to_section(section_gid: str, task_gid: str):
    return asana_post(f"/sections/{section_gid}/addTask", {"task": task_gid})

def main():
    print("Buscando board do Trello...")
    board = get_trello_board()
    print(f"Board encontrado: {board['name']}")

    print("Buscando listas...")
    trello_lists = get_trello_lists()
    print(f"Listas encontradas: {len(trello_lists)}")

    print("Buscando cards...")
    trello_cards = get_trello_cards()
    print(f"Cards encontrados: {len(trello_cards)}")

    print("Criando projeto no Asana...")
    project = create_asana_project(board["name"])
    project_gid = project["data"]["gid"]
    print(f"Projeto criado com sucesso: {project_gid}")

    list_to_section = {}

    print("Criando sections...")
    sorted_lists = sorted(trello_lists, key=lambda x: x.get("pos", 0))
    for trello_list in sorted_lists:
        section = create_asana_section(project_gid, trello_list["name"])
        section_gid = section["data"]["gid"]
        list_to_section[trello_list["id"]] = section_gid
        print(f"Section criada: {trello_list['name']} -> {section_gid}")

    print("Criando tasks e associando às sections...")
    sorted_cards = sorted(trello_cards, key=lambda x: (x.get("idList", ""), x.get("pos", 0)))

    for card in sorted_cards:
        notes = card.get("desc") or ""

        due_on = None
        if card.get("due"):
            due_on = card["due"][:10]

        task = create_asana_task(
            name=card["name"],
            notes=notes,
            due_on=due_on,
        )
        task_gid = task["data"]["gid"]

        section_gid = list_to_section.get(card["idList"])
        if section_gid:
            add_task_to_section(section_gid, task_gid)

        print(f"Task criada: {card['name']} -> {task_gid}")

    print("Sincronização finalizada")

if __name__ == "__main__":
    main()