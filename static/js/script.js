/*
    jQuery for MaterializeCSS initialization
*/

$(document).ready(function(){
  $(".sidenav").sidenav({edge: "right"});
  $('.collapsible').collapsible();
  $('.tooltipped').tooltip();
  $("select").formSelect();
  $('.datepicker').datepicker({
    format: "dd mmm, yyyy",
    yearRange: 1,
    showClearBtn: true,
    i18n: {
      done: "Select"
    }
  });
  $('.timepicker').timepicker();
});

