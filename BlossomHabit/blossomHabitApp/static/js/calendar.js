document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendarID');
    // creare calendar folosind fullcalendar in care afisam unele elemente
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        timeZone: 'Europe/Bucharest',
        height: 'auto',
        events: calendarEvents,
        // functie pentru afisarea activitatilor in calendar
        eventContent: function(info) {
            var backgroundColor = info.event.backgroundColor;
            var borderColor = info.event.borderColor || 'black';
            var innerHtml = '<div style="background-color:' + backgroundColor + '; border: 1px solid ' + borderColor + '; height: 20px; width: 100%;"></div>';
            return { html: innerHtml };
        },
        dateClick: function(info) {
            var selectedDate = info.dateStr;
            window.location.href = `/calendar_date/${selectedDate}/`;
        },
        // afisare informatii pentru cand tinem hover pe o activitate
        eventMouseEnter: function(info) {
            var tooltip = new bootstrap.Tooltip(info.el, {
                title: 'Name: ' + info.event.title + "<br>" + 
                       'Category: ' + (info.event.extendedProps.category || 'undefined') + "<br>" + 
                       'Notes: ' + (info.event.extendedProps.notes || 'undefined'),
                html: true,
                placement: 'top',
                trigger: 'hover',
                container: 'body'
            });
            tooltip.show();
            info.el.tooltipInstance = tooltip;
        },
        eventMouseLeave: function(info) {
           
            if (info.el.tooltipInstance) {
                info.el.tooltipInstance.dispose();
                delete info.el.tooltipInstance;
            }
        },
    });

    calendar.render();
});
