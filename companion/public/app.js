import { formatLastReportedAt, getSafeThreadHref, isSnapshotStale } from '/status-view.js';

const refreshButton = document.querySelector('#refreshButton');
const message = document.querySelector('#message');
const snapshotInfo = document.querySelector('#snapshotInfo');
const chiefLink = document.querySelector('#chiefLink');
const board = document.querySelector('#board');

const SECTION_DEFINITIONS = [
  { title: 'Needs you / Blocked', statuses: new Set(['needs-you', 'blocked']) },
  { title: 'Ready for review', statuses: new Set(['ready-for-review']) },
  { title: 'Working', statuses: new Set(['working']) },
  { title: 'Unknown', statuses: new Set(['unknown']) },
];

function addTextElement(parent, tagName, className, text) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  element.textContent = text;
  parent.append(element);
  return element;
}

function createAssignmentCard(assignment) {
  const card = document.createElement('article');
  card.className = 'assignment-card';

  const heading = document.createElement('div');
  heading.className = 'card-heading';
  addTextElement(heading, 'span', 'assignment-id', assignment.assignmentId);
  addTextElement(heading, 'h3', '', assignment.title);
  addTextElement(heading, 'span', 'status-pill', assignment.status);
  card.append(heading);
  addTextElement(card, 'p', 'summary', assignment.summary);

  const metadata = document.createElement('dl');
  metadata.className = 'metadata';
  addTextElement(metadata, 'dt', '', 'Last reported');
  addTextElement(metadata, 'dd', '', formatLastReportedAt(assignment.lastReportedAt));
  addTextElement(metadata, 'dt', '', 'Phase');
  addTextElement(metadata, 'dd', '', assignment.phase);
  addTextElement(metadata, 'dt', '', 'Coordinator');
  const coordinatorValue = document.createElement('dd');
  const href = getSafeThreadHref(assignment.coordinatorLink);
  if (href) {
    const link = document.createElement('a');
    link.href = href;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = assignment.coordinatorLink;
    coordinatorValue.append(link);
  } else {
    coordinatorValue.textContent = assignment.coordinatorLink === null ? 'Unknown' : 'Unavailable';
  }
  metadata.append(coordinatorValue);

  if (assignment.blocker !== null) {
    addTextElement(metadata, 'dt', '', 'Blocker');
    addTextElement(metadata, 'dd', '', assignment.blocker);
  }
  if (assignment.decisionNeeded !== null) {
    addTextElement(metadata, 'dt', '', 'Decision needed');
    addTextElement(metadata, 'dd', '', assignment.decisionNeeded);
  }
  card.append(metadata);
  return card;
}

function createSection(title, assignments) {
  const section = document.createElement('section');
  section.className = 'status-section';
  section.setAttribute('aria-label', title);
  const heading = document.createElement('div');
  heading.className = 'section-heading';
  addTextElement(heading, 'h2', '', title);
  addTextElement(heading, 'span', 'count', `${assignments.length} ${assignments.length === 1 ? 'assignment' : 'assignments'}`);
  section.append(heading);

  if (assignments.length === 0) {
    addTextElement(section, 'p', 'empty', 'No assignments in this group.');
    return section;
  }

  const list = document.createElement('div');
  list.className = 'card-list';
  assignments.forEach((assignment) => list.append(createAssignmentCard(assignment)));
  section.append(list);
  return section;
}

function renderProjection(projection) {
  board.replaceChildren();
  chiefLink.replaceChildren();
  snapshotInfo.classList.remove('stale');

  const generatedAt = projection.generatedAt;
  if (isSnapshotStale(generatedAt)) {
    snapshotInfo.classList.add('stale');
    snapshotInfo.textContent = `Snapshot is more than 30 minutes old. Generated at ${generatedAt}.`;
  } else {
    snapshotInfo.textContent = `Snapshot generated at ${generatedAt}. Snapshot age is informational only.`;
  }

  const chiefHref = getSafeThreadHref(projection.chief.link);
  if (chiefHref) {
    const link = document.createElement('a');
    link.href = chiefHref;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = 'Open Cortex chief';
    chiefLink.append(link);
  }

  for (const sectionDefinition of SECTION_DEFINITIONS) {
    const assignments = projection.assignments.filter((assignment) => sectionDefinition.statuses.has(assignment.status));
    board.append(createSection(sectionDefinition.title, assignments));
  }

  const doneAssignments = projection.assignments.filter((assignment) => assignment.status === 'done');
  const done = document.createElement('details');
  done.className = 'done-section';
  const doneSummary = document.createElement('summary');
  doneSummary.textContent = `Done (${doneAssignments.length})`;
  done.append(doneSummary);
  if (doneAssignments.length === 0) {
    addTextElement(done, 'p', 'empty', 'No completed assignments.');
  } else {
    const list = document.createElement('div');
    list.className = 'card-list';
    doneAssignments.forEach((assignment) => list.append(createAssignmentCard(assignment)));
    done.append(list);
  }
  board.append(done);
}

async function refresh() {
  refreshButton.disabled = true;
  message.textContent = 'Reading status snapshot…';
  try {
    const response = await fetch('/api/status', {
      method: 'GET',
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    });
    if (!response.ok) throw new Error('unavailable');
    const projection = await response.json();
    renderProjection(projection);
    message.textContent = `Loaded ${projection.assignments.length} assignments.`;
  } catch {
    message.textContent = 'Could not load the status snapshot. Select Refresh snapshot to try again.';
  } finally {
    refreshButton.disabled = false;
  }
}

refreshButton.addEventListener('click', refresh);

const replyForm = document.querySelector('#replyForm');
const replyText = document.querySelector('#replyText');
const sendReplyButton = document.querySelector('#sendReplyButton');
const retryReplyButton = document.querySelector('#retryReplyButton');
const reconcileReplyButton = document.querySelector('#reconcileReplyButton');
const recoverReplyButton = document.querySelector('#recoverReplyButton');
const replyMessage = document.querySelector('#replyMessage');
const LOCAL_SUBMISSION_KEY = 'cortex-status-board-c004-submission-v1';
const LOCAL_STATES = new Set(['draft', 'pending', 'sent', 'unknown', 'not-sent']);
let replyBusy = false;

function emptyReplyRecord(text = '') {
  return { text, submissionId: null, state: 'draft', attempt: 0, reason: null };
}

function loadReplyRecord() {
  try {
    const value = JSON.parse(localStorage.getItem(LOCAL_SUBMISSION_KEY) ?? 'null');
    if (
      value
      && typeof value === 'object'
      && typeof value.text === 'string'
      && LOCAL_STATES.has(value.state)
      && (value.submissionId === null || typeof value.submissionId === 'string')
      && Number.isInteger(value.attempt)
    ) {
      return value;
    }
  } catch {
    // A damaged local draft stays untouched; the user can recover from the local journal.
  }
  return emptyReplyRecord();
}

let replyRecord = loadReplyRecord();
replyText.value = replyRecord.state === 'sent' ? '' : replyRecord.text;

function saveReplyRecord() {
  try {
    localStorage.setItem(LOCAL_SUBMISSION_KEY, JSON.stringify(replyRecord));
    return true;
  } catch {
    replyMessage.textContent = 'The browser could not save this draft locally. Keep this page open until its state is resolved.';
    return false;
  }
}

function renderReplyControls() {
  const locked = ['pending', 'unknown', 'not-sent'].includes(replyRecord.state);
  replyText.disabled = replyBusy || locked;
  sendReplyButton.disabled = replyBusy || locked || replyText.value.trim().length === 0;
  retryReplyButton.hidden = replyRecord.state !== 'not-sent';
  reconcileReplyButton.hidden = replyRecord.state !== 'unknown' || !replyRecord.submissionId;
  recoverReplyButton.disabled = replyBusy;
}

function describeReplyResult(record) {
  if (record.state === 'sent') {
    return 'The fixed CLI receipt matched the chief thread. T3 may label message provenance as agent/MCP; this is not authenticated human provenance.';
  }
  if (record.state === 'not-sent' && record.reason === 'target-mismatch') {
    return 'No message was sent. The live chief environment did not match the fixed target. The text and submission ID are preserved.';
  }
  if (record.state === 'not-sent') {
    return 'No message was sent. The text and submission ID are preserved; retry uses the same ID after an explicit click.';
  }
  if (record.state === 'unknown') {
    return 'This attempt may have arrived. Do not resend it. Use Check recent chief messages to reconcile the same ID.';
  }
  if (record.state === 'pending') return 'Checking the fixed chief and submission receipt…';
  return 'Drafts stay on this Mac. No message is sent until you select a button.';
}

function acceptReplyResult(result) {
  replyRecord = {
    text: typeof result.text === 'string' ? result.text : replyRecord.text,
    submissionId: result.submissionId ?? null,
    state: result.state,
    attempt: Number.isInteger(result.attempt) ? result.attempt : replyRecord.attempt,
    reason: result.reason ?? null,
  };
  saveReplyRecord();
  if (replyRecord.state === 'sent') replyText.value = '';
  replyMessage.textContent = describeReplyResult(replyRecord);
  renderReplyControls();
}

async function postReplyRoute(path, payload) {
  return fetch(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Cortex-Board': '1',
    },
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
}

replyText.addEventListener('input', () => {
  if (replyRecord.state === 'sent' && replyText.value !== replyRecord.text) {
    replyRecord = emptyReplyRecord(replyText.value);
  } else if (replyRecord.state === 'draft') {
    replyRecord.text = replyText.value;
  }
  saveReplyRecord();
  renderReplyControls();
});

replyForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (replyBusy || ['pending', 'unknown', 'not-sent'].includes(replyRecord.state)) return;
  const text = replyText.value;
  if (!text.trim()) {
    replyMessage.textContent = 'Enter a message before sending.';
    return;
  }
  replyBusy = true;
  replyRecord = { ...emptyReplyRecord(text), state: 'pending' };
  saveReplyRecord();
  replyMessage.textContent = 'Verifying the fixed chief target before any send…';
  renderReplyControls();
  try {
    const response = await postReplyRoute('/api/reply', { text });
    const result = await response.json();
    if (typeof result.submissionId === 'string' && LOCAL_STATES.has(result.state)) {
      acceptReplyResult(result);
    } else if (response.status >= 500) {
      replyRecord = { ...replyRecord, state: 'unknown', reason: 'response-unavailable' };
      saveReplyRecord();
      replyMessage.textContent = 'The server did not return a safe receipt. This attempt may have arrived; recover its ID before taking any next step.';
    } else {
      replyRecord = emptyReplyRecord(text);
      saveReplyRecord();
      replyMessage.textContent = typeof result.error === 'string' ? result.error : 'The request was rejected before sending.';
    }
  } catch {
    replyRecord = { ...replyRecord, state: 'unknown', reason: 'network-uncertain' };
    saveReplyRecord();
    replyMessage.textContent = 'The connection ended without a receipt. This attempt may have arrived; recover its ID before taking any next step.';
  } finally {
    replyBusy = false;
    renderReplyControls();
  }
});

retryReplyButton.addEventListener('click', async () => {
  if (replyBusy || replyRecord.state !== 'not-sent' || !replyRecord.submissionId) return;
  replyBusy = true;
  replyMessage.textContent = 'Retrying this known-unsent draft with the same submission ID…';
  renderReplyControls();
  try {
    const response = await postReplyRoute('/api/reply/retry', { submissionId: replyRecord.submissionId });
    const result = await response.json();
    if (typeof result.submissionId === 'string' && LOCAL_STATES.has(result.state)) acceptReplyResult(result);
    else replyMessage.textContent = 'Retry was rejected. The draft and submission ID remain saved.';
  } catch {
    replyRecord = { ...replyRecord, state: 'unknown', reason: 'network-uncertain' };
    saveReplyRecord();
    replyMessage.textContent = describeReplyResult(replyRecord);
  } finally {
    replyBusy = false;
    renderReplyControls();
  }
});

reconcileReplyButton.addEventListener('click', async () => {
  if (replyBusy || replyRecord.state !== 'unknown' || !replyRecord.submissionId) return;
  replyBusy = true;
  replyMessage.textContent = 'Checking the fixed chief’s 20 latest messages for this ID. Nothing will be resent.';
  renderReplyControls();
  try {
    const response = await postReplyRoute('/api/reply/reconcile', { submissionId: replyRecord.submissionId });
    const result = await response.json();
    if (result.state === 'sent' || result.state === 'unknown') acceptReplyResult(result);
    else replyMessage.textContent = 'The status could not be reconciled. The draft and ID remain saved.';
  } catch {
    replyMessage.textContent = 'The status check failed. The draft and ID remain saved; no retry was made.';
  } finally {
    replyBusy = false;
    renderReplyControls();
  }
});

recoverReplyButton.addEventListener('click', async () => {
  if (replyBusy) return;
  replyBusy = true;
  replyMessage.textContent = 'Reading the local submission journal…';
  renderReplyControls();
  try {
    const response = await postReplyRoute('/api/reply/recover', {});
    const result = await response.json();
    if (result.state === 'none') {
      if (replyRecord.state === 'unknown' && !replyRecord.submissionId) {
        const text = replyText.value || replyRecord.text;
        replyRecord = emptyReplyRecord(text);
        saveReplyRecord();
        replyMessage.textContent = 'No local submission record exists, so the draft was not sent. The text is ready to submit again.';
      } else {
        replyMessage.textContent = 'There is no prior local submission to recover.';
      }
      return;
    }
    if (typeof result.submissionId !== 'string' || !LOCAL_STATES.has(result.state) || typeof result.text !== 'string') {
      replyMessage.textContent = 'The local journal response was invalid. The current draft was kept.';
      return;
    }
    const existingText = replyText.value || replyRecord.text;
    if (existingText && existingText !== result.text && replyRecord.submissionId !== result.submissionId) {
      replyMessage.textContent = 'A different prior submission exists in the local journal. Your current draft was kept.';
      return;
    }
    acceptReplyResult(result);
    if (result.state !== 'sent') replyText.value = result.text;
  } catch {
    replyMessage.textContent = 'The local journal could not be read. Your current draft was kept.';
  } finally {
    replyBusy = false;
    renderReplyControls();
  }
});

replyMessage.textContent = describeReplyResult(replyRecord);
renderReplyControls();
