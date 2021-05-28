from django.urls import path
from .views import (
    SubjectListView,
    SubjectCreateView,
    SubjectDetailView,
    SubjectUpdateView,
    SubjectDeleteView,
    SessionDetailView,
    SessionDataAcousticDetailView,
    SessionDataAcousticUpdateView,
    SessionDataQuestionnaireDetailView,
    SessionDataQuestionnaireCreateView,
    SessionDataQuestionnaireUpdateView,
    SessionDataQuestionnaireUploadView,
    create_session,
    export_acoustic_data,
    export_questionnaire_data
)


# Define the application name
app_name = 'subjects'


# Define the URL patterns
urlpatterns = [
    path('', SubjectListView.as_view(), name='subject_list'),

    # Subjects
    path('create/', SubjectCreateView.as_view(), name='subject_create'),
    path('<str:code>/', SubjectDetailView.as_view(), name='subject_detail'),
    path('<str:code>/update/', SubjectUpdateView.as_view(), name='subject_update'),
    path('<str:code>/delete/', SubjectDeleteView.as_view(), name='subject_delete'),

    # Sessions
    path('<str:code>/create_session/', create_session, name='session_create'),
    path('<str:code>/session/<int:session_number>/detail/', SessionDetailView.as_view(), name='session_detail'),

    # 1. acoustic data
    path('<str:code>/session/<int:session_number>/data_acoustic/export',
         export_acoustic_data,
         name='export_acoustic_data'),
    path('<str:code>/session/<int:session_number>/data_acoustic/',
         SessionDataAcousticDetailView.as_view(),
         name='session_detail_data_acoustic'),
    path('<str:code>/session/<int:session_number>/data_acoustic/upload/',
         SessionDataAcousticUpdateView.as_view(),
         name='session_update_data_acoustic'),

    # 2. questionnaire data
    path('<str:code>/session/<int:session_number>/data_questionnaire/import/',
         SessionDataQuestionnaireUploadView.as_view(),
         name='import_data_questionnaire'),
    path('<str:code>/session/<int:session_number>/data_questionnaire/export',
         export_questionnaire_data,
         name='export_questionnaire_data'),
    path('<str:code>/session/<int:session_number>/data_questionnaire/',
         SessionDataQuestionnaireDetailView.as_view(),
         name='session_detail_data_questionnaire'),
    path('<str:code>/session/<int:session_number>/data_questionnaire/create/',
         SessionDataQuestionnaireCreateView.as_view(),
         name='session_create_data_questionnaire'),
    path('<str:code>/session/<int:session_number>/data_questionnaire/update/',
         SessionDataQuestionnaireUpdateView.as_view(),
         name='session_update_data_questionnaire')
]
