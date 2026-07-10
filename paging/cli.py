# Memoria representada como una lista de bloques
# Cada bloque es un diccionario con: inicio, tamaño, libre y (si esta ocupado) pid
memoria = [
    {
        "inicio": 0,
        "tamano": 100,
        "libre": True,
        "pid": None
    }
]

UMBRAL = 4  # si el remanente al dividir un bloque es menor a esto, no se divide


# Busqueda de bloque segun estrategia

def buscar_bloque(tamano, estrategia):
    #Devuelve el indice del bloque elegido en 'memoria' segun la estrategia, o None
    candidatos = [
        i for i, b in enumerate(memoria)
        if b["libre"] and b["tamano"] >= tamano
    ]
    if not candidatos:
        return None

    if estrategia == "first":
        return candidatos[0]

    if estrategia == "best":
        return min(candidatos, key=lambda i: memoria[i]["tamano"])

    if estrategia == "worst":
        return max(candidatos, key=lambda i: memoria[i]["tamano"])

    return None



# Asignacion de procesos

def asignar_proceso(pid, tamano, estrategia):
    # verificar que el pid no este ya asignado
    for b in memoria:
        if not b["libre"] and b["pid"] == pid:
            print(f"El proceso P{pid} ya tiene memoria asignada.")
            return

    idx = buscar_bloque(tamano, estrategia)
    if idx is None:
        print(f"No hay un bloque libre suficiente para P{pid} ({tamano}u).")
        return

    bloque = memoria[idx]
    remanente = bloque["tamano"] - tamano

    if remanente < UMBRAL:
        # no conviene dividirtodo el bloque queda ocupado (fragmentacion interna)
        bloque["libre"] = False
        bloque["pid"] = pid
    else:
        # dividir el bloque en: ocupado + libre remanente
        ocupado = {
            "inicio": bloque["inicio"],
            "tamano": tamano,
            "libre": False,
            "pid": pid
        }
        libre = {
            "inicio": bloque["inicio"] + tamano,
            "tamano": remanente,
            "libre": True,
            "pid": None
        }
        memoria[idx:idx + 1] = [ocupado, libre]

    print(f"P{pid} asignado ({tamano}u) con estrategia {estrategia}")


# --------------------------------------------------------------------- #
# Liberacion de procesos
# --------------------------------------------------------------------- #
def liberar_proceso(pid):
    for b in memoria:
        if not b["libre"] and b["pid"] == pid:
            b["libre"] = True
            b["pid"] = None
            fusionar_bloques_libres()
            print(f"P{pid} liberado.")
            return
    print(f"No se encontro un bloque ocupado por P{pid}")


def fusionar_bloques_libres():
    fusionada = []
    for b in memoria:
        if fusionada and fusionada[-1]["libre"] and b["libre"]:
            fusionada[-1]["tamaño"] += b["tamaño"]
        else:
            fusionada.append(b)
    memoria[:] = fusionada



# Metricas de fragmentacion

def fragmentacion_externa():
    libres = [b["tamano"] for b in memoria if b["libre"]]
    if not libres:
        return 0
    return sum(libres) - max(libres)


def fragmentacion_interna():
    # con este esquema (sin dividir cuando el remanente < UMBRAL) el desperdicio queda "oculto" dentro de bloques ocupados que
    # son mas grandes que lo pedido; aqui se reporta como 0 porque no se guarda el tamano solicitado por separado
    # Si se quiere calcular, hay que guardar tambien el tamano pedido en el bloque
    return 0



# Visualizacion

def ver_estado():
    print("\n--- Bloques de memoria ---")
    for b in memoria:
        fin = b["inicio"] + b["tamano"]
        estado = "LIBRE" if b["libre"] else f"P{b['pid']}"
        print(f"[{b['inicio']:>4} - {fin:<4}] tamano={b['tamano']:<4} -> {estado}")

    print("\n--- Metricas ---")
    print(f"Fragmentacion externa: {fragmentacion_externa()}")
    print(f"Fragmentacion interna: {fragmentacion_interna()}")



# Menu principal

def main():
    while True:
        print("\n=== Simulador de Memoria ===")
        print("1. Asignar proceso")
        print("2. Liberar proceso")
        print("3. Ver estado")
        print("0. Salir")
        opcion = input("Opción: ")

        if opcion == "1":
            try:
                pid = int(input("ID del proceso: "))
                tamano = int(input("Tamaño a reservar: "))
                estrategia = input("Estrategia [first/best/worst]: ").strip().lower() or "first"
                if estrategia not in ("first", "best", "worst"):
                    print("Estrategia inválida.")
                    continue
                asignar_proceso(pid, tamano, estrategia)
            except ValueError:
                print("Debes ingresar números válidos.")

        elif opcion == "2":
            try:
                pid = int(input("ID del proceso a liberar: "))
                liberar_proceso(pid)
            except ValueError:
                print("Debes ingresar un número válido.")

        elif opcion == "3":
            ver_estado()

        elif opcion == "0":
            break

        else:
            print("Opción inválida.")


if __name__ == "__main__":
    main()