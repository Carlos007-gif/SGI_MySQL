import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from database import DatabaseConnection


class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Inventario")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")

        # Inicializar conexión a DB
        try:
            self.db = DatabaseConnection()
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo conectar a la base de datos:\n{e}")
            root.destroy()
            return

        # Variables para formularios
        self.product_id = tk.StringVar()
        self.quantity = tk.StringVar()
        self.movement_type = tk.StringVar(value="salida")
        self.responsible = tk.StringVar(value="Carlos Martinez")

        # Crear interfaz
        self.create_widgets()
        self.load_stock_data()

    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Panel izquierdo: Formulario de movimientos
        left_frame = ttk.LabelFrame(
            main_frame, text="Registrar Movimiento", padding="15")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        # Formulario
        ttk.Label(left_frame, text="ID Producto:").grid(
            row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(left_frame, textvariable=self.product_id,
                  width=20).grid(row=0, column=1, pady=5)

        ttk.Label(left_frame, text="Cantidad:").grid(
            row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(left_frame, textvariable=self.quantity,
                  width=20).grid(row=1, column=1, pady=5)

        ttk.Label(left_frame, text="Tipo:").grid(
            row=2, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(left_frame, textvariable=self.movement_type,
                     values=["entrada", "salida"], width=18).grid(row=2, column=1, pady=5)

        ttk.Label(left_frame, text="Responsable:").grid(
            row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(left_frame, textvariable=self.responsible,
                  width=20).grid(row=3, column=1, pady=5)

        ttk.Button(left_frame, text="Registrar Movimiento",
                   command=self.register_movement).grid(row=4, column=0, columnspan=2, pady=15)

        # Panel derecho: Stock y alertas
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tabla de stock
        stock_frame = ttk.LabelFrame(
            right_frame, text="Inventario Actual", padding="15")
        stock_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        self.stock_tree = ttk.Treeview(stock_frame, columns=(
            "id", "producto", "cantidad", "ubicacion", "estado"), show="headings")
        self.stock_tree.pack(fill=tk.BOTH, expand=True)

        # Configurar columnas
        self.stock_tree.heading("id", text="ID")
        self.stock_tree.heading("producto", text="Producto")
        self.stock_tree.heading("cantidad", text="Cantidad")
        self.stock_tree.heading("ubicacion", text="Ubicación")
        self.stock_tree.heading("estado", text="Estado")

        self.stock_tree.column("id", width=50)
        self.stock_tree.column("producto", width=150)
        self.stock_tree.column("cantidad", width=100)
        self.stock_tree.column("ubicacion", width=150)
        self.stock_tree.column("estado", width=100)

        # Panel de alertas
        alerts_frame = ttk.LabelFrame(
            right_frame, text="Alertas de Stock", padding="15")
        alerts_frame.pack(fill=tk.BOTH, expand=True)

        self.alerts_text = scrolledtext.ScrolledText(
            alerts_frame, height=10, width=60)
        self.alerts_text.pack(fill=tk.BOTH, expand=True)
        self.alerts_text.config(state=tk.DISABLED)

    def load_stock_data(self):
        # Limpiar tabla
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)

        # Obtener datos de stock
        query = """
        SELECT p.id_producto, p.nombre, s.cantidad, s.ubicacion, 
               CASE 
                   WHEN p.tipo = 'papel' AND s.cantidad < 500 THEN 'CRITICO'
                   WHEN p.tipo = 'toner' AND s.cantidad < 10 THEN 'CRITICO'
                   WHEN p.tipo = 'encuadernacion' AND s.cantidad < 20 THEN 'CRITICO'
                   ELSE 'NORMAL'
               END AS estado
        FROM productos p
        JOIN stock s ON p.id_producto = s.producto_id
        """

        stock_data = self.db.fetch_all(query)

        # Cargar en tabla
        for item in stock_data:
            self.stock_tree.insert("", tk.END, values=(
                str(item["id_producto"]) if isinstance(
                    item, dict) else str(item[0]),
                str(item["nombre"]) if isinstance(
                    item, dict) else str(item[1]),
                str(item["cantidad"]) if isinstance(
                    item, dict) else str(item[2]),
                str(item["ubicacion"]) if isinstance(
                    item, dict) else str(item[3]),
                str(item["estado"]) if isinstance(item, dict) else str(item[4])
            ))

        # Actualizar alertas
        self.update_alerts()

    def update_alerts(self):
        # Obtener alertas
        query = "SELECT * FROM vista_alertas_stock"
        alerts = self.db.fetch_all(query)

        # Actualizar texto de alertas
        self.alerts_text.config(state=tk.NORMAL)
        self.alerts_text.delete(1.0, tk.END)

        if not alerts:
            self.alerts_text.insert(tk.END, "No hay alertas de stock crítico")
        else:
            for alert in alerts:
                alert_text = alert[1] if isinstance(
                    alert, tuple) else alert.get("nombre", "")
                quantity = alert[2] if isinstance(
                    alert, tuple) else alert.get("cantidad", "")
                location = alert[3] if isinstance(
                    alert, tuple) else alert.get("ubicacion", "")
                self.alerts_text.insert(
                    tk.END, f"🚨 {alert_text}: {quantity} unidades ({location})\n")

        self.alerts_text.config(state=tk.DISABLED)

    def register_movement(self):
        # Validar entradas
        if not self.product_id.get() or not self.quantity.get():
            messagebox.showerror("Error", "Todos los campos son requeridos")
            return

        try:
            product_id = int(self.product_id.get())
            quantity = int(self.quantity.get())
        except ValueError:
            messagebox.showerror("Error", "ID y cantidad deben ser números")
            return

        # Registrar movimiento
        query = """
        INSERT INTO movimientos (producto_id, tipo, cantidad, responsable, motivo)
        VALUES (%s, %s, %s, %s, %s)
        """

        motivo = "Movimiento manual"  # Puedes hacer esto un campo en el formulario
        params = (product_id, self.movement_type.get(), quantity,
                  self.responsible.get(), motivo)

        if self.db.execute_query(query, params):
            messagebox.showinfo("Éxito", "Movimiento registrado correctamente")
            self.load_stock_data()
            # Limpiar campos
            self.product_id.set("")
            self.quantity.set("")
        else:
            messagebox.showerror("Error", "No se pudo registrar el movimiento")

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()
