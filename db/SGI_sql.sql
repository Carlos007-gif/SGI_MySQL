-- Crear base de datos con codificación compatible con MariaDB
CREATE DATABASE IF NOT EXISTS gestion_inventario 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE gestion_inventario;

-- Tabla de productos
CREATE TABLE IF NOT EXISTS productos (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo ENUM('papel', 'toner', 'encuadernacion', 'otro') NOT NULL,
    precio_unitario DECIMAL(10,2) DEFAULT 0.00,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de stock
CREATE TABLE IF NOT EXISTS stock (
    id_stock INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL DEFAULT 0,
    ubicacion VARCHAR(100) DEFAULT 'Almacen Principal',
    ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_producto_stock 
        FOREIGN KEY (producto_id) 
        REFERENCES productos(id_producto)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabla de movimientos
CREATE TABLE IF NOT EXISTS movimientos (
    id_movimiento INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT NOT NULL,
    tipo ENUM('entrada', 'salida') NOT NULL,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    responsable VARCHAR(100) NOT NULL,
    motivo TEXT,
    CONSTRAINT fk_producto_movimiento 
        FOREIGN KEY (producto_id) 
        REFERENCES productos(id_producto)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Trigger para actualizar stock automáticamente
DELIMITER $$
CREATE TRIGGER actualizar_stock_despues_movimiento
AFTER INSERT ON movimientos
FOR EACH ROW
BEGIN
    IF NEW.tipo = 'entrada' THEN
        UPDATE stock 
        SET cantidad = cantidad + NEW.cantidad,
            ultima_actualizacion = NOW()
        WHERE producto_id = NEW.producto_id;
    ELSEIF NEW.tipo = 'salida' THEN
        UPDATE stock 
        SET cantidad = cantidad - NEW.cantidad,
            ultima_actualizacion = NOW()
        WHERE producto_id = NEW.producto_id;
    END IF;
END$$
DELIMITER ;

-- Vista para reporte de productos con bajo stock
CREATE VIEW vista_alertas_stock AS
SELECT 
    p.id_producto,
    p.nombre,
    p.tipo,
    s.cantidad,
    s.ubicacion,
    CASE 
        WHEN p.tipo = 'papel' AND s.cantidad < 500 THEN 'CRITICO'
        WHEN p.tipo = 'toner' AND s.cantidad < 10 THEN 'CRITICO'
        WHEN p.tipo = 'encuadernacion' AND s.cantidad < 20 THEN 'CRITICO'
        ELSE 'NORMAL'
    END AS nivel_alerta
FROM productos p
JOIN stock s ON p.id_producto = s.producto_id
HAVING nivel_alerta = 'CRITICO';

SHOW TABLES FROM gestion_inventario;
SELECT * FROM information_schema.views 
WHERE table_schema = 'gestion_inventario' AND table_name = 'vista_alertas_stock';

-- Insertar productos típicos de fotocopiado
INSERT INTO productos (nombre, tipo, precio_unitario) VALUES
('Papel A4 75g', 'papel', 45.00),
('Toner Negro HP', 'toner', 850.00),
('Toner Color HP', 'toner', 1200.00),
('Grapadora', 'encuadernacion', 150.00);

-- Inicializar stock con cantidades realistas
INSERT INTO stock (producto_id, cantidad, ubicacion) VALUES
(1, 3000, 'Departamento Fotocopiado'),
(2, 8, 'Almacen Principal'),
(3, 5, 'Almacen Principal'),
(4, 15, 'Departamento Fotocopiado');

-- Registrar algunos movimientos iniciales
INSERT INTO movimientos (producto_id, tipo, cantidad, responsable, motivo) VALUES
(1, 'salida', 500, 'Carlos Martinez', 'Impresión de exámenes parciales'),
(2, 'salida', 2, 'Carlos Martinez', 'Reemplazo de toner en impresora principal'),
(1, 'entrada', 2000, 'Carlos Martinez', 'Compra mensual de papel');

-- Verificar estado actual del stock
SELECT 
    p.nombre AS 'Producto',
    p.tipo AS 'Categoría',
    s.cantidad AS 'Cantidad Actual',
    s.ubicacion AS 'Ubicación'
FROM productos p
JOIN stock s ON p.id_producto = s.producto_id;

-- Consultar alertas activas (debe mostrar toners con stock crítico)
SELECT 
    nombre AS 'Producto',
    cantidad AS 'Stock Actual',
    ubicacion AS 'Ubicación',
    nivel_alerta AS 'Estado'
FROM vista_alertas_stock;