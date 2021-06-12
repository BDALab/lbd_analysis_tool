import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import reverse, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.views import generic
from django.urls import reverse_lazy
from .models import Subject, ExaminationSession, DataAcoustic, DataQuestionnaire
from .forms import SubjectModelForm, CustomUserCreationForm, DataAcousticForm, DataQuestionnaireForm, UploadFileForm
from predictor.client import predict_lbd_probability


# Get the module-level logger instance
logger = logging.getLogger(__name__)


class SigninView(LoginView):
    """Class implementing signin view"""

    # Define the template name
    template_name = 'registration/login.html'

    # Define the authenticated user redirection
    redirect_authenticated_user = True

    def get_success_url(self):
        """Returns the success URL"""
        return reverse_lazy('subjects:subject_list')


class SignupView(generic.CreateView):
    """Class implementing signup view"""

    # Define the template name
    template_name = 'registration/signup.html'

    # Define the form class
    form_class = CustomUserCreationForm

    def get(self, *args, **kwargs):
        """Authenticated user hook: gets redirected to a list of subjects"""

        # If a user is already authenticated, redirect him/her to the list of subjects
        if self.request.user.is_authenticated:
            return redirect('subjects:subject_list')

        # Otherwise, proceed as usual
        return super(SignupView, self).get(*args, **kwargs)

    def get_success_url(self):
        """Returns the success URL"""
        return reverse_lazy('login')


class LandingPageView(generic.TemplateView):
    """Class implementing landing page view"""

    # Define the template name
    template_name = 'landing_page.html'


class SubjectListView(LoginRequiredMixin, generic.ListView):
    """Class implementing subject list view"""

    # Define the template name
    template_name = 'subjects/subject_list.html'

    # Define the context object name
    context_object_name = 'subjects'

    # Define the pagination
    paginate_by = 5

    def get_queryset(self):
        """Gets the queryset to be returned"""

        # Get the non-filtered queryset (no search applied over the subjects)
        if not self.request.GET.get('q'):
            return Subject.get_subjects(self.request.user.organization, order_by=('code',))

        # Get the filtered queryset
        else:
            return Subject.get_subjects_filtered(
                organization=self.request.user.organization,
                search_phrase=self.request.GET.get('q'),
                order_by=('code',))

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SubjectListView, self).get_context_data(**kwargs)

        # Add the examination session
        if self.request.GET.get('q'):
            context.update({'q': self.request.GET.get('q')})

        # Return the updated context
        return context


class SubjectDetailView(LoginRequiredMixin, generic.DetailView):
    """Class implementing subject detail view"""

    # Define the template name
    template_name = 'subjects/subject_detail.html'

    # Define the slug attributes to enable filtering based on the specified field
    slug_field = 'code'
    slug_url_kwarg = 'code'

    # Define the context object name
    context_object_name = 'subject'

    def get_queryset(self):
        """Gets the queryset to be returned"""
        return Subject.get_subjects(self.request.user.organization)

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SubjectDetailView, self).get_context_data(**kwargs)

        # Add the examination session
        sessions = ExaminationSession.get_sessions(subject=self.object.id, order_by=('session_number',))
        context.update({'examination_sessions': sessions})

        if sessions:

            # TODO: update data and model when we have the real data
            # Prepare the data and the model for the prediction
            data = [[1, 2], [3, 4]]
            model = 'dummy_predictor'

            # TODO: log the internal server errors
            # Prepare the predictor API client
            predicted = predict_lbd_probability(self.request.user, data, model)

            # Add the prediction
            if predicted:
                context.update({'prediction': predicted})

        # Return the updated context
        return context


class SubjectCreateView(LoginRequiredMixin, generic.CreateView):
    """Class implementing subject create view"""

    # Define the template name
    template_name = 'subjects/subject_create.html'

    # Define the slug attributes to enable filtering based on the specified field
    slug_field = 'code'
    slug_url_kwarg = 'code'

    # Define the form class
    form_class = SubjectModelForm

    def form_valid(self, form):
        """Form valid hook: sets subject's organization same as the user"""

        # Save the form without database update
        subject = form.save(commit=False)

        # Update the organization and update the database records
        subject = self.set_organization(subject)
        subject.save()

        # Return the updated data
        return super(SubjectCreateView, self).form_valid(form)

    def get_success_url(self):
        """Returns the success URL"""
        return reverse_lazy('subjects:subject_detail', kwargs={'code': self.object.code})

    def set_organization(self, subject):
        """Sets the organization for a given subject after creating"""

        # Update the organization
        subject.organization = self.request.user.organization

        # Return the updated subject
        return subject


class SubjectUpdateView(LoginRequiredMixin, generic.UpdateView):
    """Class implementing subject update view"""

    # Define the template name
    template_name = 'subjects/subject_update.html'

    # Define the slug attributes to enable filtering based on the specified field
    slug_field = 'code'
    slug_url_kwarg = 'code'

    # Define the form class
    form_class = SubjectModelForm

    def get_queryset(self):
        """Gets the queryset to be returned"""
        return Subject.get_subjects(self.request.user.organization)

    def get_success_url(self):
        """Returns the success URL"""
        return reverse_lazy('subjects:subject_detail', kwargs={'code': self.object.code})


class SubjectDeleteView(LoginRequiredMixin, generic.DeleteView):
    """Class implementing subject delete view"""

    # Define the template name
    template_name = 'subjects/subject_delete.html'

    # Define the slug attributes to enable filtering based on the specified field
    slug_field = 'code'
    slug_url_kwarg = 'code'

    def get_queryset(self):
        """Gets the queryset to be returned"""
        return Subject.get_subjects(self.request.user.organization)

    def get_success_url(self):
        """Returns the success URL"""
        return reverse_lazy('subjects:subject_list')


@login_required(login_url='/login')
def create_session(request, code):
    """
    Creates a new examination session for a requested subject.

    :param request: HTTP request
    :type request: Request
    :param code: code of the subject
    :type code: str
    :return: redirected HTTP response to the subject detail view
    :rtype: HttpResponseRedirect
    """

    # Fetch the user or raise 404 error if non-existent
    subject = Subject.get_subject(code=code)

    # Get the last session
    last_session = ExaminationSession.get_sessions(subject=subject).last()

    # Get the new session number
    session_number = last_session.session_number + 1 if last_session else 1

    # Create and save a new session
    session = ExaminationSession(subject=subject, session_number=session_number)
    session.save()

    # Redirect back to the subject detail view
    return HttpResponseRedirect(
        reverse(
            'subjects:session_detail',
            kwargs={'code': subject.code, 'session_number': session_number}
        )
    )


class SessionDetailView(LoginRequiredMixin, generic.DetailView):
    """Class implementing session: session data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail.html'

    # Define the slug attributes to enable filtering based on the specified field
    slug_field = 'session_number'
    slug_url_kwarg = 'session_number'

    # Define the context object name
    context_object_name = 'session'

    # Define the examination session parts (examinations/questionnaires, etc.)
    # 1. examination name
    # 2. path name
    # 3. model
    examinations = [
        ('acoustic', 'session_detail_data_acoustic', DataAcoustic),
        ('questionnaire', 'session_detail_data_questionnaire', DataQuestionnaire)
    ]

    def get_queryset(self):
        """Gets the queryset to be returned"""
        return ExaminationSession.get_sessions(subject=Subject.get_subject(code=self.kwargs.get('code')))

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SessionDetailView, self).get_context_data(**kwargs)

        # Get the examinations for the given session
        examinations = [
            {'name': name, 'path': path, 'data': model.get_data(examination_session=self.object.id)}
            for name, path, model in self.examinations
        ]

        # Add the examinations
        context.update({'examinations': examinations})

        # Return the updated context
        return context


class SessionDataAcousticDetailView(LoginRequiredMixin, generic.DetailView):
    """Class implementing session: acoustic data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail_data_acoustic.html'

    # Define the slug attributes to enable filtering based on the specified field
    slug_field = 'session_number'
    slug_url_kwarg = 'session_number'

    # Define the context object name
    context_object_name = 'session'

    # Define the pagination
    paginate_by = 5

    def get_queryset(self):
        """Gets the queryset to be returned"""
        return ExaminationSession.get_sessions(subject=Subject.get_subject(code=self.kwargs.get('code')))

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SessionDataAcousticDetailView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        acoustic_data = DataAcoustic.get_data(examination_session=self.object.id)

        # Prepare the acoustic data
        if acoustic_data:
            acoustic_data = DataAcoustic.prepare_presentable(record=acoustic_data)

        # Add the acoustic data
        context.update({'acoustic_data': acoustic_data})

        # Filter the acoustic data and add the filtration into the context
        if acoustic_data and self.request.GET.get('q'):
            acoustic_data = [data for data in acoustic_data if self.request.GET.get('q') in data.get('label')]
            context.update({'q': self.request.GET.get('q')})

        # Add the pagination if there are any loaded acoustic data
        if acoustic_data:
            paginator = Paginator(acoustic_data, self.paginate_by)
            goto_page = self.request.GET.get('page')

            context.update({
                'is_paginated': True if acoustic_data and len(acoustic_data) > self.paginate_by else False,
                'paginator': paginator,
                'page_number': self.request.GET.get('page'),
                'page_obj': paginator.get_page(goto_page)
            })

        # Return the updated context
        return context


class SessionDataAcousticUpdateView(LoginRequiredMixin, generic.CreateView):
    """Class implementing session: acoustic data update view"""

    # Define the template name
    template_name = 'subjects/session_update_data_acoustic.html'

    # Define the model name
    model = DataAcoustic

    # Define the form class
    form_class = DataAcousticForm

    def form_valid(self, form):
        """Form valid hook: sets data's session after created"""

        # Save the form without database update
        data = form.save(commit=False)

        # Update the session and update the database records
        data = self.set_session(data)
        data.save()

        # Return the updated data
        return super(SessionDataAcousticUpdateView, self).form_valid(form)

    def set_session(self, data):
        """Sets the session for a given data after creating"""

        # Update the examination session
        data.examination_session = ExaminationSession.get_session(
            subject_code=self.kwargs.get('code'),
            session_number=self.kwargs.get('session_number'))

        # Return the updated data
        return data

    def get_success_url(self):
        """Returns the success URL"""
        return reverse_lazy(
            'subjects:session_detail_data_acoustic',
            kwargs={'code': self.kwargs.get('code'), 'session_number': self.kwargs.get('session_number')})

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SessionDataAcousticUpdateView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        session = ExaminationSession.get_session(
            subject_code=self.kwargs.get('code'),
            session_number=self.kwargs.get('session_number'))

        # Add the examination session
        context.update({'session': session})

        # Return the updated context
        return context


class SessionDataQuestionnaireDetailView(LoginRequiredMixin, generic.DetailView):
    """Class implementing session: questionnaire data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail_data_questionnaire.html'

    # Define the slug attributes to enable filtering based on the specified field
    slug_field = 'session_number'
    slug_url_kwarg = 'session_number'

    # Define the context object name
    context_object_name = 'session'

    # Define the pagination
    paginate_by = 5

    def get_queryset(self):
        """Gets the queryset to be returned"""
        return ExaminationSession.get_sessions(subject=Subject.get_subject(code=self.kwargs.get('code')))

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SessionDataQuestionnaireDetailView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        questionnaire_data = DataQuestionnaire.get_data(examination_session=self.object.id)

        # Prepare the questionnaire data
        if questionnaire_data:
            questionnaire_data = DataQuestionnaire.prepare_presentable(record=questionnaire_data, use_questions=True)

        # Add the questionnaire data
        context.update({'questionnaire_data': questionnaire_data})

        # Add the pagination if there are any loaded questionnaire data
        if questionnaire_data:
            paginator = Paginator(questionnaire_data, self.paginate_by)
            goto_page = self.request.GET.get('page')

            context.update({
                'is_paginated': True if questionnaire_data and len(questionnaire_data) > self.paginate_by else False,
                'paginator': paginator,
                'page_number': self.request.GET.get('page'),
                'page_obj': paginator.get_page(goto_page)
            })

        # Return the updated context
        return context


class SessionDataQuestionnaireCreateView(LoginRequiredMixin, generic.CreateView):
    """Class implementing session: questionnaire data create view"""

    # Define the template name
    template_name = 'subjects/session_create_data_questionnaire.html'

    # Define the model name
    model = DataQuestionnaire

    # Define the form class
    form_class = DataQuestionnaireForm

    def form_valid(self, form):
        """Form valid hook: sets data's session after created"""

        # Save the form without database update
        data = form.save(commit=False)

        # Update the session and update the database records
        data = self.set_session(data)
        data.save()

        # Return the updated data
        return super(SessionDataQuestionnaireCreateView, self).form_valid(form)

    def get_success_url(self):
        """Returns the success URL"""
        return reverse_lazy(
            'subjects:session_detail_data_questionnaire',
            kwargs={'code': self.kwargs.get('code'), 'session_number': self.kwargs.get('session_number')})

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SessionDataQuestionnaireCreateView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        session = ExaminationSession.get_session(
            subject_code=self.kwargs.get('code'),
            session_number=self.kwargs.get('session_number'))

        # Add the examination session
        context.update({'session': session})

        # Return the updated context
        return context

    def set_session(self, data):
        """Sets the session for a given data after creating"""

        # Update the examination session
        data.examination_session = ExaminationSession.get_session(
            subject_code=self.kwargs.get('code'),
            session_number=self.kwargs.get('session_number'))

        # Return the updated data
        return data


class SessionDataQuestionnaireUpdateView(LoginRequiredMixin, generic.UpdateView):
    """Class implementing session: questionnaire data update view"""

    # Define the template name
    template_name = 'subjects/session_update_data_questionnaire.html'

    # Define the model
    model = DataQuestionnaire

    # Define the form class
    form_class = DataQuestionnaireForm

    def get_object(self, queryset=None):
        """Gets the object to be returned"""

        # Get the examination session for given URL parameters
        session = ExaminationSession.get_session(
            subject_code=self.kwargs.get('code'),
            session_number=self.kwargs.get('session_number'))

        # Return the object
        return DataQuestionnaire.get_data(examination_session=session)

    def get_success_url(self):
        """Returns the success URL"""
        return reverse_lazy(
            'subjects:session_detail_data_questionnaire',
            kwargs={'code': self.kwargs.get('code'), 'session_number': self.kwargs.get('session_number')})


class SessionDataQuestionnaireUploadView(LoginRequiredMixin, generic.FormView):
    """Class implementing session: questionnaire data upload view"""

    # Define the template name
    template_name = 'subjects/session_upload_data_questionnaire.html'

    # Define the model name
    model = DataQuestionnaire

    # Define the form class
    form_class = UploadFileForm

    def form_valid(self, form):
        """Form valid hook: sets data's session after created"""

        # Get the data
        data = DataQuestionnaire.get_data(
            subject_code=self.kwargs.get('code'),
            session_number=self.kwargs.get('session_number'))

        # If the questionnaire does not exist yet, create it from the form data
        if not data:

            # Get the examination session
            session = ExaminationSession.get_session(
                subject_code=self.kwargs.get('code'),
                session_number=self.kwargs.get('session_number'))

            # Create the questionnaire data
            DataQuestionnaire.create_from_form(form, examination_session=session)

        # Otherwise, update the questionnaire from the form
        else:
            DataQuestionnaire.update_from_form(form, data)

        # Return the updated data
        return super(SessionDataQuestionnaireUploadView, self).form_valid(form)

    def set_session(self, data):
        """Sets the session for a given data after creating"""

        # Update the examination session
        data.examination_session = ExaminationSession.get_session(
            subject_code=self.kwargs.get('code'),
            session_number=self.kwargs.get('session_number'))

        # Return the updated data
        return data

    def get_success_url(self):
        """Returns the success URL"""
        return reverse_lazy(
            'subjects:session_detail_data_questionnaire',
            kwargs={'code': self.kwargs.get('code'), 'session_number': self.kwargs.get('session_number')})

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SessionDataQuestionnaireUploadView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        session = ExaminationSession.get_session(
            subject_code=self.kwargs.get('code'),
            session_number=self.kwargs.get('session_number'))

        # Add the examination session
        context.update({'session': session})

        # Return the updated context
        return context


def export_acoustic_data(request, code, session_number):
    """Exports the acoustic data in a CSV file"""
    return _export_data(request, code, session_number, model=DataAcoustic)


def export_questionnaire_data(request, code, session_number):
    """Exports the questionnaire data in a CSV file"""
    return _export_data(request, code, session_number, model=DataQuestionnaire)


def _export_data(request, code, session_number, model):
    """
    Exports the data in a CSV file that is downloaded in a browser.

    :param request: HTTP request
    :type request: Request
    :param code: code of the subject
    :type code: str
    :param session_number: session number
    :type session_number: str
    :param model: model to be used to get the data to be exported
    :type model: Model
    :return: HTTP response for the data to be exported
    :rtype: HttpResponse
    """

    # Prepare the HTTP response and the fetched data to be exported
    response = HttpResponse(content_type='text/csv')
    fetched = model.get_data(subject_code=code, session_number=session_number)

    # Prepare the fetched data to be downloadable
    response = model.prepare_downloadable(record=fetched, response=response)

    # Set the content disposition (to be downloaded by a browser)
    response['Content-Disposition'] = 'attachment; filename="exported.csv"'

    # Return the HTTP response
    return response
