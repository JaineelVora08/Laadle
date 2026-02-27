# BEACON — Scaffold Generation Prompt for GitHub Copilot
# INSTRUCTION TO COPILOT: Generate ONLY project structure — folders, files, class definitions,
# method signatures with docstrings, and placeholder return values.
# DO NOT write any business logic, algorithms, or implementation.
# Every method body should contain only: a docstring + `pass` or a dummy return value.

---

## STEP 1 — Create this exact folder and file structure (empty files)

```
beacon/
├── .env.example
├── docker-compose.yml
├── README.md
├── shared/
│   └── schemas.md
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── beacon/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── apps/
│       ├── auth_service/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   └── services/
│       │       └── client.py
│       ├── user_profile_service/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   └── services/
│       │       └── client.py
│       ├── domain_management_service/
│       │   ├── __init__.py
│       │   ├── graph_models.py
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   └── services/
│       │       └── client.py
│       ├── mentor_matching_service/
│       │   ├── __init__.py
│       │   ├── matching_engine.py
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   └── services/
│       │       └── client.py
│       ├── trust_score_service/
│       │   ├── __init__.py
│       │   ├── calculator.py
│       │   ├── serializers.py
│       │   ├── views.py
│       │   └── urls.py
│       ├── query_orchestrator/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── orchestrator.py
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   └── services/
│       │       └── client.py
│       ├── ai_services/
│       │   ├── __init__.py
│       │   ├── embedding_generator.py
│       │   ├── rag_engine.py
│       │   ├── llm_synthesizer.py
│       │   └── conflict_consensus_engine.py
│       └── adaptive_scheduler_service/
│           ├── __init__.py
│           ├── tasks.py
│           ├── views.py
│           └── urls.py
└── frontend/
    ├── package.json
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api/
        │   ├── axiosInstance.js
        │   ├── auth.js
        │   ├── profile.js
        │   ├── domains.js
        │   ├── mentorMatching.js
        │   └── query.js
        ├── store/
        │   ├── authStore.js
        │   └── queryStore.js
        ├── pages/
        │   ├── LoginPage.jsx
        │   ├── RegisterPage.jsx
        │   ├── StudentDashboard.jsx
        │   ├── SeniorDashboard.jsx
        │   ├── ProfilePage.jsx
        │   ├── MentorMatchPage.jsx
        │   ├── QueryPage.jsx
        │   └── SeniorInboxPage.jsx
        └── components/
            ├── Navbar.jsx
            ├── ProfileCard.jsx
            ├── DomainBadge.jsx
            ├── MentorCard.jsx
            ├── QueryCard.jsx
            ├── TrustScoreBadge.jsx
            ├── ProvisionalAnswerBox.jsx
            └── ConflictAlert.jsx
```

---

## STEP 2 — Fill each file with ONLY class/function signatures (no logic)

### backend/apps/auth_service/models.py
```python
from django.contrib.auth.models import AbstractBaseUser
import uuid

class User(AbstractBaseUser):
    """
    Base user model stored in PostgreSQL.
    Shared by both Student and Senior roles.
    Fields: id, name, email, role, availability, trust_score, current_level, active_load
    """
    pass

class Student(models.Model):
    """
    Extended profile for students.
    Fields: user (OneToOne), low_energy_mode, momentum_score
    """
    pass

class Senior(models.Model):
    """
    Extended profile for seniors.
    Fields: user (OneToOne), consistency_score, alignment_score, follow_through_rate
    """
    pass

class Achievement(models.Model):
    """
    Verified achievement uploaded by senior.
    Fields: id, user, title, proof_url, verified, created_at
    """
    pass

class TrustMetrics(models.Model):
    """
    Trust score breakdown for a senior. Used by trust_score_service.
    Fields: senior, student_feedback_score, consistency_score,
            alignment_score, follow_through_rate, achievement_weight
    """
    pass
```

### backend/apps/auth_service/views.py
```python
class RegisterView(APIView):
    """
    POST /api/auth/register/
    Input:  { name, email, password, role, current_level }
    Output: AuthTokenResponse
    Calls:  Nothing
    """
    def post(self, request):
        pass

class LoginView(APIView):
    """
    POST /api/auth/login/
    Input:  { email, password }
    Output: AuthTokenResponse { access, refresh, user_id, role }
    Calls:  Nothing
    """
    def post(self, request):
        pass

class TokenRefreshView(APIView):
    """
    POST /api/auth/token/refresh/
    Input:  { refresh }
    Output: { access }
    """
    def post(self, request):
        pass

class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists the refresh token.
    """
    def post(self, request):
        pass
```

### backend/apps/user_profile_service/views.py
```python
class UserProfileView(APIView):
    """
    GET  /api/profile/<user_id>/
    Output: UserProfileResponse
    Calls:  Nothing
    """
    def get(self, request, user_id):
        pass

class UpdateProfileView(APIView):
    """
    PUT /api/profile/<user_id>/update/
    Input:  Partial UserProfileResponse fields
    Output: Updated UserProfileResponse
    """
    def put(self, request, user_id):
        pass

class AchievementView(APIView):
    """
    POST /api/profile/<user_id>/achievements/
    Input:  { title, proof_url }
    Output: { id, title, proof_url, verified: false }
    Calls:  trust_score_service — POST /internal/trust-score/recalculate/
    """
    def post(self, request, user_id):
        pass

    def get(self, request, user_id):
        pass
```

### backend/apps/auth_service/services/client.py
```python
class InternalUserClient:
    """
    Used by other modules (Module 2, 3) to fetch user data internally.
    Calls Module 1 (auth/user_profile_service) via X-Internal-Secret header.
    """

    def get_user(self, user_id: str) -> dict:
        """
        GET /internal/users/<user_id>/
        Returns: UserProfileResponse dict
        """
        pass

    def increment_senior_load(self, senior_id: str) -> dict:
        """
        PATCH /internal/users/<senior_id>/increment-load/
        Returns: { senior_id, new_active_load }
        """
        pass
```

---

### backend/apps/domain_management_service/graph_models.py
```python
from neomodel import StructuredNode, StructuredRel

class UserNode(StructuredNode):
    """
    Neo4j node mirroring PostgreSQL User.
    Properties: uid, role, availability, trust_score, current_level, active_load
    """
    pass

class DomainNode(StructuredNode):
    """
    Neo4j node representing a domain/area of interest.
    Properties: uid, name, type, embedding_ref (Pinecone ID), popularity_score
    """
    pass

class InterestedIn(StructuredRel):
    """
    Relationship: Student → DomainNode
    Properties: priority (int), current_level (str)
    """
    pass

class ExperiencedIn(StructuredRel):
    """
    Relationship: Senior → DomainNode
    Properties: experience_level (str), years_of_involvement (int)
    """
    pass

class MentoredBy(StructuredRel):
    """
    Relationship: Student → Senior
    Properties: start_date, status (ACTIVE | CLOSED)
    """
    pass

class ConnectedWith(StructuredRel):
    """
    Peer relationship: Student ↔ Student
    Properties: since (date)
    """
    pass
```

### backend/apps/domain_management_service/views.py
```python
class AddDomainView(APIView):
    """
    POST /api/domains/add/
    Input:  { user_id, raw_interest_text }
    Output: DomainLinkResponse
    Calls:  ai_services — POST /internal/embeddings/generate/
            Neo4j — cosine similarity check, create/link DomainNode
    """
    def post(self, request):
        pass

class UserDomainsView(APIView):
    """
    GET /api/domains/user/<user_id>/
    Output: list of DomainLinkResponse
    """
    def get(self, request, user_id):
        pass

class AllDomainsView(APIView):
    """
    GET /api/domains/all/
    Output: list of all DomainNode records
    """
    def get(self, request):
        pass
```

### backend/apps/mentor_matching_service/matching_engine.py
```python
class MentorMatchingEngine:
    """
    Handles all graph traversal logic for mentor and peer matching.
    All Neo4j traversal queries go here (no logic in views).
    """

    def find_mentors(self, student_id: str, domain_id: str, priority: int) -> list:
        """
        2-hop traversal: Student → INTERESTED_IN → DomainNode → EXPERIENCED_IN → Senior
        Filters: availability=True, active_load < threshold, level compatibility, trust_score desc
        Returns: list of matched senior dicts (MentorMatchResponse format)
        """
        pass

    def find_peers(self, student_id: str, domain_id: str) -> list:
        """
        Traversal: Student → DomainNode ← Student (same domain, similar level)
        Filters: level similarity, availability overlap, priority alignment
        Returns: list of matched student dicts
        """
        pass

    def create_mentorship_edge(self, student_id: str, senior_id: str, domain_id: str) -> dict:
        """
        Creates MENTORED_BY edge in Neo4j.
        Calls Module 1: PATCH /internal/users/<senior_id>/increment-load/
        Returns: { mentorship_id, status: "PENDING" }
        """
        pass
```

### backend/apps/mentor_matching_service/views.py
```python
class FindMentorView(APIView):
    """
    POST /api/mentor-matching/find/
    Input:  MentorMatchRequest { student_id, domain_id, priority }
    Output: MentorMatchResponse
    Calls:  MentorMatchingEngine.find_mentors()
    """
    def post(self, request):
        pass

class ConnectMentorView(APIView):
    """
    POST /api/mentor-matching/connect/
    Input:  { student_id, senior_id, domain_id }
    Output: { mentorship_id, status }
    Calls:  MentorMatchingEngine.create_mentorship_edge()
    """
    def post(self, request):
        pass

class FindPeerView(APIView):
    """
    POST /api/peer-matching/find/
    Input:  { student_id, domain_id }
    Output: PeerMatchResponse
    Calls:  MentorMatchingEngine.find_peers()
    """
    def post(self, request):
        pass
```

### backend/apps/trust_score_service/calculator.py
```python
class TrustScoreCalculator:
    """
    Computes and updates trust scores for seniors.
    Reads from TrustMetrics (PostgreSQL), writes to both PostgreSQL and Neo4j.
    Formula weights: feedback=0.25, follow_through=0.25, consistency=0.20,
                     alignment=0.15, achievement=0.15
    """

    def compute(self, senior_id: str) -> float:
        """
        Fetches TrustMetrics for senior_id, applies weighted formula.
        Writes result back to User.trust_score (PostgreSQL) and UserNode.trust_score (Neo4j).
        Returns: new trust score float
        """
        pass

    def update_feedback(self, senior_id: str, feedback_data: dict) -> dict:
        """
        Updates individual TrustMetrics fields after a query is resolved.
        Triggers compute() after update.
        Returns: { senior_id, new_trust_score }
        """
        pass
```

### backend/apps/trust_score_service/views.py
```python
class RecalculateTrustView(APIView):
    """
    POST /internal/trust-score/recalculate/
    Input:  { senior_id }
    Output: { senior_id, new_trust_score }
    Calls:  TrustScoreCalculator.compute()
    Called by: Module 1 (after achievement upload)
    """
    def post(self, request):
        pass

class UpdateFeedbackView(APIView):
    """
    POST /internal/trust-score/update-feedback/
    Input:  TrustUpdateRequest
    Output: { senior_id, new_trust_score }
    Calls:  TrustScoreCalculator.update_feedback()
    Called by: Module 3 (after query resolution)
    """
    def post(self, request):
        pass
```

---

### backend/apps/query_orchestrator/models.py
```python
class Query(models.Model):
    """
    Stores a student query and its resolution state.
    Fields: id (UUID), student_id, domain_id, content, timestamp,
            is_resolved, rag_response, final_response, related_query_ids
    """
    pass

class ConflictRecord(models.Model):
    """
    Stores detected conflicts between senior advice items.
    Fields: id, query_id, new_advice, conflicting_advice, flagged_at
    """
    pass
```

### backend/apps/query_orchestrator/orchestrator.py
```python
class QueryOrchestrator:
    """
    Central coordinator for query processing pipeline.
    Connects: EmbeddingGenerator → RAGEngine → MentorMatching → SeniorInbox → ConflictEngine → LLMSynthesizer
    """

    def handle_new_query(self, student_id: str, domain_id: str, content: str) -> dict:
        """
        Full pipeline for a new student query:
        1. Generate embedding (ai_services.EmbeddingGenerator)
        2. Retrieve similar cases (ai_services.RAGEngine)
        3. Generate provisional LLM answer (ai_services.RAGEngine)
        4. Save Query to PostgreSQL
        5. Find matched seniors (mentor_matching_service)
        6. Dispatch query to senior inboxes
        7. Generate predictive follow-up questions (ai_services.LLMSynthesizer)
        Returns: QuerySubmitResponse
        """
        pass

    def handle_senior_response(self, senior_id: str, query_id: str, advice_content: str, answered_followups: list) -> dict:
        """
        Pipeline when a senior submits a response:
        1. Run conflict detection (ai_services.ConflictConsensusEngine)
        2. Aggregate weighted advice (ai_services.LLMSynthesizer)
        3. Update Query.is_resolved = True, store final_response
        4. Update trust score (trust_score_service)
        Returns: FinalAdviceResponse
        """
        pass
```

### backend/apps/query_orchestrator/views.py
```python
class SubmitQueryView(APIView):
    """
    POST /api/query/submit/
    Input:  QuerySubmitRequest { student_id, domain_id, content }
    Output: QuerySubmitResponse
    Calls:  QueryOrchestrator.handle_new_query()
    """
    def post(self, request):
        pass

class QueryStatusView(APIView):
    """
    GET /api/query/<query_id>/status/
    Output: QueryStatusResponse { query_id, status, provisional_answer, final_answer }
    """
    def get(self, request, query_id):
        pass

class SeniorResponseView(APIView):
    """
    POST /api/query/<query_id>/senior-response/
    Input:  SeniorResponseRequest
    Output: FinalAdviceResponse
    Calls:  QueryOrchestrator.handle_senior_response()
    """
    def post(self, request, query_id):
        pass

class SeniorPendingQueriesView(APIView):
    """
    GET /api/query/pending/senior/<senior_id>/
    Output: list of pending QuerySubmitResponse objects for this senior
    """
    def get(self, request, senior_id):
        pass
```

---

### backend/apps/ai_services/embedding_generator.py
```python
class EmbeddingGenerator:
    """
    Wraps external embedding API (e.g. OpenAI text-embedding-ada-002).
    Stores/retrieves vectors in Pinecone index: "beacon-domains"
    """

    def generate(self, text: str) -> list:
        """
        Calls embedding API with text.
        Returns: embedding vector list[float] (length 1536)
        """
        pass

    def store(self, vector_id: str, embedding: list, metadata: dict) -> bool:
        """
        Upserts embedding into Pinecone.
        metadata keys: domain_name, type, domain_id
        Returns: True if successful
        """
        pass

    def query_similar(self, embedding: list, top_k: int = 5, filter: dict = None) -> list:
        """
        Queries Pinecone for top_k similar vectors.
        Returns: list of { id, score, metadata }
        """
        pass
```

### backend/apps/ai_services/rag_engine.py
```python
class RAGEngine:
    """
    Retrieval-Augmented Generation engine.
    Retrieves similar past Q&A pairs from Pinecone, feeds to LLM for provisional answer.
    """

    def retrieve_similar_cases(self, query_embedding: list, domain_id: str) -> list:
        """
        Queries Pinecone filtered by domain_id.
        Returns: list of { query_text, advice_text, trust_score, senior_id }
        """
        pass

    def generate_provisional_response(self, student_query: str, similar_cases: list, high_trust_advice: list) -> str:
        """
        Builds prompt from retrieved context + high-trust advice.
        Calls LLM API.
        Returns: provisional answer string (includes disclaimer)
        """
        pass
```

### backend/apps/ai_services/llm_synthesizer.py
```python
class LLMSynthesizer:
    """
    Weighted aggregation of multiple senior advice items.
    Weight formula: trust_score × similarity_score
    """

    def compute_weight(self, trust_score: float, similarity_score: float) -> float:
        """
        Returns: weight float
        """
        pass

    def synthesize(self, student_query: str, advice_list: list) -> dict:
        """
        advice_list items: { content, senior_id, trust_score, similarity_score }
        Builds LLM prompt, calls API, extracts agreements/disagreements.
        Returns: SynthesizedAdviceResponse { final_answer, agreements, disagreements }
        """
        pass

    def generate_followup_questions(self, query_content: str, domain_id: str) -> list:
        """
        Analyzes historical interaction patterns, generates likely follow-up questions.
        Returns: list of question strings (max 3)
        """
        pass
```

### backend/apps/ai_services/conflict_consensus_engine.py
```python
class ConflictConsensusEngine:
    """
    Detects when new senior advice contradicts historical trends.
    Uses embedding cosine similarity to measure deviation.
    Threshold for anomaly: avg_similarity < 0.3
    """

    def detect_anomaly(self, new_advice: str, historical_advice: list) -> bool:
        """
        Embeds new_advice and each item in historical_advice.
        Computes average cosine similarity.
        Returns: True if anomaly detected (conflict), False otherwise
        """
        pass

    def flag_conflict(self, query_id: str, new_advice: str, conflicting_advice: str) -> dict:
        """
        Stores ConflictRecord in PostgreSQL.
        Returns: ConflictRecord dict { id, query_id, new_advice, conflicting_advice, flagged_at }
        """
        pass
```

### backend/apps/adaptive_scheduler_service/tasks.py
```python
from celery import shared_task

@shared_task
def redistribute_tasks(senior_id: str):
    """
    Celery task: triggered when senior.active_load exceeds threshold.
    Finds next available senior via mentor_matching_service.
    Reassigns pending queries from overloaded senior.
    """
    pass

@shared_task
def broadcast_cold_start(query_id: str, domain_id: str):
    """
    Celery task: triggered when no mentor match found.
    Sends notification to ALL available seniors for the given domain.
    """
    pass
```

---

### frontend/src/api/axiosInstance.js
```javascript
/**
 * Base axios instance.
 * - baseURL: process.env.REACT_APP_API_BASE_URL
 * - Attaches Authorization: Bearer <token> from authStore on every request
 * - Auto-refreshes token on 401 using POST /api/auth/token/refresh/
 */
const axiosInstance = null; // TODO: implement
export default axiosInstance;
```

### frontend/src/api/auth.js
```javascript
/**
 * Calls Module 1 auth endpoints.
 */
export const register = async (payload) => { /* POST /api/auth/register/ */ };
export const login    = async (payload) => { /* POST /api/auth/login/ */ };
export const logout   = async ()        => { /* POST /api/auth/logout/ */ };
export const refresh  = async (token)   => { /* POST /api/auth/token/refresh/ */ };
```

### frontend/src/api/domains.js
```javascript
/**
 * Calls Module 2 domain management endpoints.
 */
export const addDomain    = async (payload) => { /* POST /api/domains/add/ */ };
export const getUserDomains = async (userId) => { /* GET /api/domains/user/<userId>/ */ };
export const getAllDomains = async ()        => { /* GET /api/domains/all/ */ };
```

### frontend/src/api/mentorMatching.js
```javascript
/**
 * Calls Module 2 mentor matching endpoints.
 */
export const findMentors  = async (payload) => { /* POST /api/mentor-matching/find/ */ };
export const connectMentor = async (payload) => { /* POST /api/mentor-matching/connect/ */ };
export const findPeers    = async (payload) => { /* POST /api/peer-matching/find/ */ };
```

### frontend/src/api/query.js
```javascript
/**
 * Calls Module 3 query orchestrator endpoints.
 */
export const submitQuery         = async (payload)          => { /* POST /api/query/submit/ */ };
export const getQueryStatus      = async (queryId)          => { /* GET /api/query/<id>/status/ */ };
export const submitSeniorResponse = async (queryId, payload) => { /* POST /api/query/<id>/senior-response/ */ };
export const getSeniorPending    = async (seniorId)         => { /* GET /api/query/pending/senior/<id>/ */ };
```

### frontend/src/store/authStore.js
```javascript
/**
 * Zustand store for auth state.
 * State: { user: UserProfileResponse | null, token: string | null }
 * Actions: login(credentials), logout(), setUser(user)
 */
export const useAuthStore = () => {}; // TODO: implement with zustand create()
```

### frontend/src/store/queryStore.js
```javascript
/**
 * Zustand store for query state.
 * State: { queries: QuerySubmitResponse[], activeQuery: QuerySubmitResponse | null }
 * Actions: addQuery(q), setActiveQuery(q), resolveQuery(queryId, finalResponse)
 */
export const useQueryStore = () => {}; // TODO: implement with zustand create()
```

### frontend pages — each file exports a default React component (empty shell):
```
LoginPage.jsx        → renders login form, calls api/auth.login(), redirects by role
RegisterPage.jsx     → renders register form, calls api/auth.register()
StudentDashboard.jsx → shows domains, mentor matches, query history
SeniorDashboard.jsx  → shows stats, quick link to inbox
ProfilePage.jsx      → shows UserProfileResponse, achievement list
MentorMatchPage.jsx  → calls findMentors(), renders MentorCard list
QueryPage.jsx        → calls submitQuery(), shows ProvisionalAnswerBox, polls status
SeniorInboxPage.jsx  → calls getSeniorPending(), renders QueryCard list, response form
```

### frontend components — each file exports a default React component (empty shell):
```
Navbar.jsx              → props: { user: UserProfileResponse }
ProfileCard.jsx         → props: { user: UserProfileResponse }
DomainBadge.jsx         → props: { domain: DomainLinkResponse }
MentorCard.jsx          → props: { mentor: MentorMatchResponse item }
QueryCard.jsx           → props: { query: QuerySubmitResponse | FinalAdviceResponse }
TrustScoreBadge.jsx     → props: { score: float }
ProvisionalAnswerBox.jsx→ props: { answer: string, disclaimer: string, followups: string[] }
ConflictAlert.jsx       → props: { detected: bool, details: string | null }
```

---

## STEP 3 — Generate these config files with real content

### requirements.txt
```
django==4.2
djangorestframework==3.15
djangorestframework-simplejwt==5.3
django-cors-headers==4.3
psycopg2-binary==2.9
neomodel==5.2
pinecone-client==3.0
openai==1.0
celery==5.3
redis==5.0
python-dotenv==1.0
```

### docker-compose.yml
```yaml
version: "3.9"
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: beacon_db
      POSTGRES_USER: beacon_user
      POSTGRES_PASSWORD: beacon_pass
    ports: ["5432:5432"]

  neo4j:
    image: neo4j:5
    environment:
      NEO4J_AUTH: neo4j/testpassword
      NEO4JLABS_PLUGINS: '["apoc"]'
    ports: ["7474:7474", "7687:7687"]

  redis:
    image: redis:7
    ports: ["6379:6379"]

  backend:
    build: ./backend
    command: python manage.py runserver 0.0.0.0:8000
    env_file: .env
    ports: ["8000:8000"]
    depends_on: [postgres, neo4j, redis]

  celery:
    build: ./backend
    command: celery -A beacon worker --loglevel=info
    env_file: .env
    depends_on: [backend, redis]

  frontend:
    build: ./frontend
    command: npm run dev
    ports: ["3000:3000"]
    depends_on: [backend]
```

### .env.example
```
POSTGRES_DB=beacon_db
POSTGRES_USER=beacon_user
POSTGRES_PASSWORD=beacon_pass
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=testpassword
PINECONE_API_KEY=
PINECONE_ENV=
PINECONE_INDEX=beacon-domains
OPENAI_API_KEY=
SECRET_KEY=changeme
DEBUG=True
INTERNAL_SECRET=internal_shared_secret
REDIS_URL=redis://redis:6379/0
REACT_APP_API_BASE_URL=http://localhost:8000
```

---

## STEP 4 — Generate shared/schemas.md with all JSON contracts

List every request/response shape used across all 4 modules.
These are the contracts — all 4 devs must match these exactly when implementing.

```
AuthTokenResponse, UserProfileResponse,
DomainLinkResponse, MentorMatchRequest, MentorMatchResponse, PeerMatchResponse,
TrustUpdateRequest, QuerySubmitRequest, QuerySubmitResponse,
SeniorResponseRequest, FinalAdviceResponse, QueryStatusResponse
```

For each, show the exact JSON shape with field names and types (no sample values needed).