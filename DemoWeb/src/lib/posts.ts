import "server-only"

import { neon, type NeonQueryFunction } from "@neondatabase/serverless"

export type Post = {
  id: number
  title: string
  author: string
  content: string
  createdAt: string
  updatedAt: string
}

export type PostInput = Pick<Post, "title" | "author" | "content">

type Row = {
  id: number
  title: string
  author: string
  content: string
  created_at: Date
  updated_at: Date
}

function getSql() {
  const url = process.env.DATABASE_URL
  if (!url) throw new Error("DATABASE_URL 환경 변수가 없습니다. .env.local을 확인하세요.")
  return neon(url)
}

// 서버 프로세스마다 처음 한 번만 테이블을 만들고, 비어 있으면 안내 글을 넣는다
let ready: Promise<NeonQueryFunction<false, false>> | null = null
function db() {
  ready ??= (async () => {
    const sql = getSql()
    await sql`
      CREATE TABLE IF NOT EXISTS posts (
        id         SERIAL PRIMARY KEY,
        title      VARCHAR(100) NOT NULL,
        author     VARCHAR(30)  NOT NULL,
        content    TEXT         NOT NULL,
        created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ  NOT NULL DEFAULT now()
      )`
    await sql`
      INSERT INTO posts (title, author, content)
      SELECT '게시판에 오신 것을 환영합니다', '관리자',
             E'DemoWeb 게시판입니다.\n상단의 ''글쓰기'' 버튼으로 새 글을 작성하고, 글 상세 화면에서 수정·삭제할 수 있습니다.'
      WHERE NOT EXISTS (SELECT 1 FROM posts)`
    return sql
  })().catch((err) => {
    ready = null
    throw err
  })
  return ready
}

function toPost(row: Row): Post {
  return {
    id: row.id,
    title: row.title,
    author: row.author,
    content: row.content,
    createdAt: new Date(row.created_at).toISOString(),
    updatedAt: new Date(row.updated_at).toISOString(),
  }
}

export async function listPosts({
  query = "",
  page = 1,
  pageSize = 10,
}: {
  query?: string
  page?: number
  pageSize?: number
}) {
  const sql = await db()
  // %, _ 를 글자 그대로 검색하도록 이스케이프
  const pattern = `%${query.trim().replace(/[\\%_]/g, "\\$&")}%`

  const [{ count }] = (await sql`
    SELECT count(*)::int AS count FROM posts WHERE title ILIKE ${pattern}
  `) as { count: number }[]

  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  const current = Math.min(Math.max(1, page), totalPages)
  const rows = (await sql`
    SELECT * FROM posts
    WHERE title ILIKE ${pattern}
    ORDER BY created_at DESC, id DESC
    LIMIT ${pageSize} OFFSET ${(current - 1) * pageSize}
  `) as Row[]

  return { posts: rows.map(toPost), total: count, page: current, totalPages }
}

export async function getPost(id: number) {
  if (!Number.isInteger(id)) return null
  const sql = await db()
  const rows = (await sql`SELECT * FROM posts WHERE id = ${id}`) as Row[]
  return rows[0] ? toPost(rows[0]) : null
}

export async function createPost(input: PostInput) {
  const sql = await db()
  const rows = (await sql`
    INSERT INTO posts (title, author, content)
    VALUES (${input.title}, ${input.author}, ${input.content})
    RETURNING *
  `) as Row[]
  return toPost(rows[0])
}

export async function updatePost(id: number, input: PostInput) {
  const sql = await db()
  const rows = (await sql`
    UPDATE posts
    SET title = ${input.title}, author = ${input.author}, content = ${input.content},
        updated_at = now()
    WHERE id = ${id}
    RETURNING *
  `) as Row[]
  return rows[0] ? toPost(rows[0]) : null
}

export async function deletePost(id: number) {
  const sql = await db()
  const rows = await sql`DELETE FROM posts WHERE id = ${id} RETURNING id`
  return rows.length > 0
}
