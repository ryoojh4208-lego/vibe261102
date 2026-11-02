import { toDateKey, createId } from './utils.js';

const TODOS_KEY = 'todolist:v1:todos';
const SETTINGS_KEY = 'todolist:v1:settings';

export const MAX_LENGTH = 100;
const PRIORITIES = ['high', 'medium', 'low'];
const FILTERS = ['all', 'active', 'done'];
const THEMES = ['system', 'light', 'dark'];

const persistent = checkStorage();
const listeners = new Set();

const state = {
  todos: loadTodos(),
  settings: loadSettings(),
  today: toDateKey(),
};

let lastDeleted = null;

function checkStorage() {
  try {
    const key = 'todolist:probe';
    localStorage.setItem(key, key);
    localStorage.removeItem(key);
    return true;
  } catch {
    return false;
  }
}

function readJSON(key) {
  if (!persistent) return null;
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function isValidTodo(t) {
  return t && typeof t.id === 'string' && typeof t.text === 'string' && typeof t.date === 'string';
}

function loadTodos() {
  const data = readJSON(TODOS_KEY);
  if (!Array.isArray(data)) return [];
  return data.filter(isValidTodo).map((t, i) => ({
    id: t.id,
    text: t.text.slice(0, MAX_LENGTH),
    completed: Boolean(t.completed),
    priority: PRIORITIES.includes(t.priority) ? t.priority : 'medium',
    date: t.date,
    order: Number.isFinite(t.order) ? t.order : i,
    createdAt: Number.isFinite(t.createdAt) ? t.createdAt : Date.now(),
    completedAt: Number.isFinite(t.completedAt) ? t.completedAt : null,
  }));
}

function loadSettings() {
  const data = readJSON(SETTINGS_KEY) || {};
  return {
    filter: FILTERS.includes(data.filter) ? data.filter : 'all',
    theme: THEMES.includes(data.theme) ? data.theme : 'system',
    carryDismissedOn: typeof data.carryDismissedOn === 'string' ? data.carryDismissedOn : null,
  };
}

function save() {
  if (!persistent) return;
  try {
    localStorage.setItem(TODOS_KEY, JSON.stringify(state.todos));
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(state.settings));
  } catch {
    // 용량 초과 등: 메모리 상태로 계속 동작
  }
}

function commit() {
  save();
  listeners.forEach((fn) => fn(state));
}

function nextOrder() {
  const orders = state.todos.filter((t) => t.date === state.today).map((t) => t.order);
  return orders.length ? Math.max(...orders) + 1 : 0;
}

export function isPersistent() {
  return persistent;
}

export function getState() {
  return state;
}

export function subscribe(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

// 오늘 할일: 미완료가 위, 완료가 아래, 각 그룹은 order(생성 순/드래그 순)
export function getTodayTodos() {
  return state.todos
    .filter((t) => t.date === state.today)
    .sort((a, b) => Number(a.completed) - Number(b.completed) || a.order - b.order);
}

export function getCarryOverCount() {
  if (state.settings.carryDismissedOn === state.today) return 0;
  return state.todos.filter((t) => t.date < state.today && !t.completed).length;
}

export function addTodo(text, priority = 'medium') {
  const trimmed = text.trim().slice(0, MAX_LENGTH);
  if (!trimmed) return false;
  state.todos.push({
    id: createId(),
    text: trimmed,
    completed: false,
    priority: PRIORITIES.includes(priority) ? priority : 'medium',
    date: state.today,
    order: nextOrder(),
    createdAt: Date.now(),
    completedAt: null,
  });
  commit();
  return true;
}

export function toggleTodo(id) {
  const todo = state.todos.find((t) => t.id === id);
  if (!todo) return;
  todo.completed = !todo.completed;
  todo.completedAt = todo.completed ? Date.now() : null;
  commit();
}

export function updateTodoText(id, text) {
  const todo = state.todos.find((t) => t.id === id);
  const trimmed = text.trim().slice(0, MAX_LENGTH);
  if (!todo || !trimmed || trimmed === todo.text) return;
  todo.text = trimmed;
  commit();
}

export function deleteTodo(id) {
  const index = state.todos.findIndex((t) => t.id === id);
  if (index === -1) return;
  const [todo] = state.todos.splice(index, 1);
  lastDeleted = { todo, index };
  commit();
}

export function undoDelete() {
  if (!lastDeleted) return;
  const { todo, index } = lastDeleted;
  state.todos.splice(Math.min(index, state.todos.length), 0, todo);
  lastDeleted = null;
  commit();
}

export function clearCompleted() {
  state.todos = state.todos.filter((t) => !(t.date === state.today && t.completed));
  lastDeleted = null;
  commit();
}

// 드래그 정렬: dragId를 targetId 앞(또는 after면 뒤)으로 옮기고 order를 다시 매긴다.
export function moveTodo(dragId, targetId, after = false) {
  if (dragId === targetId) return;
  const list = getTodayTodos();
  const from = list.findIndex((t) => t.id === dragId);
  if (from === -1) return;
  const [dragged] = list.splice(from, 1);
  let to = list.findIndex((t) => t.id === targetId);
  if (to === -1) return;
  if (after) to += 1;
  list.splice(to, 0, dragged);
  list.forEach((t, i) => { t.order = i; });
  commit();
}

export function carryOver() {
  let order = nextOrder();
  state.todos
    .filter((t) => t.date < state.today && !t.completed)
    .sort((a, b) => a.date.localeCompare(b.date) || a.order - b.order)
    .forEach((t) => {
      t.date = state.today;
      t.order = order++;
    });
  commit();
}

export function dismissCarryOver() {
  state.settings.carryDismissedOn = state.today;
  commit();
}

export function setFilter(filter) {
  if (!FILTERS.includes(filter)) return;
  state.settings.filter = filter;
  commit();
}

export function cycleTheme() {
  const i = THEMES.indexOf(state.settings.theme);
  state.settings.theme = THEMES[(i + 1) % THEMES.length];
  commit();
}

// 자정이 지나면 오늘 날짜를 갱신한다.
export function refreshToday() {
  const key = toDateKey();
  if (key === state.today) return;
  state.today = key;
  commit();
}
