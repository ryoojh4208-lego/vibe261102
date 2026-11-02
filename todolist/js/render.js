import { getTodayTodos, getCarryOverCount, isPersistent, MAX_LENGTH } from './store.js';
import { formatKoreanDate } from './utils.js';

const $ = (id) => document.getElementById(id);

const els = {
  today: $('today'),
  themeToggle: $('theme-toggle'),
  track: document.querySelector('.progress__track'),
  progressFill: $('progress-fill'),
  progressCat: $('progress-cat'),
  progressText: $('progress-text'),
  celebrate: $('celebrate'),
  carryBanner: $('carry-banner'),
  carryText: $('carry-text'),
  storageBanner: $('storage-banner'),
  list: $('todo-list'),
  empty: $('empty-state'),
  emptyArt: $('empty-art'),
  emptyText: $('empty-text'),
  remaining: $('remaining'),
  clearCompleted: $('clear-completed'),
  filters: document.querySelectorAll('.filter'),
};

const PRIORITY_LABEL = { high: '높음', medium: '보통', low: '낮음' };
const THEME_ICON = { system: '🌗', light: '☀️', dark: '🌙' };
const THEME_LABEL = { system: '시스템 테마', light: '라이트 테마', dark: '다크 테마' };
const EMPTY_TEXT = {
  all: '오늘 할 일을 추가해 보세요',
  active: '진행 중인 할일이 없어요',
  done: '완료된 할일이 없어요',
};

function setCatSymbol(svg, symbol) {
  svg.querySelector('use').setAttribute('href', symbol);
}

function renderTheme(theme) {
  if (theme === 'system') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.setAttribute('data-theme', theme);
  els.themeToggle.textContent = THEME_ICON[theme];
  els.themeToggle.setAttribute('aria-label', `테마 변경 (현재: ${THEME_LABEL[theme]})`);
  els.themeToggle.title = THEME_LABEL[theme];
}

function renderHeader(state, todos) {
  els.today.textContent = formatKoreanDate(new Date(`${state.today}T00:00:00`));

  const total = todos.length;
  const done = todos.filter((t) => t.completed).length;
  const pct = total ? Math.round((done / total) * 100) : 0;
  const allDone = total > 0 && done === total;

  els.progressFill.style.width = `${pct}%`;
  els.progressCat.style.left = `${pct}%`;
  setCatSymbol(els.progressCat, allDone ? '#cat-happy' : '#cat');
  els.track.setAttribute('aria-valuenow', String(pct));

  els.progressText.replaceChildren();
  const strong = document.createElement('strong');
  strong.textContent = `${done} / ${total}`;
  els.progressText.append(strong, ' 완료');

  els.celebrate.hidden = !allDone;
}

function createTodoItem(todo, editingId) {
  const li = document.createElement('li');
  li.className = `todo${todo.completed ? ' done' : ''}`;
  li.dataset.id = todo.id;

  const check = document.createElement('input');
  check.type = 'checkbox';
  check.className = 'todo__check';
  check.checked = todo.completed;
  check.setAttribute('aria-label', `${todo.text} 완료`);

  const dot = document.createElement('span');
  dot.className = `dot dot--${todo.priority}`;
  dot.title = `우선순위 ${PRIORITY_LABEL[todo.priority]}`;
  const dotLabel = document.createElement('span');
  dotLabel.className = 'visually-hidden';
  dotLabel.textContent = `우선순위 ${PRIORITY_LABEL[todo.priority]}`;
  dot.append(dotLabel);

  li.append(check, dot);

  if (todo.id === editingId) {
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'edit-input';
    input.value = todo.text;
    input.maxLength = MAX_LENGTH;
    input.setAttribute('aria-label', '할일 수정');
    li.append(input);
    li.draggable = false;
  } else {
    const text = document.createElement('span');
    text.className = 'todo__text';
    text.textContent = todo.text;

    const edit = document.createElement('button');
    edit.type = 'button';
    edit.className = 'todo__btn todo__btn--edit';
    edit.textContent = '✎';
    edit.setAttribute('aria-label', `${todo.text} 수정`);

    li.append(text, edit);
    li.draggable = true;
  }

  const del = document.createElement('button');
  del.type = 'button';
  del.className = 'todo__btn todo__btn--delete';
  del.textContent = '✕';
  del.setAttribute('aria-label', `${todo.text} 삭제`);
  li.append(del);

  return li;
}

function renderList(state, todos, editingId) {
  const { filter } = state.settings;
  const visible = todos.filter((t) =>
    filter === 'all' ? true : filter === 'active' ? !t.completed : t.completed);

  els.list.replaceChildren(...visible.map((t) => createTodoItem(t, editingId)));

  els.empty.hidden = visible.length > 0;
  els.emptyArt.hidden = filter !== 'all';
  els.emptyText.textContent = EMPTY_TEXT[filter];

  els.filters.forEach((btn) => {
    btn.setAttribute('aria-pressed', String(btn.dataset.filter === filter));
  });

  const remaining = todos.filter((t) => !t.completed).length;
  els.remaining.textContent = `남은 할일 ${remaining}개`;
  els.clearCompleted.disabled = !todos.some((t) => t.completed);

  const input = els.list.querySelector('.edit-input');
  if (input) {
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
  }
}

function renderBanners() {
  els.storageBanner.hidden = isPersistent();
  const carry = getCarryOverCount();
  els.carryBanner.hidden = carry === 0;
  if (carry) els.carryText.textContent = `🍠 이전에 못 끝낸 할일이 ${carry}개 있어요.`;
}

export function render(state, ui) {
  const todos = getTodayTodos();
  renderTheme(state.settings.theme);
  renderHeader(state, todos);
  renderBanners();
  renderList(state, todos, ui.editingId);
}
