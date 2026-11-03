# DemoWeb 게시판

Next.js(App Router) + TypeScript + shadcn/ui로 만든 간단한 웹 게시판입니다.

## 기능

- 게시글 목록 (최신순, 10개씩 페이지네이션)
- 제목 검색
- 게시글 상세 보기
- 게시글 작성 / 수정 / 삭제 (제목, 작성자, 내용) — 입력값 검증, 삭제 전 확인 대화상자
- 반응형 레이아웃 (모바일에서는 번호·작성자·작성일 열을 제목 아래로 접어서 표시)

## 실행

1. `.env.example`을 `.env.local`로 복사하고 `DATABASE_URL`에 Neon 연결 문자열을 넣습니다.
2. 실행:

```bash
npm install
npm run dev -- -p 3100   # http://localhost:3100
```

`posts` 테이블은 첫 요청 때 자동으로 만들어지고, 비어 있으면 안내 글 1개가 들어갑니다.

프로덕션 빌드: `npm run build && npm start`

## 데이터 저장 방식: Neon(PostgreSQL) + Server Actions

글은 Neon의 서버리스 PostgreSQL `posts` 테이블에 저장합니다. 읽기는 서버 컴포넌트에서, 쓰기(작성·수정·삭제)는 Server Actions(`src/app/actions.ts`)에서 처리하고, 연결에는 `@neondatabase/serverless` 드라이버(HTTP 방식)를 씁니다.

이 방식을 고른 이유:

- **설치 없이 바로 실행** — DB 서버를 직접 띄울 필요 없이 연결 문자열만 있으면 됩니다. Windows에서 네이티브 모듈을 빌드할 일도 없습니다.
- **배포 환경에서도 데이터 유지** — 처음 쓰던 로컬 JSON 파일과 달리, 여러 서버나 Vercel 같은 서버리스 환경에 배포해도 데이터가 남습니다.
- **교체가 쉬움** — 데이터 접근은 `src/lib/posts.ts` 한 곳에 모여 있습니다.

연결 문자열에는 비밀번호가 들어 있으므로 `.env.local`에만 두고 git에는 올리지 않습니다(`.gitignore`의 `.env*`).

## 폴더 구조

```
src/
  app/
    page.tsx                 목록 + 검색 + 페이지네이션
    posts/new/page.tsx       글쓰기
    posts/[id]/page.tsx      상세 보기 (수정·삭제 버튼)
    posts/[id]/edit/page.tsx 글 수정
    actions.ts               Server Actions (작성·수정·삭제)
  components/
    post-form.tsx            작성/수정 공용 폼
    delete-post-button.tsx   삭제 확인 대화상자
    ui/                      shadcn/ui 컴포넌트
  lib/posts.ts               Neon(PostgreSQL) 데이터 접근
.env.local                   DATABASE_URL (git에는 올리지 않음)
```
