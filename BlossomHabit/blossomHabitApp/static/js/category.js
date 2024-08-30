document.addEventListener('DOMContentLoaded', function() {
    var editCategoryBtn = document.querySelector('.edit-category');
    var deleteCategoryBtn = document.querySelector('.delete-category');
    var popupCategory = document.getElementById('edit-category-popup');
    var closeCategoryBtn = document.querySelector('.close-popup');

    var editActivityBtns = document.querySelectorAll('.edit-activity');
    var deleteActivityBtns = document.querySelectorAll('.delete-activity');
    var popupActivity = document.getElementById('edit-activity-popup');
    var closeActivityBtn = document.querySelector('.close-popup-act');

    if (editCategoryBtn) {
        editCategoryBtn.addEventListener('click', function() {
            popupCategory.style.display = 'flex';
        });
    }

    if (closeCategoryBtn) {
        closeCategoryBtn.addEventListener('click', function() {
            popupCategory.style.display = 'none';
        });
    }

    if (deleteCategoryBtn) {
        deleteCategoryBtn.addEventListener('click', function(event) {
            var categoryId = this.getAttribute('data-category-id');
            var deleteUrl = this.getAttribute('data-url').replace('/0/', '/' + categoryId + '/');
            if (confirm('Are you sure you want to delete this category?')) {
                window.location.href = deleteUrl;
            }
        });
    }

    editActivityBtns.forEach(function(editBtn) {
        editBtn.addEventListener('click', function() {
            var activityId = this.getAttribute('data-activity-id');
            var activityPostIt = this.closest('.cat-post-it');

            if (!activityPostIt) {
                console.error('Activity post-it not found');
                return;
            }

            var activityNameElement = activityPostIt.querySelector('h2');
            var activityDateElement = activityPostIt.querySelector('.act-date');
            var activityStartTimeElement = activityPostIt.querySelector('li:nth-child(2)');
            var activityEndTimeElement = activityPostIt.querySelector('li:nth-child(3)');
            var activityNotesElement = activityPostIt.querySelector('li:nth-child(5)');
            var activityCategoryElement = activityPostIt.querySelector('li:nth-child(6)');
            var activityStateElement = activityPostIt.querySelector('li:nth-child(7)');

            var activityNameInput = document.getElementById('activity_name');
            var activityDateInput = document.getElementById('activity_date');
            var startTimeInput = document.getElementById('start_time');
            var endTimeInput = document.getElementById('end_time');
            var notesInput = document.getElementById('notes');
            var categorySelect = document.getElementById('category');
            var stateSelect = document.getElementById('state');
            var activityIdInput = document.getElementById('activity_id');

            // verificam daca exista elementul html si daca exista elementul in formular
            // daca exista transferam continutul in formularul din popup
            if (activityNameElement && activityNameInput) {
                activityNameInput.value = activityNameElement.textContent.trim();
            }

            if (activityDateElement && activityDateInput) {
                activityDateInput.value = activityDateElement.textContent.trim();
            }

            if (activityStartTimeElement && startTimeInput) {
                startTimeInput.value = activityStartTimeElement.textContent.replace('Begins: ', '').trim();
            }

            if (activityEndTimeElement && endTimeInput) {
                endTimeInput.value = activityEndTimeElement.textContent.replace('Ends: ', '').trim();
            }

            if (activityNotesElement && notesInput) {
                notesInput.value = activityNotesElement.textContent.replace('Notes: ', '').trim();
            } else if (notesInput) {
                notesInput.value = '';
            }

            if (activityCategoryElement && categorySelect) {
                for (var i = 0; i < categorySelect.options.length; i++) {
                    if (categorySelect.options[i].text === activityCategoryElement.textContent.trim()) {
                        categorySelect.selectedIndex = i;
                        break;
                    }
                }
            }

            if (activityStateElement && stateSelect) {
                for (var i = 0; i < stateSelect.options.length; i++) {
                    if (stateSelect.options[i].text.toLowerCase() === activityStateElement.textContent.replace('Status: ', '').trim().toLowerCase()) {
                        stateSelect.selectedIndex = i;
                        break;
                    }
                }
            }

            if (activityIdInput) {
                activityIdInput.value = activityId;
            }

            if (popupActivity) {
                popupActivity.style.display = 'flex';
            }
        });
    });

    if (closeActivityBtn) {
        closeActivityBtn.addEventListener('click', function() {
            if (popupActivity) {
                popupActivity.style.display = 'none';
            }
        });
    }

    deleteActivityBtns.forEach(function(deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            var activityId = this.getAttribute('data-activity-id');
            var deleteUrl = this.getAttribute('data-url').replace('/0/', '/' + activityId + '/');
            if (confirm('Are you sure you want to delete this activity?')) {
                window.location.href = deleteUrl;
            }
        });
    });
});
