"""
Versión 2 - Simulador de Asignación Contigua
Ajustes
Representar la memoria como un único bloque libre.
Permitir visualizar el estado de la memoria.
"""

MEMORIA_TOTAL = 100

# La memoria inicia con un solo bloque libre
memoria = [
    {
        "inicio": 0,
        "fin": MEMORIA_TOTAL - 1,
        "tamano": MEMORIA_TOTAL,
        "libre": True,
        "pid": None
    }
]


def mostrar_memoria():
    print("\n========== ESTADO DE LA MEMORIA ==========\n")

    print(f"{'Inicio ':<10}{'Fin ':<10}{'Tamaño ':<10}{'Estado ':<10}")

    for bloque in memoria:
        estado = "Libre" if bloque["libre"] else f"P{bloque['pid']}"
        print(
            f"{bloque['inicio']:<10}"
            f"{bloque['fin']:<10}"
            f"{bloque['tamano']:<10}"
            f"{estado:<10}"
        )

    print("\nMemoria total:", MEMORIA_TOTAL, "unidades")


def asignar():
    pid = int(input("ID del proceso: "))
    tam = int(input("Tamaño: "))

    for i, bloque in enumerate(memoria):

        if bloque["libre"] and bloque["tamano"] >= tam:

            nuevo = {
                "inicio": bloque["inicio"],
                "fin": bloque["inicio"] + tam - 1,
                "tamano": tam,
                "libre": False,
                "pid": pid
            }

            restante = bloque["tamano"] - tam

            memoria[i] = nuevo

            if restante > 0:
                memoria.insert(i + 1, {
                    "inicio": nuevo["fin"] + 1,
                    "fin": bloque["fin"],
                    "tamano": restante,
                    "libre": True,
                    "pid": None
                })

            print("Proceso asignado.")
            return

    print("No existe memoria suficiente.")


def main():

    while True:

        print("\n1. Asignar")
        print("2. Ver memoria")
        print("0. Salir")

        op = input("Opción: ")

        if op == "1":
            asignar()

        elif op == "2":
            mostrar_memoria()

        elif op == "0":
            break

main()