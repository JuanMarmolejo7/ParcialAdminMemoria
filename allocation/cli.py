"""
Simulador de asignacion contigua de memoria - Interfaz de consola.

Menu interactivo para asignar/liberar procesos con las estrategias
First / Best / Worst Fit y visualizar el mapa de memoria y las metricas
de fragmentacion.

Uso:
    python cli.py                     # inicia el menu interactivo
    python cli.py --demo              # corre el caso de prueba del enunciado y termina
    python cli.py --file procesos.txt # ejecuta un archivo de procesos y termina
"""

import importlib.util
import os
import sys

# Carpeta donde vive este archivo (allocation/).
_AQUI = os.path.dirname(os.path.abspath(__file__))


def _cargar_local(nombre_modulo):
    """Carga un modulo desde ESTA carpeta por ruta explicita

    Esto evita que Python tome un paquete externo del mismo nombre instalado en el entorno (por ejemplo
     un 'allocator' en site-packages). Siempre gana el archivo que esta junto a este cli.py
    """
    ruta = os.path.join(_AQUI, nombre_modulo + ".py")
    if not os.path.exists(ruta):
        sys.exit(
            "\nError: no se encontro '" + nombre_modulo + ".py' en:\n  " + _AQUI +
            "\nAsegurate de tener cli.py, allocator.py y ui.py en la MISMA carpeta.\n"
        )
    spec = importlib.util.spec_from_file_location(nombre_modulo, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


ui = _cargar_local("ui")
MemoryAllocator = _cargar_local("allocator").MemoryAllocator



# Visualizacion

def draw_memory_bar(alloc: MemoryAllocator) -> None:
    """Dibuja la memoria como una barra proporcional al ancho de la terminal"""
    width = ui.term_width() - 2
    total = alloc.total_size
    ui.section("Mapa de memoria")

    bar = ""
    for block in alloc.blocks:
        cells = max(1, round(block.size / total * width))
        if block.free:
            bar += f"{ui.BG_GREEN}{ui.BOLD}{' ' * cells}{ui.RESET}"
        else:
            color = ui.proc_color(block.pid)
            label = f"P{block.pid}".center(cells)[:cells]
            bar += f"{color}{ui.BOLD}{label}{ui.RESET}"
    print(bar)
    print(
        f"{ui.BG_GREEN}  {ui.RESET} libre    "
        f"{ui.BG_BLUE}  {ui.RESET} ocupado (Pn)    "
        f"{ui.DIM}0 -> {total}{ui.RESET}"
    )


def show_state(alloc: MemoryAllocator) -> None:
    draw_memory_bar(alloc)

    ui.section("Bloques")
    rows = []
    for b in alloc.blocks:
        estado = f"{ui.GREEN}LIBRE{ui.RESET}" if b.free else f"{ui.BLUE}P{b.pid}{ui.RESET}"
        rows.append([
            b.start,
            b.end,
            b.size,
            estado,
            b.internal_frag if not b.free and b.internal_frag else "-",
        ])
    ui.table(
        ["Inicio", "Fin", "Tamaño", "Estado", "Frag.Int"],
        rows,
        aligns=["r", "r", "r", "c", "r"],
    )

    ui.section("Metricas")
    ui.kv("Memoria total", alloc.total_size, "u")
    ui.kv("Memoria usada", alloc.total_used(), "u")
    ui.kv("Memoria libre", alloc.total_free(), "u")
    ui.kv("Fragmentacion interna", alloc.internal_fragmentation(), "u")
    ui.kv("Fragmentacion externa", alloc.external_fragmentation(), "u")
    ui.kv("Umbral de division", alloc.threshold, "u")


# Acciones del menu

def action_allocate(alloc: MemoryAllocator) -> None:
    try:
        pid = int(ui.prompt("ID del proceso (numero)"))
        size = int(ui.prompt("Tamano a reservar (unidades)"))
        strat = ui.prompt("Estrategia [first/best/worst]").lower() or "first"
        if strat not in MemoryAllocator.STRATEGIES:
            ui.error(f"Estrategia invalida: {strat}")
            return
        if alloc.allocate(pid, size, strat):
            ui.ok(f"P{pid} asignado ({size}u) con estrategia {strat}.")
        else:
            ui.warn(f"No hay un bloque libre suficiente para P{pid} ({size}u).")
    except ValueError as e:
        ui.error(str(e))


def action_free(alloc: MemoryAllocator) -> None:
    try:
        pid = int(ui.prompt("ID del proceso a liberar"))
        if alloc.free(pid):
            ui.ok(f"P{pid} liberado y bloques libres fusionados.")
        else:
            ui.warn(f"No se encontro un bloque ocupado por P{pid}.")
    except ValueError as e:
        ui.error(str(e))


def action_reset(alloc: MemoryAllocator) -> None:
    try:
        total = int(ui.prompt("Nuevo tamano total de memoria"))
        thr = int(ui.prompt("Nuevo umbral de division"))
        alloc.reset(total_size=total, threshold=thr)
        ui.ok(f"Memoria reiniciada: {total}u, umbral {thr}u.")
    except ValueError as e:
        ui.error(str(e))


def action_load_file(alloc: MemoryAllocator) -> None:
    ruta = ui.prompt("Ruta del archivo .txt de procesos")
    run_from_file(alloc, ruta)


# Carga de procesos desde archivo

def run_from_file(alloc: MemoryAllocator, path: str) -> None:
    """
    Ejecuta un archivo de texto con una instruccion por linea

    Formato soportado (una instruccion por linea, mayus/minus indiferente):
        ALLOCATE <pid> <size> [estrategia]   -> estrategia por defecto: first
        FREE <pid>
        RESET <total_size> [threshold]
        # esto es un comentario y las lineas vacias se ignoran
    """
    ui.banner(f"Archivo: {os.path.basename(path)}", "Ejecutando procesos desde archivo")

    if not os.path.isfile(path):
        ui.error(f"No se encontro el archivo: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    ejecutadas, fallidas = 0, 0
    for num, cruda in enumerate(lineas, start=1):
        linea = cruda.strip()
        if not linea or linea.startswith("#"):
            continue

        partes = linea.split()
        comando = partes[0].upper()

        try:
            if comando == "ALLOCATE":
                if len(partes) < 3:
                    raise ValueError("ALLOCATE requiere: pid size [estrategia]")
                pid = int(partes[1])
                size = int(partes[2])
                strat = partes[3].lower() if len(partes) > 3 else "first"
                if strat not in MemoryAllocator.STRATEGIES:
                    raise ValueError(f"estrategia invalida '{strat}'")
                if alloc.allocate(pid, size, strat):
                    ui.ok(f"[L{num}] ALLOCATE P{pid} ({size}u, {strat}) -> asignado")
                else:
                    ui.warn(f"[L{num}] ALLOCATE P{pid} ({size}u, {strat}) -> sin espacio suficiente")

            elif comando == "FREE":
                if len(partes) < 2:
                    raise ValueError("FREE requiere: pid")
                pid = int(partes[1])
                if alloc.free(pid):
                    ui.ok(f"[L{num}] FREE P{pid} -> liberado")
                else:
                    ui.warn(f"[L{num}] FREE P{pid} -> proceso no encontrado")

            elif comando == "RESET":
                if len(partes) < 2:
                    raise ValueError("RESET requiere: total_size [threshold]")
                total = int(partes[1])
                thr = int(partes[2]) if len(partes) > 2 else alloc.threshold
                alloc.reset(total_size=total, threshold=thr)
                ui.ok(f"[L{num}] RESET -> memoria de {total}u, umbral {thr}u")

            else:
                raise ValueError(f"instruccion desconocida '{comando}'")

            ejecutadas += 1
        except (ValueError, IndexError) as e:
            ui.error(f"[L{num}] '{linea}' -> {e}")
            fallidas += 1

    ui.section("Resumen del archivo")
    ui.kv("Lineas ejecutadas", ejecutadas)
    ui.kv("Lineas con error", fallidas)
    show_state(alloc)


# Caso de prueba del enunciado

def run_demo() -> None:
    ui.banner("DEMO - Asignacion contigua", "Caso de prueba del enunciado")
    alloc = MemoryAllocator(total_size=100, threshold=4)
    steps = [
        ("allocate", 1, 20, "first"),
        ("allocate", 2, 30, "first"),
        ("allocate", 3, 10, "first"),
        ("free", 2, None, None),
        ("allocate", 4, 15, "best"),
    ]
    for op, pid, size, strat in steps:
        if op == "allocate":
            alloc.allocate(pid, size, strat)
            ui.info(f"allocate(P{pid}, {size}u, {strat})")
        else:
            alloc.free(pid)
            ui.info(f"free(P{pid})")
    show_state(alloc)
    ui.section("Resultado esperado")
    ui.kv("P4 debe iniciar en", 20)
    ui.kv("Fragmentacion externa", 15, "u")



# Bucle principal

def main() -> None:
    if "--demo" in sys.argv:
        run_demo()
        return

    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        if idx + 1 >= len(sys.argv):
            sys.exit("Uso: python cli.py --file <ruta_al_archivo.txt>")
        ruta = sys.argv[idx + 1]
        alloc = MemoryAllocator(total_size=100, threshold=4)
        run_from_file(alloc, ruta)
        return

    ui.clear()
    ui.banner("Simulador de Asignacion Contigua",
              "First Fit - Best Fit - Worst Fit")
    try:
        total = int(ui.prompt("Tamaño total de memoria (Enter = 100)") or "100")
        thr = int(ui.prompt("Umbral de division (Enter = 4)") or "4")
    except ValueError:
        total, thr = 100, 4
        ui.warn("Valores invalidos, uso 100uds y umbral 4uds")

    alloc = MemoryAllocator(total_size=total, threshold=thr)

    options = [
        ("1", "Asignar proceso"),
        ("2", "Liberar proceso"),
        ("3", "Ver estado de la memoria"),
        ("4", "Reiniciar memoria"),
        ("5", "Correr caso de prueba (demo)"),
        ("6", "Cargar archivo de procesos (.txt)"),
        ("0", "Salir"),
    ]

    while True:
        ui.menu("Menu principal", options)
        choice = ui.prompt("Opcion")

        if choice == "1":
            action_allocate(alloc)
            show_state(alloc)
        elif choice == "2":
            action_free(alloc)
            show_state(alloc)
        elif choice == "3":
            show_state(alloc)
        elif choice == "4":
            action_reset(alloc)
            show_state(alloc)
        elif choice == "5":
            run_demo()
        elif choice == "6":
            action_load_file(alloc)
        elif choice == "0":
            ui.ok("Hasta luego")
            break
        else:
            ui.warn("Opcion no reconocida")
        ui.pause()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
        ui.info("Se interrumpió")
