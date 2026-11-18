import router

packet_in_bytes = b'\x7f\x00\x00\x01\x22\xb1\x0ahola'

# SIN TTL
# ---------- PASO 4 ----------
#IP_packet_v1 = packet_in_bytes

#parsed_IP_packet = router.parse_packet(IP_packet_v1)
#print("parsed:", parsed_IP_packet)

#IP_packet_v2 = router.create_packet(parsed_IP_packet)
#print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))


# CON TTL
# ---------- PASO 1 ----------
IP_packet_v1 = packet_in_bytes

parsed_IP_packet = router.parse_packet(IP_packet_v1)
print("parsed:", parsed_IP_packet)

IP_packet_v2_str = router.create_packet(parsed_IP_packet)
#IP_packet_v2 = IP_packet_v2_str.encode()
print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2_str))