/*
 * Agregación semanal de inasistencias.
 *
 * Este archivo es la única fuente de verdad y se ejecuta tanto en la API de
 * Azure Functions (CommonJS) como en el navegador (window.ASTINAggregate).
 * El script scripts/10_sincronizar_agregacion.py copia este archivo a
 * web/assets/aggregate.js; no edite la copia del navegador por separado.
 *
 * La API nunca devuelve los registros crudos: agrupa por aprendiz y ficha y
 * solo entrega los totales del intervalo solicitado.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.ASTINAggregate = factory();
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  class ValidationError extends Error {
    constructor(message) {
      super(message);
      this.name = 'ValidationError';
      this.status = 400;
    }
  }

  const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
  const DIACRITICS_RE = /[\u0300-\u036f]/g;

  function normalizeText(value) {
    return String(value == null ? '' : value)
      .normalize('NFD')
      .replace(DIACRITICS_RE, '')
      .toLowerCase()
      .trim();
  }

  function asString(value, maxLength) {
    const limit = maxLength || 200;
    return String(value == null ? '' : value).trim().slice(0, limit);
  }

  function asNumber(value) {
    if (typeof value === 'number') {
      return Number.isFinite(value) && value >= 0 ? value : 0;
    }
    const text = String(value == null ? '' : value).trim().replace(',', '.');
    const number = Number(text);
    return Number.isFinite(number) && number >= 0 ? number : 0;
  }

  function round1(value) {
    return Math.round((Number(value) || 0) * 10) / 10;
  }

  function parseDate(value, field) {
    const text = asString(value, 10);
    if (!text) return null;
    if (!DATE_RE.test(text)) {
      throw new ValidationError('El parámetro "' + field + '" debe tener formato AAAA-MM-DD.');
    }
    const date = new Date(text + 'T00:00:00Z');
    if (Number.isNaN(date.valueOf()) || date.toISOString().slice(0, 10) !== text) {
      throw new ValidationError('El parámetro "' + field + '" no es una fecha válida.');
    }
    return text;
  }

  function weekStart(value) {
    const text = asString(value, 10);
    if (!DATE_RE.test(text)) return '';
    const date = new Date(text + 'T00:00:00Z');
    if (Number.isNaN(date.valueOf())) return '';
    const offset = (date.getUTCDay() + 6) % 7;
    date.setUTCDate(date.getUTCDate() - offset);
    return date.toISOString().slice(0, 10);
  }

  function readParam(query, key) {
    if (!query) return '';
    if (typeof query.get === 'function') return query.get(key) || '';
    return query[key] == null ? '' : query[key];
  }

  function normalizeRecord(record) {
    if (!record || typeof record !== 'object') return null;
    const id = asString(record.id, 80);
    const name = asString(record.name, 200);
    const date = asString(record.date, 10);
    const ficha = asString(record.ficha, 40);
    if (!id || !name || !DATE_RE.test(date) || !ficha) return null;
    const hours = asNumber(record.hours);
    const unjustified = Math.min(asNumber(record.unjustified), hours);
    return {
      id: id,
      name: name,
      date: date,
      ficha: ficha,
      instructor: asString(record.instructor, 200) || 'Sin instructor',
      hours: hours,
      unjustified: unjustified
    };
  }

  function buildFilters(records) {
    const fichas = new Set();
    const instructors = new Set();
    let minDate = '';
    let maxDate = '';
    for (const record of records) {
      fichas.add(record.ficha);
      instructors.add(record.instructor);
      if (!minDate || record.date < minDate) minDate = record.date;
      if (!maxDate || record.date > maxDate) maxDate = record.date;
    }
    const sortEs = function (a, b) {
      return a.localeCompare(b, 'es');
    };
    return {
      fichas: Array.from(fichas).sort(sortEs),
      instructores: Array.from(instructors).sort(sortEs),
      minDate: minDate,
      maxDate: maxDate
    };
  }

  function aggregate(dataset, query) {
    if (!dataset || !Array.isArray(dataset.records)) {
      throw new ValidationError('La fuente de datos no tiene el formato esperado.');
    }

    const records = dataset.records.map(normalizeRecord).filter(Boolean);
    const filters = buildFilters(records);
    const desde = parseDate(readParam(query, 'desde'), 'desde');
    const hasta = parseDate(readParam(query, 'hasta'), 'hasta');
    if (desde && hasta && desde > hasta) {
      throw new ValidationError('La fecha "desde" no puede ser posterior a "hasta".');
    }

    const ficha = asString(readParam(query, 'ficha'), 40);
    const instructor = asString(readParam(query, 'instructor'), 200);
    const q = normalizeText(readParam(query, 'q')).slice(0, 120);

    const selected = records.filter(function (record) {
      if (ficha && record.ficha !== ficha) return false;
      if (instructor && record.instructor !== instructor) return false;
      if (desde && record.date < desde) return false;
      if (hasta && record.date > hasta) return false;
      if (q && !normalizeText(record.name).includes(q)) return false;
      return true;
    });

    const groups = new Map();
    const learnerIds = new Set();
    let events = 0;
    let hours = 0;
    let unjustified = 0;

    for (const record of selected) {
      events += 1;
      hours += record.hours;
      unjustified += record.unjustified;
      learnerIds.add(record.id);

      const key = record.id + '|' + record.ficha;
      let group = groups.get(key);
      if (!group) {
        group = {
          aprendiz: record.name,
          ficha: record.ficha,
          inasistencias: 0,
          horas: 0,
          noJustificadas: 0,
          weeks: new Map()
        };
        groups.set(key, group);
      }
      group.inasistencias += 1;
      group.horas += record.hours;
      group.noJustificadas += record.unjustified;
      const week = weekStart(record.date);
      group.weeks.set(week, (group.weeks.get(week) || 0) + record.unjustified);
    }

    const rows = Array.from(groups.values()).map(function (group) {
      const peorSemana = group.weeks.size ? Math.max.apply(null, Array.from(group.weeks.values())) : 0;
      const semaforo = peorSemana < 12 ? 'Verde' : peorSemana <= 16 ? 'Amarillo' : 'Rojo';
      return {
        aprendiz: group.aprendiz,
        ficha: group.ficha,
        inasistencias: group.inasistencias,
        horas: round1(group.horas),
        noJustificadas: round1(group.noJustificadas),
        peorSemana: round1(peorSemana),
        semaforo: semaforo
      };
    }).sort(function (a, b) {
      return (
        b.peorSemana - a.peorSemana ||
        b.noJustificadas - a.noJustificadas ||
        a.aprendiz.localeCompare(b.aprendiz, 'es')
      );
    });

    return {
      meta: {
        generatedAt: asString(dataset.generatedAt, 40),
        sourceLabel: asString(dataset.sourceLabel, 120) || 'Corte institucional',
        synthetic: Boolean(dataset.synthetic),
        minDate: filters.minDate,
        maxDate: filters.maxDate,
        desde: desde || filters.minDate,
        hasta: hasta || filters.maxDate,
        totalRecords: selected.length,
        totalLearners: learnerIds.size,
        totalRows: rows.length,
        timezone: 'America/Bogota',
        thresholds: { greenMax: 12, yellowMax: 16 }
      },
      kpis: {
        aprendices: learnerIds.size,
        inasistencias: events,
        horas: round1(hours),
        noJustificadas: round1(unjustified)
      },
      filters: {
        fichas: filters.fichas,
        instructores: filters.instructores,
        minDate: filters.minDate,
        maxDate: filters.maxDate
      },
      applied: {
        ficha: ficha,
        instructor: instructor,
        desde: desde || '',
        hasta: hasta || '',
        q: asString(readParam(query, 'q'), 120)
      },
      rows: rows
    };
  }

  return {
    aggregate: aggregate,
    weekStart: weekStart,
    normalizeText: normalizeText,
    ValidationError: ValidationError
  };
});
