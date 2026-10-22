/** The conversation is a fixed sidebar; old floating layouts are ignored. */
export function setupChatWindow() {
  const paint=()=>{
    const width=Math.min(380,innerWidth*.42);
    document.documentElement.style.setProperty('--chat-width',width+'px');
    document.documentElement.style.setProperty('--scene-left',(width+24)+'px');
  };
  addEventListener('resize',paint);paint();
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
    const left=document.querySelector('#avatar').getBoundingClientRect().left+margin;
    const available=Math.max(1,innerWidth-left-margin);
    layout.width=clamp(layout.width,Math.min(180,available),Math.min(available,(innerHeight-100-margin)*16/9));
    const height=layout.width*9/16;
    layout.x=clamp(layout.x,left,innerWidth-layout.width-margin);layout.y=clamp(layout.y,100,Math.max(100,innerHeight-height-margin));
    for(const el of [screen,tools])Object.assign(el.style,{left:layout.x+'px',top:layout.y+'px',width:layout.width+'px',height:height+'px'});
  }
  function pointer(id,resize=false){
    const handle=document.querySelector(id);let active=null;
    handle.addEventListener('pointerdown',event=>{
      if(event.button!==0 || (!resize && event.target.closest('#screenResize')))return;event.stopPropagation();active={id:event.pointerId,x:event.clientX,y:event.clientY,start:{...layout}};handle.setPointerCapture(event.pointerId);event.preventDefault();
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
      event.preventDefault();event.stopPropagation();paint();save();
    });
  }
  pointer('#screenTools');pointer('#screenResize',true);
  document.querySelector('#resetScreen').addEventListener('click',()=>{layout=defaults();paint();save();});
  document.querySelector('#screenEnabled').addEventListener('change',()=>{tools.hidden=!document.querySelector('#screenEnabled').checked;});
  tools.hidden=localStorage.getItem('virtual-human-v2-screen')==='false';
  addEventListener('resize',()=>{paint();save();});paint();
}
