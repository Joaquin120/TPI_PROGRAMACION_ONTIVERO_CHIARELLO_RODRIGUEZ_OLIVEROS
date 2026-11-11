# Spec Delta

## Purpose
Proveer una capa cliente HTTP centralizada en JavaScript nativo para gestionar peticiones REST con prefijo '/api/', normalización de rutas con barra final, cabeceras JSON y formateo unificado de errores.

## ADDED Requirements

### Requirement: Prefijado de base y normalización de endpoints
El módulo cliente HTTP SHALL asegurar que todas las solicitudes dirigidas a la API utilicen el prefijo `/api/` y SHALL preservar o agregar la barra final en los endpoints de colección para evitar redirecciones HTTP 307.

#### Scenario: Petición a colección sin prefijo ni barra final
- **WHEN** el código de la aplicación invoca `api.get('/libros')` o `api.get('libros')`
- **THEN** el módulo envía la solicitud `fetch` a la URL `/api/libros/`

#### Scenario: Petición que ya contiene prefijo y barra final
- **WHEN** el código de la aplicación invoca `api.get('/api/clientes/')`
- **THEN** el módulo envía la solicitud exactamente a `/api/clientes/` sin duplicar el prefijo `/api`

#### Scenario: Petición a recurso individual por identificador
- **WHEN** el código de la aplicación invoca `api.get('/libros/42')`
- **THEN** el módulo envía la solicitud a `/api/libros/42` sin forzar una barra final tras el ID numérico

### Requirement: Configuración de cabeceras y métodos HTTP estándar
El cliente SHALL proveer funciones auxiliares para los verbos GET, POST y PATCH, configurando automáticamente las cabeceras `Accept: application/json` y `Content-Type: application/json` cuando se envíe un cuerpo de datos.

#### Scenario: Envío de datos mediante POST
- **WHEN** se invoca `api.post('/libros/', data)` con un objeto JavaScript como carga útil
- **THEN** el módulo ejecuta `fetch` con método POST, cabeceras JSON y el cuerpo serializado con `JSON.stringify`

#### Scenario: Modificación parcial mediante PATCH
- **WHEN** se invoca `api.patch('/libros/1', data)` con los campos modificados
- **THEN** el módulo ejecuta `fetch` con método PATCH, cabeceras JSON y el cuerpo serializado correspondiente

### Requirement: Deserialización de respuestas exitosas
El módulo cliente SHALL deserializar automáticamente las respuestas con códigos de estado HTTP exitosos (200 OK, 201 Created) retornando los datos en formato objeto JavaScript o array.

#### Scenario: Procesamiento de respuesta exitosa con payload JSON
- **WHEN** la API responde con código HTTP 200 o 201 y un cuerpo con formato JSON válido
- **THEN** la promesa resuelve entregando el objeto o lista JavaScript deserializado

### Requirement: Formateo y captura unificada de errores HTTP y de red
El cliente SHALL capturar y tipificar las respuestas de error HTTP (400, 404, 409, 422, 500) y las fallas de red del navegador, entregando un objeto de error estructurado con código y mensaje accesible sin arrojar excepciones no controladas.

#### Scenario: Captura de error de conflicto 409 por duplicado
- **WHEN** la API responde con HTTP 409 Conflict ante un ISBN o email ya registrado
- **THEN** el cliente retorna un error estructurado indicando status 409 y preservando el detalle emitido por el servidor

#### Scenario: Captura de error de validación 422 de contrato
- **WHEN** la API responde con HTTP 422 Unprocessable Entity
- **THEN** el cliente extrae los mensajes de error de los campos invalidados y los expone amigablemente para la interfaz

#### Scenario: Captura de falla de transporte o red desconectada
- **WHEN** la llamada `fetch` es rechazada por falta de conexión o el servidor responde 502 Bad Gateway
- **THEN** el cliente retorna un error descriptivo de falla de comunicación con el servidor
