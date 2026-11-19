# 연구질문 코치

전공과 관심 키워드를 입력하면 AI(Gemini)가 연구 질문 후보 3개와 문헌 검색 키워드를 제안하는 웹 서비스입니다.

- **배포 URL**: (Vercel 배포 후 기입)
- 기획서: [docs/plan.md](docs/plan.md) · 개념 설명: [docs/concepts.md](docs/concepts.md) · 체크리스트: [CHECKLIST.md](CHECKLIST.md)

## 기술 스택
- 프론트엔드: 순수 HTML, CSS, JavaScript (프레임워크 없음)
- 백엔드: Vercel Serverless Functions (Python), `api/` 폴더
- AI: Google Gemini API (`requests`로 REST 호출)
- 배포: GitHub 연동 + Vercel

## 폴더 구조
```text
index.html        메인 페이지(4개 섹션)
css/ js/          프론트엔드
api/coach.py      엔드포인트 POST /api/coach
api/_core.py      검증, 프롬프트, 호출 로직 (밑줄 파일은 엔드포인트가 아님)
tests/            단위 테스트
docs/             기획서, 개념 설명
requirements.txt  Python 의존성
```

## 환경 변수
| 이름 | 필수 | 설명 |
|---|---|---|
| `GEMINI_API_KEY` | 필수 | Google AI Studio에서 발급한 키 |
| `GEMINI_MODEL` | 선택 | 기본값 `gemini-2.5-flash` |

키는 코드, README, 스크린샷에 넣지 않습니다. `.env.example`을 참고하되 실제 값은 `.env`(Git 제외) 또는 Vercel 설정에만 저장합니다.

## 로컬 실행 (macOS, 관리자 권한 불필요)
Vercel CLI는 Node.js가 필요합니다. 없다면 아래 "화면만 확인" 방법을 쓰세요.

```bash
python3 -m venv .venv
```
```bash
source .venv/bin/activate
```
```bash
pip install -r requirements.txt
```
```bash
cp .env.example .env
```
`.env` 파일을 열어 `GEMINI_API_KEY=` 뒤에 키를 입력합니다.

```bash
npx vercel dev
```
브라우저에서 안내된 주소(보통 http://localhost:3000)를 엽니다.

**화면만 확인**(AI 호출 없이): `python3 -m http.server 8000` 실행 후 http://localhost:8000 접속. 제출하면 `/api/coach`가 없어 오류 안내가 표시됩니다.

## 테스트
```bash
python3 -m unittest discover -s tests -v
```
외부 AI 호출은 mock으로 대체한 단위 테스트이며, 실제 API 호출 테스트는 아닙니다.

## Vercel 배포
1. GitHub에 이 저장소를 push합니다.
2. Vercel에서 **Add New → Project**로 저장소를 가져옵니다. `vercel.json`이 프레임워크 자동 감지를 끄므로 Framework Preset은 **Other**(빌드 명령 없음)로 둡니다. Python 프리셋이 선택되면 `PYTHON_ENTRYPOINT_NOT_FOUND` 오류가 날 수 있습니다.
3. **Settings → Environment Variables**에 `GEMINI_API_KEY`를 추가합니다(Production, Preview 모두).
4. **Deploy** 후 배포 URL에서 네비게이션, 모바일 화면, AI 기능을 확인합니다.
5. 환경 변수를 바꾼 뒤에는 재배포해야 반영됩니다. 오류는 Vercel의 Logs에서 확인합니다.

## 주의사항
- AI 호출에는 비용이 발생할 수 있습니다. 입력 길이와 출력 토큰을 제한했고, Google AI Studio에서 사용량과 결제 설정을 확인하세요.
- 키가 노출되었다면 즉시 폐기하고 재발급하세요.
- 제안된 연구 질문은 출발점이며, 선행 연구 확인과 지도교수 검토가 필요합니다.
