const thread = document.querySelector('#thread');
const composer = document.querySelector('#composer');
const input = document.querySelector('#message');
const caseList = document.querySelector('#case-list');
const reactionLabels = {
  good_suggestion: '좋은 제안',
  considering: '고려해 볼게',
  not_for_now: '지금은 맞지 않아',
  keep_as_is: '그대로 둘래',
};
const executionLabels = {unknown: '아직 모름', done: '해봤어요', not_done: '하지 않았어요'};
const outcomeLabels = {unknown: '아직 모름', helped: '도움이 됨', no_change: '변화 없음', worse: '불편했음'};
let scenarios = [];
let conversations = [];
let selectedId = null;
let nextId = 1;
const historyDrawer = document.querySelector('#history-drawer');

function closeMobileHistory() {
  if (matchMedia('(max-width: 720px)').matches) historyDrawer.open = false;
}

function element(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = content;
  return node;
}

function currentConversation() {
  return conversations.find(conversation => conversation.id === selectedId) || null;
}

function makeConversation(question) {
  const conversation = {id: `chat-${nextId++}`, title: question.slice(0, 45), messages: []};
  conversations.unshift(conversation);
  selectedId = conversation.id;
  return conversation;
}

function lastReaction(conversation) {
  return conversation.messages.filter(message => message.kind === 'assistant' && message.feedback).at(-1)?.feedback.expression;
}

function ruleProposal(message, previousReaction) {
  const isMeasurement = /측정|체중|체지방|인바디/i.test(message);
  const isEvening = /저녁|퇴근/.test(message);
  let suggestion = '최근에 떠오르는 구체적인 한 장면을 알려주실래요?';
  let unknown = '언제 어떤 상황에서 반복되는지 아직 모릅니다.';
  let rationale = '상황을 먼저 알면 필요하지 않은 자료나 행동을 요구하지 않을 수 있습니다.';
  if (previousReaction === 'not_for_now') {
    suggestion = '앞의 제안이 지금 맞지 않았던 이유를 한 가지만 알려주실래요?';
    rationale = '지난 반응을 이번 대화에만 참고하며 고정된 성향으로 판단하지 않습니다.';
  } else if (isMeasurement) {
    suggestion = '두 측정이 같은 기기와 비슷한 조건에서 이루어졌는지 확인해 볼까요?';
    unknown = '측정 조건과 수치 차이의 원인은 아직 확인되지 않았습니다.';
    rationale = '단발 측정이나 불완전한 운동 기록만으로 원인을 단정할 수 없습니다.';
  } else if (isEvening) {
    suggestion = '최근 며칠 저녁 시간이 얼마나 들쭉날쭉했나요?';
    unknown = '저녁 일정과 실제로 쓸 수 있는 시간이 얼마나 되는지 모릅니다.';
    rationale = '부담이 적은 다음 선택을 찾으려면 가능한 시간을 먼저 알아야 합니다.';
  }
  return {
    suggestion,
    observation: '지금 확인된 것은 사용자가 직접 적은 이야기입니다. 사실 관계는 더 확인해야 합니다.',
    unknowns: [unknown],
    rationale,
    evidence: [{source_label: '현재 대화의 사용자 메시지', observed_at: new Date().toISOString(), summary: message, limitations: ['추가 자료로 확인되지 않은 자기 보고입니다.']}],
  };
}

function proposalFromScenario(scenario) {
  const proposal = scenario.proposals[0];
  const observation = scenario.claims.filter(claim => proposal.observation_claim_ids.includes(claim.id)).map(claim => claim.text).join(' ');
  return {
    suggestion: proposal.suggestion,
    observation: observation || '현재 확인된 관찰이 없습니다.',
    unknowns: proposal.unknowns,
    rationale: proposal.rationale,
    evidence: scenario.evidence.filter(item => proposal.evidence_ids.includes(item.id)),
  };
}

function appendUserAndReply(conversation, message) {
  const previousReaction = lastReaction(conversation);
  conversation.messages.push({kind: 'user', text: message});
  conversation.messages.push({kind: 'assistant', proposal: ruleProposal(message, previousReaction), feedback: null});
}

function loadScenario(scenario) {
  const conversation = makeConversation(scenario.case.question);
  const evidence = scenario.id === 'measurements_with_incomplete_activity_log' ? scenario.evidence : [];
  conversation.messages.push({kind: 'user', text: scenario.case.question, evidence});
  conversation.messages.push({kind: 'assistant', proposal: proposalFromScenario(scenario), feedback: null});
  closeMobileHistory();
  render(true);
}

function evidenceDetails(items, title) {
  const details = element('details', 'evidence');
  details.append(element('summary', '', `${title} ${items.length}건`));
  const list = element('ul');
  for (const item of items) {
    const time = item.observed_at?.slice(0, 10) || '시점 미상';
    const row = element('li');
    row.append(element('strong', '', `${item.source_label} · ${time}`));
    row.append(element('span', '', ` — ${item.summary}`));
    if (item.limitations?.length) row.append(element('small', '', ` / 한계: ${item.limitations.join(', ')}`));
    list.append(row);
  }
  details.append(list);
  return details;
}

function renderUser(message) {
  const turn = element('article', 'turn user');
  turn.append(element('div', 'role', '나'));
  const bubble = element('div', 'bubble', message.text);
  if (message.evidence?.length) bubble.append(evidenceDetails(message.evidence, '함께 본 합성 자료'));
  turn.append(bubble);
  return turn;
}

function feedbackButtons(parent, values, selected, action) {
  const row = element('div', 'state-buttons');
  for (const [value, label] of Object.entries(values)) {
    const button = element('button', selected === value ? 'selected' : '', label);
    button.type = 'button';
    button.setAttribute('aria-pressed', String(selected === value));
    button.addEventListener('click', () => action(value));
    row.append(button);
  }
  parent.append(row);
}

function renderAssistant(message) {
  const turn = element('article', 'turn assistant');
  turn.append(element('div', 'role', 'Life OS · 합성 규칙 응답'));
  const bubble = element('div', 'bubble');
  bubble.append(element('p', 'suggestion', message.proposal.suggestion));
  bubble.append(element('p', '', `현재 확인된 것: ${message.proposal.observation}`));
  bubble.append(element('p', 'unknown', `아직 모르는 점: ${message.proposal.unknowns.join(' ')}`));
  const reasons = element('details');
  reasons.append(element('summary', '', '왜 이렇게 물었나요?'));
  reasons.append(element('p', '', message.proposal.rationale));
  if (message.proposal.evidence.length) reasons.append(evidenceDetails(message.proposal.evidence, '참고한 근거'));
  bubble.append(reasons);

  bubble.append(element('div', 'reaction-label', '이 질문이나 제안은 어떤가요?'));
  const reactions = element('div', 'reactions');
  for (const [value, label] of Object.entries(reactionLabels)) {
    const button = element('button', message.feedback?.expression === value ? 'selected' : '', label);
    button.type = 'button';
    button.setAttribute('aria-pressed', String(message.feedback?.expression === value));
    button.addEventListener('click', () => {
      message.feedback = {...(message.feedback || {execution: 'unknown', outcome: 'unknown'}), expression: value};
      render();
    });
    reactions.append(button);
  }
  bubble.append(reactions);
  if (message.feedback) {
    bubble.append(element('p', 'feedback-state', `의사 표현: ${reactionLabels[message.feedback.expression]} · 실행: ${executionLabels[message.feedback.execution]} · 체감: ${outcomeLabels[message.feedback.outcome]}`));
    const later = element('details');
    later.open = Boolean(message.showLater);
    later.addEventListener('toggle', () => { message.showLater = later.open; });
    later.append(element('summary', '', '나중에 실행·체감 남기기'));
    later.append(element('p', '', '실제 실행 여부'));
    feedbackButtons(later, executionLabels, message.feedback.execution, value => {
      message.feedback.execution = value;
      message.showLater = true;
      render();
    });
    later.append(element('p', '', '나중에 느낀 결과'));
    feedbackButtons(later, outcomeLabels, message.feedback.outcome, value => {
      message.feedback.outcome = value;
      message.showLater = true;
      render();
    });
    const remove = element('button', 'remove', '이 반응 지우기');
    remove.type = 'button';
    remove.addEventListener('click', () => { message.feedback = null; render(); });
    later.append(remove);
    bubble.append(later);
  }
  turn.append(bubble);
  return turn;
}

function renderList() {
  caseList.replaceChildren();
  if (!conversations.length) caseList.append(element('p', 'empty', '아직 대화가 없습니다.'));
  for (const conversation of conversations) {
    const row = element('div', 'case-row');
    const select = element('button', conversation.id === selectedId ? 'active' : '', conversation.title);
    select.type = 'button';
    select.addEventListener('click', () => { selectedId = conversation.id; closeMobileHistory(); render(true); });
    const remove = element('button', 'remove', '지우기');
    remove.type = 'button';
    remove.setAttribute('aria-label', `${conversation.title} 대화 지우기`);
    remove.addEventListener('click', () => {
      conversations = conversations.filter(item => item.id !== conversation.id);
      if (selectedId === conversation.id) selectedId = conversations[0]?.id || null;
      render(true);
    });
    row.append(select, remove);
    caseList.append(row);
  }
}

function render(scrollToEnd = false) {
  const oldScroll = thread.scrollTop;
  thread.replaceChildren();
  const conversation = currentConversation();
  if (!conversation) {
    const welcome = element('div', 'welcome');
    welcome.append(element('h1', '', '지금 무엇이 궁금하세요?'));
    welcome.append(element('p', '', '생활의 한 장면이나 질문부터 들려주세요. 자료가 없어도 시작할 수 있습니다. 근거가 부족하면 왜 더 알아야 하는지 먼저 설명하겠습니다.'));
    thread.append(welcome);
  } else {
    for (const message of conversation.messages) thread.append(message.kind === 'user' ? renderUser(message) : renderAssistant(message));
  }
  renderList();
  thread.scrollTop = scrollToEnd ? thread.scrollHeight : oldScroll;
}

composer.addEventListener('submit', event => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  const conversation = currentConversation() || makeConversation(message);
  appendUserAndReply(conversation, message);
  input.value = '';
  render(true);
  input.focus();
});

document.querySelector('#new-chat').addEventListener('click', () => {
  selectedId = null;
  input.value = '';
  closeMobileHistory();
  render(true);
  input.focus();
});

document.querySelectorAll('[data-scenario]').forEach(button => button.addEventListener('click', () => {
  const scenario = scenarios.find(item => item.id === button.dataset.scenario);
  if (scenario) loadScenario(scenario);
}));

closeMobileHistory();
fetch('/fixtures/first_flow.synthetic.json').then(response => response.json()).then(data => { scenarios = data; }).catch(() => {
  document.querySelectorAll('[data-scenario]').forEach(button => { button.disabled = true; });
});
render();
