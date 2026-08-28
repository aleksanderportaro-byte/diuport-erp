from database import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Company(Base):
  __tablename__ = "companies"

  id = Column(Integer, primary_key=True, index=True)
  legal_name = Column(String(255), nullable=False)
  tax_id = Column(String(50), unique=True, nullable=False, index=True)
  address = Column(Text, nullable=True)
  currency = Column(String(10), default="PEN")
  settings = Column(JSONB, default={})
  is_active = Column(Boolean, default=True)
  created_at = Column(DateTime, server_default=func.now())

  users = relationship("User", back_populates="company", cascade="all, delete")


class User(Base):
  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True)
  company_id = Column(
      Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
  )
  username = Column(String(100), nullable=False)
  email = Column(String(150), unique=True, nullable=False, index=True)
  password_hash = Column(String(255), nullable=False)
  role = Column(String(50), default="admin")
  is_active = Column(Boolean, default=True)
  created_at = Column(DateTime, server_default=func.now())

  company = relationship("Company", back_populates="users")


class ThirdParty(Base):
  __tablename__ = "third_parties"

  id = Column(Integer, primary_key=True, index=True)
  company_id = Column(
      Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
  )
  type = Column(String(20), nullable=False)  # 'client', 'supplier', o 'both'
  document_number = Column(String(50), nullable=False)
  name = Column(String(255), nullable=False)
  address = Column(Text, nullable=True)
  email = Column(String(150), nullable=True)
  phone = Column(String(50), nullable=True)
  extra_data = Column(JSONB, default={})

  company = relationship("Company")


class Product(Base):
  __tablename__ = "products"

  id = Column(Integer, primary_key=True, index=True)
  company_id = Column(
      Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
  )
  sku = Column(String(100), nullable=False, index=True)
  name = Column(String(255), nullable=False)
  description = Column(Text, nullable=True)
  type = Column(
      String(20), default="termined", nullable=False
  )  # 'raw' (materia prima) o 'termined' (producto terminado)
  price = Column(Float, default=0.0)
  cost = Column(Float, default=0.0)
  stock = Column(Integer, default=0, nullable=False)
  is_active = Column(Boolean, default=True)

  company = relationship("Company")

  @staticmethod
  def valid_types():
    """Tipos de producto soportados por el módulo de inventario."""
    return ("raw", "termined")

  @staticmethod
  def normalize_type(raw_type):
    """Normaliza y valida el tipo de producto.

    Acepta 'raw'/'materia prima' y 'termined'/'producto terminado'/'finished'
    (case-insensitive). Lanza ValueError si el valor no es reconocido.
    """
    aliases = {
        "raw": "raw",
        "materia prima": "raw",
        "insumo": "raw",
        "termined": "termined",
        "producto terminado": "termined",
        "terminado": "termined",
        "finished": "termined",
    }
    key = (raw_type or "").strip().lower()
    normalized = aliases.get(key)
    if normalized is None:
      raise ValueError(
          f"Tipo de producto inválido: '{raw_type}'. Use 'raw' o 'termined'."
      )
    return normalized

  @property
  def type_label(self):
    return "Materia Prima" if self.type == "raw" else "Producto Terminado"
  
  
class SaleOrder(Base):
  __tablename__ = "sale_orders"

  id = Column(Integer, primary_key=True, index=True)
  company_id = Column(
      Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
  )
  client_id = Column(
      Integer, ForeignKey("third_parties.id"), nullable=False
  )  # Cliente que compra
  total_amount = Column(Float, default=0.0)
  status = Column(
      String(50), default="completed"
  )  # 'completed', 'pending', 'cancelled'
  payment_status = Column(
      String(50), default="pending"
  )  # 'pending', 'paid', 'partial' — ingreso real / cuenta por cobrar
  created_at = Column(DateTime, server_default=func.now())

  company = relationship("Company")
  client = relationship("ThirdParty")
  items = relationship(
    "SaleOrderItem", back_populates="sale_order", cascade="all, delete"
  )
  receivable = relationship(
      "AccountReceivable",
      back_populates="sale_order",
      uselist=False,
      cascade="all, delete",
  )

class SaleOrderItem(Base):
  __tablename__ = "sale_order_items"

  id = Column(Integer, primary_key=True, index=True)
  sale_order_id = Column(
      Integer, ForeignKey("sale_orders.id", ondelete="CASCADE"), nullable=False
  )
  product_id = Column(
      Integer, ForeignKey("products.id"), nullable=False
  )  # Producto vendido
  quantity = Column(Integer, nullable=False)
  unit_price = Column(Float, nullable=False)
  subtotal = Column(Float, nullable=False)

  sale_order = relationship("SaleOrder", back_populates="items")
  product = relationship("Product")
  
class PurchaseOrder(Base):
  __tablename__ = "purchase_orders"

  id = Column(Integer, primary_key=True, index=True)
  company_id = Column(
      Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
  )
  supplier_id = Column(
      Integer, ForeignKey("third_parties.id"), nullable=False
  )  # Proveedor que nos vende
  total_amount = Column(Float, default=0.0)
  status = Column(String(50), default="completed")
  payment_status = Column(
      String(50), default="pending"
  )  # 'pending', 'paid', 'partial' — deuda con el proveedor (cuenta por pagar)
  due_date = Column(DateTime, nullable=True)  # Fecha límite de pago (opcional)
  created_at = Column(DateTime, server_default=func.now())

  company = relationship("Company")
  supplier = relationship("ThirdParty")
  items = relationship(
      "PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete"
  )
  payable = relationship(
      "AccountPayable",
      back_populates="purchase_order",
      uselist=False,
      cascade="all, delete",
  )


class PurchaseOrderItem(Base):
  __tablename__ = "purchase_order_items"

  id = Column(Integer, primary_key=True, index=True)
  purchase_order_id = Column(
      Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
  )
  product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
  quantity = Column(Integer, nullable=False)
  unit_cost = Column(Float, nullable=False)
  subtotal = Column(Float, nullable=False)

  purchase_order = relationship("PurchaseOrder", back_populates="items")
  product = relationship("Product")
  
class Employee(Base):
  __tablename__ = "employees"

  id = Column(Integer, primary_key=True, index=True)
  company_id = Column(
      Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
  )
  full_name = Column(String(150), nullable=False)
  document_number = Column(String(20), nullable=False)  # DNI
  position = Column(String(100), nullable=False)  # Puesto (Ej. Operario, Administrador)
  salary = Column(Float, nullable=False, default=0.0)  # Sueldo mensual
  contract_type = Column(
      String(50), default="Indefinido"
  )  # 'Indefinido', 'Plazo Fijo', 'Honorarios'
  contract_start = Column(String(20), nullable=True)  # Inicio de contrato
  contract_end = Column(String(20), nullable=True)  # Fin de contrato (si aplica)
  vacation_days_available = Column(
      Integer, default=30
  )  # Días de vacaciones disponibles
  status = Column(
      String(50), default="active"
  )  # 'active' (activo), 'terminated' (cesado)

  company = relationship("Company")

  @staticmethod
  def valid_contract_types():
    return ("Indefinido", "Plazo Fijo", "Honorarios")

  @staticmethod
  def normalize_contract_type(raw):
    """Normaliza y valida el tipo de contrato.

    Acepta (case-insensitive): indefinido, plazo fijo, fijo, honorarios,
    recibo por honorarios, contrata, etc.
    """
    mapping = {
        "indefinido": "Indefinido",
        "planilla": "Indefinido",
        "plazo fijo": "Plazo Fijo",
        "plazo fijo definido": "Plazo Fijo",
        "fijo": "Plazo Fijo",
        "temporal": "Plazo Fijo",
        "honorarios": "Honorarios",
        "recibo por honorarios": "Honorarios",
        "servicios": "Honorarios",
    }
    key = (raw or "").strip().lower()
    normalized = mapping.get(key)
    if normalized is None:
      raise ValueError(
          f"Tipo de contrato inválido: '{raw}'. Use 'Indefinido', 'Plazo Fijo'"
          " u 'Honorarios'."
      )
    return normalized

  @staticmethod
  def valid_statuses():
    return ("active", "terminated")

  @staticmethod
  def normalize_status(raw):
    key = (raw or "").strip().lower()
    if key in ("active", "activo", "activa"):
      return "active"
    if key in ("terminated", "cesado", "cesada", "inactivo", "inactive"):
      return "terminated"
    raise ValueError(
        f"Estado inválido: '{raw}'. Use 'active' o 'terminated'."
    )

  @staticmethod
  def validate_salary(salary):
    if not isinstance(salary, (int, float)) or salary < 0:
      raise ValueError("El sueldo debe ser un número mayor o igual a 0.")
    return float(salary)

  def use_vacation_days(self, days):
    """Consume días de vacaciones de forma segura (no permite valores negativos)."""
    if not isinstance(days, int) or days <= 0:
      raise ValueError("Los días de vacaciones a usar deben ser un entero positivo.")
    if days > self.vacation_days_available:
      raise ValueError(
          f"Vacaciones insuficientes. Disponibles: {self.vacation_days_available},"
          f" solicitados: {days}."
      )
    self.vacation_days_available -= days
    return self.vacation_days_available

  @property
  def is_active(self):
    return self.status == "active"

  def __repr__(self):
    return f"<Employee #{self.id}: {self.full_name} ({self.contract_type})>"


class BillOfMaterial(Base):
  """Receta/lista de materiales que define cómo producir un producto terminado.

  La BOM indica cuántas unidades de cada materia prima (BillOfMaterialLine) se
  necesitan para fabricar output_quantity unidades del producto final
  (output_product).
  """
  __tablename__ = "bill_of_materials"

  id = Column(Integer, primary_key=True, index=True)
  company_id = Column(
      Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
  )
  output_product_id = Column(
      Integer, ForeignKey("products.id"), nullable=False
  )  # Producto terminado que se fabrica
  name = Column(String(255), nullable=False)  # Nombre de la receta
  output_quantity = Column(Integer, default=1)  # Unidades producidas por ronda
  notes = Column(Text, nullable=True)

  company = relationship("Company")
  output_product = relationship("Product", foreign_keys=[output_product_id])
  lines = relationship(
      "BillOfMaterialLine",
      back_populates="bom",
      cascade="all, delete",
    )

  @staticmethod
  def validate_product_type(product, expected_type, label):
    """Valida que el producto sea del tipo esperado (raw/termined).

    product: instancia de Product o None.
    expected_type: 'raw' o 'termined'.
    label: descripción usada en el mensaje de error.
    """
    if product is None:
      raise ValueError(f"{label} no existe.")
    if product.type != expected_type:
      expected_label = "materia prima" if expected_type == "raw" else "producto terminado"
      raise ValueError(
          f"'{product.name}' debe ser {expected_label} (tipo '{expected_type}'),"
          f" pero es '{product.type}'."
      )
    return product


class BillOfMaterialLine(Base):
  """Línea de la BOM: materia prima requerida y su cantidad por ronda."""
  __tablename__ = "bill_of_material_lines"

  id = Column(Integer, primary_key=True, index=True)
  bom_id = Column(
      Integer, ForeignKey("bill_of_materials.id", ondelete="CASCADE"), nullable=False
  )
  product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
  quantity = Column(Float, nullable=False, default=1)  # Cantidad usada por ronda

  bom = relationship("BillOfMaterial", back_populates="lines")
  product = relationship("Product")


class ProductionOrder(Base):
  """Orden de producción/ensamblaje.

  Consume insumos (materias primas) del inventario según la BOM vinculada y
  devuelve producto terminado al finalizar (status='completed').
  """
  __tablename__ = "production_orders"

  id = Column(Integer, primary_key=True, index=True)
  company_id = Column(
      Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
  )
  bom_id = Column(
      Integer, ForeignKey("bill_of_materials.id"), nullable=False
  )  # Receta a ejecutar
  quantity = Column(Integer, nullable=False, default=1)  # Nº de rondas a fabricar
  machine_time_min = Column(Float, default=0.0)  # Tiempo de máquina estimado (min)
  status = Column(
      String(50), default="pending"
  )  # 'pending', 'in_progress', 'completed', 'cancelled'
  produced_quantity = Column(Integer, default=0)  # Unidades realmente fabricadas
  total_cost = Column(Float, default=0.0)  # Costo total de producción (insumos)
  created_at = Column(DateTime, server_default=func.now())

  company = relationship("Company")
  bom = relationship("BillOfMaterial")

  def __repr__(self):
    return f"<ProductionOrder #{self.id}: {self.quantity}x BOM {self.bom_id}>"


class Expense(Base):
  """Gasto operativo general no asociado a una compra de insumos.

  Nutre el módulo financiero como egreso junto con Compras y la Planilla (RRHH).
  """
  __tablename__ = "expenses"

  id = Column(Integer, primary_key=True, index=True)
  company_id = Column(
      Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
  )
  category = Column(String(100), nullable=False)  # Ej. Servicios, Alquiler, ...
  description = Column(Text, nullable=True)
  amount = Column(Float, nullable=False, default=0.0)
  expense_date = Column(DateTime, server_default=func.now())

  company = relationship("Company")

  def __repr__(self):
    return f"<Expense #{self.id}: {self.category} {self.amount}>"


class AccountPayable(Base):
  """Cuenta por pagar derivada de una orden de compra.

  Representa la deuda con el proveedor que el módulo Finanzas consolida como
  pasivo. Al pagar, se incrementa amount_paid y, al cubrirse, el status pasa
  a 'paid'.
  """
  __tablename__ = "account_payables"

  id = Column(Integer, primary_key=True, index=True)
  company_id = Column(
      Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
  )
  purchase_order_id = Column(
      Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
  )
  supplier_id = Column(Integer, ForeignKey("third_parties.id"), nullable=False)
  amount = Column(Float, nullable=False, default=0.0)  # Monto total adeudado
  amount_paid = Column(Float, nullable=False, default=0.0)  # Monto ya pagado
  status = Column(
      String(50), default="pending"
  )  # 'pending', 'partial', 'paid'
  due_date = Column(DateTime, nullable=True)
  created_at = Column(DateTime, server_default=func.now())

  company = relationship("Company")
  purchase_order = relationship("PurchaseOrder", back_populates="payable")
  supplier = relationship("ThirdParty")

  @property
  def balance(self):
    return (self.amount or 0.0) - (self.amount_paid or 0.0)

  def apply_payment(self, db, amount):
    """Registra un pago parcial o total contra la cuenta por pagar."""
    if amount <= 0:
      raise ValueError("El monto del pago debe ser mayor a 0.")
    if amount > self.balance:
      raise ValueError(
          f"El pago excede el saldo pendiente ({round(self.balance, 2)})."
      )
    self.amount_paid += amount
    if self.balance <= 0:
      self.status = "paid"
    else:
      self.status = "partial"
    return self.balance

  def __repr__(self):
    return f"<AccountPayable #{self.id}: {self.amount} - {self.amount_paid}>"


class AccountReceivable(Base):
  """Cuenta por cobrar derivada de una orden de venta.

  Representa el ingreso/crédito a favor de la empresa por la venta. El monto
  de la venta se registra como ingreso real en Finanzas al crearse la orden
  (status='completed'); esta cuenta permite darle trazabilidad al cobro.
  """
  __tablename__ = "account_receivables"

  id = Column(Integer, primary_key=True, index=True)
  company_id = Column(
      Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
  )
  sale_order_id = Column(
      Integer, ForeignKey("sale_orders.id", ondelete="CASCADE"), nullable=False
  )
  client_id = Column(Integer, ForeignKey("third_parties.id"), nullable=False)
  amount = Column(Float, nullable=False, default=0.0)  # Monto total del ingreso
  amount_received = Column(Float, nullable=False, default=0.0)  # Monto cobrado
  status = Column(
      String(50), default="pending"
  )  # 'pending', 'partial', 'paid'
  due_date = Column(DateTime, nullable=True)
  created_at = Column(DateTime, server_default=func.now())

  company = relationship("Company")
  sale_order = relationship("SaleOrder", back_populates="receivable")
  client = relationship("ThirdParty")

  @property
  def balance(self):
    return (self.amount or 0.0) - (self.amount_received or 0.0)

  def apply_receipt(self, db, amount):
    """Registra un cobro (parcial o total) contra la cuenta por cobrar."""
    if amount <= 0:
      raise ValueError("El monto del cobro debe ser mayor a 0.")
    if amount > self.balance:
      raise ValueError(
          f"El cobro excede el saldo pendiente ({round(self.balance, 2)})."
      )
    self.amount_received += amount
    if self.balance <= 0:
      self.status = "paid"
    else:
      self.status = "partial"
    return self.balance

  def __repr__(self):
    return f"<AccountReceivable #{self.id}: {self.amount} - {self.amount_received}>"