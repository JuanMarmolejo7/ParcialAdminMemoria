"""
Utilidades de interfaz de consola (sin dependencias externas).

Provee colores ANSI, cajas, titulos, tablas simples y una barra de memoria
proporcional para que la salida por consola sea clara y ordenada
"""

import os
import re
import shutil


# Colores ANSI

_USE_COLOR = os.environ.get("NO_COLOR") is None


def _c(code: str) -> str:
    return code if _USE_COLOR else ""


RESET = _c("\033[0m")
BOLD = _c("\033[1m")
DIM = _c("\033[2m")

RED = _c("\033[31m")
GREEN = _c("\033[32m")
YELLOW = _c("\033[33m")
BLUE = _c("\033[34m")
MAGENTA = _c("\033[35m")
CYAN = _c("\033[36m")
GREY = _c("\033[90m")

# Fondos (para la barra de memoria)
BG_GREEN = _c("\033[42m")
BG_RED = _c("\033[41m")
BG_YELLOW = _c("\033[43m")
BG_BLUE = _c("\033[44m")
BG_CYAN = _c("\033[46m")
BG_MAGENTA = _c("\033[45m")

# Paleta ciclica para procesos
_PROC_BG = [BG_BLUE, BG_CYAN, BG_MAGENTA, BG_YELLOW]


def proc_color(pid: int) -> str:
    """Color de fondo estable para un pid dado"""
    return _PROC_BG[pid % len(_PROC_BG)]


# Utilidad para medir/alinear texto con codigos ANSI

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _visible_len(s: str) -> int:
    """Longitud visible de un string, ignorando codigos de color ANSI

    Sin esto, celdas como '{GREEN}LIBRE{RESET}' se miden con mas
    caracteres de los que realmente se ven en pantalla, y las tablas
    quedan descuadradas (columnas mas anchas de lo necesario, bordes
    que no alinean).
    """
    return len(_ANSI_RE.sub("", s))


def _pad(s: str, width: int, align: str = "l") -> str:
    """Alinea `s` a `width` columnas visibles, preservando sus codigos ANSI

    No se puede usar str.ljust/rjust/center directamente porque cuentan
    los codigos de color como caracteres visibles.
    """
    faltante = max(0, width - _visible_len(s))
    if align == "r":
        return " " * faltante + s
    if align == "c":
        izq = faltante // 2
        der = faltante - izq
        return " " * izq + s + " " * der
    return s + " " * faltante



# Ancho de terminal

def term_width(default: int = 76) -> int:
    try:
        return min(shutil.get_terminal_size().columns, 100)
    except Exception:
        return default



# Bloques visuales

def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def banner(title: str, subtitle: str = "") -> None:
    """Encabezado principal enmarcado"""
    width = term_width()
    top = "╔" + "═" * (width - 2) + "╗"
    bottom = "╚" + "═" * (width - 2) + "╝"
    print(f"{BOLD}{CYAN}{top}{RESET}")
    _framed_line(title.center(width - 4), width, color=BOLD + CYAN)
    if subtitle:
        _framed_line(subtitle.center(width - 4), width, color=DIM + CYAN)
    print(f"{BOLD}{CYAN}{bottom}{RESET}")


def _framed_line(text: str, width: int, color: str = "") -> None:
    print(f"{BOLD}{CYAN}║{RESET} {color}{text}{RESET} {BOLD}{CYAN}║{RESET}")


def section(title: str) -> None:
    """Titulo de seccion con linea"""
    width = term_width()
    label = f" {title} "
    line = "─" * (width - len(label))
    print(f"\n{BOLD}{YELLOW}{label}{RESET}{GREY}{line}{RESET}")


def info(msg: str) -> None:
    print(f"{CYAN}i{RESET}  {msg}")


def ok(msg: str) -> None:
    print(f"{GREEN}✓{RESET}  {msg}")


def warn(msg: str) -> None:
    print(f"{YELLOW}!{RESET}  {msg}")


def error(msg: str) -> None:
    print(f"{RED}✗{RESET}  {msg}")


def kv(key: str, value, unit: str = "") -> None:
    """Imprime una linea clave: valor alineada"""
    val = f"{value}{(' ' + unit) if unit else ''}"
    print(f"  {GREY}{key:<22}{RESET}{BOLD}{val}{RESET}")


def menu(title: str, options) -> None:
    """Imprime un menu numerado options: lista de (tecla, descripcion)"""
    section(title)
    for key, desc in options:
        print(f"  {BOLD}{CYAN}[{key}]{RESET} {desc}")


def prompt(msg: str) -> str:
    return input(f"\n{BOLD}{GREEN}»{RESET} {msg}: ").strip()


def pause() -> None:
    input(f"\n{DIM}Enter para continuar...{RESET}")


def table(headers, rows, aligns=None) -> None:
    """
    Imprime una tabla simple con bordes
    headers: lista de str. rows: lista de listas. aligns: 'l'/'r'/'c' por col

    Los anchos de columna y el padding se calculan sobre la longitud
    VISIBLE del texto (sin contar codigos de color ANSI), para que
    celdas coloreadas (como "LIBRE" en verde o "P3" en azul) no
    descuadren los bordes de la tabla.
    """
    cols = len(headers)
    aligns = aligns or ["l"] * cols
    widths = [_visible_len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], _visible_len(str(cell)))

    def fmt(cell, i):
        return _pad(str(cell), widths[i], aligns[i])

    top = "┌" + "┬".join("─" * (w + 2) for w in widths) + "┐"
    sep = "├" + "┼".join("─" * (w + 2) for w in widths) + "┤"
    bot = "└" + "┴".join("─" * (w + 2) for w in widths) + "┘"

    print(f"{GREY}{top}{RESET}")
    head_cells = " │ ".join(f"{BOLD}{fmt(h, i)}{RESET}" for i, h in enumerate(headers))
    print(f"{GREY}│{RESET} {head_cells} {GREY}│{RESET}")
    print(f"{GREY}{sep}{RESET}")
    for row in rows:
        cells = " │ ".join(fmt(c, i) for i, c in enumerate(row))
        print(f"{GREY}│{RESET} {cells} {GREY}│{RESET}")
    print(f"{GREY}{bot}{RESET}")
