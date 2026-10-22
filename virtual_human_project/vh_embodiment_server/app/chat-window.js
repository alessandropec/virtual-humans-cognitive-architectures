/** Movable/resizable chat, with viewport bounds and local layout persistence. */
export function setupChatWindow() {
  const panel=document.querySelector('#conversation');
  const margin=12, key='virtual-human-v2-chat-layout';
  const defaults=()=>{
    const width=Math.min(420,innerWidth-margin*2),height=Math.max(210,innerHeight-92);
    return {mode:'left',x:margin,y:80,width,height};
  };
  let layout=defaults(), previous=null;
  try {
    const saved=JSON.parse(localStorage.getItem(key));
    if(saved && ['x','y','width','height'].every(field=>Number.isFinite(saved[field])) && ['bottom','floating','left','expanded'].includes(saved.mode)) layout=saved.mode==='bottom'?defaults():saved;
  } catch {}
  const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
  function paint() {
    const maxWidth=Math.max(1,innerWidth-margin*2),maxHeight=Math.max(1,innerHeight-margin*2);
    layout.width=clamp(layout.width,Math.min(320,maxWidth),maxWidth);
    layout.height=clamp(layout.height,Math.min(210,maxHeight),maxHeight);
    if(layout.mode==='left') {layout.x=margin;layout.y=Math.min(80,Math.max(margin,innerHeight-210-margin));layout.height=innerHeight-layout.y-margin;}
    if(layout.mode==='bottom') {layout.x=(innerWidth-layout.width)/2;layout.y=innerHeight-layout.height-24;}
    if(layout.mode==='expanded') {layout.width=Math.min(1000,maxWidth);layout.height=Math.min(maxHeight,Math.max(210,innerHeight-104));layout.x=(innerWidth-layout.width)/2;layout.y=80;}
    layout.x=clamp(layout.x,margin,Math.max(margin,innerWidth-layout.width-margin));
    layout.y=clamp(layout.y,margin,Math.max(margin,innerHeight-layout.height-margin));
    Object.assign(panel.style,{left:`${layout.x}px`,top:`${layout.y}px`,width:`${layout.width}px`,height:`${layout.height}px`});
    document.querySelector('#dockChat').setAttribute('aria-pressed',String(layout.mode==='left'));
    document.querySelector('#expandChat').setAttribute('aria-pressed',String(layout.mode==='expanded'));
    panel.dataset.mode=layout.mode;
  }
  function save() {try{localStorage.setItem(key,JSON.stringify(layout));}catch{}}
  function dock() {layout={...layout,mode:'left',width:Math.min(420,innerWidth-margin*2),height:innerHeight-92,y:80};paint();save();}
  document.querySelector('#dockChat').addEventListener('click',dock);
  document.querySelector('#resetChat').addEventListener('click',()=>{layout=defaults();previous=null;paint();save();});
  document.querySelector('#expandChat').addEventListener('click',()=>{
    if(layout.mode==='expanded') {layout=previous||defaults();previous=null;}
    else {previous={...layout};layout.mode='expanded';}
    paint();save();
  });
  function pointer(element,resize=false) {
    let active=null;
    element.addEventListener('pointerdown',event=>{
      if(event.button!==0)return;
      active={id:event.pointerId,x:event.clientX,y:event.clientY,start:{...layout},moved:false};
      element.setPointerCapture(event.pointerId);event.preventDefault();
    });
    element.addEventListener('pointermove',event=>{
      if(!active || event.pointerId!==active.id)return;
      const dx=event.clientX-active.x,dy=event.clientY-active.y;
      if(Math.abs(dx)+Math.abs(dy)<3&&!active.moved)return;
      active.moved=true;
      if(resize) {
        layout.mode=active.start.mode==='left'?'left':'floating';
        layout.width=active.start.width+dx;layout.height=active.start.height+dy;
        layout.width=Math.min(layout.width,innerWidth-layout.x-margin);
        layout.height=Math.min(layout.height,innerHeight-layout.y-margin);
      } else {layout.mode='floating';layout.x=active.start.x+dx;layout.y=active.start.y+dy;}
      paint();panel.classList.toggle('dock-hint',!resize&&layout.x<32);
    });
    const finish=event=>{
      if(!active||event.pointerId!==active.id)return;
      const moved=active.moved;active=null;panel.classList.remove('dock-hint');
      if(element.hasPointerCapture(event.pointerId))element.releasePointerCapture(event.pointerId);
      if(moved&&!resize&&layout.x<32)dock();else save();
    };
    element.addEventListener('pointerup',finish);element.addEventListener('pointercancel',finish);
    element.addEventListener('keydown',event=>{
      if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key))return;
      const step=event.shiftKey?40:10;
      const dx=event.key==='ArrowLeft'?-step:event.key==='ArrowRight'?step:0;
      const dy=event.key==='ArrowUp'?-step:event.key==='ArrowDown'?step:0;
      layout.mode='floating';
      if(resize){layout.width+=dx;layout.height+=dy;}else{layout.x+=dx;layout.y+=dy;}
      event.preventDefault();paint();save();
    });
  }
  pointer(document.querySelector('#chatDrag'));
  pointer(document.querySelector('#resizeChat'),true);
  addEventListener('resize',()=>{paint();save();});
  paint();
}


/** Board and handles share a layer behind the pointer-transparent avatar canvas. */
export function setupStudioScreen() {
  const screen=document.querySelector('#studioScreen'),tools=document.querySelector('#screenTools');
  const key='virtual-human-v2-screen-layout',margin=12;
  const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
  const defaults=()=>({x:Math.max(margin,innerWidth*.43),y:Math.max(105,innerHeight*.16),width:Math.min(620,innerWidth*.53)});
  let layout=defaults();
  try {const saved=JSON.parse(localStorage.getItem(key));if(saved&&['x','y','width'].every(k=>Number.isFinite(saved[k])))layout=saved;}catch{}
  const save=()=>{try{localStorage.setItem(key,JSON.stringify(layout));}catch{}};
  function paint(){
    layout.width=clamp(layout.width,Math.min(180,innerWidth-margin*2),Math.min(innerWidth-margin*2,(innerHeight-margin*2)*16/9));
    const height=layout.width*9/16;
    layout.x=clamp(layout.x,margin,innerWidth-layout.width-margin);layout.y=clamp(layout.y,margin,innerHeight-height-margin);
    for(const el of [screen,tools])Object.assign(el.style,{left:layout.x+'px',top:layout.y+'px',width:layout.width+'px',height:height+'px'});
  }
  function pointer(id,resize=false){
    const handle=document.querySelector(id);let active=null;
    handle.addEventListener('pointerdown',event=>{
      if(event.button!==0)return;active={id:event.pointerId,x:event.clientX,y:event.clientY,start:{...layout}};handle.setPointerCapture(event.pointerId);event.preventDefault();
    });
    handle.addEventListener('pointermove',event=>{
      if(!active||active.id!==event.pointerId)return;
      if(resize)layout.width=active.start.width+Math.max(event.clientX-active.x,(event.clientY-active.y)*16/9);
      else {layout.x=active.start.x+event.clientX-active.x;layout.y=active.start.y+event.clientY-active.y;}
      paint();
    });
    const finish=event=>{if(!active||active.id!==event.pointerId)return;active=null;if(handle.hasPointerCapture(event.pointerId))handle.releasePointerCapture(event.pointerId);save();};
    handle.addEventListener('pointerup',finish);handle.addEventListener('pointercancel',finish);
    handle.addEventListener('keydown',event=>{
      if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key))return;
      const step=event.shiftKey?40:10,dx=event.key==='ArrowLeft'?-step:event.key==='ArrowRight'?step:0,dy=event.key==='ArrowUp'?-step:event.key==='ArrowDown'?step:0;
      if(resize)layout.width+=dx||dy;else {layout.x+=dx;layout.y+=dy;}
      event.preventDefault();paint();save();
    });
  }
  pointer('#screenDrag');pointer('#screenResize',true);
  document.querySelector('#resetScreen').addEventListener('click',()=>{layout=defaults();paint();save();});
  document.querySelector('#screenEnabled').addEventListener('change',()=>{tools.hidden=!document.querySelector('#screenEnabled').checked;});
  tools.hidden=localStorage.getItem('virtual-human-v2-screen')==='false';
  addEventListener('resize',()=>{paint();save();});paint();
}
