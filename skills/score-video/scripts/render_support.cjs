'use strict';

/** Fail closed until the corresponding playback-to-geometry case has proof. */
function assertSupportedScore(score, trackIndex) {
 const track=score.tracks[trackIndex];
 if(!track)throw Error('Selected track index does not exist');
 if(track.staves.length!==1)throw Error('This renderer currently supports one staff per selected track');
 const staff=track.staves[0];
 if(staff.isPercussion||staff.stringTuning.tunings.length===0)throw Error('Select a fretted instrument track with string tuning');
 for(const bar of score.masterBars){
  const where=' at bar '+(bar.index+1);
  if(bar.isRepeatStart||bar.repeatCount>0||bar.alternateEndings||bar.directions?.size)throw Error('Repeats and navigation require an unfolded score'+where);
  if(bar.isFreeTime||bar.isAnacrusis)throw Error('Free time and pickup timing are not supported'+where);
  if(bar.tripletFeel)throw Error('Swing/triplet feel needs separate playback timing support'+where);
  if(bar.fermata?.size)throw Error('Fermata timing is not supported'+where);
  if(bar.syncPoints?.length)throw Error('Backing-track sync points are not supported'+where);
  if(bar.tempoAutomations.some(t=>t.isLinear))throw Error('Tempo ramps are not supported; use explicit step tempo changes'+where);
 }
 for(const bar of staff.bars){
  const active=bar.voices.filter(v=>v.beats.some(b=>!b.isEmpty));
  if(active.length!==1)throw Error('Exactly one explicit voice, including rests, is required at bar '+(bar.index+1));
  for(const beat of active[0].beats){
   if(beat.graceType)throw Error('Grace-note cursor timing is not supported at bar '+(bar.index+1));
   if(beat.fermata)throw Error('Fermata timing is not supported at bar '+(bar.index+1));
  }
  const duration=active[0].beats.reduce((sum,b)=>sum+b.playbackDuration,0),expected=score.masterBars[bar.index].calculateDuration();
  if(duration!==expected)throw Error('Incomplete or overfull selected voice at bar '+(bar.index+1));
 }
 return {bars:staff.bars.length,trackIndex,trackName:track.name};
}

module.exports={assertSupportedScore};
