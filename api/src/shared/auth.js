'use strict';

/**
 * Autorización de la API nominal.
 *
 * La regla de ruta de Azure Static Web Apps ya exige el rol configurado, pero
 * la API vuelve a validar el principal para no depender de una sola capa.
 * No se registran correos, nombres ni identificadores de aprendices.
 */

function splitList(value) {
  return String(value == null ? '' : value)
    .split(',')
    .map(function (item) { return item.trim(); })
    .filter(Boolean);
}

function getPrincipal(request) {
  const header = request && request.headers ? request.headers.get('x-ms-client-principal') : null;
  if (!header) return null;
  try {
    const decoded = Buffer.from(header, 'base64').toString('utf8');
    const principal = JSON.parse(decoded);
    return principal && typeof principal === 'object' ? principal : null;
  } catch (error) {
    return null;
  }
}

function authorize(request) {
  const principal = getPrincipal(request);
  if (!principal) {
    return {
      ok: false,
      status: 401,
      code: 'unauthenticated',
      message: 'Inicie sesión con su cuenta institucional para consultar datos nominales.'
    };
  }

  const roles = Array.isArray(principal.userRoles) ? principal.userRoles : [];
  if (!roles.includes('authenticated')) {
    return {
      ok: false,
      status: 401,
      code: 'unauthenticated',
      message: 'La sesión no está autenticada.'
    };
  }

  const mode = String(process.env.AUTH_MODE || 'roles').trim().toLowerCase();
  const email = String(principal.userDetails || '').trim().toLowerCase();

  if (mode === 'allowlist') {
    const allowedEmails = splitList(process.env.ALLOWED_EMAILS).map(function (item) {
      return item.toLowerCase();
    });
    const allowedDomains = splitList(process.env.ALLOWED_EMAIL_DOMAINS).map(function (item) {
      return item.replace(/^@/, '').toLowerCase();
    });
    const domain = email.indexOf('@') !== -1 ? email.split('@').pop() : '';
    const emailAllowed = allowedEmails.indexOf(email) !== -1;
    const domainAllowed = domain && allowedDomains.indexOf(domain) !== -1;

    if (!emailAllowed && !domainAllowed) {
      return {
        ok: false,
        status: 403,
        code: 'forbidden',
        message: 'Su cuenta no está autorizada para consultar datos nominales.'
      };
    }
    return { ok: true, principal: principal, email: email };
  }

  const requiredRole = String(process.env.NOMINAL_ROLE || 'nominal').trim();
  if (!requiredRole || !roles.includes(requiredRole)) {
    return {
      ok: false,
      status: 403,
      code: 'forbidden',
      message: 'Su cuenta no tiene el rol requerido para consultar datos nominales.'
    };
  }

  return { ok: true, principal: principal, email: email };
}

module.exports = {
  splitList: splitList,
  getPrincipal: getPrincipal,
  authorize: authorize
};
