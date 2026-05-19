import json
from pathlib import Path

from src.models.neighborhood import Neighborhood

DEFAULT_DATASET = Path(__file__).parent.parent.parent / "data" / "the_continent_kingdoms.json"


def load(path: str | Path = DEFAULT_DATASET) -> tuple[list[Neighborhood], list[dict]]:
    """
    Carrega o dataset e retorna (neighborhoods, connections).

    Raises:
        FileNotFoundError: se o arquivo não existir.
        ValueError: se o JSON estiver mal formado ou faltar campos obrigatórios.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset não encontrado: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido em {path}: {exc}") from exc

    _validate(data, path)

    neighborhoods = [Neighborhood.from_dict(k) for k in data["kingdoms"]]
    connections = data["connections"]
    return neighborhoods, connections


def metadata(path: str | Path = DEFAULT_DATASET) -> dict:
    """Retorna apenas o bloco de metadados do dataset."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("metadata", {})


# ------------------------------------------------------------------
# Internal
# ------------------------------------------------------------------

_REQUIRED_KINGDOM_FIELDS = {"id", "name", "region", "coords"}
_REQUIRED_CONNECTION_FIELDS = {"id", "source", "target", "distance_km", "terrain", "cost"}


def _validate(data: dict, path: Path) -> None:
    for section in ("kingdoms", "connections"):
        if section not in data:
            raise ValueError(f"Campo obrigatório ausente no dataset: '{section}' ({path})")

    kingdom_ids = set()
    for i, k in enumerate(data["kingdoms"]):
        missing = _REQUIRED_KINGDOM_FIELDS - k.keys()
        if missing:
            raise ValueError(f"Reino #{i} sem campos obrigatórios: {missing}")
        if k["id"] in kingdom_ids:
            raise ValueError(f"ID de reino duplicado: {k['id']!r}")
        kingdom_ids.add(k["id"])

    for i, c in enumerate(data["connections"]):
        missing = _REQUIRED_CONNECTION_FIELDS - c.keys()
        if missing:
            raise ValueError(f"Conexão #{i} sem campos obrigatórios: {missing}")
        for field in ("source", "target"):
            if c[field] not in kingdom_ids:
                raise ValueError(
                    f"Conexão {c['id']!r}: {field} {c[field]!r} não existe nos reinos"
                )