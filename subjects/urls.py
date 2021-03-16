from django.urls import path
from .views import (
    SubjectListView,
    SubjectCreateView,
    SubjectDetailView,
    SubjectUpdateView,
    SubjectDeleteView,
    SessionDataAcousticDetailView,
    SessionDataAcousticUpdateView,
    SessionDataQuestionnaireDetailView,
    SessionDataQuestionnaireCreateView,
    SessionDataQuestionnaireUpdateView,
    create_session
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
    # 1. acoustic data
    # 2. questionnaire data

    # 1. acoustic data
    path('<str:code>/create_session/', create_session, name='session_create'),
    path('<str:code>/session/<int:session_number>/data_acoustic/',
         SessionDataAcousticDetailView.as_view(),
         name='session_detail_data_acoustic'),
    path('<str:code>/session/<int:session_number>/data_acoustic/upload/',
         SessionDataAcousticUpdateView.as_view(),
         name='session_update_data_acoustic'),

    # 2. questionnaire data
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
