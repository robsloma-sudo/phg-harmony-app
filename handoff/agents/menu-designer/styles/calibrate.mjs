// Measures average character width per Menu Studio font in Chromium; paste the output into CHAR_W in tools/design.mjs.
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_PATH || '/opt/node22/lib/node_modules/playwright');
const fs = await import('node:fs');
const { fontFaces } = await import('../tools/render.mjs'); const css = fontFaces();
const STACKS = [`Georgia, 'Gelasio', serif`,`'Times New Roman', Times, 'Nimbus Roman', serif`,`Palatino, 'P052', serif`,`Helvetica, Arial, 'Nimbus Sans', sans-serif`,`'Avenir Next', Avenir, 'Nunito Sans', sans-serif`,`'Trebuchet MS', 'Fira Sans', sans-serif`,`'Century Gothic', 'URW Gothic', sans-serif`,`'Courier New', 'Nimbus Mono PS', monospace`];
const sample = 'Spicy Pineapple Margarita Tequila, grapefruit, lime and soda House Cabernet Glass 11 / Bottle 40 Lagunitas IPA Mezcal Negroni Campari';
const b = await chromium.launch(); const p = await b.newPage();
await p.setContent(`<style>${css}</style><body>${STACKS.map((s,i)=>`<span id=r${i} style="font:100px ${s};white-space:nowrap"></span><span id=b${i} style="font:bold 100px ${s};white-space:nowrap"></span><span id=u${i} style="font:100px ${s};white-space:nowrap"></span>`).join('')}</body>`);
await p.evaluate(()=>document.fonts.ready);
const r = await p.evaluate(([n,s])=>{const o=[];for(let i=0;i<n;i++){const f=id=>{const e=document.getElementById(id+i);e.textContent=id==='u'?s.toUpperCase():s;return e.getBoundingClientRect().width/100/s.length};o.push([f('r'),f('b'),f('u')].map(x=>+x.toFixed(3)))}return o},[8,sample]);
console.log(JSON.stringify(r)); await b.close();
