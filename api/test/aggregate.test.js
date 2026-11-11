'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const apiAggregate = require('../src/shared/aggregate.js');
const webAggregate = require('../../web/assets/aggregate.js');

const dataset = {
  generatedAt: '2026-11-11T08:00:00-05:00',
  sourceLabel: 'Prueba sintética',
  synthetic: true,
  records: [
    { id: 'A1', name: 'Ana Demo', date: '2026-08-03', ficha: 'F1', instructor: 'Instructora Uno', hours: 4, unjustified: 4 },
    { id: 'A1', name: 'Ana Demo', date: '2026-08-04', ficha: 'F1', instructor: 'Instructora Uno', hours: 8, unjustified: 8 },
    { id: 'A1', name: 'Ana Demo', date: '2026-08-10', ficha: 'F1', instructor: 'Instructora Uno', hours: 4, unjustified: 0 },
    { id: 'A2', name: 'Luis Demo', date: '2026-08-05', ficha: 'F2', instructor: 'Instructor Dos', hours: 20, unjustified: 20 },
    { id: 'A2', name: 'Luis Demo', date: '2026-08-06', ficha: 'F2', instructor: 'Instructor Dos', hours: 2, unjustified: 2 },
    { id: 'A3', name: 'Sofía Demo', date: '2026-08-12', ficha: 'F1', instructor: 'Instructora Uno', hours: 4, unjustified: 4 }
  ]
};

test('la copia del navegador es idéntica a la de la API', function () {
  const apiFile = path.join(__dirname, '..', 'src', 'shared', 'aggregate.js');
  const webFile = path.join(__dirname, '..', '..', 'web', 'assets', 'aggregate.js');
  const normalize = function (file) {
    return fs.readFileSync(file, 'utf8').replace(/\r\n/g, '\n');
  };
  assert.equal(normalize(webFile), normalize(apiFile));
});

test('weekStart devuelve el lunes de la semana', function () {
  assert.equal(apiAggregate.weekStart('2026-08-03'), '2026-08-03');
  assert.equal(apiAggregate.weekStart('2026-08-09'), '2026-08-03');
  assert.equal(apiAggregate.weekStart('2026-08-10'), '2026-08-10');
});

test('agrupa, calcula semáforo y ordena por peor semana', function () {
  const result = apiAggregate.aggregate(dataset, {});
  assert.equal(result.kpis.aprendices, 3);
  assert.equal(result.kpis.inasistencias, 6);
  assert.equal(result.kpis.horas, 42);
  assert.equal(result.kpis.noJustificadas, 38);
  assert.equal(result.meta.totalRecords, 6);
  assert.equal(result.meta.totalRows, 3);
  assert.equal(result.rows[0].aprendiz, 'Luis Demo');
  assert.equal(result.rows[0].peorSemana, 22);
  assert.equal(result.rows[0].semaforo, 'Rojo');
  assert.equal(result.rows[1].aprendiz, 'Ana Demo');
  assert.equal(result.rows[1].peorSemana, 12);
  assert.equal(result.rows[1].semaforo, 'Amarillo');
  assert.equal(result.rows[2].aprendiz, 'Sofía Demo');
  assert.equal(result.rows[2].semaforo, 'Verde');
});

test('respeta filtros de ficha, instructor, fecha y búsqueda', function () {
  const byFicha = apiAggregate.aggregate(dataset, { ficha: 'F1' });
  assert.equal(byFicha.kpis.aprendices, 2);
  assert.equal(byFicha.kpis.inasistencias, 4);

  const byInstructor = apiAggregate.aggregate(dataset, { instructor: 'Instructor Dos' });
  assert.equal(byInstructor.kpis.aprendices, 1);
  assert.equal(byInstructor.rows[0].aprendiz, 'Luis Demo');

  const byDate = apiAggregate.aggregate(dataset, { desde: '2026-08-05', hasta: '2026-08-10' });
  assert.equal(byDate.kpis.inasistencias, 3);

  const bySearch = apiAggregate.aggregate(dataset, { q: 'sofia' });
  assert.equal(bySearch.kpis.aprendices, 1);
  assert.equal(bySearch.rows[0].aprendiz, 'Sofía Demo');
});

test('rechaza fechas inválidas y rangos invertidos', function () {
  assert.throws(function () {
    apiAggregate.aggregate(dataset, { desde: '2026-13-01' });
  }, apiAggregate.ValidationError);

  assert.throws(function () {
    apiAggregate.aggregate(dataset, { desde: '2026-09-01', hasta: '2026-08-01' });
  }, apiAggregate.ValidationError);
});

test('la copia del navegador produce el mismo resultado', function () {
  const apiResult = apiAggregate.aggregate(dataset, { q: 'demo' });
  const webResult = webAggregate.aggregate(dataset, { q: 'demo' });
  assert.deepEqual(webResult, apiResult);
});
