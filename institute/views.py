from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import authenticate, login
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User

from .models import Batch, Course, Trainer, TopicProgress, Topic, Module, UserProfile
from .forms import BatchForm, TrainerForm, CourseCreateForm, ModuleCreateForm, TopicCreateForm, UserCreationForm, \
    UserProfileForm


# Define the permission functions FIRST, before they are used in decorators
def is_admin(user):
    return user.is_staff or (hasattr(user, 'userprofile') and user.userprofile.role == 'admin')


def is_trainer(user):
    # Check if user has trainer profile and is active
    try:
        return user.userprofile.role == 'trainer' and hasattr(user, 'trainer') and user.trainer.is_active
    except UserProfile.DoesNotExist:
        return False


def is_manager(user):
    try:
        return user.userprofile.role == 'manager'
    except UserProfile.DoesNotExist:
        return False


class CustomLoginView(LoginView):
    template_name = 'institute/login.html'

    def form_valid(self, form):
        # Authenticate user
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=username, password=password)

        if user is not None:
            login(self.request, user)

            # Get the selected role from the form
            role = self.request.POST.get('role', 'auto')

            # Get user role from UserProfile
            try:
                user_role = user.userprofile.role
            except UserProfile.DoesNotExist:
                # Create default profile if it doesn't exist
                profile = UserProfile.objects.create(user=user, role='student')
                user_role = 'student'

            # Handle redirection based on role selection
            if role == 'admin' and user_role == 'admin':
                return redirect('admin_dashboard')
            elif role == 'trainer' and user_role == 'trainer':
                return redirect('trainer_dashboard')
            elif role == 'manager' and user_role == 'manager':
                return redirect('admin_dashboard')  # Redirect to admin dashboard for now
            elif role == 'admin' and user_role != 'admin':
                messages.error(self.request, "You don't have administrator privileges.")
                return redirect('dashboard')
            elif role == 'trainer' and user_role != 'trainer':
                messages.error(self.request, "You don't have a trainer profile.")
                return redirect('dashboard')
            elif role == 'manager' and user_role != 'manager':
                messages.error(self.request, "You don't have manager privileges.")
                return redirect('dashboard')
            else:
                # Auto detect - redirect based on user role
                if user_role == 'admin' or user.is_staff:
                    return redirect('admin_dashboard')
                elif user_role == 'trainer':
                    return redirect('trainer_dashboard')
                elif user_role == 'manager':
                    return redirect('admin_dashboard')  # Redirect to admin dashboard for now
                elif user_role == 'student':
                    # Redirect to student dashboard (to be implemented)
                    return redirect('dashboard')
                else:
                    return redirect('dashboard')

        return super().form_invalid(form)


from django.views.decorators.csrf import csrf_exempt


class CustomLogoutView(LogoutView):
    template_name = 'institute/logout.html'
    next_page = reverse_lazy('login')

    # Allow GET requests for logout
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


@login_required
def dashboard(request):
    # Ensure user has a profile
    try:
        user_role = request.user.userprofile.role
    except UserProfile.DoesNotExist:
        # Create default profile if it doesn't exist
        profile = UserProfile.objects.create(user=request.user, role='student')
        user_role = 'student'

    if user_role == 'admin' or request.user.is_staff:
        return admin_dashboard(request)
    elif user_role == 'trainer':
        return trainer_dashboard(request)
    elif user_role == 'manager':
        # Redirect to manager dashboard (to be implemented)
        return admin_dashboard(request)
    else:
        messages.warning(request, "You don't have a specific role assigned. Please contact administrator.")
        return render(request, 'institute/access_denied.html')


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    batches = Batch.objects.all()
    total_batches = batches.count()
    ongoing_batches = batches.filter(status='ongoing').count()
    completed_batches = batches.filter(status='completed').count()
    active_trainers = Trainer.objects.filter(is_active=True).count()

    # Team statistics
    total_users = User.objects.count()
    admin_count = UserProfile.objects.filter(role='admin').count()
    trainer_count = UserProfile.objects.filter(role='trainer').count()
    manager_count = UserProfile.objects.filter(role='manager').count()
    student_count = UserProfile.objects.filter(role='student').count()

    # Batch progress data
    batch_progress = []
    for batch in batches:
        progress = batch.get_completion_rate()
        batch_progress.append({
            'batch': batch,
            'progress': progress
        })

    # Trainer statistics
    trainers = Trainer.objects.all()
    trainer_stats = []

    for trainer in trainers:
        trainer_batches = Batch.objects.filter(trainer=trainer)
        total_trainer_batches = trainer_batches.count()
        ongoing_trainer_batches = trainer_batches.filter(status='ongoing').count()
        completed_trainer_batches = trainer_batches.filter(status='completed').count()

        # Calculate average progress for this trainer's batches
        total_progress = 0
        batch_count = 0
        for batch in trainer_batches:
            progress = batch.get_completion_rate()
            total_progress += progress
            batch_count += 1

        avg_progress = total_progress / batch_count if batch_count > 0 else 0

        # Calculate rates for progress bar
        completion_rate = (completed_trainer_batches / total_trainer_batches * 100) if total_trainer_batches > 0 else 0
        ongoing_rate = (ongoing_trainer_batches / total_trainer_batches * 100) if total_trainer_batches > 0 else 0

        trainer_stats.append({
            'trainer': trainer,
            'total_batches': total_trainer_batches,
            'ongoing_batches': ongoing_trainer_batches,
            'completed_batches': completed_trainer_batches,
            'avg_progress': avg_progress,
            'completion_rate': completion_rate,
            'ongoing_rate': ongoing_rate,
        })

    context = {
        'total_batches': total_batches,
        'ongoing_batches': ongoing_batches,
        'completed_batches': completed_batches,
        'active_trainers': active_trainers,
        'batch_progress': batch_progress,
        'trainer_stats': trainer_stats,
        # Team statistics
        'total_users': total_users,
        'admin_count': admin_count,
        'trainer_count': trainer_count,
        'manager_count': manager_count,
        'student_count': student_count,
    }
    return render(request, 'institute/dashboard.html', context)


@login_required
@user_passes_test(is_trainer)
def trainer_dashboard(request):
    trainer = request.user.trainer
    batches = Batch.objects.filter(trainer=trainer)

    batch_progress = []
    for batch in batches:
        progress = batch.get_completion_rate()
        batch_progress.append({
            'batch': batch,
            'progress': progress
        })

    # Get user profile for additional info
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user, role='trainer')

    context = {
        'trainer': trainer,
        'user_profile': user_profile,
        'batch_progress': batch_progress,
    }
    return render(request, 'institute/trainer_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def batch_list(request):
    batch_list = Batch.objects.all().order_by('-created_at')
    paginator = Paginator(batch_list, 10)

    page_number = request.GET.get('page')
    batches = paginator.get_page(page_number)

    return render(request, 'institute/batch_list.html', {'batches': batches})


@login_required
@user_passes_test(is_trainer)
def trainer_batch_list(request):
    trainer = request.user.trainer
    batch_list = Batch.objects.filter(trainer=trainer).order_by('-created_at')
    paginator = Paginator(batch_list, 10)

    page_number = request.GET.get('page')
    batches = paginator.get_page(page_number)

    return render(request, 'institute/batch_list.html', {'batches': batches})


@login_required
def batch_detail(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)

    # Check if user has access to this batch
    if not request.user.is_staff and not (hasattr(request.user, 'trainer') and batch.trainer == request.user.trainer):
        return render(request, 'institute/access_denied.html')

    modules = batch.course.modules.all()
    topics_progress = {}

    for module in modules:
        topics_progress[module] = []
        for topic in module.topics.all():
            try:
                progress = TopicProgress.objects.get(batch=batch, topic=topic)
                topics_progress[module].append({
                    'topic': topic,
                    'progress': progress
                })
            except TopicProgress.DoesNotExist:
                progress = TopicProgress.objects.create(batch=batch, topic=topic)
                topics_progress[module].append({
                    'topic': topic,
                    'progress': progress
                })

    completion_rate = batch.get_completion_rate()

    context = {
        'batch': batch,
        'modules': modules,
        'topics_progress': topics_progress,
        'completion_rate': completion_rate,
    }
    return render(request, 'institute/batch_detail.html', context)


@login_required
@user_passes_test(is_admin)
def create_batch(request):
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save()
            # Initialize topic progress for all topics in the course
            topics = Topic.objects.filter(module__course=batch.course)
            for topic in topics:
                TopicProgress.objects.get_or_create(batch=batch, topic=topic)
            messages.success(request, f'Batch "{batch.name}" created successfully!')
            return redirect('batch_detail', batch_id=batch.id)
    else:
        form = BatchForm()

    return render(request, 'institute/create_batch.html', {'form': form})


@login_required
@user_passes_test(is_trainer)
def mark_topic_complete(request, progress_id):
    progress = get_object_or_404(TopicProgress, id=progress_id)

    # Check if the current trainer owns this batch
    if progress.batch.trainer != request.user.trainer:
        return render(request, 'institute/access_denied.html')

    if request.method == 'POST':
        completed = request.POST.get('completed') == 'true'
        progress.completed = completed
        if completed:
            progress.completed_date = timezone.now()
            messages.success(request, f'Topic "{progress.topic.name}" marked as completed!')
        else:
            progress.completed_date = None
            messages.info(request, f'Topic "{progress.topic.name}" marked as incomplete!')
        progress.save()

    return redirect('batch_detail', batch_id=progress.batch.id)


@login_required
@user_passes_test(is_admin)
def trainer_list(request):
    trainer_list = Trainer.objects.all().order_by('-created_at')
    paginator = Paginator(trainer_list, 10)

    page_number = request.GET.get('page')
    trainers = paginator.get_page(page_number)

    context = {
        'trainers': trainers,
    }
    return render(request, 'institute/trainer_list.html', context)


@login_required
@user_passes_test(is_admin)
def create_trainer(request):
    if request.method == 'POST':
        form = TrainerForm(request.POST)
        if form.is_valid():
            trainer = form.save()
            messages.success(request, f'Trainer "{trainer.user.get_full_name()}" created successfully!')
            return redirect('trainer_list')
    else:
        form = TrainerForm()

    context = {
        'form': form,
    }
    return render(request, 'institute/create_trainer.html', context)


@login_required
@user_passes_test(is_admin)
def course_list(request):
    course_list = Course.objects.all().order_by('-created_at')
    paginator = Paginator(course_list, 10)

    page_number = request.GET.get('page')
    courses = paginator.get_page(page_number)

    context = {
        'courses': courses,
    }
    return render(request, 'institute/course_list.html', context)


@login_required
@user_passes_test(is_admin)
def create_course(request):
    if request.method == 'POST':
        form = CourseCreateForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course.name}" created successfully!')
            return redirect('course_list')
    else:
        form = CourseCreateForm()

    context = {
        'form': form,
    }
    return render(request, 'institute/create_course.html', context)


@login_required
@user_passes_test(is_admin)
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    modules = course.modules.all()

    context = {
        'course': course,
        'modules': modules,
    }
    return render(request, 'institute/course_detail.html', context)


@login_required
@user_passes_test(is_admin)
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = CourseCreateForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course.name}" updated successfully!')
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseCreateForm(instance=course)

    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'institute/edit_course.html', context)


@login_required
@user_passes_test(is_admin)
def edit_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)

    if request.method == 'POST':
        form = ModuleCreateForm(request.POST, instance=module)
        if form.is_valid():
            module = form.save()
            messages.success(request, f'Module "{module.name}" updated successfully!')
            return redirect('course_detail', course_id=module.course.id)
    else:
        form = ModuleCreateForm(instance=module)

    context = {
        'form': form,
        'module': module,
    }
    return render(request, 'institute/edit_module.html', context)


@login_required
@user_passes_test(is_admin)
def edit_topic(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)

    if request.method == 'POST':
        form = TopicCreateForm(request.POST, instance=topic)
        if form.is_valid():
            topic = form.save()
            messages.success(request, f'Topic "{topic.name}" updated successfully!')
            return redirect('course_detail', course_id=topic.module.course.id)
    else:
        form = TopicCreateForm(instance=topic)

    context = {
        'form': form,
        'topic': topic,
    }
    return render(request, 'institute/edit_topic.html', context)


@login_required
@user_passes_test(is_admin)
def delete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course_id = module.course.id

    if request.method == 'POST':
        module_name = module.name
        module.delete()
        messages.success(request, f'Module "{module_name}" deleted successfully!')
        return redirect('course_detail', course_id=course_id)

    context = {
        'module': module,
    }
    return render(request, 'institute/delete_module.html', context)


@login_required
@user_passes_test(is_admin)
def delete_topic(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    course_id = topic.module.course.id

    if request.method == 'POST':
        topic_name = topic.name
        topic.delete()
        messages.success(request, f'Topic "{topic_name}" deleted successfully!')
        return redirect('course_detail', course_id=course_id)

    context = {
        'topic': topic,
    }
    return render(request, 'institute/delete_topic.html', context)


@login_required
@user_passes_test(is_admin)
def add_module(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = ModuleCreateForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            messages.success(request, f'Module "{module.name}" added successfully!')
            return redirect('course_detail', course_id=course.id)
    else:
        form = ModuleCreateForm()

    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'institute/add_module.html', context)


@login_required
@user_passes_test(is_admin)
def add_topic(request, module_id):
    module = get_object_or_404(Module, id=module_id)

    if request.method == 'POST':
        form = TopicCreateForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.module = module
            topic.save()
            messages.success(request, f'Topic "{topic.name}" added successfully!')
            return redirect('course_detail', course_id=module.course.id)
    else:
        form = TopicCreateForm()

    context = {
        'form': form,
        'module': module,
    }
    return render(request, 'institute/add_topic.html', context)


# Team Management Views
@login_required
@user_passes_test(is_admin)
def team_management(request):
    users = User.objects.all().order_by('-date_joined')

    # Combine users with their profiles
    team_members = []
    for user in users:
        try:
            profile = user.userprofile
            team_members.append({
                'user': user,
                'profile': profile,
                'is_trainer': hasattr(user, 'trainer') and user.trainer.is_active
            })
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = UserProfile.objects.create(user=user, role='student')
            team_members.append({
                'user': user,
                'profile': profile,
                'is_trainer': False
            })

    context = {
        'team_members': team_members,
    }
    return render(request, 'institute/team_management.html', context)


@login_required
@user_passes_test(is_admin)
def create_team_member(request):
    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            # Create user
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()

            # Create user profile
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            # If role is trainer, create trainer profile
            if profile.role == 'trainer':
                trainer, created = Trainer.objects.get_or_create(
                    user=user,
                    defaults={
                        'specialization': 'General',
                        'experience_years': 1,
                        'is_active': True,
                        'phone': profile.phone or '',
                        'email': user.email
                    }
                )
                if not created:
                    trainer.is_active = True
                    trainer.save()

            messages.success(request, f'Team member {user.get_full_name()} created successfully!')
            return redirect('team_management')
    else:
        user_form = UserCreationForm()
        profile_form = UserProfileForm()

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'institute/create_team_member.html', context)


@login_required
@user_passes_test(is_admin)
def update_team_member_role(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Get or create user profile
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user, role='student')

    if request.method == 'POST':
        old_role = profile.role
        new_role = request.POST.get('role')

        profile.role = new_role
        profile.save()

        # Handle trainer profile creation/removal
        if new_role == 'trainer' and old_role != 'trainer':
            # Create trainer profile if it doesn't exist
            trainer, created = Trainer.objects.get_or_create(
                user=user,
                defaults={
                    'specialization': 'General',
                    'experience_years': 1,
                    'is_active': True,
                    'phone': profile.phone or '',
                    'email': user.email
                }
            )
            if not created:
                trainer.is_active = True
                trainer.save()

        elif old_role == 'trainer' and new_role != 'trainer':
            # Deactivate trainer profile
            if hasattr(user, 'trainer'):
                trainer = user.trainer
                trainer.is_active = False
                trainer.save()

        messages.success(request, f'Role updated for {user.get_full_name()}!')
        return redirect('team_management')

    return redirect('team_management')