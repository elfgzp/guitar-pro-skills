'use strict';
const alpha=require('@coderline/alphatab');
const OUT=new Map([[1,'shift'],[2,'legato'],[3,'out-up'],[4,'out-down'],[5,'pick-down'],[6,'pick-up']]);
const IN=new Map([[1,'into-from-below'],[2,'into-from-above']]);
const DIRECTED=new Set(['shift','legato']);
const KINDS=new Set([...OUT.values(),...IN.values()]);
const unsafeCodes=new Set(['slide_target','slide_time','slide_string','slide_reciprocal','slide_context']);
const rounded=value=>Math.round(value*1e6)/1e6;
function invalid(message){const error=new Error(message);error.code='slide_reference_input';throw error;}
function integer(value,min){return Number.isInteger(value)&&value>=min;}
function inScope(note,scope){return scope.some(s=>note.track===s.track&&note.staff===s.staff&&note.bar>=s.fromBar&&note.bar<=s.toBar);}
function normalizeEndpoint(note,ticksPerQuarter=960){
 if(!note||typeof note!=='object')invalid('A slide endpoint must be an object.');
 const result={};
 for(const key of ['track','staff','bar','voice']){
  if(!integer(note[key],key==='bar'?1:0))invalid('Invalid endpoint '+key+'.');
  result[key]=note[key];
 }
 if(!Number.isFinite(note.onset)||note.onset<0)invalid('Invalid endpoint onset.');
 result.onset=rounded(note.onset*960/ticksPerQuarter);
 if(note.grace!==undefined&&typeof note.grace!=='boolean')invalid('Endpoint grace must be boolean.');
 if(note.grace===true){
  if(note.graceIndex!==undefined&&!integer(note.graceIndex,0))invalid('Invalid graceIndex.');
  result.grace=true;result.graceIndex=note.graceIndex??0;
 }else if(note.graceIndex!==undefined)invalid('graceIndex requires grace:true.');
 if(note.dead!==undefined&&typeof note.dead!=='boolean')invalid('Endpoint dead must be boolean.');
 result.dead=note.dead===true;
 if(note.string!==undefined){
  if(!integer(note.string,1))invalid('String numbers start at 1 for the highest string.');
  result.string=note.string;
  if(result.dead){
   if(note.fret!==undefined&&note.fret!==null)invalid('A dead note has unknown fret; use null.');
   result.fret=null;
  }else{
   if(!integer(note.fret,0))invalid('A fretted endpoint needs its source fret.');
   result.fret=note.fret;
  }
 }else{
  if(result.dead)result.pitch=null;
  else{
   if(!integer(note.pitch,0)||note.pitch>127)invalid('A non-stringed endpoint needs its MIDI pitch.');
   result.pitch=note.pitch;
  }
 }
 return result;
}
function endpoint(note){
 const beat=note.beat,bar=beat.voice.bar,staff=bar.staff;
 const result={track:staff.track.index,staff:staff.index,bar:bar.index+1,voice:beat.voice.index,onset:rounded(beat.displayStart),dead:note.isDead};
 if(beat.graceType!==alpha.model.GraceType.None){
  result.grace=true;
  result.graceIndex=beat.voice.beats.filter(b=>b.index<beat.index&&b.graceType!==alpha.model.GraceType.None&&Math.abs(b.displayStart-beat.displayStart)<0.000001).length;
 }
 if(note.isStringed){result.string=staff.stringTuning.tunings.length-note.string+1;result.fret=note.isDead?null:note.fret;}
 else result.pitch=note.isDead?null:note.realValue;
 return result;
}
function validateReference(reference){
 if(!reference||reference.schemaVersion!==1)invalid('Expected slide reference schemaVersion 1.');
 if(!Number.isFinite(reference.ticksPerQuarter)||reference.ticksPerQuarter<=0)invalid('Declare a positive ticksPerQuarter.');
 if(!Array.isArray(reference.scope)||!reference.scope.length||!Array.isArray(reference.slides))invalid('Provide a nonempty reviewed scope and a slides array, even when no slides were found.');
 const scope=reference.scope.map(s=>{
  if(!s||!integer(s.track,0)||!integer(s.staff,0)||!integer(s.fromBar,1)||!integer(s.toBar,s.fromBar))invalid('Invalid reviewed scope.');
  return {track:s.track,staff:s.staff,fromBar:s.fromBar,toBar:s.toBar};
 });
 const seen=new Set();
 const slides=reference.slides.map(row=>{
  if(!row||!KINDS.has(row.kind))invalid('Unknown slide kind.');
  const origin=normalizeEndpoint(row.origin,reference.ticksPerQuarter);
  if(!inScope(origin,scope))invalid('Expected slide origin is outside the reviewed scope.');
  let target=null;
  if(DIRECTED.has(row.kind))target=normalizeEndpoint(row.target,reference.ticksPerQuarter);
  else if(row.target!==undefined&&row.target!==null)invalid('Incoming, outgoing and pick slides do not have a fretted destination.');
  const key=JSON.stringify([row.kind,origin]);
  if(seen.has(key))invalid('Duplicate expected slide origin and kind.');
  seen.add(key);return {kind:row.kind,origin,target};
 });
 return {schemaVersion:1,ticksPerQuarter:960,scope,slides};
}
function before(origin,target){
 const a=endpoint(origin),b=endpoint(target);
 return a.bar<b.bar||a.bar===b.bar&&(a.onset<b.onset||a.onset===b.onset&&a.voice===b.voice&&origin.beat.index<target.beat.index);
}
function buildSlideLedger(notes,problem,warn){
 const ledger=[];
 for(const note of notes){
  const origin=endpoint(note),out=OUT.get(note.slideOutType),incoming=IN.get(note.slideInType);
  if(note.slideOutType!==alpha.model.SlideOutType.None&&!out)problem('slide_kind',{origin,value:note.slideOutType});
  if(note.slideInType!==alpha.model.SlideInType.None&&!incoming)problem('slide_kind',{origin,value:note.slideInType});
  if(incoming)ledger.push({kind:incoming,origin,target:null});
  if(!out)continue;
  const target=DIRECTED.has(out)&&note.slideTarget?endpoint(note.slideTarget):null;
  ledger.push({kind:out,origin,target});
  if(!DIRECTED.has(out))continue;
  if(!target){problem('slide_target',{origin,kind:out});continue;}
  if(target.track!==origin.track||target.staff!==origin.staff)problem('slide_context',{origin,target});
  if(!before(note,note.slideTarget))problem('slide_time',{origin,target});
  if(note.isStringed&&note.slideTarget.isStringed&&target.string!==origin.string)problem('slide_string',{origin,target});
  if(note.slideTarget.slideOrigin!==note)problem('slide_reciprocal',{origin,target});
  if(target.voice!==origin.voice)warn({code:'slide_cross_voice',origin,target,review:'Verify the source connection.'});
  if(!origin.dead&&!target.dead&&note.realValue===note.slideTarget.realValue)warn({code:'slide_zero_interval',origin,target,review:'Check whether the slide belongs on the last tied segment before a pitch change.'});
 }
 return ledger;
}
function compareSlides(ledger,reference,score,problem){
 for(const range of reference.scope){
  const staff=score.tracks[range.track]?.staves[range.staff];
  if(!staff||range.toBar>staff.bars.length)invalid('Reviewed scope is outside the parsed score.');
 }
 const actual=ledger.filter(row=>inScope(row.origin,reference.scope)),remaining=actual.slice();
 const key=value=>JSON.stringify(value,(_key,item)=>item&&typeof item==='object'&&!Array.isArray(item)?Object.fromEntries(Object.entries(item).sort(([a],[b])=>a.localeCompare(b))):item);
 let missing=0,extra=0,wrongEndpoints=0;
 for(const expected of reference.slides){
  let index=remaining.findIndex(row=>key(row)===key(expected));
  if(index>=0){remaining.splice(index,1);continue;}
  index=remaining.findIndex(row=>row.kind===expected.kind&&key(row.origin)===key(expected.origin));
  if(index>=0){wrongEndpoints++;problem('slide_endpoint',{expected,actual:remaining.splice(index,1)[0]});}
  else{missing++;problem('slide_missing',{expected});}
 }
 for(const row of remaining){extra++;problem('slide_extra',{actual:row});}
 return {status:'compared',pass:missing+extra+wrongEndpoints===0,scope:reference.scope,expectedCount:reference.slides.length,actualCount:actual.length,missing,extra,wrongEndpoints};
}
module.exports={validateReference,buildSlideLedger,compareSlides,unsafeCodes};
