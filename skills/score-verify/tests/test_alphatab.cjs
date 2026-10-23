const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process');
const skill=path.join(__dirname,'..');
const auditPath=path.join(skill,'scripts/audit_alphatab.cjs');
let audit={};try{audit=require(auditPath);}catch(e){if(e.code!=='MODULE_NOT_FOUND')throw e;}
test('auditor exposes a reusable model audit',()=>assert.equal(typeof audit.auditScore,'function'));
function fixture(){return require(path.join(skill,'scripts/make_demo.cjs')).makeDemoScore();}
test('triplets, per-note drum ties and real MIDI attacks survive GP export/import',()=>{
 const alpha=require(path.join(skill,'node_modules/@coderline/alphatab'));
 const s=fixture(),data=new alpha.exporter.Gp7Exporter().export(s,new alpha.Settings());
 const report=audit.auditBytes(data,{filename:'synthetic.gp'});
 assert.equal(report.structural.pass,true,JSON.stringify(report.structural.errors));
 assert.equal(report.tracks.length,2);assert.equal(report.masterBars,3);
 assert.equal(report.tracks[0].notes,10);assert.equal(report.tracks[0].tieDestinations,1);
 assert.equal(report.tracks[1].notes,16);assert.equal(report.tracks[1].tieDestinations,3);
 assert.equal(report.midi.tracks[0].noteOnCount,9);assert.equal(report.midi.tracks[1].noteOnCount,13);
 assert.deepEqual(Object.values(report.tracks[1].percussionMapping).map(x=>x.gm).sort((a,b)=>a-b),[36,42]);
 assert.equal(report.evidence.visual.status,'not_checked');assert.equal(report.evidence.audio.status,'not_checked');assert.equal(report.evidence.source.status,'not_checked');
});
test('wrong identity and orphan ties fail without silently repairing input',()=>{
 const s=fixture(),b=s.tracks[1].staves[0].bars[0].voices[0].beats;
 b[1].notes[0].tieOrigin=b[0].notes[1];
 const r=audit.auditScore(s);assert(r.structural.errors.some(e=>e.code==='tie_identity'));
 b[1].notes[0].tieOrigin=null;assert(audit.auditScore(s).structural.errors.some(e=>e.code==='tie_orphan'));
});
test('custom articulation index outside its kit fails even if engine falls back to a legacy ID',()=>{
 const s=fixture();s.tracks[1].staves[0].bars[0].voices[0].beats[0].notes[0].percussionArticulation=36;
 const r=audit.auditScore(s);assert(r.structural.errors.some(e=>e.code==='percussion_index'));
});
test('truly empty alternate voices are excluded but short silent voices are checked',()=>{
 const alpha=require(path.join(skill,'node_modules/@coderline/alphatab')),s=fixture(),bar=s.tracks[0].staves[0].bars[0];
 let b;for(const current of s.tracks[0].staves[0].bars){const v=new alpha.model.Voice();current.addVoice(v);const empty=new alpha.model.Beat();empty.isEmpty=true;v.addBeat(empty);if(current===bar)b=empty;}s.finish(new alpha.Settings());
 assert.equal(audit.auditScore(s).structural.pass,true);
 b.isEmpty=false;s.finish(new alpha.Settings());assert(audit.auditScore(s).structural.errors.some(e=>e.code==='voice_duration'));
});
test('explicit pickup uses actual shared duration instead of requiring a full meter',()=>{
 const alpha=require(path.join(skill,'node_modules/@coderline/alphatab')),s=fixture();
 for(const t of s.tracks){const v=t.staves[0].bars[0].voices[0];v.beats=v.beats.slice(0,1);v.beats[0].duration=4;v.beats[0].tupletNumerator=1;v.beats[0].tupletDenominator=1;for(const n of v.beats[0].notes)n.tieDestination=null;}
 s.masterBars[0].isAnacrusis=true;s.finish(new alpha.Settings());
 const r=audit.auditScore(s);assert.equal(r.structural.pass,true,JSON.stringify(r.structural.errors));assert.equal(r.tracks[0].voices[0].expectedTicks,960);
});
test('short ordinary bar fails, and corrupt input produces a machine-readable parse failure',()=>{
 const s=fixture();s.tracks[0].staves[0].bars[0].voices[0].beats.pop();
 assert(audit.auditScore(s).structural.errors.some(e=>e.code==='voice_duration'));
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'score-audit-'));try{const input=path.join(dir,'bad.gp'),out=path.join(dir,'report.json');fs.writeFileSync(input,'not a score');
 const run=cp.spawnSync(process.execPath,[auditPath,input,'--json',out]);assert.equal(run.status,2);assert.equal(JSON.parse(fs.readFileSync(out)).parse.pass,false);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});

for(const alias of ['same-path','hard-link','symbolic-link'])test('report rejects '+alias+' input alias without changing the score',()=>{
 const alpha=require(path.join(skill,'node_modules/@coderline/alphatab')),dir=fs.mkdtempSync(path.join(os.tmpdir(),'score-alias-'));
 try{const input=path.join(dir,'input.gp'),bytes=Buffer.from(new alpha.exporter.Gp7Exporter().export(fixture(),new alpha.Settings()));fs.writeFileSync(input,bytes);let output=input;
 if(alias!=='same-path'){output=path.join(dir,'alias.json');if(alias==='hard-link')fs.linkSync(input,output);else fs.symlinkSync(input,output);}
 const result=cp.spawnSync(process.execPath,[auditPath,input,'--json',output],{encoding:'utf8'});
 assert.equal(result.status,2);assert.equal(JSON.parse(result.stdout).output.code,'output_alias');assert.deepEqual(fs.readFileSync(input),bytes);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});

test('synthetic drum noteheads and percussion clef survive the GP round trip',()=>{
 const alpha=require(path.join(skill,'node_modules/@coderline/alphatab'));
 const parsed=alpha.importer.ScoreLoader.loadScoreFromBytes(new alpha.exporter.Gp7Exporter().export(fixture(),new alpha.Settings()));
 const drums=parsed.tracks[1];assert(drums.staves[0].bars.every(b=>b.clef===alpha.model.Clef.Neutral));
 assert.equal(drums.percussionArticulations[0].noteHeadDefault,0xe0a4);
 assert.equal(drums.percussionArticulations[1].noteHeadDefault,0xe0a9);
});
