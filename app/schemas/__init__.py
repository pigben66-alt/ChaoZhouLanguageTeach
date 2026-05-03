from app.schemas.user import (
    UserRegister, UserLogin, TokenResponse, RefreshTokenRequest,
    UserProfileResponse, UserProfileUpdate, UserProgressResponse,
    AbilitySnapshotResponse, ActivityLogResponse,
    SendVerificationCodeRequest, VerifyCodeRequest,
    ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest,
    UserInfoResponse,
)
from app.schemas.learning import (
    KnowledgePointResponse, KnowledgePointDetail, KnowledgePointCreate, KnowledgePointUpdate,
    KnowledgeRelationCreate, VocabularyResponse, VocabularyCreate,
    LessonResponse, LessonCreate, DialogueSceneResponse, DialogueSceneCreate,
    LearningRecordCreate, LearningRecordResponse, KnowledgeMasteryResponse,
    ReviewQueueItem, PaginatedResponse,
)
from app.schemas.agent import (
    AgentSessionCreate, AgentSessionResponse, AgentSessionDetail,
    AgentMessageCreate, AgentMessageResponse, AgentStreamChunk,
)
from app.schemas.analytics import (
    DashboardSummary, HeatmapData, RadarData, TrendData,
    WeaknessItem, ReportResponse,
)
from app.schemas.admin import (
    AdminUserResponse, AdminUserDetail, AdminUserProfileResponse, AdminUserStatsResponse,
    AdminUpdateUserRole, AdminToggleUserStatus,
    AdminContentPublishRequest, AdminContentVersionResponse,
    AdminActivityLogResponse, AdminSystemStatsResponse,
    AdminLearningTrendResponse, AdminContentStatsResponse, AdminDashboardResponse,
)
