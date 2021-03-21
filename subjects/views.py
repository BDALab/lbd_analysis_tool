from django.http import HttpResponseRedirect
from django.shortcuts import reverse, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.urls import reverse_lazy
from .models import Subject, ExaminationSession, DataAcoustic, DataQuestionnaire
from .forms import SubjectModelForm, CustomUserCreationForm, DataAcousticForm, DataQuestionnaireForm


class SignupView(generic.CreateView):
    """Class implementing signup view"""

    # Define the template name
    template_name = 'registration/signup.html'

    # Define the form class
    form_class = CustomUserCreationForm

    def get_success_url(self):
        return reverse('login')


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
        return reverse('subjects:subject_detail', kwargs={'code': self.object.code})


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
        return reverse('subjects:subject_list')


@login_required(login_url='/login')
def create_session(request, code):
    """
    Creates a new examination session for a requested subject.

    :param request: HTTP request
    :type request: django.core.handlers.wsgi.WSGIRequest
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
            'subjects:session_detail_data_acoustic',
            kwargs={'code': subject.code, 'session_number': session_number}
        )
    )


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
            acoustic_data = DataAcoustic.read_file(acoustic_data)

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

        # Get the examination session for given URL parameters
        subject = Subject.get_subject(code=self.kwargs.get('code'))
        session = ExaminationSession.get_session(subject=subject, session_number=self.kwargs.get('session_number'))

        # Update the examination session
        data.examination_session = session

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
        subject = Subject.get_subject(code=self.kwargs.get('code'))
        session = ExaminationSession.get_session(subject=subject, session_number=self.kwargs.get('session_number'))

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
            questionnaire_data = [
                questionnaire_data.question_1,
                questionnaire_data.question_2,
                questionnaire_data.question_3,
                questionnaire_data.question_4,
                questionnaire_data.question_5
            ]

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
        subject = Subject.get_subject(code=self.kwargs.get('code'))
        session = ExaminationSession.get_session(subject=subject, session_number=self.kwargs.get('session_number'))

        # Add the examination session
        context.update({'session': session})

        # Return the updated context
        return context

    def set_session(self, data):
        """Sets the session for a given data after creating"""

        # Get the examination session for given URL parameters
        subject = Subject.get_subject(code=self.kwargs.get('code'))
        session = ExaminationSession.get_session(subject=subject, session_number=self.kwargs.get('session_number'))

        # Update the examination session
        data.examination_session = session

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
        subject = Subject.get_subject(code=self.kwargs.get('code'))
        session = ExaminationSession.get_session(subject=subject, session_number=self.kwargs.get('session_number'))

        # Return the object
        return DataQuestionnaire.get_data(examination_session=session)

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SessionDataQuestionnaireUpdateView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        subject = Subject.get_subject(code=self.kwargs.get('code'))
        session = ExaminationSession.get_session(subject=subject, session_number=self.kwargs.get('session_number'))

        # Add the examination session
        context.update({'session': session})

        # Return the updated context
        return context

    def get_success_url(self):
        """Returns the success URL"""
        return reverse_lazy(
            'subjects:session_detail_data_questionnaire',
            kwargs={'code': self.kwargs.get('code'), 'session_number': self.kwargs.get('session_number')})
