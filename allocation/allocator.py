"""
Simulador de asignacion contigua de memoria.

Contiene la logica orientada a objetos:
  - Block: representa un bloque de memoria (libre u ocupado)
  - MemoryAllocator: orquesta la lista de bloques y aplica las estrategias First Fit, Best Fit y Worst Fit, ademas de
  dividir/fusionar bloques y calcular las metricas de fragmentacion interna y externa
"""

from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class Block:
    """Un bloque contiguo de memoria"""
    start: int                      # direccion de inicio del bloque
    size: int                       # tamaño total del bloque
    free: bool = True               # True si esta libre, False si esta ocupado
    pid: Optional[int] = None       # id del proceso que lo ocupa (si aplica)
    internal_frag: int = 0          # fragmentacion interna dentro del bloque

    @property
    def end(self) -> int:
        """Primera direccion despues del bloque (start + size)"""
        return self.start + self.size

    def to_dict(self) -> Dict:
        return {
            "start": self.start,
            "end": self.end,
            "size": self.size,
            "free": self.free,
            "pid": self.pid,
            "internal_frag": self.internal_frag,
        }


class MemoryAllocator:
    """
    Administrador de memoria contigua

    Estrategias soportadas: "first", "best", "worst"
    El umbral (threshold) define el tamaño minimo que debe tener el remanente para que valga la pena dividir un bloque
    si el remanente es menor, ese espacio se cuenta como fragmentacion interna del proceso
    """

    STRATEGIES = ("first", "best", "worst")

    def __init__(self, total_size: int, threshold: int = 4):
        if total_size <= 0:
            raise ValueError("El tamaño total de memoria debe ser positivo.")
        self.total_size = total_size
        self.threshold = threshold
        # Al inicio toda la memoria es un unico bloque libre.
        self.blocks: List[Block] = [Block(start=0, size=total_size, free=True)]


    # Seleccion de bloque segun estrategia

    def _select_block(self, size: int, strategy: str) -> Optional[int]:
        """Devuelve el indice del bloque elegido segun la estrategia, o None."""
        strategy = strategy.lower()
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Estrategia invalida: {strategy}")

        candidates = [
            (i, b) for i, b in enumerate(self.blocks) if b.free and b.size >= size
        ]
        if not candidates:
            return None

        if strategy == "first":
            # el primer bloque libre que alcance
            return candidates[0][0]
        if strategy == "best":
            # el bloque libre mas chico que alcance
            return min(candidates, key=lambda c: c[1].size)[0]
        # worst: el bloque libre mas grande disponible
        return max(candidates, key=lambda c: c[1].size)[0]


    # Asignacion

    def allocate(self, pid: int, size: int, strategy: str = "first") -> bool:
        """
        Intenta asignar `size` unidades al proceso `pid` usando `strategy`.
        Devuelve True si lo logra, False si no hay bloque que alcance.
        """
        if size <= 0:
            raise ValueError("El tamaño del proceso debe ser positivo.")
        if any(b.pid == pid and not b.free for b in self.blocks):
            raise ValueError(f"El proceso {pid} ya tiene memoria asignada.")

        idx = self._select_block(size, strategy)
        if idx is None:
            return False

        block = self.blocks[idx]
        remainder = block.size - size

        if remainder < self.threshold:
            # No conviene dividir: el proceso ocupatodo el bloque y el sobrante se contabiliza como fragmentacion interna
            block.free = False
            block.pid = pid
            block.internal_frag = remainder
        else:
            # Dividir: un bloque ocupado exacto + un bloque libre remanente.
            occupied = Block(
                start=block.start, size=size, free=False, pid=pid, internal_frag=0
            )
            free_block = Block(
                start=block.start + size, size=remainder, free=True
            )
            self.blocks[idx : idx + 1] = [occupied, free_block]
        return True

    # Liberacion

    def free(self, pid: int) -> bool:
        """Libera el bloque del proceso `pid` y fusiona vecinos libres."""
        for block in self.blocks:
            if block.pid == pid and not block.free:
                block.free = True
                block.pid = None
                block.internal_frag = 0
                self._merge_free_blocks()
                return True
        return False

    def _merge_free_blocks(self) -> None:
        """Fusiona bloques libres contiguos en uno solo"""
        merged: List[Block] = []
        for block in self.blocks:
            if merged and merged[-1].free and block.free:
                # extender el ultimo bloque libre
                merged[-1].size += block.size
            else:
                merged.append(block)
        self.blocks = merged


    # Metricas

    def free_blocks(self) -> List[Block]:
        return [b for b in self.blocks if b.free]

    def used_blocks(self) -> List[Block]:
        return [b for b in self.blocks if not b.free]

    def external_fragmentation(self) -> int:
        """
        Fragmentacion externa = memoria libre total menos el bloque libre mas grande (espacio libre que NO sirve para
        la asignacion mas grande posible por estar disperso)
        """
        frees = self.free_blocks()
        total_free = sum(b.size for b in frees)
        largest_free = max((b.size for b in frees), default=0)
        return total_free - largest_free

    def internal_fragmentation(self) -> int:
        """Fragmentacion interna = suma del espacio desperdiciado dentro de bloques ocupados"""
        return sum(b.internal_frag for b in self.used_blocks())

    def total_free(self) -> int:
        return sum(b.size for b in self.free_blocks())

    def total_used(self) -> int:
        return sum(b.size for b in self.used_blocks())

    def snapshot(self) -> Dict:
        """Estado completo de la memoria para renderizar en la interfaz"""
        return {
            "total_size": self.total_size,
            "threshold": self.threshold,
            "blocks": [b.to_dict() for b in self.blocks],
            "free_blocks": [b.to_dict() for b in self.free_blocks()],
            "used_blocks": [b.to_dict() for b in self.used_blocks()]}