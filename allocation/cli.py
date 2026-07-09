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


def main():
    while True:

        print("\n===== SIMULADOR DE MEMORIA =====")
        print("1. Asignar proceso")
        print("2. Liberar proceso")
        print("3. Ver estado de la memoria")
        print("0. Salir")

        opcion = input("\nSeleccione una opción : ")

        if opcion == "1":
            print("\nLa asignación de procesos aún no está implementada ")

        elif opcion == "2":
            print("\nLa liberación de procesos aún no está implementada ")

        elif opcion == "3":
            mostrar_memoria()

        elif opcion == "0":
            print("\nHasta luego ")
            break

        else:
            print("\nOpción inválida ")


if __name__ == "__main__":
    main()