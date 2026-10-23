/* alphaTab adapter: place native glyphs on a musical-time axis; never stretch pixels. */
(function (global) {
 'use strict';
 const SUPPORTED_VERSION = '1.8.4';
 function installProportionalLayout(alpha, pixelsPerQuarter) {
  if (alpha.meta.version !== SUPPORTED_VERSION) throw Error('Proportional layout requires alphaTab '+SUPPORTED_VERSION+'; found '+alpha.meta.version);
  if (!Number.isFinite(pixelsPerQuarter) || pixelsPerQuarter < 40) throw Error('pixelsPerQuarter must be at least 40');
  const factory = alpha.Environment.layoutEngines.get(alpha.LayoutMode.Horizontal);
  if (!factory || typeof factory.createLayout !== 'function') throw Error('Unsupported alphaTab layout factory');
  alpha.Environment.layoutEngines.set(alpha.LayoutMode.Horizontal, {
   vertical: false,
   createLayout(renderer) {
    const layout = factory.createLayout(renderer);
    if (typeof layout._scaleBars !== 'function' || typeof layout._alignRenderers !== 'function') throw Error('Unsupported alphaTab horizontal layout shape');
    const unitsPerTick = pixelsPerQuarter / (960 * renderer.settings.display.scale);
    const anchorPad = 8;
    layout._scaleBars = function (result) {
     result.width = 0;
     for (const r of result.renderers) {
      if (!r.voiceContainer?.beatGlyphs || !r._preBeatGlyphs || !r._postBeatGlyphs || typeof r.updateSizes !== 'function' || typeof r.applyLayoutingInfo !== 'function') throw Error('Unsupported alphaTab bar renderer shape');
      const first = r.bar.index === renderer.settings.display.startBar - 1;
      // The TAB clef and initial meter occur once, before musical time zero.
      // Later barlines and meter changes must not add width to the time axis.
      const prefix = first ? r._preBeatGlyphs.width : 0;
      const duration = r.bar.masterBar.calculateDuration();
      const targetWidth = duration * unitsPerTick + prefix;
      if (!first) r._preBeatGlyphs.paint = () => {};
      r.scaleToWidth = function () {
       this.voiceContainer.x = prefix + anchorPad;
       this.voiceContainer.width = duration * unitsPerTick;
       for (const beats of this.voiceContainer.beatGlyphs.values()) {
        for (const b of beats) {
         if (!b.beat || !Number.isFinite(b.onTimeX)) throw Error('Unsupported alphaTab beat glyph shape');
         b.x = b.beat.playbackStart * unitsPerTick - b.onTimeX;
        }
        for (let i=0; i<beats.length; i++) beats[i].scaleToWidth(i+1<beats.length ? beats[i+1].x-beats[i].x : this.voiceContainer.width-beats[i].x);
       }
       // Native beams, ties, slides and effects resolve their endpoints from
       // these moved glyphs; font metrics, y coordinates and note shapes stay intact.
       for (const voice of this.helpers.beamHelpers) for (const beam of voice) beam.alignWithBeats();
       this._postBeatGlyphs.x = targetWidth - this._postBeatGlyphs.width;
       this.width = targetWidth;
       this.topEffects.alignGlyphs();
       this.bottomEffects.alignGlyphs();
      };
      // Finalization may recalculate overflow/width and reset container.x.
      // Reapply timing positions after both native size-refresh paths.
      const updateSizes = r.updateSizes.bind(r);
      r.updateSizes = function () { updateSizes(); this.scaleToWidth(targetWidth); };
      const applyLayoutingInfo = r.applyLayoutingInfo.bind(r);
      r.applyLayoutingInfo = function () { const changed=applyLayoutingInfo(); this.scaleToWidth(targetWidth); return changed; };
      const mb = r.bar.masterBar, previous = r.bar.previousBar?.masterBar;
      if (!first && previous && (mb.timeSignatureNumerator!==previous.timeSignatureNumerator || mb.timeSignatureDenominator!==previous.timeSignatureDenominator)) {
       // Put a meter label above the temporal bar boundary, without horizontal overhead.
       r.registerOverflowTop(20);
       const paintContent = r.paintContent.bind(r);
       r.paintContent = function (cx,cy,canvas) {
        paintContent(cx,cy,canvas);
        const font=canvas.font,color=canvas.color,align=canvas.textAlign;
        canvas.font=this.resources.barNumberFont; canvas.color=this.resources.mainGlyphColor; canvas.textAlign=alpha.platform.TextAlign.Left;
        canvas.fillText(mb.timeSignatureNumerator+'/'+mb.timeSignatureDenominator,cx+this.x+anchorPad,cy+this.y-16);
        canvas.font=font; canvas.color=color; canvas.textAlign=align;
       };
      }
      r.scaleToWidth(targetWidth);
      result.width = Math.max(result.width,r.width);
     }
    };
    return layout;
   }
  });
 }
 if (typeof module==='object' && module.exports) module.exports={installProportionalLayout,SUPPORTED_VERSION};
 else global.installProportionalLayout=installProportionalLayout;
})(globalThis);
