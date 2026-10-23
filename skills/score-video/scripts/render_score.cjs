#!/usr/bin/env node
// Dependencies: @coderline/alphatab 1.8.4, playwright. No soundfont is needed.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const {chromium}=require('playwright');
const alpha=require('@coderline/alphatab');
const {assertSupportedScore}=require('./render_support.cjs');

function options(argv){
 const o={track:0,scale:1.6,height:360,tileWidth:2048,yOffset:18};
 const names={'--input':'input','--output':'output','--track':'track','--scale':'scale','--height':'height','--tile-width':'tileWidth','--y-offset':'yOffset','--chromium':'chromium'};
 for(let i=0;i<argv.length;i++){if(argv[i]==='--help'){console.log('node render_score.cjs --input score.gp --output assets --track 0 [--chromium /path/to/browser] [--height 360 --scale 1.6 --tile-width 2048 --y-offset 18]');process.exit(0);}const n=names[argv[i]];if(!n||argv[i+1]===undefined)throw Error('Unknown or incomplete argument: '+argv[i]);o[n]=argv[++i];}
 if(!o.input||!o.output)throw Error('--input and --output are required');
 for(const n of ['track','scale','height','tileWidth','yOffset'])o[n]=Number(o[n]);
 if(!Number.isInteger(o.track)||o.track<0||!Number.isFinite(o.scale)||o.scale<=0||o.scale>4||![o.height,o.tileWidth,o.yOffset].every(Number.isInteger)||o.height<64||o.tileWidth<64||o.yOffset<0)throw Error('Invalid numeric option');
 return o;
}

async function main(){
 const opt=options(process.argv.slice(2)),source=fs.readFileSync(opt.input),output=path.resolve(opt.output);
 assertSupportedScore(alpha.importer.ScoreLoader.loadScoreFromBytes(source),opt.track);
 if(fs.existsSync(output)&&(!fs.lstatSync(output).isDirectory()||fs.readdirSync(output).length))throw Error('--output must be a new or empty directory; existing artifacts are not overwritten');
 fs.mkdirSync(output,{recursive:true});
 const alphaDir=path.dirname(require.resolve('@coderline/alphatab'));
 const pageHtml=fs.readFileSync(path.join(__dirname,'render.html'));
 const config={track:opt.track,scale:opt.scale};
 const mime={'.js':'application/javascript','.woff2':'font/woff2','.woff':'font/woff','.ttf':'font/ttf','.json':'application/json'};
 const server=http.createServer((req,res)=>{
  const u=new URL(req.url,'http://localhost');let body,type='application/octet-stream';
  try{if(u.pathname==='/'){body=pageHtml;type='text/html';}
   else if(u.pathname==='/config'){body=JSON.stringify(config);type='application/json';}
   else if(u.pathname==='/score')body=source;
   else if(u.pathname==='/alphaTab.js'){body=fs.readFileSync(path.join(alphaDir,'alphaTab.js'));type='application/javascript';}
   else if(/^\/fonts\/[\w.-]+$/.test(u.pathname)){const file=u.pathname.slice('/fonts/'.length);body=fs.readFileSync(path.join(alphaDir,'font',file));type=mime[path.extname(file)]||type;}
   else{res.writeHead(404);res.end();return;}
   res.writeHead(200,{'Content-Type':type,'Cache-Control':'no-store'});res.end(body);
  }catch(e){res.writeHead(500);res.end(String(e.message));}
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 let browser;
 try{
  browser=await chromium.launch({headless:true,...(opt.chromium?{executablePath:opt.chromium}:{})});
  const page=await browser.newPage({viewport:{width:opt.tileWidth,height:opt.height},deviceScaleFactor:1});
  const consoleErrors=[];page.on('pageerror',e=>consoleErrors.push(String(e)));
  await page.goto(`http://127.0.0.1:${server.address().port}/`,{waitUntil:'networkidle'});
  await page.waitForFunction(()=>window.evidence?.finished||window.evidence?.errors.length,{timeout:120000});
  await page.evaluate(()=>document.fonts.ready);
  const raw=await page.evaluate(()=>{
   if(evidence.errors.length)throw Error(evidence.errors.join('; '));
   const bounds=o=>o?{x:o.x,y:o.y,w:o.w,h:o.h}:null,lookup=api.renderer.boundsLookup;
   const midi=new alphaTab.midi.MidiFile(),generator=new alphaTab.midi.MidiFileGenerator(api.score,api.settings,new alphaTab.midi.AlphaSynthMidiFileHandler(midi));generator.generate();
   return {...evidence,fontFaces:Array.from(document.fonts).map(f=>({family:f.family,status:f.status})),tempo:api.score.tempo,trackName:api.score.tracks[config.track].name,ticksPerQuarter:midi.division,tickShift:midi.tickShift,
    playbackBars:generator.tickLookup.masterBars.map(m=>({bar:m.masterBar.index+1,startTick:m.start,endTick:m.end,tempo:m.tempoChanges.map(t=>({tick:t.tick,bpm:t.tempo}))})),
    bars:api.score.tracks[config.track].staves[0].bars.map(b=>{const mb=api.score.masterBars[b.index],bb=lookup.findMasterBar(mb);return{bar:b.index+1,startTick:mb.start,durationTick:mb.calculateDuration(),numerator:mb.timeSignatureNumerator,denominator:mb.timeSignatureDenominator,real:bounds(bb?.realBounds),line:bounds(bb?.lineAlignedBounds),beats:b.voices.flatMap(v=>v.beats.map(beat=>{const be=lookup.findBeat(beat);return{voice:v.index,index:beat.index,relativeStartTick:beat.playbackStart,durationTick:beat.playbackDuration,rest:beat.isRest,empty:beat.isEmpty,grace:beat.graceType,notes:beat.notes.length,x:be?.onNotesX,real:bounds(be?.realBounds)}}))}})
   };
  });
  if(consoleErrors.length)throw Error(consoleErrors.join('; '));
  if(!raw.fontFaces.some(f=>/alphaTab/i.test(f.family)&&f.status==='loaded'))throw Error('alphaTab font was not loaded');
  if(raw.chunks.length===0)throw Error('No rendered notation');
  if(raw.tickShift!==0)throw Error('Score playback has an initial grace-note tick shift, which is not supported');
  if(raw.playbackBars.length!==raw.bars.length||raw.playbackBars.some((b,i)=>b.bar!==i+1))throw Error('Playback includes a navigation or repeat not supported by continuous scrolling');
  if(raw.chunks.some(c=>c.height+opt.yOffset>opt.height))throw Error('Notation would be clipped vertically; increase --height');
  const width=Math.ceil(Math.max(...raw.chunks.map(c=>c.x+c.width))),height=opt.height;
  const tempoMap=[{tick:0,bpm:raw.tempo},...raw.playbackBars.flatMap(b=>b.tempo)].sort((a,b)=>a.tick-b.tick);
  const secondsAt=tick=>{let seconds=0,prevTick=0,bpm=raw.tempo;for(const t of tempoMap){if(t.tick>tick)break;seconds+=(t.tick-prevTick)/raw.ticksPerQuarter*60/bpm;prevTick=t.tick;bpm=t.bpm;}return seconds+(tick-prevTick)/raw.ticksPerQuarter*60/bpm;};
  const anchors=[],barStartSeconds=[];
  for(const p of raw.playbackBars){
   const bar=raw.bars[p.bar-1],unique=new Map();
   for(const beat of bar.beats.filter(b=>Number.isFinite(b.x)&&!b.empty).sort((a,b)=>a.relativeStartTick-b.relativeStartTick||a.voice-b.voice)){
    const tick=p.startTick+beat.relativeStartTick;if(tick<0||tick>=p.endTick||unique.has(tick))continue;
    unique.set(tick,{seconds:secondsAt(tick),tick,x:beat.x,bar:p.bar,beat:beat.index,voice:beat.voice,rest:beat.rest,grace:beat.grace});
   }
   if(unique.size===0)throw Error('No timed beat geometry in bar '+p.bar);
   const seq=[...unique.values()].sort((a,b)=>a.tick-b.tick);
   anchors.push(...seq);barStartSeconds.push({bar:p.bar,seconds:secondsAt(p.startTick),endSeconds:secondsAt(p.endTick),numerator:bar.numerator,denominator:bar.denominator});
  }
  const last=raw.playbackBars.at(-1),lastBounds=raw.bars[last.bar-1].real,durationSeconds=secondsAt(last.endTick);
  anchors.push({seconds:durationSeconds,tick:last.endTick,x:lastBounds.x+lastBounds.w,bar:last.bar,beat:null,end:true});
  if(anchors.some((a,i)=>i&&a.seconds<anchors[i-1].seconds))throw Error('Playback anchors are not chronological');
  if(anchors.some((a,i)=>i&&a.x<anchors[i-1].x))throw Error('Playback requires backward geometry movement');
  const manifest={schemaVersion:1,engine:'alphaTab 1.8.4',layout:'continuous-horizontal',sourceSha256:crypto.createHash('sha256').update(source).digest('hex'),trackIndex:opt.track,name:raw.trackName,width,height,tileWidth:opt.tileWidth,yOffset:opt.yOffset,durationSeconds,ticksPerQuarter:raw.ticksPerQuarter,tickShift:raw.tickShift,bpm:raw.tempo,tempoMap,tiles:[],anchors,barStartSeconds,staffTop:raw.bars[0].line.y+opt.yOffset,staffBottom:raw.bars[0].line.y+raw.bars[0].line.h+opt.yOffset,notes:'Coordinates refer to horizontal notation; seconds refer to the generated MIDI playback timeline. Only sequential forward playback is supported.'};
  await page.evaluate(()=>{
   document.querySelector('#score').style.visibility='hidden';
   const stage=document.createElement('div');stage.id='tile';stage.className=document.querySelector('#score .at-surface').className;stage.style.cssText='position:absolute;left:0;top:0;width:100vw;height:100vh;overflow:hidden';document.body.append(stage);
   const style=document.createElement('style');style.textContent='#tile svg{filter:drop-shadow(0 1px 1.1px rgba(0,0,0,.95)) drop-shadow(1px 0 0 rgba(0,0,0,.85)) drop-shadow(-1px 0 0 rgba(0,0,0,.85))}';document.head.append(style);
  });
  for(let x=0,n=1;x<width;x+=opt.tileWidth,n++){
   // Place only nearby partials at local coordinates: giant translated browser layers
   // can silently become blank past a GPU/browser texture limit (~32k pixels).
   const chunks=raw.chunks.filter(c=>c.x+c.width>x-6&&c.x<x+opt.tileWidth+6);
   await page.evaluate(({x,y,chunks})=>{const stage=document.querySelector('#tile');stage.replaceChildren();for(const c of chunks){const wrap=document.createElement('div');wrap.style.cssText=`position:absolute;left:${c.x-x}px;top:${c.y+y}px`;wrap.innerHTML=c.svg;wrap.firstElementChild.setAttribute('width',`${c.width}px`);wrap.firstElementChild.setAttribute('height',`${c.height}px`);stage.append(wrap);}},{x,y:opt.yOffset,chunks});
   const glyphFont=await page.evaluate(()=>{const glyph=document.querySelector('#tile .at');return glyph?getComputedStyle(glyph).fontFamily:null;});
   if(glyphFont&&!/alphaTab/i.test(glyphFont))throw Error('Music glyphs lost their font while tiling');
   await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   const file=`tile-${String(n).padStart(3,'0')}.png`;
   const png=await page.screenshot({path:path.join(output,file),omitBackground:true,clip:{x:0,y:0,width:opt.tileWidth,height}});
   const pixels=await page.evaluate(async bytes=>{
    const bitmap=await createImageBitmap(new Blob([new Uint8Array(bytes)],{type:'image/png'}));
    const canvas=document.createElement('canvas');canvas.width=bitmap.width;canvas.height=bitmap.height;
    const ctx=canvas.getContext('2d');ctx.drawImage(bitmap,0,0);const rgba=ctx.getImageData(0,0,canvas.width,canvas.height).data;
    let alphaMin=255,alphaMax=0,visiblePixels=0;for(let i=3;i<rgba.length;i+=4){alphaMin=Math.min(alphaMin,rgba[i]);alphaMax=Math.max(alphaMax,rgba[i]);if(rgba[i])visiblePixels++;}bitmap.close();return{alphaMin,alphaMax,visiblePixels};
   },Array.from(png));
   if(pixels.alphaMin!==0||pixels.alphaMax!==255||pixels.visiblePixels===0)throw Error('Tile is blank or lacks real transparency: '+file);
   manifest.tiles.push({file,x,y:0,width:opt.tileWidth,height,...pixels});
  }
  fs.writeFileSync(path.join(output,'manifest.json'),JSON.stringify(manifest,null,2));
  fs.writeFileSync(path.join(output,'geometry.raw.json'),JSON.stringify({...raw,consoleErrors},null,2));
  for(const [i,c]of raw.chunks.entries())fs.writeFileSync(path.join(output,`part-${String(i+1).padStart(3,'0')}.svg`),c.svg);
  console.log(JSON.stringify({output,sourceSha256:manifest.sourceSha256,tiles:manifest.tiles.length,bars:raw.bars.length,anchors:anchors.length,width,height,durationSeconds,fontFaces:raw.fontFaces,errors:consoleErrors}));
 }finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
}
main().catch(e=>{console.error(e.stack||e);process.exitCode=1;});
