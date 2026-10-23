#!/usr/bin/env node
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const alpha=require('@coderline/alphatab');
const slides=require('./slide_ledger.cjs');
const TICKS_PER_QUARTER=960;
const EPSILON=0.01;
const legacyCache=new Map();

function envelope(){
  return {schemaVersion:1,tool:'score-verify',versions:{node:process.versions.node,alphaTab:alpha.meta.version,alphaTabCommit:alpha.meta.commit},parse:{pass:true},structural:{pass:false,errors:[],warnings:[]},evidence:{visual:{status:'not_checked'},audio:{status:'not_checked'},source:{status:'not_checked'}},limitations:['Structural consistency does not establish transcription accuracy against a source score.','MIDI event generation is not an audible playback check. Repeats, grace notes and ornaments may change attack counts.','A parser may normalize or discard invalid source constructs; post-parse checks cannot detect every source-format defect.']};
}
function midiFile(score){
  const file=new alpha.midi.MidiFile();
  new alpha.midi.MidiFileGenerator(score,new alpha.Settings(),new alpha.midi.AlphaSynthMidiFileHandler(file)).generate();
  return file;
}
function noteOns(file){
  // alphaTab's enum is authoritative; its numeric NoteOn is not the SMF status byte.
  return file.tracks.flatMap(t=>t.events).filter(e=>e.type===alpha.midi.MidiEventType.NoteOn&&e.noteVelocity>0);
}
function legacyGM(index){
  if(legacyCache.has(index))return legacyCache.get(index);
  const m=alpha.model,score=new m.Score(),master=new m.MasterBar(),track=new m.Track(),staff=new m.Staff(),bar=new m.Bar(),voice=new m.Voice(),beat=new m.Beat(),note=new m.Note();
  score.addMasterBar(master);score.addTrack(track);track.addStaff(staff);staff.isPercussion=true;staff.addBar(bar);bar.addVoice(voice);voice.addBeat(beat);beat.duration=1;beat.addNote(note);note.percussionArticulation=index;note.octave=3;note.tone=0;track.playbackInfo.primaryChannel=9;track.playbackInfo.secondaryChannel=9;
  score.finish(new alpha.Settings());
  const gm=noteOns(midiFile(score))[0]?.noteKey??null;
  legacyCache.set(index,gm);
  return gm;
}
function metricBeats(voice){return voice.beats.filter(b=>b.graceType===alpha.model.GraceType.None);}
function metricEnd(voice){return Math.max(0,...metricBeats(voice).map(b=>b.displayStart+b.displayDuration));}
function isEmptyAlternate(voice){return voice.index>0&&voice.beats.every(b=>b.isEmpty&&b.notes.length===0);}
function pickupLength(score,index){return Math.max(0,...score.tracks.flatMap(t=>t.staves.flatMap(s=>s.bars[index]?.voices.filter(v=>!isEmptyAlternate(v)).map(metricEnd)||[])));}
function location(note){const beat=note.beat;return {track:beat.voice.bar.staff.track.index,staff:beat.voice.bar.staff.index,bar:beat.voice.bar.index+1,voice:beat.voice.index,onset:beat.displayStart,note:note.index};}
function earlier(a,b){return a.bar<b.bar||a.bar===b.bar&&a.onset<b.onset;}
function identity(note,resolve){return note.isPercussion?'drum:'+resolve(note):'pitch:'+note.realValue+(note.isStringed?':string:'+note.string:'');}
function auditScore(score,options={}){
  const expectedSlides=options.expectedSlides===undefined?null:slides.validateReference(options.expectedSlides);
  const report=envelope(),errors=report.structural.errors,warnings=report.structural.warnings;
  const problem=(code,details)=>errors.push({code,...details});
  report.masterBars=score.masterBars.length;
  report.tracks=[];
  if(!score.masterBars.length||!score.tracks.length)problem('empty_score',{});
  const mappings=new Map();
  function resolve(note){
    if(mappings.has(note))return mappings.get(note);
    const track=note.beat.voice.bar.staff.track,index=note.percussionArticulation,kit=track.percussionArticulations;
    let gm=null,mode='legacy-engine';
    if(kit.length&&index>=0&&index<kit.length){gm=kit[index].outputMidiNumber;mode='custom-index';}
    else{
      if(kit.length)problem('percussion_index',{...location(note),index,kitLength:kit.length});
      if(!Number.isInteger(index)||index<0)problem('percussion_identity',{...location(note),index});
      else gm=legacyGM(index);
    }
    if(!Number.isInteger(gm)||gm<0||gm>127)problem('percussion_output',{...location(note),index,gm});
    const key=String(index),row=report.tracks[track.index];
    if(row)row.percussionMapping[key]={mode,index,gm};
    mappings.set(note,gm);return gm;
  }
  const allNotes=[];
  for(const track of score.tracks){
    const row={index:track.index,name:track.name,staves:track.staves.length,bars:track.staves.map(s=>s.bars.length),notes:0,tieDestinations:0,notatedAttacks:0,voices:[],percussionMapping:{}};
    report.tracks.push(row);
    for(const staff of track.staves){
      if(staff.bars.length!==score.masterBars.length)problem('bar_count',{track:track.index,staff:staff.index,expected:score.masterBars.length,actual:staff.bars.length});
      for(const bar of staff.bars){
        const master=score.masterBars[bar.index];if(!master)continue;
        const nominal=TICKS_PER_QUARTER*4*master.timeSignatureNumerator/master.timeSignatureDenominator;
        const expected=master.isAnacrusis?pickupLength(score,bar.index):nominal;
        for(const voice of bar.voices){
          const context={track:track.index,staff:staff.index,bar:bar.index+1,voice:voice.index};
          const skipped=isEmptyAlternate(voice),actual=metricEnd(voice);
          row.voices.push({...context,status:skipped?'empty-alternate':master.isFreeTime?'free-time-unchecked':'checked',pickup:master.isAnacrusis,expectedTicks:expected,actualTicks:actual});
          if(!skipped&&!master.isFreeTime){
            if(Math.abs(actual-expected)>EPSILON||expected<=0||master.isAnacrusis&&expected>nominal+EPSILON)problem('voice_duration',{...context,expectedTicks:expected,actualTicks:actual});
            let cursor=0;
            for(const beat of metricBeats(voice)){
              if(Math.abs(beat.displayStart-cursor)>EPSILON||beat.displayDuration<=0)problem('beat_timeline',{...context,onset:beat.displayStart,duration:beat.displayDuration,expectedOnset:cursor});
              cursor=beat.displayStart+beat.displayDuration;
            }
          }
          if(master.isFreeTime&&!skipped)warnings.push({code:'free_time_duration_not_checked',...context});
          for(const beat of voice.beats)for(const note of beat.notes){
            row.notes++;allNotes.push(note);
            if(note.isPercussion)resolve(note);
            if(note.isTieDestination)row.tieDestinations++;else row.notatedAttacks++;
          }
        }
      }
    }
  }
  for(const note of allNotes){
    const here=location(note);
    if(note.isTieDestination){
      const origin=note.tieOrigin;
      if(!origin)problem('tie_orphan',here);
      else{
        const previous=location(origin);
        if(previous.staff!==here.staff||previous.voice!==here.voice)warnings.push({code:'tie_cross_voice_or_staff',...here,origin:previous,review:'May be intentional cross-staff notation; verify source.'});
        if(previous.track!==here.track||identity(origin,resolve)!==identity(note,resolve))problem('tie_identity',{...here,origin:previous,currentIdentity:identity(note,resolve),originIdentity:identity(origin,resolve)});
        if(!earlier(previous,here))problem('tie_time',{...here,origin:previous});
        if(origin.tieDestination!==note)problem('tie_reciprocal',{...here,origin:previous});
      }
    }
    if(note.tieDestination&&!note.tieDestination.isTieDestination)problem('tie_flag',here);
    if(note.tieDestination&&note.tieDestination.tieOrigin!==note)problem('tie_reciprocal',here);
  }
  report.slides={ticksPerQuarter:960,stringNumbering:'highest-string-is-1',ledger:slides.buildSlideLedger(allNotes,problem,item=>warnings.push(item)),reference:{status:'not_provided'}};
  if(expectedSlides)report.slides.reference=slides.compareSlides(report.slides.ledger,expectedSlides,score,problem);
  if(errors.some(e=>e.code.startsWith('tie_')||slides.unsafeCodes.has(e.code))){report.midi={status:'not_generated',reason:'Unsafe tie or slide graph; generation could loop or dereference an orphan.'};}
  else try{
    const events=noteOns(midiFile(score));
    report.midi={status:'generated',noteOnEnum:alpha.midi.MidiEventType.NoteOn,noteOnCount:events.length,tracks:score.tracks.map(t=>{
      const notes=events.filter(e=>e.track===t.index),keys={};for(const n of notes)keys[n.noteKey]=(keys[n.noteKey]||0)+1;
      return {track:t.index,noteOnCount:notes.length,keys};
    })};
  }catch(error){report.midi={status:'failed',error:error.message};problem('midi_generation',{message:error.message});}
  report.structural.pass=errors.length===0;
  return report;
}
function auditBytes(bytes,options={}){
  if(options.expectedSlides!==undefined)slides.validateReference(options.expectedSlides);
  let report;
  try{report=auditScore(alpha.importer.ScoreLoader.loadScoreFromBytes(new Uint8Array(bytes)),options);}
  catch(error){if(error.code==='slide_reference_input')throw error;report=envelope();report.parse={pass:false,error:error.message};report.structural={pass:false,status:'not_checked',errors:[],warnings:[]};}
  report.input={name:options.filename?path.basename(options.filename):null,bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')};
  return report;
}
function writeReport(output,json,inputs){
  let destination=null;
  try{destination=fs.statSync(output);}catch(error){if(error.code!=='ENOENT')throw error;}
  for(const input of inputs){
    const source=fs.statSync(input);
    if(path.resolve(output)===path.resolve(input)||destination&&source.dev===destination.dev&&source.ino===destination.ino){
      const error=new Error('Report output aliases an input score or reference.');error.code='output_alias';throw error;
    }
  }
  const directory=path.dirname(path.resolve(output));
  fs.mkdirSync(directory,{recursive:true});
  const temporary=path.join(directory,'.score-report-'+crypto.randomUUID()+'.tmp');
  let fd;
  try{
    fd=fs.openSync(temporary,'wx',0o600);
    fs.writeFileSync(fd,json);fs.fsyncSync(fd);fs.closeSync(fd);fd=undefined;
    fs.renameSync(temporary,output);
  }finally{
    if(fd!==undefined)fs.closeSync(fd);
    try{fs.unlinkSync(temporary);}catch(error){if(error.code!=='ENOENT')throw error;}
  }
}
function main(args=process.argv.slice(2)){
  const usage='Usage: node audit_alphatab.cjs SCORE [--json REPORT.json] [--expected-slides SOURCE-SLIDES.json]';
  if(args.includes('--help')){console.log(usage);return;}
  const input=args[0],flags=new Map();let valid=!!input&&!input.startsWith('-');
  for(let i=1;i<args.length;i+=2){
    if(!['--json','--expected-slides'].includes(args[i])||!args[i+1]||args[i+1].startsWith('-')||flags.has(args[i])){valid=false;break;}
    flags.set(args[i],args[i+1]);
  }
  if(!valid){console.error(usage);process.exitCode=2;return;}
  const output=flags.get('--json'),reference=flags.get('--expected-slides');
  let report;
  try{
    let expectedSlides,referenceBytes;
    if(reference){referenceBytes=fs.readFileSync(reference);expectedSlides=JSON.parse(referenceBytes);slides.validateReference(expectedSlides);}
    report=auditBytes(fs.readFileSync(input),{filename:input,expectedSlides});
    if(referenceBytes&&report.slides?.reference)report.slides.reference.input={name:path.basename(reference),sha256:crypto.createHash('sha256').update(referenceBytes).digest('hex')};
  }
  catch(error){report=envelope();report.parse={pass:false,error:error.message};report.inputError={code:error.code||'input',error:error.message};}
  if(output)try{writeReport(output,JSON.stringify(report,null,2)+'\n',[input,...reference?[reference]:[]]);}
  catch(error){report.output={pass:false,code:error.code||'report_output',error:error.message};}
  console.log(JSON.stringify(report,null,2));
  process.exitCode=report.output?.pass===false||!report.parse.pass?2:report.structural.pass?0:1;
}
if(require.main===module)main();
module.exports={auditScore,auditBytes,noteOns};
