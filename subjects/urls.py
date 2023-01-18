from django.urls import path
from .views import (
    SubjectListView,
    SubjectCohortImportView,
    SubjectCreateView,
    SubjectDetailView,
    SubjectUpdateView,
    SubjectDeleteView,
    SessionDetailView,
    SessionDataAcousticDetailView,
    SessionDataAcousticUpdateView,
    SessionDataActigraphyDetailView,
    SessionDataActigraphyUpdateView,
    SessionDataHandwritingDetailView,
    SessionDataHandwritingUpdateView,
    SessionDataPsychologyDetailView,
    SessionDataPsychologyUpdateView,
    SessionDataTCSDetailView,
    SessionDataTCSUpdateView,
    SessionDataCEIDetailView,
    SessionDataCEIUpdateView,
    create_session,
    export_acoustic_data,
    export_actigraphy_data,
    export_handwriting_data,
    export_psychology_data,
    export_tcs_data,
    export_cei_data,
    export_subject_report,
    export_session_report
)


# Define the application name
app_name = 'subjects'


# Define the URL patterns
urlpatterns = [
    path('', SubjectListView.as_view(), name='subject_list'),

    # Subjects
    path('create/', SubjectCreateView.as_view(), name='subject_create'),
    path('import/', SubjectCohortImportView.as_view(), name='subject_import_cohort'),
    path('<str:code>/', SubjectDetailView.as_view(), name='subject_detail'),
    path('<str:code>/update/', SubjectUpdateView.as_view(), name='subject_update'),
    path('<str:code>/delete/', SubjectDeleteView.as_view(), name='subject_delete'),
    path('<str:code>/export_subject_report',
         export_subject_report,
         name='export_subject_report'),

    # Sessions
    path('<str:code>/create_session/', create_session, name='session_create'),
    path('<str:code>/session/<int:session_number>/detail/', SessionDetailView.as_view(), name='session_detail'),
    path('<str:code>/session/<int:session_number>/export_session_report',
         export_session_report,
         name='export_session_report'),

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

    # 2. actigraphy data
    path('<str:code>/session/<int:session_number>/data_actigraphy/export',
         export_actigraphy_data,
         name='export_actigraphy_data'),
    path('<str:code>/session/<int:session_number>/data_actigraphy/',
         SessionDataActigraphyDetailView.as_view(),
         name='session_detail_data_actigraphy'),
    path('<str:code>/session/<int:session_number>/data_actigraphy/upload/',
         SessionDataActigraphyUpdateView.as_view(),
         name='session_update_data_actigraphy'),

    # 3. handwriting data
    path('<str:code>/session/<int:session_number>/data_handwriting/export',
         export_handwriting_data,
         name='export_handwriting_data'),
    path('<str:code>/session/<int:session_number>/data_handwriting/',
         SessionDataHandwritingDetailView.as_view(),
         name='session_detail_data_handwriting'),
    path('<str:code>/session/<int:session_number>/data_handwriting/upload/',
         SessionDataHandwritingUpdateView.as_view(),
         name='session_update_data_handwriting'),

    # 4. psychology data
    path('<str:code>/session/<int:session_number>/data_psychology/export',
         export_psychology_data,
         name='export_psychology_data'),
    path('<str:code>/session/<int:session_number>/data_psychology/',
         SessionDataPsychologyDetailView.as_view(),
         name='session_detail_data_psychology'),
    path('<str:code>/session/<int:session_number>/data_psychology/upload/',
         SessionDataPsychologyUpdateView.as_view(),
         name='session_update_data_psychology'),

    # 5. TCS data
    path('<str:code>/session/<int:session_number>/data_tcs/export',
         export_tcs_data,
         name='export_tcs_data'),
    path('<str:code>/session/<int:session_number>/data_tcs/',
         SessionDataTCSDetailView.as_view(),
         name='session_detail_data_tcs'),
    path('<str:code>/session/<int:session_number>/data_tcs/upload/',
         SessionDataTCSUpdateView.as_view(),
         name='session_update_data_tcs'),

    # 6. CEI data
    path('<str:code>/session/<int:session_number>/data_cei/export',
         export_cei_data,
         name='export_cei_data'),
    path('<str:code>/session/<int:session_number>/data_cei/',
         SessionDataCEIDetailView.as_view(),
         name='session_detail_data_cei'),
    path('<str:code>/session/<int:session_number>/data_cei/upload/',
         SessionDataCEIUpdateView.as_view(),
         name='session_update_data_cei')
]
