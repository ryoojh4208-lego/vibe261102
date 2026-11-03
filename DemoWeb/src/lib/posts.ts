import "server-only"

import { db, iso } from "@/lib/db"

export type PostSummary = {
  id: number
  title: string
  author: string
  createdAt: string
  views: number
  likeCount: number
  commentCount: number
}

export type Post = PostSummary & {
  boardId: number
  boardName: string
  content: string
  updatedAt: string
  liked: boolean
}

export type PostInput = Pick<Post, "title" | "author" | "content">

type SummaryRow = {
  id: number
  title: string
  author: string
  created_at: Date
  views: number
  like_count: number
  comment_count: number
}

type Row = SummaryRow & {
  board_id: number
  board_name: string
  content: string
  updated_at: Date
  liked: boolean
}

function toSummary(row: SummaryRow): PostSummary {
  return {
    id: row.id,
    title: row.title,
    author: row.author,
    createdAt: iso(row.created_at)!,
    views: row.views,
    likeCount: row.like_count,
    commentCount: row.comment_count,
  }
}

export async function listPosts({
  boardId,
  query = "",
  page = 1,
  pageSize = 10,
}: {
  boardId: number
  query?: string
  page?: number
  pageSize?: number
}) {
  const sql = await db()
  // %, _ 를 글자 그대로 검색하도록 이스케이프
  const pattern = `%${query.trim().replace(/[\\%_]/g, "\\$&")}%`

  const [{ count }] = (await sql`
    SELECT count(*)::int AS count FROM posts
    WHERE board_id = ${boardId} AND title ILIKE ${pattern}
  `) as { count: number }[]

  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  const current = Math.min(Math.max(1, page), totalPages)
  const rows = (await sql`
    SELECT p.id, p.title, p.author, p.created_at, p.views,
           (SELECT count(*) FROM post_likes l WHERE l.post_id = p.id)::int AS like_count,
           (SELECT count(*) FROM comments c WHERE c.post_id = p.id)::int AS comment_count
    FROM posts p
    WHERE p.board_id = ${boardId} AND p.title ILIKE ${pattern}
    ORDER BY p.created_at DESC, p.id DESC
    LIMIT ${pageSize} OFFSET ${(current - 1) * pageSize}
  `) as SummaryRow[]

  return { posts: rows.map(toSummary), total: count, page: current, totalPages }
}

export async function getPost(id: number, visitorId?: string) {
  if (!Number.isInteger(id)) return null
  const sql = await db()
  const rows = (await sql`
    SELECT p.*, b.name AS board_name,
           (SELECT count(*) FROM post_likes l WHERE l.post_id = p.id)::int AS like_count,
           (SELECT count(*) FROM comments c WHERE c.post_id = p.id)::int AS comment_count,
           EXISTS (SELECT 1 FROM post_likes l
                   WHERE l.post_id = p.id AND l.visitor_id = ${visitorId ?? ""}) AS liked
    FROM posts p JOIN boards b ON b.id = p.board_id
    WHERE p.id = ${id}
  `) as Row[]
  const row = rows[0]
  if (!row) return null
  return {
    ...toSummary(row),
    boardId: row.board_id,
    boardName: row.board_name,
    content: row.content,
    updatedAt: iso(row.updated_at)!,
    liked: row.liked,
  } satisfies Post
}

export async function createPost(boardId: number, input: PostInput) {
  const sql = await db()
  const rows = (await sql`
    INSERT INTO posts (board_id, title, author, content)
    VALUES (${boardId}, ${input.title}, ${input.author}, ${input.content})
    RETURNING id
  `) as { id: number }[]
  return rows[0].id
}

export async function updatePost(id: number, input: PostInput) {
  const sql = await db()
  const rows = await sql`
    UPDATE posts
    SET title = ${input.title}, author = ${input.author}, content = ${input.content},
        updated_at = now()
    WHERE id = ${id}
    RETURNING id
  `
  return rows.length > 0
}

/** 삭제한 글이 있던 게시판 ID를 돌려준다 */
export async function deletePost(id: number) {
  const sql = await db()
  const rows = (await sql`
    DELETE FROM posts WHERE id = ${id} RETURNING board_id
  `) as { board_id: number }[]
  return rows[0]?.board_id ?? null
}

export async function incrementViews(id: number) {
  const sql = await db()
  const rows = (await sql`
    UPDATE posts SET views = views + 1 WHERE id = ${id} RETURNING views
  `) as { views: number }[]
  return rows[0]?.views ?? null
}

/** 하트를 누른 상태면 취소하고, 아니면 누른다 */
export async function toggleLike(postId: number, visitorId: string) {
  const sql = await db()
  const removed = await sql`
    DELETE FROM post_likes WHERE post_id = ${postId} AND visitor_id = ${visitorId}
    RETURNING post_id
  `
  if (removed.length === 0) {
    await sql`
      INSERT INTO post_likes (post_id, visitor_id)
      SELECT id, ${visitorId} FROM posts WHERE id = ${postId}
      ON CONFLICT DO NOTHING
    `
  }
}
