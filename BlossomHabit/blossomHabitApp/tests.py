from datetime import date, time
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth.models import User 
from .models import Category, Activity, Emojiii, Journall, AvatarEyes, AvatarHair, AvatarMouth, Avatar
from .forms import CategoryForm
from django.urls import reverse
from django.templatetags.static import static
from django.core.files.uploadedfile import SimpleUploadedFile

class Tests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        
        self.category = Category.objects.create(
            category_name='Work2',
            color='#aa54e8',
            user=self.user
        )
        
        self.activity = Activity.objects.create(
            activity_name='Meeting',
            date=date(2023, 6, 26),
            start_time=time(10, 0),
            end_time=time(12, 0),
            category=self.category,
            user=self.user,
            state='planned'
        )
        
        self.emoji = Emojiii.objects.create(
            image='media/imagini/emoji/cat.png',
            status='cat'
        )
        
        self.journal = Journall.objects.create(
            Date=date(2023, 6, 26),
            Text='This is a test for journal text',
            Image='media/imagini/images_from_journal/image_10.05.2024.jpg',
            user=self.user
        )
        self.journal.Emojis.add(self.emoji)
        
        self.avatar_eyes = AvatarEyes.objects.create(
            img_eyes='media/imagini/avatar/eyes/eyes1_brown.png'
        )
        self.avatar_hair = AvatarHair.objects.create(
            img_hair='media/imagini/avatar/hair/hair6_blonde.png'
        )
        self.avatar_mouth = AvatarMouth.objects.create(
            img_mouth='media/imagini/avatar/mouth/mouth2.png'
        )
        self.avatar = Avatar.objects.create(
            user=self.user,
            imagine_finala='media/avatar/final/avatar_final_QY0AFKh.png'
        )
        self.eye1 = AvatarEyes.objects.create(img_eyes=SimpleUploadedFile(name='eyes1_brown.png', content=b'', content_type='image/png'))

    # teste pentru models

    def test_category_create(self):
        self.assertEqual(self.category.category_name, 'Work2')
        self.assertEqual(self.category.color, '#aa54e8')
        self.assertEqual(self.category.user, self.user)

    def test_activity_create(self):
        self.assertEqual(self.activity.activity_name, 'Meeting')
        self.assertEqual(self.activity.category, self.category)
        self.assertEqual(self.activity.user, self.user)
        self.assertEqual(self.activity.state, 'planned')
        self.assertEqual(self.activity.date, date(2023, 6, 26))
        self.assertEqual(self.activity.start_time, time(10, 0))
        self.assertEqual(self.activity.end_time, time(12, 0))

    def test_emoji_create(self):
        self.assertEqual(self.emoji.status, 'cat')

    def test_journal_create(self):
        self.assertEqual(self.journal.Text, 'This is a test for journal text')
        self.assertEqual(self.journal.user, self.user)
        self.assertIn(self.emoji, self.journal.Emojis.all())

    def test_avatar_create(self):
        self.assertEqual(self.avatar.user, self.user)
        self.assertEqual(self.avatar.imagine_finala, 'media/avatar/final/avatar_final_QY0AFKh.png')

    def test_avatar_eyes_create(self):
        self.assertEqual(self.avatar_eyes.img_eyes, 'media/imagini/avatar/eyes/eyes1_brown.png')

    def test_avatar_hair_create(self):
        self.assertEqual(self.avatar_hair.img_hair, 'media/imagini/avatar/hair/hair6_blonde.png')

    def test_avatar_mouth_create(self):
        self.assertEqual(self.avatar_mouth.img_mouth, 'media/imagini/avatar/mouth/mouth2.png')

    # teste pentru views

    def test_homepage_view(self):
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage.html')

    def test_calendar_view(self):
        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')
        self.assertContains(response, 'Meeting')

    def test_calendar_date_view(self):
        selected_date = '2023-06-26'
        response = self.client.get(reverse('calendar_date', args=[selected_date]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar_date.html')
        self.assertContains(response, 'Meeting')
        self.assertContains(response, 'This is a test for journal text')

    def test_new_activity_view(self):
        response = self.client.get(reverse('new_activity'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'new_activity.html')

    def test_categories_view(self):
        response = self.client.get(reverse('categories'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'categories.html')
        self.assertContains(response, 'Work2')

    def test_category_view(self):
        response = self.client.get(reverse('category'), {'category': 'Work2'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'category.html')
        self.assertContains(response, 'Meeting')

    def test_edit_category_view(self):
        response = self.client.post(reverse('edit_category'), {
            'old_category_name': 'Work2',
            'new_category_name': 'Work2 Updated'
        })
        self.assertEqual(response.status_code, 302)
        self.category.refresh_from_db()
        self.assertEqual(self.category.category_name, 'Work2 Updated')

    def test_delete_category_view(self):
        self.activity.delete()
        response = self.client.post(reverse('delete_category', args=[self.category.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())

    def test_add_new_category_view(self):
        response = self.client.post(reverse('add_new_category'), {
            'category_name': 'New Category Test',
            'color': '#d6872e'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(category_name='New Category Test').exists())

    def test_complete_activity_view(self):
        response = self.client.post(reverse('complete_activity', args=[self.activity.id]))
        self.assertEqual(response.status_code, 302)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.state, 'completed')

    def test_cancel_activity_view(self):
        response = self.client.post(reverse('cancel_activity', args=[self.activity.id]))
        self.assertEqual(response.status_code, 302)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.state, 'canceled')

    def test_profile_view(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')

    def test_customize_avatar_view(self):
        response = self.client.get(reverse('customize_avatar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'customize_avatar.html')
    
    def test_user_logout(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('user_logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))

        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('profile'))
    
    # teste pentru templates si forms

    def test_add_new_category_template(self):
        response = self.client.get(reverse('add_new_category'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_new_category.html')
        self.assertContains(response, '<h2>Add a new category</h2>')
        self.assertContains(response, 'name="category_name"')
        self.assertContains(response, 'name="color"')
        self.assertContains(response, 'type="submit"')

    def test_add_new_category_form_submission(self):
        form_data = {
            'category_name': 'New Category',
            'color': '#ffffff'
        }
        response = self.client.post(reverse('add_new_category'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(category_name='New Category').exists())

    def test_base_template_elements(self):
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base.html')

        self.assertContains(response, '<span class="app-name">BlossomHabit</span>')
        self.assertContains(response, f'<img src="{static("imagini/blossom_icon.png")}" alt="Logo">')

        self.assertContains(response, reverse('homepage'))
        self.assertContains(response, reverse('calendar'))
        self.assertContains(response, reverse('journal'))
        self.assertContains(response, reverse('statistics'))

        self.assertContains(response, reverse('profile'))
        self.assertContains(response, reverse('user_logout'))
        self.assertContains(response, f'<img src="{static("imagini/logout_icon.png")}" alt="Logout Icon" class="logout-icon">')

    def test_calendar_date_view_template(self):
        response = self.client.get(reverse('calendar_date', args=['2023-06-26']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar_date.html')
        
        self.assertContains(response, 'Activities')
        self.assertContains(response, 'Statistics')
        self.assertContains(response, 'Journal')
        self.assertContains(response, 'Image of the Day')
        self.assertContains(response, 'How I Felt Today')
        
        self.assertContains(response, 'Meeting')
        self.assertContains(response, '10:00')
        self.assertContains(response, 'This is a test for journal text')
        
        journal_image_url = self.journal.Image.url
        self.assertContains(response, f'<img src="{journal_image_url}" alt="Journal Image" class="journal-img">')

    def test_customize_avatar_template_elements(self):
        response = self.client.get(reverse('customize_avatar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'customize_avatar.html')

        self.assertContains(response, '<link rel="stylesheet" href="/static/css/customize_avatar.css">')
        self.assertContains(response, '<script src="/static/js/customize_avatar.js"></script>')

        self.assertContains(response, '<img src="/static/imagini/base.png" alt="Avatar">')

        self.assertContains(response, '<form method="post" id="customize-avatar-form">')
        self.assertContains(response, '<button type="submit" class="profile-button save-button">Save Avatar</button>')

        self.assertContains(response, '<button type="button" class="tab-link" onclick="openTab(event, \'all\')">All</button>')
        self.assertContains(response, '<button type="button" class="tab-link" onclick="openTab(event, \'eyes\')">Eyes</button>')

        self.assertContains(response, '<div class="tab-item" style="grid-column: span 5;">')
        self.assertContains(response, '<h3>Eyes</h3>')

        self.assertContains(response, f'<img src="{self.eye1.img_eyes.url}" onclick="selectComponent(\'eyes\', \'{self.eye1.img_eyes.url}\')" class="component-img">')

        self.assertContains(response, '<div id="eyes" class="tab-content">')
        self.assertContains(response, '<div id="hair" class="tab-content">')
        self.assertContains(response, '<div id="mouth" class="tab-content">')

    def test_statistics_template_no_activities(self):
        Activity.objects.all().delete()
        response = self.client.get(reverse('s_of_the_day'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 's_of_the_day.html')

        self.assertContains(response, '<p>There are no activities</p>')

    def test_add_new_category_form_invalid_submission(self):
        form_data = {
            'category_name': '',
            'color': '#12345g'
        }
        response = self.client.post(reverse('add_new_category'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'category_name', 'This field is required.')
        self.assertFormError(response, 'form', 'color', 'Enter a valid color.')

