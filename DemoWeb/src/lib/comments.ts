import "server-only"

import { db, iso } from "@/lib/db"

export type Comment = {
  id: number
  author: string
  content: string
  createdAt: string
}

export type CommentInput = Pick<Comment, "author" | "content">

type Row = { id: number; author: string; content: string; created_at: Date }

export async function listComments(postId: number) {
  const sql = await db()
  const rows = (await sql`
    SELECT id, author, content, created_at FROM comments
    WHERE post_id = ${postId}
    ORDER BY created_at, id
  `) as Row[]
  return rows.map(
    (row): Comment => ({
      id: row.id,
      author: row.author,
      content: row.content,
      createdAt: iso(row.created_at)!,
    }),
  )
}

export async function addComment(postId: number, input: CommentInput) {
  const sql = await db()
  const rows = await sql`
    INSERT INTO comments (post_id, author, content)
    SELECT id, ${input.author}, ${input.content} FROM posts WHERE id = ${postId}
    RETURNING id
  `
  return rows.length > 0
}

/** 삭제한 댓글이 달려 있던 글 ID를 돌려준다 */
export async function deleteComment(id: number) {
  const sql = await db()
  const rows = (await sql`
    DELETE FROM comments WHERE id = ${id} RETURNING post_id
  `) as { post_id: number }[]
  return rows[0]?.post_id ?? null
}
