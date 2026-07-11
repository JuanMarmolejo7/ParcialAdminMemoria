"""
Simulador de paginacion de un nivel - Interfaz de consola

Menu interactivo para crear/terminar procesos, ver las tablas de paginas,
el estado de los marcos fisicos y traducir direcciones virtuales a fisicas

Uso:
    python cli.py                     # inicia el menu interactivo
    python cli.py --demo              # corre el caso de prueba del enunciado y termina
    python cli.py --file procesos.txt # ejecuta un archivo de procesos y termina
"""

import importlib.util
import os
import sys

# Carpeta donde vive este archivo (paging/).
_AQUI = os.path.dirname(os.path.abspath(__file__))


def _cargar_local(nombre_modulo):
    """Carga un modulo desde ESTA carpeta por ruta explicita.

    Esto evita que Python tome un paquete externo del mismo nombre instalado
    en el entorno (por ejemplo un 'paging' en site-packages). Siempre gana
    el archivo que esta junto a este cli.py.
    """
    ruta = os.path.join(_AQUI, nombre_modulo + ".py")
    if not os.path.exists(ruta):
        sys.exit(
            "\nError: no se encontro '" + nombre_modulo + ".py' en:\n  " + _AQUI +
            "\nAsegurate de tener cli.py, paging.py y ui.py en la MISMA carpeta.\n"
        )
    spec = importlib.util.spec_from_file_location(nombre_modulo, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


ui = _cargar_local("ui")
_paging = _cargar_local("paging")
PagingSystem = _paging.PagingSystem
TranslationError = _paging.TranslationError



# Visualizacion

def draw_frames(system: PagingSystem) -> None:
    """Dibuja los marcos fisicos como una grilla de celdas."""
    ui.section("Marcos fisicos")
    cells = []
    for f in range(system.total_frames):
        owner = system.frame_owner[f]
        if owner is None:
            cells.append(f"{ui.BG_GREEN}{ui.BOLD} F{f:<2} libre {ui.RESET}")
        else:
            color = ui.proc_color(owner)
            cells.append(f"{color}{ui.BOLD} F{f:<2}  P{owner:<2}{ui.RESET}")

    # imprimir en filas de 4 marcos
    per_row = 4
    for i in range(0, len(cells), per_row):
        print("  " + "  ".join(cells[i : i + per_row]))
    print(
        f"\n  {ui.BG_GREEN}  {ui.RESET} libre    "
        f"{ui.BG_BLUE}  {ui.RESET} ocupado (Pn)"
    )


def show_state(system: PagingSystem) -> None:
    ui.section("Configuracion")
    ui.kv("Memoria virtual", system.virtual_size, "bytes")
    ui.kv("Memoria fisica", system.physical_size, "bytes")
    ui.kv("Tamaño de pagina/marco  ", system.page_size, "bytes")
    ui.kv("Marcos totales", system.total_frames)
    ui.kv("Marcos libres", len(system.free_frames))
    ui.kv("Marcos usados", system.total_frames - len(system.free_frames))

    draw_frames(system)

    if system.processes:
        for proc in system.processes.values():
            ui.section(f"Tabla de paginas - P{proc.pid} "
                       f"({proc.size} bytes, {proc.num_pages} paginas)")
            rows = [
                [e.page_number, e.frame if e.valid else "-",
                 "si" if e.valid else "no"]
                for e in proc.page_table
            ]
            ui.table(["Pagina", "Marco", "Valida"], rows, aligns=["r", "r", "c"])
    else:
        ui.info("No hay procesos cargados.")



# Acciones del menu

def action_create(system: PagingSystem) -> None:
    try:
        pid = int(ui.prompt("ID del proceso (numero)"))
        size = int(ui.prompt("Tamaño del proceso (bytes)"))
        proc = system.create_process(pid, size)
        ui.ok(f"P{pid} creado: {size} bytes -> {proc.num_pages} paginas.")
    except ValueError as e:
        ui.error(str(e))


def action_terminate(system: PagingSystem) -> None:
    try:
        pid = int(ui.prompt("ID del proceso a terminar"))
        if system.terminate_process(pid):
            ui.ok(f"P{pid} terminado y sus marcos liberados.")
        else:
            ui.warn(f"El proceso P{pid} no existe.")
    except ValueError as e:
        ui.error(str(e))


def action_translate(system: PagingSystem) -> None:
    try:
        pid = int(ui.prompt("ID del proceso"))
        vaddr = int(ui.prompt("Direccion virtual a traducir"))
        r = system.translate(pid, vaddr)
        ui.section("Traduccion de direccion")
        ui.kv("Proceso", f"P{r['pid']}")
        ui.kv("Direccion virtual", r["virtual_address"])
        ui.kv("Pagina", r["page"])
        ui.kv("Offset", r["offset"])
        ui.kv("Marco fisico", r["frame"])
        ui.ok(f"Direccion fisica = {r['frame']} x {system.page_size} + "
              f"{r['offset']} = {ui.BOLD}{r['physical_address']}{ui.RESET}")
    except (ValueError, TranslationError) as e:
        ui.error(str(e))


def action_reset(system: PagingSystem) -> None:
    try:
        v = int(ui.prompt("Memoria virtual (bytes)"))
        p = int(ui.prompt("Memoria fisica (bytes)"))
        pg = int(ui.prompt("Tamaño de pagina (bytes)"))
        system.reset(virtual_size=v, physical_size=p, page_size=pg)
        ui.ok(f"Sistema reiniciado: {system.total_frames} marcos disponibles.")
    except ValueError as e:
        ui.error(str(e))


def action_load_file(system: PagingSystem) -> None:
    ruta = ui.prompt("Ruta del archivo .txt de procesos")
    run_from_file(system, ruta)



# Carga de procesos desde archivo

def run_from_file(system: PagingSystem, path: str) -> None:
    """
    Ejecuta un archivo de texto con una instruccion por linea.

    Formato soportado (una instruccion por linea, mayus/minus indiferente):
        CREATE <pid> <size_bytes>
        TERMINATE <pid>
        TRANSLATE <pid> <direccion_virtual>
        RESET <virtual_size> <physical_size> <page_size>
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
            if comando == "CREATE":
                if len(partes) < 3:
                    raise ValueError("CREATE requiere: pid size_bytes")
                pid = int(partes[1])
                size = int(partes[2])
                proc = system.create_process(pid, size)
                ui.ok(f"[L{num}] CREATE P{pid} ({size} bytes) -> {proc.num_pages} paginas")

            elif comando == "TERMINATE":
                if len(partes) < 2:
                    raise ValueError("TERMINATE requiere: pid")
                pid = int(partes[1])
                if system.terminate_process(pid):
                    ui.ok(f"[L{num}] TERMINATE P{pid} -> marcos liberados")
                else:
                    ui.warn(f"[L{num}] TERMINATE P{pid} -> proceso no existe")

            elif comando == "TRANSLATE":
                if len(partes) < 3:
                    raise ValueError("TRANSLATE requiere: pid direccion_virtual")
                pid = int(partes[1])
                vaddr = int(partes[2])
                r = system.translate(pid, vaddr)
                ui.ok(f"[L{num}] TRANSLATE P{pid} vaddr={vaddr} -> "
                      f"pagina={r['page']} marco={r['frame']} "
                      f"fisica={r['physical_address']}")

            elif comando == "RESET":
                if len(partes) < 4:
                    raise ValueError("RESET requiere: virtual_size physical_size page_size")
                v, p, pg = int(partes[1]), int(partes[2]), int(partes[3])
                system.reset(virtual_size=v, physical_size=p, page_size=pg)
                ui.ok(f"[L{num}] RESET -> {system.total_frames} marcos disponibles")

            else:
                raise ValueError(f"instruccion desconocida '{comando}'")

            ejecutadas += 1
        except (ValueError, TranslationError, IndexError) as e:
            ui.error(f"[L{num}] '{linea}' -> {e}")
            fallidas += 1

    ui.section("Resumen del archivo")
    ui.kv("Lineas ejecutadas", ejecutadas)
    ui.kv("Lineas con error", fallidas)
    show_state(system)



# Caso de prueba del enunciado

def run_demo() -> None:
    ui.banner("DEMO - Paginacion", "Caso de prueba del enunciado")
    system = PagingSystem(virtual_size=1024, physical_size=512, page_size=64)
    proc = system.create_process(1, 150)
    ui.info(f"create_process(P1, 150 bytes) -> {proc.num_pages} paginas")
    show_state(system)

    ui.section("Traduccion de direccion virtual 130")
    r = system.translate(1, 130)
    ui.kv("Pagina", r["page"])
    ui.kv("Offset", r["offset"])
    ui.kv("Marco", r["frame"])
    ui.kv("Direccion fisica", r["physical_address"])
    ui.section("Resultado esperado")
    ui.kv("Pagina / Offset / Marco", "2 / 2 / 2")
    ui.kv("Direccion fisica", 130)



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
        system = PagingSystem(virtual_size=1024, physical_size=512, page_size=64)
        run_from_file(system, ruta)
        return

    ui.clear()
    ui.banner("Simulador de Paginacion", "Traduccion de direcciones - 1 nivel")
    try:
        v = int(ui.prompt("Memoria virtual en bytes (Enter = 1024)") or "1024")
        p = int(ui.prompt("Memoria fisica en bytes (Enter = 512)") or "512")
        pg = int(ui.prompt("Tamaño de pagina en bytes (Enter = 64)") or "64")
    except ValueError:
        v, p, pg = 1024, 512, 64
        ui.warn("Valores invalidos, uso 1024 / 512 / 64.")

    system = PagingSystem(virtual_size=v, physical_size=p, page_size=pg)

    options = [
        ("1", "Crear proceso"),
        ("2", "Terminar proceso"),
        ("3", "Traducir direccion virtual"),
        ("4", "Ver estado del sistema"),
        ("5", "Reiniciar sistema"),
        ("6", "Correr caso de prueba (demo)"),
        ("7", "Cargar archivo de procesos (.txt)"),
        ("0", "Salir"),
    ]

    while True:
        ui.menu("Menu principal", options)
        choice = ui.prompt("Opcion")

        if choice == "1":
            action_create(system)
            show_state(system)
        elif choice == "2":
            action_terminate(system)
            show_state(system)
        elif choice == "3":
            action_translate(system)
        elif choice == "4":
            show_state(system)
        elif choice == "5":
            action_reset(system)
            show_state(system)
        elif choice == "6":
            run_demo()
        elif choice == "7":
            action_load_file(system)
        elif choice == "0":
            ui.ok("Hasta luego.")
            break
        else:
            ui.warn("Opcion no reconocida.")
        ui.pause()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
        ui.info("Interrumpido. Saliendo.")
