import * as store from './store.js';
import { render } from './render.js';

const ui = { editingId: null };

const form = document.getElementById('add-form');
const input = document.getElementById('new-todo');
const prioritySelect = document.getElementById('new-priority');
const list = document.getElementById('todo-list');
const toast = document.getElementById('toast');
let toastTimer = null;

function update() {
  render(store.getState(), ui);
}

store.subscribe(update);

// 추가
form.addEventListener('submit', (e) => {
  e.preventDefault();
  if (store.addTodo(input.value, prioritySelect.value)) {
    input.value = '';
  }
  input.focus();
});

// 목록: 이벤트 위임
const idOf = (el) => el.closest('.todo')?.dataset.id;

list.addEventListener('change', (e) => {
  if (e.target.classList.contains('todo__check')) store.toggleTodo(idOf(e.target));
});

list.addEventListener('click', (e) => {
  const id = idOf(e.target);
  if (!id) return;
  if (e.target.classList.contains('todo__btn--delete')) {
    store.deleteTodo(id);
    showUndoToast();
  } else if (e.target.classList.contains('todo__btn--edit')) {
    startEdit(id);
  }
});

list.addEventListener('dblclick', (e) => {
  if (e.target.classList.contains('todo__text')) startEdit(idOf(e.target));
});

// 수정
function startEdit(id) {
  ui.editingId = id;
  update();
}

function finishEdit(save) {
  const field = list.querySelector('.edit-input');
  const id = ui.editingId;
  if (!id) return;
  ui.editingId = null;
  if (save && field) store.updateTodoText(id, field.value);
  update();
}

list.addEventListener('keydown', (e) => {
  if (!e.target.classList.contains('edit-input')) return;
  if (e.key === 'Enter' && !e.isComposing) finishEdit(true);
  else if (e.key === 'Escape') finishEdit(false);
});

list.addEventListener('focusout', (e) => {
  if (e.target.classList.contains('edit-input')) finishEdit(true);
});

// 삭제 되돌리기
function showUndoToast() {
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.hidden = true; }, 5000);
}

document.getElementById('toast-undo').addEventListener('click', () => {
  store.undoDelete();
  toast.hidden = true;
  clearTimeout(toastTimer);
});

document.getElementById('clear-completed').addEventListener('click', () => {
  if (confirm('완료한 할일을 모두 지울까요?')) store.clearCompleted();
});

// 필터
document.querySelectorAll('.filter').forEach((btn) => {
  btn.addEventListener('click', () => store.setFilter(btn.dataset.filter));
});

document.getElementById('theme-toggle').addEventListener('click', store.cycleTheme);

// 이월
document.getElementById('carry-accept').addEventListener('click', store.carryOver);
document.getElementById('carry-dismiss').addEventListener('click', store.dismissCarryOver);

// 드래그 정렬
let dragId = null;

list.addEventListener('dragstart', (e) => {
  const li = e.target.closest('.todo');
  if (!li) return;
  dragId = li.dataset.id;
  li.classList.add('dragging');
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/plain', dragId);
});

list.addEventListener('dragover', (e) => {
  const li = e.target.closest('.todo');
  if (!dragId || !li) return;
  e.preventDefault();
  list.querySelectorAll('.drag-over').forEach((el) => el.classList.remove('drag-over'));
  if (li.dataset.id !== dragId) li.classList.add('drag-over');
});

list.addEventListener('drop', (e) => {
  const li = e.target.closest('.todo');
  if (!dragId || !li) return;
  e.preventDefault();
  const rect = li.getBoundingClientRect();
  const after = e.clientY > rect.top + rect.height / 2;
  store.moveTodo(dragId, li.dataset.id, after);
});

list.addEventListener('dragend', () => {
  dragId = null;
  list.querySelectorAll('.dragging, .drag-over').forEach((el) => el.classList.remove('dragging', 'drag-over'));
});

// 자정이 지나면 날짜 갱신
setInterval(store.refreshToday, 60 * 1000);
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) store.refreshToday();
});

update();
