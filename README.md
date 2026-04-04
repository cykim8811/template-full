# Full-Stack Template

FastAPI + Next.js 기반 풀스택 웹 애플리케이션 템플릿입니다.

## 기술 스택

**Backend**
- Python 3.12 / FastAPI
- SQLAlchemy 2.0 (async) + Alembic
- PostgreSQL + Redis
- arq (백그라운드 작업)
- OAuth2 (GitHub, Google)

**Frontend**
- Next.js (App Router) + React 19
- TypeScript + Tailwind CSS 4
- shadcn/ui

## 빠른 시작

### Docker Compose (권장)

```bash
# 환경변수 설정
cp backend/.env.example backend/.env
# backend/.env에 SECRET_KEY, GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET 입력

# 실행
docker compose up
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 로컬 개발

**Backend**
```bash
cd backend
cp .env.example .env
# .env 파일에 값 입력

uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
cp .env.example .env.local
# .env.local 파일에 값 입력

pnpm install
pnpm dev
```

## 환경변수

### `backend/.env`

| 변수 | 설명 |
|------|------|
| `DATABASE_URL` | PostgreSQL 연결 URL |
| `REDIS_URL` | Redis 연결 URL |
| `SECRET_KEY` | JWT 서명 키 (`python -c "import secrets; print(secrets.token_hex(32))"`) |
| `GITHUB_CLIENT_ID` | GitHub OAuth App Client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Client Secret |
| `GITHUB_REDIRECT_URI` | GitHub OAuth 콜백 URL |
| `GOOGLE_CLIENT_ID` | (선택) Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | (선택) Google OAuth Client Secret |
| `DEBUG` | 디버그 모드 (기본값: false) |

### `frontend/.env.local`

| 변수 | 설명 |
|------|------|
| `BACKEND_URL` | 백엔드 서버 URL (서버 사이드 전용) |
| `SECRET_KEY` | backend의 `SECRET_KEY`와 동일한 값 |
| `NEXT_PUBLIC_GOOGLE_ENABLED` | Google 로그인 버튼 표시 여부 |

## OAuth 설정

### GitHub

1. https://github.com/settings/developers → "New OAuth App"
2. **Authorization callback URL**: `http://localhost:3000/api/auth/github/callback`
3. 발급된 Client ID, Client Secret을 `backend/.env`에 입력

### Google (선택)

1. https://console.cloud.google.com → API 및 서비스 → OAuth 2.0 클라이언트 ID 생성
2. **승인된 리디렉션 URI**: `http://localhost:3000/api/auth/google/callback`
3. 발급된 값을 `backend/.env`에 입력하고 `NEXT_PUBLIC_GOOGLE_ENABLED=true` 설정

## 프로젝트 구조

```
.
├── backend/
│   ├── app/
│   │   ├── auth/          # OAuth 인증 (GitHub, Google)
│   │   ├── core/          # 설정, DB, Redis, 보안
│   │   ├── users/         # 유저 모델, API
│   │   ├── deps.py        # FastAPI 의존성
│   │   └── main.py        # 앱 진입점
│   ├── alembic/           # DB 마이그레이션
│   └── tests/             # pytest 테스트
├── frontend/
│   ├── app/
│   │   ├── api/auth/      # BFF 인증 엔드포인트
│   │   └── login/         # 로그인 페이지
│   ├── contexts/          # React Context (Auth)
│   ├── hooks/             # useAuth 훅
│   └── middleware.ts      # JWT 검증, 인증 리다이렉트
└── compose.yaml           # Docker Compose
```

## 인증 흐름

1. 사용자가 `/login`에서 OAuth 버튼 클릭
2. Next.js BFF(`/api/auth/[provider]`)가 OAuth 플로우 시작
3. OAuth 콜백에서 백엔드와 토큰 교환
4. Access Token + Refresh Token을 HttpOnly 쿠키에 저장
5. Next.js 미들웨어가 매 요청마다 JWT 검증
6. 토큰 만료 시 자동 갱신

## 개발

**백엔드 테스트**
```bash
cd backend
uv run pytest
```

**백엔드 린트**
```bash
cd backend
uv run ruff check
```

**프론트엔드 린트**
```bash
cd frontend
pnpm lint
```
