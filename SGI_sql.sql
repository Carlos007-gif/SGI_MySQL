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