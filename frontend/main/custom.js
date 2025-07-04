(function ($) {
	"use strict";

	// Header background switch on scroll
	$(window).scroll(function() {
	  var scroll = $(window).scrollTop();
	  var box = $('.header-text').height();
	  var header = $('header').height();
	  if (scroll >= box - header) {
	    $("header").addClass("background-header");
	  } else {
	    $("header").removeClass("background-header");
	  }
	});

	// Isotope filtering
	var $grid = $(".grid").isotope({
	  itemSelector: ".all",
	  percentPosition: true,
	  masonry: {
	    columnWidth: ".all"
	  }
	});

	$('.filters ul li').click(function(){
	  $('.filters ul li').removeClass('active');
	  $(this).addClass('active');
	  var data = $(this).attr('data-filter');
	  $grid.isotope({ filter: data });
	});

	// Accordion
	const Accordion = {
	  settings: {
	    first_expanded: false,
	    toggle: false
	  },
	  openAccordion: function(toggle, content) {
	    if (content.children.length) {
	      toggle.classList.add("is-open");
	      let final_height = Math.floor(content.children[0].offsetHeight);
	      content.style.height = final_height + "px";
	    }
	  },
	  closeAccordion: function(toggle, content) {
	    toggle.classList.remove("is-open");
	    content.style.height = 0;
	  },
	  init: function(el) {
	    const _this = this;
	    let is_first_expanded = _this.settings.first_expanded;
	    if (el.classList.contains("is-first-expanded")) is_first_expanded = true;
	    let is_toggle = _this.settings.toggle;
	    if (el.classList.contains("is-toggle")) is_toggle = true;
	    const sections = el.getElementsByClassName("accordion");
	    const all_toggles = el.getElementsByClassName("accordion-head");
	    const all_contents = el.getElementsByClassName("accordion-body");
	    for (let i = 0; i < sections.length; i++) {
	      const toggle = all_toggles[i];
	      const content = all_contents[i];
	      toggle.addEventListener("click", function() {
	        if (!is_toggle) {
	          for (let a = 0; a < all_contents.length; a++) {
	            _this.closeAccordion(all_toggles[a], all_contents[a]);
	          }
	          _this.openAccordion(toggle, content);
	        } else {
	          if (toggle.classList.contains("is-open")) {
	            _this.closeAccordion(toggle, content);
	          } else {
	            _this.openAccordion(toggle, content);
	          }
	        }
	      });
	      if (i === 0 && is_first_expanded) {
	        _this.openAccordion(toggle, content);
	      }
	    }
	  }
	};
	(function() {
	  const accordions = document.getElementsByClassName("accordions");
	  for (let i = 0; i < accordions.length; i++) {
	    Accordion.init(accordions[i]);
	  }
	})();

	// Owl Carousels
	$('.owl-service-item').owlCarousel({
	  items:3, loop:true, dots: true, nav: true, autoplay: true, margin:30,
	  responsive:{ 0:{items:1}, 600:{items:2}, 1000:{items:3} }
	});
	$('.owl-courses-item').owlCarousel({
	  items:4, loop:true, dots: true, nav: true, autoplay: true, margin:30,
	  responsive:{ 0:{items:1}, 600:{items:2}, 1000:{items:4} }
	});

	// Menu dropdown toggle
	if($('.menu-trigger').length){
	  $(".menu-trigger").on('click', function() {
	    $(this).toggleClass('active');
	    $('.header-area .nav').slideToggle(200);
	  });
	}

	// Smooth scroll to anchor only for href beginning with #
	$('.scroll-to-section a[href^="#"]').on('click', function (e) {
	  e.preventDefault();
	  $(document).off("scroll");
	  $('.scroll-to-section a').removeClass('active');
	  $(this).addClass('active');
	  var target = $(this.hash);
	  if (target.length) {
	    $('html, body').stop().animate({ scrollTop: target.offset().top - 80 }, 700, 'swing', function () {
	      window.location.hash = target;
	      $(document).on("scroll", onScroll);
	    });
	  }
	});

	function onScroll() {
	  var scrollPos = $(document).scrollTop();
	  $('.nav a[href^="#"]').each(function () {
	    var refElement = $($(this).attr("href"));
	    if (refElement.length && refElement.position().top <= scrollPos && refElement.position().top + refElement.height() > scrollPos) {
	      $('.nav ul li a').removeClass("active");
	      $(this).addClass("active");
	    } else {
	      $(this).removeClass("active");
	    }
	  });
	}

	// Page loading animation
	$(window).on('load', function() {
	  if($('.cover').length){
	    $('.cover').parallax({ imageSrc: $('.cover').data('image'), zIndex: '1' });
	  }
	  $("#preloader").animate({'opacity': '0'}, 600, function(){
	    setTimeout(function(){
	      $("#preloader").css("visibility", "hidden").fadeOut();
	    }, 300);
	  });
	});

	// Dropdown submenu behavior
	const dropdownOpener = $('.main-nav ul.nav .has-sub > a');
	if (dropdownOpener.length) {
	  dropdownOpener.each(function () {
	    var _this = $(this);
	    _this.on('click', function (e) {
	      var parent = _this.parent('li');
	      var submenu = parent.find('> ul.sub-menu');
	      if (submenu.is(':visible')) {
	        submenu.slideUp(450);
	        parent.removeClass('is-open-sub');
	      } else {
	        parent.addClass('is-open-sub');
	        parent.siblings().removeClass('is-open-sub').find('.sub-menu').slideUp(250);
	        submenu.slideDown(250);
	      }
	      e.preventDefault();
	    });
	  });
	}

	// Visibility check and counter animation
	function visible($t) {
	  if (!$t || !$t.offset()) return false;
	  var $w = $(window),
	      viewTop = $w.scrollTop(),
	      viewBottom = viewTop + $w.height(),
	      _top = $t.offset().top,
	      _bottom = _top + $t.height();
	  return (_bottom <= viewBottom && _top >= viewTop && $t.is(':visible'));
	}

	$(window).scroll(function() {
	  if (visible($('.count-digit'))) {
	    if ($('.count-digit').hasClass('counter-loaded')) return;
	    $('.count-digit').addClass('counter-loaded');
	    $('.count-digit').each(function() {
	      var $this = $(this);
	      $({ Counter: 0 }).animate({ Counter: $this.text() }, {
	        duration: 3000,
	        easing: 'swing',
	        step: function () { $this.text(Math.ceil(this.Counter)); }
	      });
	    });
	  }
	});

})(window.jQuery);
