// Builds SEFS_Presentation.pptx.  Run from this folder:  node build_slides.js
//
// HOW TO UPDATE AS PARTS ARE COMPLETED
//   1. Flip the part's flag in DONE below (e.g. part3: true).
//   2. Update its line in STATUS (status text + detail).
//   3. Rebuild. Slides for a part only appear once its flag is true.
//   Slides for Part 4 and the extension have not been written yet: add a
//   function like part3() and call it from build() behind its flag.

const pptxgen = require("pptxgenjs");
const { applyTheme } = require("./apply_theme.js");

// Bump the version number each time the deck is reissued (v4 was the previous progress review).
const OUT = "Group 6 SEFS Progress v10.pptx";

const TEAM = [
  ["Pascal Felix Erotu", "MAY26/MAIDS/0056U"],
  ["Daniel Odong", "MAY26/MAIDS/0883U"],
];

const DONE = {
  part1: true,
  part2: true,
  part3: true,
  part4: false,
  extension: true,
};

// One row per part on the status slide. state: "done" | "progress" | "todo"
const STATUS = [
  { part: "Part 1 · User authentication", marks: "20 marks", state: "done", detail: "5 functions · salted PBKDF2 · demo 13/13 recorded in logs/" },
  { part: "Part 2 · Simplified SEFS", marks: "30 marks", state: "done", detail: "9 functions · demo 15/15 recorded in logs/" },
  { part: "Part 3 · Full multi-chunk SEFS", marks: "45 marks", state: "done", detail: "chunk chains · demo 24/24 recorded in logs/" },
  { part: "Part 4 · Interoperability", marks: "5 marks", state: "progress", detail: "Next: exchange files with a partner group" },
  { part: "Extension · AI vs manual tests", marks: "+25 marks", state: "done", detail: "AI 14/20 vs manual 5/20 seeded faults (p = 0.004)" },
];

const THEME = {
  // Palette taken from Group 6 SEFS Progress v4 so the decks look like one series.
  name: "Group 6 SEFS",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0F2233", lt1: "FFFFFF", dk2: "3E4C59", lt2: "EAF1F3",
    accent1: "0E7C7B", // teal   - main
    accent2: "D98E1E", // amber  - highlights, step numbers
    accent3: "B83A2E", // red    - attacks, failure
    accent4: "3D5A80", // steel  - IVs, inputs
    accent5: "2E8B57", // green  - success
    accent6: "0F2233", // navy   - meta files / dark panels
    hlink: "0E7C7B", folHlink: "3D5A80",
  },
};
const HEX = THEME.colors;
const DARK_BG = "0F2233";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.author = "Group 6";
pres.title = "SEFS: Secure Encrypted File System";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
// Explicit hex colours (not theme references) so every viewer, including WPS Office and
// previews, shows the same colours.
const C = {
  text1: HEX.dk1, text2: HEX.dk2, background1: "FFFFFF", background2: HEX.lt2,
  accent1: HEX.accent1, accent2: HEX.accent2, accent3: HEX.accent3,
  accent4: HEX.accent4, accent5: HEX.accent5, accent6: HEX.accent6,
};
const SH = pres.shapes;

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "TITLE",
  background: { color: DARK_BG },
});
pres.defineSlideMaster({
  title: "SECTION",
  background: { color: DARK_BG },
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: "FFFFFF" },
});

// ---------- helpers ----------
let section = null;
let slideNo = 0;
function newSlide(master, sectionTitle) {
  if (sectionTitle && sectionTitle !== section) {
    pres.addSection({ title: sectionTitle });
    section = sectionTitle;
  }
  const sl = pres.addSlide({ masterName: master, sectionTitle: section });
  sl.background = { color: master === "CONTENT" ? "FFFFFF" : DARK_BG };
  slideNo += 1;
  if (master !== "TITLE") {
    // Footer and page number as plain text on the slide itself (no layout fields).
    if (master === "CONTENT") sl.addText("Group 6 · SEFS Cryptosystems Project", { isTextBox: true, x: 0.6, y: 6.95, w: 8, h: 0.3, fontSize: 11, color: "6B7A88", margin: 0 });
    sl.addText(String(slideNo), { isTextBox: true, x: 12.1, y: 6.95, w: 0.6, h: 0.3, fontSize: 10, color: "8A99A6", align: "right", margin: 0 });
  }
  return sl;
}
// Titles are ordinary text boxes, not layout placeholders, so no viewer shows them empty.
function titleText(s, text, o) {
  s.addText(text, { isTextBox: true, margin: 0, bold: true, fontFace: THEME.headFontFace, align: "left", ...o });
}
function content(title, sectionTitle) {
  const s = newSlide("CONTENT", sectionTitle);
  titleText(s, title, { x: 0.6, y: 0.35, w: 12.1, h: 0.85, fontSize: 30, color: HEX.dk1, valign: "middle" });
  return s;
}
// Section opener: number, title, and a short "in this section" list (no empty decoration).
function divider(kicker, title, sectionTitle, agenda = []) {
  const s = newSlide("SECTION", sectionTitle);
  s.addText(kicker, { isTextBox: true, x: 0.7, y: 1.3, w: 6, h: 0.6, margin: 0, fontSize: 20, bold: true, color: HEX.accent1 });
  titleText(s, title, { x: 0.7, y: 1.9, w: 11.9, h: 1.2, fontSize: 40, color: "FFFFFF", valign: "top" });
  if (agenda.length) {
    s.addText("In this section", { isTextBox: true, x: 0.7, y: 3.45, w: 6, h: 0.4, margin: 0, fontSize: 16, bold: true, color: HEX.accent2 });
    const half = Math.ceil(agenda.length / 2);
    [agenda.slice(0, half), agenda.slice(half)].forEach((col, c) => {
      if (!col.length) return;
      s.addText(col.map((a, i) => ({ text: a, options: { bullet: true, breakLine: i < col.length - 1 } })),
        { isTextBox: true, x: 0.7 + c * 6.0, y: 3.95, w: 5.8, h: 2.6, margin: 0, fontSize: 16, color: "D6DEE5", valign: "top", paraSpaceAfter: 8 });
    });
  }
  return s;
}
function chunkChain(s, x, y, w, fill, lineColor) {
  for (let i = 0; i < 3; i++) {
    const bx = x + i * (w + 0.55);
    s.addShape(SH.ROUNDED_RECTANGLE, { x: bx, y, w, h: 0.55, rectRadius: 0.08, fill: { color: fill }, line: { color: fill } });
    arrow(s, bx + w + 0.05, y + 0.275, bx + w + 0.5, y + 0.275, lineColor);
  }
  s.addText("NULL", { x: x + 3 * (w + 0.55), y, w: 0.9, h: 0.55, fontSize: 14, bold: true, color: lineColor, valign: "middle", margin: 0, isTextBox: true });
}
function box(s, text, x, y, w, h, o = {}) {
  const fill = o.fill ?? C.background2;
  s.addText(text, {
    shape: o.shape ?? SH.ROUNDED_RECTANGLE, rectRadius: o.r ?? 0.08, x, y, w, h,
    fill: { color: fill, transparency: o.transparency ?? 0 }, line: { color: o.line ?? fill, width: o.lw ?? 1 },
    color: o.color ?? C.text1, fontSize: o.size ?? 14, bold: o.bold ?? false,
    fontFace: o.font, align: o.align ?? "center", valign: o.valign ?? "middle", margin: o.margin ?? 6,
    paraSpaceAfter: o.psa ?? 0,
  });
}
function txt(s, text, x, y, w, h, o = {}) {
  s.addText(text, {
    x, y, w, h, isTextBox: true, margin: 0, fontSize: o.size ?? 14, color: o.color ?? C.text2,
    bold: o.bold ?? false, italic: o.italic ?? false, align: o.align ?? "left", valign: o.valign ?? "top",
    fontFace: o.font, paraSpaceAfter: o.psa ?? 0,
  });
}
function arrow(s, x1, y1, x2, y2, color = HEX.dk2) {
  s.addShape(SH.LINE, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    flipH: x2 < x1, flipV: y2 < y1, line: { color, width: 1.75, endArrowType: "triangle" },
  });
}
function circleNum(s, n, x, y, d, fill = C.accent2) {
  s.addText(String(n), { shape: SH.OVAL, x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, color: C.background1, bold: true, fontSize: 14, align: "center", valign: "middle", margin: 0 });
}
// header line + detail line inside a box
const hd = (head, detail, dsize = 12) => [
  { text: head, options: { bold: true, breakLine: true } },
  { text: detail, options: { fontSize: dsize } },
];

// ======================================================================
// OPENING
// ======================================================================
function opening() {
  const s = newSlide("TITLE", "Overview");
  s.addText("CRYPTOSYSTEMS · GROUP 6 · PROGRESS UPDATE", { x: 0.7, y: 1.0, w: 11.9, h: 0.45, isTextBox: true, margin: 0, fontSize: 18, bold: true, color: HEX.accent2, charSpacing: 3 });
  titleText(s, "SEFS: a Secure Encrypted File System, built and verified part by part", { x: 0.7, y: 1.5, w: 11.9, h: 1.5, fontSize: 44, color: "FFFFFF", valign: "bottom" });
  s.addText("Pure Python implementation · November 2026", { isTextBox: true, x: 0.7, y: 3.15, w: 11.9, h: 0.7, margin: 0, fontSize: 22, color: "B9C6D1" });
  const th = (t2) => ({ text: t2, options: { bold: true, color: "FFFFFF", fill: { color: HEX.accent1 } } });
  s.addTable([[th("Name"), th("Reg Number")], ...TEAM.map((r, i) => r.map((c) => ({ text: c, options: { bold: true, color: HEX.dk1, fill: { color: i % 2 ? "E7EEEF" : "CFDCDE" } } })))], {
    x: 0.7, y: 4.4, w: 7.2, colW: [3.6, 3.6], rowH: 0.48, fontSize: 18, border: { type: "solid", pt: 1, color: "FFFFFF" }, valign: "middle", margin: [0.04, 0.12, 0.04, 0.12],
  });
  s.addNotes("SEFS stores files encrypted on disk, split into fixed-size chunks, with every chunk authenticated. This deck covers the parts completed so far and is extended as each further part is finished.");

  // ---- introduction and objectives ----
  const io = content("Introduction and objectives", "Overview");
  box(io, "", 0.6, 1.4, 5.6, 5.2, { fill: C.text1 });
  txt(io, "Introduction", 0.85, 1.6, 5.1, 0.4, { bold: true, color: HEX.accent2, size: 17 });
  txt(io, [
    { text: "Files saved on a shared disk can be read or quietly changed by anyone who can reach that disk.", options: { breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "SEFS, a Secure Encrypted File System, solves this: only registered users can log in, every file is stored encrypted, split into fixed-size chunks, and every chunk carries an integrity tag, so any tampering is detected before data is returned.", options: { breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "We built it in pure Python and then used it as the test subject for a study comparing AI-assisted and manual testing." },
  ], 0.85, 2.1, 5.1, 4.3, { size: 14, color: "D6DEE5" });
  txt(io, "Objectives", 6.6, 1.4, 6.1, 0.4, { bold: true, color: C.text1, size: 17 });
  const objs = [
    ["Authenticate users", "Store passwords only as a salt and a slow hash (Part 1)"],
    ["Keep file contents confidential", "AES-128-CTR encryption with per-user keys (Parts 2–3)"],
    ["Detect any tampering", "HMAC on every chunk and a digest of every meta file (Parts 2–3)"],
    ["Handle files of any size", "Linked chains of 1,024-byte chunks with safe partial writes (Part 3)"],
    ["Interoperate", "Exchange files with a partner group (Part 4, next)"],
    ["Answer a research question", "Does AI-assisted test generation find more defects than manual tests in a fixed time? (Extension)"],
  ];
  objs.forEach(([h, t2], i) => {
    const y = 1.9 + i * 0.78;
    circleNum(io, i + 1, 6.6, y + 0.08, 0.42, i === 5 ? C.accent2 : C.accent1);
    txt(io, [
      { text: h, options: { bold: true, color: C.text1, fontSize: 15, breakLine: true } },
      { text: t2, options: { fontSize: 12 } },
    ], 7.2, y, 5.5, 0.75);
  });
  io.addNotes("The first five objectives come from the assignment brief (Parts 1-4). The sixth is our group's extension: a controlled experiment comparing AI-assisted and manual test generation on the finished system.");


  // ---- methodology, step by step ----
  const me = content("Methodology: build the system, then run the experiment", "Overview");
  const build = ["Read the spec", "Implement Parts 1–3 in Python", "Unit tests + recorded demos (52/52)", "Freeze the code: sefs-v1.0"];
  txt(me, "A · Build the system", 0.6, 1.3, 4, 0.35, { bold: true, color: C.text1, size: 14 });
  build.forEach((t2, i) => {
    const x = 0.6 + i * 3.08;
    box(me, t2, x, 1.68, 2.88, 0.5, { fill: C.background2, color: C.text1, size: 13, bold: true, r: 0.04 });
    if (i < 3) arrow(me, x + 2.9, 1.93, x + 3.06, 1.93);
  });
  txt(me, "B · Run the experiment (extension)", 0.6, 2.35, 6, 0.35, { bold: true, color: C.text1, size: 14 });
  const cols = [
    ["1 · Set up", C.text1, [
      "Code frozen at tag sefs-v1.0; it never changes between arms",
      "Pascal seeds 20 realistic bugs, 5 per area, as find/replace edits",
      "Faults are git-ignored: the tester and the AI never see them",
      "Both arms get the same specification and test fixtures",
    ]],
    ["2 · Manual arm", HEX.accent4, [
      "Daniel writes pytest tests by hand, no AI",
      "120-minute budget (he used 160)",
      "Written first, then frozen, so AI output cannot influence it",
      "Extra tests after the budget are kept apart (manual_extended)",
    ]],
    ["3 · AI-assisted arm", HEX.accent1, [
      "Fresh Claude agent, locked in an isolated workspace with the spec only",
      "5 standard prompts: authentication, round trip, chunk boundaries, tamper, gap review",
      "Daniel reviews every test with the group: accept, edit or reject",
      "Every prompt and decision logged",
    ]],
    ["4 · Measure and analyse", HEX.accent2, [
      "Mutation testing: run each suite against each fault (run_mutants.py)",
      "Coverage of src/sefs with coverage.py",
      "False positives and minutes from the logs",
      "McNemar exact test + bootstrap 95% CI (analyze.py)",
    ]],
  ];
  cols.forEach(([h, col, items], i) => {
    const x = 0.6 + i * 3.08;
    box(me, h, x, 2.73, 2.88, 0.45, { fill: col, color: C.background1, bold: true, size: 15, r: 0.04 });
    box(me, "", x, 3.22, 2.88, 2.5, { fill: C.background2, r: 0.04 });
    txt(me, items.map((t2, j) => ({ text: t2, options: { bullet: true, breakLine: j < items.length - 1 } })), x + 0.1, 3.3, 2.7, 2.38, { size: 11.5, color: C.text1, psa: 3 });
    if (i < 3) arrow(me, x + 2.9, 2.955, x + 3.06, 2.955);
  });
  box(me, [
    { text: "Why it is fair: ", options: { bold: true } },
    { text: "a paired design. Every arm is scored against the same 20 hidden faults on the same frozen code, so the arms are compared fault by fault. A fault counts as detected when at least one test fails on the faulty copy; every suite must first pass on the unchanged code." },
  ], 0.6, 5.85, 12.1, 0.85, { fill: C.text1, color: C.background1, size: 12.5, align: "left", margin: 12 });
  me.addNotes("Full procedure: docs/EXPERIMENT.md sections 3-5. The evaluation set (seeded faults) works like a held-out test set: nobody writing tests could tune to it. Prompts are logged in logs/ai_prompt_log.csv, review decisions in logs/ai_review_sheet.csv, time in logs/time_log.csv.");

  // ---- status ----
  const t = content("Where the project stands", "Overview");
  const done = STATUS.filter((r) => r.state === "done").length;
  txt(t, `${done}/5`, 0.6, 1.55, 3.3, 1.1, { size: 60, bold: true, color: C.accent1, font: THEME.headFontFace });
  txt(t, "assignment parts completed", 0.6, 2.65, 3.3, 0.4, { size: 14 });
  txt(t, "52/52", 0.6, 3.55, 3.3, 1.1, { size: 60, bold: true, color: C.accent1, font: THEME.headFontFace });
  txt(t, "demo checks as expected across Parts 1–3", 0.6, 4.65, 3.3, 0.7, { size: 14 });
  const pill = { done: ["Complete", C.accent5], progress: ["Next", C.accent2], todo: ["Not started", "8A99A6"] };
  STATUS.forEach((r, i) => {
    const y = 1.5 + i * 1.03;
    box(t, "", 4.3, y, 8.4, 0.88, { fill: C.background2 });
    txt(t, [
      { text: r.part, options: { bold: true, color: C.text1, fontSize: 16, breakLine: true } },
      { text: `${r.marks} · ${r.detail}`, options: { fontSize: 13 } },
    ], 4.55, y + 0.1, 6.0, 0.7, { valign: "middle" });
    const [label, color] = pill[r.state];
    box(t, label, 10.75, y + 0.22, 1.7, 0.44, { fill: color, color: C.background1, bold: true, size: 13, r: 0.22 });
  });
  t.addNotes("Parts 1 to 3 are implemented and tested. Part 2 and Part 3 demonstrations are recorded in logs/ (part_2_log and part_3_log, .txt and .csv). Part 4 is the next milestone; this deck is updated each time a part is finished.");
}

// ======================================================================
// ARCHITECTURE
// ======================================================================
function architecture() {
  divider("01", "System architecture and flow", "Architecture", ["System context and threat model", "Layered module design", "Data model: how the files fit together", "Key hierarchy: which secret protects what", "The checks every file call passes", "End-to-end write and read flows", "The fourteen functions at a glance", "Security goals (CIA) and how they are met"]);
  slideContext();

  const s = content("Layered design: one module per responsibility", "Architecture");
  box(s, hd("Python API", "import sefs"), 0.6, 1.5, 4.0, 0.8, { fill: C.accent4, color: C.background1, size: 15 });
  box(s, hd("Command line", "python -m sefs keygen | register | encrypt | read …"), 4.9, 1.5, 4.0, 0.8, { fill: C.accent4, color: C.background1, size: 15 });
  arrow(s, 2.6, 2.33, 2.6, 2.62); arrow(s, 6.9, 2.33, 6.9, 2.62);
  box(s, hd("fs.py", "the nine file functions: create, encrypt, decrypt, read, write, size, check, delete, health"), 0.6, 2.65, 8.3, 0.85, { fill: C.accent1, color: C.background1, size: 15 });
  [1.9, 4.75, 7.6].forEach((x) => arrow(s, x, 3.53, x, 3.82));
  box(s, hd("auth.py", "Part 1: users and passwords"), 0.6, 3.85, 2.6, 0.95, { fill: C.accent6, color: C.background1, size: 15 });
  box(s, hd("chunk.py", "one encrypted chunk"), 3.45, 3.85, 2.6, 0.95, { fill: C.accent6, color: C.background1, size: 15 });
  box(s, hd("meta.py", "meta files and Master File List"), 6.3, 3.85, 2.6, 0.95, { fill: C.accent6, color: C.background1, size: 15 });
  [1.9, 4.75, 7.6].forEach((x) => arrow(s, x, 4.83, x, 5.12));
  box(s, hd("crypto.py", "AES-128-CTR · HMAC-SHA256\nSHA-256 · PBKDF2 · CSPRNG"), 0.6, 5.15, 2.6, 1.2, { size: 15 });
  box(s, hd("util.py", "atomic writes · master key\nbinary file I/O"), 3.45, 5.15, 2.6, 1.2, { size: 15 });
  box(s, hd("config.py", "every format constant in one place"), 6.3, 5.15, 2.6, 1.2, { size: 15 });

  box(s, "", 9.4, 1.5, 3.3, 4.85, { fill: C.background2 });
  txt(s, "On disk (working folder)", 9.65, 1.65, 2.9, 0.4, { bold: true, color: C.text1, size: 15 });
  const files = [
    ["passwd", "user accounts"], ["master.key", "master key + IV"], ["masterlist", "file → meta digest"],
    ["<name>.meta", "encrypted file record"], ["chunks/<32 hex>", "encrypted chunks"],
  ];
  files.forEach(([f, d], i) => {
    txt(s, [
      { text: f, options: { fontFace: "Courier New", bold: true, color: C.text1, fontSize: 14, breakLine: true } },
      { text: d, options: { fontSize: 12 } },
    ], 9.65, 2.2 + i * 0.8, 2.9, 0.7);
  });
  s.addNotes("Each module has one job. fs.py orchestrates; it asks auth.py to check the password, chunk.py and meta.py to read and write encrypted structures, and crypto.py for primitives. All format constants are in config.py, so a format decision changes one line.");

  slideDataModel();
  slideKeys();

  // ---- system flow ----
  const f = content("Every file call passes the same checks before it acts", "Architecture");
  const steps = [
    ["Validate name", "letters and digits, 1–20"], ["Check password", "match_user (Part 1)"],
    ["Listed in masterlist?", "file must exist"], ["Meta file verified", "decrypts; SHA-256 digest matches"],
    ["Caller is the owner", "owner field in meta"], ["Every chunk verified", "HMAC checked first"],
    ["Perform the operation", "in memory"], ["Atomic save", "temp file → os.replace"],
  ];
  const xs = [0.6, 3.75, 6.9, 10.05];
  steps.forEach(([h, d], i) => {
    const row = i < 4 ? 0 : 1;
    const x = row === 0 ? xs[i] : xs[7 - i];
    const y = row === 0 ? 1.6 : 3.3;
    const last = i === 7;
    box(f, hd(`${i + 1}  ${h}`, d, 13), x, y, 2.65, 1.1, { fill: last ? C.accent1 : C.background2, color: last ? C.background1 : C.text1, size: 15 });
  });
  for (let i = 0; i < 3; i++) arrow(f, xs[i] + 2.68, 2.15, xs[i + 1] - 0.03, 2.15);
  arrow(f, 11.375, 2.73, 11.375, 3.27);
  for (let i = 3; i > 0; i--) arrow(f, xs[i] - 0.03, 3.85, xs[i - 1] + 2.68, 3.85);
  box(f, [
    { text: "Any check fails → stop:  ", options: { bold: true } },
    { text: "return -1 (None for read_from_file). Nothing on disk is changed." },
  ], 0.6, 4.85, 12.1, 0.75, { fill: C.accent3, transparency: 85, line: C.accent3, color: C.accent3, size: 16 });
  txt(f, [
    { text: "Why: ", options: { bold: true, color: C.text1 } },
    { text: "the system fails closed. No data is decrypted, returned or rewritten until identity, ownership and integrity have all been proven." },
  ], 0.6, 5.9, 12.1, 0.7, { size: 15 });
  f.addNotes("This is the internal _authorize path in fs.py. The order matters: cheap input checks first, then the password, then the integrity of the meta file and chunks, and only then the operation. The final save is atomic.");
  slideFlows();
  slideFunctions();
}

// ======================================================================
// PART 1
// ======================================================================
function part1() {
  divider("02", "Part 1 · User authentication", "Part 1", ["How passwords are stored: salt + slow hash", "Why each safeguard was chosen", "Simulation: the life of one account", "Recorded demonstration (logs/part_1_log)"]);

  const s = content("Passwords are never stored, only a salt and a slow hash", "Part 1");
  txt(s, "One line of the passwd file", 0.6, 1.4, 6, 0.35, { size: 14, bold: true, color: C.text1 });
  box(s, "alice01", 0.6, 1.8, 2.0, 0.8, { fill: C.accent4, color: C.background1, bold: true, size: 16, font: "Courier New" });
  txt(s, ":", 2.62, 1.8, 0.2, 0.8, { size: 20, bold: true, valign: "middle", align: "center" });
  box(s, "salt · 64 hex characters", 2.85, 1.8, 5.5, 0.8, { fill: C.accent2, color: C.background1, bold: true, size: 16 });
  txt(s, ":", 8.37, 1.8, 0.2, 0.8, { size: 20, bold: true, valign: "middle", align: "center" });
  box(s, "hash · 40 hex characters", 8.6, 1.8, 4.1, 0.8, { fill: C.accent1, color: C.background1, bold: true, size: 16 });
  txt(s, "username, 6–31 letters/digits", 0.6, 2.7, 2.2, 0.6, { size: 12 });
  txt(s, "32 random bytes from the OS (secrets.token_bytes)", 2.85, 2.7, 5.5, 0.4, { size: 12 });
  txt(s, "PBKDF2-HMAC-SHA1, 20,000 rounds, 20 bytes", 8.6, 2.7, 4.1, 0.4, { size: 12 });
  const cards = [
    ["Unique salt per user", "Two users with the same password get different hashes, so precomputed rainbow tables are useless. A fresh salt is made on every password change."],
    ["Deliberately slow hash", "20,000 PBKDF2 rounds make every password guess about 20,000 times more expensive for an attacker, at negligible cost for one login."],
    ["Constant-time compare", "hmac.compare_digest takes the same time however many bytes match, so response timing reveals nothing about the stored hash."],
  ];
  cards.forEach(([h, d], i) => {
    const x = 0.6 + i * 4.13;
    box(s, "", x, 3.5, 3.85, 2.45, { fill: C.background2 });
    circleNum(s, i + 1, x + 0.25, 3.7, 0.45);
    txt(s, h, x + 0.85, 3.72, 2.8, 0.45, { bold: true, color: C.text1, size: 16, valign: "middle" });
    txt(s, d, x + 0.25, 4.35, 3.4, 1.5, { size: 14 });
  });
  txt(s, "Passwords: 9–31 characters from letters, digits and @ # $ % & * ( ) - + =  ·  non-ASCII input rejected  ·  the file is rewritten atomically", 0.6, 6.2, 12.1, 0.4, { size: 13, italic: true });
  s.addNotes("The password itself never touches the disk. On login the typed password is hashed with the stored salt and compared in constant time. Q2 (20-byte hash, lowercase hex) and Q8 (username 6–31, password 9–31) were settled by the group on 24 Nov 2026, keeping these values.");

  // ---- account lifecycle simulation ----
  const t = content("Simulation: the life of one account", "Part 1");
  const steps = [
    ["register_user", "alice01, Passw0rd#1", "1", true, "alice01:salt1:hash1", "line appended"],
    ["match_user", "wrong password", "-1", false, "alice01:salt1:hash1", "unchanged"],
    ["change_user_password", "old → NewPassw0rd=", "1", true, "alice01:salt2:hash2", "fresh salt, line replaced"],
    ["match_user", "old password", "-1", false, "alice01:salt2:hash2", "old password rejected"],
    ["delete_user", "new password", "1", true, "(no line)", "account removed"],
  ];
  t.addShape(SH.LINE, { x: 1.1, y: 2.95, w: 11.1, h: 0, line: { color: "B9C6D1", width: 2 } });
  steps.forEach(([fn, arg, res, ok, state, note], i) => {
    const x = 0.6 + i * 2.47;
    txt(t, [
      { text: fn, options: { bold: true, color: C.text1, fontFace: "Courier New", fontSize: 13, breakLine: true } },
      { text: arg, options: { fontSize: 13 } },
    ], x, 1.5, 2.3, 1.0, { align: "center", valign: "bottom" });
    circleNum(t, i + 1, x + 0.9, 2.7, 0.5);
    box(t, `returns ${res}`, x + 0.4, 3.45, 1.5, 0.45, { fill: ok ? C.accent5 : C.accent3, color: C.background1, bold: true, size: 14, r: 0.22 });
    box(t, [
      { text: state, options: { fontFace: "Courier New", fontSize: 12, bold: true, breakLine: true } },
      { text: note, options: { fontSize: 12 } },
    ], x, 4.15, 2.3, 1.15, { fill: C.background2, size: 13 });
  });
  txt(t, "passwd file after each call · recorded 24 Nov 2026 in logs/part_1_log.txt", 0.6, 5.4, 9, 0.35, { size: 12, italic: true });
  box(t, [
    { text: "Also rejected with -1, file untouched:  ", options: { bold: true } },
    { text: "a duplicate username · username \"bob\" (too short) · password \"short\" (too short)" },
  ], 0.6, 5.9, 12.1, 0.65, { fill: C.background2, size: 14, align: "left", margin: 10 });
  t.addNotes("This follows the Part 1 demonstration script in docs/PART1_USER_AUTHENTICATION.md and is covered by 5 acceptance tests. Note step 3: changing the password generates a new salt, so the whole line changes.");
}

// ======================================================================
// PART 2
// ======================================================================
function part2() {
  divider("03", "Part 2 · Simplified SEFS", "Part 2", ["File format: meta file + 1,076-byte chunk", "Simulation: encrypt_file step by step", "Reads verify integrity before decrypting", "Live demo: 15 of 15 calls as expected", "Proof on disk: only ciphertext"]);

  // ---- on-disk format ----
  const s = content("One file = an encrypted meta file plus a 1,076-byte chunk", "Part 2");
  const segs = [
    ["IV · 16 B", 1.35, C.accent2], ["next name · 32 B", 2.35, C.accent4],
    ["size · 4 B", 1.3, C.accent4], ["content · 1,024 B, padded with 0x00", 7.1, C.accent4],
  ];
  let x = 0.6;
  segs.forEach(([l, w, c]) => { box(s, l, x, 1.55, w - 0.05, 0.75, { fill: c, color: C.background1, bold: true, size: 15, r: 0.04 }); x += w; });
  txt(s, "plaintext, new every write", 0.6, 2.38, 1.6, 0.6, { size: 12 });
  txt(s, "encrypted with AES-128-CTR(chunk key, IV)  ·  whole chunk file = 1,076 bytes", 1.95, 2.38, 10.75, 0.35, { size: 13, bold: true, color: C.accent4, align: "center" });

  box(s, [
    { text: "doc1.meta", options: { bold: true, fontFace: "Courier New", fontSize: 16, breakLine: true } },
    { text: "Encrypted with the master key and IV", options: { bold: true, breakLine: true } },
    { text: "owner · chunk count · file size · start and end chunk · per chunk: name, key, HMAC-SHA256" },
  ], 0.6, 3.6, 5.6, 1.9, { fill: C.accent6, color: C.background1, size: 14, align: "left", valign: "top", margin: 10 });
  box(s, [
    { text: "masterlist", options: { bold: true, fontFace: "Courier New", fontSize: 16, breakLine: true } },
    { text: "Plaintext, one line per file", options: { bold: true, breakLine: true } },
    { text: "filename + SHA-256 of the stored meta bytes" },
  ], 7.1, 3.6, 5.6, 1.9, { fill: C.background2, size: 14, align: "left", valign: "top", margin: 10 });
  arrow(s, 7.05, 4.55, 6.25, 4.55);
  txt(s, "digest", 6.25, 4.15, 0.85, 0.3, { size: 12, align: "center" });
  arrow(s, 3.4, 3.55, 3.4, 2.8);
  txt(s, "key + HMAC open and verify the chunk", 3.55, 2.95, 4.5, 0.35, { size: 12 });
  txt(s, [
    { text: "Why the key and HMAC live in the meta file: ", options: { bold: true, color: C.text1 } },
    { text: "anyone who edits a chunk cannot also fix its tag, because the tag is sealed under the master key." },
  ], 0.6, 5.8, 12.1, 0.7, { size: 15 });
  s.addNotes("Every chunk file is exactly 1,076 bytes: a 16-byte IV in the clear, then 1,060 encrypted bytes holding the next-chunk name, a 4-byte size and 1,024 bytes of content. In Part 2 a file has exactly one chunk, so next name is NULL.");

  // ---- encrypt simulation ----
  const e = content("Simulation: encrypt_file(\"doc1\") step by step", "Part 2");
  const steps = [
    ["Read plaintext", "doc1 = \"hello SEFS world\" (16 B)"],
    ["Fresh randomness", "chunk name, key and IV from the OS CSPRNG"],
    ["Build the body", "next = NULL · size = 16 · pad to 1,024 B"],
    ["Encrypt", "AES-128-CTR(key, IV) → 1,060 B ciphertext"],
    ["Write chunk", "IV + ciphertext = 1,076 B, atomic write"],
    ["Tag it", "HMAC-SHA256(key, all 1,076 B)"],
    ["Save meta", "owner, size, name, key, HMAC, sealed with master key"],
    ["Register", "SHA-256(meta) into masterlist → return 1"],
  ];
  const xs = [0.6, 3.75, 6.9, 10.05];
  steps.forEach(([h, d], i) => {
    const row = i < 4 ? 0 : 1;
    const bx = row === 0 ? xs[i] : xs[7 - i];
    const by = row === 0 ? 1.55 : 3.55;
    box(e, "", bx, by, 2.65, 1.45, { fill: i === 7 ? C.accent1 : C.background2 });
    circleNum(e, i + 1, bx + 0.15, by + 0.15, 0.42, i === 7 ? C.accent6 : i === 1 ? C.accent2 : C.accent1);
    txt(e, h, bx + 0.7, by + 0.15, 1.85, 0.42, { bold: true, size: 15, color: i === 7 ? C.background1 : C.text1, valign: "middle" });
    txt(e, d, bx + 0.15, by + 0.68, 2.4, 0.72, { size: 13, color: i === 7 ? C.background1 : C.text2 });
  });
  for (let i = 0; i < 3; i++) arrow(e, xs[i] + 2.68, 2.27, xs[i + 1] - 0.03, 2.27);
  arrow(e, 11.375, 3.03, 11.375, 3.52);
  for (let i = 3; i > 0; i--) arrow(e, xs[i] - 0.03, 4.27, xs[i - 1] + 2.68, 4.27);
  txt(e, [
    { text: "Why a new key and IV every time: ", options: { bold: true, color: C.text1 } },
    { text: "CTR mode turns key + IV into a keystream. Reusing it for two different contents would let an attacker XOR the ciphertexts and learn the XOR of the plaintexts." },
  ], 0.6, 5.35, 12.1, 0.9, { size: 15 });
  e.addNotes("These are the steps in fs._store_plaintext and chunk.write for the one-chunk case. The same steps run on every write_to_file call, so every rewrite of a chunk gets a fresh key and IV.");

  // ---- read: integrity first ----
  const r = content("Reads check integrity before any decryption", "Part 2");
  const cy = 2.0, ch = 1.1;
  box(r, hd("read_from_file", "(\"doc1\", 6, 4)"), 0.6, cy, 1.95, ch, { fill: C.accent4, color: C.background1, size: 14 });
  arrow(r, 2.58, cy + ch / 2, 2.85, cy + ch / 2);
  box(r, hd("Authorize", "password · owner · meta digest"), 2.88, cy, 2.1, ch, { size: 14 });
  arrow(r, 5.01, cy + ch / 2, 5.28, cy + ch / 2);
  box(r, "HMAC matches?", 5.3, cy - 0.15, 1.95, ch + 0.3, { shape: SH.DIAMOND, fill: C.accent2, color: C.background1, bold: true, size: 13 });
  arrow(r, 7.28, cy + ch / 2, 7.6, cy + ch / 2);
  txt(r, "yes", 7.3, cy + 0.1, 0.4, 0.3, { size: 12, bold: true });
  box(r, hd("Decrypt", "AES-128-CTR"), 7.63, cy, 1.6, ch, { size: 14 });
  arrow(r, 9.26, cy + ch / 2, 9.53, cy + ch / 2);
  box(r, "6 + 4 ≤ size?", 9.55, cy - 0.15, 1.85, ch + 0.3, { shape: SH.DIAMOND, fill: C.accent2, color: C.background1, bold: true, size: 13 });
  arrow(r, 11.43, cy + ch / 2, 11.7, cy + ch / 2);
  txt(r, "yes", 11.42, cy + 0.1, 0.4, 0.3, { size: 12, bold: true });
  box(r, "b'SEFS'", 11.72, cy + 0.2, 0.98, ch - 0.4, { fill: C.accent5, color: C.background1, bold: true, size: 12, font: "Courier New", margin: 1 });
  arrow(r, 6.275, cy + ch + 0.18, 6.275, 3.85);
  txt(r, "no", 6.4, 3.4, 0.4, 0.3, { size: 12, bold: true });
  box(r, hd("Return None", "tampered data is never decrypted"), 4.95, 3.9, 2.65, 0.95, { fill: C.accent3, color: C.background1, size: 14 });
  arrow(r, 10.475, cy + ch + 0.18, 10.475, 3.85);
  txt(r, "no", 10.6, 3.4, 0.4, 0.3, { size: 12, bold: true });
  box(r, hd("Return None", "e.g. read(\"doc1\", 10, 100): past the end"), 9.0, 3.9, 3.7, 0.95, { fill: C.accent3, color: C.background1, size: 14 });
  box(r, [
    { text: "Why verify first (encrypt-then-MAC): ", options: { bold: true } },
    { text: "AES-CTR is malleable: flipping one ciphertext bit flips the same plaintext bit, and decryption still \"succeeds\". Checking the HMAC first means modified data is rejected before it is ever decrypted or returned." },
  ], 0.6, 5.25, 12.1, 1.3, { fill: C.background2, size: 15, align: "left", margin: 12 });
  r.addNotes("chunk.read checks the length, then the HMAC, and only then decrypts. read_from_file returns None on any failure so a caller can never confuse an error code with file data.");

  // ---- demo results ----
  const d = content("Live demo: all 15 calls returned the expected value", "Part 2");
  const rows = [
    ["register_user(alice01)", "1", "1"], ["create_file(\"notes\")", "1", "1"], ["file_size(\"notes\")", "0", "0"],
    ["write_to_file(\"notes\", 0, b\"helloworld\")", "1", "1"], ["write_to_file(\"notes\", 5, b\", \")  insert", "1", "1"],
    ["read_from_file(\"notes\", 0, 12)", "b'hello, world'", "b'hello, world'"], ["encrypt_file(\"doc1\")", "1", "1"],
    ["read_from_file(\"doc1\", 6, 4)", "b'SEFS'", "b'SEFS'"], ["read_from_file(\"doc1\", 10, 100)  past end", "None", "None"],
    ["decrypt_file(\"doc1\", \"doc1_out.txt\")", "1", "1"], ["file_integrity_check(\"doc1\")", "1", "1"],
    ["system_health_check()", "1", "1"], ["register_user(mallory1)", "1", "1"],
    ["delete_file(\"doc1\") by mallory1  not owner", "-1", "-1"], ["delete_file(\"doc1\") by alice01", "1", "1"],
  ];
  const head = ["#", "Call", "Expected", "Actual", "Result"].map((h) => ({ text: h, options: { bold: true, color: C.background1, fill: { color: C.text1 } } }));
  const body = rows.map(([c, ex, ac], i) => [
    String(i + 1), { text: c, options: { fontFace: "Courier New" } }, ex, ac,
    { text: "PASS", options: { bold: true, color: C.accent5 } },
  ].map((cell) => (typeof cell === "string" ? { text: cell, options: { fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } } } : { text: cell.text, options: { ...cell.options, fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } } })));
  d.addTable([head, ...body], {
    x: 0.6, y: 1.35, w: 12.1, colW: [0.5, 6.6, 1.9, 1.9, 1.2], rowH: 0.32, fontSize: 12, color: HEX.dk1,
    border: { type: "solid", pt: 0.5, color: "D5DCE2" }, valign: "middle", margin: [0.02, 0.08, 0.02, 0.08],
  });
  txt(d, "Recorded 21 Nov 2026 in logs/part_2_log.txt and logs/part_2_log.csv · U = alice01 (owner), mallory1 = second user", 0.6, 6.55, 12.1, 0.3, { size: 11, italic: true });
  d.addNotes("Step 14 is the important negative test: a valid, logged-in user who is not the owner cannot delete someone else's file. Step 9 shows reads past the end of a file return None instead of partial data.");

  // ---- proof on disk ----
  const p = content("Proof on disk: the chunk file holds only ciphertext", "Part 2");
  box(p, "", 0.6, 1.45, 7.9, 3.55, { fill: "1E2A36" });
  const mono = (t2, color = "D6DEE5", bold = false) => ({ text: t2, options: { fontFace: "Courier New", color, bold, fontSize: 13, breakLine: true } });
  txt(p, [
    mono("> certutil -dump chunks\\057f21e8…", "8FD3C7", true),
    mono(" "),
    mono("0000  eb 3d 21 0e 02 fa a1 a8  fc 9c 29 24 1c c9 49 c4", "F2C14E"),
    mono("0010  05 b6 10 95 10 d0 b0 03  50 87 44 a7 53 1d fc c1"),
    mono("0020  3b 71 89 b4 73 40 f2 79  cd 67 f1 b5 8b a3 0d ef"),
    mono("0030  cc ee e9 15 62 b0 89 7b  5d 5c 81 59 f5 35 98 10"),
    mono(" …   (rows 0040–0420: random-looking bytes)", "8A99A6"),
    mono("0430  5b c4 ce d6"),
    mono(" "),
    { text: "length 0x434 = 1,076 bytes", options: { fontFace: "Courier New", color: "8FD3C7", fontSize: 13 } },
  ], 0.85, 1.65, 7.5, 4.2);
  txt(p, "IV (16 B, plaintext)", 6.2, 2.13, 2.2, 0.3, { size: 11, color: "F2C14E", align: "right", bold: true });
  const stats = [
    ["0", "matches for \"hello SEFS world\" in any chunk file"],
    ["1,076", "bytes per chunk, exactly as specified"],
    ["~1,000", "bytes of zero padding, invisible after encryption"],
  ];
  stats.forEach(([n, l], i) => {
    txt(p, n, 8.95, 1.45 + i * 1.55, 3.75, 0.8, { size: 44, bold: true, color: C.accent1, font: THEME.headFontFace });
    txt(p, l, 8.95, 2.2 + i * 1.55, 3.75, 0.6, { size: 14 });
  });
  p.addNotes("This hex dump was taken during the recorded demo. The first 16 bytes are the IV, stored in the clear as CTR mode requires. Everything after it is ciphertext: even the long run of zero padding looks random because each byte is XORed with the keystream.");
}

// ======================================================================
// PART 3 (shown once DONE.part3 is true)
// ======================================================================
function part3() {
  divider("04", "Part 3 · Full multi-chunk SEFS", "Part 3", ["Large files as linked chunk chains", "The chunk-count rule and cross-boundary reads", "Simulation: a safe insert", "Tampering simulation: every attack caught"]);

  const s = content("Large files become a linked chain of chunks", "Part 3");
  box(s, hd("report.meta", "start A · end C · 3 chunks · 2,548 B", 12), 0.6, 1.55, 2.5, 1.05, { fill: C.accent6, color: C.background1, size: 15 });
  arrow(s, 3.13, 2.075, 3.47, 2.075);
  [["Chunk A", "1,024 B"], ["Chunk B", "1,024 B"], ["Chunk C", "500 B + padding"]].forEach(([h, d2], i) => {
    const bx = 3.5 + i * 2.55;
    box(s, hd(h, d2, 13), bx, 1.55, 2.0, 1.05, { fill: C.accent4, color: C.background1, size: 15 });
    arrow(s, bx + 2.03, 2.075, bx + 2.52, 2.075);
    txt(s, "next", bx + 2.05, 1.7, 0.5, 0.3, { size: 11, align: "center" });
  });
  txt(s, "NULL", 11.2, 1.55, 1.2, 1.05, { size: 18, bold: true, color: C.text1, valign: "middle" });
  const rows = [["File size S", "Chunks"], ["0", "1"], ["1 – 1,024", "1"], ["1,025 – 2,048", "2"], ["2,049 – 3,072", "3"]];
  txt(s, "Chunks used = max(1, ceil(S / 1,024))", 0.6, 3.05, 5.6, 0.4, { bold: true, color: C.text1, size: 16 });
  s.addTable(rows.map((r, i) => r.map((c) => ({ text: c, options: i === 0 ? { bold: true, color: C.background1, fill: { color: C.text1 } } : { fill: { color: i % 2 ? HEX.lt2 : "FFFFFF" } } }))), {
    x: 0.6, y: 3.55, w: 5.6, colW: [3.4, 2.2], rowH: 0.42, fontSize: 14, color: HEX.dk1, border: { type: "solid", pt: 0.5, color: "D5DCE2" }, valign: "middle",
  });
  box(s, "", 6.7, 3.05, 6.0, 3.1, { fill: C.background2 });
  txt(s, "Reading across a boundary", 6.95, 3.2, 5.5, 0.4, { bold: true, color: C.text1, size: 16 });
  txt(s, "read_from_file(\"report\", 1019, 10)", 6.95, 3.65, 5.5, 0.35, { size: 14, font: "Courier New" });
  box(s, "…AAAAA", 6.95, 4.2, 2.6, 0.6, { fill: C.accent4, color: C.background1, font: "Courier New", bold: true, size: 15 });
  box(s, "BBBBB…", 9.6, 4.2, 2.6, 0.6, { fill: C.accent6, color: C.background1, font: "Courier New", bold: true, size: 15 });
  txt(s, "last 5 B of A", 6.95, 4.85, 2.6, 0.3, { size: 12, align: "center" });
  txt(s, "first 5 B of B", 9.6, 4.85, 2.6, 0.3, { size: 12, align: "center" });
  txt(s, "→ b'AAAAABBBBB' · every chunk's HMAC is verified, then the chain is decrypted in order and sliced", 6.95, 5.25, 5.5, 0.8, { size: 13 });
  s.addNotes("Each chunk has its own random name, key and IV. The meta file lists the chunks in order with each key and HMAC, so the chain can be walked and verified link by link.");

  const w = content("Simulation: inserting \"xyz\" at position 10 safely", "Part 3");
  const steps = [
    "Verify every chunk HMAC and decrypt the chain (2,548 B)",
    "Build old[:10] + \"xyz\" + old[10:] → 2,551 B",
    "Re-split into ceil(2,551 / 1,024) = 3 chunks",
    "New random name, key and IV for every chunk; write them",
    "Save the new meta atomically and update the masterlist digest",
    "Only now delete the three old chunks",
  ];
  steps.forEach((t2, i) => {
    const y = 1.5 + i * 0.8;
    circleNum(w, i + 1, 0.6, y + 0.1, 0.48, i === 4 ? C.accent2 : C.accent1);
    box(w, t2, 1.25, y, 6.75, 0.68, { fill: C.background2, align: "left", size: 15, margin: 10 });
  });
  box(w, [
    { text: "Crash safety", options: { bold: true, fontSize: 17, breakLine: true } },
    { text: "A crash before step 5 leaves the old meta pointing at the old, intact chunks. After step 5 the new version is complete. A half-written file can never exist." },
  ], 8.4, 1.5, 4.3, 2.55, { fill: C.accent1, color: C.background1, size: 15, align: "left", valign: "top", margin: 12 });
  box(w, [
    { text: "Appending to a partial chunk", options: { bold: true, fontSize: 17, breakLine: true } },
    { text: "512 B + 200 B = 712 B: still one chunk, because ceil(712 / 1,024) = 1." },
  ], 8.4, 4.25, 4.3, 1.75, { fill: C.background2, size: 15, align: "left", valign: "top", margin: 12 });
  txt(w, "Result: read_from_file(\"report\", 8, 7) → b'AAxyzAA'", 0.6, 6.35, 12.1, 0.4, { size: 14, font: "Courier New", bold: true, color: C.text1 });
  w.addNotes("write_to_file inserts: later content shifts forward. Old chunks are deleted only after the new meta file is saved, which is the step that commits the change.");

  const t = content("Tampering simulation: every attack we tried was caught", "Part 3");
  const attacks = [
    ["Modify any byte", "HMAC mismatch"], ["Delete a chunk", "chunk file cannot be read"],
    ["Swap two chunks", "each checked under the other's key → HMAC mismatch"], ["Edit a next-link", "chunk changes → HMAC mismatch"],
    ["Add an extra chunk", "count must equal ceil(size / 1,024)"], ["Edit the meta file", "SHA-256 ≠ masterlist digest"],
    ["Change start/end name", "must equal first and last chunk"], ["Fake the size fields", "chunk sizes must add up"],
  ];
  attacks.forEach(([a, dct], i) => {
    const x = 0.6 + (i % 4) * 3.08, y = 1.4 + Math.floor(i / 4) * 1.5;
    box(t, "", x, y, 2.85, 1.35, { fill: C.background2 });
    txt(t, a, x + 0.2, y + 0.12, 2.5, 0.4, { bold: true, color: C.accent3, size: 15 });
    txt(t, dct, x + 0.2, y + 0.55, 2.5, 0.75, { size: 14 });
  });
  txt(t, "Run in the recorded demo (logs/part_3_log): the health check returned 1 before each attack", 0.6, 4.5, 12.1, 0.35, { size: 14, bold: true, color: C.text1 });
  [
    ["Flip one bit in a chunk", "system_health_check → -1\nfile_integrity_check shows the file"],
    ["Swap chunks A and B", "file_integrity_check → -1\nread_from_file → None"],
    ["Delete chunk C", "file_integrity_check → -1"],
  ].forEach(([a, r], i) => {
    const x = 0.6 + i * 4.13;
    box(t, a, x, 5.0, 3.85, 0.55, { fill: C.accent3, color: C.background1, bold: true, size: 15 });
    box(t, r, x, 5.6, 3.85, 0.95, { fill: C.text1, color: C.background1, size: 14 });
  });
  t.addNotes("Top: how each kind of tampering is detected (by the code, and covered by the acceptance tests). Bottom: the three attacks run in the recorded Part 3 demo. After each one was undone, the health check returned 1 again.");
}

// ======================================================================
// DECISIONS, TESTING, LIMITATIONS, CLOSE
// ======================================================================
function decisions() {
  divider("05", "Design decisions and justification", "Decisions", ["Cryptographic choices and why", "Engineering choices and why", "Verification: automated tests", "Known limitations, stated openly"]);

  const s = content("Cryptographic choices and why", "Decisions");
  const rows = [
    ["AES-128-CTR for chunks and meta", "Required by the brief. No padding, so no padding-oracle attacks; any byte can be reached directly."],
    ["New random key and IV on every chunk write", "Reusing a CTR key + IV reuses the keystream, which leaks the XOR of two plaintexts."],
    ["Encrypt-then-MAC: HMAC-SHA256 over IV + ciphertext", "CTR gives secrecy but not integrity. A MAC on the ciphertext lets us reject tampering before decrypting."],
    ["Chunk key and HMAC kept in the encrypted meta", "Someone who edits a chunk cannot forge its tag; a chunk moved to another slot fails under the wrong key."],
    ["SHA-256 digest of each meta file in the masterlist", "Detects edits to the meta file itself."],
    ["PBKDF2-HMAC-SHA1 · 20,000 rounds · 32-byte salt", "Slows password guessing; per-user salts defeat precomputed tables."],
    ["OS CSPRNG (secrets) for keys, IVs, salts, names", "Python's random module is predictable and unsafe for keys."],
  ];
  const head = [{ text: "Decision", options: { bold: true, color: C.background1, fill: { color: C.text1 } } }, { text: "Why", options: { bold: true, color: C.background1, fill: { color: C.text1 } } }];
  s.addTable([head, ...rows.map(([a, b], i) => [
    { text: a, options: { bold: true, fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } } },
    { text: b, options: { fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } } },
  ])], { x: 0.6, y: 1.4, w: 12.1, colW: [4.7, 7.4], rowH: 0.62, fontSize: 14, color: HEX.dk1, border: { type: "solid", pt: 0.5, color: "D5DCE2" }, valign: "middle", margin: [0.04, 0.1, 0.04, 0.1] });
  s.addNotes("Each choice either follows the brief or closes a specific attack. The most important pair is fresh key + IV per write (secrecy in CTR mode) and verify-before-decrypt (integrity).");

  const e = content("Engineering choices and why", "Decisions");
  const cards = [
    ["Atomic writes everywhere", "Temp file + fsync + os.replace: a crash never leaves a half-written chunk, meta or passwd file."],
    ["Old data removed last", "The previous version stays valid until the new meta file is saved."],
    ["write_to_file inserts", "Later content shifts forward, as the brief describes; writing beyond the end is rejected."],
    ["Errors are -1 or None", "read_from_file returns None on any failure, so an error can never be mistaken for file data."],
    ["All constants in config.py", "Every format decision lives in one file, so answering a specification question changes one line."],
    ["Binary mode, \\n line endings", "Identical files on Windows and Linux, needed for exchanging files with other groups."],
  ];
  cards.forEach(([h, d], i) => {
    const x = 0.6 + (i % 3) * 4.13, y = 1.45 + Math.floor(i / 3) * 2.2;
    box(e, "", x, y, 3.85, 2.0, { fill: C.background2 });
    circleNum(e, i + 1, x + 0.22, y + 0.2, 0.45);
    txt(e, h, x + 0.8, y + 0.2, 2.9, 0.45, { bold: true, color: C.text1, size: 16, valign: "middle" });
    txt(e, d, x + 0.22, y + 0.8, 3.45, 1.15, { size: 14 });
  });
  txt(e, [
    { text: "Settled by the group (21 and 24 Nov 2026): ", options: { bold: true, color: C.text1 } },
    { text: "Q1 padding 0x00 · Q2 20-byte hash, lowercase hex · Q3 HMAC over IV + ciphertext · Q4 meta layout · Q5 32-hex chunk names · Q6 plaintext masterlist · Q7 HMAC checked first · Q8 username 6–31, password 9–31" },
  ], 0.6, 5.95, 12.1, 0.7, { size: 13 });
  e.addNotes("The open specification questions Q1–Q8 were settled by the group, keeping the documented values. Only Q9 (Part 4, the file exchange with another group) remains open.");
}

function testing() {
  const s = content("Verification: automated tests, all passing", "Testing");
  const data = [
    { label: "Part 1 · authentication", n: 5, on: DONE.part1 },
    { label: "Part 2 · file functions", n: 5, on: DONE.part2 },
    { label: "Part 3 · chunk chains", n: 3, on: DONE.part3 },
    { label: "Part 3 · tamper detection", n: 2, on: DONE.part3 },
    { label: "File-format known answers", n: 3, on: true },
  ].filter((d) => d.on).reverse();
  const total = data.reduce((a, d) => a + d.n, 0);
  s.addChart(pres.charts.BAR, [{ name: "Tests", labels: data.map((d) => d.label), values: data.map((d) => d.n) }], {
    x: 0.6, y: 1.4, w: 7.2, h: 4.9, barDir: "bar", chartColors: [HEX.accent1], barGapWidthPct: 60,
    showTitle: true, title: `Tests by area (${total} shown, all passing)`, titleFontSize: 16, titleColor: HEX.dk1, titleFontFace: "+mj-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 14, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 13, catAxisLabelColor: HEX.dk2, catAxisLabelFontFace: "+mn-lt",
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 6,
    valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
  });
  const notes = [
    ["Acceptance tests", "Every function: valid and invalid input, boundaries, ownership, tampering"],
    ["Known-answer format tests", "Hand-made passwd and chunk files are read correctly; written files match the documented byte layout"],
    ["Recorded demos", "Part 1: 13 · Part 2: 15 · Part 3: 24 checks, all as expected (logs/)"],
  ];
  notes.forEach(([h, d], i) => {
    const y = 1.5 + i * 1.5;
    circleNum(s, i + 1, 8.3, y, 0.45);
    txt(s, h, 8.95, y, 3.75, 0.45, { bold: true, color: C.text1, size: 16, valign: "middle" });
    txt(s, d, 8.95, y + 0.48, 3.75, 0.9, { size: 14 });
  });
  box(s, "python -m pytest tests\\acceptance tests\\format → 18 passed", 8.3, 6.0, 4.4, 0.55, { fill: C.text1, color: C.background1, size: 12, font: "Courier New" });
  s.addNotes(`The full suite (18 tests) passes. This chart shows the tests for the parts presented so far (${total}); the Part 3 tests are added to it when Part 3 is presented.`);
}

function limitations() {
  const s = content("Known limitations, stated openly", "Testing");
  const cards = [
    ["Same master key + IV for every meta file", "The brief specifies this, but in CTR mode it reuses the keystream: XORing two meta files leaks the XOR of their plaintexts. Fix: a fresh IV per meta file."],
    ["Plaintext masterlist", "File names are visible to anyone with access to the folder (contents stay encrypted)."],
    ["master.key stored unprotected", "Anyone who can read it can open every meta file. A real system would derive it from a password or use a key manager."],
    ["Whole file re-encrypted on each write", "Simple and always uses the minimum number of chunks, but the cost grows with file size."],
  ];
  cards.forEach(([h, d], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.45 + Math.floor(i / 2) * 2.35;
    box(s, "", x, y, 5.95, 2.15, { fill: C.background2 });
    circleNum(s, "!", x + 0.22, y + 0.2, 0.45, C.accent3);
    txt(s, h, x + 0.85, y + 0.2, 4.9, 0.45, { bold: true, color: C.text1, size: 16, valign: "middle" });
    txt(s, d, x + 0.22, y + 0.8, 5.5, 1.3, { size: 14 });
  });
  txt(s, "Still open: Q9, how test files are exchanged with a partner group (Part 4). Q1–Q8 are settled.", 0.6, 6.3, 12.1, 0.4, { size: 13, italic: true });
  s.addNotes("The first limitation is the most important for the report: the code follows the specification as written, and the weakness is raised as a limitation rather than silently changed.");
}

function closing() {
  const s = newSlide("TITLE", "Next steps");
  titleText(s, "Summary and next steps", { x: 0.7, y: 1.5, w: 11.9, h: 1.5, fontSize: 44, color: "FFFFFF", valign: "bottom" });
  s.addText("Parts 1–3 and the extension complete; Part 4 next", { isTextBox: true, x: 0.7, y: 3.15, w: 11.9, h: 0.7, margin: 0, fontSize: 22, color: "B9C6D1" });
  const done = [
    "Parts 1–3 built, tested (18/18) and demonstrated (52/52 checks)",
    "Salted, slow password hashes; per-chunk encryption verified before decryption",
    "Every operation fails closed; every save is crash-safe",
  ];
  if (DONE.extension) done.push("Extension: AI-assisted tests caught 70% of seeded faults vs 25% manual");
  const next = [];
  if (!DONE.part3) next.push("Part 3: complete, demonstrate and log multi-chunk files");
  if (!DONE.part4) next.push("Part 4: exchange files with a partner group (Q9)");
  if (!DONE.extension) next.push("Extension: run the AI vs manual testing experiment");
  txt(s, "Achieved", 0.7, 4.2, 5.8, 0.4, { bold: true, color: HEX.accent1, size: 18 });
  txt(s, done.map((d, i) => ({ text: d, options: { bullet: true, breakLine: i < done.length - 1 } })), 0.7, 4.7, 5.9, 2.2, { size: 15, color: "D6DEE5", psa: 6 });
  txt(s, "Next", 6.95, 4.2, 5.7, 0.4, { bold: true, color: HEX.accent2, size: 18 });
  txt(s, next.map((d, i) => ({ text: d, options: { bullet: true, breakLine: i < next.length - 1 } })), 6.95, 4.7, 5.7, 2.2, { size: 15, color: "D6DEE5", psa: 6 });
  s.addNotes("Close on what is proven so far and what comes next. This slide's 'Next' list updates automatically from the DONE flags in build_slides.js.");
}

// ======================================================================
// SYSTEM DESIGN AND FLOW (extra architecture slides)
// ======================================================================
function slideContext() {
  const s = content("System context: who uses SEFS, and who it defends against", "Architecture");
  const row = [
    ["User", "e.g. alice01, with a password", C.accent4],
    ["Python API / CLI", "import sefs · python -m sefs", C.accent4],
    ["SEFS", "auth.py + fs.py: every call checks password, owner, integrity", C.accent1],
    ["Working folder", "passwd, master.key, masterlist,\nmeta files, chunks/", C.text1],
  ];
  row.forEach(([h, t2, col], i) => {
    const x = 0.6 + i * 3.1;
    box(s, hd(h, t2, 12), x, 1.45, 2.8, 1.1, { fill: col, color: C.background1, size: 15 });
    if (i < 3) arrow(s, x + 2.83, 2.0, x + 3.07, 2.0);
  });
  box(s, hd("Attacker with access to the folder", "reads, edits, deletes or swaps files on disk", 12), 9.9, 3.0, 2.8, 1.0, { fill: C.accent3, color: C.background1, size: 14 });
  arrow(s, 11.3, 2.97, 11.3, 2.6, HEX.accent3);
  box(s, hd("Another valid user", "logged in, but not the file's owner", 12), 6.8, 3.0, 2.8, 1.0, { fill: C.accent3, color: C.background1, size: 14 });
  arrow(s, 8.2, 2.97, 8.2, 2.6, HEX.accent3);
  txt(s, "Defended (in scope)", 0.6, 4.3, 6, 0.4, { bold: true, color: C.accent1, size: 16 });
  const inS = [
    "Reading file contents on disk → everything stored is encrypted",
    "Editing, swapping or deleting chunks or meta files → HMACs, digest and chain checks",
    "Using someone else's files → password check plus owner check",
    "A crash in the middle of a save → atomic writes keep the last good version",
  ];
  txt(s, inS.map((x, i) => ({ text: x, options: { bullet: true, breakLine: i < inS.length - 1 } })), 0.6, 4.75, 6.4, 2.0, { size: 13, color: C.text1, psa: 4 });
  txt(s, "Not defended (out of scope)", 7.3, 4.3, 5.4, 0.4, { bold: true, color: C.accent3, size: 16 });
  const outS = [
    "An attacker who also has master.key",
    "Data in memory while SEFS is running",
    "Deleting everything (denial of service)",
    "File names, visible in the plaintext masterlist",
  ];
  txt(s, outS.map((x, i) => ({ text: x, options: { bullet: true, breakLine: i < outS.length - 1 } })), 7.3, 4.75, 5.4, 2.0, { size: 13, color: C.text1, psa: 4 });
  s.addNotes("The threat model: SEFS protects data at rest against someone who can read and change the files in the folder, and against other users of the same system. Keeping master.key safe is outside the scope of the assignment.");
}

function slideDataModel() {
  const s = content("Data model: how the stored files fit together", "Architecture");
  box(s, hd("masterlist", "report → SHA-256(report.meta)", 12), 0.6, 1.45, 2.7, 0.95, { fill: C.background2, size: 15 });
  arrow(s, 3.33, 1.925, 3.67, 1.925);
  txt(s, "digest", 3.3, 1.55, 0.4, 0.3, { size: 10, align: "center" });
  box(s, hd("report.meta", "owner, count, size, start/end\nname + key + HMAC per chunk", 11), 3.7, 1.45, 3.1, 0.95, { fill: C.text1, color: C.background1, size: 15 });
  arrow(s, 6.83, 1.925, 7.17, 1.925);
  ["A", "B", "C"].forEach((n, i) => {
    const x = 7.2 + i * 1.6;
    box(s, hd(`chunk ${n}`, "1,076 B", 11), x, 1.45, 1.3, 0.95, { fill: C.accent4, color: C.background1, size: 14 });
    arrow(s, x + 1.33, 1.925, x + 1.57, 1.925);
  });
  txt(s, "NULL", 12.0, 1.45, 0.7, 0.95, { bold: true, size: 14, color: C.text1, valign: "middle" });
  box(s, hd("master.key", "16-byte key + 16-byte IV", 12), 3.95, 2.85, 2.6, 0.85, { fill: C.accent2, color: C.background1, size: 14 });
  arrow(s, 5.25, 2.82, 5.25, 2.43, HEX.accent2);
  txt(s, "decrypts every meta file", 5.4, 2.5, 2.4, 0.3, { size: 11 });
  box(s, hd("passwd", "alice01:salt:hash\nchecked on every call", 12), 0.6, 2.85, 2.7, 0.85, { fill: C.background2, size: 14 });
  txt(s, "The meta file's owner must equal the logged-in user", 0.6, 3.75, 3.3, 0.4, { size: 11, italic: true });
  const H = (t2) => ({ text: t2, options: { bold: true, color: C.background1, fill: { color: C.text1 } } });
  const rows = [
    ["passwd", "username, 32-byte salt, PBKDF2 hash", "one-way hash: no password to steal"],
    ["master.key", "master key and IV", "file permissions only (a stated limitation)"],
    ["masterlist", "file name + SHA-256 of its meta file", "plaintext; the digest exposes edited meta files"],
    ["<name>.meta", "owner, chunk count, size, start/end, each chunk's name, key and HMAC", "AES-128-CTR under the master key"],
    ["chunks/<32 hex>", "IV + encrypted (next name, size, 1,024 B content)", "AES-128-CTR under its own key; HMAC kept in the meta"],
  ];
  s.addTable([[H("File"), H("Holds"), H("Protected by")], ...rows.map((r, i) => r.map((c, j) => ({
    text: c, options: { bold: j === 0, fontFace: j === 0 ? "Courier New" : undefined, fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } },
  })))], { x: 0.6, y: 4.2, w: 12.1, colW: [2.2, 5.3, 4.6], rowH: 0.4, fontSize: 12, color: HEX.dk1, border: { type: "solid", pt: 0.5, color: "D5DCE2" }, valign: "middle", margin: [0.03, 0.1, 0.03, 0.1] });
  s.addNotes("Every stored file has one job. The masterlist anchors the meta files, each meta file anchors its chunks, and the master key opens the meta files. Nothing about a file can change without one of these links breaking.");
}

function slideKeys() {
  const s = content("Key hierarchy: which secret protects what", "Architecture");
  const chains = [
    ["User password", "PBKDF2-HMAC-SHA1 · own 32-byte salt · 20,000 rounds", "Stored hash in passwd: login check only, never used to encrypt", C.accent4],
    ["master.key (key + IV)", "AES-128-CTR", "Every .meta file, which holds all chunk keys and HMACs", C.accent2],
    ["Chunk key (random, new every write)", "AES-128-CTR with a random IV", "That chunk's next name, size and content", C.accent1],
    ["Chunk key (same)", "HMAC-SHA256 over IV + ciphertext", "That chunk's tag, stored in the encrypted meta", C.accent1],
    ["No key", "SHA-256 of the stored meta bytes", "The meta digest in the masterlist", "8A99A6"],
  ];
  txt(s, "Secret", 0.6, 1.3, 3.3, 0.3, { bold: true, size: 13, color: C.text1 });
  txt(s, "Algorithm", 4.4, 1.3, 3.6, 0.3, { bold: true, size: 13, color: C.text1 });
  txt(s, "Protects", 8.5, 1.3, 4.2, 0.3, { bold: true, size: 13, color: C.text1 });
  chains.forEach(([a, b, c, col], i) => {
    const y = 1.7 + i * 0.86;
    box(s, a, 0.6, y, 3.3, 0.7, { fill: col, color: C.background1, bold: true, size: 14 });
    arrow(s, 3.93, y + 0.35, 4.37, y + 0.35);
    box(s, b, 4.4, y, 3.6, 0.7, { fill: C.background2, size: 13 });
    arrow(s, 8.03, y + 0.35, 8.47, y + 0.35);
    box(s, c, 8.5, y, 4.2, 0.7, { fill: C.background2, size: 13, align: "left", margin: 8 });
  });
  box(s, [
    { text: "What a leak costs: ", options: { bold: true } },
    { text: "a leaked chunk key exposes one chunk version only, because the next write uses a new key. A leaked master.key exposes every meta file, and therefore every chunk key, which is why it is the most sensitive file." },
  ], 0.6, 6.05, 12.1, 0.75, { fill: C.text1, color: C.background1, size: 13, align: "left", margin: 10 });
  s.addNotes("Two separate concerns: the password proves who you are (authentication), and the keys keep data secret and tamper-evident (confidentiality and integrity). The password is never used as an encryption key.");
}

function slideFlows() {
  const s = content("End-to-end flows: writing and reading a file", "Architecture");
  const write = [
    ["Check user", "password + owner"], ["Verify chain", "HMACs, then decrypt"], ["Insert bytes", "later content shifts"],
    ["Split", "1,024-byte blocks"], ["Encrypt", "new key + IV, HMAC"], ["Save meta", "atomic + masterlist"], ["Clean up", "delete old chunks"],
  ];
  const read = [
    ["Check user", "password + owner"], ["Meta digest", "matches masterlist?"], ["HMAC each chunk", "before decrypting"],
    ["Decrypt", "chunks in order"], ["Check chain", "links, count, size"], ["Return", "requested bytes"],
  ];
  const lane = (label, steps, y, col) => {
    txt(s, label, 0.6, y, 12, 0.4, { bold: true, color: col, size: 16 });
    const n = steps.length, gap = 0.26, w = (12.1 - gap * (n - 1)) / n;
    steps.forEach(([h, t2], i) => {
      const x = 0.6 + i * (w + gap);
      box(s, hd(h, t2, 11), x, y + 0.45, w, 1.15, { fill: i === n - 1 ? col : C.background2, color: i === n - 1 ? C.background1 : C.text1, size: 13 });
      if (i < n - 1) arrow(s, x + w + 0.02, y + 1.025, x + w + gap - 0.02, y + 1.025);
    });
  };
  lane("write_to_file(f, position, data, u, p)", write, 1.35, HEX.accent1);
  lane("read_from_file(f, position, length, u, p)", read, 3.35, HEX.accent4);
  box(s, [
    { text: "Shared rule: ", options: { bold: true } },
    { text: "both paths use the same checks, in the same order. Any failure stops at once with -1 (or None for reads), before data is changed or returned. Only the final atomic save makes a write visible." },
  ], 0.6, 5.45, 12.1, 0.95, { fill: C.background2, size: 14, align: "left", margin: 12 });
  s.addNotes("encrypt_file and decrypt_file follow the same two paths: encrypt starts at Split with data from a plaintext file; decrypt runs the whole read path and writes the result to a file instead of returning it.");
}

function slideFunctions() {
  const s = content("The fourteen functions at a glance", "Architecture");
  const H = (t2) => ({ text: t2, options: { bold: true, color: C.background1, fill: { color: C.text1 } } });
  const group = (t2) => [{ text: t2, options: { bold: true, color: C.background1, fill: { color: C.accent1 }, colspan: 3 } }];
  const f = (name, what, ret, i) => [
    { text: name, options: { fontFace: "Courier New", bold: true, fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } } },
    { text: what, options: { fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } } },
    { text: ret, options: { fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } } },
  ];
  const p1 = [
    ["register_user(u, p, pFile)", "Add a user with a fresh salt and hash", "1 / -1"],
    ["delete_user(u, p, pFile)", "Remove a user, only with the right password", "1 / -1"],
    ["is_user_valid(u, pFile)", "Does this username exist?", "1 / -1"],
    ["match_user(u, p, pFile)", "Login: re-hash and compare in constant time", "1 / -1"],
    ["change_user_password(u, p, pn, pFile)", "New password with a fresh salt, only with the old one", "1 / -1"],
  ];
  const p2 = [
    ["create_file(f, u, p)", "New empty file: one chunk, size 0", "1 / -1"],
    ["encrypt_file(f, u, p)", "Store a plaintext file from disk, encrypted", "1 / -1"],
    ["decrypt_file(f, pf, u, p)", "Verify, then write the plaintext to file pf", "1 / -1"],
    ["read_from_file(f, pos, n, u, p)", "n bytes from pos, after full verification", "bytes / None"],
    ["write_to_file(f, pos, data, u, p)", "Insert data at pos, re-encrypt with fresh keys", "1 / -1"],
    ["file_size(f, u, p)", "Size from the verified meta file", "size / -1"],
    ["file_integrity_check(f, u, p)", "Recheck digest, every HMAC and every link", "1 / -1"],
    ["delete_file(f, u, p)", "Owner only: remove chunks, meta and list entry", "1 / -1"],
    ["system_health_check(u, p)", "Integrity-check every file in the masterlist", "1 / -1"],
  ];
  const rows = [[H("Function"), H("What it does"), H("Returns")], group("Part 1 · authentication (auth.py)"),
    ...p1.map((r, i) => f(...r, i)), group("Parts 2–3 · encrypted files (fs.py)"), ...p2.map((r, i) => f(...r, i))];
  s.addTable(rows, { x: 0.6, y: 1.3, w: 12.1, colW: [4.4, 5.9, 1.8], rowH: 0.31, fontSize: 12, color: HEX.dk1, border: { type: "solid", pt: 0.5, color: "D5DCE2" }, valign: "middle", margin: [0.02, 0.08, 0.02, 0.08] });
  s.addNotes("Every file function starts with the Part 1 password check, so authentication is built into all of Parts 2 and 3.");
}

// ======================================================================
// SECURITY GOALS (CIA)
// ======================================================================
function securityGoals() {
  const s = content("Security goals: what SEFS protects and how", "Architecture");
  const cols = [
    {
      letter: "C", name: "Confidentiality", tag: "Only ciphertext ever reaches the disk", color: C.accent1,
      how: [
        "AES-128-CTR on every chunk and every meta file",
        "Fresh random key and IV on every chunk write, so no keystream is reused",
        "Chunk keys exist only inside the encrypted meta file",
        "Passwords are never stored, only a salted PBKDF2 hash",
      ],
      where: "Parts 1–3", proof: "Hex dump of a chunk shows no plaintext",
    },
    {
      letter: "I", name: "Integrity", tag: "Any change is caught before data is used", color: C.accent2,
      how: [
        "HMAC-SHA256 on every chunk, checked before decrypting",
        "SHA-256 of each meta file stored in the masterlist",
        "Chain checks: links, chunk count, sizes, start and end",
        "Atomic writes, so a crash never leaves a half-written file",
      ],
      where: "Parts 2–3", proof: "Flipped bit, swapped and missing chunks all return -1",
    },
    {
      letter: "A", name: "Authentication", tag: "Only the right user, only their own files", color: C.accent4,
      how: [
        "Password checked on every call (PBKDF2, constant-time compare)",
        "Ownership check: only the owner can read, write or delete",
        "Strict username and password rules",
        "A wrong password changes nothing on disk",
      ],
      where: "Parts 1–2", proof: "Wrong password and mallory1's delete both return -1",
    },
  ];
  cols.forEach((c2, i) => {
    const x = 0.6 + i * 4.13, w = 3.85;
    box(s, "", x, 1.4, w, 1.15, { fill: c2.color });
    s.addText(c2.letter, { shape: SH.OVAL, x: x + 0.2, y: 1.55, w: 0.85, h: 0.85, fill: { color: C.background1 }, line: { color: C.background1 }, color: c2.color, bold: true, fontSize: 28, fontFace: THEME.headFontFace, align: "center", valign: "middle", margin: 0 });
    txt(s, [
      { text: c2.name, options: { bold: true, fontSize: 19, breakLine: true } },
      { text: c2.tag, options: { fontSize: 12 } },
    ], x + 1.2, 1.5, w - 1.35, 0.95, { color: C.background1, valign: "middle" });
    box(s, "", x, 2.6, w, 3.3, { fill: C.background2, r: 0.06 });
    txt(s, c2.how.map((h, j) => ({ text: h, options: { bullet: true, breakLine: j < c2.how.length - 1 } })), x + 0.2, 2.75, w - 0.35, 2.3, { size: 14, color: C.text1, psa: 5 });
    txt(s, [
      { text: `${c2.where} · Proved: `, options: { bold: true, color: C.text1 } },
      { text: c2.proof },
    ], x + 0.2, 5.1, w - 0.35, 0.7, { size: 12, valign: "bottom" });
  });
  txt(s, [
    { text: "Note on the triad: ", options: { bold: true, color: C.text1 } },
    { text: "the classic CIA triad's A is Availability. SEFS supports it only in part: crash-safe writes keep the last good version and the health check finds damage, but there are no backups, so a deleted chunk makes its file unreadable." },
  ], 0.6, 6.05, 12.1, 0.75, { size: 12 });
  s.addNotes("Confidentiality comes from AES-CTR with fresh keys and IVs; integrity from HMACs, the meta digest and the chain checks, always verified before decryption; authentication from the salted, slow password hash and the owner check on every call. Strictly, the A in the CIA triad is Availability; we address it only partially, as the note says.");
}

// ======================================================================
// EXTENSION: AI-ASSISTED VS MANUAL TEST GENERATION (results from analysis/results.md)
// ======================================================================
function extension() {
  const SEC = "Extension";
  divider("06", "Extension · AI-assisted vs manual test generation", SEC, ["Research question and fair design", "The three arms and the 20 seeded faults", "How scoring works", "Results: full table, detection, coverage, time", "Faults every arm missed", "Intent vs delivered", "Threats to validity", "Conclusions and recommendations"]);

  // ---- research question and design ----
  const d = content("The question, and how we tested it fairly", SEC);
  box(d, [
    { text: "Research question", options: { bold: true, fontSize: 15, color: HEX.accent2, breakLine: true } },
    { text: "Does AI-assisted test generation find more implementation defects than manually designed tests under a fixed time budget?", options: { fontSize: 17, breakLine: true } },
    { text: " ", options: { fontSize: 8, breakLine: true } },
    { text: "H0: both find the same share of seeded faults.  H1: the shares differ.", options: { fontSize: 14, italic: true } },
  ], 0.6, 1.4, 12.1, 1.55, { fill: C.text1, color: C.background1, align: "left", margin: 14 });
  const steps = [
    ["Freeze", "code tagged sefs-v1.0"],
    ["Seed faults", "Pascal writes 20 hidden bugs, 5 per area"],
    ["Manual arm", "Daniel, no AI, 120 min"],
    ["AI arm", "Claude proposes tests, Daniel reviews"],
    ["Score", "every suite run against every fault"],
  ];
  steps.forEach(([h, t2], i) => {
    const x = 0.6 + i * 2.48;
    box(d, hd(h, t2, 13), x, 3.3, 2.2, 1.35, { fill: i === 1 ? C.accent3 : i === 3 ? C.accent1 : C.background2, color: i === 1 || i === 3 ? C.background1 : C.text1, size: 15 });
    if (i < 4) arrow(d, x + 2.23, 3.975, x + 2.45, 3.975);
  });
  const ctl = [
    ["Faults stay hidden", "The tester never sees them; they are git-ignored and scored only at the end."],
    ["AI kept isolated", "The AI sees only the specification and fixtures, never the code, faults or manual tests."],
    ["Manual first", "Manual tests are written before any AI output exists, so the AI cannot influence them."],
  ];
  ctl.forEach(([h, t2], i) => {
    const x = 0.6 + i * 4.13;
    circleNum(d, i + 1, x, 5.0, 0.42);
    txt(d, [
      { text: h, options: { bold: true, color: C.text1, fontSize: 15, breakLine: true } },
      { text: t2, options: { fontSize: 13 } },
    ], x + 0.55, 4.97, 3.4, 1.3);
  });
  d.addNotes("The design follows docs/EXPERIMENT.md. Seeded faults are the held-out evaluation set, like a test set in machine learning: both arms are scored against the same 20 faults.");

  // ---- the three arms ----
  const a = content("Three arms, scored against the same 20 faults", SEC);
  const H = (t2) => ({ text: t2, options: { bold: true, color: C.background1, fill: { color: C.text1 } } });
  const rowsA = [
    ["manual", "Daniel, by hand, no AI", "8 tests", "160 min (120 + 40 over budget)"],
    ["ai/run1", "Fresh Claude agent proposes; Daniel reviews in a walkthrough", "132 functions, 340 cases", "50 min review (+ 6.5 min machine generation)"],
    ["manual_extended", "Daniel, extra tests after the budget", "5 tests", "100 min"],
  ];
  a.addTable([[H("Arm"), H("Who writes the tests"), H("Tests"), H("Tester time")], ...rowsA.map((r, i) => r.map((c, j) => ({
    text: c, options: { bold: j === 0, fontFace: j === 0 ? "Courier New" : undefined, fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } },
  })))], { x: 0.6, y: 1.4, w: 12.1, colW: [2.2, 4.6, 2.4, 2.9], rowH: 0.6, fontSize: 14, color: HEX.dk1, border: { type: "solid", pt: 0.5, color: "D5DCE2" }, valign: "middle", margin: [0.04, 0.1, 0.04, 0.1] });
  const areas = [["Authentication", "M01–M05"], ["Round trip", "M06–M10"], ["Chunk boundaries", "M11–M15"], ["Tamper", "M16–M20"]];
  txt(a, "The 20 seeded faults: small, realistic bugs, 5 per area", 0.6, 4.2, 12.1, 0.4, { bold: true, color: C.text1, size: 16 });
  areas.forEach(([h, ids], i) => {
    box(a, hd(h, ids, 13), 0.6 + i * 3.08, 4.7, 2.85, 0.95, { fill: C.accent3, color: C.background1, size: 15 });
  });
  txt(a, "A fault counts as detected when at least one test in the suite fails on the faulty copy of the code. Every suite passed on the unchanged code first.", 0.6, 5.95, 12.1, 0.7, { size: 14 });
  a.addNotes("Daniel had no IT background, so all three arms measure a beginner tester. The AI arm used an isolated Claude Opus 5.5 agent instead of the claude.ai chat that was planned; the review was a 45-minute group walkthrough.");

  // ---- how scoring works ----
  const sc = content("How a suite is scored against the hidden faults", SEC);
  const flow = [
    ["Copy the code", "a fresh temporary copy of src/sefs for each fault"],
    ["Insert one bug", "apply the fault's find/replace edit to the copy"],
    ["Run the suite", "every test in the arm, against the faulty copy"],
    ["Record", "any test fails → detected; all pass → missed"],
  ];
  flow.forEach(([h, t2], i) => {
    const y = 1.45 + i * 1.15;
    circleNum(sc, i + 1, 0.6, y + 0.22, 0.5, i === 3 ? C.accent1 : C.accent2);
    box(sc, hd(h, t2, 13), 1.3, y, 4.5, 0.95, { fill: C.background2, align: "left", size: 15, margin: 10 });
  });
  txt(sc, "The real code is never changed. Before scoring, each suite must pass on the unchanged code, so a failure can only come from the bug.", 0.6, 6.15, 5.2, 0.7, { size: 12, italic: true });
  box(sc, "", 6.2, 1.45, 6.5, 4.2, { fill: "1E2A36" });
  const mono2 = (t2, color = "D6DEE5", bold = false) => ({ text: t2, options: { fontFace: "Courier New", color, bold, fontSize: 11, breakLine: true } });
  txt(sc, [
    mono2("> python tools\\run_mutants.py --tests tests\\ai\\run1", "8FD3C7", true),
    mono2(" "),
    mono2("baseline: suite passes on the unmodified code", "8A99A6"),
    mono2("M01_AUTH_allowed_characters    detected", "8FD3C7"),
    mono2("M02_AUTH_password_check        detected", "8FD3C7"),
    mono2("M04_AUTH_delete_or_change_line missed", "F2A07B"),
    mono2("M06_ROUNDTRIP_read_returns...  detected", "8FD3C7"),
    mono2("M13_CHUNKS_middle_chunks_full  missed", "F2A07B"),
    mono2("M16_TAMPER_meta_digest_check   detected", "8FD3C7"),
    mono2("M20_TAMPER_padding_check       missed", "F2A07B"),
    mono2("...", "8A99A6"),
    mono2(" "),
    { text: "ai/run1:  14/20 faults detected", options: { fontFace: "Courier New", color: "F2C14E", bold: true, fontSize: 12, breakLine: true } },
    { text: "manual:    5/20 faults detected", options: { fontFace: "Courier New", color: "F2C14E", bold: true, fontSize: 12 } },
  ], 6.45, 1.65, 6.1, 4.8);
  sc.addNotes("Excerpt of the real scoring output (analysis/mutants_ai_run1.csv and mutants_manual.csv). This is mutation testing: the share of seeded bugs a suite catches is its mutation score.");

  // ---- headline result ----
  const r = content("Result: AI-assisted tests caught 70% of the faults, manual 25%", SEC);
  const big = [["25%", "manual", "5 of 20 faults", HEX.accent4], ["70%", "AI-assisted", "14 of 20 faults", HEX.accent1], ["0%", "manual extended", "0 of 20 faults", "8A99A6"]];
  big.forEach(([n, l, sub, col], i) => {
    const x = 0.6 + i * 2.75;
    txt(r, n, x, 1.5, 2.6, 1.1, { size: 60, bold: true, color: col, font: THEME.headFontFace });
    txt(r, [
      { text: l, options: { bold: true, color: C.text1, fontSize: 16, breakLine: true } },
      { text: sub, options: { fontSize: 14 } },
    ], x, 2.65, 2.6, 0.8);
  });
  box(r, "", 8.95, 1.45, 3.75, 4.25, { fill: C.background2 });
  txt(r, "AI-assisted vs manual", 9.2, 1.6, 3.3, 0.4, { bold: true, color: C.text1, size: 16 });
  txt(r, [
    { text: "Caught by both: 5", options: { breakLine: true } },
    { text: "Only by AI-assisted: 9", options: { breakLine: true } },
    { text: "Only by manual: 0", options: { breakLine: true } },
    { text: "Missed by both: 6", options: { breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "Difference: +45 points", options: { bold: true, breakLine: true } },
    { text: "95% CI +25 to +65 points", options: { breakLine: true } },
    { text: "McNemar exact p = 0.0039", options: { bold: true, color: HEX.accent1 } },
  ], 9.2, 2.1, 3.3, 3.4, { size: 15, psa: 4 });
  box(r, [
    { text: "Answer: ", options: { bold: true } },
    { text: "in this experiment, yes. The AI-assisted suite found every fault the manual suite found, plus nine more, in less tester time. H0 is rejected (p < 0.01)." },
  ], 0.6, 3.75, 8.0, 1.95, { fill: C.accent1, color: C.background1, size: 17, align: "left", margin: 14 });
  txt(r, "Source: analysis/results.md (20 faults scored in every arm; bootstrap 10,000 resamples, seed 2026)", 0.6, 6.05, 12.1, 0.35, { size: 11, italic: true });
  r.addNotes("McNemar's test uses only the faults one arm caught and the other missed: 9 versus 0. The confidence interval comes from resampling the 20 faults.");

  // ---- full results (from analysis/results.md) ----
  const fr = content("Results in full: every arm, every fault", SEC);
  const rowsR = [
    ["manual", "8", "5/20 (25%)", "11–47%", "70.9%", "47.1%", "5", "160"],
    ["ai/run1", "340", "14/20 (70%)", "48–86%", "87.7%", "77.3%", "1", "50"],
    ["manual_extended", "5", "0/20 (0%)", "0–16%", "36.8%", "9.7%", "0", "100"],
  ];
  fr.addTable([[H("Arm"), H("Tests"), H("Faults detected"), H("95% CI"), H("Line cov."), H("Branch cov."), H("False pos."), H("Minutes")],
    ...rowsR.map((rw, i) => rw.map((v2, j) => ({ text: v2, options: { bold: j === 0 || (i === 1 && j === 2), color: i === 1 && j === 2 ? HEX.accent1 : HEX.dk1, fontFace: j === 0 ? "Courier New" : undefined, fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } } })))],
    { x: 0.6, y: 1.35, w: 12.1, colW: [2.3, 1.0, 2.0, 1.4, 1.35, 1.45, 1.3, 1.3], rowH: 0.42, fontSize: 13, color: HEX.dk1, border: { type: "solid", pt: 0.5, color: "D5DCE2" }, valign: "middle", margin: [0.03, 0.1, 0.03, 0.1] });
  txt(fr, "Every fault, every arm", 0.6, 3.25, 6, 0.35, { bold: true, color: C.text1, size: 15 });
  const DET = {
    "manual": [7, 11, 12, 15, 17],
    "ai/run1": [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 15, 16, 17],
    "manual_extended": [],
  };
  const areaNames = ["Authentication", "Round trip", "Chunk boundaries", "Tamper"];
  const gx = 2.4, cw = 0.48, gap = 0.12;
  const cx = (n) => gx + (n - 1) * cw + Math.floor((n - 1) / 5) * gap;
  areaNames.forEach((an, ai) => {
    txt(fr, an, cx(ai * 5 + 1), 3.65, 5 * cw - 0.04, 0.3, { size: 11, bold: true, color: C.text2, align: "center" });
  });
  for (let n = 1; n <= 20; n++) {
    txt(fr, "M" + String(n).padStart(2, "0"), cx(n), 3.95, cw - 0.04, 0.28, { size: 10, align: "center", color: C.text2 });
  }
  Object.entries(DET).forEach(([arm, hits], ri) => {
    const y = 4.28 + ri * 0.5;
    txt(fr, arm, 0.6, y, 1.95, 0.44, { size: 12, bold: true, color: C.text1, font: "Courier New", valign: "middle" });
    for (let n = 1; n <= 20; n++) {
      const hit = hits.includes(n);
      fr.addShape(SH.RECTANGLE, { x: cx(n), y, w: cw - 0.04, h: 0.44, fill: { color: hit ? HEX.accent5 : "E4E9ED" }, line: { color: "FFFFFF", width: 0.5 } });
    }
    txt(fr, `${hits.length}/20`, cx(20) + cw + 0.1, y, 0.7, 0.44, { size: 12, bold: true, color: C.text1, valign: "middle" });
  });
  fr.addShape(SH.RECTANGLE, { x: 0.6, y: 5.9, w: 0.3, h: 0.22, fill: { color: HEX.accent5 }, line: { color: HEX.accent5 } });
  txt(fr, "detected", 0.98, 5.86, 1.2, 0.3, { size: 12 });
  fr.addShape(SH.RECTANGLE, { x: 2.1, y: 5.9, w: 0.3, h: 0.22, fill: { color: "E4E9ED" }, line: { color: "C9D2DA" } });
  txt(fr, "missed", 2.48, 5.86, 1.2, 0.3, { size: 12 });
  txt(fr, "Every manual catch was also an AI catch. Six faults (M04, M13, M14, M18, M19, M20) were missed by all three arms.", 3.7, 5.86, 9.0, 0.5, { size: 12, italic: true });
  txt(fr, [
    { text: "AI prompt/review log: ", options: { bold: true, color: C.text1 } },
    { text: "5 prompts · 132 tests proposed · 131 accepted · 1 edited · 0 rejected (logs/ai_prompt_log.csv).   " },
    { text: "Real defects in the unchanged code: ", options: { bold: true, color: C.text1 } },
    { text: "0 in every arm." },
  ], 0.6, 6.2, 12.1, 0.35, { size: 12 });
  txt(fr, "Source: analysis/results.md, produced by analysis/analyze.py from the scoring runs (95% CI = Wilson interval of the detection rate)", 0.6, 6.58, 12.1, 0.28, { size: 10, italic: true });
  fr.addNotes("This slide is a direct copy of analysis/results.md: the per-arm table and the per-fault table. Fault descriptions are in that file and on the 'Six faults escaped every arm' slide.");

  // ---- by area (native chart) ----
  const b = content("Detection by area: AI leads in authentication and round trips", SEC);
  b.addChart(pres.charts.BAR, [
    { name: "manual", labels: ["Authentication", "Round trip", "Chunk boundaries", "Tamper"], values: [0, 20, 60, 20] },
    { name: "AI-assisted", labels: ["Authentication", "Round trip", "Chunk boundaries", "Tamper"], values: [80, 100, 60, 40] },
    { name: "manual extended", labels: ["Authentication", "Round trip", "Chunk boundaries", "Tamper"], values: [0, 0, 0, 0] },
  ], {
    x: 0.6, y: 1.4, w: 7.6, h: 5.0, barDir: "col", barGrouping: "clustered", chartColors: [HEX.accent4, HEX.accent1, "B9C6D1"],
    showTitle: true, title: "Seeded faults detected (%)", titleFontSize: 16, titleColor: HEX.dk1, titleFontFace: "+mj-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt", dataLabelFormatCode: "0\"%\"",
    catAxisLabelFontSize: 13, catAxisLabelColor: HEX.dk2, catAxisLabelFontFace: "+mn-lt",
    valAxisMinVal: 0, valAxisMaxVal: 110, valAxisMajorUnit: 20, valAxisLabelFontSize: 11, valAxisLabelColor: HEX.dk2, valAxisLabelFormatCode: "0\"%\"",
    valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 13, legendFontFace: "+mn-lt", legendColor: HEX.dk2,
  });
  const notes = [
    ["Authentication 0% → 80%", "The AI systematically tried boundary lengths and odd characters; the manual suite had one registration test."],
    ["Round trip 20% → 100%", "AI tests stored data and read it back; most manual round-trip tests ended up checking only rejected names."],
    ["Chunk boundaries 60% = 60%", "The one area where the manual tests matched the AI."],
    ["Tamper 20% → 40%", "Both arms damaged chunk files; neither probed sizes, lengths or padding in detail."],
  ];
  notes.forEach(([h, t2], i) => {
    txt(b, [
      { text: h, options: { bold: true, color: C.text1, fontSize: 15, breakLine: true } },
      { text: t2, options: { fontSize: 13 } },
    ], 8.6, 1.5 + i * 1.25, 4.1, 1.15);
  });
  b.addNotes("Each area has 5 faults, so one fault is 20 percentage points.");

  // ---- coverage, false positives, time ----
  const c = content("Coverage, false positives and time", SEC);
  const rowsC = [
    ["Faults detected", "5/20 (25%)", "14/20 (70%)", "0/20 (0%)"],
    ["Line coverage", "70.9%", "87.7%", "36.8%"],
    ["Branch coverage", "47.1%", "77.3%", "9.7%"],
    ["False positives (test wrong, code right)", "5", "1", "0"],
    ["Real defects found in the unchanged code", "0", "0", "0"],
    ["Tester time", "160 min", "50 min", "100 min"],
    ["Faults detected per tester hour", "1.9", "16.8", "0"],
    ["AI prompts / tests proposed / accepted / edited / rejected", "–", "5 / 132 / 131 / 1 / 0", "–"],
  ];
  c.addTable([[H("Measure"), H("manual"), H("AI-assisted"), H("manual extended")], ...rowsC.map((rw, i) => rw.map((v, j) => ({
    text: v, options: { bold: j === 0 || (j === 2 && i < 3), color: j === 2 && i < 3 ? HEX.accent1 : HEX.dk1, fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } },
  })))], { x: 0.6, y: 1.4, w: 12.1, colW: [5.3, 2.1, 2.6, 2.1], rowH: 0.5, fontSize: 14, color: HEX.dk1, border: { type: "solid", pt: 0.5, color: "D5DCE2" }, valign: "middle", margin: [0.04, 0.1, 0.04, 0.1] });
  txt(c, "Times are the tester's own estimates (not timed). The AI agent's 6.5 minutes of generation are machine time and not included.", 0.6, 6.15, 12.1, 0.5, { size: 12, italic: true });
  c.addNotes("All 6 false positives were tests that disagreed with the specification, not bugs in the code: wrong file names, a too-short password, a missing argument, an empty chunk list, and one AI miscount of a byte position.");

  // ---- coverage chart + analysis figure ----
  const g = content("Evidence from the analysis tools", SEC);
  g.addChart(pres.charts.BAR, [
    { name: "Line coverage", labels: ["manual", "AI-assisted", "manual ext."], values: [70.9, 87.7, 36.8] },
    { name: "Branch coverage", labels: ["manual", "AI-assisted", "manual ext."], values: [47.1, 77.3, 9.7] },
  ], {
    x: 0.6, y: 1.4, w: 5.9, h: 4.6, barDir: "col", barGrouping: "clustered", chartColors: [HEX.accent1, HEX.accent2],
    showTitle: true, title: "Code coverage of src/sefs (%)", titleFontSize: 15, titleColor: HEX.dk1, titleFontFace: "+mj-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt", dataLabelFormatCode: "0\"%\"",
    catAxisLabelFontSize: 13, catAxisLabelColor: HEX.dk2, catAxisLabelFontFace: "+mn-lt",
    valAxisMinVal: 0, valAxisMaxVal: 110, valAxisMajorUnit: 20, valAxisLabelFontSize: 11, valAxisLabelColor: HEX.dk2, valAxisLabelFormatCode: "0\"%\"",
    valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 13, legendFontFace: "+mn-lt", legendColor: HEX.dk2,
  });
  g.addImage({ path: "../analysis/fig_detection_by_area.png", x: 6.85, y: 1.45, w: 5.85, h: 3.29, altText: "Bar chart from analyze.py: seeded faults detected per area for each arm" });
  txt(g, [
    { text: "Left: ", options: { bold: true, color: C.text1 } },
    { text: "coverage measured with coverage.py. Line coverage counts lines run at least once; branch coverage counts both outcomes of each if/else.", options: { breakLine: true } },
    { text: "Right: ", options: { bold: true, color: C.text1 } },
    { text: "the chart produced by analysis/analyze.py from the scoring results." },
  ], 6.85, 4.95, 5.85, 1.5, { size: 12 });
  txt(g, "High coverage is necessary but not sufficient: the AI suite ran 88% of the lines yet still missed 6 faults.", 0.6, 6.15, 5.9, 0.6, { size: 12, italic: true });
  g.addNotes("Per-line coverage reports are in analysis/htmlcov_<arm>/index.html.");

  // ---- faults every arm missed ----
  const m = content("Six faults escaped every arm", SEC);
  const missed = [
    ["M04 · authentication", "Deleting \"bob\" also removes \"bobby\" (prefix match)"],
    ["M13 · chunk boundaries", "A shortened middle chunk, or a wrong link, is accepted"],
    ["M14 · chunk boundaries", "A size field of 1,025–1,076 is accepted"],
    ["M18 · tamper", "Extra data added to the chunks is returned to the user"],
    ["M19 · tamper", "A chunk file with bytes appended is accepted"],
    ["M20 · tamper", "A change to the first padding byte is not noticed"],
  ];
  missed.forEach(([h, t2], i) => {
    const x = 0.6 + (i % 3) * 4.13, y = 1.45 + Math.floor(i / 3) * 1.95;
    box(m, "", x, y, 3.85, 1.75, { fill: C.background2 });
    txt(m, h, x + 0.22, y + 0.18, 3.4, 0.4, { bold: true, color: C.accent3, size: 15 });
    txt(m, t2, x + 0.22, y + 0.65, 3.4, 1.0, { size: 14 });
  });
  box(m, [
    { text: "What they share: ", options: { bold: true } },
    { text: "each needs a test that hand-crafts a subtly broken file (a near-match username, an edited size field, an appended byte) and checks the exact response. Even 340 AI test cases did not reach them; this is where a specialist tester adds value." },
  ], 0.6, 5.5, 12.1, 1.05, { fill: C.text1, color: C.background1, size: 14, align: "left", margin: 12 });
  m.addNotes("These are the strongest candidates for the next round of tests, by either method.");

  // ---- intent vs delivered ----
  const v = content("Project intent vs what we delivered", SEC);
  const rowsV = [
    ["Research question", "Answered for this setting: AI-assisted found more faults (70% vs 25%, p = 0.004)"],
    ["AI proposes tests for authentication, round trips, chunk boundaries, tamper", "Done: 5 standard prompts, 132 test functions across all four areas"],
    ["Manually validate each generated test", "Done as a 45-min group walkthrough; 1 test corrected, 131 accepted"],
    ["Compare test coverage", "Done: 71% vs 88% lines, 47% vs 77% branches"],
    ["Compare valid defects discovered", "Done: 5 vs 14 of 20 seeded faults; 0 real defects in the unchanged code"],
    ["Compare false-positive failures", "Done: 5 manual vs 1 AI"],
    ["Compare time spent", "Done (estimated): 160 min manual vs 50 min AI review"],
    ["Retain an AI prompt/review log", "Done: logs/ai_prompt_log.csv and logs/ai_review_sheet.csv"],
    ["Unique output: AI-assisted regression suite", "Delivered: tests/ai/run1 (340 cases, all passing on sefs-v1.0)"],
    ["Unique output: controlled evaluation", "Delivered: frozen code, hidden faults, isolated AI workspace, statistics in analysis/"],
  ];
  v.addTable([[H("Intended"), H("Delivered")], ...rowsV.map((rw, i) => rw.map((t2, j) => ({
    text: t2, options: { bold: j === 0, fill: { color: i % 2 ? "FFFFFF" : HEX.lt2 } },
  })))], { x: 0.6, y: 1.35, w: 12.1, colW: [5.2, 6.9], rowH: 0.45, fontSize: 13, color: HEX.dk1, border: { type: "solid", pt: 0.5, color: "D5DCE2" }, valign: "middle", margin: [0.03, 0.1, 0.03, 0.1] });
  v.addNotes("Every item in the original project brief has a matching deliverable in the repository.");

  // ---- threats to validity ----
  const t = content("How far the result can be trusted", SEC);
  const thr = [
    ["Small study", "One tester, one AI run, 20 faults. The result describes this setting; it does not generalise on its own."],
    ["Beginner tester", "Daniel had no IT background. An experienced tester would likely narrow the gap."],
    ["Estimated times", "No session was timed, and the manual arm ran 40 minutes over budget."],
    ["AI arm deviations", "An isolated Claude Opus 5.5 agent replaced the claude.ai chat; review was a group walkthrough, not test by test."],
    ["AI help in the set-up", "Fault locations were AI-suggested and fault M01 was AI-written; test instructions and examples were AI-prepared."],
    ["Uneven test counts", "8 manual tests vs 340 AI cases: the AI's volume is part of the effect being measured."],
  ];
  thr.forEach(([h, t2], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.4 + Math.floor(i / 2) * 1.75;
    box(t, "", x, y, 5.95, 1.55, { fill: C.background2 });
    circleNum(t, "!", x + 0.2, y + 0.18, 0.42, C.accent3);
    txt(t, h, x + 0.8, y + 0.18, 5.0, 0.42, { bold: true, color: C.text1, size: 15, valign: "middle" });
    txt(t, t2, x + 0.2, y + 0.7, 5.6, 0.8, { size: 13 });
  });
  t.addNotes("Stating these openly is part of a controlled evaluation. A repeated run (ai/run2, a second tester) would strengthen the evidence.");

  // ---- conclusions ----
  const k = content("Conclusions", SEC);
  const concl = [
    ["AI assistance found more defects in less time", "70% vs 25% of seeded faults, 16.8 vs 1.9 faults per tester hour, significant at p = 0.004."],
    ["Its strength is breadth", "The AI covered boundaries and odd inputs systematically: 80–100% in authentication and round trips, where the beginner wrote few tests."],
    ["Human review still matters", "1 of 132 AI tests was wrong (a miscounted byte position) and was caught only because a person checked it."],
    ["Neither approach is enough on its own", "6 subtle faults escaped every arm. Targeted, hand-crafted tamper and boundary tests are the next step."],
  ];
  concl.forEach(([h, t2], i) => {
    const y = 1.4 + i * 1.18;
    circleNum(k, i + 1, 0.6, y + 0.12, 0.5, C.accent1);
    txt(k, [
      { text: h, options: { bold: true, color: C.text1, fontSize: 17, breakLine: true } },
      { text: t2, options: { fontSize: 14 } },
    ], 1.3, y, 6.6, 1.1);
  });
  box(k, "", 8.3, 1.4, 4.4, 4.75, { fill: C.text1 });
  txt(k, "Recommendations", 8.55, 1.6, 3.9, 0.4, { bold: true, color: HEX.accent2, size: 16 });
  const rec = [
    "Use AI to draft a broad regression suite, then have a person review every test against the spec",
    "Add hand-written tests for the six missed faults",
    "Repeat the study: a second AI run and a second tester, with every session timed",
  ];
  txt(k, rec.map((x, i) => ({ text: x, options: { bullet: true, breakLine: i < rec.length - 1 } })), 8.55, 2.15, 3.95, 3.8, { size: 14, color: "D6DEE5", psa: 8 });
  txt(k, "Delivered: SEFS Parts 1–3 · a 340-case AI-assisted regression suite · a controlled evaluation with logs and analysis", 0.6, 6.25, 12.1, 0.45, { size: 13, italic: true });
  k.addNotes("The conclusions hold for this setting (one beginner tester, one AI run, 20 faults); the threats slide lists the limits.");
}

async function build() {
  opening();
  architecture();
  securityGoals();
  if (DONE.part1) part1();
  if (DONE.part2) part2();
  if (DONE.part3) part3();
  decisions();
  testing();
  limitations();
  if (DONE.extension) extension();
  closing();
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("Wrote " + OUT);
}
build().catch((e) => { console.error(e); process.exit(1); });
