$(document).ready(function(){
  $(window).on("resize",
    function(){
      var ihh = $('#logo').height()/2;
      $("#top-stripe").height(ihh+25px);
    );
  });
});