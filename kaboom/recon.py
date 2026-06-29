# script for TryHackMe room Kaboom https://tryhackme.com/room/kaboom

from pymodbus.client import ModbusTcpClient

ip= sys.argv[1]

c = ModbusTcpClient(ip, port=502)
c.connect()

# Sweep holding registers
rr = c.read_holding_registers(address=0, count=20, slave=1)
print(rr.registers)

# Sweep coils
rc = c.read_coils(address=0, count=20, slave=1)
print(rc.bits)

c.close()
