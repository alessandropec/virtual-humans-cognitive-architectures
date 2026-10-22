import assert from 'node:assert/strict';
import {setupChatWindow,setupStudioScreen} from '../app/chat-window.js';
class Element extends EventTarget {
  style={}; hidden=false; checked=true; captured=null;
  getBoundingClientRect(){return {left:parseFloat(root.style['--scene-left'])};}
  closest(){return null;}
  setPointerCapture(id){this.captured=id;}
  hasPointerCapture(id){return this.captured===id;}
  releasePointerCapture(){this.captured=null;}
}
const root=new Element(), selectors=new Map();
for(const id of ['avatar','studioScreen','screenTools','screenResize','screenDrag','resetScreen','screenEnabled'])selectors.set('#'+id,new Element());
globalThis.document={documentElement:root,querySelector:id=>selectors.get(id)};
root.style.setProperty=(key,value)=>root.style[key]=value;
globalThis.innerWidth=1200;globalThis.innerHeight=800;
const resizeListeners=[];
globalThis.addEventListener=(name,listener)=>{if(name==='resize')resizeListeners.push(listener);};
const saved=new Map([['virtual-human-v2-screen-layout',JSON.stringify({x:5,y:10,width:700})]]);
globalThis.localStorage={getItem:key=>saved.get(key),setItem:(key,value)=>saved.set(key,value)};
setupChatWindow();setupStudioScreen();
const board=selectors.get('#studioScreen'),surface=selectors.get('#screenTools');
const number=(el,key)=>parseFloat(el.style[key]);
assert.equal(root.style['--chat-width'],'380px');
assert.ok(number(board,'left')>=416,'Saved whiteboard layout is kept outside the conversation');
const fire=(element,type,values={})=>{const event=new Event(type);Object.assign(event,{button:0,pointerId:1,clientX:700,clientY:300,...values});element.dispatchEvent(event);};
const initialLeft=number(board,'left'),initialTop=number(board,'top');
fire(surface,'pointerdown');fire(surface,'pointermove',{clientX:730,clientY:340});fire(surface,'pointerup');
assert.equal(number(board,'left'),initialLeft+30,'Dragging board content moves the board');
assert.equal(number(board,'top'),initialTop+40);
fire(surface,'pointerdown');fire(surface,'pointermove',{clientX:-2000,clientY:-2000});fire(surface,'pointerup');
assert.ok(number(board,'left')>=416,'Dragging cannot cover the chat');
assert.ok(number(board,'top')>=100,'Dragging cannot cover the header');
globalThis.innerWidth=700;globalThis.innerHeight=500;
for(const listener of resizeListeners)listener();
assert.ok(number(board,'left')>=parseFloat(root.style['--scene-left']));
assert.ok(number(board,'left')+number(board,'width')<=688,'Board remains in the viewport after resize');
assert.ok(number(board,'top')+number(board,'height')<=488);
console.log('PASS fixed sidebar, restored bounds, board content dragging, chat exclusion and viewport resizing');
