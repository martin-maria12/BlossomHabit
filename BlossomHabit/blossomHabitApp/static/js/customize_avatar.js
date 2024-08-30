function openTab(event, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tab-link");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "grid";
    event.currentTarget.className += " active";
}

function selectComponent(type, url) {
    var preview = document.getElementById("avatar-preview");

    var oldComponents = preview.querySelectorAll("img[data-type='" + type + "']");
    oldComponents.forEach(function(component) {
        preview.removeChild(component);
    });

    var img = document.createElement("img");
    img.src = url;
    img.setAttribute("data-type", type);
    img.style.position = "absolute";
    img.style.transform = "translate(-50%, -50%)";

    
    if (url.includes("eyes") || url.includes("mouth")){
        img.style.zIndex = "100";
    }
    else if (url.includes("hair")){
        img.style.zIndex = "1000";
    }
    
    if (url.includes("eyes1")) {
        img.style.width = "100px";
        img.style.height = "40px";
        img.style.left = "53%";
        img.style.top = "30%";
    } else if (url.includes("eyes2")) {
        img.style.width = "92px";
        img.style.height = "62px";
        img.style.left = "52%";
        img.style.top = "31%";
    } else if (url.includes("eyes3")) {
        img.style.width = "142px";
        img.style.height = "87px";
        img.style.left = "54%";
        img.style.top = "32%";
    } else if (url.includes("eyes4")) {
        img.style.width = "125px";
        img.style.height = "32px";
        img.style.left = "53%";
        img.style.top = "30%";
    } else if (url.includes("hair1")) {
        img.style.width = "180px";
        img.style.height = "170px";
        img.style.left = "52%";
        img.style.top = "27%";
    } else if (url.includes("hair2")) {
        img.style.width = "165px";
        img.style.height = "137px";
        img.style.left = "52%";
        img.style.top = "27%";
    } else if (url.includes("hair3")) {
        img.style.width = "244px";
        img.style.height = "230px";
        img.style.left = "54%";
        img.style.top = "24%";
    } else if (url.includes("hair4")) {
        img.style.width = "316px";
        img.style.height = "321px";
        img.style.left = "51%";
        img.style.top = "49%";
    } else if (url.includes("hair5")) {
        img.style.width = "212px";
        img.style.height = "348px";
        img.style.left = "51%";
        img.style.top = "48%";
    } else if (url.includes("hair6")) {
        img.style.width = "209px";
        img.style.height = "220px";
        img.style.left = "51%";
        img.style.top = "35%";
    } else if (url.includes("mouth1")) {
        img.style.width = "55px";
        img.style.height = "25px";
        img.style.left = "52%";
        img.style.top = "48%";
    } else if (url.includes("mouth2")) {
        img.style.width = "80px";
        img.style.height = "30px";
        img.style.left = "54%";
        img.style.top = "48%";
    } else if (url.includes("mouth3")) {
        img.style.width = "50px";
        img.style.height = "25px";
        img.style.left = "53%";
        img.style.top = "48%";
    } else if (url.includes("mouth4")) {
        img.style.width = "45px";
        img.style.height = "20px";
        img.style.left = "53%";
        img.style.top = "48%";
    } else if (url.includes("mouth5")) {
        img.style.width = "30px";
        img.style.height = "25px";
        img.style.left = "53%";
        img.style.top = "48%";
    }

    preview.appendChild(img);

    var input = document.getElementById(type + '-input');
    input.value = url;
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('.tab-link').click();
});
