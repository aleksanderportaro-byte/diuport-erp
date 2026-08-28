import os
from core.models import (
    AccountPayable,
    AccountReceivable,
    BillOfMaterial,
    BillOfMaterialLine,
    Company,
    Employee,
    Expense,
    Product,
    ProductionOrder,
    PurchaseOrder,
    PurchaseOrderItem,
    SaleOrder,
    SaleOrderItem,
    ThirdParty,
    User,
)
from database import get_db
from flask import Flask, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func
import io

app = Flask(__name__)


@app.route("/")
def home():
  return render_template("index.html")


@app.route("/dashboard")
def dashboard():
  return render_template("dashboard.html")


# =====================================================================
# VISTAS HTML INDEPENDIENTES POR MÓDULO
# (rutas /dashboard/*; el CRUD POST/PUT/DELETE y el upload con Pandas se
#  sirven a través de los endpoints /api/* que cada plantilla consume vía JS)
# =====================================================================


def _company_context(db):
  """Devuelve el (ids de) contexto de empresa que se reutiliza en las vistas.

  Retorna (company, companies): la primera empresa activa (o None) y la lista
  de todas las empresas disponibles para poblar los jselects de los formularios.
  """
  companies = db.query(Company).order_by(Company.legal_name).all()
  company = next((c for c in companies if c.is_active), None)
  return company, companies


def _serialize_third_party(tp):
  return {
      "id": tp.id,
      "company_id": tp.company_id,
      "type": tp.type,
      "document_number": tp.document_number,
      "name": tp.name,
      "address": tp.address,
      "email": tp.email,
      "phone": tp.phone,
  }


def _serialize_product(p):
  return {
      "id": p.id,
      "company_id": p.company_id,
      "sku": p.sku,
      "name": p.name,
      "description": p.description,
      "type": p.type,
      "type_label": p.type_label,
      "price": p.price,
      "cost": p.cost,
      "stock": p.stock,
      "is_active": p.is_active,
  }


def _serialize_company(c):
  return {
      "id": c.id,
      "name": c.legal_name,
      "ruc": c.tax_id,
      "address": c.address,
      "currency": c.currency,
      "is_active": c.is_active,
  }


def _serialize_employee(e):
  return {
      "id": e.id,
      "company_id": e.company_id,
      "full_name": e.full_name,
      "document_number": e.document_number,
      "position": e.position,
      "salary": e.salary,
      "contract_type": e.contract_type,
      "contract_start": e.contract_start,
      "contract_end": e.contract_end,
      "vacation_days_available": e.vacation_days_available,
      "status": e.status,
  }


# --- MÓDULO VENTAS -----------------------------------------------------
@app.route("/dashboard/ventas")
def view_ventas():
  db = next(get_db())
  sales = db.query(SaleOrder).order_by(SaleOrder.created_at.desc()).all()
  clients = db.query(ThirdParty).filter(
      ThirdParty.type.in_(("client", "both"))
  ).order_by(ThirdParty.name).all()
  products = db.query(Product).order_by(Product.name).all()
  company, companies = _company_context(db)
  return render_template(
      "ventas.html",
      sales=[
          {
              "id": s.id,
              "company_id": s.company_id,
              "client_id": s.client_id,
              "client": s.client.name if s.client else "",
              "total_amount": s.total_amount,
              "status": s.status,
              "payment_status": s.payment_status,
              "created_at": s.created_at.isoformat() if s.created_at else None,
          }
          for s in sales
      ],
      clients=[_serialize_third_party(c) for c in clients],
      products=[_serialize_product(p) for p in products],
      companies=[_serialize_company(c) for c in companies],
      company=company,
  )


@app.route("/ventas")
def view_ventas_legacy():
  return redirect(url_for("view_ventas"))


# --- MÓDULO COMPRAS ----------------------------------------------------
@app.route("/dashboard/compras")
def view_compras():
  db = next(get_db())
  purchases = db.query(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).all()
  suppliers = db.query(ThirdParty).filter(
      ThirdParty.type.in_(("supplier", "both"))
  ).order_by(ThirdParty.name).all()
  products = db.query(Product).order_by(Product.name).all()
  company, companies = _company_context(db)
  return render_template(
      "compras.html",
      purchases=[
          {
              "id": p.id,
              "company_id": p.company_id,
              "supplier_id": p.supplier_id,
              "supplier": p.supplier.name if p.supplier else "",
              "total_amount": p.total_amount,
              "status": p.status,
              "payment_status": p.payment_status,
              "due_date": p.due_date.isoformat() if p.due_date else None,
              "created_at": p.created_at.isoformat() if p.created_at else None,
          }
          for p in purchases
      ],
      suppliers=[_serialize_third_party(s) for s in suppliers],
      products=[_serialize_product(p) for p in products],
      companies=[_serialize_company(c) for c in companies],
      company=company,
  )


@app.route("/compras")
def view_compras_legacy():
  return redirect(url_for("view_compras"))


# --- MÓDULO ABASTECIMIENTO (inventario) --------------------------------
@app.route("/dashboard/abastecimiento")
def view_abastecimiento():
  db = next(get_db())
  products = db.query(Product).order_by(Product.name).all()
  suppliers = db.query(ThirdParty).filter(
      ThirdParty.type.in_(("supplier", "both"))
  ).order_by(ThirdParty.name).all()
  company, companies = _company_context(db)
  return render_template(
      "abastecimiento.html",
      products=[_serialize_product(p) for p in products],
      suppliers=[_serialize_third_party(s) for s in suppliers],
      companies=[_serialize_company(c) for c in companies],
      company=company,
  )


@app.route("/abastecimiento")
def view_abastecimiento_legacy():
  return redirect(url_for("view_abastecimiento"))


# --- MÓDULO PRODUCCIÓN --------------------------------------------------
@app.route("/dashboard/produccion")
def view_produccion():
  db = next(get_db())
  orders = db.query(ProductionOrder).order_by(
      ProductionOrder.created_at.desc()
  ).all()
  boms = db.query(BillOfMaterial).order_by(BillOfMaterial.name).all()
  products = db.query(Product).order_by(Product.name).all()
  company, companies = _company_context(db)
  return render_template(
      "produccion.html",
      orders=[
          {
              "id": o.id,
              "company_id": o.company_id,
              "bom_id": o.bom_id,
              "bom": o.bom.name if o.bom else "",
              "quantity": o.quantity,
              "machine_time_min": o.machine_time_min,
              "status": o.status,
              "produced_quantity": o.produced_quantity,
              "total_cost": o.total_cost,
              "created_at": o.created_at.isoformat() if o.created_at else None,
          }
          for o in orders
      ],
      boms=[
          {
              "id": b.id,
              "company_id": b.company_id,
              "output_product_id": b.output_product_id,
              "name": b.name,
              "output_quantity": b.output_quantity,
              "notes": b.notes,
          }
          for b in boms
      ],
      products=[_serialize_product(p) for p in products],
      companies=[_serialize_company(c) for c in companies],
      company=company,
  )


@app.route("/produccion")
def view_produccion_legacy():
  return redirect(url_for("view_produccion"))


# --- MÓDULO RRHH --------------------------------------------------------
@app.route("/dashboard/rrhh")
def view_rrhh():
  db = next(get_db())
  employees = db.query(Employee).order_by(Employee.full_name).all()
  company, companies = _company_context(db)
  return render_template(
      "rrhh.html",
      employees=[_serialize_employee(e) for e in employees],
      companies=[_serialize_company(c) for c in companies],
      company=company,
  )


@app.route("/rrhh")
def view_rrhh_legacy():
  return redirect(url_for("view_rrhh"))


# --- MÓDULO FINANZAS ----------------------------------------------------
@app.route("/dashboard/finanzas")
def view_finanzas():
  db = next(get_db())
  expenses = db.query(Expense).order_by(Expense.expense_date.desc()).all()
  receivables = db.query(AccountReceivable).order_by(
      AccountReceivable.created_at.desc()
  ).all()
  payables = db.query(AccountPayable).order_by(
      AccountPayable.created_at.desc()
  ).all()
  company, companies = _company_context(db)
  return render_template(
      "finanzas.html",
      expenses=[
          {
              "id": e.id,
              "company_id": e.company_id,
              "category": e.category,
              "description": e.description,
              "amount": e.amount,
              "expense_date": e.expense_date.isoformat()
              if e.expense_date else None,
          }
          for e in expenses
      ],
      receivables=[
          {
              "id": r.id,
              "company_id": r.company_id,
              "sale_order_id": r.sale_order_id,
              "client": r.client.name if r.client else "",
              "amount": r.amount,
              "amount_received": r.amount_received,
              "balance": r.balance,
              "status": r.status,
              "due_date": r.due_date.isoformat() if r.due_date else None,
          }
          for r in receivables
      ],
      payables=[
          {
              "id": p.id,
              "company_id": p.company_id,
              "purchase_order_id": p.purchase_order_id,
              "supplier": p.supplier.name if p.supplier else "",
              "amount": p.amount,
              "amount_paid": p.amount_paid,
              "balance": p.balance,
              "status": p.status,
              "due_date": p.due_date.isoformat() if p.due_date else None,
          }
          for p in payables
      ],
      companies=[_serialize_company(c) for c in companies],
      company=company,
  )


@app.route("/finanzas")
def view_finanzas_legacy():
  return redirect(url_for("view_finanzas"))


# --- MÓDULO PROYECCIONES (solo lectura) --------------------------------
@app.route("/dashboard/proyecciones")
def view_proyecciones():
  db = next(get_db())
  company, companies = _company_context(db)
  return render_template(
      "proyecciones.html",
      companies=[_serialize_company(c) for c in companies],
      company=company,
  )


@app.route("/proyecciones")
def view_proyecciones_legacy():
  return redirect(url_for("view_proyecciones"))


# --- MÓDULO EMPRESAS ---


@app.route("/api/companies", methods=["GET"])
def get_companies():
  db = next(get_db())
  companies = db.query(Company).all()
  result = [
      {
          "id": c.id,
          "name": c.legal_name,
          "ruc": c.tax_id,
          "address": c.address,
          "currency": c.currency,
      }
      for c in companies
  ]
  return jsonify(result)


@app.route("/api/companies", methods=["POST"])
def create_company():
  data = request.get_json()
  db = next(get_db())

  try:
    new_company = Company(
        legal_name=data.get("legal_name"),
        tax_id=data.get("tax_id"),
        address=data.get("address", ""),
        currency=data.get("currency", "PEN"),
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    return (
        jsonify({
            "status": "success",
            "message": "¡Empresa registrada con éxito en el ERP!",
            "company_id": new_company.id,
        }),
        201,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


# --- MÓDULO TERCEROS (CLIENTES Y PROVEEDORES) ---


@app.route("/api/third-parties", methods=["GET"])
def get_third_parties():
  db = next(get_db())
  third_parties = db.query(ThirdParty).all()
  result = [
      {
          "id": tp.id,
          "company_id": tp.company_id,
          "type": tp.type,
          "document_number": tp.document_number,
          "name": tp.name,
          "email": tp.email,
          "phone": tp.phone,
      }
      for tp in third_parties
  ]
  return jsonify(result)


@app.route("/api/third-parties", methods=["POST"])
def create_third_party():
  data = request.get_json()
  db = next(get_db())

  try:
    new_tp = ThirdParty(
        company_id=data.get("company_id"),
        type=data.get("type", "client"),
        document_number=data.get("document_number"),
        name=data.get("name"),
        address=data.get("address", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
    )
    db.add(new_tp)
    db.commit()
    db.refresh(new_tp)

    return (
        jsonify({
            "status": "success",
            "message": "¡Tercero registrado con éxito!",
            "third_party_id": new_tp.id,
        }),
        201,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


# --- MÓDULO PRODUCTOS E INVENTARIO ---


def _adjust_stock(db, product, delta):
  """Ajusta el stock de un producto de forma segura.

  - Adquiere un bloqueo a nivel de fila (FOR UPDATE) para evitar condiciones
    de carrera entre solicitudes concurrentes (ventas/producción/ajustes).
  - Rechaza cualquier operación que deje el stock en negativo, devolviendo
    un mensaje con el stock disponible.
  """
  db.refresh(
      product, with_for_update={"read": True}
  )  # Fija el valor actual con lock de fila
  if product.stock is None:
    product.stock = 0

  new_stock = product.stock + delta
  if new_stock < 0:
    raise ValueError(
        f"Stock insuficiente para '{product.name}'. Disponible: {product.stock},"
        f" requerido: {-delta}."
    )
  product.stock = new_stock
  return new_stock


@app.route("/api/products", methods=["GET"])
def get_products():
  db = next(get_db())
  q = db.query(Product)

  company_id = request.args.get("company_id", type=int)
  prod_type = request.args.get("type", type=str)
  search = request.args.get("search", type=str)

  if company_id is not None:
    q = q.filter(Product.company_id == company_id)
  if prod_type in ("raw", "termined"):
    q = q.filter(Product.type == prod_type)
  if search:
    like = f"%{search}%"
    q = q.filter(db.or_(Product.name.ilike(like), Product.sku.ilike(like)))

  products = q.order_by(Product.name).all()
  result = [
      {
          "id": p.id,
          "company_id": p.company_id,
          "sku": p.sku,
          "name": p.name,
          "description": p.description,
          "type": p.type,
          "type_label": p.type_label,
          "price": p.price,
          "cost": p.cost,
          "stock": p.stock,
          "is_active": p.is_active,
      }
      for p in products
  ]
  return jsonify(result)


@app.route("/api/products", methods=["POST"])
def create_product():
  data = request.get_json()
  db = next(get_db())

  try:
    try:
      product_type = Product.normalize_type(data.get("type", "termined"))
    except ValueError as e:
      return jsonify({"status": "error", "message": str(e)}), 400

    stock = data.get("stock", 0)
    if not isinstance(stock, int) or stock < 0:
      return (
          jsonify({
              "status": "error",
              "message": "El stock inicial debe ser un entero mayor o igual a 0.",
          }),
          400,
      )

    new_product = Product(
        company_id=data.get("company_id"),
        sku=data.get("sku"),
        name=data.get("name"),
        description=data.get("description", ""),
        type=product_type,
        price=data.get("price", 0.0),
        cost=data.get("cost", 0.0),
        stock=stock,
        is_active=data.get("is_active", True),
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return (
        jsonify({
            "status": "success",
            "message": "¡Producto registrado con éxito en el inventario!",
            "product_id": new_product.id,
            "type": new_product.type,
            "stock": new_product.stock,
        }),
        201,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
  db = next(get_db())
  p = db.query(Product).get(product_id)
  if not p:
    return jsonify({"status": "error", "message": "Producto no encontrado."}), 404
  return jsonify({
      "id": p.id,
      "company_id": p.company_id,
      "sku": p.sku,
      "name": p.name,
      "description": p.description,
      "type": p.type,
      "type_label": p.type_label,
      "price": p.price,
      "cost": p.cost,
      "stock": p.stock,
      "is_active": p.is_active,
  })


@app.route("/api/products/<int:product_id>/stock", methods=["POST"])
def update_product_stock(product_id):
  """Actualiza el stock de un producto.

  Body: {"op": "set"|"increase"|"decrease", "amount": <cantidad>}

  - 'set': fija el stock a la cantidad absoluta (no puede ser negativa).
  - 'increase': suma la cantidad (ajuste por entrada, siempre >= 0).
  - 'decrease': resta la cantidad (ajuste por salida), nunca deja el stock < 0.
  """
  data = request.get_json()
  db = next(get_db())

  try:
    product = (
        db.query(Product)
        .filter_by(id=product_id)
        .with_for_update()
        .first()
    )
    if not product:
      return (
          jsonify({
              "status": "error",
              "message": f"Producto con ID {product_id} no encontrado.",
          }),
          404,
      )

    op = (data.get("op") or "").lower()
    amount = data.get("amount", 0)

    if not isinstance(amount, int):
      return (
          jsonify({
              "status": "error",
              "message": "El parámetro 'amount' debe ser un entero.",
          }),
          400,
      )

    if op == "set":
      if amount < 0:
        return (
            jsonify({
                "status": "error",
                "message": "El stock no puede ser negativo.",
            }),
            400,
        )
      product.stock = amount
      new_stock = amount
    elif op == "increase":
      if amount < 0:
        return (
            jsonify({
                "status": "error",
                "message": "'amount' debe ser mayor o igual a 0 para 'increase'.",
            }),
            400,
        )
      product.stock = (product.stock or 0) + amount
      new_stock = product.stock
    elif op == "decrease":
      if amount < 0:
        return (
            jsonify({
                "status": "error",
                "message": "'amount' debe ser mayor o igual a 0 para 'decrease'.",
            }),
            400,
        )
      try:
        new_stock = _adjust_stock(db, product, -amount)
      except ValueError as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    else:
      return (
          jsonify({
              "status": "error",
              "message": "Operación inválida. Use 'set', 'increase' o 'decrease'.",
          }),
          400,
      )

    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Stock actualizado.",
            "product_id": product.id,
            "stock": new_stock,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


# --- CRUD COMPLETO Y SUBIDA DE ARCHIVOS (CSV/EXCEL) ---


def _read_upload_df(uploaded_file):
  """Lee un CSV/Excel enviado por multipart y devuelve un DataFrame de pandas.

  Reconoce la extensión por el nombre del archivo; devuelve (df, filename).
  Lanza ValueError si el formato no es soportado o no tiene filas.
  """
  import pandas as pd

  filename = (uploaded_file.filename or "").lower()
  raw = uploaded_file.read()

  if filename.endswith(".csv"):
    df = pd.read_csv(io.BytesIO(raw))
  elif filename.endswith(".xls"):
    df = pd.read_excel(io.BytesIO(raw), engine="xlrd")
  elif filename.endswith((".xlsx", ".xlsm")):
    df = pd.read_excel(io.BytesIO(raw), engine="openpyxl")
  else:
    raise ValueError(
        "Formato no soportado. Sube un archivo .csv, .xls o .xlsx."
    )

  df = df.dropna(how="all")
  if df.empty:
    raise ValueError("El archivo no contiene filas de datos.")
  return df.reindex(columns=df.columns).reset_index(drop=True), filename


def _parse_row_str(value):
  """Normaliza un valor a string limpio (NaN/None -> '')."""
  if value is None:
    return ""
  try:
    if isinstance(value, float) and value != value:  # NaN
      return ""
  except Exception:
    pass
  if isinstance(value, float) and value.is_integer():
    return str(int(value))
  return str(value).strip()


# ---- PRODUCTOS / INVENTARIO (CRUD + subida) ----


@app.route("/api/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
  data = request.get_json()
  db = next(get_db())
  try:
    product = db.query(Product).get(product_id)
    if not product:
      return (
          jsonify({"status": "error", "message": "Producto no encontrado."}),
          404,
      )
    if "type" in data:
      try:
        product.type = Product.normalize_type(data.get("type"))
      except ValueError as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    if "sku" in data:
      product.sku = data.get("sku")
    if "name" in data:
      product.name = data.get("name")
    if "description" in data:
      product.description = data.get("description")
    if "price" in data:
      product.price = data.get("price", product.price)
    if "cost" in data:
      product.cost = data.get("cost", product.cost)
    if "stock" in data:
      stock = data.get("stock")
      if not isinstance(stock, int) or stock < 0:
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": "El stock debe ser un entero >= 0.",
            }),
            400,
        )
      product.stock = stock

    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Producto actualizado.",
            "product_id": product.id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
  db = next(get_db())
  try:
    product = db.query(Product).get(product_id)
    if not product:
      return (
          jsonify({"status": "error", "message": "Producto no encontrado."}),
          404,
      )
    db.delete(product)
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Producto eliminado.",
            "product_id": product_id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/products/upload", methods=["POST"])
def upload_products():
  db = next(get_db())
  try:
    df, fname = _read_upload_df(request.files["file"])
    # Mapeo tolerante de columnas
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    company_id = request.form.get("company_id", 1, type=int)

    created, errors = 0, []
    for idx, r in df.iterrows():
      try:
        price = float(r.get("price", 0) or 0)
        cost = float(r.get("cost", 0) or 0)
        stock = int(r.get("stock", 0) or 0)
        product_type = Product.normalize_type(
            r.get("type", r.get("tipo", "termined"))
        )
        db.add(Product(
            company_id=company_id,
            sku=_parse_row_str(r.get("sku")),
            name=_parse_row_str(r.get("name", r.get("nombre"))),
            description=_parse_row_str(r.get("description", r.get("descripcion"))),
            type=product_type,
            price=price,
            cost=cost,
            stock=stock,
        ))
        created += 1
      except Exception as e:
        errors.append(f"Fila {idx + 2}: {e}")
    db.commit()
    return jsonify({
        "status": "success",
        "created": created,
        "errors": errors,
    }), 200
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


# ---- TERCEROS (CLIENTES / PROVEEDORES) CRUD + subida ----


@app.route("/api/third-parties/<int:tp_id>", methods=["PUT"])
def update_third_party(tp_id):
  data = request.get_json()
  db = next(get_db())
  try:
    tp = db.query(ThirdParty).get(tp_id)
    if not tp:
      return (
          jsonify({"status": "error", "message": "Tercero no encontrado."}),
          404,
      )
    if "type" in data:
      tp.type = data.get("type")
    if "document_number" in data:
      tp.document_number = data.get("document_number")
    if "name" in data:
      tp.name = data.get("name")
    if "address" in data:
      tp.address = data.get("address")
    if "email" in data:
      tp.email = data.get("email")
    if "phone" in data:
      tp.phone = data.get("phone")
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Tercero actualizado.",
            "third_party_id": tp.id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/third-parties/<int:tp_id>", methods=["DELETE"])
def delete_third_party(tp_id):
  db = next(get_db())
  try:
    tp = db.query(ThirdParty).get(tp_id)
    if not tp:
      return (
          jsonify({"status": "error", "message": "Tercero no encontrado."}),
          404,
      )
    db.delete(tp)
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Tercero eliminado.",
            "third_party_id": tp_id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/third-parties/upload", methods=["POST"])
def upload_third_parties():
  db = next(get_db())
  try:
    df, fname = _read_upload_df(request.files["file"])
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    company_id = request.form.get("company_id", 1, type=int)

    created, errors = 0, []
    for idx, r in df.iterrows():
      try:
        tp_type = _parse_row_str(r.get("type", r.get("tipo", "client")))
        if tp_type not in ("client", "supplier", "both"):
          raise ValueError("Tipo inválido (client/supplier/both).")
        db.add(ThirdParty(
            company_id=company_id,
            type=tp_type,
            document_number=_parse_row_str(r.get("document_number", r.get("documento"))),
            name=_parse_row_str(r.get("name", r.get("nombre"))),
            address=_parse_row_str(r.get("address", r.get("direccion"))),
            email=_parse_row_str(r.get("email")),
            phone=_parse_row_str(r.get("phone", r.get("telefono"))),
        ))
        created += 1
      except Exception as e:
        errors.append(f"Fila {idx + 2}: {e}")
    db.commit()
    return jsonify({"status": "success", "created": created, "errors": errors}), 200
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/third-parties/clients", methods=["GET"])
def get_clients():
  db = next(get_db())
  rows = (
      db.query(ThirdParty)
      .filter(ThirdParty.type.in_(("client", "both")))
      .all()
  )
  return jsonify([{"id": t.id, "name": t.name, "document_number": t.document_number}
      for t in rows])


@app.route("/api/third-parties/suppliers", methods=["GET"])
def get_suppliers():
  db = next(get_db())
  rows = (
      db.query(ThirdParty)
      .filter(ThirdParty.type.in_(("supplier", "both")))
      .all()
  )
  return jsonify([{"id": t.id, "name": t.name, "document_number": t.document_number}
      for t in rows])


# --- MÓDULO DE VENTAS (SALES) ---


@app.route("/api/sales", methods=["GET"])
def get_sales():
  db = next(get_db())
  company_id = request.args.get("company_id", type=int)
  q = db.query(SaleOrder)
  if company_id is not None:
    q = q.filter(SaleOrder.company_id == company_id)
  sales = q.order_by(SaleOrder.created_at.desc()).all()
  result = []
  for s in sales:
    receivable = s.receivable
    items_list = [{
        "product_id": i.product_id,
        "product_name": i.product.name if i.product else None,
        "quantity": i.quantity,
        "unit_price": i.unit_price,
        "subtotal": i.subtotal,
    } for i in s.items]

    result.append({
        "sale_id": s.id,
        "company_id": s.company_id,
        "client_id": s.client_id,
        "client_name": s.client.name if s.client else None,
        "total_amount": s.total_amount,
        "status": s.status,
        "payment_status": s.payment_status,
        "receivable_balance": round(receivable.balance, 2) if receivable else None,
        "items": items_list,
    })
  return jsonify(result)


@app.route("/api/sales", methods=["POST"])
def create_sale():
  data = request.get_json()
  db = next(get_db())

  try:
    company_id = data.get("company_id")
    client_id = data.get("client_id")
    items_data = data.get("items", [])
    due_date = data.get("due_date", None)

    if not items_data:
      return (
          jsonify({
              "status": "error",
              "message": "La venta debe incluir al menos un producto.",
          }),
          400,
      )

    # El cliente debe existir y ser de tipo 'client' (o 'both')
    client = (
        db.query(ThirdParty)
        .filter(ThirdParty.id == client_id, ThirdParty.company_id == company_id)
        .with_for_update()
        .first()
    )
    if not client:
      db.rollback()
      return (
          jsonify({
              "status": "error",
              "message": f"Cliente con ID {client_id} no encontrado.",
          }),
          404,
      )
    if client.type not in ("client", "both"):
      db.rollback()
      return (
          jsonify({
              "status": "error",
              "message": (
                  f"'{client.name}' no es un cliente (tipo '{client.type}')."
                  " Use un ThirdParty de tipo 'client'."
              ),
          }),
          400,
      )

    total_amount = 0.0
    new_sale = SaleOrder(
        company_id=company_id,
        client_id=client_id,
        total_amount=0.0,
        status="completed",  # Ingreso real: cuenta en el reporte financiero
        payment_status="pending",
    )
    db.add(new_sale)
    db.flush()

    for item in items_data:
      product_id = item.get("product_id")
      quantity = item.get("quantity")

      if not isinstance(quantity, int) or quantity <= 0:
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": "La cantidad de cada ítem debe ser un entero positivo.",
            }),
            400,
        )

      # Bloqueo de fila (FOR UPDATE) para lectura/descuento atómicos
      product = (
          db.query(Product)
          .filter_by(id=product_id, company_id=company_id)
          .with_for_update()
          .first()
      )
      if not product:
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": f"Producto con ID {product_id} no encontrado.",
            }),
            404,
        )

      # Solo se vende producto terminado ('termined')
      if product.type != "termined":
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": (
                    f"'{product.name}' es materia prima (tipo 'raw');"
                    " solo se pueden vender productos terminados ('termined')."
                ),
            }),
            400,
        )

      # Descuento atómico y con validación de stock suficiente
      try:
        _adjust_stock(db, product, -quantity)
      except ValueError as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

      unit_price = product.price
      subtotal = unit_price * quantity
      total_amount += subtotal

      sale_item = SaleOrderItem(
          sale_order_id=new_sale.id,
          product_id=product_id,
          quantity=quantity,
          unit_price=unit_price,
          subtotal=subtotal,
      )
      db.add(sale_item)

    new_sale.total_amount = total_amount

    # Registrar el ingreso como cuenta por cobrar (trazabilidad en Finanzas)
    receivable = AccountReceivable(
        company_id=company_id,
        sale_order_id=new_sale.id,
        client_id=client_id,
        amount=total_amount,
        amount_received=0.0,
        status="pending",
        due_date=due_date,
    )
    db.add(receivable)

    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "¡Venta registrada como ingreso, stock actualizado y cuenta por cobrar creada!",
            "sale_id": new_sale.id,
            "total_amount": total_amount,
            "receivable_id": receivable.id,
        }),
        201,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/receivables", methods=["GET"])
def get_receivables():
  db = next(get_db())
  company_id = request.args.get("company_id", type=int)
  status = request.args.get("status", type=str)
  q = db.query(AccountReceivable)
  if company_id is not None:
    q = q.filter(AccountReceivable.company_id == company_id)
  if status in ("pending", "partial", "paid"):
    q = q.filter(AccountReceivable.status == status)
  receivables = q.order_by(AccountReceivable.created_at.desc()).all()
  result = [{
      "id": ar.id,
      "company_id": ar.company_id,
      "sale_order_id": ar.sale_order_id,
      "client_id": ar.client_id,
      "client_name": ar.client.name if ar.client else None,
      "amount": ar.amount,
      "amount_received": ar.amount_received,
      "balance": round(ar.balance, 2),
      "status": ar.status,
      "due_date": str(ar.due_date) if ar.due_date else None,
  } for ar in receivables]
  return jsonify(result)


@app.route("/api/receivables/<int:receivable_id>/collect", methods=["POST"])
def collect_receivable(receivable_id):
  """Registra un cobro (parcial o total) contra una cuenta por cobrar."""
  data = request.get_json()
  db = next(get_db())

  try:
    receivable = (
        db.query(AccountReceivable)
        .filter_by(id=receivable_id)
        .with_for_update()
        .first()
    )
    if not receivable:
      return (
          jsonify({
              "status": "error",
              "message": f"Cuenta por cobrar {receivable_id} no encontrada.",
          }),
          404,
      )

    amount = data.get("amount", 0.0)
    try:
      balance = receivable.apply_receipt(db, amount)
    except ValueError as e:
      db.rollback()
      return jsonify({"status": "error", "message": str(e)}), 400

    order = db.query(SaleOrder).get(receivable.sale_order_id)
    if order:
      order.payment_status = receivable.status

    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Cobro registrado.",
            "receivable_id": receivable.id,
            "amount_received": receivable.amount_received,
            "balance": round(balance, 2),
            "status": receivable.status,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


# --- CRUD VENTAS (editar estado, cancelar, subida) ---


@app.route("/api/sales/<int:sale_id>", methods=["PUT"])
def update_sale(sale_id):
  """Actualiza campos editables de una venta (estado / estado de pago)."""
  data = request.get_json()
  db = next(get_db())
  try:
    sale = db.query(SaleOrder).get(sale_id)
    if not sale:
      return jsonify({"status": "error", "message": "Venta no encontrada."}), 404

    if "payment_status" in data:
      new_status = data.get("payment_status")
      if new_status not in ("pending", "partial", "paid"):
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": "Estado de pago inválido.",
            }),
            400,
        )
      sale.payment_status = new_status
    if "status" in data:
      new_status = data.get("status")
      if new_status not in ("completed", "pending", "cancelled"):
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": "Estado de venta inválido.",
            }),
            400,
        )
      sale.status = new_status

    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Venta actualizada.",
            "sale_id": sale.id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/sales/<int:sale_id>", methods=["DELETE"])
def delete_sale(sale_id):
  """Cancela una venta devolviendo el stock de sus productos al inventario."""
  db = next(get_db())
  try:
    sale = db.query(SaleOrder).get(sale_id)
    if not sale:
      return jsonify({"status": "error", "message": "Venta no encontrada."}), 404

    for item in sale.items:
      product = db.query(Product).get(item.product_id)
      if product:
        product.stock = (product.stock or 0) + item.quantity

    db.delete(sale)
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Venta eliminada y stock restaurado.",
            "sale_id": sale_id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/sales/upload", methods=["POST"])
def upload_sales():
  """Importa ventas desde CSV/Excel: cliente_ruc, producto_sku, cantidad,
  estado_pago. Crea la orden de venta validando stock (solo termined)."""
  db = next(get_db())
  try:
    df, fname = _read_upload_df(request.files["file"])
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    company_id = request.form.get("company_id", 1, type=int)

    created, errors = 0, []
    for idx, r in df.iterrows():
      try:
        ruc = _parse_row_str(r.get("cliente_ruc", r.get("ruc")))
        sku = _parse_row_str(r.get("producto_sku", r.get("sku")))
        quantity = int(r.get("cantidad", 1) or 1)
        payment_status = _parse_row_str(
            r.get("estado_pago", r.get("pago", "paid"))
        )

        if not ruc or not sku:
          raise ValueError("Faltan cliente_ruc o producto_sku.")

        client = (
            db.query(ThirdParty)
            .filter(
                ThirdParty.company_id == company_id,
                ThirdParty.document_number == ruc,
                ThirdParty.type.in_(("client", "both")),
            )
            .first()
        )
        if not client:
          raise ValueError(f"Cliente con RUC {ruc} no encontrado.")

        product = (
            db.query(Product)
            .filter_by(company_id=company_id, sku=sku)
            .with_for_update()
            .first()
        )
        if not product:
          raise ValueError(f"Producto con SKU {sku} no encontrado.")
        if product.type != "termined":
          raise ValueError(f"'{product.name}' no es producto terminado.")

        try:
          _adjust_stock(db, product, -quantity)
        except ValueError as e:
          raise ValueError(str(e))

        total = product.price * quantity
        sale = SaleOrder(
            company_id=company_id,
            client_id=client.id,
            total_amount=total,
            status="completed",
            payment_status=payment_status if payment_status in (
                "pending", "partial", "paid") else "paid",
        )
        db.add(sale)
        db.flush()
        db.add(SaleOrderItem(
            sale_order_id=sale.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.price,
            subtotal=total,
        ))
        db.add(AccountReceivable(
            company_id=company_id,
            sale_order_id=sale.id,
            client_id=client.id,
            amount=total,
            amount_received=(
                total if payment_status == "paid"
                else (total * 0.5 if payment_status == "partial" else 0.0)
            ),
            status=(
                "paid" if payment_status == "paid"
                else ("partial" if payment_status == "partial" else "pending")
            ),
        ))
        created += 1
      except Exception as e:
        db.rollback()
        errors.append(f"Fila {idx + 2}: {e}")

    db.commit()
    return jsonify({"status": "success", "created": created, "errors": errors}), 200
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


# --- MÓDULO DE AUTENTICACIÓN (LOGIN) ---


@app.route("/api/login", methods=["POST"])
def login():
  data = request.get_json()
  db = next(get_db())

  ruc = data.get("ruc")
  username = data.get("username")
  password = data.get("password")

  try:
    company = db.query(Company).filter_by(tax_id=ruc).first()
    if not company:
      return (
          jsonify({
              "status": "error",
              "message": "El RUC de la empresa no está registrado.",
          }),
          404,
      )

    user = (
        db.query(User)
        .filter_by(company_id=company.id, username=username)
        .first()
    )
    if not user:
      return (
          jsonify({
              "status": "error",
              "message": "Usuario no encontrado en esta empresa.",
          }),
          404,
      )

    if user.password_hash != password:
      return (
          jsonify({"status": "error", "message": "Contraseña incorrecta."}),
          401,
      )

    return jsonify({
        "status": "success",
        "message": "¡Bienvenido al sistema!",
        "company_id": company.id,
        "user": user.username,
    })

  except Exception as e:
    return jsonify({"status": "error", "message": str(e)}), 500

# --- MÓDULO DE COMPRAS (PURCHASES) ---


@app.route("/api/purchases", methods=["GET"])
def get_purchases():
  db = next(get_db())
  company_id = request.args.get("company_id", type=int)
  q = db.query(PurchaseOrder)
  if company_id is not None:
    q = q.filter(PurchaseOrder.company_id == company_id)
  purchases = q.order_by(PurchaseOrder.created_at.desc()).all()
  result = []
  for p in purchases:
    payable = p.payable
    result.append({
        "purchase_id": p.id,
        "company_id": p.company_id,
        "supplier_id": p.supplier_id,
        "supplier_name": p.supplier.name if p.supplier else None,
        "total_amount": p.total_amount,
        "status": p.status,
        "payment_status": p.payment_status,
        "payable_balance": round(payable.balance, 2) if payable else None,
        "items": [
            {
                "product_id": i.product_id,
                "product_name": i.product.name if i.product else None,
                "quantity": i.quantity,
                "unit_cost": i.unit_cost,
                "subtotal": i.subtotal,
            }
            for i in p.items
        ],
    })
  return jsonify(result)


@app.route("/api/purchases", methods=["POST"])
def create_purchase():
  data = request.get_json()
  db = next(get_db())

  try:
    company_id = data.get("company_id")
    supplier_id = data.get("supplier_id")
    items_data = data.get("items", [])
    due_date = data.get("due_date", None)

    if not items_data:
      return (
          jsonify({
              "status": "error",
              "message": "La compra debe incluir al menos un producto.",
          }),
          400,
      )

    # El proveedor debe existir y ser de tipo 'supplier' (o 'both')
    supplier = (
        db.query(ThirdParty)
        .filter(ThirdParty.id == supplier_id, ThirdParty.company_id == company_id)
        .with_for_update()
        .first()
    )
    if not supplier:
      db.rollback()
      return (
          jsonify({
              "status": "error",
              "message": f"Proveedor con ID {supplier_id} no encontrado.",
          }),
          404,
      )
    if supplier.type not in ("supplier", "both"):
      db.rollback()
      return (
          jsonify({
              "status": "error",
              "message": (
                  f"'{supplier.name}' no es un proveedor (tipo '{supplier.type}')."
                  " Use un ThirdParty de tipo 'supplier'."
              ),
          }),
          400,
      )

    total_amount = 0.0
    new_purchase = PurchaseOrder(
        company_id=company_id,
        supplier_id=supplier_id,
        total_amount=0.0,
        payment_status="pending",
        due_date=due_date,
    )
    db.add(new_purchase)
    db.flush()

    for item in items_data:
      product_id = item.get("product_id")
      quantity = item.get("quantity")
      unit_cost = item.get("unit_cost", 0.0)

      if not isinstance(quantity, int) or quantity <= 0:
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": "La cantidad de cada ítem debe ser un entero positivo.",
            }),
            400,
        )
      if not isinstance(unit_cost, (int, float)) or unit_cost < 0:
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": "El costo unitario de cada ítem debe ser un número >= 0.",
            }),
            400,
        )

      product = (
          db.query(Product)
          .filter_by(id=product_id, company_id=company_id)
          .with_for_update()
          .first()
      )
      if not product:
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": f"Producto con ID {product_id} no encontrado.",
            }),
            404,
        )

      # Aumentar stock atómicamente (bloqueo de fila + validación de no negativo)
      _adjust_stock(db, product, quantity)

      # Actualizar el costo unitario del producto solo si se especifica un valor > 0
      if unit_cost > 0:
        product.cost = unit_cost

      subtotal = unit_cost * quantity
      total_amount += subtotal

      purchase_item = PurchaseOrderItem(
          purchase_order_id=new_purchase.id,
          product_id=product_id,
          quantity=quantity,
          unit_cost=unit_cost,
          subtotal=subtotal,
      )
      db.add(purchase_item)

    new_purchase.total_amount = total_amount

    # Registrar la deuda/cuenta por pagar para el módulo de Finanzas
    payable = AccountPayable(
        company_id=company_id,
        purchase_order_id=new_purchase.id,
        supplier_id=supplier_id,
        amount=total_amount,
        amount_paid=0.0,
        status="pending",
        due_date=due_date,
    )
    db.add(payable)

    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "¡Compra registrada con éxito, stock incrementado y cuenta por pagar creada!",
            "purchase_id": new_purchase.id,
            "total_amount": total_amount,
            "payable_id": payable.id,
            "payable_balance": total_amount,
        }),
        201,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/payables", methods=["GET"])
def get_payables():
  db = next(get_db())
  company_id = request.args.get("company_id", type=int)
  status = request.args.get("status", type=str)
  q = db.query(AccountPayable)
  if company_id is not None:
    q = q.filter(AccountPayable.company_id == company_id)
  if status in ("pending", "partial", "paid"):
    q = q.filter(AccountPayable.status == status)
  payables = q.order_by(AccountPayable.created_at.desc()).all()
  result = [{
      "id": ap.id,
      "company_id": ap.company_id,
      "purchase_order_id": ap.purchase_order_id,
      "supplier_id": ap.supplier_id,
      "supplier_name": ap.supplier.name if ap.supplier else None,
      "amount": ap.amount,
      "amount_paid": ap.amount_paid,
      "balance": round(ap.balance, 2),
      "status": ap.status,
      "due_date": str(ap.due_date) if ap.due_date else None,
  } for ap in payables]
  return jsonify(result)


@app.route("/api/payables/<int:payable_id>/pay", methods=["POST"])
def pay_payable(payable_id):
  """Registra un pago (parcial o total) contra una cuenta por pagar."""
  data = request.get_json()
  db = next(get_db())

  try:
    payable = (
        db.query(AccountPayable)
        .filter_by(id=payable_id)
        .with_for_update()
        .first()
    )
    if not payable:
      return (
          jsonify({
              "status": "error",
              "message": f"Cuenta por pagar {payable_id} no encontrada.",
          }),
          404,
      )

    amount = data.get("amount", 0.0)
    try:
      balance = payable.apply_payment(db, amount)
    except ValueError as e:
      db.rollback()
      return jsonify({"status": "error", "message": str(e)}), 400

    # Reflejar el estado de pago en la orden de compra asociada
    order = db.query(PurchaseOrder).get(payable.purchase_order_id)
    if order:
      order.payment_status = payable.status

    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Pago registrado.",
            "payable_id": payable.id,
            "amount_paid": payable.amount_paid,
            "balance": round(balance, 2),
            "status": payable.status,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


# --- CRUD COMPRAS (editar estado, eliminar, subida) ---


@app.route("/api/purchases/<int:purchase_id>", methods=["PUT"])
def update_purchase(purchase_id):
  """Actualiza campos editables de una compra (estado / estado de pago)."""
  data = request.get_json()
  db = next(get_db())
  try:
    purchase = db.query(PurchaseOrder).get(purchase_id)
    if not purchase:
      return (
          jsonify({"status": "error", "message": "Compra no encontrada."}),
          404,
      )
    if "payment_status" in data:
      new_status = data.get("payment_status")
      if new_status not in ("pending", "partial", "paid"):
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": "Estado de pago inválido.",
            }),
            400,
        )
      purchase.payment_status = new_status
    if "status" in data:
      new_status = data.get("status")
      if new_status not in ("completed", "pending", "cancelled"):
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": "Estado de compra inválido.",
            }),
            400,
        )
      purchase.status = new_status
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Compra actualizada.",
            "purchase_id": purchase.id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/purchases/<int:purchase_id>", methods=["DELETE"])
def delete_purchase(purchase_id):
  """Elimina una compra y devuelve el stock de sus insumos al inventario."""
  db = next(get_db())
  try:
    purchase = db.query(PurchaseOrder).get(purchase_id)
    if not purchase:
      return (
          jsonify({"status": "error", "message": "Compra no encontrada."}),
          404,
      )
    for item in purchase.items:
      product = db.query(Product).get(item.product_id)
      if product:
        product.stock = max((product.stock or 0) - item.quantity, 0)
    db.delete(purchase)
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Compra eliminada y stock ajustado.",
            "purchase_id": purchase_id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/purchases/upload", methods=["POST"])
def upload_purchases():
  """Importa compras desde CSV/Excel: proveedor_ruc, insumo_sku, cantidad,
  costo_unitario. Aumenta el stock de los insumos al recibir."""
  db = next(get_db())
  try:
    df, fname = _read_upload_df(request.files["file"])
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    company_id = request.form.get("company_id", 1, type=int)

    created, errors = 0, []
    for idx, r in df.iterrows():
      try:
        ruc = _parse_row_str(r.get("proveedor_ruc", r.get("ruc")))
        sku = _parse_row_str(r.get("insumo_sku", r.get("sku")))
        quantity = int(r.get("cantidad", 1) or 1)
        unit_cost = float(r.get("costo_unitario", r.get("costo", 0)) or 0)

        if not ruc or not sku:
          raise ValueError("Faltan proveedor_ruc o insumo_sku.")

        supplier = (
            db.query(ThirdParty)
            .filter(
                ThirdParty.company_id == company_id,
                ThirdParty.document_number == ruc,
                ThirdParty.type.in_(("supplier", "both")),
            )
            .first()
        )
        if not supplier:
          raise ValueError(f"Proveedor con RUC {ruc} no encontrado.")

        product = (
            db.query(Product)
            .filter_by(company_id=company_id, sku=sku)
            .with_for_update()
            .first()
        )
        if not product:
          raise ValueError(f"Insumo con SKU {sku} no encontrado.")

        _adjust_stock(db, product, quantity)
        if unit_cost > 0:
          product.cost = unit_cost

        total = unit_cost * quantity
        purchase = PurchaseOrder(
            company_id=company_id,
            supplier_id=supplier.id,
            total_amount=total,
            status="completed",
            payment_status="pending",
        )
        db.add(purchase)
        db.flush()
        db.add(PurchaseOrderItem(
            purchase_order_id=purchase.id,
            product_id=product.id,
            quantity=quantity,
            unit_cost=unit_cost,
            subtotal=total,
        ))
        db.add(AccountPayable(
            company_id=company_id,
            purchase_order_id=purchase.id,
            supplier_id=supplier.id,
            amount=total,
            amount_paid=0.0,
            status="pending",
        ))
        created += 1
      except Exception as e:
        db.rollback()
        errors.append(f"Fila {idx + 2}: {e}")

    db.commit()
    return jsonify({"status": "success", "created": created, "errors": errors}), 200
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


# --- MÓDULO DE RECURSOS HUMANOS (RRHH) ---


def _build_payroll(db, company_id):
  """Suma el sueldo de los empleados ACTIVOS (gasto fijo de planilla).

  Disponible automáticamente para que Finanzas lo use como egreso fijo.
  """
  monthly = (
      db.query(func.coalesce(func.sum(Employee.salary), 0))
      .filter(Employee.company_id == company_id, Employee.status == "active")
      .scalar()
      or 0.0
  )
  active_count = (
      db.query(func.count(Employee.id))
      .filter(Employee.company_id == company_id, Employee.status == "active")
      .scalar()
      or 0
  )
  return {
      "gasto_planilla_mensual": round(monthly, 2),
      "gasto_planilla_anual": round(monthly * 12, 2),
      "empleados_activos": active_count,
  }


@app.route("/api/employees", methods=["GET"])
def get_employees():
  db = next(get_db())
  company_id = request.args.get("company_id", type=int)
  status = request.args.get("status", type=str)

  q = db.query(Employee)
  if company_id is not None:
    q = q.filter(Employee.company_id == company_id)
  if status in ("active", "terminated"):
    q = q.filter(Employee.status == status)

  employees = q.order_by(Employee.full_name).all()
  result = [
      {
          "id": e.id,
          "company_id": e.company_id,
          "full_name": e.full_name,
          "document_number": e.document_number,
          "position": e.position,
          "salary": e.salary,
          "contract_type": e.contract_type,
          "contract_start": e.contract_start,
          "contract_end": e.contract_end,
          "vacation_days_available": e.vacation_days_available,
          "status": e.status,
          "is_active": e.is_active,
      }
      for e in employees
  ]
  return jsonify(result)


@app.route("/api/employees", methods=["POST"])
def create_employee():
  data = request.get_json()
  db = next(get_db())

  try:
    full_name = (data.get("full_name") or "").strip()
    document_number = (data.get("document_number") or "").strip()
    position = (data.get("position") or "").strip()

    if not full_name:
      return (
          jsonify({"status": "error", "message": "El nombre completo es obligatorio."}),
          400,
      )
    if not document_number:
      return (
          jsonify({"status": "error", "message": "El documento (DNI) es obligatorio."}),
          400,
      )
    if not position:
      return (
          jsonify({"status": "error", "message": "El puesto es obligatorio."}),
          400,
      )

    try:
      contract_type = Employee.normalize_contract_type(
          data.get("contract_type", "Indefinido")
      )
    except ValueError as e:
      return jsonify({"status": "error", "message": str(e)}), 400

    try:
      salary = Employee.validate_salary(data.get("salary", 0.0))
    except ValueError as e:
      return jsonify({"status": "error", "message": str(e)}), 400

    try:
      status = Employee.normalize_status(data.get("status", "active"))
    except ValueError as e:
      return jsonify({"status": "error", "message": str(e)}), 400

    company_id = data.get("company_id", 1)

    # DNI único dentro de la empresa
    existing = (
        db.query(Employee)
        .filter_by(company_id=company_id, document_number=document_number)
        .first()
    )
    if existing:
      return (
          jsonify({
              "status": "error",
              "message": "Ya existe un empleado con ese documento en esta empresa.",
          }),
          400,
      )

    vacation_days = data.get("vacation_days", 30)
    if not isinstance(vacation_days, int) or vacation_days < 0:
      return (
          jsonify({
              "status": "error",
              "message": "Los días de vacaciones deben ser un entero >= 0.",
          }),
          400,
      )

    new_employee = Employee(
        company_id=company_id,
        full_name=full_name,
        document_number=document_number,
        position=position,
        salary=salary,
        contract_type=contract_type,
        contract_start=data.get("contract_start", ""),
        contract_end=data.get("contract_end", ""),
        vacation_days_available=vacation_days,
        status=status,
    )
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    return (
        jsonify({
            "status": "success",
            "message": "¡Trabajador registrado con éxito en RRHH!",
            "employee_id": new_employee.id,
            "contract_type": new_employee.contract_type,
            "salary": new_employee.salary,
        }),
        201,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/employees/<int:employee_id>/status", methods=["PATCH"])
def update_employee_status(employee_id):
  """Actualiza el estado del colaborador (active/terminated).

  Al cesar a un empleado (status='terminated') su sueldo deja de contar en la
  planilla para Finanzas automáticamente.
  """
  data = request.get_json()
  db = next(get_db())

  try:
    employee = db.query(Employee).get(employee_id)
    if not employee:
      return (
          jsonify({
              "status": "error",
              "message": f"Empleado {employee_id} no encontrado.",
          }),
          404,
      )

    try:
      new_status = Employee.normalize_status(data.get("status"))
    except ValueError as e:
      return jsonify({"status": "error", "message": str(e)}), 400

    employee.status = new_status
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": f"Estado del empleado actualizado a '{new_status}'.",
            "employee_id": employee.id,
            "status": employee.status,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/employees/<int:employee_id>/vacations", methods=["POST"])
def use_vacations(employee_id):
  """Consume días de vacaciones de un empleado activo de forma segura."""
  data = request.get_json()
  db = next(get_db())

  try:
    employee = (
        db.query(Employee)
        .filter_by(id=employee_id)
        .with_for_update()
        .first()
    )
    if not employee:
      return (
          jsonify({
              "status": "error",
              "message": f"Empleado {employee_id} no encontrado.",
          }),
          404,
      )
    if not employee.is_active:
      return (
          jsonify({
              "status": "error",
              "message": "Solo los empleados activos pueden usar vacaciones.",
          }),
          400,
      )

    days = data.get("days", 0)
    try:
      remaining = employee.use_vacation_days(days)
    except ValueError as e:
      db.rollback()
      return jsonify({"status": "error", "message": str(e)}), 400

    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Vacaciones registradas.",
            "employee_id": employee.id,
            "vacation_days_available": remaining,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/payroll", methods=["GET"])
def get_payroll():
  """Devuelve el gasto de planilla (RRHH) mensual y anual de una empresa.

  Suma automáticamente los sueldos de los empleados con status='active'.
  El mismo cálculo alimenta directamente el reporte financiero.
  """
  db = next(get_db())
  company_id = request.args.get("company_id", 1, type=int)
  return jsonify(_build_payroll(db, company_id))


# --- CRUD RRHH (editar, eliminar, subida) ---


@app.route("/api/employees/<int:employee_id>", methods=["PUT"])
def update_employee(employee_id):
  data = request.get_json()
  db = next(get_db())
  try:
    employee = db.query(Employee).get(employee_id)
    if not employee:
      return (
          jsonify({
              "status": "error",
              "message": "Empleado no encontrado.",
          }),
          404,
      )
    if "full_name" in data:
      employee.full_name = data.get("full_name")
    if "document_number" in data:
      employee.document_number = data.get("document_number")
    if "position" in data:
      employee.position = data.get("position")
    if "salary" in data:
      try:
        employee.salary = Employee.validate_salary(data.get("salary"))
      except ValueError as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    if "contract_type" in data:
      try:
        employee.contract_type = Employee.normalize_contract_type(
            data.get("contract_type")
        )
      except ValueError as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    if "contract_start" in data:
      employee.contract_start = data.get("contract_start")
    if "contract_end" in data:
      employee.contract_end = data.get("contract_end")
    if "status" in data:
      try:
        employee.status = Employee.normalize_status(data.get("status"))
      except ValueError as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Empleado actualizado.",
            "employee_id": employee.id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/employees/<int:employee_id>", methods=["DELETE"])
def delete_employee(employee_id):
  db = next(get_db())
  try:
    employee = db.query(Employee).get(employee_id)
    if not employee:
      return (
          jsonify({
              "status": "error",
              "message": "Empleado no encontrado.",
          }),
          404,
      )
    db.delete(employee)
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Empleado eliminado.",
            "employee_id": employee_id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/employees/upload", methods=["POST"])
def upload_employees():
  db = next(get_db())
  try:
    df, fname = _read_upload_df(request.files["file"])
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    company_id = request.form.get("company_id", 1, type=int)

    created, errors = 0, []
    for idx, r in df.iterrows():
      try:
        full_name = _parse_row_str(r.get("full_name", r.get("colaborador", r.get("nombre"))))
        document_number = _parse_row_str(r.get("document_number", r.get("dni")))
        position = _parse_row_str(r.get("position", r.get("puesto")))
        if not full_name or not document_number or not position:
          raise ValueError("Faltan nombre, documento o puesto.")
        salary = Employee.validate_salary(r.get("salary", r.get("sueldo", 0)) or 0)
        contract_type = Employee.normalize_contract_type(
            r.get("contract_type", r.get("tipo_contrato", "Indefinido"))
        )
        status = Employee.normalize_status(r.get("status", r.get("estado", "active")))
        existing = db.query(Employee).filter_by(
            company_id=company_id, document_number=document_number
        ).first()
        if existing:
          raise ValueError(f"Documento {document_number} ya registrado.")
        db.add(Employee(
            company_id=company_id,
            full_name=full_name,
            document_number=document_number,
            position=position,
            salary=salary,
            contract_type=contract_type,
            vacation_days_available=30,
            status=status,
        ))
        created += 1
      except Exception as e:
        db.rollback()
        errors.append(f"Fila {idx + 2}: {e}")
    db.commit()
    return jsonify({"status": "success", "created": created, "errors": errors}), 200
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


# --- MÓDULO DE PRODUCCIÓN (Lista de Materiales + Órdenes) ---


@app.route("/api/bom", methods=["GET"])
def get_boms():
  db = next(get_db())
  company_id = request.args.get("company_id", type=int)
  q = db.query(BillOfMaterial)
  if company_id is not None:
    q = q.filter(BillOfMaterial.company_id == company_id)
  boms = q.all()
  result = []
  for b in boms:
    result.append({
        "id": b.id,
        "company_id": b.company_id,
        "output_product_id": b.output_product_id,
        "output_product_name": b.output_product.name if b.output_product else None,
        "name": b.name,
        "output_quantity": b.output_quantity,
        "lines": [
            {
                "product_id": l.product_id,
                "product_name": l.product.name if l.product else None,
                "quantity": l.quantity,
            }
            for l in b.lines
        ],
    })
  return jsonify(result)


@app.route("/api/bom", methods=["POST"])
def create_bom():
  data = request.get_json()
  db = next(get_db())

  try:
    output_product_id = data.get("output_product_id")
    lines_data = data.get("lines", [])
    company_id = data.get("company_id")

    if not lines_data:
      return (
          jsonify({
              "status": "error",
              "message": "La lista de materiales debe incluir al menos un insumo.",
          }),
          400,
      )

    # El producto de salida debe existir y ser un producto terminado
    output = db.query(Product).filter_by(id=output_product_id).first()
    try:
      BillOfMaterial.validate_product_type(output, "termined", "El producto de salida")
    except ValueError as e:
      db.rollback()
      return jsonify({"status": "error", "message": str(e)}), 400

    # Validar insumos antes de crear la BOM (todos deben ser materias primas)
    seen_inputs = set()
    for line in lines_data:
      raw_id = line.get("product_id")
      qty = line.get("quantity", 1)

      if raw_id == output_product_id:
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": "Un insumo no puede ser el mismo producto de salida.",
            }),
            400,
        )
      if raw_id in seen_inputs:
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": f"El insumo {raw_id} está duplicado en la lista.",
            }),
            400,
        )
      if not isinstance(qty, (int, float)) or qty <= 0:
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": "Cada insumo debe tener una cantidad positiva.",
            }),
            400,
        )
      seen_inputs.add(raw_id)

      raw = db.query(Product).filter_by(id=raw_id).first()
      try:
        BillOfMaterial.validate_product_type(raw, "raw", f"El insumo {raw_id}")
      except ValueError as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

    new_bom = BillOfMaterial(
        company_id=company_id,
        output_product_id=output_product_id,
        name=data.get("name") or f"Receta para producto {output.id}",
        output_quantity=data.get("output_quantity", 1),
        notes=data.get("notes", ""),
    )
    db.add(new_bom)
    db.flush()

    for line in lines_data:
      db.add(BillOfMaterialLine(
          bom_id=new_bom.id,
          product_id=line.get("product_id"),
          quantity=line.get("quantity", 1),
      ))

    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "¡Lista de materiales (BOM) registrada con éxito!",
            "bom_id": new_bom.id,
        }),
        201,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/production", methods=["GET"])
def get_production_orders():
  db = next(get_db())
  company_id = request.args.get("company_id", type=int)
  q = db.query(ProductionOrder)
  if company_id is not None:
    q = q.filter(ProductionOrder.company_id == company_id)
  orders = q.order_by(ProductionOrder.created_at.desc()).all()
  result = [{
      "id": o.id,
      "company_id": o.company_id,
      "bom_id": o.bom_id,
      "output_product": (
          o.bom.output_product.name if o.bom and o.bom.output_product else None
      ),
      "quantity": o.quantity,
      "produced_quantity": o.produced_quantity,
      "total_cost": o.total_cost,
      "status": o.status,
      "created_at": str(o.created_at) if o.created_at else None,
  } for o in orders]
  return jsonify(result)


@app.route("/api/production", methods=["POST"])
def create_production_order():
  data = request.get_json()
  db = next(get_db())

  try:
    company_id = data.get("company_id")
    bom_id = data.get("bom_id")
    quantity = data.get("quantity", 1)

    bom = (
        db.query(BillOfMaterial)
        .filter_by(id=bom_id, company_id=company_id)
        .first()
    )
    if not bom:
      db.rollback()
      return (
          jsonify({
              "status": "error",
              "message": f"Lista de materiales (BOM) con ID {bom_id} no encontrada.",
          }),
          404,
      )

    order = ProductionOrder(
        company_id=company_id,
        bom_id=bom_id,
        quantity=quantity,
        status="pending",
    )
    db.add(order)
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "¡Orden de producción creada! Ejecútala para actualizar stock.",
            "production_order_id": order.id,
        }),
        201,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/production/<int:order_id>/execute", methods=["POST"])
def execute_production_order(order_id):
  """Ejecuta una orden de producción de forma atómica.

  - Bloquea la orden (FOR UPDATE) para impedir doble ejecución concurrente.
  - Verifica el stock de TODOS los insumos y los consume (materia prima 'raw').
  - Aumenta el stock del producto terminado ('termined').
  - Registra produced_quantity y total_cost (suma costo de insumos consumidos).

  Todo ocurre en una única transacción: si cualquier insumo no alcanza, se
  revierte por completo y no se modifica inventario.
  """
  db = next(get_db())

  try:
    order = (
        db.query(ProductionOrder)
        .filter_by(id=order_id)
        .with_for_update()
        .first()
    )
    if not order:
      return (
          jsonify({
              "status": "error",
              "message": f"Orden de producción {order_id} no encontrada.",
          }),
          404,
      )
    if order.status == "completed":
      return (
          jsonify({
              "status": "error",
              "message": "La orden ya fue completada.",
          }),
          400,
      )

    bom = (
        db.query(BillOfMaterial)
        .filter_by(id=order.bom_id)
        .with_for_update()
        .first()
    )
    if not bom:
      db.rollback()
      return (
          jsonify({
              "status": "error",
              "message": f"Lista de materiales (BOM) {order.bom_id} no encontrada.",
          }),
          404,
      )

    # Validar fuerza bruta: el producto de salida debe ser un producto terminado
    output = (
        db.query(Product)
        .filter_by(id=bom.output_product_id)
        .with_for_update()
        .first()
    )
    try:
      BillOfMaterial.validate_product_type(output, "termined", "El producto de salida")
    except ValueError as e:
      db.rollback()
      return jsonify({"status": "error", "message": str(e)}), 400

    produced = bom.output_quantity * order.quantity

    # --- Consumir insumos de forma atómica y acumular costo ---
    # Primera pasada: verificar stock de TODOS los insumos (bloqueando filas)
    # para asegurar decisión atómica antes de descontar nada.
    inputs = []
    for line in bom.lines:
      needed = line.quantity * order.quantity
      if not isinstance(needed, int):
        needed = int(needed)

      raw = (
          db.query(Product)
          .filter_by(id=line.product_id)
          .with_for_update()
          .first()
      )
      try:
        BillOfMaterial.validate_product_type(raw, "raw", f"El insumo {line.product_id}")
      except ValueError as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

      if raw.stock is None:
        raw.stock = 0
      if raw.stock < needed:
        db.rollback()
        return (
            jsonify({
                "status": "error",
                "message": (
                    f"Stock insuficiente de '{raw.name}'. Requerido: {needed},"
                    f" Disponible: {raw.stock}."
                ),
            }),
            400,
        )
      inputs.append({"product": raw, "needed": needed})

    # Segunda pasada: descontar insumos (sin riesgo, ya validado) y calcular costo
    total_cost = 0.0
    rundown_details = []
    for entry in inputs:
      raw = entry["product"]
      needed = entry["needed"]
      raw.stock -= needed
      cost_of_raw = (raw.cost or 0.0) * needed
      total_cost += cost_of_raw
      rundown_details.append({
          "product_id": raw.id,
          "name": raw.name,
          "consumed": needed,
          "unit_cost": raw.cost or 0.0,
          "line_cost": round(cost_of_raw, 2),
      })

    # Aumentar stock del producto terminado
    output.stock = (output.stock or 0) + produced

    # Registrar resultado y costo de producción
    order.status = "completed"
    order.produced_quantity = produced
    order.total_cost = round(total_cost, 2)

    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "¡Producción ejecutada: insumos consumidos y stock actualizado!",
            "production_order_id": order.id,
            "output": {
                "product_id": output.id,
                "name": output.name,
                "added": produced,
            },
            "total_cost": round(total_cost, 2),
            "inputs_consumed": rundown_details,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


# --- CRUD PRODUCCIÓN / BOM (editar, eliminar, subida) ---


@app.route("/api/bom/<int:bom_id>", methods=["PUT"])
def update_bom(bom_id):
  data = request.get_json()
  db = next(get_db())
  try:
    bom = db.query(BillOfMaterial).get(bom_id)
    if not bom:
      return jsonify({"status": "error", "message": "BOM no encontrada."}), 404
    if "name" in data:
      bom.name = data.get("name")
    if "output_quantity" in data:
      bom.output_quantity = data.get("output_quantity", bom.output_quantity)
    if "notes" in data:
      bom.notes = data.get("notes")
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Lista de materiales actualizada.",
            "bom_id": bom.id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/bom/<int:bom_id>", methods=["DELETE"])
def delete_bom(bom_id):
  db = next(get_db())
  try:
    bom = db.query(BillOfMaterial).get(bom_id)
    if not bom:
      return jsonify({"status": "error", "message": "BOM no encontrada."}), 404
    db.delete(bom)
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Lista de materiales eliminada.",
            "bom_id": bom_id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/production/<int:order_id>", methods=["DELETE"])
def delete_production_order(order_id):
  db = next(get_db())
  try:
    order = db.query(ProductionOrder).get(order_id)
    if not order:
      return (
          jsonify({
              "status": "error",
              "message": "Orden de producción no encontrada.",
          }),
          404,
      )
    db.delete(order)
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Orden de producción eliminada.",
            "order_id": order_id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/bom/upload", methods=["POST"])
def upload_boms():
  """Importa recetas BOM desde CSV/Excel.

  Columnas: producto_terminado (SKU), nombre, output_quantity,
  insumos (columna "SKU:cantidad" separados por ';').
  """
  db = next(get_db())
  try:
    df, fname = _read_upload_df(request.files["file"])
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    company_id = request.form.get("company_id", 1, type=int)

    created, errors = 0, []
    for idx, r in df.iterrows():
      try:
        out_sku = _parse_row_str(r.get("producto_terminado", r.get("producto", r.get("sku"))))
        if not out_sku:
          raise ValueError("Falta producto_terminado (SKU).")
        output = db.query(Product).filter_by(
            company_id=company_id, sku=out_sku
        ).first()
        if not output:
          raise ValueError(f"Producto terminado {out_sku} no encontrado.")
        BillOfMaterial.validate_product_type(output, "termined", "Producto de salida")

        insumos = _parse_row_str(r.get("insumos"))
        if not insumos:
          raise ValueError("Falta la columna 'insumos' (SKU:cant;...).")

        lines = []
        for token in insumos.split(";"):
          token = token.strip()
          if not token:
            continue
          sku, _, qty = token.partition(":")
          sku = sku.strip()
          raw = db.query(Product).filter_by(company_id=company_id, sku=sku).first()
          if not raw:
            raise ValueError(f"Insumo {sku} no encontrado.")
          BillOfMaterial.validate_product_type(raw, "raw", f"Insumo {sku}")
          lines.append((raw.id, float(qty or 1)))

        bom = BillOfMaterial(
            company_id=company_id,
            output_product_id=output.id,
            name=_parse_row_str(r.get("name", r.get("nombre"))) or f"Receta {out_sku}",
            output_quantity=int(r.get("output_quantity", 1) or 1),
        )
        db.add(bom)
        db.flush()
        for pid, qty in lines:
          db.add(BillOfMaterialLine(bom_id=bom.id, product_id=pid, quantity=qty))
        created += 1
      except Exception as e:
        db.rollback()
        errors.append(f"Fila {idx + 2}: {e}")
    db.commit()
    return jsonify({"status": "success", "created": created, "errors": errors}), 200
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


# --- MÓDULO ADMINISTRACIÓN Y FINANZAS + ANÁLISIS Y PROYECCIÓN ---


@app.route("/api/expenses", methods=["GET"])
def get_expenses():
  db = next(get_db())
  expenses = db.query(Expense).all()
  result = [{
      "id": e.id,
      "company_id": e.company_id,
      "category": e.category,
      "description": e.description,
      "amount": e.amount,
      "expense_date": str(e.expense_date) if e.expense_date else None,
  } for e in expenses]
  return jsonify(result)


@app.route("/api/expenses", methods=["POST"])
def create_expense():
  data = request.get_json()
  db = next(get_db())

  try:
    new_expense = Expense(
        company_id=data.get("company_id", 1),
        category=data.get("category"),
        description=data.get("description", ""),
        amount=float(data.get("amount", 0.0)),
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return (
        jsonify({
            "status": "success",
            "message": "¡Gasto registrado con éxito!",
            "expense_id": new_expense.id,
        }),
        201,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/expenses/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):
  data = request.get_json()
  db = next(get_db())
  try:
    expense = db.query(Expense).get(expense_id)
    if not expense:
      return jsonify({"status": "error", "message": "Gasto no encontrado."}), 404
    if "category" in data:
      expense.category = data.get("category")
    if "description" in data:
      expense.description = data.get("description")
    if "amount" in data:
      expense.amount = float(data.get("amount", expense.amount))
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Gasto actualizado.",
            "expense_id": expense.id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
  db = next(get_db())
  try:
    expense = db.query(Expense).get(expense_id)
    if not expense:
      return jsonify({"status": "error", "message": "Gasto no encontrado."}), 404
    db.delete(expense)
    db.commit()
    return (
        jsonify({
            "status": "success",
            "message": "Gasto eliminado.",
            "expense_id": expense_id,
        }),
        200,
    )
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/expenses/upload", methods=["POST"])
def upload_expenses():
  db = next(get_db())
  try:
    df, fname = _read_upload_df(request.files["file"])
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    company_id = request.form.get("company_id", 1, type=int)

    created, errors = 0, []
    for idx, r in df.iterrows():
      try:
        category = _parse_row_str(r.get("category", r.get("concepto", r.get("tipo"))))
        if not category:
          raise ValueError("Falta la categoría/concepto.")
        db.add(Expense(
            company_id=company_id,
            category=category,
            description=_parse_row_str(r.get("description", r.get("descripcion"))),
            amount=float(r.get("amount", r.get("monto", 0)) or 0),
        ))
        created += 1
      except Exception as e:
        db.rollback()
        errors.append(f"Fila {idx + 2}: {e}")
    db.commit()
    return jsonify({"status": "success", "created": created, "errors": errors}), 200
  except Exception as e:
    db.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


def _parse_period(start_str, end_str):
  """Convierte fechas 'YYYY-MM-DD' a datetime, o devuelve (None, None)."""
  from datetime import datetime
  start = end = None
  if start_str:
    start = datetime.strptime(start_str, "%Y-%m-%d")
  if end_str:
    end = datetime.strptime(end_str, "%Y-%m-%d")
  return start, end


def _build_financial_report(db, company_id, start_date=None, end_date=None):
  """Consolida ingresos y egresos de una empresa para un periodo.

  - Ingresos: Ventas COMPLETADAS (SaleOrder.status='completed').
  - Egresos:  Cuentas por pagar de Compras (AccountPayable) +
              Planilla activa en tiempo real de RRHH (empleados activos) +
              Gastos operativos (Expense).

  start_date/end_date (datetime) acotan el periodo del Resultado Neto.
  """
  # --- INGRESOS REALES (ventas completadas) ---
  sales_q = (
      db.query(func.coalesce(func.sum(SaleOrder.total_amount), 0))
      .filter(SaleOrder.company_id == company_id, SaleOrder.status == "completed")
  )
  if start_date:
    sales_q = sales_q.filter(SaleOrder.created_at >= start_date)
  if end_date:
    sales_q = sales_q.filter(SaleOrder.created_at < end_date)
  sales = sales_q.scalar()

  # --- EGRESOS ---
  # 1) Cuentas por pagar de Compras (deuda registrada por cada compra)
  payables_q = (
      db.query(func.coalesce(func.sum(AccountPayable.amount), 0))
      .filter(AccountPayable.company_id == company_id)
  )
  if start_date:
    payables_q = payables_q.filter(AccountPayable.created_at >= start_date)
  if end_date:
    payables_q = payables_q.filter(AccountPayable.created_at < end_date)
  payables = payables_q.scalar()

  # 2) Planilla activa en tiempo real (RRHH) — gasto fijo mensual
  payroll_info = _build_payroll(db, company_id)
  payroll = payroll_info["gasto_planilla_mensual"]

  # 3) Gastos operativos (Expense)
  expenses_q = (
      db.query(func.coalesce(func.sum(Expense.amount), 0))
      .filter(Expense.company_id == company_id)
  )
  if start_date:
    expenses_q = expenses_q.filter(Expense.expense_date >= start_date)
  if end_date:
    expenses_q = expenses_q.filter(Expense.expense_date < end_date)
  expenses = expenses_q.scalar()

  # 4) Costo de producción (informativo, NO suma al total para evitar
  #    doble conteo con las compras de materia prima en 'cuentas_por_pagar').
  prod_q = (
      db.query(func.coalesce(func.sum(ProductionOrder.total_cost), 0))
      .filter(
          ProductionOrder.company_id == company_id,
          ProductionOrder.status == "completed",
      )
  )
  if start_date:
    prod_q = prod_q.filter(ProductionOrder.created_at >= start_date)
  if end_date:
    prod_q = prod_q.filter(ProductionOrder.created_at < end_date)
  produccion = prod_q.scalar() or 0.0

  sales = sales or 0.0
  payables = payables or 0.0
  payroll = payroll or 0.0
  expenses = expenses or 0.0
  total_egresos = payables + payroll + expenses
  resultado_neto = sales - total_egresos

  return {
      "periodo": {
          "inicio": str(start_date.date()) if start_date else None,
          "fin": str(end_date.date()) if end_date else None,
      },
      "ingresos": {
          "ventas_completadas": round(sales, 2),
          "total_ingresos": round(sales, 2),
      },
      "egresos": {
          "cuentas_por_pagar_compras": round(payables, 2),
          "planilla_rrhh": round(payroll, 2),
          "gastos_operativos": round(expenses, 2),
          "costo_produccion_informativo": round(produccion, 2),
          "total_egresos": round(total_egresos, 2),
      },
      "resultado_neto": round(resultado_neto, 2),
      "tipo_resultado": (
          "utilidad" if resultado_neto > 0
          else ("perdida" if resultado_neto < 0 else "equilibrio")
      ),
  }


@app.route("/api/finance/report", methods=["GET"])
def financial_report():
  db = next(get_db())
  company_id = request.args.get("company_id", 1, type=int)
  start_date, end_date = _parse_period(
      request.args.get("start_date"), request.args.get("end_date")
  )
  return jsonify(_build_financial_report(db, company_id, start_date, end_date))


@app.route("/api/finance/projection", methods=["GET"])
def financial_projection():
  """Proyección del flujo de caja a partir de la data histórica real.

  - Toma datos reales de los 6 módulos (Ventas, Compras, RRHH, Gastos,
    Inventario y Producción).
  - Calcula promedios PONDERADOS (más peso a meses recientes) y la TENDENCIA
    (pendiente de regresión lineal) de la actividad mensual.
  - Proyecta mensual (promedio) y anual (x12): ingresos, egresos
    (compras + planilla fija + gastos), flujo de caja y Utilidad Neta.
  """
  db = next(get_db())
  company_id = request.args.get("company_id", 1, type=int)

  # ---- Serie mensual histórica (Ventas completadas) ----
  month_label = func.date_trunc("month", SaleOrder.created_at)
  sales_rows = (
      db.query(
          month_label.label("mes"),
          func.coalesce(func.sum(SaleOrder.total_amount), 0).label("ventas"),
          func.count(SaleOrder.id).label("n_ventas"),
      )
      .filter(SaleOrder.company_id == company_id, SaleOrder.status == "completed")
      .group_by(month_label)
      .order_by(month_label)
      .all()
  )

  # ---- Serie mensual de Compras (cuentas por pagar) ----
  ap_month = func.date_trunc("month", AccountPayable.created_at)
  purchases_rows = (
      db.query(
          ap_month.label("mes"),
          func.coalesce(func.sum(AccountPayable.amount), 0).label("compras"),
      )
      .filter(AccountPayable.company_id == company_id)
      .group_by(ap_month)
      .all()
  )

  # ---- Serie mensual de Gastos operativos ----
  ex_month = func.date_trunc("month", Expense.expense_date)
  expenses_rows = (
      db.query(
          ex_month.label("mes"),
          func.coalesce(func.sum(Expense.amount), 0).label("gastos"),
      )
      .filter(Expense.company_id == company_id)
      .group_by(ex_month)
      .all()
  )

  # ---- Serie mensual de Costo de Producción (informativo) ----
  prod_month = func.date_trunc("month", ProductionOrder.created_at)
  production_rows = (
      db.query(
          prod_month.label("mes"),
          func.coalesce(func.sum(ProductionOrder.total_cost), 0).label("costo"),
      )
      .filter(
          ProductionOrder.company_id == company_id,
          ProductionOrder.status == "completed",
      )
      .group_by(prod_month)
      .all()
  )

  purchases_by_month = {str(r.mes): r.compras for r in purchases_rows}
  expenses_by_month = {str(r.mes): r.gastos for r in expenses_rows}

  # ---- Métricas de contexto de los otros módulos (diagnóstico) ----
  production_info = (
      db.query(
          func.coalesce(func.sum(ProductionOrder.produced_quantity), 0),
          func.coalesce(func.sum(ProductionOrder.total_cost), 0),
      )
      .filter(ProductionOrder.company_id == company_id)
      .first()
  )
  total_produced, total_prod_cost = production_info or (0, 0)
  inventory_value = (
      db.query(func.coalesce(func.sum(Product.stock * Product.cost), 0))
      .filter(Product.company_id == company_id)
      .scalar()
      or 0.0
  )

  # ---- Promedio ponderado de VENTAS (más peso a meses recientes) ----
  total_ventas = 0.0
  total_ventas_mes = 0
  total_n_ventas = 0
  weighted_sum = 0.0
  weight_total = 0.0
  months_list = []

  n = len(sales_rows)
  for i, row in enumerate(sales_rows):
    total_ventas += row.ventas
    total_n_ventas += row.n_ventas
    # Ponderación exponencial/lineal: el mes más reciente pesa más
    weight = (i + 1)  # peso progresivo 1..n
    weighted_sum += row.ventas * weight
    weight_total += weight
    months_list.append({"month": str(row.mes)[:7], "ingresos": round(float(row.ventas), 2)})
    if row.n_ventas > 0:
      total_ventas_mes += 1

  total_ventas_mes = max(total_ventas_mes, 1)
  weighted_avg_ventas = weighted_sum / weight_total if weight_total else 0.0

  # ---- Tendencia de actividad (regresión lineal simple sobre ventas mensuales) ----
  # y = ventas, x = índice de mes (0..n-1); pendiente = tendencia por mes
  trend = 0.0
  if n >= 2:
    x_vals = list(range(n))
    y_vals = [float(r.ventas) for r in sales_rows]
    mean_x = sum(x_vals) / n
    mean_y = sum(y_vals) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
    den = sum((x - mean_x) ** 2 for x in x_vals)
    if den:
      trend = num / den  # cambio esperado de ventas por mes

  # ---- Compras y gastos ponderados ----
  weighted_compras = purchases_total_proxy(db, company_id, purchases_rows)
  weighted_gastos = expenses_total_proxy(db, company_id, expenses_rows)

  # ---- Planilla fija de RRHH (activos en tiempo real) ----
  payroll_info = _build_payroll(db, company_id)
  monthly_payroll = payroll_info["gasto_planilla_mensual"]
  emp_count = payroll_info["empleados_activos"]

  # ---- Proyección mensual (promedio ponderado + tendencia) ----
  ventas_proyectadas_mes = weighted_avg_ventas + trend
  egresos_mes = weighted_compras + monthly_payroll + weighted_gastos
  flujo_neto_mes = ventas_proyectadas_mes - egresos_mes

  monthly = {
      "ingresos_esperados": round(ventas_proyectadas_mes, 2),
      "egresos": {
          "prom_compras": round(weighted_compras, 2),
          "planilla_rrhh": round(monthly_payroll, 2),
          "prom_gastos": round(weighted_gastos, 2),
          "total_egresos": round(egresos_mes, 2),
      },
      "flujo_neto": round(flujo_neto_mes, 2),
      "empleados_activos": emp_count,
      "tendencia_ventas_mensual": round(trend, 2),
  }

  # ---- Proyección anual (x12) ----
  annual = {
      "ingresos_proyectados": round(ventas_proyectadas_mes * 12, 2),
      "egresos_proyectados": round(egresos_mes * 12, 2),
      "utilidad_neta_proyectada": round(flujo_neto_mes * 12, 2),
  }

  return jsonify({
      "data_historica": {
          "meses_con_actividad": total_ventas_mes,
          "total_ventas_brutas": round(total_ventas, 2),
          "num_ventas": total_n_ventas,
          "produccion_total_unidades": total_produced or 0,
          "costo_produccion_total": round(total_prod_cost or 0.0, 2),
          "valor_inventario": round(inventory_value, 2),
          "planilla_mensual": round(monthly_payroll, 2),
          "serie_ventas_mensual": months_list,
          "serie_costo_produccion": [
              {
                  "month": str(r.mes)[:7],
                  "costo_produccion": round(float(r.costo), 2),
              }
              for r in production_rows
          ],
      },
      "metodo": {
          "promedio_ponderado": round(weighted_avg_ventas, 2),
          "tendencia_mensual": round(trend, 2),
      },
      "proyeccion_mensual": monthly,
      "proyeccion_anual": annual,
  })


def purchases_total_proxy(db, company_id, rows):
  """Promedio mensual ponderado de compras (cuentas por pagar)."""
  wsum = 0.0
  wtotal = 0.0
  for i, r in enumerate(rows):
    wsum += float(r.compras) * (i + 1)
    wtotal += (i + 1)
  return wsum / wtotal if wtotal else 0.0


def expenses_total_proxy(db, company_id, rows):
  """Promedio mensual ponderado de gastos operativos."""
  wsum = 0.0
  wtotal = 0.0
  for i, r in enumerate(rows):
    wsum += float(r.gastos) * (i + 1)
    wtotal += (i + 1)
  return wsum / wtotal if wtotal else 0.0


if __name__ == "__main__":
  app.run(debug=True, port=5000)