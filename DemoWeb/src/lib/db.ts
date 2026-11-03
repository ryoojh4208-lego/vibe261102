import "server-only"

import { neon, type NeonQueryFunction } from "@neondatabase/serverless"

type Sql = NeonQueryFunction<false, false>

// 서버 프로세스마다 처음 한 번만 스키마를 맞춘다 (여러 번 실행해도 안전)
async function migrate(sql: Sql) {
  await sql.transaction([
    // 동시에 뜬 서버(dev, build 등)가 같이 마이그레이션하지 않도록 잠금
    sql`SELECT pg_advisory_xact_lock(261102)`,
    sql`
      CREATE TABLE IF NOT EXISTS boards (
        id          SERIAL PRIMARY KEY,
        name        VARCHAR(30)  NOT NULL,
        description VARCHAR(200) NOT NULL DEFAULT '',
        created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
      )`,
    sql`
      INSERT INTO boards (name, description)
      SELECT '자유게시판', '자유롭게 이야기를 나누는 공간입니다.'
      WHERE NOT EXISTS (SELECT 1 FROM boards)`,
    sql`
      CREATE TABLE IF NOT EXISTS posts (
        id         SERIAL PRIMARY KEY,
        title      VARCHAR(100) NOT NULL,
        author     VARCHAR(30)  NOT NULL,
        content    TEXT         NOT NULL,
        created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ  NOT NULL DEFAULT now()
      )`,
    // 게시판이 하나뿐이던 시절의 글은 첫 번째 게시판으로 옮긴다
    sql`ALTER TABLE posts ADD COLUMN IF NOT EXISTS board_id INT REFERENCES boards(id) ON DELETE CASCADE`,
    sql`UPDATE posts SET board_id = (SELECT min(id) FROM boards) WHERE board_id IS NULL`,
    sql`ALTER TABLE posts ALTER COLUMN board_id SET NOT NULL`,
    sql`ALTER TABLE posts ADD COLUMN IF NOT EXISTS views INT NOT NULL DEFAULT 0`,
    sql`CREATE INDEX IF NOT EXISTS posts_board_created_idx ON posts (board_id, created_at DESC)`,
    sql`
      CREATE TABLE IF NOT EXISTS comments (
        id         SERIAL PRIMARY KEY,
        post_id    INT          NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
        author     VARCHAR(30)  NOT NULL,
        content    VARCHAR(1000) NOT NULL,
        created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
      )`,
    sql`CREATE INDEX IF NOT EXISTS comments_post_idx ON comments (post_id, created_at)`,
    // 로그인이 없으므로 브라우저마다 발급한 방문자 ID로 하트를 한 번만 누르게 한다
    sql`
      CREATE TABLE IF NOT EXISTS post_likes (
        post_id    INT         NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
        visitor_id VARCHAR(64) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (post_id, visitor_id)
      )`,
    sql`
      INSERT INTO posts (board_id, title, author, content)
      SELECT (SELECT min(id) FROM boards), '게시판에 오신 것을 환영합니다', '관리자',
             E'DemoWeb 게시판입니다.\n상단의 ''글쓰기'' 버튼으로 새 글을 작성하고, 글 상세 화면에서 수정·삭제할 수 있습니다.'
      WHERE NOT EXISTS (SELECT 1 FROM posts)`,
  ])
}

let ready: Promise<Sql> | null = null
export function db() {
  ready ??= (async () => {
    const url = process.env.DATABASE_URL
    if (!url) throw new Error("DATABASE_URL 환경 변수가 없습니다. .env.local을 확인하세요.")
    const sql = neon(url)
    await migrate(sql)
    return sql
  })().catch((err) => {
    ready = null
    throw err
  })
  return ready
}

export function iso(value: Date | string | null) {
  return value ? new Date(value).toISOString() : null
}
