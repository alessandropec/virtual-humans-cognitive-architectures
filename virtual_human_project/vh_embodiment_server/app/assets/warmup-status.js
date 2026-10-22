/** Retry only the read-only model-status probe, never a chat or synthesis request. */
export async function readWarmupStatus(request) {
  for(let attempt=0;attempt<3;attempt++) {
    try {return await request('/api/models/warmup',undefined,'GET',15000);}
    catch(error) {
      if(error.name!=='TimeoutError')throw error;
      if(attempt===2)throw new Error('The server is taking too long to report model status. Check Server logs and try again.');
    }
  }
}
