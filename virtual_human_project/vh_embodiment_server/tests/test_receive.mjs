import {listInputs,openInput} from '../app/assets/microphone.js';
// Response behaviour and gesture deadlines, without a renderer or real waiting.
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {Vector3} from '../app/lib/dependencies/three/build/three.core.js';
let picture=null, head, now=0, timerId=0;
const timers=new Map();
globalThis.setTimeout=(fn,delay)=>{const id=++timerId;timers.set(id,{fn,at:now+delay});return id;};
globalThis.clearTimeout=id=>timers.delete(id);
function advance(ms){
  const end=now+ms;
  while(true){
    const next=[...timers].sort((a,b)=>a[1].at-b[1].at||a[0]-b[0])[0];
    if(!next||next[1].at>end)break;
    timers.delete(next[0]);now=next[1].at;next[1].fn();
  }
  now=end;
}
globalThis.devicePixelRatio=1;
globalThis.document={addEventListener(){},querySelectorAll:()=>[],querySelector:()=>({replaceChildren(...items){picture=items[0]||null;}})};
globalThis.window={addEventListener(){}};
globalThis.DelayNode=class {connect(){}};
globalThis.Image=class {async decode(){if(this.src==='bad')throw Error('Image failed');}};
globalThis.fetch=async()=>({ok:true,json:async()=>({gestures:[{id:'handup'},{id:'index'},{id:'ok'}],expressions:[{id:'wink',aliases:[]}]})});
class TalkingHead {
  constructor(){
    head=this;this.opt={};
    this.camera={position:new Vector3(0,1,8),fov:45,matrixWorld:{elements:[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]},updateMatrixWorld(){}};
    this.controls={target:new Vector3(0,1,0),update(){}};
    this.audioCtx={audioWorklet:{addModule:async()=>{}},resume:async()=>{}};
    this.audioSpeechGainNode={connect(){},disconnect(){}};
    this.mtAvatar={};this.animQueue=[];this.moodName='neutral';this.viewName='upper';
  }
  async showAvatar(){}
  setMood(name){this.moodName=name;}
  playGesture(name,seconds){
    assert.equal(seconds,5);
    this.animQueue.push({gesture:true,name});
    if(name!=='wink')this.gestureTimeout=setTimeout(()=>this.stopGesture(1000),seconds*1000);
  }
  stopGesture(ms){clearTimeout(this.gestureTimeout);this.lastStopMilliseconds=ms;this.animQueue=this.animQueue.filter(item=>!item.gesture);}
  stopSpeaking(){}
}
class HeadAudio {async loadModel(){} update(){}}
const source=readFileSync(new URL('../app/avatar.js',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'').replace('export async function','async function');
const createAvatar=new Function('TalkingHead','HeadAudio','listInputs','openInput',source+'\nreturn createAvatar;')(TalkingHead,HeadAudio,listInputs,openInput);
const avatar=await createAvatar({});
const nil={speech_text:null,emotion:null,expression:null,gesture:null,whiteboard:null};
await avatar.receive(nil);assert.equal(avatar.getState().mood,'neutral');
await avatar.receive({emotion:'HAPPY',expression:'wink',gesture:'handup',whiteboard:{type:'image',image_url:'/media/first.png'}});
assert.equal(avatar.getState().gesture,'handup');
const first=picture;
advance(1000);
await avatar.receive({gesture:'index'});
assert.equal(avatar.getState().expression,'wink');
assert.equal(head.animQueue.filter(item=>item.vhExpression).length,1);
await avatar.receive(nil);
assert.equal(picture,first);
assert.equal(avatar.getState().mood,'happy');
assert.equal(avatar.getState().gesture,'index');
await assert.rejects(avatar.receive({whiteboard:{type:'image',image_url:'bad'}}));
assert.equal(picture,first);
await avatar.receive({whiteboard:{type:'clear'}});assert.equal(picture,null);
advance(3999);
assert.equal(avatar.getState().expression,'wink');
assert.equal(avatar.getState().gesture,'index');
advance(1);assert.equal(avatar.getState().expression,null);
assert.equal(avatar.getState().gesture,'index');
advance(999);assert.equal(avatar.getState().gesture,'index');
advance(1);assert.equal(avatar.getState().gesture,null);
assert.equal(head.lastStopMilliseconds,150,'Our deadline cancels the slower library release');
assert.equal(avatar.getState().mood,'happy');
await avatar.receive({expression:'wink',gesture:'ok'});
avatar.stopMotion('body');assert.equal(avatar.getState().gesture,null);
assert.equal(avatar.getState().expression,'wink');
const initial=head.camera.position.distanceTo(head.controls.target);
avatar.zoom(1);assert.ok(head.camera.position.distanceTo(head.controls.target)<initial);
avatar.zoom(-1);assert.ok(Math.abs(head.camera.position.distanceTo(head.controls.target)-initial)<1e-10);
for(let i=0;i<100;i++)avatar.zoom(1);
assert.ok(head.camera.position.distanceTo(head.controls.target)>=2-1e-10);
for(let i=0;i<100;i++)avatar.zoom(-1);
assert.ok(head.camera.position.distanceTo(head.controls.target)<=28+1e-10);
const before=head.controls.target.clone(),distance=head.camera.position.distanceTo(head.controls.target);
avatar.pan(1,1);assert.ok(head.controls.target.x<before.x&&head.controls.target.y<before.y);
assert.ok(Math.abs(head.camera.position.distanceTo(head.controls.target)-distance)<1e-10);
console.log('PASS null keeps state, emotion persists, expressions/gestures expire after 5s, replacement cancels old timers, board and camera');
