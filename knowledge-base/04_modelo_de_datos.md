# Modelo de Datos

## Dominios
1. **Catálogo:** Libros, editoriales, géneros, autores y la tabla intermedia de autoría con roles.
2. **Clientes:** Entidad de compradores identificados por correo electrónico único.
3. **Ventas:** Encabezados de transacciones y renglones de venta que congelan el precio unitario del catálogo.

## ERD (Entity Relationship Diagram)
```
  ┌──────────────┐          ┌───────────────────┐          ┌──────────────┐
  │  EDITORIAL   │          │       LIBRO       │          │    GENERO    │
  ├──────────────┤ 1      N ├───────────────────┤ N      1 ├──────────────┤
  │ id (PK)      │──────────│ id (PK)           │──────────│ id (PK)      │
  │ nombre       │          │ titulo            │          │ nombre       │
  └──────────────┘          │ isbn (UNIQUE)     │          └──────────────┘
                            │ precio (Numeric)  │
                            │ stock (Integer)   │
                            │ editorial_id (FK) │
                            │ genero_id (FK,opt)│
                            └─────────┬─────────┘
                                      │ 1
                                      │
               ┌──────────────────────┴──────────────────────┐
             N │                                           N │
  ┌────────────▼───────┐                        ┌────────────▼────────┐
  │    LIBRO_AUTOR     │                        │    VENTA_RENGLON    │
  ├────────────────────┤                        ├─────────────────────┤
  │ libro_id (PK, FK)  │                        │ id (PK)             │
  │ autor_id (PK, FK)  │                        │ venta_id (FK)       │
  │ rol (Enum/String)  │                        │ libro_id (FK)       │
  │ orden (Integer)    │                        │ cantidad (Integer)  │
  └────────────┬───────┘                        │ precio_unitario     │
             N │                                │ subtotal            │
  ┌────────────▼───────┐                        └────────────▲────────┘
  │       AUTOR        │                                   N │
  ├────────────────────┤                        ┌────────────┴────────┐
  │ id (PK)            │                        │        VENTA        │
  │ nombre             │                        ├─────────────────────┤
  │ biografia (opt)    │                        │ id (PK)             │
  └────────────────────┘                      1 │ cliente_id (FK)     │
                                                │ fecha (Timestamp)   │
  ┌──────────────┐                            N │ total (Numeric)     │
  │   CLIENTE    │                              └────────────┬────────┘
  ├──────────────┤ 1                                         │
  │ id (PK)      │───────────────────────────────────────────┘
  │ nombre       │
  │ email (UNIQ) │
  └──────────────┘
```

## Entidades y Atributos

### 1. `libros`
- `id`: `INTEGER`, Primary Key, autoincremental.
- `titulo`: `VARCHAR(255)`, NOT NULL.
- `isbn`: `VARCHAR(32)`, NOT NULL, UNIQUE.
- `precio`: `NUMERIC(10, 2)`, NOT NULL, Constraint: `precio > 0`.
- `stock`: `INTEGER`, NOT NULL, Constraint: `stock >= 0`.
- `editorial_id`: `INTEGER`, NOT NULL, Foreign Key a `editoriales(id)`.
- `genero_id`: `INTEGER`, NULLABLE, Foreign Key a `generos(id)`.

### 2. `editoriales`
- `id`: `INTEGER`, Primary Key.
- `nombre`: `VARCHAR(128)`, NOT NULL, UNIQUE.

### 3. `generos`
- `id`: `INTEGER`, Primary Key.
- `nombre`: `VARCHAR(128)`, NOT NULL, UNIQUE.

### 4. `autores`
- `id`: `INTEGER`, Primary Key.
- `nombre`: `VARCHAR(128)`, NOT NULL.

### 5. `libros_autores` (Tabla Intermedia)
- `libro_id`: `INTEGER`, Primary Key, Foreign Key a `libros(id)`.
- `autor_id`: `INTEGER`, Primary Key, Foreign Key a `autores(id)`.
- `rol`: `VARCHAR(32)`, NOT NULL (Valores: `'autor'`, `'coautor'`, `'traductor'`, `'ilustrador'`).
- `orden`: `INTEGER`, NOT NULL, Default: 1.

### 6. `clientes`
- `id`: `INTEGER`, Primary Key, autoincremental.
- `nombre`: `VARCHAR(128)`, NOT NULL.
- `email`: `VARCHAR(255)`, NOT NULL, UNIQUE.

### 7. `ventas`
- `id`: `INTEGER`, Primary Key, autoincremental.
- `cliente_id`: `INTEGER`, NOT NULL, Foreign Key a `clientes(id)`.
- `fecha`: `TIMESTAMP WITH TIME ZONE`, NOT NULL, Default `now()`.
- `total`: `NUMERIC(12, 2)`, NOT NULL (Suma de los subtotales de sus renglones).

### 8. `ventas_renglones`
- `id`: `INTEGER`, Primary Key, autoincremental.
- `venta_id`: `INTEGER`, NOT NULL, Foreign Key a `ventas(id)` con eliminación en cascada si aplica.
- `libro_id`: `INTEGER`, NOT NULL, Foreign Key a `libros(id)`.
- `cantidad`: `INTEGER`, NOT NULL, Constraint: `cantidad > 0`.
- `precio_unitario`: `NUMERIC(10, 2)`, NOT NULL. Copiado del precio del libro en el instante de la venta.
- `subtotal`: `NUMERIC(12, 2)`, NOT NULL. Equivalente a `cantidad * precio_unitario`.

## Seed Data Inicial Requerido
Para el arranque del sistema y ejecución de los casos de prueba, la base de datos debe inicializarse con al menos:
- **Editoriales:** Al menos 3 editoriales (ej. *Sudamericana*, *Planeta*, *Alianza*).
- **Géneros:** Al menos 3 géneros (ej. *Ficción*, *Ciencia Ficción*, *Ensayo*).
- **Autores:** Al menos 3 autores (ej. *Gabriel García Márquez*, *Jorge Luis Borges*, *Julio Cortázar*).
- **Libros iniciales:** 2 a 3 libros cargados con stock suficiente para permitir ventas de prueba.
- **Clientes iniciales:** Al menos 1 cliente de muestra registrado.
