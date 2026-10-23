#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),a=require('@coderline/alphatab'),m=a.model;
function fixture(){
 const s=new m.Score(),track=new m.Track(),staff=new m.Staff();
 s.title='Synthetic scrolling TAB timing';track.name='Synthetic Guitar';s.addTrack(track);track.addStaff(staff);staff.stringTuning.tunings=[64,59,55,50,45,40];
 for(let i=0;i<2;i++){
  const master=new m.MasterBar();master.timeSignatureNumerator=i===0?4:3;s.addMasterBar(master);
  const tempo=new m.Automation();tempo.type=m.AutomationType.Tempo;tempo.value=i===0?120:90;master.tempoAutomations.push(tempo);
  const bar=new m.Bar(),voice=new m.Voice();staff.addBar(bar);bar.addVoice(voice);
  const durations=i===0?[4,8,4,2]:[4,4,4];
  for(const [j,duration]of durations.entries()){
   const beat=new m.Beat();beat.duration=duration;if(i===0&&j<2){beat.tupletNumerator=3;beat.tupletDenominator=2;}voice.addBeat(beat);
   if(!(i===1&&j===0)){const n=new m.Note();n.string=6;n.fret=3+j;beat.addNote(n);}
  }
 }
 s.finish(new a.Settings());return s;
}
if(require.main===module){const output=process.argv[2];if(!output)throw Error('Usage: node make_demo.cjs output.gp');fs.writeFileSync(output,new a.exporter.Gp7Exporter().export(fixture(),new a.Settings()),{flag:'wx'});}
module.exports={fixture};
