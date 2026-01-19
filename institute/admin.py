from django.contrib import admin
from .models import Course, Module, Topic, Trainer, Batch, TopicProgress


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1
    fields = ['name', 'description', 'duration_hours', 'order']


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    fields = ['name', 'description', 'order']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'total_duration_hours', 'get_total_modules', 'get_total_topics', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    inlines = [ModuleInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'total_duration_hours', 'is_active')
        }),
    )

    def get_total_modules(self, obj):
        return obj.get_total_modules()

    get_total_modules.short_description = 'Modules'

    def get_total_topics(self, obj):
        return obj.get_total_topics()

    get_total_topics.short_description = 'Topics'


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'order', 'get_topics_count', 'get_total_duration']
    list_filter = ['course']
    search_fields = ['name', 'description']
    inlines = [TopicInline]
    ordering = ['course', 'order']

    def get_topics_count(self, obj):
        return obj.get_topics_count()

    get_topics_count.short_description = 'Topics Count'

    def get_total_duration(self, obj):
        return f"{obj.get_total_duration()} hours"

    get_total_duration.short_description = 'Total Duration'


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'module', 'duration_hours', 'order']
    list_filter = ['module__course', 'module']
    search_fields = ['name', 'description']
    ordering = ['module', 'order']


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'phone', 'specialization', 'experience_years', 'is_active',
                    'get_active_batches_count']
    list_filter = ['is_active', 'specialization']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'email', 'specialization']
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'phone', 'email', 'bio')
        }),
        ('Professional Information', {
            'fields': ('specialization', 'experience_years', 'is_active')
        }),
    )

    def get_active_batches_count(self, obj):
        return obj.get_active_batches_count()

    get_active_batches_count.short_description = 'Active Batches'


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'trainer', 'start_date', 'end_date', 'status', 'get_completion_rate']
    list_filter = ['status', 'course', 'trainer']
    search_fields = ['name']
    date_hierarchy = 'start_date'

    def get_completion_rate(self, obj):
        return f"{obj.get_completion_rate()}%"

    get_completion_rate.short_description = 'Completion'


@admin.register(TopicProgress)
class TopicProgressAdmin(admin.ModelAdmin):
    list_display = ['batch', 'topic', 'completed', 'completed_date']
    list_filter = ['completed', 'batch']
    search_fields = ['batch__name', 'topic__name']