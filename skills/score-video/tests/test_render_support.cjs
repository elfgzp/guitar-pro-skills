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
 ['grace note',s=>s.tracks[0].staves[0].bars[0].voices[0].beats[0].graceType=1,/Grace/],
 ['second voice',s=>{const b=s.tracks[0].staves[0].bars[0];const v=new m.Voice();b.addVoice(v);const beat=new m.Beat();v.addBeat(beat);},/one explicit voice/],
 ['short bar',s=>s.tracks[0].staves[0].bars[0].voices[0].beats.pop(),/Incomplete/]
])test('rejects unsupported '+name,()=>{const s=fixture();edit(s);assert.throws(()=>assertSupportedScore(s,0),pattern);});
module.exports={fixture};
