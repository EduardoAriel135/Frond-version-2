-- =====================================================================
-- Cine Paradiso - Script de creación y carga (Hito 1, versión corregida)
-- Requiere MySQL 8.0.16 o superior (los CHECK se aplican desde esa versión).
-- Ejecutar con el cliente mysql o MySQL Workbench (usa DELIMITER para los triggers):
--     mysql -u root -p < cine_paradiso_corregido.sql
-- =====================================================================

-- PENDIENTE DE DECISIÓN DEL GRUPO: el script original empezaba con
-- DROP DATABASE IF EXISTS cine_paradiso;
-- Borra todos los datos existentes. Queda comentado hasta que el grupo lo apruebe.
-- Sin esa línea, el CREATE DATABASE falla si la base ya existe (no se pisa nada).

SET NAMES utf8mb4;

CREATE DATABASE cine_paradiso
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE cine_paradiso;

-- ---------------------------------------------------------------------
-- Usuarios (S20, S21)
-- ---------------------------------------------------------------------
CREATE TABLE usuarios (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    nombre        VARCHAR(80)  NOT NULL,
    email         VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol           ENUM('administrador','cliente') NOT NULL DEFAULT 'cliente'
);

-- ---------------------------------------------------------------------
-- Locales y salas: precargados y fijos (S6). Sin endpoints de alta/baja.
-- ---------------------------------------------------------------------
CREATE TABLE locales (
    id     INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Filas identificadas con letras (S7): fila 1 = A ... fila 26 = Z.
CREATE TABLE salas (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    local_id  INT NOT NULL,
    nombre    VARCHAR(50) NOT NULL,
    filas     SMALLINT NOT NULL,
    columnas  SMALLINT NOT NULL,
    capacidad SMALLINT GENERATED ALWAYS AS (filas * columnas) STORED,
    UNIQUE KEY uq_sala_local (local_id, nombre),
    CONSTRAINT chk_salas_filas    CHECK (filas BETWEEN 1 AND 26),
    CONSTRAINT chk_salas_columnas CHECK (columnas BETWEEN 1 AND 50),
    FOREIGN KEY (local_id) REFERENCES locales(id)
);

-- ---------------------------------------------------------------------
-- Películas (S8, S9, S10). El período de cartelera es de la película.
-- ---------------------------------------------------------------------
CREATE TABLE generos (
    id     INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE peliculas (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    tmdb_id       INT NOT NULL UNIQUE,
    titulo        VARCHAR(200) NOT NULL,
    sinopsis      TEXT,
    poster_url    VARCHAR(500),
    duracion_min  SMALLINT NOT NULL,
    clasificacion ENUM('ATP','+13','+16','+18') NOT NULL,
    vigente_desde DATE NOT NULL,
    vigente_hasta DATE NOT NULL,
    activa        TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT chk_peliculas_duracion CHECK (duracion_min > 0),
    CONSTRAINT chk_peliculas_periodo  CHECK (vigente_hasta >= vigente_desde)
);

CREATE TABLE pelicula_genero (
    pelicula_id INT NOT NULL,
    genero_id   INT NOT NULL,
    PRIMARY KEY (pelicula_id, genero_id),
    FOREIGN KEY (pelicula_id) REFERENCES peliculas(id) ON DELETE CASCADE,
    FOREIGN KEY (genero_id)   REFERENCES generos(id)
);

-- ---------------------------------------------------------------------
-- Funciones (S4, S11, S12). Fecha y hora en un único DATETIME.
-- Reglas de período y de 20 minutos de limpieza: ver triggers más abajo.
-- ---------------------------------------------------------------------
CREATE TABLE funciones (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    pelicula_id INT NOT NULL,
    sala_id     INT NOT NULL,
    inicio      DATETIME NOT NULL,
    precio      DECIMAL(10,2) NOT NULL,
    activa      TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT chk_funciones_precio CHECK (precio > 0),
    KEY idx_funciones_sala_inicio (sala_id, inicio),
    FOREIGN KEY (pelicula_id) REFERENCES peliculas(id),
    FOREIGN KEY (sala_id)     REFERENCES salas(id)
);

-- ---------------------------------------------------------------------
-- Servicios (S5): disponibles para todas las salas, sin stock.
-- ---------------------------------------------------------------------
CREATE TABLE servicios (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    precio      DECIMAL(10,2) NOT NULL,
    activo      TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT chk_servicios_precio CHECK (precio > 0)
);

-- ---------------------------------------------------------------------
-- Compras (S1, S13, S14, S16, S17, S19). Una compra = una función = un QR.
--   activa    -> pagada (pago simulado), QR válido
--   usada     -> QR validado al ingresar (cuenta como película vista, S22)
--   cancelada -> butacas liberadas y QR inválido
-- ---------------------------------------------------------------------
CREATE TABLE compras (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id         INT NOT NULL,
    funcion_id         INT NOT NULL,
    fecha              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total              DECIMAL(12,2) NOT NULL,
    estado             ENUM('activa','usada','cancelada') NOT NULL DEFAULT 'activa',
    qr_token           VARCHAR(64) NOT NULL UNIQUE,  -- generado en Python con secrets (S17)
    fecha_cancelacion  DATETIME NULL,
    fecha_validacion   DATETIME NULL,
    UNIQUE KEY uq_compra_funcion (id, funcion_id),  -- lo usa la FK compuesta de entradas
    KEY idx_compras_estado (estado),
    CONSTRAINT chk_compras_total       CHECK (total >= 0),
    CONSTRAINT chk_compras_cancelacion CHECK ((estado = 'cancelada') = (fecha_cancelacion IS NOT NULL)),
    CONSTRAINT chk_compras_validacion  CHECK ((estado = 'usada') = (fecha_validacion IS NOT NULL)),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (funcion_id) REFERENCES funciones(id)
);

-- ---------------------------------------------------------------------
-- Entradas: una por butaca. Sin QR propio (S16).
-- La FK compuesta obliga a que la entrada sea de la misma función que su compra.
-- "cancelada" se copia desde la compra (trigger trg_compras_au) para liberar la butaca.
-- uq_funcion_butaca impide vender dos veces la misma butaca en una función,
-- también con compras simultáneas (S23): las entradas canceladas tienen
-- ocupada = NULL y no cuentan para la restricción.
-- ---------------------------------------------------------------------
CREATE TABLE entradas (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    compra_id  INT NOT NULL,
    funcion_id INT NOT NULL,
    fila       SMALLINT NOT NULL,
    columna    SMALLINT NOT NULL,
    precio     DECIMAL(10,2) NOT NULL,
    cancelada  TINYINT(1) NOT NULL DEFAULT 0,
    ocupada    TINYINT GENERATED ALWAYS AS (IF(cancelada = 0, 1, NULL)) STORED,
    UNIQUE KEY uq_funcion_butaca (funcion_id, fila, columna, ocupada),
    CONSTRAINT chk_entradas_fila    CHECK (fila >= 1),
    CONSTRAINT chk_entradas_columna CHECK (columna >= 1),
    CONSTRAINT chk_entradas_precio  CHECK (precio > 0),
    FOREIGN KEY (compra_id, funcion_id) REFERENCES compras(id, funcion_id)
);

CREATE TABLE compra_servicios (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    compra_id       INT NOT NULL,
    servicio_id     INT NOT NULL,
    cantidad        SMALLINT NOT NULL DEFAULT 1,
    precio_unitario DECIMAL(10,2) NOT NULL,
    UNIQUE KEY uq_compra_servicio (compra_id, servicio_id),
    CONSTRAINT chk_cs_cantidad CHECK (cantidad >= 1),
    CONSTRAINT chk_cs_precio   CHECK (precio_unitario > 0),
    FOREIGN KEY (compra_id)   REFERENCES compras(id),
    FOREIGN KEY (servicio_id) REFERENCES servicios(id)
);

-- =====================================================================
-- Triggers: reglas que un CHECK no puede expresar porque miran otras filas.
-- =====================================================================
DELIMITER //

-- S10 y S12: la función cae dentro del período de cartelera y no se superpone
-- con otra función activa de la misma sala, dejando 20 minutos de limpieza.
CREATE PROCEDURE validar_funcion(
    IN p_id INT, IN p_pelicula_id INT, IN p_sala_id INT, IN p_inicio DATETIME)
BEGIN
    DECLARE v_desde DATE;
    DECLARE v_hasta DATE;
    DECLARE v_duracion SMALLINT;
    DECLARE v_sala INT;

    SELECT vigente_desde, vigente_hasta, duracion_min
      INTO v_desde, v_hasta, v_duracion
      FROM peliculas WHERE id = p_pelicula_id;

    IF DATE(p_inicio) NOT BETWEEN v_desde AND v_hasta THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'La función está fuera del período de cartelera de la película';
    END IF;

    -- Bloquea la sala para que dos altas simultáneas no se superpongan.
    SELECT id INTO v_sala FROM salas WHERE id = p_sala_id FOR UPDATE;

    IF EXISTS (
        SELECT 1
          FROM funciones f
          JOIN peliculas p ON p.id = f.pelicula_id
         WHERE f.sala_id = p_sala_id
           AND f.activa = 1
           AND f.id <> IFNULL(p_id, 0)
           AND p_inicio < f.inicio + INTERVAL (p.duracion_min + 20) MINUTE
           AND f.inicio < p_inicio + INTERVAL (v_duracion + 20) MINUTE
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'La función se superpone con otra de la misma sala (incluye 20 minutos de limpieza)';
    END IF;
END//

CREATE TRIGGER trg_funciones_bi BEFORE INSERT ON funciones
FOR EACH ROW
BEGIN
    IF NEW.activa = 1 THEN
        CALL validar_funcion(NULL, NEW.pelicula_id, NEW.sala_id, NEW.inicio);
    END IF;
END//

CREATE TRIGGER trg_funciones_bu BEFORE UPDATE ON funciones
FOR EACH ROW
BEGIN
    IF NEW.activa = 1 THEN
        CALL validar_funcion(NEW.id, NEW.pelicula_id, NEW.sala_id, NEW.inicio);
    END IF;
END//

-- S10: no se puede acortar el período dejando funciones activas afuera.
CREATE TRIGGER trg_peliculas_bu BEFORE UPDATE ON peliculas
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1 FROM funciones
         WHERE pelicula_id = NEW.id
           AND activa = 1
           AND DATE(inicio) NOT BETWEEN NEW.vigente_desde AND NEW.vigente_hasta
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Hay funciones activas fuera del nuevo período de cartelera';
    END IF;
END//

-- Butaca dentro de la sala, compra activa y máximo 6 entradas por compra (S3, S7).
CREATE TRIGGER trg_entradas_bi BEFORE INSERT ON entradas
FOR EACH ROW
BEGIN
    DECLARE v_filas SMALLINT;
    DECLARE v_columnas SMALLINT;
    DECLARE v_estado VARCHAR(10);

    SELECT s.filas, s.columnas INTO v_filas, v_columnas
      FROM funciones f JOIN salas s ON s.id = f.sala_id
     WHERE f.id = NEW.funcion_id;

    IF NEW.fila > v_filas OR NEW.columna > v_columnas THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La butaca no existe en la sala de la función';
    END IF;

    SELECT estado INTO v_estado FROM compras WHERE id = NEW.compra_id;
    IF v_estado <> 'activa' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La compra no está activa';
    END IF;

    IF (SELECT COUNT(*) FROM entradas WHERE compra_id = NEW.compra_id) >= 6 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Una compra admite como máximo 6 entradas';
    END IF;
END//

-- Solo se permiten activa -> cancelada y activa -> usada (QR de un solo uso, S17).
CREATE TRIGGER trg_compras_bu BEFORE UPDATE ON compras
FOR EACH ROW
BEGIN
    IF NEW.estado <> OLD.estado AND OLD.estado <> 'activa' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La compra ya fue cancelada o utilizada';
    END IF;
END//

-- S14: cancelar la compra libera todas sus butacas.
CREATE TRIGGER trg_compras_au AFTER UPDATE ON compras
FOR EACH ROW
BEGIN
    IF NEW.estado = 'cancelada' AND OLD.estado <> 'cancelada' THEN
        UPDATE entradas SET cancelada = 1 WHERE compra_id = NEW.id;
    END IF;
END//

DELIMITER ;

-- =====================================================================
-- Datos al inicializar la base
-- =====================================================================
INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES
('Administrador', 'admin@cineparadiso.com',
 'scrypt:32768:8:1$O5LVFkHA4utaEh3N$547bdbbaf9174db804128272be3eda2d47d735a2e4a3ebd965ea8dca293665ea56feb1e08f206bd9a9e233eeb8a14340a3bcc4f7e111748532e0b5ea7306cd3d',
 'administrador');

INSERT INTO locales (id, nombre) VALUES
(1, 'Cine Paradiso Centro'),
(2, 'Cine Paradiso Norte'),
(3, 'Cine Paradiso Sur');

INSERT INTO salas (local_id, nombre, filas, columnas) VALUES
(1, 'Sala 1', 10, 12),
(1, 'Sala 2',  8, 10),
(2, 'Sala 1', 12, 15),
(2, 'Sala 2',  6,  8),
(3, 'Sala 1',  9, 10),
(3, 'Sala 2',  5,  6);

INSERT INTO generos (nombre) VALUES
('Acción'), ('Aventura'), ('Animación'), ('Comedia'), ('Crimen'),
('Documental'), ('Drama'), ('Familia'), ('Fantasía'), ('Historia'),
('Terror'), ('Música'), ('Misterio'), ('Romance'), ('Ciencia ficción'),
('Suspenso'), ('Bélica'), ('Western');
