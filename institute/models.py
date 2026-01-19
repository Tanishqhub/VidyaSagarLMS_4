from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('trainer', 'Trainer'),
        ('student', 'Student'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    department = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role}"


class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    specialization = models.CharField(max_length=200)
    experience_years = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def get_active_batches_count(self):
        return self.batch_set.filter(status='ongoing').count()


class Course(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    total_duration_hours = models.IntegerField(default=120, help_text="Total course duration in hours")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def get_total_topics(self):
        return Topic.objects.filter(module__course=self).count()

    def get_total_modules(self):
        return self.modules.count()


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.name} - {self.name}"

    def get_total_duration(self):
        return sum(topic.duration_hours for topic in self.topics.all())

    def get_topics_count(self):
        return self.topics.count()


class Topic(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_hours = models.IntegerField(default=2, validators=[MinValueValidator(1)])
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.module.name} - {self.name}"


class Batch(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]

    name = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_completion_rate(self):
        total_topics = Topic.objects.filter(module__course=self.course).count()
        if total_topics == 0:
            return 0

        completed_topics = TopicProgress.objects.filter(
            batch=self,
            completed=True
        ).count()

        return round((completed_topics / total_topics) * 100, 2)


class TopicProgress(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['batch', 'topic']

    def __str__(self):
        return f"{self.batch.name} - {self.topic.name}"