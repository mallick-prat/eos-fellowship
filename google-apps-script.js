/**
 * Eos Fellowship applications -> Google Sheet, plus an emailed copy to each applicant.
 *
 * Set this up while signed in as mallickprat@gmail.com: confirmation emails are sent
 * from whichever Google account owns the script.
 *
 * Setup:
 * 1. Create a Google Sheet (e.g. "Eos Fellowship Applications").
 * 2. In the sheet: Extensions > Apps Script. Replace everything in Code.gs with this file. Save.
 * 3. Deploy > New deployment > type "Web app".
 *      Execute as: Me
 *      Who has access: Anyone
 *    Click Deploy and approve the permissions prompt (Sheets + send email as you).
 * 4. Copy the Web app URL (it ends in /exec) into SHEET_ENDPOINT in the site's apply.html.
 *
 * If you edit this script later, use Deploy > Manage deployments > Edit > New version,
 * so the /exec URL stays the same.
 *
 * Gmail limit: a personal Gmail account can send about 100 of these emails a day.
 * Past that, applications still save to the sheet; only the copy email is skipped.
 */

const SHEET_NAME = 'Applications';
const FROM_NAME = 'Eos Fellowship';

const COLUMNS = [
  ['submitted', 'Submitted'],
  ['name', 'Name'],
  ['school', 'School'],
  ['level', 'G/UG'],
  ['degree', 'Degree'],
  ['year', 'Year'],
  ['email', 'Email'],
  ['phone', 'Phone'],
  ['linkedin', 'LinkedIn'],
  ['subject', 'A subject you know more about than anyone else'],
  ['pick', 'Company or person to join or invest in'],
  ['goals', 'Goals for 3-5 years from now'],
  ['peer', 'Peer for the cohort (optional)'],
  ['emailed', 'Copy emailed'],
  ['id', 'Submission id'],
];

const QUESTIONS = [
  ['name', 'Name'],
  ['school', 'School'],
  ['level', 'G/UG'],
  ['degree', 'Degree'],
  ['year', 'Year'],
  ['email', 'Email'],
  ['phone', 'Phone #'],
  ['linkedin', 'LinkedIn'],
  ['subject', 'What is a subject you know more about than anyone else? Why are you fascinated by it? What have you accomplished or built in this space?'],
  ['pick', 'If you could choose any company or person to join or invest in today what/who would it be? Why?'],
  ['goals', 'What are your goals for 3-5 years from now?'],
  ['peer', '(Optional) Who is a peer you would be excited to see in the cohort?'],
];

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const data = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    if (data.website) return json({ ok: true }); // honeypot field filled in: a bot

    const sheet = getSheet();
    const col = key => COLUMNS.findIndex(([k]) => k === key) + 1;
    const rows = sheet.getLastRow() > 1
      ? sheet.getRange(2, 1, sheet.getLastRow() - 1, COLUMNS.length).getValues()
      : [];
    if (data.id && rows.some(r => String(r[col('id') - 1]) === String(data.id))) {
      return json({ ok: true, duplicate: true });
    }

    const email = String(data.email || '').trim();
    const validEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    // one copy per address per day, so the endpoint can't be used to flood someone's inbox
    const dayAgo = Date.now() - 24 * 3600 * 1000;
    const recentlyEmailed = rows.some(r =>
      String(r[col('email') - 1]).toLowerCase() === email.toLowerCase() &&
      r[col('emailed') - 1] === 'yes' &&
      new Date(r[col('submitted') - 1]).getTime() > dayAgo);

    let emailed = 'no';
    if (validEmail && !recentlyEmailed && MailApp.getRemainingDailyQuota() > 0) {
      try { sendCopy(email, data); emailed = 'yes'; } catch (err) { emailed = 'failed: ' + err; }
    } else if (recentlyEmailed) {
      emailed = 'skipped (sent in last 24h)';
    }

    const row = COLUMNS.map(([key]) =>
      key === 'submitted' ? new Date() : key === 'emailed' ? emailed : clean(data[key]));
    sheet.appendRow(row);
    return json({ ok: true, emailed });
  } catch (err) {
    return json({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

function sendCopy(to, data) {
  const first = String(data.name || '').trim().split(/\s+/)[0];
  const rows = QUESTIONS
    .filter(([key]) => String(data[key] || '').trim())
    .map(([key, q]) =>
      '<tr><td style="padding:10px 0;border-bottom:1px solid #e3d6bd">' +
      '<div style="font:600 13px Georgia,serif;color:#26448c;margin-bottom:4px">' + esc(q) + '</div>' +
      '<div style="font:15px/1.5 Georgia,serif;color:#2a1e16;white-space:pre-wrap">' + esc(data[key]) + '</div></td></tr>')
    .join('');
  const html =
    '<div style="max-width:600px;margin:0 auto;padding:24px;background:#f6f0df;font:15px/1.5 Georgia,serif;color:#2a1e16">' +
    '<h1 style="font:400 28px Georgia,serif;color:#a8291b;margin:0 0 12px">Eos Fellowship</h1>' +
    '<p>' + (first ? 'Hi ' + esc(first) + ',' : 'Hi,') + '</p>' +
    '<p>Thank you for applying to the Eos Fellowship. Here is a copy of your application.</p>' +
    '<p>We will review all applications and reach out in early 2027 if you are invited to interview. ' +
    'First cohort will be selected by the end of Q1 2027.</p>' +
    '<table style="width:100%;border-collapse:collapse;margin-top:12px">' + rows + '</table>' +
    '</div>';
  const text = QUESTIONS
    .filter(([key]) => String(data[key] || '').trim())
    .map(([key, q]) => q + '\n' + String(data[key]))
    .join('\n\n');
  MailApp.sendEmail({
    to: to,
    subject: 'Your Eos Fellowship application',
    name: FROM_NAME,
    htmlBody: html,
    body: 'Thank you for applying to the Eos Fellowship. Here is a copy of your application.\n\n' + text,
  });
}

function getSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(COLUMNS.map(([, header]) => header));
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, COLUMNS.length).setFontWeight('bold');
  }
  return sheet;
}

// Keep cells as plain text: a leading = + - or @ would otherwise run as a formula.
function clean(value) {
  const s = String(value == null ? '' : value).slice(0, 4000);
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}

function esc(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
