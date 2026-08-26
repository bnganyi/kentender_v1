// Shared localStorage-backed state for the STD Configuration prototype (KE-PPRA-IT).
// All KenTender STD DCs import this module to read/write the one Draft.

const KEY = 'kt_std_ke_ppra_it_v1';

const COVERAGE_LABELS = [
  'Tender identity and invitation', 'Instructions to Tenderers', 'Tender Data Sheet',
  'Evaluation and Qualification', 'Non-price Tendering Forms', 'Price Schedule Forms',
  'Requirements of the Information System', 'Technical Requirements', 'Implementation Schedule',
  'System Inventory Tables', 'Background and Informational Materials', 'General Conditions of Contract',
  'Special Conditions of Contract', 'Contract Forms and appendices', 'Securities, declarations and evidence',
  'Post-award administration forms'
];

const AREA_DEFS = [
  { key: 'source-profile', label: 'Source and Profile', file: 'PCFG_01_Source_Profile.dc.html' },
  { key: 'coverage-structure', label: 'Coverage and Document Structure', file: 'PCFG_02_Coverage_Document_Structure.dc.html' },
  { key: 'tender-parameters', label: 'Tender Parameters', file: 'PCFG_03_Tender_Parameters.dc.html' },
  { key: 'it-requirements', label: 'IT Requirements', file: 'PCFG_04_IT_Requirements.dc.html' },
  { key: 'schedule-inventory', label: 'Schedule, Inventory and Background', file: 'PCFG_05_Schedule_Inventory_Background.dc.html' },
  { key: 'price-schedules', label: 'Price Schedules', file: 'PCFG_06_Price_Schedules.dc.html' },
  { key: 'evaluation-qualification', label: 'Evaluation and Qualification', file: 'PCFG_07_Evaluation_Qualification.dc.html' },
  { key: 'forms-evidence', label: 'Forms and Evidence', file: 'PCFG_08_Forms_Evidence.dc.html' },
  { key: 'contract-outputs', label: 'Contract and Outputs', file: 'PCFG_09_Contract_Outputs.dc.html' },
];

function nowLabel() {
  return new Date().toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) + ' EAT';
}

function defaultState() {
  return {
    packageCode: 'KE-PPRA-IT',
    officialTitle: 'Standard Tender Document for Procurement of Information Technology',
    requirementProfile: 'Information Technology',
    officialIssue: 'April 2021 edition',
    officialSourceFile: 'PPRA IT Standard Tender Document.pdf',
    proposedVersionNumber: 1,
    activeVersionNumber: null,
    lifecycle: 'Draft', // Draft | In review | Returned | Active
    submittedAt: null,
    lastCorrection: null,
    areas: Object.fromEntries(AREA_DEFS.map(a => [a.key, { status: 'Complete' }])),
    tenderValidityMinDays: 120,
    coverageRows: COVERAGE_LABELS.map((label, i) => ({ no: i + 1, label, result: 'Complete' })),
    blockingFindings: 0,
    warnings: [
      { area: 'IT Requirements', text: 'Vendor-neutrality trigger includes named cloud platforms and requires reviewer attention.' }
    ],
    history: [
      { time: '25 Aug 2026, 09:00 EAT', text: 'Draft Version 1 created', actor: 'System' }
    ],
    assistanceDecisions: {}, // itemKey -> 'accepted' | 'rejected'
    versionComparison: null,
  };
}

export function load() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) { const s = defaultState(); save(s); return s; }
    const parsed = JSON.parse(raw);
    return { ...defaultState(), ...parsed };
  } catch (e) {
    const s = defaultState();
    save(s);
    return s;
  }
}

export function save(state) {
  localStorage.setItem(KEY, JSON.stringify(state));
  return state;
}

export function reset() {
  const s = defaultState();
  save(s);
  return s;
}

export function areaDefs() { return AREA_DEFS; }
export function coverageLabels() { return COVERAGE_LABELS; }

export function logHistory(state, text, actor) {
  state.history = [{ time: nowLabel(), text, actor: actor || 'Amina Hassan' }, ...state.history];
}

export function saveArea(areaKey, patch) {
  const s = load();
  s.areas[areaKey] = { ...s.areas[areaKey], ...patch, status: 'Complete' };
  const def = AREA_DEFS.find(a => a.key === areaKey);
  logHistory(s, `Saved ${def ? def.label : areaKey}`, 'Amina Hassan');
  save(s);
  return s;
}

export function runCompleteCheck() {
  const s = load();
  logHistory(s, 'Complete check passed', 'Amina Hassan');
  save(s);
  return s;
}

export function submitForReview() {
  const s = load();
  if (s.blockingFindings > 0) throw new Error('STD_VALIDATION_BLOCKED');
  s.lifecycle = 'In review';
  s.submittedAt = nowLabel();
  logHistory(s, 'Submitted for review', 'Amina Hassan');
  save(s);
  return s;
}

export function returnForCorrection(note) {
  const s = load();
  s.lifecycle = 'Returned';
  s.lastCorrection = note;
  logHistory(s, `Returned for correction: ${note}`, 'David Mwangi');
  save(s);
  return s;
}

export function resubmit() {
  const s = load();
  s.lifecycle = 'In review';
  logHistory(s, 'Resubmitted for review', 'Amina Hassan');
  save(s);
  return s;
}

export function activate() {
  const s = load();
  const newVersion = (s.activeVersionNumber || 0) + 1;
  if (s.activeVersionNumber) {
    s.versionComparison = {
      fromVersion: s.activeVersionNumber,
      toVersion: newVersion,
    };
  }
  s.activeVersionNumber = newVersion;
  s.proposedVersionNumber = newVersion + 1;
  s.lifecycle = 'Active';
  s.submittedAt = null;
  logHistory(s, `Version ${newVersion} activated`, 'David Mwangi');
  save(s);
  return s;
}

export function createNextDraft() {
  const s = load();
  s.lifecycle = 'Draft';
  s.officialIssue = 'June 2028 revision';
  s.officialSourceFile = 'PPRA IT Standard Tender Document June 2028.pdf';
  s.tenderValidityMinDays = 150;
  logHistory(s, `Draft Version ${s.proposedVersionNumber} created`, 'System');
  save(s);
  return s;
}

export function setAssistanceDecision(itemKey, decision) {
  const s = load();
  s.assistanceDecisions[itemKey] = decision;
  save(s);
  return s;
}

export function patchTopLevel(patch) {
  const s = load();
  Object.assign(s, patch);
  save(s);
  return s;
}

export function completeAreaCount(s) {
  return Object.values(s.areas).filter(a => a.status === 'Complete').length;
}
