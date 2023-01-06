from django.contrib import admin
from .models import (
    User,
    Organization,
    Subject,
    ExaminationSession,
    DataAcoustic,
    DataActigraphy,
    DataHandwriting,
    DataPsychology,
    DataTCS,
    DataCEI
)


# Register the sites
admin.site.register(User)
admin.site.register(Organization)
admin.site.register(Subject)
admin.site.register(ExaminationSession)
admin.site.register(DataAcoustic)
admin.site.register(DataActigraphy)
admin.site.register(DataHandwriting)
admin.site.register(DataPsychology)
admin.site.register(DataTCS)
admin.site.register(DataCEI)
