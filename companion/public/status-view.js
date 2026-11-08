const THREAD_LINK_PREFIX = 't3-thread://v2/';
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const SAFE_THREAD_SEGMENT = /^[A-Za-z0-9._~:-]{1,256}$/;
const SAFE_ENCODED_SEGMENT = /^(?:[A-Za-z0-9._~:-]|%[0-9a-f]{2}){1,768}$/i;

export function getSafeThreadHref(value) {
  if (typeof value !== 'string' || value.length === 0 || value.length > 1024) return null;
  const wrapped = value.startsWith('<') && value.endsWith('>');
  if ((value.startsWith('<') || value.endsWith('>')) && !wrapped) return null;
  const href = wrapped ? value.slice(1, -1) : value;
  if (!href.startsWith(THREAD_LINK_PREFIX)) return null;

  const path = href.slice(THREAD_LINK_PREFIX.length);
  const slash = path.indexOf('/');
  if (slash < 0 || path.indexOf('/', slash + 1) !== -1) return null;
  const environment = path.slice(0, slash);
  const encodedThreadId = path.slice(slash + 1);
  if (!UUID_PATTERN.test(environment) || !SAFE_ENCODED_SEGMENT.test(encodedThreadId)) return null;

  let threadId;
  try {
    threadId = decodeURIComponent(encodedThreadId);
  } catch {
    return null;
  }
  if (!SAFE_THREAD_SEGMENT.test(threadId) || threadId === '.' || threadId === '..') return null;
  return href;
}

export function isSnapshotStale(generatedAt, now = Date.now()) {
  const generatedTime = Date.parse(generatedAt);
  return Number.isFinite(generatedTime) && now - generatedTime > 30 * 60 * 1000;
}

export function formatLastReportedAt(value) {
  return value === null ? 'Unknown' : value;
}
