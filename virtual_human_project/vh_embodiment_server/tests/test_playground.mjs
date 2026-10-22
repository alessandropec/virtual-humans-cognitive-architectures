import assert from 'node:assert/strict';
import {composeReply} from '../app/assets/api-playground.js';
const empty={speech:'',emotion:'',expression:'',gesture:'',board:'',imageUrl:''};
const nil={speech_text:null,emotion:null,expression:null,gesture:null,whiteboard:null};
assert.deepEqual(composeReply(empty),nil);
assert.deepEqual(composeReply({...empty,speech:' Hello ',emotion:'HAPPY',expression:'\u{1F609}',gesture:'handup',board:'clear'}),{
  speech_text:'Hello',emotion:'HAPPY',expression:'\u{1F609}',gesture:'handup',whiteboard:{type:'clear'}
});
assert.deepEqual(composeReply({...empty,board:'image'}),nil);
assert.deepEqual(composeReply({...empty,board:'image',imageUrl:'/media/picture.png'}),{...nil,whiteboard:{type:'image',image_url:'/media/picture.png'}});
console.log('PASS Playground always sends all fields, nulls, plain gesture IDs and image commands');
