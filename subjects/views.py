import logging
from django.http import HttpResponseRedirect
from django.shortcuts import reverse, redirect
from django.conf import settings
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.views import generic
from django.urls import reverse_lazy
from visualizer.subject import visualize_evolution_of_predictions
from visualizer.modalities import visualize_most_differentiating_features
from reporter.subject import create_report as create_subject_report
from reporter.session import create_report as session_subject_report
from .views_io import import_subjects_from_external_source
from .views_predictors import SubjectLBDPredictor, ExaminationSessionLBDPredictor
from .models_io import export_data, export_report
from .models_utils import compute_difference_from_norm
from .models_formatters import FeaturesFormatter
from .models import (
    Subject,
    ExaminationSession,
    DataAcoustic,
    DataActigraphy,
    DataHandwriting,
    DataPsychology,
    DataTCS,
    DataCEI,
    examinations
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

    def get_queryset(self):
        """Gets the queryset to be returned"""
        return ExaminationSession.get_sessions(subject=Subject.get_subject(code=self.kwargs.get('code')))

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super(SessionDetailView, self).get_context_data(**kwargs)

        # Get the examinations for the given session
        examination_data = [
            {'name': name, 'path': path, 'data': model.get_data(examination_session=self.object.id)}
            for name, path, model in examinations
        ]

        # Add the examinations
        context.update({'examinations': examination_data})

        # Predict the LBD probability (get the cached value)
        lbd_probability = ExaminationSessionLBDPredictor.predict_lbd_probability(self.request.user, self.object)

        # Add the prediction
        if lbd_probability:
            context.update({'prediction': lbd_probability})

        # Return the updated context
        return context


class SessionDataDetailViewTemplate(LoginRequiredMixin, generic.DetailView):
    """Base class for examination session data (detail view)"""

    # Define the template name
    template_name = ''

    # Define the slug attributes to enable filtering based on the specified field
    slug_field = 'session_number'
    slug_url_kwarg = 'session_number'

    # Define the context object name
    context_object_name = 'session'

    # Define the modality label
    modality = ''
    modality_data = ''

    # Define the model
    model = None

    # Define the pagination
    paginate_by = 15

    @classmethod
    def get_norms(cls):
        return getattr(settings, 'NORM_CONFIGURATION')[cls.modality]

    @classmethod
    def get_presentation(cls):
        return getattr(settings, 'PRESENTATION_CONFIGURATION')['features'][cls.modality]

    def get_queryset(self):
        """Gets the queryset to be returned"""
        return ExaminationSession.get_sessions(subject=Subject.get_subject(code=self.kwargs.get('code')))

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super().get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        original_data = self.model.get_data(examination_session=self.object.id)

        # Prepare the data
        if original_data:
            presentable_data = FeaturesFormatter(self.model).prepare_presentable(record=original_data)
            computable_data = FeaturesFormatter(self.model).prepare_computable(record=original_data)
        else:
            presentable_data = None
            computable_data = None

        # Compute the comparison with the normative data
        if computable_data:
            comparison = compute_difference_from_norm(computable_data, self.get_norms(), modality=self.modality)
            comparison = {c['feature']: c for c in comparison}

            for feature in presentable_data:
                if feature[FeaturesFormatter.FEATURE_LABEL_FIELD] in comparison:
                    norm = comparison[feature[FeaturesFormatter.FEATURE_LABEL_FIELD]]['norm value']
                    diff = comparison[feature[FeaturesFormatter.FEATURE_LABEL_FIELD]]['difference']
                    norm = round(float(norm), 4) if norm is not None else ''
                    diff = round(float(diff), 4) if diff is not None else ''
                    feature.update({'norm': norm, 'diff': diff})

        # Convert the numerical data into strings of fixed number of decimal places (for better UX)
        for feature in presentable_data:
            for key, value in feature.items():
                if isinstance(value, float):
                    feature[key] = '{:.4f}'.format(value)

        # Filter the data and add the filtration into the context
        if presentable_data and self.request.GET.get('q'):
            context.update({'q': self.request.GET.get('q')})
            presentable_data = [
                data for data in presentable_data
                if self.request.GET.get('q') in data.get(FeaturesFormatter.FEATURE_LABEL_FIELD)
            ]

        # Add the data
        context.update({self.modality_data: presentable_data})

        # Add the pagination if there are any loaded data
        if presentable_data:
            paginator = Paginator(object_list=presentable_data, per_page=self.paginate_by)
            goto_page = self.request.GET.get('page')

            context.update({
                'is_paginated': True if presentable_data and len(presentable_data) > self.paginate_by else False,
                'paginator': paginator,
                'page_number': self.request.GET.get('page'),
                'page_obj': paginator.get_page(goto_page)
            })

        # Add the visualization of the most discriminating features to the context
        if computable_data:
            context.update({
                'plot_div': visualize_most_differentiating_features(
                    session_data=computable_data,
                    norm_data=self.get_norms(),
                    modality=self.modality)
            })

        # Return the updated context
        return context


class SessionDataUpdateViewTemplate(LoginRequiredMixin, generic.CreateView):
    """Base class for examination session data (update view)"""

    # Define the template name
    template_name = ''

    # Define the successful redirect URL
    success_url = ''

    # Define the model name
    model = None

    # Define the form class
    form_class = None

    def form_valid(self, form):
        """Form valid hook: sets data's session after created"""

        # Save the form without database update
        data = form.save(commit=False)

        # Update the session and update the database records
        data = self.set_session(data)
        data.save()

        # Return the updated data
        return super().form_valid(form)

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
            self.success_url,
            kwargs={'code': self.kwargs.get('code'), 'session_number': self.kwargs.get('session_number')})

    def get_context_data(self, **kwargs):
        """Enriches the context with additional data"""

        # Get the context
        context = super().get_context_data(**kwargs)

        # Get the examination session for given URL parameters
        session = ExaminationSession.get_session(
            subject_code=self.kwargs.get('code'),
            session_number=self.kwargs.get('session_number'))

        # Add the examination session
        context.update({'session': session})

        # Return the updated context
        return context


class SessionDataAcousticDetailView(SessionDataDetailViewTemplate):
    """Class implementing session: acoustic data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail_data_acoustic.html'

    # Define the modality label
    modality = 'acoustic'
    modality_data = 'acoustic_data'

    # Define the model
    model = DataAcoustic


class SessionDataAcousticUpdateView(SessionDataUpdateViewTemplate):
    """Class implementing session: acoustic data update view"""

    # Define the template name
    template_name = 'subjects/session_update_data_acoustic.html'

    # Define the successful redirect URL
    success_url = 'subjects:session_detail_data_acoustic'

    # Define the model name
    model = DataAcoustic

    # Define the form class
    form_class = DataAcousticForm


class SessionDataActigraphyDetailView(SessionDataDetailViewTemplate):
    """Class implementing session: actigraphy data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail_data_actigraphy.html'

    # Define the modality label
    modality = 'actigraphy'
    modality_data = 'actigraphy_data'

    # Define the model
    model = DataActigraphy


class SessionDataActigraphyUpdateView(SessionDataUpdateViewTemplate):
    """Class implementing session: actigraphy data update view"""

    # Define the template name
    template_name = 'subjects/session_update_data_actigraphy.html'

    # Define the successful redirect URL
    success_url = 'subjects:session_detail_data_actigraphy'

    # Define the model name
    model = DataActigraphy

    # Define the form class
    form_class = DataActigraphyForm


class SessionDataHandwritingDetailView(SessionDataDetailViewTemplate):
    """Class implementing session: handwriting data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail_data_handwriting.html'

    # Define the modality label
    modality = 'handwriting'
    modality_data = 'handwriting_data'

    # Define the model
    model = DataHandwriting


class SessionDataHandwritingUpdateView(SessionDataUpdateViewTemplate):
    """Class implementing session: handwriting data update view"""

    # Define the template name
    template_name = 'subjects/session_update_data_handwriting.html'

    # Define the successful redirect URL
    success_url = 'subjects:session_detail_data_handwriting'

    # Define the model name
    model = DataHandwriting

    # Define the form class
    form_class = DataHandwritingForm


class SessionDataPsychologyDetailView(SessionDataDetailViewTemplate):
    """Class implementing session: psychology data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail_data_psychology.html'

    # Define the modality label
    modality = 'psychology'
    modality_data = 'psychology_data'

    # Define the model
    model = DataPsychology


class SessionDataPsychologyUpdateView(SessionDataUpdateViewTemplate):
    """Class implementing session: psychology data update view"""

    # Define the template name
    template_name = 'subjects/session_update_data_psychology.html'

    # Define the successful redirect URL
    success_url = 'subjects:session_detail_data_psychology'

    # Define the model name
    model = DataPsychology

    # Define the form class
    form_class = DataPsychologyForm


class SessionDataTCSDetailView(SessionDataDetailViewTemplate):
    """Class implementing session: TCS data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail_data_tcs.html'

    # Define the modality label
    modality = 'tcs'
    modality_data = 'tcs_data'

    # Define the model
    model = DataTCS


class SessionDataTCSUpdateView(SessionDataUpdateViewTemplate):
    """Class implementing session: TCS data update view"""

    # Define the template name
    template_name = 'subjects/session_update_data_tcs.html'

    # Define the successful redirect URL
    success_url = 'subjects:session_detail_data_tcs'

    # Define the model name
    model = DataTCS

    # Define the form class
    form_class = DataTCSForm


class SessionDataCEIDetailView(SessionDataDetailViewTemplate):
    """Class implementing session: CEI data detail view"""

    # Define the template name
    template_name = 'subjects/session_detail_data_cei.html'

    # Define the modality label
    modality = 'cei'
    modality_data = 'cei_data'

    # Define the model
    model = DataCEI


class SessionDataCEIUpdateView(SessionDataUpdateViewTemplate):
    """Class implementing session: cei data update view"""

    # Define the template name
    template_name = 'subjects/session_update_data_cei.html'

    # Define the successful redirect URL
    success_url = 'subjects:session_detail_data_cei'

    # Define the model name
    model = DataCEI

    # Define the form class
    form_class = DataCEIForm


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


def export_subject_report(request, code):
    """Exports the subject preDLB probability predictions report in a PDF file"""

    # Prepare the report
    report_path = create_subject_report(request, Subject.get_subject(code=code))

    # Export the report
    return export_report(request, code, report_path)


def export_session_report(request, code, session_number):
    """Exports the session preDLB probability predictions report in a PDF file"""

    # Get the subject and the session
    subject = Subject.get_subject(code=code)
    session = ExaminationSession.get_session(subject=subject, session_number=session_number)

    # Prepare the report
    report_path = session_subject_report(request, subject, session)

    # Export the report
    return export_report(request, code, report_path)
