var interval = 1000;

function refreshMatches() {
    $.ajax({
        url: '/matches/',
        success: function(data) {
            $('#id_refresh').html(data);
        },
        complete: function (data) {
            $('#dataTable').append('<tr><td>Sahil P. vs Rohan Mann</td><td>40</td></tr>');
            $('#dataTable').append('<tr><td>Navdeep vs Arun Kumar</td><td>20</td></tr>');
            $('#dataTable').append('<tr><td>Himanshi vs Murari Jha</td><td>100</td></tr>');
            $('#dataTable').append('<tr><td>Rohit Garg vs Dinesh Singh</td><td>20</td></tr>');
            setTimeout(refreshMatches, interval);
        }
    });
}

// Note that I'm using complete, not success, to schedule the next call,
// so that an interruption (temporary drop in your 'net connection, whatever) doesn't kill the process.

$(function(){
    setTimeout(refreshMatches, interval);
});