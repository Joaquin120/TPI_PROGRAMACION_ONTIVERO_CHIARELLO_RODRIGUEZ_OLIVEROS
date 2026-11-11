import { describe, it, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { ApiError, api } from './api.js';

describe('ApiError', () => {
  it('instantiates with custom message, status and data', () => {
    const data = { detail: 'Campo requerido' };
    const err = new ApiError('Error personalizado', 400, data);

    assert.ok(err instanceof Error);
    assert.ok(err instanceof ApiError);
    assert.strictEqual(err.name, 'ApiError');
    assert.strictEqual(err.message, 'Error personalizado');
    assert.strictEqual(err.status, 400);
    assert.deepStrictEqual(err.data, data);
  });

  it('uses default status 500 and data null when omitted', () => {
    const err = new ApiError('Fallo del servidor');

    assert.strictEqual(err.name, 'ApiError');
    assert.strictEqual(err.message, 'Fallo del servidor');
    assert.strictEqual(err.status, 500);
    assert.strictEqual(err.data, null);
  });
});

describe('buildUrl', () => {
  it('adds /api/ prefix and trailing slash when missing', () => {
    assert.strictEqual(api.buildUrl('/libros'), '/api/libros/');
    assert.strictEqual(api.buildUrl('libros'), '/api/libros/');
  });

  it('preserves existing /api prefix and normalizes trailing slash', () => {
    assert.strictEqual(api.buildUrl('/api/libros'), '/api/libros/');
    assert.strictEqual(api.buildUrl('/api/libros/'), '/api/libros/');
  });

  it('does not force trailing slash on purely numeric resource IDs', () => {
    assert.strictEqual(api.buildUrl('/libros/42'), '/api/libros/42');
    assert.strictEqual(api.buildUrl('/api/clientes/1'), '/api/clientes/1');
  });

  it('serializes query parameters with URLSearchParams', () => {
    const result = api.buildUrl('/libros', { limit: 20, offset: 0, titulo: 'faro' });
    assert.strictEqual(result, '/api/libros/?limit=20&offset=0&titulo=faro');
  });
});

describe('api HTTP requests (fetch mock)', () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('api.get performs GET request and parses JSON on 200 OK', async () => {
    const mockData = [{ id: 1, titulo: 'El principito' }];

    globalThis.fetch = async (url, options) => {
      assert.strictEqual(url, '/api/libros/');
      assert.strictEqual(options.method, 'GET');
      assert.strictEqual(options.headers['Accept'], 'application/json');
      return {
        ok: true,
        status: 200,
        json: async () => mockData
      };
    };

    const result = await api.get('/libros');
    assert.deepStrictEqual(result, mockData);
  });

  it('api.post sends JSON Content-Type and stringified body on 201 Created', async () => {
    const payload = { titulo: 'Libro Nuevo', precio: 1500 };
    const responsePayload = { id: 10, ...payload };

    globalThis.fetch = async (url, options) => {
      assert.strictEqual(url, '/api/libros/');
      assert.strictEqual(options.method, 'POST');
      assert.strictEqual(options.headers['Accept'], 'application/json');
      assert.strictEqual(options.headers['Content-Type'], 'application/json');
      assert.strictEqual(options.body, JSON.stringify(payload));
      return {
        ok: true,
        status: 201,
        json: async () => responsePayload
      };
    };

    const result = await api.post('/libros', payload);
    assert.deepStrictEqual(result, responsePayload);
  });

  it('api.patch sends JSON Content-Type and stringified body on 200 OK', async () => {
    const payload = { precio: 2200 };
    const responsePayload = { id: 5, titulo: 'Libro Existente', precio: 2200 };

    globalThis.fetch = async (url, options) => {
      assert.strictEqual(url, '/api/libros/5');
      assert.strictEqual(options.method, 'PATCH');
      assert.strictEqual(options.headers['Accept'], 'application/json');
      assert.strictEqual(options.headers['Content-Type'], 'application/json');
      assert.strictEqual(options.body, JSON.stringify(payload));
      return {
        ok: true,
        status: 200,
        json: async () => responsePayload
      };
    };

    const result = await api.patch('/libros/5', payload);
    assert.deepStrictEqual(result, responsePayload);
  });

  it('returns null on 204 No Content', async () => {
    globalThis.fetch = async () => {
      return {
        ok: true,
        status: 204
      };
    };

    const result = await api.get('/libros/1');
    assert.strictEqual(result, null);
  });

  it('throws ApiError on 409 Conflict extracting detail string', async () => {
    globalThis.fetch = async () => {
      return {
        ok: false,
        status: 409,
        json: async () => ({ detail: 'El ISBN ya está registrado' })
      };
    };

    await assert.rejects(
      async () => {
        await api.post('/libros', { isbn: '978-84-376-0494-7' });
      },
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.strictEqual(err.status, 409);
        assert.strictEqual(err.message, 'El ISBN ya está registrado');
        assert.deepStrictEqual(err.data, { detail: 'El ISBN ya está registrado' });
        return true;
      }
    );
  });

  it('throws ApiError on 422 Unprocessable Entity extracting detail array', async () => {
    const validationErrors = [
      { loc: ['body', 'isbn'], msg: 'ISBN inválido', type: 'value_error' }
    ];

    globalThis.fetch = async () => {
      return {
        ok: false,
        status: 422,
        json: async () => ({ detail: validationErrors })
      };
    };

    await assert.rejects(
      async () => {
        await api.post('/libros', {});
      },
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.strictEqual(err.status, 422);
        assert.strictEqual(err.message, 'Error de validación en los datos enviados.');
        assert.deepStrictEqual(err.data, validationErrors);
        return true;
      }
    );
  });

  it('throws ApiError with status 0 on network error (fetch rejection)', async () => {
    globalThis.fetch = async () => {
      throw new TypeError('Failed to fetch');
    };

    await assert.rejects(
      async () => {
        await api.get('/libros');
      },
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.strictEqual(err.status, 0);
        assert.strictEqual(
          err.message,
          'No se pudo conectar con el servidor. Verifique su conexión de red.'
        );
        assert.strictEqual(err.data, null);
        return true;
      }
    );
  });

  it('throws ApiError on other HTTP errors (e.g. 500)', async () => {
    globalThis.fetch = async () => {
      return {
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Error interno en la base de datos' })
      };
    };

    await assert.rejects(
      async () => {
        await api.get('/libros');
      },
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.strictEqual(err.status, 500);
        assert.strictEqual(err.message, 'Error interno en la base de datos');
        return true;
      }
    );
  });
});
