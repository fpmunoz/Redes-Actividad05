import sys
import socket
import ipaddress

# variable global para check_routes
# diccionario para el indice de round robin
STATE_RR: dict[tuple, int] = {}


def parse_packet(ip_packet: bytes):
    # primeros 4 bytes son a.b.c.d.
    ip_bytes = ip_packet[0:4]

    ip_str = ""

    for b in ip_bytes:
        ip_str += str(b) + "."

    # a.b.c.d
    ip_str = ip_str[:-1]

    # dos bytes para el puerto como un int
    port_bytes = ip_packet[4:6]
    port_int = int.from_bytes(port_bytes, byteorder="big", signed=False)  # ayuda de gemini

    # ttl
    ttl_bytes = ip_packet[6]

    # el resto de los bytes es el mensaje (payload)
    remaining_bytes = ip_packet[7:]

    parsed = {"ip": ip_str,
              "port": port_int,
              "ttl": ttl_bytes,
              "payload": remaining_bytes}

    return parsed


def create_packet(parsed_ip_packet: dict):
    # pasamos a.b.c.d a un int
    oct = []

    for n in parsed_ip_packet["ip"].split("."):
        oct.append(int(n))

    # 4 bytes de ip y 2 de puerto
    ip_bytes = bytes(oct)
    port_bytes = parsed_ip_packet["port"].to_bytes(2, byteorder="big", signed=False)
    ttl_bytes = parsed_ip_packet["ttl"].to_bytes(1, byteorder="big", signed=False)

    remaining = parsed_ip_packet["payload"]

    # si el mensaje esta en str lo pasamos a bytes
    if isinstance(remaining, str):
        remaining = remaining.encode("utf-8")

    return ip_bytes + port_bytes + ttl_bytes + remaining



def  carga_tablas_rutas(file_name):
    tabla = []

    with open(file_name, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()

            # ignoramos lineas vacias y comentarios
            if not linea or linea.startswith("#"):
                continue

            parts = linea.split()
            
            reglas = {"red_cidr": parts[0],
                      "puerto_inicial": int(parts[1]),
                      "puerto_final": int(parts[2]),
                      "next_hop_ip": parts[3],
                      "next_hop_port": int(parts[4])}

            tabla.append(reglas)

    return tabla


def check_routes(routes_file_name: str, destination_address: tuple[str, int], rrstate: dict = None)-> tuple[str, int]:
    # correccion/idea de gemini
    # ponemos el estados de round robin como parametro y luego toma el valor de la variable global
    if rrstate == None:
        rrstate = STATE_RR

    dest_ip_str, dest_port = destination_address
    dest_ip = ipaddress.ip_address(dest_ip_str)  # ayuda de gemini

    # lista de posibles rutas
    eq_routes = []

    with open(routes_file_name, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
        
            if not linea or linea.startswith("#"):
                continue

            parts = linea.split()
            red = ipaddress.ip_network(parts[0], strict=False)  # ayuda de gemini
            puerto_inicial = int(parts[1])
            puerto_final = int(parts[2])
            next_hop_ip = parts[3]
            next_hop_port = int(parts[4])

            # la rutas solo es aceptada si pertenece a la red y el puerto esta en el rango
            if dest_ip in red and (puerto_inicial <= dest_port <= puerto_final):
                eq_routes.append((next_hop_ip, next_hop_port))

    if not eq_routes:
        return None

    # buscamos el indice de rutas en el diccionerio y sacamos su resto con respecto a la cantidad de rutas
    indice = rrstate.get(tuple(eq_routes), 0) % len(eq_routes)
    next_hop = eq_routes[indice]

    # guardamos el indice de la sigueinte ruta
    rrstate[tuple(eq_routes)] = (indice+1) % len(eq_routes)

    return next_hop



def main():
    # 3 parametros
    if len(sys.argv) != 4:
        sys.exit(1)

    router_ip = sys.argv[1]
    router_puerto = int(sys.argv[2])
    file_router = sys.argv[3]
    dir_router = (router_ip, router_puerto)
    
    tabla_rutas = carga_tablas_rutas(file_router)

    # socket no orientado a conexion asociado a la direccion del router
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(dir_router)

    print(f"Router iniciado en {dir_router}")
    print(f"Tablas de rutas desde '{file_router}': {tabla_rutas}\n")

    try:
        while True:
            # se bloquea hasta que recibe un paquete
            data, addr = sock.recvfrom(4096)
            parsed = parse_packet(data)

            # se acabo el ttl
            if parsed["ttl"] <= 0:
                print(f"Se recibió paquete {data} con TTL 0\n")
                continue

            dest_addr = (parsed['ip'], parsed['port'])

            # el mensaje es para el router actual si no se busca el siguiente
            if dest_addr == dir_router:
                msg = parsed["payload"].decode("utf-8", errors="replace")
                print(msg)
            else:
                dir_next_hop = check_routes(file_router, dest_addr)

                if dir_next_hop != None:
                    parsed["ttl"] -= 1
                    new_data = create_packet(parsed)

                    print(f"Redirigiendo paquete {new_data} con destino final {dest_addr} desde {dir_router} hacia {dir_next_hop}")

                    sock.sendto(new_data, dir_next_hop)
                else:
                    print(f"No hay rutas hacia {dest_addr} para paquete {data}")

    except KeyboardInterrupt:
        sock.close()
        print("\nApagando router...")
    finally:
        sock.close()


if __name__ == "__main__":
    main()