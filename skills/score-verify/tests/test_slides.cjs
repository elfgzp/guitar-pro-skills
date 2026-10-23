const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process');
const alpha=require('@coderline/alphatab');
const {auditScore,auditBytes}=require('../scripts/audit_alphatab.cjs');
const {makeDemoScore}=require('../scripts/make_demo.cjs');
function slideFixture(kind='Shift'){
 const score=makeDemoScore(),bars=score.tracks[0].staves[0].bars;
 const origin=bars[1].voices[0].beats[2].notes[0],target=bars[2].voices[0].beats[0].notes[0];
 target.fret=7;origin.slideOutType=alpha.model.SlideOutType[kind];score.finish(new alpha.Settings());
 return {score,origin,target};
}
function reference(kind='shift'){
 return {schemaVersion:1,ticksPerQuarter:960,scope:[{track:0,staff:0,fromBar:1,toBar:3}],slides:[{kind,
  origin:{track:0,staff:0,bar:2,voice:0,onset:1920,string:1,fret:3},
  target:{track:0,staff:0,bar:3,voice:0,onset:0,string:1,fret:7}}]};
}
test('cross-bar slide kind and high-string-first endpoints survive the GP round trip',()=>{
 const {score}=slideFixture(),bytes=new alpha.exporter.Gp7Exporter().export(score,new alpha.Settings());
 const report=auditBytes(bytes,{expectedSlides:reference()});
 assert.equal(report.structural.pass,true,JSON.stringify(report.structural.errors));
 assert.equal(report.slides?.reference?.pass,true);
 assert.equal(report.slides.ledger[0].origin.string,1);
 assert.equal(report.slides.ledger[0].target.bar,3);
 assert.equal(report.slides.ledger[0].target.fret,7);
 assert.equal(report.evidence.source.status,'not_checked');
});
test('a missing slide fails an independent reference although all pitches and bar durations still pass',()=>{
 const {score,origin,target}=slideFixture();origin.slideOutType=alpha.model.SlideOutType.None;origin.slideTarget=null;target.slideOrigin=null;
 const report=auditScore(score,{expectedSlides:reference()});
 assert.equal(report.structural.errors.some(e=>e.code==='slide_missing'),true);
 assert.equal(report.slides.reference.pass,false);
 assert.equal(report.structural.errors.some(e=>e.code==='voice_duration'),false);
});
test('a wrong slide endpoint is detected even when kind and slide count match',()=>{
 const {score}=slideFixture(),expected=reference();expected.slides[0].target.fret=8;
 const report=auditScore(score,{expectedSlides:expected});
 assert.equal(report.structural.errors.some(e=>e.code==='slide_endpoint'),true);
});
test('the declared source-review scope catches extra slides without claiming unreviewed bars',()=>{
 const {score}=slideFixture(),expected=reference();expected.scope[0].toBar=1;expected.slides=[];
 assert.equal(auditScore(score,{expectedSlides:expected}).slides.reference.pass,true);
 expected.scope[0].toBar=3;
 assert.equal(auditScore(score,{expectedSlides:expected}).structural.errors.some(e=>e.code==='slide_extra'),true);
});
test('directed slides with missing, backward or different-string endpoints fail safely',()=>{
 for(const fault of ['missing','backward','string']){
  const {score,origin,target}=slideFixture();
  if(fault==='missing')origin.slideTarget=null;
  if(fault==='backward')origin.slideTarget=score.tracks[0].staves[0].bars[0].voices[0].beats[0].notes[0];
  if(fault==='string')target.string=5;
  const report=auditScore(score);
  assert.equal(report.structural.errors.some(e=>e.code===({missing:'slide_target',backward:'slide_time',string:'slide_string'}[fault])),true);
  assert.equal(report.midi.status,'not_generated');
 }
});
test('terminal and incoming slides need no target and both marks remain in the ledger',()=>{
 const {score,origin}=slideFixture('OutDown');origin.slideInType=alpha.model.SlideInType.IntoFromBelow;
 const report=auditScore(score);
 assert.equal(report.structural.pass,true,JSON.stringify(report.structural.errors));
 assert.deepEqual(report.slides.ledger.map(s=>s.kind).sort(),['into-from-below','out-down']);
 assert(report.slides.ledger.every(s=>s.target===null));
});
test('dead-note slide origins retain unknown fret instead of inventing open-string pitch',()=>{
 const {score,origin}=slideFixture();origin.isDead=true;origin.fret=0;
 const expected=reference();expected.slides[0].origin.dead=true;expected.slides[0].origin.fret=null;
 const report=auditScore(score,{expectedSlides:expected});
 assert.equal(report.slides.reference.pass,true);
 assert.equal(report.slides.ledger[0].origin.fret,null);
 assert.equal(report.slides.ledger[0].origin.dead,true);
});
test('a slide reference uses its declared tick resolution',()=>{
 const {score}=slideFixture(),expected=reference();expected.ticksPerQuarter=480;expected.slides[0].origin.onset=960;
 assert.equal(auditScore(score,{expectedSlides:expected}).slides.reference.pass,true);
});
test('CLI compares source-reviewed slides and refuses to overwrite its reference input',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'score-slides-'));
 try{
  const {score}=slideFixture(),input=path.join(dir,'fixture.gp'),ref=path.join(dir,'slides.json'),report=path.join(dir,'report.json');
  const script=path.join(__dirname,'../scripts/audit_alphatab.cjs');
  fs.writeFileSync(input,new alpha.exporter.Gp7Exporter().export(score,new alpha.Settings()));
  fs.writeFileSync(ref,JSON.stringify(reference()));const before=fs.readFileSync(ref);
  let run=cp.spawnSync(process.execPath,[script,input,'--expected-slides',ref,'--json',report],{encoding:'utf8'});
  assert.equal(run.status,0,run.stderr);assert.equal(JSON.parse(fs.readFileSync(report)).slides.reference.pass,true);
  run=cp.spawnSync(process.execPath,[script,input,'--expected-slides',ref,'--json',ref],{encoding:'utf8'});
  assert.equal(run.status,2);assert.equal(JSON.parse(run.stdout).output.code,'output_alias');assert.deepEqual(fs.readFileSync(ref),before);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('invalid references fail as input errors instead of treating an empty inventory as a pass',()=>{
 const {score}=slideFixture();
 for(const change of [r=>{delete r.scope;},r=>{r.scope[0].toBar=0;},r=>{r.slides[0].kind='unknown';},r=>{r.slides[0].target=null;},r=>{r.slides[0].origin.string=0;},r=>{r.slides[0].origin.bar=4;}]){
  const expected=reference();change(expected);
  assert.throws(()=>auditScore(score,{expectedSlides:expected}),error=>error.code==='slide_reference_input');
 }
});
test('grace slides keep a separate identity at the main-note onset without adding metric duration',()=>{
 const score=makeDemoScore(),voice=score.tracks[0].staves[0].bars[2].voices[0];
 const grace=new alpha.model.Beat(),note=new alpha.model.Note();grace.duration=8;grace.graceType=alpha.model.GraceType.BeforeBeat;
 note.string=6;note.fret=5;note.slideOutType=alpha.model.SlideOutType.Legato;grace.addNote(note);
 voice.beats.unshift(grace);voice.beats.forEach((beat,index)=>{beat.voice=voice;beat.index=index;});score.finish(new alpha.Settings());
 const expected=reference('legato');expected.slides[0]={kind:'legato',origin:{track:0,staff:0,bar:3,voice:0,onset:0,string:1,fret:5,grace:true,graceIndex:0},target:{track:0,staff:0,bar:3,voice:0,onset:0,string:1,fret:3}};
 const bytes=new alpha.exporter.Gp7Exporter().export(score,new alpha.Settings()),report=auditBytes(bytes,{expectedSlides:expected});
 assert.equal(report.structural.pass,true,JSON.stringify(report.structural.errors));
 assert.equal(report.slides.ledger[0].origin.grace,true);assert.equal(report.slides.ledger[0].origin.graceIndex,0);
 assert.equal(report.slides.ledger[0].origin.onset,0);assert.equal(report.slides.ledger[0].target.grace,undefined);
 delete expected.slides[0].origin.grace;delete expected.slides[0].origin.graceIndex;
 assert.equal(auditBytes(bytes,{expectedSlides:expected}).slides.reference.pass,false);
});
test('a same-fret tie target is flagged and the source reference requires the final held segment',()=>{
 const {score,origin,target}=slideFixture();target.fret=3;target.isTieDestination=true;
 const destination=target.beat.voice.beats[1].notes[0];destination.fret=7;score.finish(new alpha.Settings());
 const expected=reference();expected.slides[0].origin={track:0,staff:0,bar:3,voice:0,onset:0,string:1,fret:3};
 expected.slides[0].target={track:0,staff:0,bar:3,voice:0,onset:960,string:1,fret:7};
 let report=auditScore(score,{expectedSlides:expected});
 assert(report.structural.warnings.some(w=>w.code==='slide_zero_interval'));assert.equal(report.slides.reference.pass,false);
 origin.slideOutType=alpha.model.SlideOutType.None;origin.slideTarget=null;target.slideOrigin=null;
 target.slideOutType=alpha.model.SlideOutType.Shift;score.finish(new alpha.Settings());
 report=auditBytes(new alpha.exporter.Gp7Exporter().export(score,new alpha.Settings()),{expectedSlides:expected});
 assert.equal(report.structural.pass,true,JSON.stringify(report.structural.errors));
 assert.equal(report.structural.warnings.some(w=>w.code==='slide_zero_interval'),false);
});
test('a slide discarded by model finishing still fails an independent source inventory',()=>{
 const {score,origin,target}=slideFixture();origin.slideTarget=null;target.slideOrigin=null;
 for(const beat of score.tracks[0].staves[0].bars[2].voices[0].beats)for(const note of beat.notes)note.string=5;
 // A fresh import rebuilds string lookup tables, then drops the unresolved flag.
 const bytes=new alpha.exporter.Gp7Exporter().export(score,new alpha.Settings());
 assert.equal(auditBytes(bytes).structural.pass,true);
 const report=auditBytes(bytes,{expectedSlides:reference()});
 assert.equal(report.slides.ledger.length,0);assert.equal(report.slides.reference.missing,1);
 assert.equal(report.structural.pass,false);
});
test('a valid slide reference does not hide a malformed score parse error or its hash',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'score-slides-invalid-'));
 try{
  const input=path.join(dir,'bad.gp'),ref=path.join(dir,'slides.json'),script=path.join(__dirname,'../scripts/audit_alphatab.cjs');
  fs.writeFileSync(input,'not a gp');const expected=reference();expected.slides=[];fs.writeFileSync(ref,JSON.stringify(expected));
  const plain=JSON.parse(cp.spawnSync(process.execPath,[script,input],{encoding:'utf8'}).stdout);
  const run=cp.spawnSync(process.execPath,[script,input,'--expected-slides',ref],{encoding:'utf8'}),withReference=JSON.parse(run.stdout);
  assert.equal(run.status,2);assert.equal(withReference.parse.pass,false);
  assert.deepEqual(withReference.input,plain.input);assert.equal(withReference.parse.error,plain.parse.error);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
