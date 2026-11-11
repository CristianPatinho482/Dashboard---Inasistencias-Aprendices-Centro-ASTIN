'use strict';

const { app } = require('@azure/functions');
const { splitList } = require('../shared/auth');

const GRAPH_BASE = 'https://graph.microsoft.com/v1.0';

/**
 * Función rolesSource de Azure Static Web Apps.
 *
 * Se ejecuta después del inicio de sesión y debe devolver los roles personalizados.
 * La pertenencia se puede demostrar por:
 *   1. Claim de grupos del token (si el registro de la app emite grupos).
 *   2. Consulta a Microsoft Graph con el token del usuario.
 *   3. Lista explícita de correos (respaldo operativo).
 *
 * Si no hay configuración o no se puede verificar, devuelve una lista vacía:
 * el acceso falla cerrado.
 */

function groupIdsFromClaims(claims) {
  const groupClaimTypes = new Set([
    'groups',
    'http://schemas.microsoft.com/ws/2008/06/identity/claims/groups',
    'http://schemas.microsoft.com/identity/claims/groups'
  ]);
  return (Array.isArray(claims) ? claims : [])
    .filter(function (claim) {
      return claim && groupClaimTypes.has(claim.typ);
    })
    .map(function (claim) { return String(claim.val || ''); })
    .filter(Boolean);
}

function appRolesFromClaims(claims) {
  const roleClaimTypes = new Set([
    'roles',
    'http://schemas.microsoft.com/ws/2008/06/identity/claims/role'
  ]);
  return (Array.isArray(claims) ? claims : [])
    .filter(function (claim) {
      return claim && roleClaimTypes.has(claim.typ);
    })
    .map(function (claim) { return String(claim.val || ''); })
    .filter(Boolean);
}

async function isMemberOfGroup(groupId, accessToken) {
  const url = new URL(GRAPH_BASE + '/me/memberOf');
  url.searchParams.set('$filter', "id eq '" + groupId + "'");
  url.searchParams.set('$select', 'id');

  const response = await fetch(url.toString(), {
    headers: { Authorization: 'Bearer ' + accessToken }
  });

  if (!response.ok) {
    return false;
  }

  const body = await response.json().catch(function () { return {}; });
  return Array.isArray(body.value) && body.value.some(function (group) {
    return group.id === groupId;
  });
}

app.http('roles', {
  methods: ['POST'],
  authLevel: 'anonymous',
  route: 'roles',
  handler: async function (request, context) {
    let body = {};
    try {
      body = await request.json();
    } catch (error) {
      body = {};
    }

    const nominalRole = String(process.env.NOMINAL_ROLE || 'nominal').trim();
    const allowedGroups = splitList(process.env.ENTRA_NOMINAL_GROUPS);
    const allowedAppRoles = splitList(process.env.ENTRA_NOMINAL_APP_ROLES);
    const allowedEmails = splitList(process.env.ALLOWED_EMAILS).map(function (email) {
      return email.toLowerCase();
    });
    const email = String(body.userDetails || '').trim().toLowerCase();
    const claims = Array.isArray(body.claims) ? body.claims : [];
    const roles = new Set();

    if (email && allowedEmails.indexOf(email) !== -1) {
      roles.add(nominalRole);
    }

    if (allowedAppRoles.length) {
      const appRoles = appRolesFromClaims(claims);
      if (appRoles.some(function (role) { return allowedAppRoles.indexOf(role) !== -1; })) {
        roles.add(nominalRole);
      }
    }

    if (allowedGroups.length && !roles.has(nominalRole)) {
      const claimGroups = groupIdsFromClaims(claims);
      if (claimGroups.some(function (id) { return allowedGroups.indexOf(id) !== -1; })) {
        roles.add(nominalRole);
      } else if (body.accessToken) {
        for (const groupId of allowedGroups) {
          if (await isMemberOfGroup(groupId, body.accessToken)) {
            roles.add(nominalRole);
            break;
          }
        }
      }
    }

    if (!allowedGroups.length && !allowedAppRoles.length && !allowedEmails.length) {
      context.warn('roles: no hay grupos, roles de aplicación ni correos configurados; se deniega el acceso.');
    }

    context.log('roles: ' + roles.size + ' rol(es) asignado(s).');
    return {
      status: 200,
      jsonBody: { roles: Array.from(roles) }
    };
  }
});
