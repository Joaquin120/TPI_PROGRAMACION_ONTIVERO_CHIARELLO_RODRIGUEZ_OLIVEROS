# Spec Delta

## Purpose
Proveer un servidor web Nginx contenerizado que distribuya los archivos estáticos del frontend y actúe como reverse proxy transparente hacia la API del backend, reescribiendo prefijos y habilitando configuración dinámica vía variables de entorno.

## ADDED Requirements

### Requirement: Servir activos estáticos del frontend
El contenedor frontend SHALL servir todos los recursos estáticos del cliente web (HTML, CSS, JavaScript nativo e imágenes) desde el puerto HTTP 80 aplicando resolución estándar con fallback 404 para rutas inexistentes.

#### Scenario: Solicitud de página principal
- **WHEN** el cliente solicita la ruta raíz `/` o `/index.html`
- **THEN** el servidor responde con código HTTP 200 y el contenido HTML del archivo `index.html`

#### Scenario: Solicitud de recurso estático inexistente
- **WHEN** el cliente realiza una petición sobre un archivo inexistente en el árbol web
- **THEN** el servidor Nginx retorna un código de error HTTP 404 Not Found

### Requirement: Proxy inverso transparente para endpoints API
El servidor Nginx SHALL interceptar todas las peticiones que comiencen con el prefijo `/api/` y reenviarlas hacia el servicio backend configurado en `API_UPSTREAM`, reescribiendo la URI para remover el prefijo `/api` y conservando parámetros de consulta y métodos HTTP.

#### Scenario: Enrutamiento de consulta de catálogo
- **WHEN** el cliente efectúa una petición `GET /api/libros/?limit=10`
- **THEN** Nginx reescribe y reenvía la petición como `GET /libros/?limit=10` al upstream del backend y entrega la respuesta del servicio sin alterar cabeceras esenciales

#### Scenario: Enrutamiento de verificación de diagnóstico
- **WHEN** se solicita el endpoint `GET /api/health/ready`
- **THEN** Nginx reenvía la consulta como `GET /health/ready` al backend y retorna la confirmación HTTP 200

### Requirement: Interpolación controlada de variables de entorno Nginx
La imagen del frontend SHALL limitar la sustitución de variables de entorno de `envsubst` exclusivamente a `API_UPSTREAM` mediante `NGINX_ENVSUBST_FILTER=^API_UPSTREAM$` para preservar variables nativas de Nginx.

#### Scenario: Generación dinámica del bloque upstream
- **WHEN** el contenedor inicia con la variable `API_UPSTREAM=backend:8000`
- **THEN** el archivo generado en `/etc/nginx/conf.d/default.conf` establece `proxy_pass http://backend:8000/;` manteniendo intactas variables como `$uri`
