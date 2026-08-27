import json
import urllib.request

url = "http://127.0.0.1:5000/api/third-parties"

# Datos de prueba de un cliente (usamos company_id: 1 de la empresa que registramos antes)
nuevo_cliente = {
    "company_id": 1,
    "type": "client",
    "document_number": "10456789123",
    "name": "Juan Pérez - Cliente Frecuente",
    "address": "Lima, Perú",
    "email": "juan.perez@email.com",
    "phone": "987654321",
}

data_json = json.dumps(nuevo_cliente).encode("utf-8")
req = urllib.request.Request(
    url,
    data=data_json,
    headers={"Content-Type": "application/json"},
    method="POST",
)

print("Registrando cliente de prueba...")

try:
  with urllib.request.urlopen(req) as response:
    resultado = json.loads(response.read().decode("utf-8"))
    print("\n¡Éxito! Respuesta del servidor:")
    print(json.dumps(resultado, indent=4, ensure_ascii=False))
except urllib.error.HTTPError as e:
  print(f"\nError ({e.code}): {e.read().decode('utf-8')}")