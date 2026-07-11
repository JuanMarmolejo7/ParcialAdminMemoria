"""
Simulador de paginacion de un nivel

Clases:
  - PageTableEntry: una fila de la tabla de paginas (pagina -> marco)
  - Process: un proceso con su propia tabla de paginas
  - PagingSystem: orquesta el pool de marcos, asigna/libera marcos y traduce direcciones virtuales a fisicas
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PageTableEntry:
    """Fila de la tabla de paginas"""
    page_number: int            # numero de pagina virtual
    frame: Optional[int] = None # marco fisico asignado
    valid: bool = False         # True si la pagina esta cargada en un marco

    def to_dict(self) -> Dict:
        return {
            "page_number": self.page_number,
            "frame": self.frame,
            "valid": self.valid,
        }


@dataclass
class Process:
    """Proceso con tamaño en bytes y su tabla de paginas"""
    pid: int
    size: int
    page_size: int
    page_table: List[PageTableEntry] = field(default_factory=list)

    @property
    def num_pages(self) -> int:
        """Cantidad de paginas necesarias (techo de size / page_size)"""
        return math.ceil(self.size / self.page_size)

    def to_dict(self) -> Dict:
        return {
            "pid": self.pid,
            "size": self.size,
            "num_pages": self.num_pages,
            "page_table": [e.to_dict() for e in self.page_table],
        }


class TranslationError(Exception):
    """Error al traducir una direccion virtual"""


class PagingSystem:
    """
    Sistema de paginacion de un nivel

    - virtual_size: tamaño del espacio de direcciones virtual (bytes)
    - physical_size: tamaño de la memoria fisica (bytes)
    - page_size: tamaño de pagina/marco (bytes)
    """

    def __init__(self, virtual_size: int, physical_size: int, page_size: int):
        if page_size <= 0 or virtual_size <= 0 or physical_size <= 0:
            raise ValueError("Todos los tamaños deben ser positivos")
        self.virtual_size = virtual_size
        self.physical_size = physical_size
        self.page_size = page_size

        self.total_frames = physical_size // page_size
        # Pool de marcos libres (por indice), en orden.
        self.free_frames: List[int] = list(range(self.total_frames))
        # Que proceso ocupa cada marco (None si esta libre).
        self.frame_owner: Dict[int, Optional[int]] = {
            f: None for f in range(self.total_frames)
        }
        self.processes: Dict[int, Process] = {}


    # Alta de procesos

    def create_process(self, pid: int, size: int) -> Process:
        """Crea un proceso, le asigna marcos libres y arma su tabla de paginas"""
        if pid in self.processes:
            raise ValueError(f"El proceso {pid} ya existe")
        if size <= 0:
            raise ValueError("El tamaños del proceso debe ser positivo")

        proc = Process(pid=pid, size=size, page_size=self.page_size)
        needed = proc.num_pages

        if needed > len(self.free_frames):
            raise ValueError(
                f"No hay marcos suficientes: P{pid} necesita {needed} "
                f"y solo hay {len(self.free_frames)} libres"
            )

        for page in range(needed):
            frame = self.free_frames.pop(0)          # primer marco libre
            self.frame_owner[frame] = pid
            proc.page_table.append(
                PageTableEntry(page_number=page, frame=frame, valid=True)
            )

        self.processes[pid] = proc
        return proc


    # Baja de procesos

    def terminate_process(self, pid: int) -> bool:
        """Libera los marcos del proceso y lo elimina"""
        proc = self.processes.get(pid)
        if proc is None:
            return False
        for entry in proc.page_table:
            if entry.frame is not None:
                self.frame_owner[entry.frame] = None
                self.free_frames.append(entry.frame)
        self.free_frames.sort()
        del self.processes[pid]
        return True


    # Traduccion de direcciones

    def translate(self, pid: int, virtual_address: int) -> Dict:
        """
        Traduce una direccion virtual a fisica para el proceso 'pid'

        pagina  = virtual_address // page_size
        offset  = virtual_address %  page_size
        fisica  = marco * page_size + offset
        """
        proc = self.processes.get(pid)
        if proc is None:
            raise TranslationError(f"El proceso {pid} no existe")
        if virtual_address < 0:
            raise TranslationError("La direccion virtual no puede ser negativa")
        if virtual_address >= proc.size:
            raise TranslationError(
                f"Direccion {virtual_address} fuera del espacio del proceso "
                f"(tamaño {proc.size})."
            )

        page = virtual_address // self.page_size
        offset = virtual_address % self.page_size

        if page >= len(proc.page_table):
            raise TranslationError(f"Pagina {page} no valida para P{pid}")

        entry = proc.page_table[page]
        if not entry.valid or entry.frame is None:
            raise TranslationError(f"Pagina {page} no cargada (page fault)")

        physical_address = entry.frame * self.page_size + offset
        return {
            "pid": pid,
            "virtual_address": virtual_address,
            "page": page,
            "offset": offset,
            "frame": entry.frame,
            "physical_address": physical_address,
        }


    # Estado

    def frames_state(self) -> List[Dict]:
        return [
            {"frame": f, "owner": self.frame_owner[f], "free": self.frame_owner[f] is None}
            for f in range(self.total_frames)
        ]

    def snapshot(self) -> Dict:
        return {
            "virtual_size": self.virtual_size,
            "physical_size": self.physical_size,
            "page_size": self.page_size,
            "total_frames": self.total_frames,
            "free_frames": len(self.free_frames),
            "used_frames": self.total_frames - len(self.free_frames),
            "frames": self.frames_state(),
            "processes": [p.to_dict() for p in self.processes.values()],
        }

    def reset(self, virtual_size: Optional[int] = None,
              physical_size: Optional[int] = None,
              page_size: Optional[int] = None) -> None:
        self.virtual_size = virtual_size or self.virtual_size
        self.physical_size = physical_size or self.physical_size
        self.page_size = page_size or self.page_size
        self.total_frames = self.physical_size // self.page_size
        self.free_frames = list(range(self.total_frames))
        self.frame_owner = {f: None for f in range(self.total_frames)}
        self.processes = {}
