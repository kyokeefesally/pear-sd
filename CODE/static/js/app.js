$(document).ready(function(){
    //connect to the socket server.
    var socketio = io.connect('http://' + document.domain + ':' + location.port + '/web');
    //var serials_received = [];

    var serial_value = 'unknown'
    var paired_status = 'unknown'
    var usb_state = 'unknown'

    $('dd.paired_status').html(paired_status);
    $('dd.serial_value').html(serial_value);
    $('dd.usb_state').html(usb_state);

    ////////////////////////////////////////////////////
    //   receive usb data from server and update UI
    ////////////////////////////////////////////////////
    socketio.on('notify_web_clients', function(msg) {

        // define message variables
        serial_value = msg.serial_value
        paired_status = msg.paired_status
        usb_state = msg.usb_state

        // console log message from server
        console.log(msg);
        console.log(serial_value);
        console.log(paired_status);
        console.log(usb_state);

        // update UI with message values

        if (paired_status === 'paired') {

            $('button#not_paired').hide()
            $('button#paired').show()

        }

        if (paired_status === 'not_paired') {

            $('button#paired').hide()
            $('button#not_paired').show()

        }

        if (paired_status === 'no_device') {
            $('button#not_paired').hide()
            $('button#paired').hide()
        }

        //$('#log').html(usb_state + " " + serial_value + " " + paired_status);
        $('dd.paired_status').html(paired_status);
        $('dd.serial_value').html(serial_value);
        $('dd.usb_state').html(usb_state);

    });

    ////////////////////////////////////////////////////
    //   pairing button 
    ////////////////////////////////////////////////////

    // send message to server when UNPAIR button is clicked
    $('button#paired').click(function(event) {
        console.log("button clicked");
        socketio.emit('pairing_button', {button_status: 'unpair', serial_value: serial_value});
        console.log("emit message: {button_status: 'unpair', serial_value: " + serial_value);
    });

    // send message to server when PAIR button is clicked
    $('button#not_paired').click(function(event) {
        console.log("button clicked");
        socketio.emit('pairing_button', {button_status: 'pair', serial_value: serial_value});
        console.log("emit message: {button_status: 'pair', serial_value: " + serial_value);
    });

/*
    // send message to server when SERVER PULL button is clicked
    $('button#server_pull').click(function(event) {
        console.log("button clicked");
        socketio.emit('client_pull_usb_values');
    });
*/
});