import fs from 'node:fs';
const d=JSON.parse(fs.readFileSync('dist/data.json','utf8'));
function assert(c,m){if(!c)throw Error(m)}
assert(d.sigs.length>=20,'Missing baseline groups');
assert(new Set(d.sigs.map(s=>s.acronym)).size===d.sigs.length,'Duplicate group');
assert(d.editorial.series.length>=8,'Missing baseline series');
assert(d.editorial.archives.length>=10,'Missing baseline archives');
const known=new Set(d.sigs.map(s=>s.acronym));
const eventKeys=new Set();
for(const e of d.events){assert(known.has(e.sig)||e.sig==='ISCA','Unknown event group');assert(/^\d{4}-\d{2}-\d{2}$/.test(e.start)&&Number.isFinite(Date.parse(e.start)),'Bad event date');assert(!e.end||e.end>=e.start,'Reversed dates');const key=e.start+'|'+e.title;assert(!eventKeys.has(key),'Duplicate event');eventKeys.add(key);assert(/^https?:/.test(e.url),'Missing source URL');assert(e.reviewed,'Missing review date')}
for(const s of d.sigs){assert(s.description&&s.fullName&&s.iscaUrl,'Incomplete profile');assert(Array.isArray(s.videos)&&Array.isArray(s.activities)&&Array.isArray(s.series),'Incomplete resources')}
const all=JSON.stringify(d);assert(!/https?:\/\/(www\.)?synsig\.org/i.test(all),'Unsafe historical link');
assert(!/[A-Z]:\\\\Users|appgprj_|GMAIL_APP_PASSWORD|BEGIN PRIVATE KEY/.test(all),'Private content in public payload');
assert(fs.readFileSync('dist/index.html','utf8').includes('speechlab0210@gmail.com'),'Contact missing');
for(const name of ['index.html','style.css','app.js','data.json'])assert(fs.readFileSync('dist/'+name).equals(fs.readFileSync('docs/'+name)),'Stale Pages output: '+name);
assert(fs.existsSync('docs/.nojekyll'),'Missing static Pages marker');
assert(JSON.stringify(fs.readdirSync('docs').sort())===JSON.stringify(['.nojekyll','app.js','data.json','index.html','style.css']),'Unexpected deployed file');
console.log(JSON.stringify({ok:true,groups:d.sigs.length,series:d.editorial.series.length,recordings:d.sigs.reduce((n,s)=>n+s.videos.length,0),events:d.events.length,archives:d.editorial.archives.length}));
