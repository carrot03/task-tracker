## Final Project

Branch reviewed: final-project


### What this submission demonstrates
- Existing Task Tracker app still runs inside the intended course scope.
- CI runs the pytest suite on push and/or pull request.
- Docker image builds and runs with /health returning 200.
- AI review, security, and ownership evidence is in docs/.


### How to run locally
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

uvicorn app.main:app --reload --port 8000
```
Frontend and API are both served from http://localhost:8000 (frontend at `/`, API under `/tasks`, `/tags`, `/health`).


### How to run tests
```bash
source venv/bin/activate
python3 -m pytest
```
To run a single file or test: `python3 -m pytest tests/test_tags.py` or `python3 -m pytest tests/test_tags.py::test_name`.


### How to run with Docker
```bash
docker build -t task-tracker .
docker run --rm -p 8000:8000 task-tracker
curl http://localhost:8000/health
```


### Evidence files
- docs/release-evidence.md
- docs/final-ai-review.md
- docs/ai-playbook.md
- docs/module5/*


### AI assistance summary
AI helped draft or review: CI, Docker, docs, security.
I verified the work by: tests , diff review, Docker, /health, manual scan.
One AI suggestion I rejected or corrected: AI suggested building more robust app using authentication and secrets but I rejected that since it is not part of the project scope.
