import json
import urllib.request

url = "http://127.0.0.1:5000/api/purchases"

# Datos de prueba: Compra para la Empresa 1, Proveedor ID 1, adquiriendo 5 unidades del Producto ID 1 a S/ 15.00 cada uno
nueva_compra = {
    "company_id": 1,
    "supplier_id": 1,
    "items": [{"product_id": 1, "quantity": 5, "unit_cost": 15.00}],
}

data_json = json.dumps(nueva_compra).encode("utf-8")
req = urllib.request.Request(
    url,
    data=data_json,
    headers={"Content-Type": "application/json"},
    method="POST",
)

print("Registrando compra de prueba y aumentando inventario...")

try:
  with urllib.request.urlopen(req) as response:
    resultado = json.loads(response.read().decode("utf-8"))
    print("\n¡Éxito! Respuesta del servidor:")
    print(json.dumps(resultado, indent=4, ensure_ascii=False))
except urllib.error.HTTPError as e:
  print(f"\nError ({e.code}): {e.read().decode('utf-8')}")