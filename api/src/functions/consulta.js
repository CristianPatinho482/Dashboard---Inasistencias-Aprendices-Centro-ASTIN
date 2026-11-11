'use strict';

const { app } = require('@azure/functions');
const { authorize } = require('../shared/auth');
const { loadDataset } = require('../shared/storage');
const { aggregate, ValidationError } = require('../shared/aggregate');

function jsonResponse(status, body) {
  return {
    status: status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store, max-age=0',
      'Pragma': 'no-cache',
      'X-Content-Type-Options': 'nosniff',
      'X-Robots-Tag': 'noindex, nofollow'
    },
    jsonBody: body
  };
}

app.http('consulta', {
  methods: ['GET'],
  authLevel: 'anonymous',
  route: 'consulta',
  handler: async function (request, context) {
    const auth = authorize(request);
    if (!auth.ok) {
      return jsonResponse(auth.status, {
        error: { code: auth.code, message: auth.message }
      });
    }

    try {
      const dataset = await loadDataset();
      const result = aggregate(dataset, request.query);
      return jsonResponse(200, result);
    } catch (error) {
      if (error instanceof ValidationError) {
        return jsonResponse(400, {
          error: { code: 'invalid_query', message: error.message }
        });
      }

      context.error('consulta: no fue posible generar la respuesta: ' + (error.message || 'error desconocido'));
      return jsonResponse(503, {
        error: {
          code: 'data_unavailable',
          message: 'No fue posible consultar la fuente de datos. Intente de nuevo en unos minutos.'
        }
      });
    }
  }
});
