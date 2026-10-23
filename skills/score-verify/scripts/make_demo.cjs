#!/usr/bin/env node
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const alpha=require('@coderline/alphatab');
const m=alpha.model;
// Public SMuFL code points; alphaTab does not export its internal symbol enum.
const HEADS={black:0xe0a4,half:0xe0a3,whole:0xe0a2,cross:0xe0a9};

/** Entirely synthetic three-bar score: mixed meter, triplets and per-note ties. */
function makeDemoScore(){
  const score=new m.Score();
  score.title='Synthetic verification demonstration';
  for(let i=0;i<3;i++){
    const master=new m.MasterBar();
    master.timeSignatureNumerator=i===0?4:3;
    score.addMasterBar(master);
  }
  for(let trackIndex=0;trackIndex<2;trackIndex++){
    const track=new m.Track();
    track.name=trackIndex===0?'Guitar':'Percussion';
    score.addTrack(track);
    const staff=new m.Staff();
    staff.isPercussion=trackIndex===1;
    track.addStaff(staff);
    if(staff.isPercussion){
      track.playbackInfo.primaryChannel=9;
      track.playbackInfo.secondaryChannel=9;
      track.percussionArticulations=[
        new m.InstrumentArticulation('Kick',7,36,HEADS.black,HEADS.half,HEADS.whole),
        new m.InstrumentArticulation('Closed hi-hat',-1,42,HEADS.cross,HEADS.cross,HEADS.cross)
      ];
    }else{
      staff.stringTuning.tunings=[64,59,55,50,45,40];
      track.playbackInfo.program=24;
    }
    for(let barIndex=0;barIndex<3;barIndex++){
      const bar=new m.Bar();
      if(staff.isPercussion)bar.clef=m.Clef.Neutral;
      staff.addBar(bar);
      const voice=new m.Voice();
      bar.addVoice(voice);
      const values=barIndex===0?[4,8,4,2]:[4,4,4];
      for(let beatIndex=0;beatIndex<values.length;beatIndex++){
        const beat=new m.Beat();
        beat.duration=values[beatIndex];
        if(barIndex===0&&beatIndex<2){beat.tupletNumerator=3;beat.tupletDenominator=2;}
        voice.addBeat(beat);
        if(staff.isPercussion){
          for(const index of beatIndex<2?[0,1]:[0]){
            const note=new m.Note();
            note.percussionArticulation=index; // Index into this track's custom kit.
            note.octave=3;
            note.tone=index===0?0:6; // Stable identity when the engine resolves ties.
            note.isTieDestination=beatIndex===1&&index===0;
            beat.addNote(note);
          }
        }else{
          const note=new m.Note();
          note.string=6;note.fret=3;
          note.isTieDestination=barIndex===0&&beatIndex===1;
          beat.addNote(note);
        }
      }
    }
  }
  score.finish(new alpha.Settings());
  return score;
}
function main(){
  const output=process.argv[2];
  if(!output||process.argv.length!==3){console.error('Usage: node make_demo.cjs OUTPUT.gp');process.exitCode=2;return;}
  if(fs.existsSync(output)){console.error('Output already exists; choose a new path.');process.exitCode=2;return;}
  fs.mkdirSync(path.dirname(path.resolve(output)),{recursive:true});
  fs.writeFileSync(output,new alpha.exporter.Gp7Exporter().export(makeDemoScore(),new alpha.Settings()),{flag:'wx'});
  console.log('Wrote synthetic three-bar demonstration: '+output);
}
if(require.main===module)main();
module.exports={makeDemoScore};
