'use strict';

const fs = require('node:fs/promises');
const { BlobClient, BlobServiceClient } = require('@azure/storage-blob');
const { DefaultAzureCredential } = require('@azure/identity');

/**
 * Carga el archivo privado de consulta.
 *
 * Modos de acceso, en orden de precedencia:
 *   1. CONSULTA_LOCAL_FILE: solo para desarrollo local. Nunca en Azure.
 *   2. BLOB_SAS_URL: URL completa del blob con SAS de solo lectura. Es la
 *      opción para la API administrada de Static Web Apps, que no tiene
 *      identidad administrada. El SAS vive únicamente en app settings.
 *   3. STORAGE_ACCOUNT_NAME + DefaultAzureCredential: requiere una Function
 *      App propia (bring your own functions) con identidad administrada y el
 *      rol "Storage Blob Data Reader" sobre el contenedor.
 *
 * El contenedor siempre debe ser privado. La API nunca devuelve el contenido
 * crudo del blob: solo la agregación del intervalo solicitado.
 */

let cache = {
  dataset: null,
  expiresAt: 0
};

function ttlMs() {
  const seconds = Number(process.env.CACHE_TTL_SECONDS || 300);
  const safe = Number.isFinite(seconds) ? Math.max(30, seconds) : 300;
  return safe * 1000;
}

function blobConfig() {
  const account = String(process.env.STORAGE_ACCOUNT_NAME || '').trim();
  const endpoint = String(process.env.BLOB_ENDPOINT || '').trim() ||
    (account ? 'https://' + account + '.blob.core.windows.net' : '');
  return {
    sasUrl: String(process.env.BLOB_SAS_URL || '').trim(),
    endpoint: endpoint,
    container: String(process.env.BLOB_CONTAINER || 'consulta-privada').trim(),
    blob: String(process.env.BLOB_NAME || 'consulta_web.json').trim()
  };
}

function assertHttps(url, label) {
  let parsed;
  try {
    parsed = new URL(url);
  } catch (error) {
    throw new Error('La configuración de ' + label + ' no es una URL válida.');
  }
  if (parsed.protocol !== 'https:') {
    throw new Error('La configuración de ' + label + ' debe usar HTTPS.');
  }
  return parsed;
}

async function readLocal() {
  const file = String(process.env.CONSULTA_LOCAL_FILE || '').trim();
  if (!file) return null;
  const text = await fs.readFile(file, 'utf8');
  return JSON.parse(text);
}

async function readBlobWithSas(sasUrl) {
  assertHttps(sasUrl, 'BLOB_SAS_URL');
  const client = new BlobClient(sasUrl);
  const buffer = await client.downloadToBuffer();
  return JSON.parse(buffer.toString('utf8'));
}

async function readBlobWithIdentity(config) {
  if (!config.endpoint) {
    throw new Error('Falta BLOB_SAS_URL o STORAGE_ACCOUNT_NAME/BLOB_ENDPOINT.');
  }
  assertHttps(config.endpoint, 'BLOB_ENDPOINT');
  const service = new BlobServiceClient(config.endpoint, new DefaultAzureCredential());
  const client = service.getContainerClient(config.container).getBlobClient(config.blob);
  const buffer = await client.downloadToBuffer();
  return JSON.parse(buffer.toString('utf8'));
}

function validate(dataset) {
  if (!dataset || typeof dataset !== 'object' || !Array.isArray(dataset.records)) {
    throw new Error('El archivo de consulta no contiene una lista de registros válida.');
  }
  if (dataset.records.length > 250000) {
    throw new Error('El archivo de consulta excede el tamaño permitido.');
  }
  return dataset;
}

async function loadDataset() {
  const now = Date.now();
  if (cache.dataset && now < cache.expiresAt) {
    return cache.dataset;
  }

  const config = blobConfig();
  let dataset = null;

  try {
    dataset = await readLocal();
  } catch (error) {
    const hasRemote = Boolean(config.sasUrl || config.endpoint);
    if (!hasRemote) throw error;
  }

  if (!dataset) {
    dataset = config.sasUrl
      ? await readBlobWithSas(config.sasUrl)
      : await readBlobWithIdentity(config);
  }

  validate(dataset);
  cache = {
    dataset: dataset,
    expiresAt: now + ttlMs()
  };
  return dataset;
}

module.exports = {
  loadDataset: loadDataset,
  blobConfig: blobConfig
};
