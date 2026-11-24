'use strict';
// Offline unit check of preference defaults, validation, persistence and locale.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.resolve(__dirname,'../payload/settings-module.js'),'utf8');
const values = new Map();
const root = {dataset:{},style:{},lang:'ja'};
const context = {
  console,
  Node:{TEXT_NODE:3},
  window:{
    localStorage:{getItem:key=>values.get(key)||null,setItem:(key,val)=>values.set(key,val)},
    matchMedia:()=>({matches:false}),
    dispatchEvent:()=>{},
  },
  document:{documentElement:root,readyState:'loading',querySelector:()=>null,querySelectorAll:()=>[],addEventListener:()=>{}},
  CustomEvent:class {constructor(type,payload){this.type=type;this.detail=payload.detail;}}
};
vm.runInNewContext(source,context,{filename:'settings-module.js'});
const api = context.window.UNPSettings;
assert.equal(api.get().theme,'system');
assert.equal(api.get().language,'ja');
assert.equal(api.get().editor.autosave,true);
api.set({version:1,theme:'dark',language:'en',editor:{autosave:false,compact:true}});
assert.equal(root.dataset.theme,'dark');
assert.equal(root.dataset.density,'compact');
assert.equal(root.lang,'en');
assert.equal(api.statusText('dirty','未保存の変更'),'Unsaved changes');
assert.equal(api.statusText('saving','再試行中 (2/3)'),'Retrying (2/3)');
assert.equal(api.translate('settings.title'),'Settings');
assert.equal(JSON.parse(values.get('unp.preferences.v1')).editor.autosave,false);
api.set({version:1,theme:'invalid',language:'xx',editor:{autosave:'bad'}});
assert.equal(api.get().theme,'system');
assert.equal(api.get().language,'ja');
assert.equal(api.get().editor.autosave,true);
console.log('Settings core JS tests: OK');
