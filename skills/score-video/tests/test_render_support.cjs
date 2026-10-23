const test=require('node:test'),assert=require('node:assert/strict');
const a=require('@coderline/alphatab'),m=a.model;
const {assertSupportedScore}=require('../scripts/render_support.cjs');
const {fixture}=require('../scripts/make_demo.cjs');
test('accepts complete mixed-meter score, tuplets, rests and step tempo changes',()=>assert.equal(assertSupportedScore(fixture(),0).bars,2));
for(const [name,edit,pattern]of [
 ['repeat',s=>s.masterBars[0].isRepeatStart=true,/Repeats/],
 ['navigation',s=>s.masterBars[0].directions=new Set([1]),/navigation/],
 ['swing',s=>s.masterBars[0].tripletFeel=1,/Swing/],
 ['fermata',s=>s.masterBars[0].fermata=new Map([[0,{}]]),/Fermata/],
 ['free time',s=>s.masterBars[0].isFreeTime=true,/Free time/],
 ['pickup',s=>s.masterBars[0].isAnacrusis=true,/pickup/],
 ['sync point',s=>s.masterBars[0].syncPoints=[{}],/sync points/],
 ['tempo ramp',s=>s.masterBars[0].tempoAutomations[0].isLinear=true,/Tempo ramps/],
 ['on-beat grace note',s=>s.tracks[0].staves[0].bars[0].voices[0].beats[0].graceType=m.GraceType.OnBeat,/Grace/],
 ['second voice',s=>{const b=s.tracks[0].staves[0].bars[0];const v=new m.Voice();b.addVoice(v);const beat=new m.Beat();v.addBeat(beat);},/one explicit voice/],
 ['short bar',s=>s.tracks[0].staves[0].bars[0].voices[0].beats.pop(),/Incomplete/]
])test('rejects unsupported '+name,()=>{const s=fixture();edit(s);assert.throws(()=>assertSupportedScore(s,0),pattern);});
module.exports={fixture};

// A complete singleton before-beat ornament borrows time from its predecessor.
// The second ornament crosses a bar boundary (and the 4-bar partial boundary).
function graceFixture(){
 const score=new m.Score(),track=new m.Track(),staff=new m.Staff();
 score.title='Synthetic anticipatory grace timing';track.name='Synthetic Bass';
 score.addTrack(track);track.addStaff(staff);staff.stringTuning.tunings=[43,38,33,28];
 for(let i=0;i<5;i++){
  const master=new m.MasterBar();score.addMasterBar(master);
  const bar=new m.Bar(),voice=new m.Voice();staff.addBar(bar);bar.addVoice(voice);
  for(let j=0;j<4;j++){
   if((i===1&&j===1)||(i===4&&j===0)){
    const grace=new m.Beat();grace.duration=8;grace.graceType=m.GraceType.BeforeBeat;
    voice.addBeat(grace);const note=new m.Note();note.string=2;note.fret=10;note.slideOutType=m.SlideOutType.Legato;grace.addNote(note);
   }
   const beat=new m.Beat();beat.duration=4;voice.addBeat(beat);
   const note=new m.Note();note.string=2;note.fret=12;beat.addNote(note);
  }
 }
 score.finish(new a.Settings());return score;
}
test('accepts complete before-beat graces inside and across bars without changing the score',()=>{
 const s=graceFixture(),beats=s.tracks[0].staves[0].bars.flatMap(b=>b.voices[0].beats);
 const before=beats.map(b=>[b.playbackStart,b.playbackDuration,b.displayStart,b.displayDuration,b.graceType]);
 assert.equal(assertSupportedScore(s,0).bars,5);
 assert.deepEqual(beats.map(b=>[b.playbackStart,b.playbackDuration,b.displayStart,b.displayDuration,b.graceType]),before);
 assert.deepEqual(beats.filter(b=>b.graceType).map(b=>[b.playbackStart,b.playbackDuration]),[[840,120],[-120,120]]);
 assert.deepEqual(beats.filter(b=>b.graceType).map(b=>b.notes[0].slideTarget.fret),[12,12]);
});
for(const [name,edit,pattern]of [
 ['incomplete grace group',s=>s.tracks[0].staves[0].bars[1].voices[0].beats[1].graceGroup.isComplete=false,/Grace/],
 ['grace group with multiple beats',s=>{const b=s.tracks[0].staves[0].bars[1].voices[0].beats[1];b.graceGroup.beats.push(b);},/Grace/],
 ['grace predecessor overlaps',s=>s.tracks[0].staves[0].bars[0].voices[0].beats[3].playbackDuration+=1,/playback|Grace|Incomplete/],
 ['grace before time zero',s=>{const b=s.tracks[0].staves[0].bars[0].voices[0].beats[0];b.playbackStart=-120;},/playback|Grace/],
 ['grace target missing',s=>s.tracks[0].staves[0].bars[1].voices[0].beats[2].graceGroup=null,/Grace/]
])test('rejects unproved '+name,()=>{const s=graceFixture();edit(s);assert.throws(()=>assertSupportedScore(s,0),pattern);});
module.exports.graceFixture=graceFixture;

test('grace geometry requires room for distinct fret numbers and a slide',()=>{
 const {assertGraceGeometry}=require('../scripts/render_support.cjs');
 const bars=[{bar:2,beats:[
  {index:0,voice:0,grace:m.GraceType.BeforeBeat,noteBounds:[{x:100,y:20,w:12,h:16}]},
  {index:1,voice:0,grace:m.GraceType.None,noteBounds:[{x:121,y:20,w:16,h:16}]}
 ]}];
 assert.equal(assertGraceGeometry(bars).minimumGapPixels,9);
 bars[0].beats[1].noteBounds[0].x=110;
 assert.throws(()=>assertGraceGeometry(bars),/pixels-per-quarter/);
 bars[0].beats[0].noteBounds=[];
 assert.throws(()=>assertGraceGeometry(bars),/geometry/);
});

test('grace geometry also rejects predecessor collisions across a bar boundary',()=>{
 const {assertGraceGeometry}=require('../scripts/render_support.cjs');
 const bars=[{bar:1,beats:[{index:0,voice:0,grace:0,rest:false,noteBounds:[{x:85,y:20,w:20,h:16}]}]},
  {bar:2,beats:[
   {index:0,voice:0,grace:m.GraceType.BeforeBeat,noteBounds:[{x:100,y:20,w:12,h:16}]},
   {index:1,voice:0,grace:0,noteBounds:[{x:121,y:20,w:16,h:16}]}
  ]}];
 assert.throws(()=>assertGraceGeometry(bars),/pixels-per-quarter/);
 bars[0].beats[0].noteBounds[0].x=70;
 assert.equal(assertGraceGeometry(bars).minimumGapPixels,9);
 bars[0].beats[0].noteBounds=[];
 assert.throws(()=>assertGraceGeometry(bars),/geometry/);
 bars[0].beats[0].rest=true;
 assert.equal(assertGraceGeometry(bars).minimumGapPixels,9);
});
