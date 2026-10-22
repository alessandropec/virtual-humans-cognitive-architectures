// Browser microphone access, shared by recording and the input-level test.
export function microphoneError(error) {
  const messages = {
    NotAllowedError: 'Microphone access denied. Allow microphone access in the browser site permissions and Windows/macOS privacy settings.',
    NotFoundError: 'No microphone found. Connect one and click Refresh devices.',
    OverconstrainedError: 'The selected microphone is unavailable. Click Refresh devices and select it again.',
    NotReadableError: 'Cannot open the microphone. Check device access and whether another application is using it.',
    SecurityError: 'Microphone access is blocked. Open the application on localhost or HTTPS.',
  };
  return new Error(messages[error.name] || error.message || 'Microphone access failed.');
}

export async function listInputs(requestPermission = false) {
  const media = navigator.mediaDevices;
  if (!media?.enumerateDevices) throw new Error('Microphone unavailable: use localhost or HTTPS.');
  let permission;
  try {
    if (requestPermission) permission = await media.getUserMedia({audio:true});
    // Keep access active while enumerating: some browsers hide labels otherwise.
    const devices = await media.enumerateDevices();
    const seen = new Set();
    return devices.filter(device => {
      if (device.kind !== 'audioinput' || !device.deviceId || device.deviceId === 'communications' || seen.has(device.deviceId)) return false;
      seen.add(device.deviceId);return true;
    }).map((device,index)=>({deviceId:device.deviceId,label:device.label || `Microphone ${index+1} (allow access to show its name)`,labelKnown:Boolean(device.label)}));
  } catch(error) { throw microphoneError(error); }
  finally { permission?.getTracks().forEach(track=>track.stop()); }
}

export async function openInput(deviceId = '') {
  if (!navigator.mediaDevices?.getUserMedia) throw new Error('Microphone unavailable: use localhost or HTTPS.');
  try {
    return await navigator.mediaDevices.getUserMedia({audio:{
      ...(deviceId && deviceId !== 'default' ? {deviceId:{exact:deviceId}} : {}),
      channelCount:1,echoCancellation:true,noiseSuppression:true,autoGainControl:true,
    }});
  } catch(error) { throw microphoneError(error); }
}
