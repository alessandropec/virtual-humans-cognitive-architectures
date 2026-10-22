// Compose one JSON payload and send exactly that payload through the HTTP API.
export function composeReply(values) {
  const body = {
    speech_text: values.speech.trim() || null,
    emotion: values.emotion || null,
    expression: values.expression || null,
    gesture: values.gesture || null,
    whiteboard: null,
  };
  if(values.board==='clear')body.whiteboard={type:'clear'};
  if(values.board==='image' && values.imageUrl)body.whiteboard={type:'image',image_url:values.imageUrl};
  return body;
}

export async function setupAPIPlayground({request,setBusy}) {
  const $=selector=>document.querySelector(selector);
  let catalog=await request('/api/catalog',undefined,'GET'), imageUrl='', available=false, firstConnection=true;
  const fill=(selector,items,empty)=>{
    $(selector).replaceChildren(...(empty?[new Option(empty,'')]:[]),...items.map(item=>new Option(item.name||item.id||item,item.id||item)));
  };
  function gestureOptions(selected='') {
    fill('#apiGesture',catalog.gestures,'Keep current gesture (null)');
    $('#apiGesture').value=selected;
  }
  function feedback(text,error=false){$('#apiFeedback').textContent=text;$('#apiFeedback').classList.toggle('error',error);}
  function payload(){return composeReply({speech:$('#apiSpeech').value,emotion:$('#apiEmotion').value,expression:$('#apiExpression').value,gesture:$('#apiGesture').value,board:$('#apiBoard').value,imageUrl});}
  function update() {
    $('#apiImageUpload').hidden=$('#apiBoard').value!=='image';
    const body=payload();
    $('#apiJson').textContent=JSON.stringify(body,null,2);
    $('#apiRun').disabled=!available||($('#apiBoard').value==='image'&&!imageUrl);
  }
  function showCatalog() {
    const container=$('#apiCatalog');container.replaceChildren();
    for(const [name,items] of [['Emotions',catalog.moods],['Expressions',catalog.expressions],['Gestures',catalog.gestures]]){
      const heading=document.createElement('h3');heading.textContent=name;
      const table=document.createElement('table');
      for(const item of items){const row=table.insertRow();row.insertCell().textContent=item.id||item;row.insertCell().textContent=item.name||item;}
      container.append(heading,table);
    }
  }
  fill('#apiEmotion',catalog.moods.map(id=>({id:id.toUpperCase(),name:id})), 'Keep current emotion (null)');
  fill('#apiExpression',catalog.expressions.map(item=>({...item,name:`${item.name} (${item.id})`})), 'Keep current expression (null)');
  gestureOptions();showCatalog();update();
  $('#apiForm').addEventListener('input',update);
  $('#apiForm').addEventListener('change',update);
  $('#apiForm').addEventListener('submit',async event=>{
    event.preventDefault();
    if($('#apiRun').disabled||!$('#apiForm').reportValidity())return;
    const body=payload();setBusy(true);feedback('Running POST /api/speak…');
    try {const result=await request('/api/speak',body);$('#apiResult').hidden=false;$('#apiResult').textContent=JSON.stringify(result,null,2);feedback('Applied. Speech and animations may still be playing.');}
    catch(error){$('#apiResult').hidden=false;$('#apiResult').textContent=JSON.stringify({detail:error.detail||error.message},null,2);feedback(error.message,true);}
    finally{setBusy(false);}
  });
  $('#apiCopy').addEventListener('click',async()=>{
    try {await navigator.clipboard.writeText($('#apiJson').textContent);feedback('JSON copied.');}
    catch {feedback('Select the JSON above and copy it with Ctrl+C or Command+C.',true);}
  });
  $('#apiReset').addEventListener('click',()=>{$('#apiForm').reset();imageUrl='';$('#apiImageUrl').textContent='Choose an image to upload.';$('#apiResult').hidden=true;gestureOptions();update();feedback('Form reset. The avatar and whiteboard have not changed.');});
  async function upload(input,path,apply){
    const file=input.files[0];if(!file)return;
    setBusy(true);feedback('Uploading '+file.name+'…');
    try{const data=new FormData();data.append('file',file);const result=await request(path,data);await apply(result);feedback('Uploaded. Run the request to apply it.');}
    catch(error){feedback(error.message,true);}
    finally{input.value='';setBusy(false);update();}
  }
  $('#apiImageFile').addEventListener('change',event=>upload(event.target,'/api/whiteboard/images',result=>{imageUrl=result.image_url;$('#apiImageUrl').textContent=imageUrl;}));
  return {setAvailable(value){available=value;$('#apiFields').disabled=!value;if(value&&firstConnection){feedback('Ready. Choose fields to compose a request.');firstConnection=false;}update();}};
}
