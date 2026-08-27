import json
import urllib.request

url = "http://127.0.0.1:5000/api/sales"

# Datos de prueba de una venta (Empresa 1, Cliente ID 1, comprando 2 unidades del Producto ID 1)
nueva_venta = {
    "company_id": 1,
    "client_id": 1,
    "items": [{"product_id": 1, "quantity": 2}],
}

data_json = json.dumps(nueva_venta).encode("utf-8")
req = urllib.request.Request(
    url,
    data=data_json,
    headers={"Content-Type": "application/json"},
    method="POST",
)

print("Registrando venta de prueba y actualizando inventario...")

try:
  with urllib.request.urlopen(req) as response:
    resultado = json.loads(response.read().decode("utf-8"))
    print("\n¡Éxito! Respuesta del servidor:")
    print(json.dumps(resultado, indent=4, ensure_ascii=False))
except urllib.error.HTTPError as e:
  print(f"\nError ({e.code}): {e.read().decode('utf-8')}")