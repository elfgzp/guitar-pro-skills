const test=require('node:test'),assert=require('node:assert/strict');
const {installProportionalLayout}=require('../scripts/proportional_layout.js');
function harness(version='1.8.4'){
 const factory={createLayout:()=>({_scaleBars(){},_alignRenderers(){}})};
 const alpha={meta:{version},LayoutMode:{Horizontal:1},Environment:{layoutEngines:new Map([[1,factory]])},platform:{TextAlign:{Left:0}}};
 const settings={display:{scale:2,startBar:1}};
 return {alpha,settings};
}
function bar(index,prefix){
 const beats=[0,240,960].map((start,i)=>({beat:{playbackStart:start},onTimeX:8+i,x:0,width:12,scaleToWidth(w){this.width=w;}}));
 return {bar:{index,masterBar:{calculateDuration:()=>3840,timeSignatureNumerator:4,timeSignatureDenominator:4}},
  _preBeatGlyphs:{width:prefix,paint(){}},_postBeatGlyphs:{width:4,x:0},
  voiceContainer:{x:prefix,width:0,beatGlyphs:new Map([[0,beats]])},
  helpers:{beamHelpers:[]},topEffects:{alignGlyphs(){}},bottomEffects:{alignGlyphs(){}},
  updateSizes(){this.voiceContainer.x=999;this.width=999;},applyLayoutingInfo(){this.voiceContainer.x=777;return true;}
 };
}
test('all note/rest anchors use ticks across bars; later prefix widths consume no musical time',()=>{
 const {alpha,settings}=harness(); installProportionalLayout(alpha,120);
 const layout=alpha.Environment.layoutEngines.get(1).createLayout({settings});
 const first=bar(0,20),second=bar(1,55);
 for(const r of [first,second])layout._scaleBars({renderers:[r]});
 assert.equal(first.width,260);assert.equal(second.width,240);
 const x=(r,b)=>r.voiceContainer.x+b.x+b.onTimeX;
 assert.equal(x(first,first.voiceContainer.beatGlyphs.get(0)[0]),28);
 for(const [r,start]of [[first,0],[second,260]])for(const b of r.voiceContainer.beatGlyphs.get(0)){
  const tick=(r===first?0:3840)+b.beat.playbackStart;
  assert.equal(start+x(r,b),28+tick/960*60);
 }
});
test('native final size and layout refreshes cannot reintroduce spacing overhead',()=>{
 const {alpha,settings}=harness();installProportionalLayout(alpha,120);
 const layout=alpha.Environment.layoutEngines.get(1).createLayout({settings}),r=bar(1,55);layout._scaleBars({renderers:[r]});
 r.updateSizes();assert.equal(r.voiceContainer.x,8);assert.equal(r.width,240);
 assert.equal(r.applyLayoutingInfo(),true);assert.equal(r.voiceContainer.x,8);assert.equal(r.width,240);
});
test('internal adapter fails closed for unproved alphaTab versions and invalid density',()=>{
 assert.throws(()=>installProportionalLayout(harness('1.9.0').alpha,120),/requires alphaTab 1.8.4/);
 assert.throws(()=>installProportionalLayout(harness().alpha,0),/at least 40/);
 const {alpha}=harness();alpha.Environment.layoutEngines.get(1).createLayout=()=>({});installProportionalLayout(alpha,120);
 assert.throws(()=>alpha.Environment.layoutEngines.get(1).createLayout({settings:{}}),/horizontal layout shape/);
});
