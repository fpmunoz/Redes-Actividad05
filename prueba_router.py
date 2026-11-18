import sys
import socket
import router

def main():
    # 3 parametros, con el primero siendo los headers
    if len(sys.argv) != 4:
        sys.exit(1)

    headers = sys.argv[1]
    split_headers = headers.split(";")

    # 3 headers
    if len(split_headers) != 3:
        sys.exit(1)

    ip_final = split_headers[0]
    port_final = int(split_headers[1])
    ttl = int(split_headers[2])

    # el resto de los parametros 
    ip_router_inicial = sys.argv[2]
    port_router_inicial = int(sys.argv[3])

    file_name = "msg.txt"  # ayuda de gemini

    # socket no orientado a conexion, no asociado a una direccion
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        with open(file_name, "r", encoding="utf-8") as f:
            for n_linea, linea in enumerate(f, 1):
                content = linea.rstrip("\r\n")

                if not content:
                    continue

                # construye el oaquete
                packet_parsed = {"ip": ip_final,
                                 "port": port_final,
                                 "ttl": ttl,
                                 "payload": content.encode("utf-8")}

                packet = router.create_packet(packet_parsed)
                sock.sendto(packet, (ip_router_inicial, port_router_inicial))

                print(f"Linea {n_linea}: Enviado a {ip_router_inicial}:{port_router_inicial}")                
    except FileNotFoundError:
        print(f"Error: No se encontro el archivo '{file_name}'")
    finally:
        sock.close()


if __name__ == "__main__":
    main()