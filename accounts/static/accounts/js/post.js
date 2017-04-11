/**
 * Created by Raymond Puisha on 09.04.2017.
 */

(function($) {
    'use strict';
    $(function() {
        $('#post-form').on('submit', function(event) {
            event.preventDefault();
            create_post();
        });

       function create_post() {
            console.log($('#post-form').serialize())
            $.ajax({
                    url : "",
                    type : "POST",
                    data : $('#post-form').serialize(),

                    // handle a successful response
                    success : function(json) {
                        $(':input','#post-form').not(':button, :submit, :reset, :hidden').val('')
                        //not(':button, :submit, :reset, :hidden').val('')
                        console.log(json); // log the returned json to the console
                        console.log("success"); // another sanity check
                        $('#result').text(JSON.stringify(json));
                        $('#result').css('background-color', 'lightgreen');
                    },

                    // handle a non-successful response
                    error : function(xhr,errmsg,err) {
                        console.log(errmsg);
                        $('#result').text(xhr.status + ": " + xhr.responseText);
                        $('#result').css('background-color', 'lightpink');
                    }
            });
       };
   });
})(django.jQuery);
