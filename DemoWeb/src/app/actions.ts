"use server"

import { revalidatePath } from "next/cache"
import { redirect } from "next/navigation"

import * as boards from "@/lib/boards"
import * as comments from "@/lib/comments"
import * as posts from "@/lib/posts"
import { ensureVisitorId } from "@/lib/visitor"

export type FormState<K extends string = string> = {
  errors?: Partial<Record<K, string>>
  values?: Record<K, string>
}

type Rule = { label: string; max: number; required?: boolean }

/** 마지막 글자에 받침이 있으면 a, 없으면 b를 붙인다 (예: 제목을, 설명을 / 작성자를) */
function josa(word: string, a: string, b: string) {
  const code = word.charCodeAt(word.length - 1) - 0xac00
  const hasFinal = code >= 0 && code <= 11171 && code % 28 !== 0
  return word + (hasFinal ? a : b)
}

/** 폼 값을 꺼내 앞뒤 공백을 지우고, 필수·길이 규칙을 검사한다 */
function parse<K extends string>(formData: FormData, rules: Record<K, Rule>) {
  const values = {} as Record<K, string>
  const errors: Partial<Record<K, string>> = {}
  for (const key of Object.keys(rules) as K[]) {
    const { label, max, required = true } = rules[key]
    const value = String(formData.get(key) ?? "").trim()
    values[key] = value
    if (required && !value) errors[key] = `${josa(label, "을", "를")} 입력하세요.`
    else if (value.length > max) errors[key] = `${josa(label, "은", "는")} ${max}자 이내로 입력하세요.`
  }
  const ok = Object.keys(errors).length === 0
  return { values, errors, ok }
}

const POST_RULES = {
  title: { label: "제목", max: 100 },
  author: { label: "작성자", max: 30 },
  content: { label: "내용", max: 20000 },
}

const BOARD_RULES = {
  name: { label: "게시판 이름", max: 30 },
  description: { label: "설명", max: 200, required: false },
}

const COMMENT_RULES = {
  author: { label: "작성자", max: 30 },
  content: { label: "댓글", max: 1000 },
}

// ── 게시판 ────────────────────────────────────────────

export async function createBoard(
  _prev: FormState<keyof typeof BOARD_RULES>,
  formData: FormData,
): Promise<FormState<keyof typeof BOARD_RULES>> {
  const { values, errors, ok } = parse(formData, BOARD_RULES)
  if (!ok) return { errors, values }

  const id = await boards.createBoard(values)
  revalidatePath("/")
  redirect(`/boards/${id}`)
}

export async function deleteBoard(id: number) {
  await boards.deleteBoard(id)
  revalidatePath("/")
  redirect("/")
}

// ── 게시글 ────────────────────────────────────────────

export async function createPost(
  boardId: number,
  _prev: FormState<keyof typeof POST_RULES>,
  formData: FormData,
): Promise<FormState<keyof typeof POST_RULES>> {
  const { values, errors, ok } = parse(formData, POST_RULES)
  if (!ok) return { errors, values }

  const id = await posts.createPost(boardId, values)
  revalidatePath(`/boards/${boardId}`)
  redirect(`/posts/${id}`)
}

export async function updatePost(
  id: number,
  _prev: FormState<keyof typeof POST_RULES>,
  formData: FormData,
): Promise<FormState<keyof typeof POST_RULES>> {
  const { values, errors, ok } = parse(formData, POST_RULES)
  if (!ok) return { errors, values }

  if (!(await posts.updatePost(id, values))) redirect("/")
  revalidatePath(`/posts/${id}`)
  redirect(`/posts/${id}`)
}

export async function deletePost(id: number) {
  const boardId = await posts.deletePost(id)
  const target = boardId ? `/boards/${boardId}` : "/"
  revalidatePath(target)
  redirect(target)
}

/** 상세 화면이 열릴 때 한 번 호출. 화면을 다시 그리지 않도록 revalidate 하지 않는다 */
export async function recordView(id: number) {
  return posts.incrementViews(id)
}

export async function toggleLike(postId: number) {
  const visitorId = await ensureVisitorId()
  await posts.toggleLike(postId, visitorId)
  revalidatePath(`/posts/${postId}`)
}

// ── 댓글 ──────────────────────────────────────────────

export async function addComment(
  postId: number,
  _prev: FormState<keyof typeof COMMENT_RULES>,
  formData: FormData,
): Promise<FormState<keyof typeof COMMENT_RULES>> {
  const { values, errors, ok } = parse(formData, COMMENT_RULES)
  if (!ok) return { errors, values }

  await comments.addComment(postId, values)
  revalidatePath(`/posts/${postId}`)
  // 작성자 이름은 남겨 두고 댓글 내용만 비운다
  return { values: { author: values.author, content: "" } }
}

export async function deleteComment(id: number) {
  const postId = await comments.deleteComment(id)
  if (postId) revalidatePath(`/posts/${postId}`)
}
