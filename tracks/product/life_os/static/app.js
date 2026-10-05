const $ = (s) => document.querySelector(s);
let csrf = "", cases = [], current = null;
const reactions = {good:"좋은 제안",consider:"고려해 볼게",not_fit:"지금은 맞지 않아",keep:"그대로 둘래"};
const actions = {unknown:"아직 모름",yes:"실행함",no:"실행하지 않음"};
function node(tag, text, className) { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(className)n.className=className; return n; }
function show(message) { $("#message").textContent=message; }
function add(parent,...children) { parent.append(...children); return parent; }
function line(parent, heading, value, className) { const p=node("p",undefined,className); add(p,node("strong",heading+" "),node("span",value)); parent.append(p); }
async function api(path, method="GET", body) {
  const options={method,headers:{}};
  if(method!=="GET") { options.headers.Origin=undefined; options.headers["X-CSRF-Token"]=csrf; if(body!==undefined){options.headers["Content-Type"]="application/json";options.body=JSON.stringify(body);} }
  delete options.headers.Origin;
  let response;
  try { response=await fetch(path,options); } catch { throw new Error("서버에 연결할 수 없습니다. 입력은 아직 저장되지 않았습니다."); }
  const data=await response.json();
  if(!response.ok)throw new Error(data.error||"저장하지 못했습니다.");
  return data;
}
async function refresh(force=false) {
  const data=await api("/api/cases");
  cases=data.cases;
  renderList();
  const next=cases.find(c=>c.id===current?.id)||cases[0]||null;
  if(force||next?.revision!==current?.revision||next?.id!==current?.id) {
    if(!force && $("#detail").contains(document.activeElement))return;
    current=next; renderDetail();
  }
}
function renderList() {
  const host=$("#case-list");host.replaceChildren();
  if(!cases.length)host.append(node("p","아직 기록이 없습니다.","muted"));
  cases.forEach(c=>{const b=node("button",c.question.slice(0,55),"secondary"+(c.id===current?.id?" selected":""));b.onclick=()=>{current=c;renderList();renderDetail();};host.append(b);});
}
async function save(path,method,body) { const result=await api(path,method,body); await refresh(true); show("저장했습니다. 다른 세션에도 곧 반영됩니다."); return result; }
function formData(form) { return Object.fromEntries(new FormData(form).entries()); }
function renderDetail() {
  const host=$("#detail");host.replaceChildren();if(!current)return;
  const c=current, head=node("section",undefined,"panel");
  add(head,node("h2","지금의 이야기"),node("p",c.question));
  const edit=node("button","질문 수정","secondary"), remove=node("button","이야기 삭제","danger");
  edit.onclick=async()=>{const question=prompt("질문을 수정해 주세요.",c.question);if(question===null)return;try{await save(`/api/cases/${c.id}`,"PUT",{question});}catch(e){show(e.message);}};
  remove.onclick=async()=>{if(!confirm("이 이야기와 자료, 피드백을 모두 삭제할까요?"))return;try{await api(`/api/cases/${c.id}`,"DELETE");current=null;await refresh(true);show("이야기를 삭제했습니다.");}catch(e){show(e.message);}};
  add(head,add(node("div",undefined,"actions"),edit,remove));host.append(head);

  const evidence=node("section",undefined,"panel");add(evidence,node("h2","근거와 생활 조건"),node("p","출처와 시점을 함께 남깁니다. 첨부는 선택이며 자동으로 해석하지 않습니다.","muted"));
  if(!c.evidence.length)evidence.append(node("p","자료가 없어도 질문으로 시작할 수 있습니다.","note"));
  c.evidence.forEach(e=>{const card=node("div",undefined,"card");line(card,`${e.source} · ${e.observed_at}`,e.note||"설명 없음");
    const categoryLabel=node("label","자료 분류 다시 정하기"),categorySelect=node("select");
    for(const [key,val] of Object.entries({essential:"필수",useful:"유용",optional:"선택"})){const option=node("option",val);option.value=key;categorySelect.append(option);}
    categorySelect.value=e.category;categorySelect.onchange=async()=>{try{await save(`/api/cases/${c.id}/evidence/${e.id}`,"PUT",{category:categorySelect.value});}catch(x){show(x.message);categorySelect.value=e.category;}};
    categoryLabel.append(categorySelect);card.append(categoryLabel);
    if(e.has_file){const link=node("a",`첨부 내려받기: ${e.filename}`);link.href=`/api/evidence/${e.id}/file`;card.append(link);}
    const del=node("button","자료 삭제","link");del.onclick=async()=>{if(!confirm("이 자료를 삭제할까요?"))return;try{await save(`/api/cases/${c.id}/evidence/${e.id}`,"DELETE");}catch(x){show(x.message);}};card.append(del);evidence.append(card);});
  const ef=node("form");ef.innerHTML='<div class="inline"><label>자료 출처<input name="source" required maxlength="120" placeholder="예: 내 메모, 합성 측정 A"></label><label>자료 시점<input name="observed_at" type="date" required></label></div><label>자료에서 확인할 내용<textarea name="note" maxlength="4000" placeholder="기록에 실제로 적힌 내용만"></textarea></label><div class="inline"><label>현재 분류<select name="category"><option value="useful">유용</option><option value="optional">선택</option><option value="essential">필수</option></select></label><label>선택적 첨부 (2MB 이하)<input name="file" type="file" accept="image/png,image/jpeg,application/pdf,text/plain"></label></div><button>자료 추가</button>';
  ef.onsubmit=async ev=>{ev.preventDefault();const d=formData(ef),file=ef.elements.file.files[0];delete d.file;
    if(file){if(file.size>2000000){show("첨부는 2MB 이하여야 합니다.");return;}const bytes=new Uint8Array(await file.arrayBuffer());let binary="";bytes.forEach(b=>binary+=String.fromCharCode(b));d.file={name:file.name,mime:file.type,base64:btoa(binary)};}
    try{await save(`/api/cases/${c.id}/evidence`,"POST",d);}catch(x){show(x.message);}};
  evidence.append(ef);host.append(evidence);

  const claims=node("section",undefined,"panel");add(claims,node("h2","관찰과 해석"),node("p","관찰된 내용과 추론을 분리해 둡니다. 측정 차이만으로 원인을 단정하지 않습니다.","muted"));
  c.claims.forEach(v=>line(claims,v.kind==="observed"?"관찰":"추론",v.text,v.kind==="inferred"?"caution":"note"));
  const cf=node("form");cf.innerHTML='<div class="inline"><label>구분<select name="kind"><option value="observed">관찰</option><option value="inferred">추론</option></select></label><label>근거 자료<select name="evidence_id"><option value="">직접 적은 내용</option></select></label></div><label>내용<input name="text" required maxlength="1000"></label><button>구분해서 기록</button>';
  c.evidence.forEach(e=>{const op=node("option",`${e.source} · ${e.observed_at}`);op.value=e.id;cf.elements.evidence_id.append(op);});
  cf.onsubmit=async ev=>{ev.preventDefault();try{await save(`/api/cases/${c.id}/claims`,"POST",formData(cf));}catch(x){show(x.message);}};claims.append(cf);host.append(claims);

  const prefs=node("section",undefined,"panel");add(prefs,node("h2","피하고 싶은 조건과 제약"));
  c.preferences.forEach(v=>line(prefs,v.kind==="constraint"?"제약":"선호",v.text));
  const pf=node("form");pf.innerHTML='<div class="inline"><label>구분<select name="kind"><option value="constraint">제약</option><option value="preference">선호</option></select></label><label>내용<input name="text" required maxlength="1000" placeholder="예: 퇴근 뒤 긴 일정은 부담스러움"></label></div><button>생활 조건 기록</button>';
  pf.onsubmit=async ev=>{ev.preventDefault();try{await save(`/api/cases/${c.id}/preferences`,"POST",formData(pf));}catch(x){show(x.message);}};prefs.append(pf);host.append(prefs);

  const proposals=node("section",undefined,"panel");add(proposals,node("h2","조심스러운 제안"),node("p","한 번에 한 가지 질문 또는 제안만 보여줍니다. 이전 반응은 이번 사례의 참고일 뿐입니다.","muted"));
  const older=node("details"),olderTitle=node("summary",`지난 제안과 반응 ${Math.max(0,c.proposals.length-1)}개`);older.append(olderTitle);
  c.proposals.slice().reverse().forEach((p,index)=>{const card=node("div",undefined,"card proposal");line(card,"현재 관찰:",p.observation);line(card,"모르는 점:",p.unknown,"caution");line(card,"지금의 한 가지:",p.suggestion,"note");line(card,"판단 근거:",p.rationale);
    const feedback=p.feedback, f=node("form");add(f,node("h3","내 반응"));
    const reactionLabel=node("label","제안에 대한 생각"),reactionSelect=node("select");reactionSelect.name="reaction";Object.entries(reactions).forEach(([key,val])=>{const op=node("option",val);op.value=key;reactionSelect.append(op);});reactionSelect.value=feedback?.reaction||"consider";reactionLabel.append(reactionSelect);f.append(reactionLabel);
    const actLabel=node("label","실제로 해봤나요?"),actSelect=node("select");actSelect.name="did_act";Object.entries(actions).forEach(([key,val])=>{const op=node("option",val);op.value=key;actSelect.append(op);});actSelect.value=feedback?.did_act||"unknown";actLabel.append(actSelect);f.append(actLabel);
    const feltLabel=node("label","이후 체감 (선택)"),felt=node("textarea");felt.name="felt_result";felt.maxLength=1000;felt.value=feedback?.felt_result||"";feltLabel.append(felt);f.append(feltLabel);
    const saveButton=node("button","반응 저장");f.append(saveButton);f.onsubmit=async ev=>{ev.preventDefault();try{await save(`/api/cases/${c.id}/feedback/${p.id}`,"PUT",formData(f));}catch(x){show(x.message);}};
    if(feedback){const del=node("button","반응 삭제","link");del.type="button";del.onclick=async()=>{if(!confirm("이 반응을 삭제할까요?"))return;try{await save(`/api/cases/${c.id}/feedback/${p.id}`,"DELETE");}catch(x){show(x.message);}};f.append(del);}card.append(f);(index===0?proposals:older).append(card);});
  if(c.proposals.length>1)proposals.append(older);
  const newProposal=node("button","지금 정보로 다시 살펴보기","secondary");newProposal.onclick=async()=>{try{await save(`/api/cases/${c.id}/proposals`,"POST",{});}catch(x){show(x.message);}};proposals.append(newProposal);host.append(proposals);

  const history=node("section",undefined,"panel");add(history,node("h2","이전 이야기와 변경"));const list=node("ol",undefined,"timeline");c.chronicle.forEach(e=>list.append(node("li",`${e.created.slice(0,16).replace("T"," ")} · ${e.event}`)));history.append(list);host.append(history);
}
$("#auth-form").addEventListener("submit",async event=>{event.preventDefault();const mode=event.submitter?.value||"login";try{const data=await api(`/api/${mode}`,"POST",formData(event.target));csrf=data.csrf;$("#account").textContent=data.name;$("#auth").hidden=true;$("#workspace").hidden=false;$("#logout").hidden=false;await refresh(true);show("이야기를 이어갈 수 있습니다.");}catch(e){show(e.message);}});
$("#case-form").addEventListener("submit",async event=>{event.preventDefault();try{const c=await api("/api/cases","POST",formData(event.target));current=c;event.target.reset();await refresh(true);show("질문을 기록했습니다.");}catch(e){show(e.message);}});
$("#logout").onclick=async()=>{try{await api("/api/logout","POST",{});}finally{location.reload();}};
async function start(){try{const data=await api("/api/me");csrf=data.csrf;$("#account").textContent=data.name;$("#auth").hidden=true;$("#workspace").hidden=false;$("#logout").hidden=false;await refresh(true);}catch(e){if(!e.message.includes("로그인"))show(e.message);}}
start();setInterval(()=>{if(!$("#workspace").hidden)refresh().catch(e=>show(e.message));},5000);
