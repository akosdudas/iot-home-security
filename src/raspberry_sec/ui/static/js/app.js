// Base
$(document).ready(function() {
    if(window.location.pathname === '/login')
        $('#logout_btn').hide();
});

// Feed
$('.dropdown-menu li a').click(function() {
    var selected = $(this).text();
    $('#feed_dropdown:first-child').html(selected + ' <span class="caret"></span>');

    var ws = new WebSocket('wss://' + location.host + '/feed/websocket');

    ws.onmessage = function(content) {
       $('#feed_content').html(content.data);
       setTimeout(() => ws.send(selected), 1000);
    };

    ws.onopen = function(e) {
        ws.send(selected);
    };
});

// Configure
$('#cfg_form').submit(function(e){
    $.ajax({
        type : 'POST',
        data: $('#cfg_form').serialize(),
        url : 'configure',
        beforeSend: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', getXSRFCookie());
        },
        success : function(data){
            $('#cfg_info_alert').html(data)
            $('#cfg_info_alert').fadeTo(2000, 500).slideUp(500, function(){
                $('#cfg_info_alert-alert').slideUp(500);
            });
        }
    });
    return false;
});

// Control
function ctrlButtonSend(onStr, zone) {
    $.ajax({
        type : 'POST',
        data: {'on': onStr, 'zone': zone},
        beforeSend: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', getXSRFCookie());
        },
        url : 'control',
        success : function(data){
            location.reload();
        }
    });
}

function onDeleteZone(zone) {
	$.ajax({
	    url: '/zones/' + zone,
	    type: 'POST',
	    data: { 'zone': zone },
        beforeSend: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', getXSRFCookie());
        },
	    success: function(result) {
                location.reload();
	    }
	});
}

function initZones(zones) {
	var zoneTable = document.getElementById("controltable");
	jQuery.each(zones, function(i, value) {
		var button = i.replace(/\s/g, '_');
		zoneTable.insertAdjacentHTML('afterBegin','<tr><td>' + i.charAt(0).toUpperCase() + i.slice(1) + '</td><td><input type="checkbox" name="zone" value="' + i + '"></td><td><input type="button" id="'+ button +'" value="Delete"></td></tr>');
		$('#' + button).click(
			function() {
				onDeleteZone(i);
		});
	});
	zoneTable.insertAdjacentHTML('afterbegin','<tr><th>Zones:</th><th>Arm:</th><th></th></tr>');
}

function onAddZone(zone) {
	$.ajax({
	   url: 'zones',
	   type: 'POST',
           data: {'zone' : zone},
       	   beforeSend: function(xhr) {
             xhr.setRequestHeader('X-CSRFToken', getXSRFCookie());
           },
	   success: function(response) {
                location.reload();
	   }
	});
}

$('#add_zone').click(
	function() {
		var zoneTable = document.getElementById("zones");
		var zone = document.getElementById("text_zone").value;
		var zone_id = zone.toLowerCase();
		onAddZone(zone);
});

window.onload = function() {
	
	if (window.location.href.match('control') != null) {
		
		$.getJSON('zones', function(data) {
   		 initZones(data)
		});

		var addButton = document.getElementById("add_zone");	
		var zoneTable = document.getElementById("zones");

		addButton.onclick = function() {
		  var zone = document.getElementById("text_zone").value;
		  var zone_id = zone.toLowerCase();
		  zoneTable.innerHTML += '<input type="checkbox" name="zone" value="' + zone_id + '">' + zone;
		}
	}
}

function printChecked(){
	var items = document.getElementsByName('zone');
	var selectedItems ='{';
	for(var i = 0; i < items.length; i++)
		if(items[i].type == 'checkbox'){
			selectedItems += '\"';
			selectedItems += items[i].value + '\":';
			if(items[i].checked == true)
				selectedItems += 'true ,';
			else
				selectedItems += 'false ,';
	}
	selectedItems = selectedItems.slice(0,-1);
	selectedItems += '}';
	if(!selectedItems)
		alert('No zone selected, please select one');
	return selectedItems;
}

$('#ctrl_start').click(
    function(){
	var zone = printChecked();
        ctrlButtonSend('true', zone);
});

$('#ctrl_stop').click(
    function(){
	zone = null
        ctrlButtonSend('false', zone);
});

// Login
$('#login_form').submit(function(){
    $('#logout_btn').show();
    $.ajax({
        type : 'POST',
        data : $('#login_form').serialize(),
        beforeSend: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', getXSRFCookie());
        },
        url : 'login'
    });
});
$('#login_pwd').on('keypress', function(e) {
    if (e.which == 32)
        return false;
});

// Logout
$('#logout_btn').click(function(){
    $.ajax({
        type : 'DELETE',
        url : 'login',
        beforeSend: function(xhr) {
            xhr.setRequestHeader('X-CSRFToken', getXSRFCookie());
        },
        success : function(data){
            location.reload();
        }
    });
});

// XSRF Protection
function getXSRFCookie() {
    var r = document.cookie.match('\\b_xsrf=([^;]*)\\b');
    return r ? r[1] : undefined;
}

