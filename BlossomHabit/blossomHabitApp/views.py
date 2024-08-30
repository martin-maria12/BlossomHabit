import base64
import io
import os
import os.path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from datetime import datetime, timedelta
from PIL import Image
from urllib.parse import unquote
from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q, Count
from django.views import View

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from matplotlib.ticker import MaxNLocator
from django.core.paginator import Paginator

from .forms import UserLoginForm, SignupForm, CategoryForm, ActivityForm, ActivityPopupForm
from .models import Category, Activity, Emojiii, Journall, Avatar, AvatarHair, AvatarEyes, AvatarMouth

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def compare_dates(activity_start, activity_end, current_time):
    
    start_time = activity_start
    end_time = activity_end
    current_time = current_time.time() 
    
    if start_time <= end_time:
        return start_time <= current_time <= end_time
    else:
        return start_time <= current_time or current_time <= end_time

@login_required
def homepage(request):
    current_date = timezone.localtime(timezone.now()).date()
    current_time = timezone.localtime(timezone.now())     

    today_activities = Activity.objects.filter(
        user=request.user, 
        date=current_time.date()
    )

    print(f"Found {today_activities.count()} activities for today.")
    for activity in today_activities:
        print(f"Activity: {activity.activity_name}, start time: {activity.start_time}, end time: {activity.end_time}")
        if compare_dates(activity.start_time, activity.end_time, current_time):
            print(f"Activity '{activity.activity_name}' is in progress, changing state")
            if activity.state != 'completed' and activity.state != 'canceled':
                activity.state = 'progress'
        else:
            print(f"Activity '{activity.activity_name}' is not in progress")
            if activity.state == 'progress':
                activity.state = 'planned'
        activity.save()

    activities = Activity.objects.filter(
        date=current_date,
        user=request.user
    ).order_by('start_time')

    context = {
        'activities': activities,
        'has_activities_today': activities.exists()
    }
    
    return render(request, 'homepage.html', context)

@login_required
def calendar(request):
    activities = Activity.objects.filter(user=request.user)
    activity_list = []
    for activity in activities:
        activity_list.append({
            'title': activity.activity_name,
            'start': f'{activity.date}T{activity.start_time}',
            'end': f'{activity.date}T{activity.end_time}',
            'backgroundColor': activity.category.color,
            'category': activity.category.category_name,
            'notes': activity.notes or 'undefined',
        })
    context = {
        'activities': activity_list
    }
    return render(request, 'calendar.html', context)

@login_required
def calendar_date(request, selected_date):
    dateSel = datetime.strptime(selected_date, '%Y-%m-%d').date()
    activities = Activity.objects.filter(user=request.user, date=dateSel).order_by('start_time')
    activity_list = []
    for activity in activities:
        start_time = activity.start_time.strftime('%H:%M')
        duration = (datetime.combine(datetime.min, activity.end_time) - datetime.combine(datetime.min, activity.start_time)).seconds // 60
        duration_str = f'{duration // 60}h {duration % 60}m'
        activity_list.append({
            'start_time': start_time,
            'activity_name': activity.activity_name,
            'duration': duration_str,
            'color': activity.category.color,
        })

    completed = activities.filter(state='completed').count()
    canceled = activities.filter(state='canceled').count()
    planned = activities.filter(state='planned').count()
    progress = activities.filter(state='progress').count()

    if not activities.exists():
        pie_chart = None
        bar_chart = None
    else:
        pie_chart = generate_calendar_pie_chart(completed, canceled, planned, progress)
        bar_chart = generate_calendar_bar_chart(request.user, dateSel)

    journal_entry = Journall.objects.filter(user=request.user, Date=dateSel).first()
    journal_text = journal_entry.Text if journal_entry else None
    journal_image = journal_entry.Image.url if journal_entry and journal_entry.Image else None
    journal_emojis = journal_entry.Emojis.all() if journal_entry else None

    context = {
        'selected_date': selected_date,
        'activities': activity_list,
        'pie_chart': pie_chart,
        'bar_chart': bar_chart,
        'journal_text': journal_text,
        'journal_image': journal_image,
        'journal_emojis': journal_emojis,
    }
    return render(request, 'calendar_date.html', context)

def generate_calendar_pie_chart(completed, canceled, planned, progress):
    sizes = [completed, canceled, planned, progress]
    if sum(sizes) == 0:
        return None

    colors = ['#9b8b1a', '#b32222', '#e9785e', '#eba034']

    fig, ax = plt.subplots(figsize=(4, 4))
    wedges, _, autotexts = ax.pie(sizes, colors=colors, startangle=140, autopct=lambda p: '{:.1f}%'.format(p), pctdistance=0.85)

    for i, text in enumerate(autotexts):
        text.set_text(f'{sizes[i]} ({text.get_text()})')

    for i, wedge in enumerate(wedges):
        wedge.set_gid(f'slice_{i}')
        ax.texts[i].set_gid(f'autotext_{i}')
    
    ax.axis('equal')

    ax.set_facecolor('none')
    fig.set_facecolor('none')
    buf = BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    plt.close(fig)
    buf.seek(0)
    image_png = buf.getvalue()
    buf.close()

    return base64.b64encode(image_png).decode('utf-8')

def generate_calendar_bar_chart(user, current_date):
    activities = Activity.objects.filter(user=user, date=current_date).values('category__category_name', 'state').annotate(count=Count('id'))
    categories = Category.objects.filter(Q(user=user) | Q(user__isnull=True)).values_list('category_name', flat=True)

    all_states = ['Completed', 'Canceled', 'Planned', 'Progress']
    data = {category: {state: 0 for state in all_states} for category in categories}

    for activity in activities:
        category = activity['category__category_name']
        state = activity['state']
        count = activity['count']
        data[category][state.capitalize()] += count

    labels = list(data.keys())
    if all(value == 0 for counts in data.values() for value in counts.values()):
        return None

    completed_counts = [data[category]['Completed'] for category in labels]
    canceled_counts = [data[category]['Canceled'] for category in labels]
    planned_counts = [data[category]['Planned'] for category in labels]
    progress_counts = [data[category]['Progress'] for category in labels]

    x = range(len(labels))

    width_px = 700 
    height_px = 400
    dpi = 100
    width_inch = width_px / dpi
    height_inch = height_px / dpi

    fig, ax = plt.subplots(figsize=(width_inch, height_inch))
    bar_width = 0.2
    ax.bar([p - bar_width*1.5 for p in x], completed_counts, width=bar_width, label='Completed', color='#9b8b1a')
    ax.bar([p - bar_width*0.5 for p in x], canceled_counts, width=bar_width, label='Canceled', color='#b32222')
    ax.bar([p + bar_width*0.5 for p in x], planned_counts, width=bar_width, label='Planned', color='#e9785e')
    ax.bar([p + bar_width*1.5 for p in x], progress_counts, width=bar_width, label='Progress', color='#eba034')

    ax.set_xlabel('Categories')
    ax.set_ylabel('Number of Activities')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45)
    ax.legend()

    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    plt.tight_layout()
    ax.set_facecolor('none')
    fig.set_facecolor('none')
    buf = BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    plt.close(fig)
    buf.seek(0)
    image_png = buf.getvalue()
    buf.close()

    return base64.b64encode(image_png).decode('utf-8')

@login_required
def new_activity(request):
    user_categories = Category.objects.filter(user=request.user).exclude(category_name="Google Calendar")
    default_categories = Category.objects.filter(user__isnull=True).exclude(category_name="Google Calendar")
    available_categories = user_categories | default_categories

    if request.method == 'POST':
        form = ActivityForm(request.POST)
        form.fields['category'].queryset = available_categories
        if form.is_valid():
            new_activity = form.save(commit=False)
            overlapping_activities = Activity.objects.filter(
                user=request.user,
                date=new_activity.date,
                end_time__gt=new_activity.start_time,
                start_time__lt=new_activity.end_time,
            )
            if overlapping_activities.exists():
                form.add_error(None, 'There is an overlap of activities')
            else:
                new_activity.user = request.user
                new_activity.save()
                return redirect('homepage')
        else:
            print(form.errors)
    else:
        form = ActivityForm()
        form.fields['category'].queryset = available_categories

    return render(request, 'new_activity.html', {'form': form})

@login_required
def categories(request):
    user_categories = Category.objects.filter(user=request.user) 
    standard_categories = Category.objects.filter(user__isnull=True)
    all_categories = user_categories | standard_categories

    context = {
        'categories': all_categories,
        'messages': messages.get_messages(request),
    }
    
    return render(request, 'categories.html', context)

@login_required
def statistics(request):
    return render(request, 'statistics.html')

@login_required
def category(request):
    category_name = request.GET.get('category', 'Default Category')
    
    categories = Category.objects.filter(Q(user=request.user) | Q(user__isnull=True))
    category = get_object_or_404(categories, category_name=category_name)
    
    activities = Activity.objects.filter(category=category, user=request.user).order_by('date', 'start_time')

    paginator = Paginator(activities, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category_name': category_name,
        'category': category,
        'categories': categories,
        'activities': activities,
        'page_obj': page_obj,
        'messages': messages.get_messages(request),
    }
    return render(request, 'category.html', context)

@login_required
def edit_category(request):
    if request.method == 'POST':
        old_category_name = request.POST['old_category_name']
        new_category_name = request.POST['new_category_name']

        if Category.objects.filter(category_name=new_category_name, user=request.user).exists():
            messages.error(request, 'This category already exists for you.')
            return redirect('categories')

        category = Category.objects.filter(category_name=old_category_name, user=request.user).first()
        if category:
            category.category_name = new_category_name
            category.save()
            messages.success(request, 'Category name updated successfully!')
        else:
            messages.error(request, 'This category cannot be updated')
    return redirect('categories')

@login_required
def delete_category(request, category_id):
    try:
        category = get_object_or_404(Category, id=category_id, user=request.user)

        if Activity.objects.filter(category=category).exists():
            messages.error(request, 'Category cannot be deleted because it contains activities')
            return redirect('categories')

        category.delete()
        messages.success(request, 'Category deleted successfully!')
    except Exception as e:
        messages.error(request, 'This category cannot be deleted')
    return redirect('categories')

@login_required
def add_new_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, user=request.user)
        if form.is_valid():
            new_category = form.save(commit=False)
            new_category.user = request.user
            new_category.save()
            messages.success(request, 'Category added successfully!')
            return redirect('categories')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CategoryForm(user=request.user)
    return render(request, 'add_new_category.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('homepage')
    
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        #print(form.is_valid())
        #print(form.errors)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('homepage')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    #print(request.method)

    old_msg = messages.get_messages(request)
    for msg in old_msg:
        pass

    return render(request, 'login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = SignupForm(data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignupForm()

    old_msg = messages.get_messages(request)
    for msg in old_msg:
        pass

    return render(request, 'register.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def complete_activity(request, activity_id):
    activity = get_object_or_404(Activity, pk=activity_id, user=request.user)
    activity.state = 'completed'
    activity.save()
    return redirect('homepage')

@login_required
def cancel_activity(request, activity_id):
    activity = get_object_or_404(Activity, pk=activity_id, user=request.user)
    activity.state = 'canceled'
    activity.save()
    return redirect('homepage')

def get_emojis(request):
    emojis = Emojiii.objects.all()
    data = [{'id': emoji.id, 'image_url': request.build_absolute_uri(emoji.image.url), 'status': emoji.status} for emoji in emojis]
    return JsonResponse({'emojis': data})

@login_required
def journal(request):
    date_today = datetime.now().date()
    journal_entry = Journall.objects.filter(Date=date_today, user=request.user).first()
    text_left = ""
    text_right = ""

    if journal_entry:
        full_text = journal_entry.Text
        text_left = full_text[:700]
        text_right = full_text[701:]

    if request.method == 'POST':
        date_str = request.POST.get('date')
        new_text = request.POST.get('text')
        emojis = request.POST.get('emojis')
        image_data = request.POST.get('image')

        messages_list = []

        try:
            date = datetime.strptime(date_str, '%d.%m.%Y').date()
        except ValueError:
            messages_list.append('Invalid date format. Date must be in DD.MM.YYYY format.')
            return render(request, 'journal.html', {'messages': messages_list, 'journal_entry': journal_entry, 'text_left': text_left, 'text_right': text_right})

        existing_entry = Journall.objects.filter(Date=date, user=request.user).first()
        if existing_entry:
            existing_entry.Text = new_text
            if emojis:
                existing_entry.Emojis.clear()
                emoji_ids = emojis.split(',')
                for emoji_id in emoji_ids:
                    try:
                        emoji = Emojiii.objects.get(id=emoji_id)
                        existing_entry.Emojis.add(emoji)
                    except Emojiii.DoesNotExist:
                        messages_list.append(f"Emoji with id {emoji_id} does not exist.")
                        return render(request, 'journal.html', {'messages': messages_list, 'journal_entry': journal_entry, 'text_left': text_left, 'text_right': text_right})
            if image_data:
                image = base64.b64decode(image_data.split(',')[1])
                existing_entry.Image = InMemoryUploadedFile(
                    io.BytesIO(image), None, f'image_{date_str}.jpg', 'image/jpeg',
                    len(image), None
                )
            existing_entry.save()
            messages_list.append('Journal entry saved successfully!')
            messages.success(request, 'Journal entry saved successfully!')
            return redirect('journal')
        else:
            journal_entry = Journall.objects.create(
                Date=date,
                Text=new_text,
                user=request.user
            )
            if emojis:
                emoji_ids = emojis.split(',')
                for emoji_id in emoji_ids:
                    try:
                        emoji = Emojiii.objects.get(id=emoji_id)
                        journal_entry.Emojis.add(emoji)
                    except Emojiii.DoesNotExist:
                        messages_list.append(f"Emoji with id {emoji_id} does not exist.")
                        return render(request, 'journal.html', {'messages': messages_list, 'journal_entry': journal_entry, 'text_left': text_left, 'text_right': text_right})
            if image_data:
                image = base64.b64decode(image_data.split(',')[1])
                journal_entry.Image = InMemoryUploadedFile(
                    io.BytesIO(image), None, f'image_{date_str}.jpg', 'image/jpeg',
                    len(image), None
                )
            journal_entry.save()
            messages_list.append('Journal entry saved successfully!')
            messages.success(request, 'Journal entry saved successfully!')
            return redirect('journal')
    else:
        messages_list = messages.get_messages(request)
        return render(request, 'journal.html', {'messages': messages_list, 'journal_entry': journal_entry, 'text_left': text_left, 'text_right': text_right})
    
@login_required
def edit_activity(request):
    if request.method == 'POST':
        activity_id = request.POST.get('activity_id')
        activity = get_object_or_404(Activity, id=activity_id, user=request.user)
        
        form = ActivityPopupForm(request.POST, instance=activity, user=request.user)
        if form.is_valid():
            edited_activity = form.save(commit=False)
            overlapping_activities = Activity.objects.filter(
                user=request.user,
                date=edited_activity.date,
                end_time__gt=edited_activity.start_time,
                start_time__lt=edited_activity.end_time,
            ).exclude(id=activity_id)
            if overlapping_activities.exists():
                form.add_error(None, 'There is an overlap of activities')
            else:
                edited_activity.save()
                messages.success(request, 'Activity updated successfully!')
                return redirect('categories')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect('categories')
    else:
        activity_id = request.GET.get('activity_id')
        activity = get_object_or_404(Activity, id=activity_id, user=request.user)
        form = ActivityPopupForm(instance=activity, user=request.user)
        user_categories = Category.objects.filter(user=request.user).exclude(category_name="Google Calendar")
        default_categories = Category.objects.filter(user__isnull=True).exclude(category_name="Google Calendar")
        categories = user_categories | default_categories
        return render(request, 'edit_activity.html', {'form': form, 'activity_id': activity_id, 'categories': categories})

@login_required
def delete_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id, user=request.user)
    activity.delete()
    messages.success(request, 'Activity deleted successfully!')
    return redirect('categories')

@login_required
def s_of_the_day(request):
    current_date = timezone.localtime(timezone.now()).date()
    activity_counts = Activity.objects.filter(date=current_date, user=request.user).values('state').annotate(count=Count('state'))

    completed_count = next((item['count'] for item in activity_counts if item['state'] == 'completed'), 0)
    canceled_count = next((item['count'] for item in activity_counts if item['state'] == 'canceled'), 0)
    planned_count = next((item['count'] for item in activity_counts if item['state'] == 'planned'), 0)
    progress_count = next((item['count'] for item in activity_counts if item['state'] == 'progress'), 0)

    pie_chart = generate_pie_chart(completed_count, canceled_count, planned_count, progress_count)
    bar_chart = generate_bar_chart(request.user, current_date)

    context = {
        'completed_count': completed_count,
        'canceled_count': canceled_count,
        'planned_count': planned_count,
        'progress_count': progress_count,
        'pie_chart': pie_chart,
        'bar_chart': bar_chart,
        'has_activities': bool(activity_counts)
    }

    return render(request, 's_of_the_day.html', context)

@login_required
def s_of_the_week(request):
    current_date = timezone.localtime(timezone.now()).date()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    activity_counts = Activity.objects.filter(
        user=request.user,
        date__range=[start_of_week, end_of_week]
    ).values('state').annotate(count=Count('state'))

    completed_count = next((item['count'] for item in activity_counts if item['state'] == 'completed'), 0)
    canceled_count = next((item['count'] for item in activity_counts if item['state'] == 'canceled'), 0)
    planned_count = next((item['count'] for item in activity_counts if item['state'] == 'planned'), 0)
    progress_count = next((item['count'] for item in activity_counts if item['state'] == 'progress'), 0)

    pie_chart = generate_pie_chart2(completed_count, canceled_count, planned_count, progress_count)
    bar_chart = generate_bar_chart2(request.user, start_of_week, end_of_week)

    context = {
        'completed_count': completed_count,
        'canceled_count': canceled_count,
        'planned_count': planned_count,
        'progress_count': progress_count,
        'pie_chart': pie_chart,
        'bar_chart': bar_chart,
        'has_activities': bool(activity_counts)
    }

    return render(request, 's_of_the_week.html', context)

@login_required
def s_of_the_month(request):
    current_date = timezone.localtime(timezone.now()).date()
    start_of_month = current_date.replace(day=1)
    next_month = start_of_month + timedelta(days=32)
    end_of_month = next_month.replace(day=1) - timedelta(days=1)

    activity_counts = Activity.objects.filter(
        user=request.user,
        date__range=[start_of_month, end_of_month]
    ).values('state').annotate(count=Count('state'))

    completed_count = next((item['count'] for item in activity_counts if item['state'] == 'completed'), 0)
    canceled_count = next((item['count'] for item in activity_counts if item['state'] == 'canceled'), 0)
    planned_count = next((item['count'] for item in activity_counts if item['state'] == 'planned'), 0)
    progress_count = next((item['count'] for item in activity_counts if item['state'] == 'progress'), 0)

    pie_chart = generate_pie_chart3(completed_count, canceled_count, planned_count, progress_count)
    bar_chart = generate_bar_chart3(request.user, start_of_month, end_of_month)

    context = {
        'completed_count': completed_count,
        'canceled_count': canceled_count,
        'planned_count': planned_count,
        'progress_count': progress_count,
        'pie_chart': pie_chart,
        'bar_chart': bar_chart,
        'has_activities': bool(activity_counts)
    }

    return render(request, 's_of_the_month.html', context)

def generate_pie_chart(completed, canceled, planned, progress):
    sizes = [completed, canceled, planned, progress]
    if sum(sizes) == 0:
        return None

    colors = ['#9b8b1a', '#b32222', '#e9785e', '#eba034']

    fig, ax = plt.subplots(figsize=(4, 4))
    wedges, _, autotexts = ax.pie(sizes, colors=colors, startangle=140, autopct=lambda p: '{:.1f}%'.format(p), pctdistance=0.85)

    for i, text in enumerate(autotexts):
        text.set_text(f'{sizes[i]} ({text.get_text()})')

    for i, wedge in enumerate(wedges):
        wedge.set_gid(f'slice_{i}')
        ax.texts[i].set_gid(f'autotext_{i}')
    
    ax.axis('equal')

    ax.set_facecolor('none')
    fig.set_facecolor('none')
    buf = BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    plt.close(fig)
    buf.seek(0)
    image_png = buf.getvalue()
    buf.close()

    return base64.b64encode(image_png).decode('utf-8')

def generate_bar_chart(user, current_date):
    activities = Activity.objects.filter(user=user, date=current_date).values('category__category_name', 'state').annotate(count=Count('id'))
    categories = Category.objects.filter(Q(user=user) | Q(user__isnull=True)).values_list('category_name', flat=True)

    all_states = ['Completed', 'Canceled', 'Planned', 'Progress']
    data = {category: {state: 0 for state in all_states} for category in categories}

    for activity in activities:
        category = activity['category__category_name']
        state = activity['state']
        count = activity['count']
        data[category][state.capitalize()] += count

    labels = list(data.keys())
    if all(value == 0 for counts in data.values() for value in counts.values()):
        return None

    completed_counts = [data[category]['Completed'] for category in labels]
    canceled_counts = [data[category]['Canceled'] for category in labels]
    planned_counts = [data[category]['Planned'] for category in labels]
    progress_counts = [data[category]['Progress'] for category in labels]

    x = range(len(labels))

    width_px = 1000
    height_px = 500
    dpi = 100
    width_inch = width_px / dpi
    height_inch = height_px / dpi

    fig, ax = plt.subplots(figsize=(width_inch, height_inch))
    bar_width = 0.2
    ax.bar([p - bar_width*1.5 for p in x], completed_counts, width=bar_width, label='Completed', color='#9b8b1a')
    ax.bar([p - bar_width*0.5 for p in x], canceled_counts, width=bar_width, label='Canceled', color='#b32222')
    ax.bar([p + bar_width*0.5 for p in x], planned_counts, width=bar_width, label='Planned', color='#e9785e')
    ax.bar([p + bar_width*1.5 for p in x], progress_counts, width=bar_width, label='Progress', color='#eba034')

    ax.set_xlabel('Categories')
    ax.set_ylabel('Number of Activities')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45)
    ax.legend(loc='upper left', bbox_to_anchor=(1,1))

    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    plt.tight_layout(rect=[0, 0, 0.85, 1])
    ax.set_facecolor('none')
    fig.set_facecolor('none')
    buf = BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    plt.close(fig)
    buf.seek(0)
    image_png = buf.getvalue()
    buf.close()

    return base64.b64encode(image_png).decode('utf-8')

def generate_pie_chart2(completed, canceled, planned, progress):
    sizes = [completed, canceled, planned, progress]
    if sum(sizes) == 0:
        return None

    colors = ['#9b8b1a', '#b32222', '#e9785e', '#eba034']

    fig, ax = plt.subplots(figsize=(4, 4))
    wedges, _, autotexts = ax.pie(sizes, colors=colors, startangle=140, autopct=lambda p: '{:.1f}%'.format(p), pctdistance=0.85)

    for i, text in enumerate(autotexts):
        text.set_text(f'{sizes[i]} ({text.get_text()})')

    for i, wedge in enumerate(wedges):
        wedge.set_gid(f'slice_{i}')
        ax.texts[i].set_gid(f'autotext_{i}')
    
    ax.axis('equal')

    ax.set_facecolor('none')
    fig.set_facecolor('none')
    buf = BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    plt.close(fig)
    buf.seek(0)
    image_png = buf.getvalue()
    buf.close()

    return base64.b64encode(image_png).decode('utf-8')

def generate_bar_chart2(user, start_date, end_date):
    activities = Activity.objects.filter(user=user, date__range=[start_date, end_date]).values('category__category_name', 'state').annotate(count=Count('id'))
    categories = Category.objects.filter(Q(user=user) | Q(user__isnull=True)).values_list('category_name', flat=True)

    all_states = ['Completed', 'Canceled', 'Planned', 'Progress']
    data = {category: {state: 0 for state in all_states} for category in categories}

    for activity in activities:
        category = activity['category__category_name']
        state = activity['state']
        count = activity['count']
        data[category][state.capitalize()] += count

    labels = list(data.keys())
    if all(value == 0 for counts in data.values() for value in counts.values()):
        return None

    completed_counts = [data[category]['Completed'] for category in labels]
    canceled_counts = [data[category]['Canceled'] for category in labels]
    planned_counts = [data[category]['Planned'] for category in labels]
    progress_counts = [data[category]['Progress'] for category in labels]

    x = range(len(labels))

    width_px = 1000
    height_px = 500
    dpi = 100
    width_inch = width_px / dpi
    height_inch = height_px / dpi

    fig, ax = plt.subplots(figsize=(width_inch, height_inch))
    bar_width = 0.2
    ax.bar([p - bar_width*1.5 for p in x], completed_counts, width=bar_width, label='Completed', color='#9b8b1a')
    ax.bar([p - bar_width*0.5 for p in x], canceled_counts, width=bar_width, label='Canceled', color='#b32222')
    ax.bar([p + bar_width*0.5 for p in x], planned_counts, width=bar_width, label='Planned', color='#e9785e')
    ax.bar([p + bar_width*1.5 for p in x], progress_counts, width=bar_width, label='Progress', color='#eba034')

    ax.set_xlabel('Categories')
    ax.set_ylabel('Number of Activities')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45)
    ax.legend(loc='upper left', bbox_to_anchor=(1,1))

    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    plt.tight_layout(rect=[0, 0, 0.85, 1]) 
    ax.set_facecolor('none')
    fig.set_facecolor('none')
    buf = BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    plt.close(fig)
    buf.seek(0)
    image_png = buf.getvalue()
    buf.close()

    return base64.b64encode(image_png).decode('utf-8')

def generate_pie_chart3(completed, canceled, planned, progress):
    sizes = [completed, canceled, planned, progress]
    if sum(sizes) == 0:
        return None

    colors = ['#9b8b1a', '#b32222', '#e9785e', '#eba034']

    fig, ax = plt.subplots(figsize=(4, 4))
    wedges, _, autotexts = ax.pie(sizes, colors=colors, startangle=140, autopct=lambda p: '{:.1f}%'.format(p), pctdistance=0.85)

    for i, text in enumerate(autotexts):
        text.set_text(f'{sizes[i]} ({text.get_text()})')

    for i, wedge in enumerate(wedges):
        wedge.set_gid(f'slice_{i}')
        ax.texts[i].set_gid(f'autotext_{i}')
    
    ax.axis('equal')

    ax.set_facecolor('none')
    fig.set_facecolor('none')
    buf = BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    plt.close(fig)
    buf.seek(0)
    image_png = buf.getvalue()
    buf.close()

    return base64.b64encode(image_png).decode('utf-8')

def generate_bar_chart3(user, start_date, end_date):
    activities = Activity.objects.filter(user=user, date__range=[start_date, end_date]).values('category__category_name', 'state').annotate(count=Count('id'))
    categories = Category.objects.filter(Q(user=user) | Q(user__isnull=True)).values_list('category_name', flat=True)

    all_states = ['Completed', 'Canceled', 'Planned', 'Progress']
    data = {category: {state: 0 for state in all_states} for category in categories}

    for activity in activities:
        category = activity['category__category_name']
        state = activity['state']
        count = activity['count']
        data[category][state.capitalize()] += count

    labels = list(data.keys())
    if all(value == 0 for counts in data.values() for value in counts.values()):
        return None

    completed_counts = [data[category]['Completed'] for category in labels]
    canceled_counts = [data[category]['Canceled'] for category in labels]
    planned_counts = [data[category]['Planned'] for category in labels]
    progress_counts = [data[category]['Progress'] for category in labels]

    x = range(len(labels))

    width_px = 1000
    height_px = 500
    dpi = 100
    width_inch = width_px / dpi
    height_inch = height_px / dpi

    fig, ax = plt.subplots(figsize=(width_inch, height_inch))
    bar_width = 0.2
    ax.bar([p - bar_width*1.5 for p in x], completed_counts, width=bar_width, label='Completed', color='#9b8b1a')
    ax.bar([p - bar_width*0.5 for p in x], canceled_counts, width=bar_width, label='Canceled', color='#b32222')
    ax.bar([p + bar_width*0.5 for p in x], planned_counts, width=bar_width, label='Planned', color='#e9785e')
    ax.bar([p + bar_width*1.5 for p in x], progress_counts, width=bar_width, label='Progress', color='#eba034')

    ax.set_xlabel('Categories')
    ax.set_ylabel('Number of Activities')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45)
    ax.legend(loc='upper left', bbox_to_anchor=(1,1))

    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    plt.tight_layout(rect=[0, 0, 0.85, 1])
    ax.set_facecolor('none')
    fig.set_facecolor('none')
    buf = BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    plt.close(fig)
    buf.seek(0)
    image_png = buf.getvalue()
    buf.close()

    return base64.b64encode(image_png).decode('utf-8')

@login_required
def profile(request):
    avatar = Avatar.objects.filter(user=request.user).first()
    return render(request, 'profile.html', {'avatar': avatar})

def customize_avatar(request):
    avatar, created = Avatar.objects.get_or_create(user=request.user)

    eyes = AvatarEyes.objects.all()
    hairs = AvatarHair.objects.all()
    mouths = AvatarMouth.objects.all()

    if request.method == 'POST':
        eyes_url = request.POST.get('eyes')
        hair_url = request.POST.get('hair')
        mouth_url = request.POST.get('mouth')

        base_image_path = os.path.join(settings.MEDIA_ROOT, 'imagini/avatar/base.png')
        base_image = Image.open(base_image_path).convert("RGBA")

        def open_and_resize_image(path, size):
            component = Image.open(path).convert("RGBA")
            return component.resize(size, Image.Resampling.LANCZOS)

        def paste_component(base_image, component, x, y):
            base_image.paste(component, (x, y), component)

        if eyes_url:
            eyes_path = os.path.join(unquote(eyes_url.lstrip('/')))
            if 'eyes1' in eyes_url:
                eyes_image = open_and_resize_image(eyes_path, (100, 40))
                eyes_x = 110
                eyes_y = 100
            elif 'eyes2' in eyes_url:
                eyes_image = open_and_resize_image(eyes_path, (92, 62))
                eyes_x = 110
                eyes_y = 90
            elif 'eyes3' in eyes_url:
                eyes_image = open_and_resize_image(eyes_path, (142, 87))
                eyes_x = 88
                eyes_y = 83
            elif 'eyes4' in eyes_url:
                eyes_image = open_and_resize_image(eyes_path, (125, 32))
                eyes_x = 100
                eyes_y = 110
            paste_component(base_image, eyes_image, eyes_x, eyes_y)

        if hair_url:
            hair_path = os.path.join(unquote(hair_url.lstrip('/')))
            if 'hair1' in hair_url:
                hair_image = open_and_resize_image(hair_path, (180, 167))
                hair_x = 68
                hair_y = 35
            elif 'hair2' in hair_url:
                hair_image = open_and_resize_image(hair_path, (165, 137))
                hair_x = 73
                hair_y = 36
            elif 'hair3' in hair_url:
                hair_image = open_and_resize_image(hair_path, (244, 230))
                hair_x = 40
                hair_y = 0
            elif 'hair4' in hair_url:
                hair_image = open_and_resize_image(hair_path, (316, 311))
                hair_x = 2
                hair_y = 50
            elif 'hair5' in hair_url:
                hair_image = open_and_resize_image(hair_path, (212, 348))
                hair_x = 50
                hair_y = 16
            elif 'hair6' in hair_url:
                hair_image = open_and_resize_image(hair_path, (209, 226))
                hair_x = 50
                hair_y = 10
            paste_component(base_image, hair_image, hair_x, hair_y)

        if mouth_url:
            mouth_path = os.path.join(unquote(mouth_url.lstrip('/')))
            if 'mouth1' in mouth_url:
                mouth_image = open_and_resize_image(mouth_path, (55, 25))
                mouth_x = 135
                mouth_y = 180
            elif 'mouth2' in mouth_url:
                mouth_image = open_and_resize_image(mouth_path, (80, 30))
                mouth_x = 120
                mouth_y = 180
            elif 'mouth3' in mouth_url:
                mouth_image = open_and_resize_image(mouth_path, (50, 25))
                mouth_x = 135
                mouth_y = 180
            elif 'mouth4' in mouth_url:
                mouth_image = open_and_resize_image(mouth_path, (45, 20))
                mouth_x = 135
                mouth_y = 180
            elif 'mouth5' in mouth_url:
                mouth_image = open_and_resize_image(mouth_path, (30, 25))
                mouth_x = 143
                mouth_y = 180
            paste_component(base_image, mouth_image, mouth_x, mouth_y)

        buffer = io.BytesIO()
        base_image.save(buffer, format="PNG")
        avatar_image_file = ContentFile(buffer.getvalue(), "avatar_final.png")

        avatar.eyes = AvatarEyes.objects.filter(img_eyes=unquote(eyes_url).lstrip('/')).first() if eyes_url else None
        avatar.hair = AvatarHair.objects.filter(img_hair=unquote(hair_url).lstrip('/')).first() if hair_url else None
        avatar.mouth = AvatarMouth.objects.filter(img_mouth=unquote(mouth_url).lstrip('/')).first() if mouth_url else None
        
        avatar.imagine_finala.save("avatar_final.png", avatar_image_file)
        avatar.save()

        return redirect('profile')

    context = {
        'eyes': eyes,
        'hairs': hairs,
        'mouths': mouths,
    }

    return render(request, 'customize_avatar.html', context)

@login_required
def details(request):
    user = request.user

    top_category = Category.objects.filter(
        activity__user=user,
        activity__state='completed'
    ).annotate(
        activities_completed=Count('activity')
    ).order_by('-activities_completed').first()

    least_category = Category.objects.filter(
        activity__user=user,
        activity__state='completed'
    ).annotate(
        activities_completed=Count('activity')
    ).order_by('activities_completed').first()

    most_canceled_category = Category.objects.filter(
        activity__user=user,
        activity__state='canceled'
    ).annotate(
        activities_canceled=Count('activity')
    ).order_by('-activities_canceled').first()

    least_canceled_category = Category.objects.filter(
        activity__user=user,
        activity__state='canceled'
    ).annotate(
        activities_canceled=Count('activity')
    ).order_by('activities_canceled').first()

    context = {
        'user': user,
        'top_category': top_category,
        'least_category': least_category,
        'most_canceled_category': most_canceled_category,
        'least_canceled_category': least_canceled_category,
    }

    return render(request, 'details.html', context)

SCOPES = ['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly']

class GoogleCalendarInitView(View):
    def get(self, request, *args, **kwargs):
        flow = InstalledAppFlow.from_client_secrets_file(
            settings.GOOGLE_CLIENT_SECRETS_FILE,
            scopes=SCOPES
        )
        flow.redirect_uri = request.build_absolute_uri('/rest/v1/calendar/redirect')

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
        )

        request.session['state'] = state
        return redirect(authorization_url)

class GoogleCalendarRedirectView(View):
    def get(self, request, *args, **kwargs):
        state = request.GET.get('state')
        flow = InstalledAppFlow.from_client_secrets_file(
            settings.GOOGLE_CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            state=state
        )
        flow.redirect_uri = request.build_absolute_uri('/rest/v1/calendar/redirect')
        authorization_response = request.build_absolute_uri()
        flow.fetch_token(authorization_response=authorization_response)

        credentials = flow.credentials
        request.session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        self.sync_google_calendar_events(request, credentials)

        return redirect('/calendar')

    def sync_google_calendar_events(self, request, credentials):
        service = build('calendar', 'v3', credentials=credentials)
        tstart = (datetime.utcnow() - timedelta(days=365)).isoformat() + 'Z'
        
        events_result = service.events().list(calendarId='primary', timeMin=tstart,
                                              maxResults=3000, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            if 'T' in start:
                start_datetime = datetime.fromisoformat(start)
                start_time = start_datetime.time()
                date = start_datetime.date()
            else:
                start_time = None
                date = start

            if 'T' in end:
                end_datetime = datetime.fromisoformat(end)
                end_time = end_datetime.time()
            else:
                end_time = None

            category, _ = Category.objects.get_or_create(
                category_name='Google Calendar',
                defaults={'color': '#ff5c5c'}
            )

            Activity.objects.get_or_create(
                user=request.user,
                activity_name=event.get('summary', ''),
                date=date,
                start_time=start_time,
                end_time=end_time,
                category=category,
                defaults={'notes': event.get('description', '')}
            )