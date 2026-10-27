
import socket
import time

IP = "127.0.0.1"
PUERTO = 5005

TIEMPO_CERO = 0.15
TIEMPO_UNO = 0.45

mensaje = input("Escribi el mensaje que queres ocultar: ")

if mensaje == "":
    print("Debes escribir un mensaje.")
    raise SystemExit

bits = "".join(
    format(byte, "08b")
    for byte in mensaje.encode("utf-8")
)

emisor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

emisor.sendto(b"S", (IP, PUERTO))

print("\nTransmitiendo mensaje mediante intervalos temporales...")

for bit in bits:
    if bit == "0":
        tiempo = TIEMPO_CERO
    else:
        tiempo = TIEMPO_UNO

    time.sleep(tiempo)
    emisor.sendto(b"B", (IP, PUERTO))

emisor.sendto(b"E", (IP, PUERTO))
emisor.close()

print("Transmision terminada.")
print("Cantidad de bits enviados:", len(bits))
