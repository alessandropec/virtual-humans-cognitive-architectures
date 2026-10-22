import { setupControlPanels } from './assets/control-panels.js';
import { setupAPIPlayground } from './assets/api-playground.js';
import { createAvatar } from './avatar.js';
import { setupChatWindow, setupStudioScreen } from './chat-window.js';
const $ = selector => document.querySelector(selector);
let playground;
let avatar, busy = false, config = {}, apiConnected = false;
let testingMicrophone = false;
let activeMicrophoneLabel = '';
let agentStatus = null;
let agentAction = false;
let warmingModels = false;
let blockingLoads = 0;
let withoutSpeechModels = false;
let needsSpeechChoice = false;
let warmupPromise = null;
let selectedMicrophone = localStorage.getItem('virtual-human-v2-microphone') || '';
if(selectedMicrophone==='default')selectedMicrophone='';
const recordingURLs = new Set();
const status = $('#status');
let pendingLine=null,pendingLabel=null;
let activeVoice=null;
let liveRecording=null;
let preparingMicrophone=false;
let shuttingDown=false;
let savingTranscription=false;
setupChatWindow();
setupStudioScreen();
setupControlPanels();
const finishStartup = blockLoading('Loading avatar and speech models...');
const report = error => { console.error(error); status.textContent = error.message || String(error);  };
const safe = callback => async (...args) => { try { await callback(...args); } catch (error) { report(error); } };

function blockLoading(text) {
  const dialog=$('#modelLoading');
  blockingLoads++;
  $('#modelLoadingText').textContent=text;
  if(!dialog.open)dialog.showModal();
  let released=false;
  return ()=>{
    if(released)return;
    released=true;blockingLoads--;
    if(blockingLoads===0 && dialog.open)dialog.close();
  };
}
$('#modelLoading').addEventListener('cancel',event=>event.preventDefault());
let logPanel='embodiment', logTimer=null;
async function refreshLogs(){
  if(!$('#serverLogs').open)return;
  try {
    const data=await request('/api/logs',undefined,'GET',5000);
    const view=$('#logOutput');const bottom=view.scrollHeight-view.scrollTop-view.clientHeight<40;
    view.textContent=data[logPanel];if(bottom)view.scrollTop=view.scrollHeight;
  } catch(error){$('#logOutput').textContent=error.message;}
}
$('#openLogs').addEventListener('click',()=>{$('#serverLogs').showModal();refreshLogs();logTimer=setInterval(refreshLogs,1000);});
$('#closeLogs').addEventListener('click',()=>$('#serverLogs').close());
$('#serverLogs').addEventListener('close',()=>clearInterval(logTimer));
for(const [id,panel,title] of [['logEmbodiment','embodiment','Embodiment Server'],['logCognitive','cognitive','Cognitive Architecture Server']]){
  $('#'+id).addEventListener('click',()=>{logPanel=panel;$('#logTitle').textContent=title;refreshLogs();});
}


function loading(selector, active, text) {
  const element=$(selector);
  element.classList.toggle('is-loading',active);
  element.setAttribute('aria-busy',String(active));
  if(text!==undefined)element.textContent=text;
}

function refreshControls() {
  const recording = avatar?.getState().recording || preparingMicrophone;
  $('#character').disabled = !avatar || (busy || warmingModels) || recording;
  playground?.setAvailable(Boolean(avatar && apiConnected && !busy && !warmingModels && !needsSpeechChoice && !recording));
  $('#send').disabled = needsSpeechChoice || !avatar || (busy || warmingModels) || recording;
  $('#mic').disabled = withoutSpeechModels || needsSpeechChoice || !avatar || (busy || warmingModels) || preparingMicrophone || savingTranscription;
  $('#text').disabled = needsSpeechChoice || !avatar || (busy || warmingModels) || recording;
  $('#clearConversation').disabled = !avatar || (busy || warmingModels) || recording;
  $('#liveTranscription').disabled = !avatar || (busy || warmingModels) || recording || savingTranscription;
  $('#ttsDevice').disabled = !avatar || (busy || warmingModels) || recording || savingTranscription;
  $('#testTtsDevice').disabled = withoutSpeechModels || needsSpeechChoice || !avatar || (busy || warmingModels) || recording || savingTranscription;
  $('#sttDevice').disabled = !avatar || (busy || warmingModels) || recording || savingTranscription;
  $('#sttModel').disabled = !avatar || (busy || warmingModels) || recording || savingTranscription;
  for (const id of ['microphone','refreshMicrophones','testMicrophone']) $( '#' + id).disabled = !avatar || (busy || warmingModels) || recording;

}
function setBusy(value) { busy = value; $('#conversation').setAttribute('aria-busy',String(value)); refreshControls(); }
function connectionLabel() {
  $('#connection').textContent = !apiConnected ? 'Avatar API disconnected' : config.agent_enabled === false ? 'Agent connection disabled' : agentStatus?.connected ? 'Cognitive Architecture Server connected' : 'Configure the Cognitive Architecture Server in Settings to connect.';
}
async function warmModels() {
  if(warmupPromise)return warmupPromise;
  const cached=await request('/api/models/warmup',undefined,'GET',5000);
  if(cached.state==='ready'){
    withoutSpeechModels=false;needsSpeechChoice=false;$('#speechModelsNotice').hidden=true;refreshControls();return;
  }
  const finishLoading=blockLoading('Warming up speech models...');
  warmingModels=true;refreshControls();
  loading('#status',true,'Warming up speech models...');
  loading('#settingsMessage',true,'Warming up speech models...');
  warmupPromise=(async()=>{
    await Promise.resolve();
    try {
      const deadline=Date.now()+180000;
      let result=cached;
      do {
        if(result.state!=='loading')break;
        $('#modelLoadingText').textContent=result.message;
        $('#status').textContent=result.message;
        $('#settingsMessage').textContent=result.message;
        if(Date.now()>deadline)throw new Error('Model warmup is taking too long. Check the server log and Settings.');
        await new Promise(resolve=>setTimeout(resolve,300));
        result=await request('/api/models/warmup',undefined,'GET',5000);
      } while(true);
      needsSpeechChoice=Boolean(result.missing);
      $('#speechModelsNotice').hidden=!needsSpeechChoice;
      if(needsSpeechChoice)$('#speechModelsMessage').textContent=result.message;
      if(result.state==='skipped'){
        withoutSpeechModels=true;$('#status').textContent=result.message;$('#settingsMessage').textContent=result.message;return;
      }
      if(result.state==='error')throw new Error(Object.entries(result.errors).map(([name,error])=>name+': '+error).join(' | '));
      withoutSpeechModels=false;
      $('#status').textContent='Ready';$('#settingsMessage').textContent='Speech models ready';
    } catch(error) {
      $('#status').textContent=error.message;
      $('#settingsMessage').textContent=error.message;
    } finally {
      finishLoading();
      warmingModels=false;warmupPromise=null;
      loading('#status',false);loading('#settingsMessage',false);refreshControls();
    }
  })();
  return warmupPromise;
}

$('#skipSpeechModels').addEventListener('click',safe(async()=>{
  const result=await request('/api/models/skip',{});
  withoutSpeechModels=true;needsSpeechChoice=false;
  $('#speechModelsNotice').hidden=true;$('#status').textContent=result.message;
  refreshControls();
}));
$('#selectSpeechModels').addEventListener('click',safe(async()=>{
  const selected=await request('/api/paths/select?kind=models',{});
  if(!selected.path)return;
  const unchanged=selected.path===config.models_dir;
  config=await request('/api/settings',{...config,models_dir:selected.path},'PUT');
  if(unchanged)await request('/api/models/retry',{});
  $('#modelsDir').value=config.models_dir;
  await refreshInstalledModels();await warmModels();
}));

function showModelHint() {
  const hints={
    tiny:'Tiny: smallest and fastest; more errors, especially with noise or difficult words.',
    base:'Base: fast, usually more accurate than Tiny.',
    small:'Small: balanced speed and accuracy. Default model.',
    medium:'Medium: usually fewer errors than Small; slower updates and more memory.',
    'large-v3':'Large v3: aims for the highest accuracy; slow and memory-intensive on CPU.',
  };
  $('#sttModelHint').textContent=hints[$('#sttModel').value] || 'No model available. Run the installer again.';
}
async function refreshInstalledModels() {
  const result=await request('/api/models',undefined,'GET');
  const model=$('#sttModel');
  model.replaceChildren(...result.installed.map(name=>new Option(name==='small'?'Small — balanced speed and accuracy':'Tiny — use this with limited computer resources',name)));
  if(!result.installed.includes(config.stt_model))model.append(new Option('Model unavailable — run the installer again',config.stt_model));
  model.value=config.stt_model;showModelHint();
}
function message(role, text) {
  const item = document.createElement('div'); item.className = `message ${role}`;
  const label = document.createElement('strong'); label.textContent = role === 'user' ? 'You' : 'Avatar';
  const content = document.createElement('p'); content.textContent = text;
  item.append(label, content); $('#messages').append(item); $('#messages').scrollTop = $('#messages').scrollHeight;
  return content;
}
function clearPending() {pendingLine?.remove();pendingLine=null;pendingLabel=null;}
function showPending(text) {
  if(!pendingLine) {
    const content=message('avatar',''); pendingLine=content.parentElement;pendingLine.classList.add('pending');
    content.classList.add('pending-content');
    const spinner=document.createElement('span');spinner.className='spinner';spinner.setAttribute('aria-hidden','true');
    pendingLabel=document.createElement('span');content.append(spinner,pendingLabel);
  }
  pendingLabel.textContent=text; status.textContent=text;$('#messages').scrollTop=$('#messages').scrollHeight;
}
function applySpeechMode() {
  const enabled=config.speech_enabled!==false;
  $('#speechEnabled').checked=enabled; avatar?.setSpeechEnabled(enabled);
  refreshControls();
}
async function request(url, body, method = 'POST', timeout = 0) {
  const options=body === undefined ? {method} : body instanceof FormData
    ? {method, body} : {method, headers:{'Content-Type':'application/json','X-Virtual-Human':'agent'}, body:JSON.stringify(body)};
  if(timeout)options.signal=AbortSignal.timeout(timeout);
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    const detail = data.detail;
    const error = new Error(typeof detail === 'string' ? detail : detail?.message || (Array.isArray(detail) ? detail.map(item=>item.msg).join('; ') : `Invalid request (${response.status})`));
    error.detail = detail; throw error;
  }
  return data;
}

function stopMicrophoneTest() {
  avatar?.stopMicrophoneTest(); testingMicrophone = false; $('#testMicrophone').textContent = 'Test level';
}
let microphoneRefresh = null;
async function refreshMicrophones(permission = false) {
  if(microphoneRefresh)await microphoneRefresh;
  microphoneRefresh=(async()=>{
    if(permission)stopMicrophoneTest();
    const devices = await avatar.listMicrophones(permission);
    const system = devices.find(device=>device.deviceId==='default');
    $('#microphone').replaceChildren(new Option(system?.labelKnown?'System default: '+system.label:'System default',''));
    for(const device of devices) if(device.deviceId && device.deviceId!=='default') $('#microphone').append(new Option(device.label,device.deviceId));
    const confirmed=permission || devices.some(device=>device.labelKnown);
    if(selectedMicrophone && !devices.some(device=>device.deviceId===selectedMicrophone)) {
      if(confirmed) {
        stopMicrophoneTest();selectedMicrophone='';localStorage.removeItem('virtual-human-v2-microphone');
        $('#microphoneStatus').textContent='The saved microphone is unavailable. System default selected; choose a device and Test level.';
      } else $('#microphone').append(new Option('Saved device (allow access to check)',selectedMicrophone));
    } else $('#microphoneStatus').textContent=confirmed?`${devices.filter(device=>device.deviceId!=='default').length || (system?1:0)} input devices found. Press Test level and speak.`:'Allow microphone access to see device names. Click Refresh devices.';
    $('#microphone').value=selectedMicrophone;
  })();
  try {await microphoneRefresh;} finally {microphoneRefresh=null;}
}
function addRecording(line, audio) {
  const details=document.createElement('details'), summary=document.createElement('summary'), player=document.createElement('audio');
  summary.textContent='Replay recording'; player.controls=true;
  const url=URL.createObjectURL(audio); recordingURLs.add(url); player.src=url;
  player.addEventListener('play',()=>avatar.stop());
  details.append(summary,player); line.parentElement.append(details);
}
async function transcribeLive(recording,audio) {
  const data=new FormData();data.append('audio',audio,'preview');
  const result=await request('/api/transcribe',data);
  showSpeechDevice(result.diagnostics);
  recording.result=result;recording.lastAudioSize=audio.size;
  if(recording===liveRecording && recording.active && result.text) {
    recording.line.textContent=result.text;
    $('#text').value=result.text;$('#text').scrollLeft=$('#text').scrollWidth;
    $('#messages').scrollTop=$('#messages').scrollHeight;
  }
  return result;
}
function showSpeechDevice(stats) {
  if(!stats?.device)return;
  const label=stats.device==='cuda'?'NVIDIA GPU':'CPU';
  $('#sttDeviceStatus').textContent=`Last used: ${label}${stats.processing_seconds!=null?' · '+stats.processing_seconds+' s':''}${stats.fallback_reason?' · CPU fallback: '+stats.fallback_reason:''}`;
}
async function refreshSpeechDevice() {
  $('#retrySpeechDevice').disabled=true;
  loading('#sttDeviceStatus',true,'Checking device…');
  try {
    const result=await request('/api/transcribe/device',undefined,'GET',15000);
    if(result.last_run?.device)showSpeechDevice(result.last_run);
    else $('#sttDeviceStatus').textContent=result.requested_device==='cpu'?'CPU selected. Applies to the next transcription.':result.cuda_detected?'NVIDIA GPU detected. It will be tested during the next transcription.':(result.detection_note||'No GPU detected.');
  } catch(error) {
    $('#sttDeviceStatus').textContent=error.name==='TimeoutError'?'The check timed out. Please try again.':'Check failed: '+error.message+'. Check that the server is running and try again.';
  } finally {
    loading('#sttDeviceStatus',false);$('#retrySpeechDevice').disabled=false;
  }
}
$('#retrySpeechDevice').addEventListener('click',refreshSpeechDevice);
// Device detection must not wait for the 3D model or audio initialization.
void refreshSpeechDevice();

function showVoiceDevice(result) {
  const stats=result.last_run||result.diagnostics;
  $('#ttsDeviceStatus').textContent=stats?.device
    ? `Last speech generation: ${stats.device==='cuda'?'NVIDIA GPU':'CPU'} · ${stats.processing_seconds} s${stats.fallback_reason?' · CPU fallback: '+stats.fallback_reason:''}`
    : result.requested_device==='cpu'?'CPU selected.':result.cuda_detected?'GPU detected. Use the speech test to check it.':result.detection_note||'GPU unavailable.';
}
async function refreshVoiceDevice() {
  loading('#ttsDeviceStatus',true,'Checking speech device…');
  try {showVoiceDevice(await request('/api/speech/device',undefined,'GET',15000));}
  catch(error) {$('#ttsDeviceStatus').textContent='Check failed: '+error.message;}
  finally {loading('#ttsDeviceStatus',false);}
}
void refreshVoiceDevice();
$('#ttsDevice').addEventListener('change',safe(async()=>{
  const finishUpdate=blockLoading('Preparing the selected speech device...');
  savingTranscription=true;refreshControls();$('#saveSettings').disabled=true;$('#speechEnabled').disabled=true;
  loading('#ttsDeviceStatus',true,'Saving speech device…');
  try {
    config=await request('/api/settings',{...config,tts_device:$('#ttsDevice').value},'PUT');
    await refreshVoiceDevice();await warmModels();
  } catch(error) {$('#ttsDevice').value=config.tts_device||'cpu';$('#ttsDeviceStatus').textContent=error.message;}
  finally {finishUpdate();loading('#ttsDeviceStatus',false);savingTranscription=false;refreshControls();$('#saveSettings').disabled=false;$('#speechEnabled').disabled=false;}
}));
$('#testTtsDevice').addEventListener('click',safe(async()=>{
  const finishLoading=blockLoading('Warming up the selected voice...');
  setBusy(true);loading('#ttsDeviceStatus',true,'Loading model and testing speech…');
  try {showVoiceDevice(await request('/api/speech/prepare',{}));}
  catch(error) {$('#ttsDeviceStatus').textContent=error.message;}
  finally {finishLoading();loading('#ttsDeviceStatus',false);setBusy(false);}
}));

function showDiagnostics(line, stats) {
  if(!stats) return;
  showSpeechDevice(stats);
  const note=document.createElement('p'); note.className='note';
  const parts=[];
  if(stats.duration_seconds!=null) parts.push(`Audio ${stats.duration_seconds}s`);
  if(stats.rms_dbfs!=null) parts.push(`level ${stats.rms_dbfs} dBFS`);
  if(stats.device)parts.push(stats.device==='cuda'?'NVIDIA GPU':'CPU');
  if(stats.processing_seconds!=null)parts.push('processing '+stats.processing_seconds+' s');
  if(stats.fallback_reason)parts.push('CPU fallback: '+stats.fallback_reason);
  if(stats.model)parts.push(`Whisper ${stats.model}`);
  if(stats.trimmed_start_seconds!=null) parts.push(`silence trimmed: ${stats.trimmed_start_seconds}s start / ${stats.trimmed_end_seconds}s end`);
  note.textContent=parts.join(' · '); line.parentElement.append(note);
}
window.addEventListener('pagehide',()=>{for(const url of recordingURLs) URL.revokeObjectURL(url);});
async function finishTurn(result) {
  if (result.reply) {await avatar.receive(result.reply);if(!result.reply.audio_url)status.textContent='Response received';}
  else {clearPending();status.textContent = 'Text received · configure the agent API in Settings';}
}
function connectAPI() {
  if(shuttingDown)return;
  const socket = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`);
  const sendState = () => { if (avatar && socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({state:avatar.getState()})); };
  socket.onopen = () => { apiConnected = true; connectionLabel(); refreshControls(); sendState(); };
  const timer = setInterval(sendState, 1000);
  socket.onmessage = async ({data}) => {
    const command = JSON.parse(data); let error;
    if(command.kind==='progress') {if(busy)showPending(command.data.text);return;}
    if(command.kind==='transcript') {
      if(activeVoice && command.data.request_id===activeVoice.id) {
        activeVoice.text=command.data.text;activeVoice.line.textContent=command.data.text;
        activeVoice.line.parentElement.classList.remove('draft');
        $('#messages').scrollTop=$('#messages').scrollHeight;
      }
      return;
    }
    try {
      if(!avatar)throw new Error("Avatar is loading. Try again when ready.");
      const args = command.data;
      switch(command.kind) {
        case 'receive': await avatar.receive(args); break;
        case 'gesture': await avatar.gesture(args.gesture); break;
        case 'expression': avatar.expression(args.expression); break;
        case 'character': await avatar.selectCharacter(args.character); config.character=args.character; $('#character').value=args.character; break;
        case 'motion-stop': avatar.stopMotion(args.track); break;
        case 'reset': avatar.reset(); break;
        case 'mood': avatar.setMood(args.mood); break;
        case 'view': avatar.setView(args.view); break;
        case 'stop': avatar.stop(); break;
        default: throw new Error('Unknown command');
      }
    } catch(exception) { error=exception.message; report(exception); }
    if (socket.readyState===WebSocket.OPEN) socket.send(JSON.stringify({id:command.id,state:avatar?.getState(),error}));
  };
  socket.onclose = event => {
    clearInterval(timer); apiConnected=false; connectionLabel(); refreshControls();
    if(shuttingDown) { $('#connection').textContent='Server stopped';return; }
    if(event.code===1008) $('#connection').textContent='Avatar API is in use by another tab';
    else setTimeout(connectAPI,3000);
  };
}

$('#settings').addEventListener('leave-microphone',stopMicrophoneTest);
$('#settings').addEventListener('close',stopMicrophoneTest);
$('#clearConversation').addEventListener('click',safe(()=>{
  if(busy || avatar?.getState().recording)return;
  avatar.stop();clearPending();$('#messages').replaceChildren();$('#text').value='';
  for(const url of recordingURLs)URL.revokeObjectURL(url);
  recordingURLs.clear();status.textContent='Conversation cleared';
  request('/api/conversation/clear',{}).catch(error=>console.warn('Remote reset failed:',error.message));
}));

let settingsSave = Promise.resolve();
function saveSettings(waitModels=true) {
  if(!config.language)return Promise.resolve();
  const next={character:config.character,agent_url:$('#agentUrl').value,agent_enabled:$('#agentEnabled').checked,agent_heartbeat_url:$('#agentHeartbeatUrl').value,agent_script:$('#agentScript').value.trim(),agent_python:$('#agentPython').value.trim(),agent_autostart:$('#agentAutostart').checked,language:$('#language').value,stt_language:$('#sttLanguage').value,models_dir:$('#modelsDir').value,vad_threshold:Number($('#vadThreshold').value),speech_enabled:$('#speechEnabled').checked,live_transcription:$('#liveTranscription').checked,stt_model:$('#sttModel').value,stt_device:$('#sttDevice').value,tts_device:$('#ttsDevice').value};
  settingsSave = settingsSave.catch(()=>{}).then(async()=>{
  if(Object.entries(next).every(([key,value])=>config[key]===value))return;
  const finishUpdate=waitModels?blockLoading('Applying settings and preparing speech models...'):()=>{};
  $('#saveSettings').disabled=true;
  loading('#settingsMessage',true,'Saving settings…');
  $('#speechEnabled').disabled=true;
  try {
    config=await request('/api/settings',next,'PUT');
    $('#settingsMessage').textContent='Settings saved'; await refreshInstalledModels();connectionLabel();applySpeechMode();if(waitModels)await warmModels();
  } catch(error) { $('#settingsMessage').textContent=error.message; throw error; }
  finally { finishUpdate();loading('#settingsMessage',false); $('#saveSettings').disabled=false;$('#speechEnabled').disabled=false; }
  });
  return settingsSave;
}
$('#saveSettings').addEventListener('click',safe(saveSettings));
for(const id of ['language','sttLanguage','modelsDir'])$('#'+id).addEventListener('change',safe(()=>saveSettings()));
$('#settings').addEventListener('close',safe(async()=>{
  try { await saveSettings(); }
  catch(error) { $('#settings').showModal();throw error; }
}));
async function saveTranscriptionSettings() {
  const modelChange=$('#sttModel').value!==config.stt_model || $('#sttDevice').value!==config.stt_device;
  const finishUpdate=modelChange?blockLoading('Preparing the selected transcription model...'):()=>{};
  savingTranscription=true;refreshControls();$('#saveSettings').disabled=true;$('#speechEnabled').disabled=true;
  showModelHint();loading('#settingsMessage',true,'Saving transcription settings…');
  try {
    config=await request('/api/settings',{...config,live_transcription:$('#liveTranscription').checked,stt_model:$('#sttModel').value,stt_device:$('#sttDevice').value,tts_device:$('#ttsDevice').value},'PUT');
    $('#settingsMessage').textContent='Transcription settings saved';await refreshSpeechDevice();if(modelChange)await warmModels();
  } catch(error) {
    $('#liveTranscription').checked=config.live_transcription!==false;
    $('#sttModel').value=config.stt_model||'small';$('#sttDevice').value=config.stt_device||'auto';showModelHint();$('#settingsMessage').textContent=error.message;
  } finally {finishUpdate();loading('#settingsMessage',false);savingTranscription=false;refreshControls();$('#saveSettings').disabled=false;$('#speechEnabled').disabled=false;}
}
$('#liveTranscription').addEventListener('change',saveTranscriptionSettings);
$('#sttModel').addEventListener('change',saveTranscriptionSettings);
$('#sttDevice').addEventListener('change',saveTranscriptionSettings);
$('#speechEnabled').addEventListener('change',safe(async(event)=>{
  const finishUpdate=blockLoading('Preparing speech settings...');
  const previous=config.speech_enabled!==false,enabled=event.target.checked;
  $('#speechEnabled').disabled=true;avatar?.setSpeechEnabled(enabled);
  $('#saveSettings').disabled=true;
  try {
    config=await request('/api/settings',{...config,speech_enabled:enabled},'PUT');
    applySpeechMode();$('#settingsMessage').textContent=enabled?'Speech enabled':'Speech disabled';await warmModels();
  } catch(error) {avatar?.setSpeechEnabled(previous);$('#speechEnabled').checked=previous;throw error;}
  finally {finishUpdate();$('#speechEnabled').disabled=false;$('#saveSettings').disabled=false;}
}));

for(const [id,kind,target] of [['browseCognitive','cognitive','agentScript'],['browsePython','python','agentPython'],['browseModels','models','modelsDir']]) {
  $('#'+id).addEventListener('click',async()=>{
    $('#'+id).disabled=true;
    try {
      const result=await request('/api/paths/select?kind='+kind,{});
      if(result.path)$('#'+target).value=result.path;
      $('#settingsMessage').textContent=result.path?'Path selected. Settings save when this window closes.':'';
      if(result.path && kind==='models')await saveSettings();
    } catch(error) { $('#settingsMessage').textContent=error.message; }
    finally { $('#'+id).disabled=false; }
  });
}

async function refreshAgentStatus() {
  try {
    agentStatus=await request('/api/agent/status',undefined,'GET');
    $('#agentStatus').textContent=agentStatus.message;
    $('#stopAgent').disabled=agentAction || !agentStatus.running;
    $('#startAgent').disabled=agentAction || !agentStatus.enabled || agentStatus.running || agentStatus.connected;
    if(!agentAction)$('#startAgent').textContent=agentStatus.connected?'Connected':agentStatus.running?'Running (not connected)':'Start Cognitive Architecture Server';
    connectionLabel();
  } catch { $('#agentStatus').textContent='Embodiment server disconnected.'; }
}
for(const [id,action] of [['testHeartbeat','heartbeat'],['testAgent','test'],['startAgent','start'],['stopAgent','stop']]) {
  $('#'+id).addEventListener('click',async()=>{
    if(agentAction)return;
    agentAction=true;$('#'+id).disabled=true;
    loading('#'+id,true);
    try {
      await saveSettings(false);
      const result=await request('/api/agent/'+action,{},'POST',25000);
      $('#agentTestResult').textContent=action==='test'?JSON.stringify(result,null,2):result.message;
    } catch(error) { $('#agentTestResult').textContent=error.message; }
    finally { agentAction=false;loading('#'+id,false);$('#'+id).disabled=false;await refreshAgentStatus(); }
  });
}
setInterval(refreshAgentStatus,3000);

try {
  connectAPI();
  config=await request('/api/settings',undefined,'GET');
  $('#agentEnabled').checked=config.agent_enabled!==false;
  $('#agentHeartbeatUrl').value=config.agent_heartbeat_url;
  $('#agentScript').value=config.agent_script;
  $('#agentPython').value=config.agent_python;
  $('#agentAutostart').checked=config.agent_autostart!==false;
  $('#agentUrl').value=config.agent_url; $('#language').value=config.language;
  $('#sttLanguage').value=config.stt_language; $('#modelsDir').value=config.models_dir;
  $('#vadThreshold').value=config.vad_threshold;
  $('#liveTranscription').checked=config.live_transcription!==false;
  $('#sttModel').value=config.stt_model||'small';$('#sttDevice').value=config.stt_device||'auto';showModelHint();
  $('#speechEnabled').checked=config.speech_enabled!==false;
  $('#ttsDevice').value=config.tts_device||'cpu';
  $('#speechEnabled').disabled=false;$('#saveSettings').disabled=false;
  await refreshAgentStatus();
  loading('#status',true,'Loading avatar and lip-sync…');
  await refreshInstalledModels();
  try { avatar=await createAvatar($('#avatar'),config.character); window.avatar=avatar; }
  finally { loading('#status',false); }
  const catalog=avatar.getCatalog();
  $('#character').replaceChildren(...catalog.characters.map(item=>new Option(item.name,item.id)));
  $('#character').value=avatar.getCharacter();
  playground=await setupAPIPlayground({request,setBusy});
  $('#character').addEventListener('change',safe(async()=>{
    const finishLoading=blockLoading('Loading character and warming up its voice...');
    setBusy(true); loading('#characterStatus',true,'Loading character…');
    try { await request('/api/avatar',{character:$('#character').value}); config.character=avatar.getCharacter();await warmModels(); $('#characterStatus').textContent='Character ready. The voice now matches the character.'; }
    catch(error) { $('#characterStatus').textContent=error.message; throw error; }
    finally { finishLoading();loading('#characterStatus',false); $('#character').value=avatar.getCharacter();setBusy(false); }
  }));
  $('#screenEnabled').checked=localStorage.getItem('virtual-human-v2-screen')!=='false';
  $('#studioScreen').hidden=!$('#screenEnabled').checked;
  $('#screenEnabled').addEventListener('change',()=>{
    $('#studioScreen').hidden=!$('#screenEnabled').checked;localStorage.setItem('virtual-human-v2-screen',String($('#screenEnabled').checked));
  });
  applySpeechMode(); status.textContent='Ready';await warmModels();
  avatar.on('text',safe(async({text})=>{
    if(busy) return;
    setBusy(true); avatar.stop(); message('user',text);showPending('Agent is writing…');
    try { await finishTurn(await request('/api/chat',{text})); }
    finally {clearPending();setBusy(false);}
  }));
  avatar.on('audio',safe(async({audio})=>{
    if(busy) return;
    const recording=liveRecording;
    if(recording)recording.active=false;
    liveRecording=null;
    $('#text').value='';
    setBusy(true); const line=recording?.line||message('user','Voice message'); addRecording(line,audio);showPending('Transcribing voice message…');
    activeVoice={id:recording?.id||crypto.randomUUID(),line,text:''};
    const data=new FormData(); data.append('audio',audio,'recording');data.append('request_id',activeVoice.id);
    try {
      let liveResult=null;
      if(recording && config.live_transcription!==false) {
        showPending('Finishing the last words…');
        try {
          if(recording.inflight)try {await recording.inflight;}catch{}
          liveResult=recording.lastAudioSize===audio.size?recording.result:await transcribeLive(recording,audio);
        } catch(error) {console.warn('Live transcription unavailable; transcribing on send with the selected model:',error.message);}
      }
      let result;
      if(liveResult) {
        const text=liveResult.text.trim();
        if(!text)throw new Error('No speech detected. Check the microphone and try again.');
        activeVoice.text=text;line.textContent=text;line.parentElement.classList.remove('draft');
        showPending('Agent is writing…');
        result=await request('/api/chat',{text});
        result.diagnostics=liveResult.diagnostics;
      } else {showPending('Transcribing voice message…');result=await request('/api/voice-chat',data);}
      activeVoice.text=result.text;line.textContent=result.text;showDiagnostics(line,result.diagnostics);await finishTurn(result);
    }
    catch(error) { line.textContent=error.detail?.transcript || activeVoice.text || error.message;showDiagnostics(line,error.detail?.diagnostics);throw error; }
    finally {line.parentElement.classList.remove('draft');activeVoice=null;clearPending();setBusy(false);}
  }));
  avatar.on('audio-chunk',async({audio})=>{
    const recording=liveRecording;
    if(!recording?.active || config.live_transcription===false || recording.inflight || performance.now()-recording.lastPreview<600)return;
    recording.lastPreview=performance.now();
    recording.inflight=transcribeLive(recording,audio);
    try {
      await recording.inflight;
    } catch(error) {
      // Keep recording and the full transcription at send time available.
      if(recording===liveRecording && recording.active)status.textContent='Listening… preview unavailable; transcription will run on send';
    } finally {recording.inflight=null;recording.lastPreview=performance.now();}
  });
  avatar.on('response',({speech_text,emotion})=>{void refreshVoiceDevice();clearPending();if(speech_text) message('avatar',speech_text);});
  avatar.on('playback',playing=>{if(playing) status.textContent='Avatar is speaking'; else if(!busy) status.textContent='Ready';});
  avatar.on('recording',recording=>{
    if(recording) {
      const line=message('user',config.live_transcription===false?'Recording…':'Listening…');
      if(config.live_transcription!==false)line.parentElement.classList.add('draft');
      liveRecording={id:crypto.randomUUID(),line,active:true,inflight:false,lastPreview:performance.now()};
    }
    $('#mic').textContent=recording?'Stop & send':'Microphone'; $('#mic').setAttribute('aria-pressed',String(recording));
    status.textContent=recording?'Listening…':'Audio recorded'; refreshControls();
    $('#liveLevel').hidden=!recording;
  });
  avatar.on('level',({percent,db,peak})=>{
    $('#microphoneLevel').value=percent; $('#liveLevel').value=percent;
    if(testingMicrophone) $('#microphoneStatus').textContent=(activeMicrophoneLabel?'Active input: '+activeMicrophoneLabel+' - ':'')+(peak>.98?'Signal is clipping: lower the microphone volume':db < -55?'Very low signal or silence: speak and check the device':`Level ${Math.round(db)} dBFS · the microphone is receiving audio`);
  });
  avatar.on('microphone',({label})=>{activeMicrophoneLabel=label;refreshMicrophones().then(()=>{$('#microphoneStatus').textContent='Active input: '+label;}).catch(error=>{$('#microphoneStatus').textContent=error.message;});});
  avatar.on('error',report);
  $('#chat').addEventListener('submit',safe(event=>{event.preventDefault(); if(!busy) {avatar.sendText($('#text').value); $('#text').value='';}}));
  $('#mic').addEventListener('click',safe(async()=>{
    let finishPreparation=()=>{};
    preparingMicrophone=!avatar.getState().recording;refreshControls();$('#mic').disabled=true;
    $('#clearConversation').disabled=true;
    try {
      if(avatar.getState().recording) await avatar.stopMicrophone();
      else {
        stopMicrophoneTest();avatar.stop();
        loading('#mic',true,'Preparing transcription…');loading('#status',true);status.textContent=`Loading installed Whisper ${config.stt_model||'small'}…`;
        await warmModels();
        await avatar.startMicrophone(selectedMicrophone);
      }
    }
    finally {finishPreparation();loading('#mic',false);loading('#status',false);preparingMicrophone=false;$('#mic').textContent=avatar.getState().recording?'Stop & send':'Microphone';refreshControls();}
  }));
  $('#settings').addEventListener('enter-microphone',()=>$('#refreshMicrophones').click());
  $('#refreshMicrophones').addEventListener('click',safe(async()=>{
    loading('#microphoneStatus',true,'Finding microphones: allow access if prompted…');
    $('#refreshMicrophones').disabled=true;
    try { await refreshMicrophones(true); }
    catch(error) { $('#microphoneStatus').textContent=error.message; throw error; }
    finally {loading('#microphoneStatus',false);refreshControls();}
  }));
  $('#microphone').addEventListener('change',()=>{
    stopMicrophoneTest(); selectedMicrophone=$('#microphone').value;
    localStorage.setItem('virtual-human-v2-microphone',selectedMicrophone);
    $('#microphoneStatus').textContent='Microphone selected. Press Test level and speak.';
  });
  $('#testMicrophone').addEventListener('click',safe(async()=>{
    if(testingMicrophone) {stopMicrophoneTest(); return;}
    $('#testMicrophone').disabled=true;loading('#microphoneStatus',true,'Opening microphone: allow access if prompted…');
    try {await avatar.testMicrophone(selectedMicrophone); testingMicrophone=true; $('#testMicrophone').textContent='Stop test';}
    catch(error) {$('#microphoneStatus').textContent=error.message; throw error;}
    finally {loading('#microphoneStatus',false);refreshControls();}
  }));
  refreshMicrophones().catch(error=>{$('#microphoneStatus').textContent=error.message;});
  navigator.mediaDevices?.addEventListener('devicechange',()=>refreshMicrophones().catch(report));
  document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',safe(()=>avatar.setView(button.dataset.view))));
  document.querySelectorAll('[data-zoom]').forEach(button=>button.addEventListener('click',safe(()=>avatar.zoom(Number(button.dataset.zoom)))));
  document.querySelectorAll('[data-pan]').forEach(button=>button.addEventListener('click',safe(()=>avatar.pan(...button.dataset.pan.split(',').map(Number)))));
  $('#resetCamera').addEventListener('click',safe(()=>avatar.setView(avatar.getState().view)));
  $('#stop').addEventListener('click',()=>avatar.stop());
} catch(error) {report(error);} finally {finishStartup();}
