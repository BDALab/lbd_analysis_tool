from datetime import datetime
from django.core.management.base import BaseCommand
from subjects.models import User, Subject, Organization
from reporter.subject import create_report


class FakeRequest:
    def __init__(self, user_record):
        self.user = user_record


# Set the organization to get the reports for
organization = Organization.objects.get(name='fnusa')

# Set the user to get the reports for
user = User.objects.get(username='zolo')

# Fake the `request` object
request = FakeRequest(user)

# Set the debugging mode
debug = True


class Command(BaseCommand):
    help = 'Creates subject reports'

    def handle(self, *args, **kwargs):
        """Handles the command: creates normative data from healthy subjects"""

        t1 = datetime.now()
        print(f'Start: {t1}')

        # Get the subjects
        subjects = Subject.get_subjects(organization=organization)

        # Create the reports
        for i, subject in enumerate(subjects, 1):
            print(f'[{i}/{subjects.count()}] {subject.code}')
            create_report(request, subject)

        t2 = datetime.now()
        print(f'End: {str(t2)}')
        print(f'Time difference: {str(t2 - t1)}')
