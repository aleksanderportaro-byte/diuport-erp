from core.models import Company, User
from database import get_db

db = next(get_db())

# 1. Buscar la empresa registrada con el RUC de prueba
company = db.query(Company).filter_by(tax_id="20609876541").first()

if company:
  # 2. Verificar si el usuario ya existe
  existing_user = (
      db.query(User)
      .filter_by(company_id=company.id, username="administrador")
      .first()
  )

  if existing_user:
    print(
        "El usuario 'administrador' ya está registrado para esta empresa."
    )
  else:
    # 3. Crear el usuario administrador vinculado a la empresa
    nuevo_usuario = User(
        company_id=company.id,
        username="administrador",
        email="admin@diuport.com",
        password_hash="123456",  # La contraseña que escribiste en el formulario
        role="admin",
    )
    db.add(nuevo_usuario)
    db.commit()
    print(
        f"¡Usuario 'administrador' creado con éxito para la empresa:"
        f" {company.legal_name}!"
    )
else:
  print(
      "No se encontró ninguna empresa con el RUC 20609876541. Asegúrate de"
      " haberla registrado primero."
  )