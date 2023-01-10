import logging
from django.http import HttpResponseRedirect
from django.shortcuts import reverse, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.views import generic
from django.urls import reverse_lazy
from visualizer.subject import visualize_evolution_of_predictions
from .views_io import import_subjects_from_external_source
from .views_predictors import SubjectLBDPredictor, ExaminationSessionLBDPredictor
from .models_io import export_data
from .models_formatters import FeaturesFormatter
from .models import (
    Subject,
    ExaminationSession,
    DataAcoustic,
    DataActigraphy,
    DataHandwriting,
    DataPsychology,
    DataTCS,
    DataCEI
)
from .forms import (
    SubjectModelForm,
    CustomUserCreationForm,
    DataAcousticForm,
    DataActigraphyForm,
    DataHandwritingForm,
    DataPsychologyForm,
    DataTCSForm,
    DataCEIForm,
    UploadFileForm
)


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
    paginate_by = 10

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

        # Add the filter
        if self.request.GET.get('q'):
            context.update({'q': self.request.GET.get('q')})

        # Add the session information
        for subject in context.get(self.context_object_name):
            subject.num_sessions = ExaminationSession.get_sessions(subject=subject).count()

        # Get the LBD probability for each subject in the list
        for subject in context.get(self.context_object_name):
            subject.lbd_probability = SubjectLBDPredictor.predict_lbd_probability(self.request.user, subject)

        # Return the updated context
        return context


class SubjectCohortImportView(LoginRequiredMixin, UserPassesTestMixin, generic.FormView):
    """Class implementing subject cohort import"""

    # Define the template name
    template_name = 'subjects/subject_import_cohort.html'

    # Define the form class
    form_class = UploadFileForm

    def test_func(self):
        """Test function to determine if a user can use the view"""
        return self.request.user.power_user

    def form_valid(self, form):
        """Form valid hook: imports the subjects"""

        # Import the subjects
        import_subjects_from_external_source(self.request.user, form)

        # Return the updated data
        return super(SubjectCohortImportView, self).form_valid(form)

    def get_success_url(self):
        """Returns the success URL"""
        return reverse_lazy('subjects:subject_list')


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

        # Predict the LBD probability and add it to the context
        if sessions:

            # Get the cached LBD probability and update the subject
            lbd_probability = SubjectLBDPredictor.predict_lbd_probability(self.request.user, self.object)
            self.object.lbd_probability = lbd_probability

            # Add the prediction to the context
            if lbd_probability:
                context.update({'prediction': lbd_probability})

        # Add the visualization of the predicted LBD probability to the context
        context.update({'plot_div': visualize_evolution_of_predictions(self.request.user, self.object)})

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

    # Define the examination session parts
    # 1. examination name
    # 2. path name
    # 3. model
    examinations = [
        ('acoustic', 'session_detail_data_acoustic', DataAcoustic),
        ('actigraphy', 'session_detail_data_actigraphy', DataActigraphy),
        ('handwriting', 'session_detail_data_handwriting', DataHandwriting),
        ('psychology', 'session_detail_data_psychology', DataPsychology),
        ('tcs', 'session_detail_data_tcs', DataTCS),
        ('cei', 'session_detail_data_cei', DataCEI)
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

        # Predict the LBD probability (get the cached value)
        lbd_probability = ExaminationSessionLBDPredictor.predict_lbd_probability(self.request.user, self.object)

        # Add the prediction
        if lbd_probability:
            context.update({'prediction': lbd_probability})

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
            acoustic_data = FeaturesFormatter(DataAcoustic).prepare_presentable(record=acoustic_data)

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


class SessionDataActigraphyDetailView(LoginRequiredMixin, generic.DetailView):
    """Class implementing session: actigraphy data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail_data_actigraphy.html'

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
        context = super(SessionDataActigraphyDetailView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        actigraphy_data = DataActigraphy.get_data(examination_session=self.object.id)

        # Prepare the actigraphy data
        if actigraphy_data:
            actigraphy_data = FeaturesFormatter(DataActigraphy).prepare_presentable(record=actigraphy_data)

        # Add the acoustic data
        context.update({'actigraphy_data': actigraphy_data})

        # Filter the actigraphy data and add the filtration into the context
        if actigraphy_data and self.request.GET.get('q'):
            actigraphy_data = [data for data in actigraphy_data if self.request.GET.get('q') in data.get('label')]
            context.update({'q': self.request.GET.get('q')})

        # Add the pagination if there are any loaded actigraphy data
        if actigraphy_data:
            paginator = Paginator(actigraphy_data, self.paginate_by)
            goto_page = self.request.GET.get('page')

            context.update({
                'is_paginated': True if actigraphy_data and len(actigraphy_data) > self.paginate_by else False,
                'paginator': paginator,
                'page_number': self.request.GET.get('page'),
                'page_obj': paginator.get_page(goto_page)
            })

        # Return the updated context
        return context


class SessionDataActigraphyUpdateView(LoginRequiredMixin, generic.CreateView):
    """Class implementing session: actigraphy data update view"""

    # Define the template name
    template_name = 'subjects/session_update_data_actigraphy.html'

    # Define the model name
    model = DataActigraphy

    # Define the form class
    form_class = DataActigraphyForm

    def form_valid(self, form):
        """Form valid hook: sets data's session after created"""

        # Save the form without database update
        data = form.save(commit=False)

        # Update the session and update the database records
        data = self.set_session(data)
        data.save()

        # Return the updated data
        return super(SessionDataActigraphyUpdateView, self).form_valid(form)

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
            'subjects:session_detail_data_actigraphy',
            kwargs={'code': self.kwargs.get('code'), 'session_number': self.kwargs.get('session_number')})

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SessionDataActigraphyUpdateView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        session = ExaminationSession.get_session(
            subject_code=self.kwargs.get('code'),
            session_number=self.kwargs.get('session_number'))

        # Add the examination session
        context.update({'session': session})

        # Return the updated context
        return context


class SessionDataHandwritingDetailView(LoginRequiredMixin, generic.DetailView):
    """Class implementing session: handwriting data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail_data_handwriting.html'

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
        context = super(SessionDataHandwritingDetailView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        handwriting_data = DataHandwriting.get_data(examination_session=self.object.id)

        # Prepare the acoustic data
        if handwriting_data:
            handwriting_data = FeaturesFormatter(DataHandwriting).prepare_presentable(record=handwriting_data)

        # Add the handwriting data
        context.update({'handwriting_data': handwriting_data})

        # Filter the handwriting data and add the filtration into the context
        if handwriting_data and self.request.GET.get('q'):
            handwriting_data = [data for data in handwriting_data if self.request.GET.get('q') in data.get('label')]
            context.update({'q': self.request.GET.get('q')})

        # Add the pagination if there are any loaded handwriting data
        if handwriting_data:
            paginator = Paginator(handwriting_data, self.paginate_by)
            goto_page = self.request.GET.get('page')

            context.update({
                'is_paginated': True if handwriting_data and len(handwriting_data) > self.paginate_by else False,
                'paginator': paginator,
                'page_number': self.request.GET.get('page'),
                'page_obj': paginator.get_page(goto_page)
            })

        # Return the updated context
        return context


class SessionDataHandwritingUpdateView(LoginRequiredMixin, generic.CreateView):
    """Class implementing session: handwriting data update view"""

    # Define the template name
    template_name = 'subjects/session_update_data_handwriting.html'

    # Define the model name
    model = DataHandwriting

    # Define the form class
    form_class = DataHandwritingForm

    def form_valid(self, form):
        """Form valid hook: sets data's session after created"""

        # Save the form without database update
        data = form.save(commit=False)

        # Update the session and update the database records
        data = self.set_session(data)
        data.save()

        # Return the updated data
        return super(SessionDataHandwritingUpdateView, self).form_valid(form)

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
            'subjects:session_detail_data_handwriting',
            kwargs={'code': self.kwargs.get('code'), 'session_number': self.kwargs.get('session_number')})

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SessionDataHandwritingUpdateView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        session = ExaminationSession.get_session(
            subject_code=self.kwargs.get('code'),
            session_number=self.kwargs.get('session_number'))

        # Add the examination session
        context.update({'session': session})

        # Return the updated context
        return context


class SessionDataPsychologyDetailView(LoginRequiredMixin, generic.DetailView):
    """Class implementing session: psychology data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail_data_psychology.html'

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
        context = super(SessionDataPsychologyDetailView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        psychology_data = DataPsychology.get_data(examination_session=self.object.id)

        # Prepare the psychology data
        if psychology_data:
            psychology_data = FeaturesFormatter(DataPsychology).prepare_presentable(record=psychology_data)

        # Add the psychology data
        context.update({'psychology_data': psychology_data})

        # Filter the psychology data and add the filtration into the context
        if psychology_data and self.request.GET.get('q'):
            psychology_data = [data for data in psychology_data if self.request.GET.get('q') in data.get('label')]
            context.update({'q': self.request.GET.get('q')})

        # Add the pagination if there are any loaded psychology data
        if psychology_data:
            paginator = Paginator(psychology_data, self.paginate_by)
            goto_page = self.request.GET.get('page')

            context.update({
                'is_paginated': True if psychology_data and len(psychology_data) > self.paginate_by else False,
                'paginator': paginator,
                'page_number': self.request.GET.get('page'),
                'page_obj': paginator.get_page(goto_page)
            })

        # Return the updated context
        return context


class SessionDataPsychologyUpdateView(LoginRequiredMixin, generic.CreateView):
    """Class implementing session: psychology data update view"""

    # Define the template name
    template_name = 'subjects/session_update_data_psychology.html'

    # Define the model name
    model = DataPsychology

    # Define the form class
    form_class = DataPsychologyForm

    def form_valid(self, form):
        """Form valid hook: sets data's session after created"""

        # Save the form without database update
        data = form.save(commit=False)

        # Update the session and update the database records
        data = self.set_session(data)
        data.save()

        # Return the updated data
        return super(SessionDataPsychologyUpdateView, self).form_valid(form)

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
            'subjects:session_detail_data_psychology',
            kwargs={'code': self.kwargs.get('code'), 'session_number': self.kwargs.get('session_number')})

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SessionDataPsychologyUpdateView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        session = ExaminationSession.get_session(
            subject_code=self.kwargs.get('code'),
            session_number=self.kwargs.get('session_number'))

        # Add the examination session
        context.update({'session': session})

        # Return the updated context
        return context


class SessionDataTCSDetailView(LoginRequiredMixin, generic.DetailView):
    """Class implementing session: TCS data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail_data_tcs.html'

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
        context = super(SessionDataTCSDetailView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        tcs_data = DataTCS.get_data(examination_session=self.object.id)

        # Prepare the tcs data
        if tcs_data:
            tcs_data = FeaturesFormatter(DataTCS).prepare_presentable(record=tcs_data)

        # Add the tcs data
        context.update({'tcs_data': tcs_data})

        # Filter the tcs data and add the filtration into the context
        if tcs_data and self.request.GET.get('q'):
            tcs_data = [data for data in tcs_data if self.request.GET.get('q') in data.get('label')]
            context.update({'q': self.request.GET.get('q')})

        # Add the pagination if there are any loaded tcs data
        if tcs_data:
            paginator = Paginator(tcs_data, self.paginate_by)
            goto_page = self.request.GET.get('page')

            context.update({
                'is_paginated': True if tcs_data and len(tcs_data) > self.paginate_by else False,
                'paginator': paginator,
                'page_number': self.request.GET.get('page'),
                'page_obj': paginator.get_page(goto_page)
            })

        # Return the updated context
        return context


class SessionDataTCSUpdateView(LoginRequiredMixin, generic.CreateView):
    """Class implementing session: TCS data update view"""

    # Define the template name
    template_name = 'subjects/session_update_data_tcs.html'

    # Define the model name
    model = DataTCS

    # Define the form class
    form_class = DataTCSForm

    def form_valid(self, form):
        """Form valid hook: sets data's session after created"""

        # Save the form without database update
        data = form.save(commit=False)

        # Update the session and update the database records
        data = self.set_session(data)
        data.save()

        # Return the updated data
        return super(SessionDataTCSUpdateView, self).form_valid(form)

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
            'subjects:session_detail_data_tcs',
            kwargs={'code': self.kwargs.get('code'), 'session_number': self.kwargs.get('session_number')})

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SessionDataTCSUpdateView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        session = ExaminationSession.get_session(
            subject_code=self.kwargs.get('code'),
            session_number=self.kwargs.get('session_number'))

        # Add the examination session
        context.update({'session': session})

        # Return the updated context
        return context


class SessionDataCEIDetailView(LoginRequiredMixin, generic.DetailView):
    """Class implementing session: CEI data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail_data_cei.html'

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
        context = super(SessionDataCEIDetailView, self).get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        cei_data = DataCEI.get_data(examination_session=self.object.id)

        # Prepare the cei data
        if cei_data:
            cei_data = FeaturesFormatter(DataCEI).prepare_presentable(record=cei_data)

        # Add the cei data
        context.update({'cei_data': cei_data})

        # Filter the cei data and add the filtration into the context
        if cei_data and self.request.GET.get('q'):
            cei_data = [data for data in cei_data if self.request.GET.get('q') in data.get('label')]
            context.update({'q': self.request.GET.get('q')})

        # Add the pagination if there are any loaded cei data
        if cei_data:
            paginator = Paginator(cei_data, self.paginate_by)
            goto_page = self.request.GET.get('page')

            context.update({
                'is_paginated': True if cei_data and len(cei_data) > self.paginate_by else False,
                'paginator': paginator,
                'page_number': self.request.GET.get('page'),
                'page_obj': paginator.get_page(goto_page)
            })

        # Return the updated context
        return context


class SessionDataCEIUpdateView(LoginRequiredMixin, generic.CreateView):
    """Class implementing session: cei data update view"""

    # Define the template name
    template_name = 'subjects/session_update_data_cei.html'

    # Define the model name
    model = DataCEI

    # Define the form class
    form_class = DataCEIForm

    def form_valid(self, form):
        """Form valid hook: sets data's session after created"""

        # Save the form without database update
        data = form.save(commit=False)

        # Update the session and update the database records
        data = self.set_session(data)
        data.save()

        # Return the updated data
        return super(SessionDataCEIUpdateView, self).form_valid(form)

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
            'subjects:session_detail_data_cei',
            kwargs={'code': self.kwargs.get('code'), 'session_number': self.kwargs.get('session_number')})

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SessionDataCEIUpdateView, self).get_context_data(**kwargs)

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
    return export_data(request, code, session_number, model=DataAcoustic)


def export_actigraphy_data(request, code, session_number):
    """Exports the actigraphy data in a CSV file"""
    return export_data(request, code, session_number, model=DataActigraphy)


def export_handwriting_data(request, code, session_number):
    """Exports the handwriting data in a CSV file"""
    return export_data(request, code, session_number, model=DataHandwriting)


def export_psychology_data(request, code, session_number):
    """Exports the psychology data in a CSV file"""
    return export_data(request, code, session_number, model=DataPsychology)


def export_tcs_data(request, code, session_number):
    """Exports the TCS data in a CSV file"""
    return export_data(request, code, session_number, model=DataTCS)


def export_cei_data(request, code, session_number):
    """Exports the CEI data in a CSV file"""
    return export_data(request, code, session_number, model=DataCEI)
