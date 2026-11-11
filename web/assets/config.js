/*
 * Configuración del portal nominal.
 *
 * En Azure, demoMode se desactiva automáticamente porque el host no es local.
 * Si necesita una demostración en Azure, cámbielo a true de forma temporal y
 * vuelva a false antes de cargar datos reales.
 *
 * El plan Free de Static Web Apps no permite autenticación personalizada ni
 * rolesSource. Use el plan Standard y mantenga requiredRole: "nominal".
 */
(function () {
  'use strict';

  const host = String(window.location.hostname || '').toLowerCase();
  const localPreview =
    host === 'localhost' ||
    host === '127.0.0.1' ||
    host === '::1' ||
    window.location.protocol === 'file:';

  window.ASTIN_CONFIG = {
    demoMode: localPreview,
    apiBase: '/api',
    requiredRole: 'nominal',
    loginUrl: '/.auth/login/aad?post_login_redirect_uri=/consulta.html',
    logoutUrl: '/.auth/logout?post_logout_redirect_uri=/',
    demoDataUrl: 'data/demo_consulta.json',
    pageSize: 100
  };
})();
