const fs=require('fs'),vm=require('vm');
const html=fs.readFileSync('index.html','utf8');
const ids=[...html.matchAll(/id="([^"]+)"/g)].map(m=>m[1]);
const elems=new Map();
const ctx2d=new Proxy({measureText:t=>({width:String(t).length*6}),createLinearGradient:()=>({addColorStop(){}}),createRadialGradient:()=>({addColorStop(){}})}, {get:(o,k)=>k in o?o[k]:(...a)=>{},set:(o,k,v)=>(o[k]=v,true)});
function el(id=''){return {id,value:({'quarterSelect':'Q125','trxWeight':'50','nrxWeight':'50','basePay':'3375','bucketSize':'10','hMin':'','hMax':''})[id]??'',innerHTML:'',textContent:'',style:{},classList:{add(){},remove(){},toggle(){}},dataset:{},disabled:false,width:700,height:400,getContext:()=>ctx2d,getBoundingClientRect:()=>({left:0,top:0,width:700,height:400}),addEventListener(){},click(){},getAttribute(){return null},contains(){return false},remove(){},replaceWith(){},parentNode:null}}
ids.forEach(id=>elems.set(id,el(id)));
const document={getElementById:id=>{if(!elems.has(id))elems.set(id,el(id));return elems.get(id)},querySelector:()=>null,querySelectorAll:()=>[],createElement:()=>el(),activeElement:null};
const territories=JSON.parse(fs.readFileSync('territories.json','utf8'));
const sandbox={console,document,window:{devicePixelRatio:1},fetch:()=>Promise.resolve({json:()=>Promise.resolve(territories)}),setTimeout,clearTimeout,Blob:function(){},URL:{createObjectURL(){return''},revokeObjectURL(){}},FileReader:function(){},alert:console.log,Math,Number,String,Array,Object,JSON,Date,parseInt,parseFloat,isNaN,Infinity};
vm.createContext(sandbox);
const core=html.match(/<script>([\s\S]*?)<\/script>/)[1];
try { vm.runInContext(core,sandbox,{filename:'index-inline.js'}); vm.runInContext(fs.readFileSync('national-summary.js','utf8'),sandbox,{filename:'national-summary.js'}); }
catch(e){console.error(e.stack);process.exit(1)}
setTimeout(()=>{
 try {
  if(!vm.runInContext('quarterlyData.length',sandbox)) throw new Error('no quarterly data');
  sandbox.renderAll();
  console.log('core territory rows, payout distribution, and national summary rendered');
  if(!elems.get('tbody').innerHTML) throw new Error('territory rows absent');
  if(!vm.runInContext('histoBars.length',sandbox)) throw new Error('distribution absent');
  if(!elems.get('nationalSummaryRoot').innerHTML) throw new Error('national section absent');
 } catch(e){console.error(e.stack);process.exit(1)}
},50);
