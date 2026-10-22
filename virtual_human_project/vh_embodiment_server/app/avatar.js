import { listInputs, openInput } from './assets/microphone.js';
import { TalkingHead } from './lib/TalkingHead/modules/talkinghead.mjs';
import { HeadAudio } from './lib/HeadAudio/dist/headaudio.min.mjs';

const MOTION_SECONDS = 5;

// Browser-only client API. No agent, STT or TTS.
export async function createAvatar(element, initialCharacter = 'julia') {
  const catalogResponse = await fetch('./api/catalog');
  if (!catalogResponse.ok) throw new Error('Avatar catalog unavailable');
  const catalog = await catalogResponse.json();
  const events = new EventTarget();
  const emit = (name, detail) => events.dispatchEvent(new CustomEvent(name, { detail }));
  const head = new TalkingHead(element, {
    ttsEndpoint: null, lipsyncModules: [], cameraView: 'upper', cameraZoomEnable: true, cameraPanEnable: false, modelFPS: 30,
    modelPixelRatio: Math.min(devicePixelRatio, 1.5), mixerGainSpeech: 1,
  });
  await head.audioCtx.audioWorklet.addModule('./lib/HeadAudio/dist/headworklet.min.mjs');
  const lipsync = new HeadAudio(head.audioCtx, {
    processorOptions: { visemeEventsEnabled: true }, parameterData: { vadMode: 1 },
  });
  await lipsync.loadModel('./lib/HeadAudio/dist/model-en-mixed.bin');
  head.audioSpeechGainNode.connect(lipsync);
  const delay = new DelayNode(head.audioCtx, { delayTime: 0.1 });
  head.audioSpeechGainNode.disconnect(head.audioReverbNode);
  head.audioSpeechGainNode.connect(delay);
  delay.connect(head.audioReverbNode);
  const diagnostics = { visemeUpdates: 0, activeVisemes: 0, lastAudioSeconds: 0 };
  lipsync.onvalue = (key, value) => {
    if (!head.mtAvatar[key]) return;
    Object.assign(head.mtAvatar[key], { newvalue: value, needsUpdate: true });
    diagnostics.visemeUpdates++;
    if (value > 0.05) diagnostics.activeVisemes++;
  };
  lipsync.onviseme = ({viseme}) => emit('viseme', lipsync.visemeNames[viseme]);
  head.opt.update = lipsync.update.bind(lipsync);
  const characters = [
    { id: 'julia', name: 'Julia', url: './assets/avatar.glb', body: 'F' },
    { id: 'david', name: 'David', url: './assets/david.glb', body: 'M' },
  ];
  let character = characters.find(item => item.id === initialCharacter) || characters[0];
  let changingCharacter = false;
  await head.showAvatar({ ...character, avatarMood: 'neutral' });
  if(head.controls){head.controls.minDistance=2;head.controls.maxDistance=28;head.controls.zoomSpeed=0.65;}
  // Frame translation lives in the projection, so orbiting keeps its avatar pivot.
  let framing={x:0,y:0};
  const applyFraming=()=>{
    const {width,height}=element.getBoundingClientRect();
    if(!width||!height)return;
    framing.x=Math.max(-width*.42,Math.min(width*.42,framing.x));
    framing.y=Math.max(-height*.42,Math.min(height*.42,framing.y));
    head.camera.setViewOffset(width,height,-framing.x,-framing.y,width,height);
  };
  const resetFraming=()=>{framing={x:0,y:0};head.camera.clearViewOffset();};
  if (head.controls?.connect) {
    head.controls.mouseButtons.LEFT=undefined;head.controls.mouseButtons.RIGHT=0;
    head.controls.disconnect();head.controls.connect(document.documentElement);
    document.documentElement.style.touchAction='auto';
    const isUI=event=>(event.type==='wheel' && event.target.closest?.('#screenTools')) ? false : event.target.closest?.('button,input,select,textarea,a,header,dialog,#conversation,#playground,#cameraControls') || (event.type!=='wheel' && event.button!==2 && event.target.closest?.('#screenTools'));
    const inScene=event=>{const r=element.getBoundingClientRect();return event.clientX>=r.left&&event.clientX<=r.right&&event.clientY>=r.top&&event.clientY<=r.bottom;};
    let drag=null;
    document.body.addEventListener('pointerdown',event=>{
      if(isUI(event)||!inScene(event)){event.stopPropagation();return;}
      head.cameraClock=null;
      if(event.button===0){
        drag={id:event.pointerId,x:event.clientX,y:event.clientY,start:{...framing}};
        document.body.setPointerCapture(event.pointerId);event.preventDefault();event.stopPropagation();
      }
    });
    document.body.addEventListener('pointermove',event=>{
      if(!drag||event.pointerId!==drag.id)return;
      framing={x:drag.start.x+event.clientX-drag.x,y:drag.start.y+event.clientY-drag.y};applyFraming();event.stopPropagation();
    });
    const finish=event=>{
      if(!drag||event.pointerId!==drag.id)return;drag=null;
      if(document.body.hasPointerCapture(event.pointerId))document.body.releasePointerCapture(event.pointerId);
      event.stopPropagation();
    };
    document.body.addEventListener('pointerup',finish);document.body.addEventListener('pointercancel',finish);
    for(const type of ['wheel','contextmenu'])document.body.addEventListener(type,event=>{
      if(isUI(event)||!inScene(event))event.stopPropagation();
      else {head.cameraClock=null;if(type==='contextmenu'){event.preventDefault();event.stopPropagation();}}
    });
    new ResizeObserver(applyFraming).observe(element);
  }




  let playback = 0, recorder = null, stream = null, chunks = [], starting = false;
  let speechEnabled = true;
  let recordingResult, finishRecording, failRecording;
  let previewStream = null, meterTimer = null, meterSource = null, analyser = null;
  let meterContext = null, meterSink = null;
  function stopMeter() {
    clearInterval(meterTimer); meterSource?.disconnect(); analyser?.disconnect();
    meterSink?.disconnect(); meterSink = null;
    const oldContext = meterContext; meterContext = null;
    if (oldContext && oldContext.state !== 'closed') oldContext.close().catch(() => {});
    meterSource = null; analyser = null; emit('level', { percent: 0, db: -120, peak: 0 });
  }
  async function monitor(input) {
    stopMeter();
    // Capture must remain independent of avatar playback/visibility suspension.
    meterContext = new AudioContext();
    await meterContext.resume();
    meterSource = meterContext.createMediaStreamSource(input);
    analyser = meterContext.createAnalyser(); analyser.fftSize = 2048;
    meterSource.connect(analyser);
    // Keep the capture graph rendering without playing the microphone back.
    meterSink = meterContext.createGain(); meterSink.gain.value = 0;
    analyser.connect(meterSink); meterSink.connect(meterContext.destination);
    const samples = new Float32Array(analyser.fftSize);
    meterTimer = setInterval(() => {
      if (!analyser) return;
      analyser.getFloatTimeDomainData(samples);
      let power = 0, peak = 0;
      for (const sample of samples) { power += sample * sample; peak = Math.max(peak, Math.abs(sample)); }
      const db = 20 * Math.log10(Math.max(1e-6, Math.sqrt(power / samples.length)));
      emit('level', { db, peak, percent: Math.max(0, Math.min(100, (db + 60) / 60 * 100)) });
    }, 80);
    emit('microphone', { label: input.getAudioTracks()[0]?.label || 'Selected microphone' });
  }
  const motions = {expression:null, gesture:null};
  let bodyTimer = null;
  let whiteboard = {type:'clear'}, responseVersion = 0;
  const motionTimers = {};
  function track(key, value, seconds) {
    clearTimeout(motionTimers[key]); motions[key] = value;
    if (seconds) motionTimers[key] = setTimeout(() => { motions[key] = null; emit('motion', {...motions, mood:head.moodName}); }, seconds*1000);
    emit('motion', {...motions, mood:head.moodName});
  }
  const reaction = name => catalog.expressions.find(item => item.id === name || item.aliases.includes(name));
  const api = {
    diagnostics,
    getCatalog: () => catalog,
    getCharacter: () => character.id,
    getCharacterName: () => character.name,
    async selectCharacter(id) {
      const next = characters.find(item => item.id === id);
      if (!next) throw new Error('Unknown character');
      if (changingCharacter || api.getState().recording) throw new Error('Wait before switching characters');
      changingCharacter = true;
      api.stop(); api.reset();
      const previous = character, mood = head.moodName, view = head.viewName;
      try {
        await head.showAvatar({...next, avatarMood:mood});
        character = next; resetFraming(); head.setView(view);
      } catch(error) {
        await head.showAvatar({...previous, avatarMood:mood}); head.setView(view);
        throw error;
      } finally { changingCharacter = false; }
    },
    stopExpression() {
      head.animQueue = head.animQueue.filter(item => !item.vhExpression);
      track('expression',null);
    },
    stopBody() {
      clearTimeout(bodyTimer); bodyTimer = null;
      head.stopGesture(150);
      head.animQueue = head.animQueue.filter(item => !item.vhBody);
      track('gesture',null);
    },
    expression(name) {
      const seconds = MOTION_SECONDS;
      const item = reaction(name);
      if (!item) throw new Error('Unknown expression');
      api.stopExpression();
      const before = new Set(head.animQueue);
      head.playGesture(item.id,seconds);
      for (const anim of head.animQueue) if (!before.has(anim) && anim.gesture) {
        anim.gesture=false; anim.vhExpression=true;
      }
      track('expression',item.id,seconds);
    },
    gesture(name) {
      const seconds = MOTION_SECONDS;
      if (!catalog.gestures.some(item => item.id === name)) throw new Error('Unknown gesture');
      api.stopBody();
      // Schedule our deadline first so it cancels TalkingHead's slower default release.
      bodyTimer = setTimeout(() => api.stopBody(), seconds * 1000);
      const before = new Set(head.animQueue);
      head.playGesture(name, seconds, false, 150);
      for (const anim of head.animQueue) if (!before.has(anim) && anim.gesture) anim.vhBody=true;
      track('gesture',name);
    },
    stopMotion(trackName='all') {
      if (trackName==='all'||trackName==='expression') api.stopExpression();
      if (trackName==='all'||trackName==='body') api.stopBody();
    },
    setSpeechEnabled(enabled) { speechEnabled = Boolean(enabled); if (!speechEnabled) api.stop(); },
    on(name, callback) {
      const listener = event => callback(event.detail);
      events.addEventListener(name, listener);
      return () => events.removeEventListener(name, listener);
    },
    getState: () => ({ ...motions, character:character.id, mood: head.moodName, view: head.viewName,
      speaking: !!head.isAudioPlaying, recording: starting || recorder?.state === 'recording', whiteboard }),
    setMood: mood => head.setMood(mood.toLowerCase()),
    setView(view) { resetFraming();head.setView(view); document.querySelectorAll('[data-view]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.view===view))); },
    zoom(direction) {
      head.cameraClock = null;
      const offset = head.camera.position.clone().sub(head.controls.target);
      const distance = offset.length();
      const next = Math.max(head.controls.minDistance,Math.min(head.controls.maxDistance,distance * (direction > 0 ? 0.85 : 1/0.85)));
      head.camera.position.copy(head.controls.target).add(offset.multiplyScalar(next/distance));
      head.controls.update();
    },
    pan(x, y) {
      head.cameraClock = null;
      const {width,height}=element.getBoundingClientRect();
      framing.x+=x*width*.06;framing.y-=y*height*.06;applyFraming();
    },
    lookAtCamera: (milliseconds = 2000) => head.lookAtCamera(milliseconds),
    reset() { api.stopMotion(); head.setMood('neutral'); },
    stop() { playback++; head.stopSpeaking(); emit('playback', false); },
    async playAudio(source) {
      if (!speechEnabled) return;
      const version = ++playback;
      await head.audioCtx.resume();
      head.stopSpeaking();
      let bytes;
      if (source instanceof Blob) bytes = await source.arrayBuffer();
      else if (source instanceof ArrayBuffer) bytes = source.slice(0);
      else {
        const response = await fetch(source);
        if (!response.ok) throw new Error(`Audio unavailable (${response.status})`);
        bytes = await response.arrayBuffer();
      }
      const audio = await head.audioCtx.decodeAudioData(bytes);
      if (version !== playback) return;
      diagnostics.lastAudioSeconds = audio.duration;
      lipsync.resetTimer();
      head.speakAudio({ audio, words: [], visemes: [] }, { isRaw: true });
      emit('playback', true);
      head.speakMarker(() => { if (version === playback) emit('playback', false); });
    },
    sendText(text) {
      text = String(text).trim();
      if (!text) throw new Error('Type a message');
      emit('text', { text });
    },
    async receive({ diagnostics: responseStats = null, speech_text = '', audio_url = null, emotion = null, expression = null, gesture = null, whiteboard: board = null }) {
      const version = ++responseVersion;
      // Load the next picture before replacing the previous one.
      let image;
      if (board?.type === 'image') {
        image = new Image(); image.alt = 'Whiteboard image';
        image.src = board.image_url;
        await image.decode();
      }
      if (version !== responseVersion) return;
      if (emotion) api.setMood(emotion.toLowerCase());
      if (expression) api.expression(expression);
      if (gesture) await api.gesture(gesture);
      if (version !== responseVersion) return;
      if (board) {
        document.querySelector('#studioScreen').replaceChildren(...(image ? [image] : []));
        whiteboard = {...board};
      }
      emit('response', { diagnostics: responseStats, speech_text, audio_url, emotion, expression, gesture });
      if (audio_url) await api.playAudio(audio_url);
    },
    listMicrophones: listInputs,
    stopMicrophoneTest() {
      if (!previewStream) return;
      previewStream.getTracks().forEach(track => track.stop()); previewStream = null; stopMeter();
    },
    async testMicrophone(deviceId = '') {
      if (starting || recorder) throw new Error('Finish recording before testing the microphone');
      api.stopMicrophoneTest();
      previewStream = await openInput(deviceId);
      try { await monitor(previewStream); }
      catch (error) { api.stopMicrophoneTest(); throw error; }
    },
    async startMicrophone(deviceId = '') {
      if (starting || recorder) throw new Error('Microphone already active');
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) throw new Error('This browser does not support recording');
      starting = true;
      try {
        api.stopMicrophoneTest();
        stream = await openInput(deviceId);
        await monitor(stream);
        const mimeType = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/webm'].find(type => MediaRecorder.isTypeSupported(type));
        recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
        chunks = [];
        recordingResult = new Promise((resolve, reject) => { finishRecording = resolve; failRecording = reject; });
        recordingResult.catch(() => {});
        recorder.ondataavailable = event => {
          if (event.data.size) {
            chunks.push(event.data);
            emit('audio-chunk', { audio: new Blob(chunks, { type: recorder.mimeType }) });
          }
        };
        recorder.onstop = () => {
          const audio = new Blob(chunks, { type: recorder.mimeType });
          stream.getTracks().forEach(track => track.stop());
          stream = null; recorder = null;
          stopMeter();
          emit('recording', false);
          if (audio.size) { emit('audio', { audio, mimeType: audio.type }); finishRecording(audio); }
          else failRecording(new Error('Empty recording'));
        };
        recorder.onerror = event => {
          const error = event.error || new Error('Recording failed');
          failRecording(error); emit('error', error);
          stream?.getTracks().forEach(track => track.stop());
          if (recorder?.state === 'recording') recorder.stop();
        };
        recorder.start(250); emit('recording', true);
      } catch (error) {
        stream?.getTracks().forEach(track => track.stop()); stream = null; recorder = null;
        stopMeter();
        throw error;
      } finally { starting = false; }
    },
    stopMicrophone() {
      if (!recorder || recorder.state !== 'recording') throw new Error('Microphone is not active');
      recorder.stop(); return recordingResult;
    },
  };
  document.addEventListener('visibilitychange', () => { document.hidden ? head.stop() : head.start(); });
  window.addEventListener('pagehide', () => { stream?.getTracks().forEach(track => track.stop()); api.stopMicrophoneTest(); stopMeter(); });
  return api;
}
