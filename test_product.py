import json
import urllib.request

url = "http://127.0.0.1:5000/api/products"

# Datos de prueba de un producto asociado a la empresa 1
nuevo_producto = {
    "company_id": 1,
    "sku": "PROD-001",
    "name": "Troquelado Decorativo Estándar",
    "description": "Pieza troquelada de alta precisión para empaques",
    "price": 45.50,
    "cost": 20.00,
    "stock": 150,
}

data_json = json.dumps(nuevo_producto).encode("utf-8")
req = urllib.request.Request(
    url,
    data=data_json,
    headers={"Content-Type": "application/json"},
    method="POST",
)

print("Registrando producto de prueba...")

try:
  with urllib.request.urlopen(req) as response:
    resultado = json.loads(response.read().decode("utf-8"))
    print("\n¡Éxito! Respuesta del servidor:")
    print(json.dumps(resultado, indent=4, ensure_ascii=False))
except urllib.error.HTTPError as e:
  print(f"\nError ({e.code}): {e.read().decode('utf-8')}")