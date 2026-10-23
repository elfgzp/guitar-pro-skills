'use strict';
const {model:{GraceType}}=require('@coderline/alphatab');

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
 const playbackBeats=[];
 for(const bar of staff.bars){
  const active=bar.voices.filter(v=>v.beats.some(b=>!b.isEmpty));
  if(active.length!==1)throw Error('Exactly one explicit voice, including rests, is required at bar '+(bar.index+1));
  for(const beat of active[0].beats){
   if(beat.graceType){
    // Proven subset: one before-beat note, complete in the same notated bar.
    // It steals 120 ticks from its predecessor, possibly in the prior bar.
    const group=beat.graceGroup,previous=beat.previousBeat,target=beat.nextBeat;
    if(beat.graceType!==GraceType.BeforeBeat||beat.notes.length!==1||beat.isRest||beat.isEmpty||
       !group?.isComplete||group.beats.length!==1||group.beats[0]!==beat||
       !previous||previous.graceType!==GraceType.None||!target||target.graceType!==GraceType.None||
       target.voice!==beat.voice||target.graceGroup!==group||beat.displayDuration!==0||
       beat.displayStart!==target.displayStart||beat.playbackDuration!==120||
       previous.absolutePlaybackStart+previous.playbackDuration!==beat.absolutePlaybackStart||
       beat.absolutePlaybackStart+beat.playbackDuration!==target.absolutePlaybackStart){
     throw Error('Grace timing requires a complete single before-beat note borrowing 120 ticks at bar '+(bar.index+1));
    }
   }
   if(beat.fermata)throw Error('Fermata timing is not supported at bar '+(bar.index+1));
  }
  // Notated durations fill each bar even when a grace steals playback from
  // the preceding bar. Validate the actual playback once over the whole track.
  let duration=0;const expected=score.masterBars[bar.index].calculateDuration();
  for(const beat of active[0].beats){
   if(!beat.graceType){
    if(beat.displayStart!==duration)throw Error('Incomplete or overfull selected voice at bar '+(bar.index+1));
    duration+=beat.displayDuration;
   }
   playbackBeats.push(beat);
  }
  if(duration!==expected)throw Error('Incomplete or overfull selected voice at bar '+(bar.index+1));
 }
 let end=0;
 for(const beat of playbackBeats){
  if(!Number.isFinite(beat.playbackDuration)||beat.playbackDuration<=0||beat.absolutePlaybackStart!==end){
   throw Error('Selected playback must cover time zero through the end without gaps or overlaps');
  }
  end+=beat.playbackDuration;
 }
 const last=score.masterBars.at(-1);
 if(end!==last.start+last.calculateDuration())throw Error('Incomplete selected playback duration');
 return {bars:staff.bars.length,trackIndex,trackName:track.name};
}

/** Require readable native fret glyphs; do not fix collisions by shifting time. */
function assertGraceGeometry(bars){
 let count=0,minimumGapPixels=Infinity;
 const sequence=bars.flatMap(bar=>bar.beats.filter(beat=>!beat.empty).map(beat=>({bar,beat})));
 for(const [index,{bar,beat}]of sequence.entries()){
  if(!beat.grace)continue;
  const target=bar.beats.find(b=>b.voice===beat.voice&&b.index===beat.index+1);
  const notes=beat.noteBounds,targetNotes=target?.noteBounds;
  const valid=rect=>rect&&['x','y','w','h'].every(k=>Number.isFinite(rect[k]))&&rect.w>0&&rect.h>0;
  if(notes?.length!==1||!valid(notes[0])||!targetNotes?.length||!targetNotes.every(valid))throw Error('Missing grace note geometry at bar '+bar.bar);
  const right=notes[0].x+notes[0].w,gaps=targetNotes.map(n=>n.x-right);
  // Before-beat playback borrows from the predecessor. Check that neighbour
  // too, including the last beat of the prior bar; a rest has no fret glyph.
  const previous=sequence[index-1]?.beat;
  if(previous&&!previous.rest){
   if(!previous.noteBounds?.length||!previous.noteBounds.every(valid))throw Error('Missing predecessor note geometry at bar '+bar.bar);
   gaps.push(...previous.noteBounds.map(n=>notes[0].x-(n.x+n.w)));
  }
  const gap=Math.min(...gaps);
  if(gap<4)throw Error('Grace fret numbers need more horizontal room at bar '+bar.bar+' (gap '+gap.toFixed(2)+' px); increase --pixels-per-quarter');
  minimumGapPixels=Math.min(minimumGapPixels,gap);count++;
 }
 return {count,minimumGapPixels:count?minimumGapPixels:null};
}
module.exports={assertSupportedScore,assertGraceGeometry};
