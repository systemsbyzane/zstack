import { homedir } from 'node:os';
import { join } from 'node:path';
import { createServer as createHttpServer } from 'node:http';
import { execFile } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { lstat, open, readFile, rename, unlink } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { getSafeThreadHref } from './public/status-view.js';

const HOST = '127.0.0.1';
const PORT = 65200;
const MAX_PROJECTION_BYTES = 1024 * 1024;
const MAX_ASSIGNMENTS = 500;
const PROJECTION_PATH = process.env.CORTEX_STATUS_PATH || join(homedir(), '.codex/cortex/status.json');
const SCHEMA_PATH = process.env.CORTEX_SCHEMA_PATH || join(homedir(), '.codex/cortex/status.schema.json');
const JOURNAL_PATH = fileURLToPath(new URL('./submission-journal.json', import.meta.url));
const T3_CLI_PATH = process.env.CORTEX_T3_CLI || join(homedir(), '.t3/bin/t3');
const T3CODE_HOME = process.env.T3CODE_HOME || join(homedir(), '.t3');
const FIXED_THREAD_ID = process.env.CORTEX_CHIEF_THREAD_ID || '';
const FIXED_ENVIRONMENT_ID = process.env.CORTEX_ENVIRONMENT_ID || '';
const SERVICE_ID = 'cortex-status-board';
const ASSIGNMENT_ID = 'C004';
const PROTOCOL_VERSION = 1;
const SOURCE_IDENTITY_TOKEN = 'c004-source-build-identity';
const MAX_REQUEST_BYTES = 16 * 1024;
const MAX_MESSAGE_CODEPOINTS = 8000;
const MAX_JOURNAL_RECORDS = 50;
const MAX_CLI_OUTPUT_BYTES = 64 * 1024;
const SUBMISSION_STATES = ['pending', 'sent', 'unknown', 'not-sent'];

const PUBLIC_ASSETS = new Map([
  ['/', ['index.html', 'text/html; charset=utf-8']],
  ['/index.html', ['index.html', 'text/html; charset=utf-8']],
  ['/app.js', ['app.js', 'text/javascript; charset=utf-8']],
  ['/status-view.js', ['status-view.js', 'text/javascript; charset=utf-8']],
  ['/styles.css', ['styles.css', 'text/css; charset=utf-8']],
]);

const TOP_LEVEL_KEYS = ['schemaVersion', 'generatedAt', 'chief', 'assignments'];
const CHIEF_KEYS = ['link'];
const ASSIGNMENT_KEYS = [
  'assignmentId',
  'title',
  'status',
  'phase',
  'summary',
  'lastReportedAt',
  'coordinatorLink',
  'blocker',
  'decisionNeeded',
  'testedRevision',
  'reviewState',
];
const ASSIGNMENT_STATUSES = ['needs-you', 'blocked', 'ready-for-review', 'working', 'done', 'unknown'];
const REVIEW_STATES = ['not-requested', 'pending', 'handled'];

export class ProjectionError extends Error {
  constructor(message = 'Invalid status projection.') {
    super(message);
    this.name = 'ProjectionError';
  }
}

function fail(message) {
  throw new ProjectionError(message);
}

function sameSet(actual, expected) {
  return Array.isArray(actual)
    && actual.length === expected.length
    && expected.every((value) => actual.includes(value));
}

function assertSchemaContract(schema) {
  if (!schema || typeof schema !== 'object' || Array.isArray(schema)) fail();
  if (schema.type !== 'object' || schema.additionalProperties !== false) fail();
  if (!sameSet(schema.required, TOP_LEVEL_KEYS)) fail();
  if (!schema.properties || !sameSet(Object.keys(schema.properties), TOP_LEVEL_KEYS)) fail();

  const props = schema.properties;
  if (props.schemaVersion?.const !== 1) fail();
  if (props.generatedAt?.type !== 'string' || props.generatedAt?.format !== 'date-time') fail();
  if (props.chief?.type !== 'object' || props.chief?.additionalProperties !== false) fail();
  if (!sameSet(props.chief?.required, CHIEF_KEYS)) fail();
  if (!props.chief?.properties || !sameSet(Object.keys(props.chief.properties), CHIEF_KEYS)) fail();
  if (props.chief.properties.link?.type !== 'string') fail();

  const assignmentArray = props.assignments;
  const assignment = assignmentArray?.items;
  if (assignmentArray?.type !== 'array' || assignment?.type !== 'object') fail();
  if (assignment.additionalProperties !== false || !sameSet(assignment.required, ASSIGNMENT_KEYS)) fail();
  if (!assignment.properties || !sameSet(Object.keys(assignment.properties), ASSIGNMENT_KEYS)) fail();
  if (!sameSet(assignment.properties.status?.enum, ASSIGNMENT_STATUSES)) fail();
  if (!sameSet(assignment.properties.reviewState?.enum, REVIEW_STATES)) fail();
}

export async function loadSchema() {
  const source = await readFile(SCHEMA_PATH);
  let schema;
  try {
    schema = JSON.parse(source.toString('utf8'));
  } catch {
    fail();
  }
  assertSchemaContract(schema);
  return schema;
}

function matchesType(value, type) {
  switch (type) {
    case 'null': return value === null;
    case 'object': return value !== null && typeof value === 'object' && !Array.isArray(value);
    case 'array': return Array.isArray(value);
    case 'string': return typeof value === 'string';
    case 'number': return typeof value === 'number' && Number.isFinite(value);
    case 'integer': return Number.isInteger(value);
    case 'boolean': return typeof value === 'boolean';
    default: return false;
  }
}

function validateAgainstSchema(value, schema) {
  if (schema.const !== undefined && value !== schema.const) fail();
  if (schema.enum && !schema.enum.includes(value)) fail();

  if (schema.type) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!types.some((type) => matchesType(value, type))) fail();
  }

  if (schema.type === 'object') {
    for (const required of schema.required ?? []) {
      if (!Object.hasOwn(value, required)) fail();
    }
    if (schema.additionalProperties === false) {
      const allowed = new Set(Object.keys(schema.properties ?? {}));
      if (Object.keys(value).some((key) => !allowed.has(key))) fail();
    }
    for (const [key, propertySchema] of Object.entries(schema.properties ?? {})) {
      if (Object.hasOwn(value, key)) validateAgainstSchema(value[key], propertySchema);
    }
  }

  if (schema.type === 'array') {
    for (const item of value) validateAgainstSchema(item, schema.items);
  }
}

const DATE_TIME_PATTERN = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?(Z|([+-])(\d{2}):(\d{2}))$/;

function isValidDateTime(value) {
  if (typeof value !== 'string' || value.length > 40) return false;
  const match = DATE_TIME_PATTERN.exec(value);
  if (!match) return false;

  const [, yearText, monthText, dayText, hourText, minuteText, secondText, , zone, , offsetHourText, offsetMinuteText] = match;
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  const hour = Number(hourText);
  const minute = Number(minuteText);
  const second = Number(secondText);
  const offsetHour = offsetHourText === undefined ? 0 : Number(offsetHourText);
  const offsetMinute = offsetMinuteText === undefined ? 0 : Number(offsetMinuteText);
  if (year < 1 || month < 1 || month > 12 || hour > 23 || minute > 59 || second > 59) return false;
  if (offsetHour > 23 || offsetMinute > 59) return false;

  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const monthDays = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (day < 1 || day > monthDays[month - 1]) return false;
  return zone === 'Z' ? Number.isFinite(Date.parse(value)) : Number.isFinite(Date.parse(value));
}

function assertText(value, maxBytes, { nonEmpty = false } = {}) {
  if (typeof value !== 'string') fail();
  if (Buffer.byteLength(value, 'utf8') > maxBytes) fail();
  if (/\p{Cc}/u.test(value)) fail();
  if (nonEmpty && value.trim().length === 0) fail();
}

function assertDateTime(value) {
  if (!isValidDateTime(value)) fail();
}

function assertLink(value, { nullable = false } = {}) {
  if (nullable && value === null) return;
  assertText(value, 1024, { nonEmpty: true });
  if (getSafeThreadHref(value) === null) fail();
}

export function validateProjectionText(source, schema) {
  const bytes = Buffer.isBuffer(source) ? source : Buffer.from(source);
  if (bytes.byteLength > MAX_PROJECTION_BYTES) fail();

  let projection;
  try {
    projection = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
  } catch {
    fail();
  }

  validateAgainstSchema(projection, schema);
  assertDateTime(projection.generatedAt);
  assertLink(projection.chief.link);
  if (projection.assignments.length > MAX_ASSIGNMENTS) fail();

  const ids = new Set();
  for (const assignment of projection.assignments) {
    assertText(assignment.assignmentId, 128, { nonEmpty: true });
    if (!/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(assignment.assignmentId)) fail();
    if (ids.has(assignment.assignmentId)) fail();
    ids.add(assignment.assignmentId);

    assertText(assignment.title, 200, { nonEmpty: true });
    assertText(assignment.phase, 128, { nonEmpty: true });
    assertText(assignment.summary, 2000, { nonEmpty: true });
    if (assignment.lastReportedAt !== null) assertDateTime(assignment.lastReportedAt);
    assertLink(assignment.coordinatorLink, { nullable: true });
    if (assignment.blocker !== null) assertText(assignment.blocker, 1000, { nonEmpty: true });
    if (assignment.decisionNeeded !== null) assertText(assignment.decisionNeeded, 1000, { nonEmpty: true });
    if (assignment.testedRevision !== null) assertText(assignment.testedRevision, 128, { nonEmpty: true });
  }
  return projection;
}

function securityHeaders(contentType) {
  return {
    'Content-Type': contentType,
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'no-referrer',
    'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
  };
}

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, securityHeaders('application/json; charset=utf-8'));
  response.end(JSON.stringify(payload));
}

function sendText(response, statusCode, message) {
  response.writeHead(statusCode, securityHeaders('text/plain; charset=utf-8'));
  response.end(message);
}

class RequestError extends Error {
  constructor(statusCode, message) {
    super(message);
    this.statusCode = statusCode;
  }
}

function hasExactKeys(value, expected) {
  return value !== null
    && typeof value === 'object'
    && !Array.isArray(value)
    && Object.keys(value).length === expected.length
    && expected.every((key) => Object.hasOwn(value, key));
}

function isAllowedSubmissionText(value) {
  if (typeof value !== 'string' || value.trim().length === 0) return false;
  let codePoints = 0;
  for (const character of value) {
    const point = character.codePointAt(0);
    if ((point >= 0xd800 && point <= 0xdfff) || (point < 0x20 && point !== 0x09 && point !== 0x0a) || (point >= 0x7f && point <= 0x9f)) return false;
  }
  codePoints = Array.from(value.trim()).length;
  return codePoints <= MAX_MESSAGE_CODEPOINTS
    && Buffer.byteLength(value, 'utf8') <= MAX_REQUEST_BYTES;
}

async function readJsonBody(request) {
  const contentType = request.headers['content-type'];
  if (typeof contentType !== 'string' || contentType.split(';', 1)[0].trim().toLowerCase() !== 'application/json') {
    throw new RequestError(415, 'JSON required.');
  }

  const declaredLength = request.headers['content-length'];
  if (declaredLength !== undefined) {
    if (!/^\d+$/.test(declaredLength)) throw new RequestError(400, 'Invalid request.');
    if (Number(declaredLength) > MAX_REQUEST_BYTES) throw new RequestError(413, 'Request too large.');
  }

  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > MAX_REQUEST_BYTES) {
      request.resume();
      throw new RequestError(413, 'Request too large.');
    }
    chunks.push(chunk);
  }

  let value;
  try {
    value = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks)));
  } catch {
    throw new RequestError(400, 'Invalid request.');
  }
  if (value === null || typeof value !== 'object' || Array.isArray(value)) throw new RequestError(400, 'Invalid request.');
  return value;
}

function validateJournalRecord(record) {
  const keys = ['submissionId', 'state', 'attempt', 'createdAt', 'updatedAt', 'text', 'reason', 'rawReceipt'];
  if (!hasExactKeys(record, keys)) fail();
  if (typeof record.submissionId !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(record.submissionId)) fail();
  if (!SUBMISSION_STATES.includes(record.state)) fail();
  if (!Number.isInteger(record.attempt) || record.attempt < 1 || record.attempt > 1000) fail();
  if (!isValidDateTime(record.createdAt) || !isValidDateTime(record.updatedAt)) fail();
  if (!isAllowedSubmissionText(record.text)) fail();
  if (record.reason !== null && !['target-mismatch', 'preflight-failed', 'spawn-failed', 'ambiguous-delivery', 'receipt-invalid', 'interrupted', 'journal-write-failed', 'found-in-recent-messages', 'not-found-in-recent-messages'].includes(record.reason)) fail();
  if (record.rawReceipt !== null && (typeof record.rawReceipt !== 'string' || Buffer.byteLength(record.rawReceipt, 'utf8') > MAX_CLI_OUTPUT_BYTES)) fail();
  return record;
}

function createFileSubmissionStore() {
  return {
    async load() {
      try {
        const details = await lstat(JOURNAL_PATH);
        if (!details.isFile() || details.isSymbolicLink() || details.uid !== process.getuid()) fail();
        const parsed = JSON.parse((await readFile(JOURNAL_PATH)).toString('utf8'));
        if (!Array.isArray(parsed) || parsed.length > MAX_JOURNAL_RECORDS) fail();
        return parsed.map(validateJournalRecord);
      } catch (error) {
        if (error?.code === 'ENOENT') return [];
        throw error;
      }
    },
    async save(records) {
      if (!Array.isArray(records) || records.length > MAX_JOURNAL_RECORDS) fail();
      records.forEach(validateJournalRecord);
      const temporaryPath = JOURNAL_PATH + '.tmp-' + randomUUID();
      const handle = await open(temporaryPath, 'wx', 0o600);
      try {
        await handle.writeFile(JSON.stringify(records), 'utf8');
        await handle.sync();
      } finally {
        await handle.close();
      }
      try {
        await rename(temporaryPath, JOURNAL_PATH);
      } catch (error) {
        await unlink(temporaryPath).catch(() => {});
        throw error;
      }
    },
  };
}

async function loadJournalRecoveringInterrupted(store) {
  const records = await store.load();
  if (!Array.isArray(records) || records.length > MAX_JOURNAL_RECORDS) fail();
  records.forEach(validateJournalRecord);
  let changed = false;
  const now = new Date().toISOString();
  for (const record of records) {
    if (record.state === 'pending') {
      record.state = 'unknown';
      record.reason = 'interrupted';
      record.updatedAt = now;
      changed = true;
    }
  }
  if (changed) await store.save(records);
  return records;
}

function runT3(args, { input, timeout }) {
  return new Promise((resolve) => {
    let spawned = false;
    let stdinError = null;
    const child = execFile(T3_CLI_PATH, args, {
      env: { ...process.env, T3CODE_HOME },
      timeout,
      maxBuffer: MAX_CLI_OUTPUT_BYTES,
      encoding: 'utf8',
      windowsHide: true,
    }, (error, stdout, stderr) => {
      resolve({ spawned, error: error ?? stdinError, stdout: stdout ?? '', stderr: stderr ?? '' });
    });
    child.once('spawn', () => { spawned = true; });
    child.once('error', () => {});
    child.stdin.on('error', (error) => { stdinError = error; });
    if (input === undefined) child.stdin.end();
    else child.stdin.end(input, 'utf8');
  });
}

function isFixedChief(thread) {
  if (!thread || thread.threadId !== FIXED_THREAD_ID || typeof thread.link !== 'string') return false;
  try {
    const link = new URL(thread.link);
    return link.protocol === 'http:'
      && link.hostname === '127.0.0.1'
      && /^\d+$/.test(link.port)
      && link.pathname === '/' + FIXED_ENVIRONMENT_ID + '/' + FIXED_THREAD_ID
      && link.search === ''
      && link.hash === '';
  } catch {
    return false;
  }
}

async function preflightFixedChief() {
  const result = await runT3(['thread', 'show', '--json', '--messages', '0', FIXED_THREAD_ID], { timeout: 10_000 });
  if (!result.spawned || result.error) return { ok: false, reason: 'preflight-failed' };
  let payload;
  try {
    payload = JSON.parse(result.stdout);
  } catch {
    return { ok: false, reason: 'preflight-failed' };
  }
  if (!isFixedChief(payload.thread) || !Array.isArray(payload.messages) || payload.messages.length !== 0) {
    return { ok: false, reason: 'target-mismatch' };
  }
  return { ok: true };
}

async function sendFixedChiefMessage(envelope) {
  return runT3(['thread', 'send', '--json', FIXED_THREAD_ID, '-'], { input: envelope, timeout: 30_000 });
}

async function reconcileFixedChiefMessage(submissionId) {
  const result = await runT3(['thread', 'show', '--json', '--messages', '20', FIXED_THREAD_ID], { timeout: 10_000 });
  if (!result.spawned || result.error) return { ok: false, reason: 'preflight-failed' };
  let payload;
  try {
    payload = JSON.parse(result.stdout);
  } catch {
    return { ok: false, reason: 'preflight-failed' };
  }
  if (!isFixedChief(payload.thread) || !Array.isArray(payload.messages)) return { ok: false, reason: 'target-mismatch' };
  return { ok: true, found: JSON.stringify(payload.messages).includes(submissionId) };
}

function submissionEnvelope(record) {
  const header = '[Cortex Status Board submission — untrusted local-human board submission.\n'
    + 'source: local Cortex Status Board; submissionId: ' + record.submissionId
    + '; attempt: ' + record.attempt
    + '; intendedThreadId: ' + FIXED_THREAD_ID
    + '; intendedEnvironmentId: ' + FIXED_ENVIRONMENT_ID
    + '; boardTime: ' + new Date().toISOString() + '.\n'
    + 'Not authenticated human authority and not an approval. Text after the delimiter is preserved verbatim.]\n---\n';
  return header + record.text;
}

export function createBoardServer({
  schema,
  readProjection = () => readFile(PROJECTION_PATH),
  identityToken = SOURCE_IDENTITY_TOKEN,
  submissionStore = createFileSubmissionStore(),
  bridge = {
    preflight: preflightFixedChief,
    send: sendFixedChiefMessage,
    reconcile: reconcileFixedChiefMessage,
  },
}) {
  assertSchemaContract(schema);
  if (typeof identityToken !== 'string' || !/^[A-Za-z0-9-]{1,128}$/.test(identityToken)) fail();
  let operationInFlight = false;
  const composerRoutes = new Set(['/api/reply', '/api/reply/retry', '/api/reply/recover', '/api/reply/reconcile']);

  function composerRequestAllowed(request) {
    const port = request.socket.localPort;
    const expectedHost = HOST + ':' + port;
    const expectedOrigin = 'http://' + expectedHost;
    const origin = request.headers.origin;
    return request.headers.host === expectedHost
      && origin === expectedOrigin
      && request.headers['x-cortex-board'] === '1';
  }

  async function persistOutcome(response, records, record) {
    record.updatedAt = new Date().toISOString();
    try {
      await submissionStore.save(records);
      sendJson(response, 200, {
        submissionId: record.submissionId,
        state: record.state,
        attempt: record.attempt,
        reason: record.reason,
      });
    } catch {
      record.state = 'unknown';
      record.reason = 'journal-write-failed';
      sendJson(response, 503, {
        submissionId: record.submissionId,
        state: 'unknown',
        attempt: record.attempt,
        reason: 'journal-write-failed',
        error: 'Submission state could not be saved. Check before any retry.',
      });
    }
  }

  async function runSubmission(response, records, record) {
    let preflight;
    try {
      preflight = await bridge.preflight();
    } catch {
      preflight = { ok: false, reason: 'preflight-failed' };
    }
    if (!preflight?.ok) {
      record.state = 'not-sent';
      record.reason = preflight?.reason === 'target-mismatch' ? 'target-mismatch' : 'preflight-failed';
      await persistOutcome(response, records, record);
      return;
    }

    let result;
    try {
      result = await bridge.send(submissionEnvelope(record));
    } catch {
      result = { spawned: true, error: new Error('ambiguous send'), stdout: '' };
    }
    record.rawReceipt = typeof result?.stdout === 'string'
      ? result.stdout.slice(0, MAX_CLI_OUTPUT_BYTES)
      : '';
    if (!result?.spawned) {
      record.state = 'not-sent';
      record.reason = 'spawn-failed';
    } else if (result.error) {
      record.state = 'unknown';
      record.reason = 'ambiguous-delivery';
    } else {
      let receipt;
      try {
        receipt = JSON.parse(record.rawReceipt);
      } catch {
        receipt = null;
      }
      if (receipt?.threadId === FIXED_THREAD_ID) {
        record.state = 'sent';
        record.reason = null;
      } else {
        record.state = 'unknown';
        record.reason = 'receipt-invalid';
      }
    }
    await persistOutcome(response, records, record);
  }

  return createHttpServer(async (request, response) => {
    let route;
    try {
      const url = new URL(request.url ?? '/', 'http://127.0.0.1');
      route = url.search === '' ? url.pathname : null;
    } catch {
      route = null;
    }

    if (composerRoutes.has(route)) {
      if (request.method !== 'POST') {
        response.setHeader('Allow', 'POST');
        sendText(response, 405, 'Method not allowed.');
        return;
      }
      if (!composerRequestAllowed(request)) {
        request.resume();
        sendJson(response, 403, { error: 'Local submission request rejected.' });
        return;
      }
      if (operationInFlight) {
        request.resume();
        sendJson(response, 409, { error: 'Another local submission operation is in progress.' });
        return;
      }

      operationInFlight = true;
      try {
        const body = await readJsonBody(request);
        const records = await loadJournalRecoveringInterrupted(submissionStore);

        if (route === '/api/reply/recover') {
          if (!hasExactKeys(body, [])) {
            sendJson(response, 400, { error: 'Invalid request.' });
            return;
          }
          const record = records.at(-1);
          if (!record) {
            sendJson(response, 200, { state: 'none' });
            return;
          }
          sendJson(response, 200, {
            submissionId: record.submissionId,
            state: record.state,
            attempt: record.attempt,
            reason: record.reason,
            text: record.text,
          });
          return;
        }

        if (route === '/api/reply') {
          if (!hasExactKeys(body, ['text']) || !isAllowedSubmissionText(body.text)) {
            sendJson(response, 400, { error: 'Message text is invalid.' });
            return;
          }
          const latest = records.at(-1);
          if (latest && ['pending', 'unknown', 'not-sent'].includes(latest.state)) {
            sendJson(response, 409, { error: 'Recover or reconcile the previous submission before starting another.' });
            return;
          }
          if (records.length >= MAX_JOURNAL_RECORDS) {
            sendJson(response, 507, { error: 'The local submission journal is full.' });
            return;
          }
          const now = new Date().toISOString();
          const record = {
            submissionId: randomUUID(),
            state: 'pending',
            attempt: 1,
            createdAt: now,
            updatedAt: now,
            text: body.text,
            reason: null,
            rawReceipt: null,
          };
          records.push(record);
          try {
            await submissionStore.save(records);
          } catch {
            sendJson(response, 503, { error: 'Draft could not be saved; nothing was sent.' });
            return;
          }
          await runSubmission(response, records, record);
          return;
        }

        if (route === '/api/reply/retry') {
          if (!hasExactKeys(body, ['submissionId']) || typeof body.submissionId !== 'string') {
            sendJson(response, 400, { error: 'Invalid request.' });
            return;
          }
          const record = records.find((item) => item.submissionId === body.submissionId);
          if (!record || record.state !== 'not-sent') {
            sendJson(response, 409, { error: 'Only a known unsent submission can be retried.' });
            return;
          }
          if (records.some((item) => item !== record && ['pending', 'unknown'].includes(item.state))) {
            sendJson(response, 409, { error: 'Another submission needs reconciliation.' });
            return;
          }
          record.state = 'pending';
          record.reason = null;
          record.attempt += 1;
          try {
            await submissionStore.save(records);
          } catch {
            record.state = 'not-sent';
            record.reason = 'journal-write-failed';
            sendJson(response, 503, { error: 'Retry was not started because its journal could not be saved.' });
            return;
          }
          await runSubmission(response, records, record);
          return;
        }

        if (!hasExactKeys(body, ['submissionId']) || typeof body.submissionId !== 'string') {
          sendJson(response, 400, { error: 'Invalid request.' });
          return;
        }
        const record = records.find((item) => item.submissionId === body.submissionId);
        if (!record || record.state !== 'unknown') {
          sendJson(response, 409, { error: 'Only an uncertain submission can be reconciled.' });
          return;
        }
        let reconciliation;
        try {
          reconciliation = await bridge.reconcile(record.submissionId);
        } catch {
          reconciliation = { ok: false, reason: 'preflight-failed' };
        }
        if (reconciliation?.ok && reconciliation.found) {
          record.state = 'sent';
          record.reason = 'found-in-recent-messages';
        } else {
          record.state = 'unknown';
          record.reason = reconciliation?.reason === 'target-mismatch'
            ? 'target-mismatch'
            : reconciliation?.reason === 'preflight-failed'
              ? 'preflight-failed'
              : 'not-found-in-recent-messages';
        }
        await persistOutcome(response, records, record);
      } catch (error) {
        if (error instanceof RequestError) sendJson(response, error.statusCode, { error: error.message });
        else sendJson(response, 503, { error: 'Local submission service is unavailable.' });
      } finally {
        operationInFlight = false;
      }
      return;
    }

    if (request.method !== 'GET') {
      response.setHeader('Allow', 'GET');
      sendText(response, 405, 'Method not allowed.');
      return;
    }

    if (route === '/api/health') {
      sendJson(response, 200, {
        serviceId: SERVICE_ID,
        assignmentId: ASSIGNMENT_ID,
        protocolVersion: PROTOCOL_VERSION,
        identityToken,
      });
      return;
    }

    if (route === '/api/status') {
      try {
        const source = await readProjection();
        validateProjectionText(source, schema);
        response.writeHead(200, securityHeaders('application/json; charset=utf-8'));
        response.end(source);
      } catch {
        sendJson(response, 503, { error: 'Status snapshot is unavailable or invalid.' });
      }
      return;
    }

    const asset = route ? PUBLIC_ASSETS.get(route) : undefined;
    if (!asset) {
      sendJson(response, 404, { error: 'Not found.' });
      return;
    }

    try {
      const assetUrl = new URL('./public/' + asset[0], import.meta.url);
      const bytes = await readFile(fileURLToPath(assetUrl));
      response.writeHead(200, securityHeaders(asset[1]));
      response.end(bytes);
    } catch {
      sendJson(response, 500, { error: 'Board asset is unavailable.' });
    }
  });
}

export async function startBoard() {
  const schema = await loadSchema();
  const identityPath = fileURLToPath(new URL('./server.identity', import.meta.url));
  let identityToken = SOURCE_IDENTITY_TOKEN;
  try {
    identityToken = (await readFile(identityPath, 'utf8')).trim();
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }
  const server = createBoardServer({ schema, identityToken });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(PORT, HOST, resolve);
  });
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('Listener unavailable');
  process.stdout.write(`Cortex status board: http://${HOST}:${address.port}\n`);
  return server;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  startBoard().catch(() => {
    process.stderr.write('Unable to start the local status board.\n');
    process.exitCode = 1;
  });
}
