import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
import sys
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.database import DatabaseConnection
from src.utils import DataUtils

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Inventario - Escuela Industrial Álvaro Obregón")
        self.root.geometry("1100x800")
        self.root.configure(bg="#f5f5f5")
        self.root.state('zoomed')  # Maximizar ventana
        
        # Variables para formularios
        self.product_id = tk.StringVar()
        self.quantity = tk.StringVar()
        self.movement_type = tk.StringVar(value="salida")
        self.responsible = tk.StringVar(value="Carlos Martinez")
        self.motivo = tk.StringVar(value="Consumo normal")
        self.search_var = tk.StringVar()
        
        # Variable para la barra de estado
        self.status_var = tk.StringVar()
        
        # Inicializar conexión a DB
        try:
            self.db = DatabaseConnection()
            # Verificar conexión al iniciar
            status = self.db.get_connection_status()
            if status.get('status') != 'connected':
                raise ConnectionError("No se pudo establecer conexión con la base de datos")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar a la base de datos:\n{e}")
            logger.error(f"Error de conexión al iniciar aplicación: {e}")
            root.destroy()
            return
        
        # Crear interfaz
        self.create_menu()
        self.create_main_layout()
        self.load_stock_data()
        self.update_status_bar()
        
        # Enlazar eventos
        self.search_var.trace("w", lambda *args: self.search_products())
    
    def create_menu(self):
        """Crea la barra de menú superior"""
        menubar = tk.Menu(self.root)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exportar Inventario", command=self.export_inventory)
        file_menu.add_command(label="Exportar Movimientos", command=self.export_movements)
        file_menu.add_separator()
        file_menu.add_command(label="Crear Backup", command=self.create_backup)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        
        # Menú Reportes
        report_menu = tk.Menu(menubar, tearoff=0)
        report_menu.add_command(label="Ver Gráfico de Stock", command=self.show_stock_chart)
        report_menu.add_command(label="Generar Reporte de Consumo", command=self.generate_consumption_report)
        menubar.add_cascade(label="Reportes", menu=report_menu)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        help_menu.add_command(label="Estado de Conexión", command=self.show_connection_status)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def show_connection_status(self):
        """Muestra el estado actual de la conexión a la base de datos"""
        try:
            status = self.db.get_connection_status()
            
            status_window = tk.Toplevel(self.root)
            status_window.title("Estado de Conexión")
            status_window.geometry("400x300")
            status_window.resizable(False, False)
            
            frame = ttk.Frame(status_window, padding=20)
            frame.pack(fill=tk.BOTH, expand=True)
            
            if status.get('status') == 'connected':
                ttk.Label(frame, text="✅ CONEXIÓN EXITOSA", font=("Arial", 14, "bold"), foreground="#2ecc71").pack(pady=10)
                info = f"""
                Base de Datos: {status.get('database', 'N/A')}
                Versión Servidor: {status.get('server_version', 'N/A')}
                ID de Conexión: {status.get('connection_id', 'N/A')}
                Última Verificación: {datetime.now().strftime('%H:%M:%S')}
                """
                ttk.Label(frame, text=info, justify=tk.LEFT).pack(pady=10)
            else:
                ttk.Label(frame, text="❌ CONEXIÓN FALLIDA", font=("Arial", 14, "bold"), foreground="#e74c3c").pack(pady=10)
                ttk.Label(frame, text=f"Error: {status.get('message', 'Desconocido')}", wraplength=350).pack(pady=10)
            
            ttk.Button(frame, text="Cerrar", command=status_window.destroy).pack(pady=15)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo verificar el estado de la conexión:\n{e}")
    
    def create_backup(self):
        """Crea un backup de la base de datos"""
        try:
            respuesta = messagebox.askyesno("Confirmar Backup", 
                                           "¿Desea crear un backup de la base de datos?\n"
                                           "Esto puede tomar unos segundos.")
            if not respuesta:
                return
            
            backup_path = self.db.backup_database()
            
            if backup_path:
                messagebox.showinfo("Backup Exitoso", 
                                  f"✅ Backup creado exitosamente:\n{backup_path}\n\n"
                                  f"Tamaño: {os.path.getsize(backup_path) / 1024:.1f} KB")
                # Abrir carpeta del backup
                os.startfile(os.path.dirname(backup_path))
            else:
                messagebox.showerror("Error en Backup", 
                                   "❌ No se pudo crear el backup de la base de datos.\n"
                                   "Verifique los permisos y que mysqldump esté disponible.")
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el backup:\n{e}")
            logger.error(f"Error al crear backup: {e}")
    
    def create_main_layout(self):
        """Crea el diseño principal de la interfaz"""
        # Frame principal con notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña 1: Inventario y Movimientos
        self.tab_inventory = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_inventory, text="Gestión de Inventario")
        
        # Pestaña 2: Productos
        self.tab_products = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_products, text="Catálogo de Productos")
        
        # Pestaña 3: Reportes
        self.tab_reports = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_reports, text="Reportes y Análisis")
        
        # Configurar cada pestaña
        self.setup_inventory_tab()
        self.setup_products_tab()
        self.setup_reports_tab()
        
        # Barra de estado
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_inventory_tab(self):
        """Configura la pestaña de gestión de inventario"""
        # Frame izquierdo: Formulario de movimientos
        left_frame = ttk.LabelFrame(self.tab_inventory, text="Registrar Movimiento", padding="15")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15), pady=10)
        
        # Formulario de movimientos
        form_fields = [
            ("ID Producto:", self.product_id),
            ("Cantidad:", self.quantity),
            ("Responsable:", self.responsible),
            ("Motivo:", self.motivo)
        ]
        
        for i, (label, var) in enumerate(form_fields):
            ttk.Label(left_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=8)
            entry = ttk.Entry(left_frame, textvariable=var, width=25)
            entry.grid(row=i, column=1, pady=8)
            if i == 0:  # ID Producto
                entry.focus()
                self.product_id_entry = entry  # Guardar referencia para focus
        
        # Tipo de movimiento
        ttk.Label(left_frame, text="Tipo de Movimiento:").grid(row=2, column=0, sticky=tk.W, pady=8)
        movement_combo = ttk.Combobox(left_frame, textvariable=self.movement_type, 
                                     values=["entrada", "salida"], width=23, state="readonly")
        movement_combo.grid(row=2, column=1, pady=8)
        movement_combo.current(1)  # Seleccionar "salida" por defecto
        
        # Botón para registrar movimiento
        ttk.Button(left_frame, text="Registrar Movimiento", 
                  command=self.register_movement, style="Accent.TButton").grid(row=5, column=0, columnspan=2, pady=15, ipadx=10)
        
        # Frame derecho: Tablas de stock y movimientos
        right_frame = ttk.Frame(self.tab_inventory)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10)
        
        # Panel de búsqueda
        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Buscar producto:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.bind("<Return>", lambda e: self.search_products())
        
        ttk.Button(search_frame, text="Limpiar", command=self.clear_search).pack(side=tk.LEFT, padx=(5, 0))
        
        # Notebook para stock y movimientos recientes
        inventory_notebook = ttk.Notebook(right_frame)
        inventory_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña de Stock
        stock_frame = ttk.Frame(inventory_notebook)
        inventory_notebook.add(stock_frame, text="Inventario Actual")
        
        # Tabla de stock
        self.stock_tree = ttk.Treeview(stock_frame, columns=("id", "producto", "tipo", "cantidad", "ubicacion", "precio", "valor_total", "estado"), show="headings")
        scrollbar = ttk.Scrollbar(stock_frame, orient="vertical", command=self.stock_tree.yview)
        self.stock_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configurar columnas
        column_config = {
            "id": ("ID", 50),
            "producto": ("Producto", 150),
            "tipo": ("Tipo", 100),
            "cantidad": ("Cantidad", 80),
            "ubicacion": ("Ubicación", 120),
            "precio": ("Precio Unit.", 100),
            "valor_total": ("Valor Total", 100),
            "estado": ("Estado", 80)
        }
        
        for col, (heading, width) in column_config.items():
            self.stock_tree.heading(col, text=heading)
            self.stock_tree.column(col, width=width, anchor=tk.CENTER if col in ["id", "cantidad"] else tk.W)
        
        self.stock_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind para doble click en producto
        self.stock_tree.bind("<Double-1>", self.on_product_double_click)
        
        # Pestaña de Movimientos Recientes
        movements_frame = ttk.Frame(inventory_notebook)
        inventory_notebook.add(movements_frame, text="Últimos Movimientos")
        
        # Tabla de movimientos
        self.movements_tree = ttk.Treeview(movements_frame, columns=("id", "producto", "tipo_mov", "cantidad", "fecha", "responsable"), show="headings")
        scrollbar_mov = ttk.Scrollbar(movements_frame, orient="vertical", command=self.movements_tree.yview)
        self.movements_tree.configure(yscrollcommand=scrollbar_mov.set)
        
        # Configurar columnas de movimientos
        movements_columns = {
            "id": ("ID Mov.", 70),
            "producto": ("Producto", 150),
            "tipo_mov": ("Tipo", 80),
            "cantidad": ("Cantidad", 80),
            "fecha": ("Fecha", 150),
            "responsable": ("Responsable", 120)
        }
        
        for col, (heading, width) in movements_columns.items():
            self.movements_tree.heading(col, text=heading)
            self.movements_tree.column(col, width=width, anchor=tk.CENTER if col in ["id", "cantidad"] else tk.W)
        
        self.movements_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_mov.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cargar movimientos recientes
        self.load_recent_movements()
        
        # Panel de alertas
        alerts_frame = ttk.LabelFrame(right_frame, text="Alertas de Stock", padding="10")
        alerts_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.alerts_text = scrolledtext.ScrolledText(alerts_frame, height=6, width=80, font=("Arial", 9))
        self.alerts_text.pack(fill=tk.BOTH, expand=True)
        self.alerts_text.config(state=tk.DISABLED)
        
        # Estilo para botones acentuados
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))
    
    def setup_products_tab(self):
        """Configura la pestaña de catálogo de productos"""
        # Frame superior: Formulario para nuevo producto
        form_frame = ttk.LabelFrame(self.tab_products, text="Agregar Nuevo Producto", padding="15")
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Variables para el formulario de productos
        self.new_prod_name = tk.StringVar()
        self.new_prod_type = tk.StringVar(value="papel")
        self.new_prod_price = tk.StringVar(value="0.00")
        self.new_prod_location = tk.StringVar(value="Departamento Fotocopiado")
        
        # Campos del formulario
        fields = [
            ("Nombre:", self.new_prod_name),
            ("Tipo:", None),
            ("Precio Unitario:", self.new_prod_price),
            ("Ubicación Inicial:", self.new_prod_location)
        ]
        
        for i, (label, var) in enumerate(fields):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=6)
            
            if label == "Tipo:":
                # ComboBox para tipo de producto
                type_combo = ttk.Combobox(form_frame, textvariable=self.new_prod_type, 
                                         values=["papel", "toner", "encuadernacion", "otro"], 
                                         width=23, state="readonly")
                type_combo.grid(row=i, column=1, pady=6)
                type_combo.current(0)
            else:
                ttk.Entry(form_frame, textvariable=var, width=25).grid(row=i, column=1, pady=6)
        
        # Botón para agregar producto
        ttk.Button(form_frame, text="Agregar Producto", 
                  command=self.add_new_product, style="Accent.TButton").grid(row=4, column=0, columnspan=2, pady=15)
        
        # Frame inferior: Tabla de productos existentes
        products_frame = ttk.LabelFrame(self.tab_products, text="Productos Existentes", padding="10")
        products_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Tabla de productos
        columns = ("id", "nombre", "tipo", "precio", "acciones")
        self.products_tree = ttk.Treeview(products_frame, columns=columns, show="headings")
        
        # Configurar columnas
        self.products_tree.heading("id", text="ID")
        self.products_tree.heading("nombre", text="Nombre")
        self.products_tree.heading("tipo", text="Tipo")
        self.products_tree.heading("precio", text="Precio Unitario")
        self.products_tree.heading("acciones", text="Acciones")
        
        self.products_tree.column("id", width=50, anchor=tk.CENTER)
        self.products_tree.column("nombre", width=200)
        self.products_tree.column("tipo", width=100)
        self.products_tree.column("precio", width=120, anchor=tk.E)
        self.products_tree.column("acciones", width=150, anchor=tk.CENTER)
        
        # Scrollbar para la tabla
        scrollbar_prod = ttk.Scrollbar(products_frame, orient="vertical", command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scrollbar_prod.set)
        
        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_prod.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cargar productos existentes
        self.load_products_data()
    
    def setup_reports_tab(self):
        """Configura la pestaña de reportes y análisis"""
        # Frame superior: Botones de exportación
        export_frame = ttk.LabelFrame(self.tab_reports, text="Exportar Reportes", padding="15")
        export_frame.pack(fill=tk.X, padx=10, pady=10)
        
        buttons = [
            ("Exportar Inventario Completo", self.export_inventory),
            ("Exportar Movimientos", self.export_movements),
            ("Reporte de Consumo por Producto", self.generate_consumption_report),
            ("Mostrar Gráfico de Stock", self.show_stock_chart)
        ]
        
        for i, (text, command) in enumerate(buttons):
            ttk.Button(export_frame, text=text, command=command).grid(row=0, column=i, padx=5, pady=5, sticky=tk.EW)
        
        export_frame.grid_columnconfigure(tuple(range(len(buttons))), weight=1)
        
        # Frame inferior: Gráfico de stock
        chart_frame = ttk.LabelFrame(self.tab_reports, text="Análisis Visual del Inventario", padding="15")
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Contenedor para el gráfico
        self.chart_container = ttk.Frame(chart_frame)
        self.chart_container.pack(fill=tk.BOTH, expand=True)
        
        # Generar gráfico inicial
        self.update_stock_chart()
    
    def load_stock_data(self):
        """Carga los datos del stock en la tabla"""
        # Limpiar tabla
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        
        # Obtener datos de stock
        query = """
        SELECT p.id_producto, p.nombre, p.tipo, s.cantidad, s.ubicacion, 
               p.precio_unitario,
               (s.cantidad * p.precio_unitario) as valor_total,
               CASE 
                   WHEN p.tipo = 'papel' AND s.cantidad < 500 THEN 'CRÍTICO'
                   WHEN p.tipo = 'toner' AND s.cantidad < 10 THEN 'CRÍTICO'
                   WHEN p.tipo = 'encuadernacion' AND s.cantidad < 20 THEN 'CRÍTICO'
                   ELSE 'NORMAL'
               END AS estado
        FROM productos p
        JOIN stock s ON p.id_producto = s.producto_id
        ORDER BY estado DESC, p.nombre
        """
        
        stock_data = self.db.fetch_all(query)
        
        # Cargar en tabla
        for item in stock_data:
            estado_tag = "critical" if item['estado'] == 'CRÍTICO' else "normal"
            
            self.stock_tree.insert("", tk.END, values=(
                item['id_producto'],
                item['nombre'],
                item['tipo'].capitalize(),
                item['cantidad'],
                item['ubicacion'],
                DataUtils.formatear_moneda(item['precio_unitario']),
                DataUtils.formatear_moneda(item['valor_total']),
                item['estado']
            ), tags=(estado_tag,))
        
        # Configurar colores para estados
        self.stock_tree.tag_configure("critical", background="#ffcccc", foreground="#cc0000", font=("Arial", 9, "bold"))
        self.stock_tree.tag_configure("normal", background="#ffffff")
        
        # Actualizar alertas
        self.update_alerts()
    
    def load_recent_movements(self):
        """Carga los últimos movimientos en la tabla"""
        # Limpiar tabla
        for item in self.movements_tree.get_children():
            self.movements_tree.delete(item)
        
        # Obtener últimos 50 movimientos
        query = """
        SELECT m.id_movimiento, p.nombre, m.tipo as tipo_mov, m.cantidad, 
               DATE_FORMAT(m.fecha, '%d/%m/%Y %H:%i') as fecha_formateada, m.responsable
        FROM movimientos m
        JOIN productos p ON m.producto_id = p.id_producto
        ORDER BY m.fecha DESC
        LIMIT 50
        """
        
        movements_data = self.db.fetch_all(query)
        
        # Cargar en tabla
        for item in movements_data:
            tipo_tag = "entrada" if item['tipo_mov'] == 'entrada' else "salida"
            
            self.movements_tree.insert("", tk.END, values=(
                item['id_movimiento'],
                item['nombre'],
                item['tipo_mov'].capitalize(),
                item['cantidad'],
                item['fecha_formateada'],
                item['responsable']
            ), tags=(tipo_tag,))
        
        # Configurar colores para tipos de movimiento
        self.movements_tree.tag_configure("entrada", background="#e6ffe6", foreground="#006600")
        self.movements_tree.tag_configure("salida", background="#ffe6e6", foreground="#cc0000")
    
    def update_alerts(self):
        """Actualiza el panel de alertas"""
        # Obtener alertas
        query = "SELECT * FROM vista_alertas_stock"
        alerts = self.db.fetch_all(query)
        
        # Actualizar texto de alertas
        self.alerts_text.config(state=tk.NORMAL)
        self.alerts_text.delete(1.0, tk.END)
        
        if not alerts:
            self.alerts_text.insert(tk.END, "✅ No hay alertas de stock crítico. Todos los productos están en niveles adecuados.", "normal")
        else:
            self.alerts_text.insert(tk.END, f"🚨 ALERTAS ACTIVAS ({len(alerts)} productos con stock crítico):\n\n", "header")
            for alert in alerts:
                self.alerts_text.insert(tk.END, f"• {alert['nombre']}: ", "producto")
                self.alerts_text.insert(tk.END, f"{alert['cantidad']} unidades", "cantidad")
                self.alerts_text.insert(tk.END, f" ({alert['nivel_alerta']}) - ", "estado")
                self.alerts_text.insert(tk.END, f"Ubicación: {alert['ubicacion']}\n", "ubicacion")
        
        # Configurar estilos de texto
        self.alerts_text.tag_config("header", font=("Arial", 10, "bold"), foreground="#cc0000")
        self.alerts_text.tag_config("producto", font=("Arial", 9, "bold"), foreground="#0066cc")
        self.alerts_text.tag_config("cantidad", font=("Arial", 9, "bold"), foreground="#cc0000")
        self.alerts_text.tag_config("estado", font=("Arial", 9), foreground="#888888")
        self.alerts_text.tag_config("ubicacion", font=("Arial", 9), foreground="#555555")
        self.alerts_text.tag_config("normal", font=("Arial", 10), foreground="#008800")
        
        self.alerts_text.config(state=tk.DISABLED)
    
    def search_products(self, event=None):
        """Busca productos en la tabla de stock"""
        search_term = self.search_var.get().lower()
        
        # Si no hay término de búsqueda, cargar todos los datos
        if not search_term:
            self.load_stock_data()
            return
        
        # Limpiar tabla
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        
        # Obtener datos filtrados
        query = """
        SELECT p.id_producto, p.nombre, p.tipo, s.cantidad, s.ubicacion, 
               p.precio_unitario,
               (s.cantidad * p.precio_unitario) as valor_total,
               CASE 
                   WHEN p.tipo = 'papel' AND s.cantidad < 500 THEN 'CRÍTICO'
                   WHEN p.tipo = 'toner' AND s.cantidad < 10 THEN 'CRÍTICO'
                   WHEN p.tipo = 'encuadernacion' AND s.cantidad < 20 THEN 'CRÍTICO'
                   ELSE 'NORMAL'
               END AS estado
        FROM productos p
        JOIN stock s ON p.id_producto = s.producto_id
        WHERE LOWER(p.nombre) LIKE %s OR LOWER(p.tipo) LIKE %s
        ORDER BY estado DESC, p.nombre
        """
        
        params = (f"%{search_term}%", f"%{search_term}%")
        results = self.db.fetch_all(query, params)
        
        # Cargar resultados en tabla
        for item in results:
            estado_tag = "critical" if item['estado'] == 'CRÍTICO' else "normal"
            
            self.stock_tree.insert("", tk.END, values=(
                item['id_producto'],
                item['nombre'],
                item['tipo'].capitalize(),
                item['cantidad'],
                item['ubicacion'],
                DataUtils.formatear_moneda(item['precio_unitario']),
                DataUtils.formatear_moneda(item['valor_total']),
                item['estado']
            ), tags=(estado_tag,))
        
        # Mostrar mensaje si no hay resultados
        if not results:
            self.stock_tree.insert("", tk.END, values=("", "No se encontraron productos", "", "", "", "", "", ""), tags=("normal",))
    
    def clear_search(self):
        """Limpia el campo de búsqueda"""
        self.search_var.set("")
        self.load_stock_data()
    
    def register_movement(self):
        """Registra un nuevo movimiento en la base de datos"""
        # Validar entradas
        if not self.product_id.get() or not self.quantity.get():
            messagebox.showerror("Error", "ID de producto y cantidad son requeridos")
            return
        
        # Validar que el ID de producto sea numérico
        try:
            product_id = int(self.product_id.get())
        except ValueError:
            messagebox.showerror("Error", "ID de producto debe ser un número entero")
            return
        
        # Validar cantidad
        is_valid, error_msg = DataUtils.validar_entrada_numerica(self.quantity.get())
        if not is_valid:
            messagebox.showerror("Error", error_msg)
            return
        
        quantity = int(self.quantity.get())
        
        # Validar que el producto exista
        check_query = "SELECT COUNT(*) as count FROM productos WHERE id_producto = %s"
        result = self.db.fetch_all(check_query, (product_id,))
        
        if not result or result[0]['count'] == 0:
            messagebox.showerror("Error", f"No existe un producto con ID {product_id}. Verifique el ID.")
            return
        
        # Registrar movimiento (usando transacción para integridad)
        try:
            # Primero verificar stock suficiente para salidas
            if self.movement_type.get() == 'salida':
                stock_query = "SELECT cantidad FROM stock WHERE producto_id = %s"
                stock_result = self.db.fetch_one(stock_query, (product_id,))
                
                if not stock_result or stock_result['cantidad'] < quantity:
                    messagebox.showerror("Error de Stock", 
                                       f"No hay suficiente stock para este producto.\n"
                                       f"Stock actual: {stock_result['cantidad'] if stock_result else 0}\n"
                                       f"Cantidad solicitada: {quantity}")
                    return
            
            # Registrar el movimiento
            query = """
            INSERT INTO movimientos (producto_id, tipo, cantidad, responsable, motivo)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                product_id,
                self.movement_type.get(),
                quantity,
                self.responsible.get(),
                self.motivo.get() or "Movimiento manual"
            )
            
            if self.db.execute_query(query, params):
                messagebox.showinfo("Éxito", "✅ Movimiento registrado correctamente")
                self.load_stock_data()
                self.load_recent_movements()
                self.update_status_bar()
                
                # Limpiar campos excepto responsable (por eficiencia)
                self.product_id.set("")
                self.quantity.set("")
                self.motivo.set("Consumo normal")
                self.product_id_entry.focus()
            else:
                messagebox.showerror("Error", "❌ No se pudo registrar el movimiento. Verifique los datos e intente nuevamente.")
        
        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al registrar movimiento:\n{e}")
            logger.error(f"Error al registrar movimiento: {e}")
    
    def add_new_product(self):
        """Agrega un nuevo producto al sistema"""
        # Validar entradas
        if not self.new_prod_name.get().strip():
            messagebox.showerror("Error", "El nombre del producto es requerido")
            return
        
        # Validar precio
        try:
            precio = float(self.new_prod_price.get())
            if precio < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El precio debe ser un número válido y positivo")
            return
        
        # Usar transacción para garantizar integridad
        try:
            # Insertar nuevo producto
            query_producto = """
            INSERT INTO productos (nombre, tipo, precio_unitario)
            VALUES (%s, %s, %s)
            """
            
            params_producto = (
                self.new_prod_name.get().strip(),
                self.new_prod_type.get(),
                precio
            )
            
            if not self.db.execute_query(query_producto, params_producto):
                raise Exception("No se pudo crear el producto")
            
            # Obtener el ID del nuevo producto
            new_product_id = self.db.get_last_insert_id()
            
            if not new_product_id:
                raise Exception("No se pudo obtener el ID del nuevo producto")
            
            # Insertar stock inicial
            query_stock = """
            INSERT INTO stock (producto_id, cantidad, ubicacion)
            VALUES (%s, %s, %s)
            """
            
            params_stock = (
                new_product_id,
                0,  # Cantidad inicial 0
                self.new_prod_location.get().strip()
            )
            
            if not self.db.execute_query(query_stock, params_stock):
                messagebox.showwarning("Advertencia", "Producto creado pero no se pudo inicializar el stock")
            
            # Actualizar vistas
            self.load_products_data()
            self.load_stock_data()
            
            # Limpiar formulario
            self.new_prod_name.set("")
            self.new_prod_price.set("0.00")
            self.new_prod_location.set("Departamento Fotocopiado")
            
            messagebox.showinfo("Éxito", f"✅ Producto creado exitosamente con ID #{new_product_id}")
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el producto:\n{e}")
            logger.error(f"Error al crear producto: {e}")
    
    def load_products_data(self):
        """Carga los productos existentes en la tabla"""
        # Limpiar tabla
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # Obtener productos
        query = """
        SELECT id_producto, nombre, tipo, precio_unitario
        FROM productos
        ORDER BY nombre
        """
        
        products = self.db.fetch_all(query)
        
        # Cargar en tabla
        for product in products:
            self.products_tree.insert("", tk.END, values=(
                product['id_producto'],
                product['nombre'],
                product['tipo'].capitalize(),
                DataUtils.formatear_moneda(product['precio_unitario']),
                "✏️ Editar | 🗑️ Eliminar"
            ))
    
    def update_stock_chart(self):
        """Actualiza el gráfico de stock en la pestaña de reportes"""
        # Obtener datos agrupados por tipo
        query = """
        SELECT p.tipo, SUM(s.cantidad) as total_cantidad, COUNT(*) as num_productos
        FROM productos p
        JOIN stock s ON p.id_producto = s.producto_id
        GROUP BY p.tipo
        """
        
        stock_data = self.db.fetch_all(query)
        
        if not stock_data:
            # Mostrar mensaje en lugar de gráfico
            for widget in self.chart_container.winfo_children():
                widget.destroy()
            
            no_data_label = ttk.Label(self.chart_container, text="No hay datos de stock para mostrar", font=("Arial", 12))
            no_data_label.pack(expand=True)
            return
        
        # Preparar datos para el gráfico
        tipos = [item['tipo'].capitalize() for item in stock_data]
        cantidades = [item['total_cantidad'] for item in stock_data]
        
        # Limpiar contenedor anterior
        for widget in self.chart_container.winfo_children():
            widget.destroy()
        
        # Generar y mostrar el gráfico
        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        
        # Crear gráfico de barras con colores diferenciados
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
        bars = ax.bar(tipos, cantidades, color=colors[:len(tipos)])
        
        # Añadir etiquetas y título
        ax.set_title('Stock Total por Tipo de Producto', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Tipo de Producto', fontsize=12)
        ax.set_ylabel('Cantidad Total en Stock', fontsize=12)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Añadir valores sobre las barras
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{int(height):,}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        # Ajustar márgenes
        plt.tight_layout()
        
        # Crear canvas para Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def export_inventory(self):
        """Exporta el inventario actual a Excel"""
        query = """
        SELECT p.id_producto, p.nombre, p.tipo, s.cantidad, s.ubicacion, 
               p.precio_unitario, (s.cantidad * p.precio_unitario) as valor_total,
               CASE 
                   WHEN p.tipo = 'papel' AND s.cantidad < 500 THEN 'CRÍTICO'
                   WHEN p.tipo = 'toner' AND s.cantidad < 10 THEN 'CRÍTICO'
                   WHEN p.tipo = 'encuadernacion' AND s.cantidad < 20 THEN 'CRÍTICO'
                   ELSE 'NORMAL'
               END AS estado
        FROM productos p
        JOIN stock s ON p.id_producto = s.producto_id
        ORDER BY p.tipo, p.nombre
        """
        
        inventory_data = self.db.fetch_all(query)
        
        if not inventory_data:
            messagebox.showinfo("Información", "No hay datos de inventario para exportar")
            return
        
        # Preparar datos para exportar
        datos = []
        for item in inventory_data:
            datos.append([
                item['id_producto'],
                item['nombre'],
                item['tipo'].capitalize(),
                item['cantidad'],
                item['ubicacion'],
                item['precio_unitario'],
                item['cantidad'] * item['precio_unitario'],
                item['estado']
            ])
        
        columnas = ["ID", "Producto", "Tipo", "Cantidad", "Ubicación", "Precio Unitario", "Valor Total", "Estado"]
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"inventario_completo_{timestamp}.xlsx"
        
        # Guardar diálogo
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
            initialfile=default_filename,
            title="Guardar Reporte de Inventario"
        )
        
        if not filepath:
            return  # Usuario canceló
        
        try:
            ruta = DataUtils.exportar_a_excel(datos, columnas, os.path.basename(filepath))
            
            if ruta:
                messagebox.showinfo("Éxito", f"✅ Reporte exportado exitosamente a:\n{ruta}")
                # Calcular valor total del inventario
                valor_total = sum(item['cantidad'] * item['precio_unitario'] for item in inventory_data)
                messagebox.showinfo("Resumen", f"📊 Valor total del inventario: {DataUtils.formatear_moneda(valor_total)}\n📦 Total de productos: {len(inventory_data)}")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al exportar el reporte:\n{e}")
            logger.error(f"Error al exportar inventario: {e}")
    
    def export_movements(self):
        """Exporta los movimientos a Excel"""
        query = """
        SELECT m.id_movimiento, p.nombre, m.tipo, m.cantidad, m.fecha, m.responsable, m.motivo
        FROM movimientos m
        JOIN productos p ON m.producto_id = p.id_producto
        ORDER BY m.fecha DESC
        """
        
        movements_data = self.db.fetch_all(query)
        
        if not movements_data:
            messagebox.showinfo("Información", "No hay movimientos para exportar")
            return
        
        # Preparar datos para exportar
        datos = []
        for item in movements_data:
            datos.append([
                item['id_movimiento'],
                item['nombre'],
                item['tipo'].capitalize(),
                item['cantidad'],
                item['fecha'].strftime("%d/%m/%Y %H:%M:%S") if item['fecha'] else "",
                item['responsable'],
                item['motivo'] or ""
            ])
        
        columnas = ["ID Movimiento", "Producto", "Tipo", "Cantidad", "Fecha", "Responsable", "Motivo"]
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"movimientos_inventario_{timestamp}.xlsx"
        
        # Guardar diálogo
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
            initialfile=default_filename,
            title="Guardar Reporte de Movimientos"
        )
        
        if not filepath:
            return  # Usuario canceló
        
        try:
            ruta = DataUtils.exportar_a_excel(datos, columnas, os.path.basename(filepath))
            
            if ruta:
                messagebox.showinfo("Éxito", f"✅ Reporte de movimientos exportado exitosamente a:\n{ruta}")
                total_movimientos = len(movements_data)
                total_entradas = sum(1 for m in movements_data if m['tipo'] == 'entrada')
                total_salidas = sum(1 for m in movements_data if m['tipo'] == 'salida')
                
                resumen = "📊 Resumen de Movimientos Exportados:\n"
                resumen += f"• Total de movimientos: {total_movimientos}\n"
                resumen += f"• Entradas registradas: {total_entradas}\n"
                resumen += f"• Salidas registradas: {total_salidas}"
                
                messagebox.showinfo("Resumen", resumen)
        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al exportar el reporte:\n{e}")
            logger.error(f"Error al exportar movimientos: {e}")
    
    def generate_consumption_report(self):
        """Genera un reporte de consumo por producto"""
        # Obtener datos de consumo (solo salidas)
        query = """
        SELECT p.nombre, p.tipo, SUM(m.cantidad) as total_consumido,
               COUNT(*) as num_movimientos,
               AVG(m.cantidad) as promedio_por_mov
        FROM movimientos m
        JOIN productos p ON m.producto_id = p.id_producto
        WHERE m.tipo = 'salida'
        GROUP BY p.id_producto
        ORDER BY total_consumido DESC
        LIMIT 10
        """
        
        consumo_data = self.db.fetch_all(query)
        
        if not consumo_data:
            messagebox.showinfo("Información", "No hay datos de consumo para generar el reporte")
            return
        
        # Crear ventana de reporte
        report_window = tk.Toplevel(self.root)
        report_window.title("Reporte de Consumo de Productos")
        report_window.geometry("900x600")
        
        # Título
        ttk.Label(report_window, text="📊 TOP 10 PRODUCTOS MÁS CONSUMIDOS", 
                 font=("Arial", 16, "bold")).pack(pady=15)
        
        # Frame para la tabla
        table_frame = ttk.Frame(report_window)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Tabla de consumo
        columns = ("pos", "producto", "tipo", "total", "movimientos", "promedio")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Configurar columnas
        tree.heading("pos", text="#")
        tree.heading("producto", text="Producto")
        tree.heading("tipo", text="Tipo")
        tree.heading("total", text="Total Consumido")
        tree.heading("movimientos", text="N° Movimientos")
        tree.heading("promedio", text="Promedio/Mov")
        
        tree.column("pos", width=50, anchor=tk.CENTER)
        tree.column("producto", width=200)
        tree.column("tipo", width=100)
        tree.column("total", width=120, anchor=tk.CENTER)
        tree.column("movimientos", width=100, anchor=tk.CENTER)
        tree.column("promedio", width=100, anchor=tk.CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Llenar tabla
        for i, item in enumerate(consumo_data, 1):
            tree.insert("", tk.END, values=(
                i,
                item['nombre'],
                item['tipo'].capitalize(),
                item['total_consumido'],
                item['num_movimientos'],
                f"{item['promedio_por_mov']:.1f}"
            ))
        
        # Total consumido
        total_consumido = sum(item['total_consumido'] for item in consumo_data)
        ttk.Label(report_window, text=f"📦 Total consumido en el periodo: {total_consumido:,} unidades", 
                 font=("Arial", 11, "bold")).pack(pady=10)
        
        # Botones
        button_frame = ttk.Frame(report_window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text="Exportar a Excel", 
                  command=lambda: self.export_consumption_report(consumo_data)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cerrar", 
                  command=report_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def export_consumption_report(self, consumo_data):
        """Exporta el reporte de consumo a Excel"""
        if not consumo_data:
            return
        
        # Preparar datos para exportar
        datos = []
        for item in consumo_data:
            datos.append([
                item['nombre'],
                item['tipo'].capitalize(),
                item['total_consumido'],
                item['num_movimientos'],
                f"{item['promedio_por_mov']:.1f}"
            ])
        
        columnas = ["Producto", "Tipo", "Total Consumido", "N° Movimientos", "Promedio por Movimiento"]
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"reporte_consumo_{timestamp}.xlsx"
        
        # Guardar diálogo
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
            initialfile=default_filename,
            title="Guardar Reporte de Consumo"
        )
        
        if not filepath:
            return
        
        try:
            ruta = DataUtils.exportar_a_excel(datos, columnas, os.path.basename(filepath))
            
            if ruta:
                messagebox.showinfo("Éxito", f"✅ Reporte de consumo exportado exitosamente a:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Error al exportar el reporte:\n{e}")
            logger.error(f"Error al exportar reporte de consumo: {e}")
    
    def show_stock_chart(self):
        """Muestra un gráfico del stock por tipo de producto en una ventana separada"""
        # Obtener datos agrupados por tipo
        query = """
        SELECT p.tipo, SUM(s.cantidad) as total_cantidad
        FROM productos p
        JOIN stock s ON p.id_producto = s.producto_id
        GROUP BY p.tipo
        """
        
        stock_data = self.db.fetch_all(query)
        
        if not stock_data:
            messagebox.showinfo("Información", "No hay datos de stock para graficar")
            return
        
        # Preparar datos para el gráfico
        tipos = [item['tipo'].capitalize() for item in stock_data]
        cantidades = [item['total_cantidad'] for item in stock_data]
        
        # Crear una nueva ventana para el gráfico
        chart_window = tk.Toplevel(self.root)
        chart_window.title("Análisis Visual de Stock")
        chart_window.geometry("950x700")
        
        # Título
        ttk.Label(chart_window, text="📊 ANÁLISIS DE STOCK POR TIPO DE PRODUCTO", 
                 font=("Arial", 16, "bold")).pack(pady=15)
        
        # Frame para el gráfico
        chart_frame = ttk.Frame(chart_window)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Generar y mostrar el gráfico
        canvas = DataUtils.generar_grafico_stock(tipos, cantidades, chart_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Información adicional
        info_frame = ttk.Frame(chart_window)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        total_items = sum(cantidades)
        ttk.Label(info_frame, text=f"📦 Total de unidades en inventario: {total_items:,}", 
                 font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=10)
        
        # Botón para cerrar
        ttk.Button(chart_window, text="Cerrar", 
                  command=chart_window.destroy, style="Accent.TButton").pack(pady=10)
    
    def on_product_double_click(self, event):
        """Maneja el doble clic en un producto de la tabla de stock"""
        # Obtener el item seleccionado
        item_id = self.stock_tree.selection()
        if not item_id:
            return
        
        # Obtener los valores del producto
        values = self.stock_tree.item(item_id[0])['values']
        if not values:
            return
        
        # Llenar el formulario con los datos del producto
        self.product_id.set(values[0])  # ID del producto
        
        # Mostrar mensaje informativo
        messagebox.showinfo("Producto Seleccionado", 
                           f"✅ Producto seleccionado: {values[1]}\n"
                           f"📊 Cantidad actual: {values[3]}\n"
                           f"📍 Ubicación: {values[4]}\n\n"
                           f"Ahora puede ingresar la cantidad y tipo de movimiento.")
        
        # Dar focus al campo de cantidad
        self.quantity_entry = event.widget.master.master.master.master.nametowidget('!entry2')
        self.quantity_entry.focus()
    
    def update_status_bar(self):
        """Actualiza la barra de estado con información relevante"""
        try:
            # Obtener valor total del inventario
            query = """
            SELECT SUM(s.cantidad * p.precio_unitario) as valor_total,
                   COUNT(*) as total_productos
            FROM stock s
            JOIN productos p ON s.producto_id = p.id_producto
            """
            
            result = self.db.fetch_all(query)
            valor_total = result[0]['valor_total'] if result and result[0]['valor_total'] else 0
            total_productos = result[0]['total_productos'] if result else 0
            
            # Obtener total de movimientos
            query_mov = "SELECT COUNT(*) as total_movimientos FROM movimientos"
            result_mov = self.db.fetch_all(query_mov)
            total_movimientos = result_mov[0]['total_movimientos'] if result_mov else 0
            
            # Actualizar barra de estado
            status_text = (f"💰 Valor Total Inventario: {DataUtils.formatear_moneda(valor_total)} | "
                          f"📦 Productos: {total_productos} | "
                          f"📊 Movimientos Registrados: {total_movimientos} | "
                          f"🕒 Última actualización: {datetime.now().strftime('%H:%M:%S')}")
            
            self.status_var.set(status_text)
            
        except Exception as e:
            logger.error(f"Error al actualizar barra de estado: {e}")
            self.status_var.set(f"❌ Error al actualizar información | {datetime.now().strftime('%H:%M:%S')}")
    
    def show_about(self):
        """Muestra información sobre la aplicación"""
        about_window = tk.Toplevel(self.root)
        about_window.title("Acerca de")
        about_window.geometry("500x450")
        about_window.resizable(False, False)
        
        # Frame principal
        main_frame = ttk.Frame(about_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo/Icono (simulado con texto)
        ttk.Label(main_frame, text="🔧 SGI", font=("Arial", 24, "bold")).pack(pady=10)
        ttk.Label(main_frame, text="Sistema de Gestión de Inventario", 
                 font=("Arial", 14)).pack(pady=5)
        
        # Información
        from src import __version__, __author__, __email__
        
        info_text = f"""
        Versión: {__version__}
        Desarrollado por: {__author__}
        Contacto: {__email__}
        Institución: Escuela Industrial y Preparatoria Técnica Álvaro Obregón
        Base de Datos: MariaDB 10.4.32
        Python: {sys.version.split()[0]}
        
        Este sistema fue desarrollado para optimizar el control de inventario
        de materiales en el departamento de fotocopiado, permitiendo un
        seguimiento en tiempo real de existencias y generación de alertas
        automáticas para reposición de materiales.
        
        Características Principales:
        • Gestión completa de inventario
        • Registro de movimientos (entradas/salidas)
        • Alertas automáticas de stock crítico
        • Reportes detallados y exportación a Excel
        • Gráficos de análisis visual
        • Sistema de backup integrado
        """
        
        info_label = ttk.Label(main_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(pady=10)
        
        # Botón de cerrar
        ttk.Button(main_frame, text="Cerrar", 
                  command=about_window.destroy).pack(pady=10)

if __name__ == "__main__":
    # Configurar logging para la aplicación
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='app.log'
    )
    logger = logging.getLogger('InventoryApp')
    
    root = tk.Tk()
    
    # Configurar tema oscuro para mejor visualización
    style = ttk.Style()
    style.theme_use('clam')  # Usar tema moderno
    
    # Configurar colores personalizados
    style.configure("TFrame", background="#f5f5f5")
    style.configure("TLabelFrame", background="#f5f5f5", font=("Arial", 10, "bold"))
    style.configure("TLabel", background="#f5f5f5")
    style.configure("TButton", font=("Arial", 10))
    
    # Colores para Treeviews
    style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff")
    style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
    
    app = InventoryApp(root)
    root.mainloop()