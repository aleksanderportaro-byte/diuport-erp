import json
import urllib.request

# URL de tu API local de Flask
url = "http://127.0.0.1:5000/api/companies"

# Datos de prueba de una empresa
nueva_empresa = {
    "legal_name": "Diuport Tecnologias y Servicios SAC",
    "tax_id": "20609876541",
    "address": "San Juan de Miraflores, Lima",
    "currency": "PEN",
}

# Convertir los datos a formato JSON bytes
data_json = json.dumps(nueva_empresa).encode("utf-8")

# Configurar la petición HTTP POST
req = urllib.request.Request(
    url,
    data=data_json,
    headers={"Content-Type": "application/json"},
    method="POST",
)

print("Enviando datos de prueba al ERP...")

try:
  with urllib.request.urlopen(req) as response:
    resultado = json.loads(response.read().decode("utf-8"))
    print("\n¡Éxito! Respuesta del servidor:")
    print(json.dumps(resultado, indent=4, ensure_ascii=False))
except urllib.error.HTTPError as e:
  error_message = e.read().decode("utf-8")
  print(f"\nError del servidor ({e.code}): {error_message}")
except Exception as e:
  print(f"\nOcurrió un error inesperado: {e}")