
import socket
import time

IP = "127.0.0.1"
PUERTO = 5005
UMBRAL = 0.30

receptor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receptor.bind((IP, PUERTO))

print("Receptor listo. Esperando mensaje...")

intervalos = []
ultimo_tiempo = None

while True:
    datos, direccion = receptor.recvfrom(1024)
    tiempo_actual = time.perf_counter()

    if datos == b"S":
        ultimo_tiempo = tiempo_actual
        print("Inicio de la transmision recibido.")

    elif datos == b"B":
        if ultimo_tiempo is not None:
            intervalo = tiempo_actual - ultimo_tiempo
            intervalos.append(intervalo)

        ultimo_tiempo = tiempo_actual

    elif datos == b"E":
        break

receptor.close()

bits = []

print("\nIntervalos medidos:")

for intervalo in intervalos:
    if intervalo < UMBRAL:
        bit = "0"
    else:
        bit = "1"

    bits.append(bit)
    print(f"{intervalo:.3f} segundos -> bit {bit}")

secuencia = "".join(bits)

print("\nBits recuperados:", secuencia)

if len(secuencia) == 0 or len(secuencia) % 8 != 0:
    print("Error: la cantidad de bits no es multiplo de 8.")
else:
    mensaje_bytes = bytes(
        int(secuencia[i:i + 8], 2)
        for i in range(0, len(secuencia), 8)
    )

    try:
        mensaje = mensaje_bytes.decode("utf-8")
        print("Mensaje recuperado:", mensaje)
    except UnicodeDecodeError:
        print("No se pudo decodificar el mensaje.")
