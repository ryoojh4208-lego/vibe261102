"use server"

import { revalidatePath } from "next/cache"
import { redirect } from "next/navigation"

import * as db from "@/lib/posts"

export type FormState = {
  errors?: Partial<Record<"title" | "author" | "content", string>>
  values?: db.PostInput
}

function parse(formData: FormData) {
  const values: db.PostInput = {
    title: String(formData.get("title") ?? "").trim(),
    author: String(formData.get("author") ?? "").trim(),
    content: String(formData.get("content") ?? "").trim(),
  }
  const errors: FormState["errors"] = {}
  if (!values.title) errors.title = "제목을 입력하세요."
  else if (values.title.length > 100) errors.title = "제목은 100자 이내로 입력하세요."
  if (!values.author) errors.author = "작성자를 입력하세요."
  else if (values.author.length > 30) errors.author = "작성자는 30자 이내로 입력하세요."
  if (!values.content) errors.content = "내용을 입력하세요."
  return { values, errors }
}

export async function createPost(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const { values, errors } = parse(formData)
  if (Object.keys(errors).length) return { errors, values }

  const post = await db.createPost(values)
  revalidatePath("/")
  redirect(`/posts/${post.id}`)
}

export async function updatePost(
  id: number,
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const { values, errors } = parse(formData)
  if (Object.keys(errors).length) return { errors, values }

  const post = await db.updatePost(id, values)
  if (!post) redirect("/")
  revalidatePath("/")
  revalidatePath(`/posts/${id}`)
  redirect(`/posts/${id}`)
}

export async function deletePost(id: number) {
  await db.deletePost(id)
  revalidatePath("/")
  redirect("/")
}
