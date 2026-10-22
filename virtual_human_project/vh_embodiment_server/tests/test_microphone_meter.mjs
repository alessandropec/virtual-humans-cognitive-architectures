import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

// Exercise the actual meter functions without avatar rendering or hardware.
const source=readFileSync(new URL('../app/avatar.js',import.meta.url),'utf8');
const start=source.indexOf('  let previewStream =');
const end=source.indexOf('  const motions =',start);
const contexts=[], events=[];
let tick;
class AudioContext {
  state='suspended'; destination={};
  constructor(){contexts.push(this);}
  async resume(){this.state='running';}
  async close(){this.state='closed';}
  createMediaStreamSource(input){this.input=input;return {connect(){},disconnect(){}};}
  createAnalyser(){return {fftSize:2048,connect(){},disconnect(){},getFloatTimeDomainData(samples){samples.fill(.1);}};}
  createGain(){const node={gain:{value:1},connect(){},disconnect(){}};this.sink=node;return node;}
}
const head={audioCtx:{state:'suspended',resume(){throw Error('Must not use avatar context');}}};
const meter=new Function('AudioContext','head','emit','setInterval','clearInterval',source.slice(start,end)+'; return {monitor,stopMeter};')(
  AudioContext,head,(name,detail)=>events.push({name,detail}),fn=>{tick=fn;return 1;},()=>{tick=null;});
const input={getAudioTracks:()=>[{label:'Test input'}]};
await meter.monitor(input);
assert.equal(contexts[0].state,'running');
assert.equal(contexts[0].input,input);
assert.equal(contexts[0].sink.gain.value,0,'Never play microphone back');
tick();
assert.ok(events.find(event=>event.name==='level' && event.detail.percent>50));
assert.equal(head.audioCtx.state,'suspended','Avatar suspension must not suspend capture');
await meter.monitor(input);
assert.equal(contexts[0].state,'closed','Replacing meter releases the previous audio context');
meter.stopMeter();
assert.equal(contexts[1].state,'closed');
assert.equal(tick,null);
assert.equal(events.at(-1).detail.percent,0);
console.log('PASS microphone meter independent of suspended avatar, level calculation, muted output and cleanup');
