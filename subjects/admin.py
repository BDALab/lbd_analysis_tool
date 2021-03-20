from django.contrib import admin
from .models import (
    User,
    Organization,
    Subject,
    ExaminationSession,
    DataAcoustic,
    DataQuestionnaire
)


# Register the sites
admin.site.register(User)
admin.site.register(Organization)
admin.site.register(Subject)
admin.site.register(ExaminationSession)
admin.site.register(DataAcoustic)
admin.site.register(DataQuestionnaire)
