import assert from 'node:assert/strict';
import {listInputs,openInput} from '../app/assets/microphone.js';

let active=false, stopped=0, constraints;
const stream={getTracks:()=>[{stop(){active=false;stopped++;}}]};
const media={
  async getUserMedia(value){constraints=value;active=true;return stream;},
  async enumerateDevices(){
    assert.equal(active,true,'Enumerate while permission stream is active');
    return [
      {kind:'audioinput',deviceId:'default',label:'Default - USB microphone'},
      {kind:'audioinput',deviceId:'communications',label:'Communications - USB microphone'},
      {kind:'audioinput',deviceId:'usb',label:'USB microphone'},
      {kind:'audioinput',deviceId:'usb',label:'USB microphone'},
      {kind:'audioinput',deviceId:'headset',label:'Headset microphone'},
      {kind:'audiooutput',deviceId:'speaker',label:'Speaker'},
    ];
  },
};
Object.defineProperty(globalThis,'navigator',{value:{mediaDevices:media},configurable:true});
const devices=await listInputs(true);
assert.deepEqual(devices.map(device=>device.deviceId),['default','usb','headset']);
assert.ok(devices.every(device=>device.labelKnown));
assert.equal(active,false);assert.equal(stopped,1);
await openInput('headset');
assert.deepEqual(constraints.audio.deviceId,{exact:'headset'});
await openInput('');assert.equal(constraints.audio.deviceId,undefined);
media.enumerateDevices=async()=>{throw new Error('Enumeration failed');};
await assert.rejects(listInputs(true),/Enumeration failed/);
assert.equal(active,false);assert.equal(stopped,2);
media.getUserMedia=async()=>{throw Object.assign(new Error('Denied'),{name:'NotAllowedError'});};
await assert.rejects(openInput('usb'),/Microphone access denied/);
let attempts=0;
media.getUserMedia=async()=>{attempts++;throw Object.assign(new Error('Gone'),{name:'OverconstrainedError'});};
await assert.rejects(openInput('missing'),/selected microphone is unavailable/);
assert.equal(attempts,1,'Never silently open another microphone');
console.log('PASS permission-aware enumeration, device deduplication, exact input selection, cleanup and actionable errors');
