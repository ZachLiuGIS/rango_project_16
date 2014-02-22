$(function(){
    $('#likes').click(function() {
       var catid;
        catid = $(this).data('catid');
        console.log(catid);

        $.ajax({
            method: "GET",
            url: "/rango/like_category",
            data: {category_id: catid},
            success: function(data) {
                var data = $.parseJSON(data);
                console.log(data);
                $('#like_count').html(data.likes);
                $('#likes').hide();
            },
            error: function(err) {
                console.log(err);
            }
        });
    });

    $('#suggestion').keyup(function(){
        var query = $(this).val();
        $.get('/rango/suggest_category', {suggestion: query}, function(results){
            $('#cats').html(results);
        });
    });

    $('.rango-add-page').click(function(){
        var $this = $(this);
        var category_id = $this.data('catid');
        var url = $this.data('url');
        var title = $this.data('title');

        $.get('/rango/auto_add_page', {category_id: category_id, url: url, title: title}, function(results){
            $('.category-pages').html(results);
        })
    });
});