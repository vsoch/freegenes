jQuery(document).ready(function($) {  
    $('body').scrollspy({ target: '#header', offset: 400});
    $(window).bind('scroll', function() {
         if ($(window).scrollTop() > 50) {
             $('#header').addClass('navbar-fixed-top');
         }
         else {
             $('#header').removeClass('navbar-fixed-top');
         }
    });
    $('a.scrollto').on('click', function(e){
        var target = this.hash;        
        e.preventDefault();
        $('body').scrollTo(target, 800, {offset: -700, 'axis':'y', easing:'easeOutQuad'});
        if ($('.navbar-collapse').hasClass('show')){
	    $('.navbar-collapse').removeClass('show');
        }	
    });
    $(window).bind('scroll', function() {
         if ($(window).scrollTop() > 50) {
             $('#header').addClass('navbar-fixed-top');
         }
         else {
             $('#header').removeClass('navbar-fixed-top');
         }
    });
});
