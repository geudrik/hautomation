
function fnInitListeners() {

    // Listener for clicking of one of the X to delete an API key
    $('[name=button-delete-api-key]').on("click", function() {

        var row = $(this).closest('tr');
        var key_id = row.attr('api-key-id');

        $.ajax({
            url: "/api/v1/users/apikey/"+key_id,
            type: 'DELETE',
            success: function(data) {

                // Remove our row from the UI
                row.remove();

                // Display a success notification
                new PNotify({
                    title: 'Success',
                    text: data.message,
                    type: 'success',
                    styling: 'bootstrap3'
                });

            },
            error: function(data) {
                new PNotify({
                    title: 'Error',
                    text: data.responseJSON.error,
                    type: 'error',
                    styling: 'bootstrap3'
                });
            }
        })

    });

    // On click in our description TD (EDIT our keys description)
    $('[name=table-api-keys-key-desc]').on("click", function() {

        var that = $(this);

        // Do nothing if we already have an input box
        if ( that.find('input').length > 0 ) {
            return;
        }

        var current_text = that.text();
        var input = $('<input>').val(current_text);

        // I suck at JS... for some reason, having only .html(input) _appends_ the input
        $(this).html("");
        $(this).html(input);
        input.focus();

        // Handle clicking off the input box
        input.on("blur", function(event_data) {

            // Set a var with our new text and delete the input box
            var input_text = input.val();
            that.find('input').remove();

            // If we've either cleared the text box, or made no changes, put it back and do nothing
            if ( input_text.length == 0 || input_text === current_text ) {
                that.text(current_text);

            // Elsewise, request an update to the key description
            } else {

                var new_desc = input_text;
                var key_id = that.closest('tr').attr('api-key-id');

                $.ajax({
                    url: "/api/v1/users/apikey/"+key_id,
                    type: "PUT",
                    data: { 'description': new_desc },
                    success: function(data) {

                        // Set TD to the next value
                        that.text(input_text);

                    },
                    error: function(data) {

                        // Reset TD to original value
                        that.text(current_text);

                        new PNotify({
                            title: 'Error',
                            text: data.responseJSON.error,
                            type: 'error',
                            styling: 'bootstrap3'
                        });
                    }
                })

            }

        });

    });



}

// Page is loaded, f-f-fire it up
$(document).ready(function() {

    // Bind our listeners
    fnInitListeners();

    // Get our API Keys
    $.ajax({
        url: "/api/v1/users/apikeys",
        type: "GET",
        success: function(data) {

            for ( var i=0; i < data.items.length; i++ ) {
                $('#table-api-keys tbody').append(
                    "<tr api-key-id=\""+data.items[i].api_key_id+"\">"+
                    "<th scope=\"row\"><i class=\"fa fa-close\" name=\"button-delete-api-key\"></th>"+
                    "<td><code>"+data.items[i].api_key+"</code></td>"+
                    "<td name=\"table-api-keys-key-desc\">"+data.items[i].description+"</td>"+
                    "</tr>"
                );
            };

            // Reinit our listeners
            fnInitListeners();

        },

        failure: function(data) {
            new PNotify({
                title: 'Error',
                text: data.responseJSON.error,
                type: 'error',
                styling: 'bootstrap3'
            });
        }

    });

});

// Listener for clicking of the create API key button
$('#button-new-api-key').on("click", function() {
    $.ajax({
        url: "/api/v1/users/apikey",
        type: "POST",
        data: {'description':'My Brand New API Key'},
        success: function(data) {

            // Add our new key row
            $('#table-api-keys tbody').append(
                "<tr api-key-id=\""+data.api_key_id+"\">"+
                "<th scope=\"row\"><i class=\"fa fa-close\" name=\"button-delete-api-key\"></th>"+
                "<td><code>"+data.api_key+"</code></td>"+
                "<td name=\"table-api-keys-key-desc\">"+data.description+"</td>"+
                "</tr>"
            );

            // Reinit our listeners since we just added a row
            fnInitListeners();
        },
        error: function(data) {
            new PNotify({
                title: 'Error',
                text: data.responseJSON.error,
                type: 'error',
                styling: 'bootstrap3'
            });
        }
    })

});
