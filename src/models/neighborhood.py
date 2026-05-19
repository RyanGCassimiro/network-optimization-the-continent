from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Coords:
    x: float
    y: float

    def distance_to(self, other: "Coords") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def __repr__(self) -> str:
        return f"({self.x}, {self.y})"


@dataclass
class Neighborhood:
    id: str
    name: str
    region: str
    coords: Coords
    capital: str = ""
    population: int = 0
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Neighborhood":
        return cls(
            id=data["id"],
            name=data["name"],
            region=data["region"],
            coords=Coords(x=data["coords"]["x"], y=data["coords"]["y"]),
            capital=data.get("capital", ""),
            population=data.get("population_estimate", 0),
            description=data.get("description", ""),
        )

    def is_in_region(self, region: str) -> bool:
        return self.region.lower() == region.lower()

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Neighborhood):
            return NotImplemented
        return self.id == other.id

    def __repr__(self) -> str:
        return f"Neighborhood(id={self.id!r}, name={self.name!r}, region={self.region!r})"
