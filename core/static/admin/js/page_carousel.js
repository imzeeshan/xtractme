// Wait for django.jQuery to be available
(function() {
    'use strict';
    
    function initCarouselWhenReady() {
        // Check if django.jQuery is available
        if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined') {
            var $ = django.jQuery;
            initPageCarousel($);
            setupEventHandlers($);
        } else if (typeof jQuery !== 'undefined') {
            // Fallback to global jQuery if available
            var $ = jQuery;
            initPageCarousel($);
            setupEventHandlers($);
        } else {
            // Wait a bit more for jQuery to load
            setTimeout(initCarouselWhenReady, 50);
        }
    }
    
    function setupEventHandlers($) {
        // Initialize carousel when document is ready
        $(document).ready(function() {
            // Wait a bit for Django admin to fully initialize
            setTimeout(function() {
                initPageCarousel($);
            }, 200);
        });
        
        // Re-initialize when inlines are added/removed
        $(document).on('formset:added formset:removed', function() {
            // Remove existing carousel and reinitialize
            $('.page-carousel-container').remove();
            setTimeout(function() {
                initPageCarousel($);
            }, 300);
        });
    }
    
    function initPageCarousel($) {
        // Find inline groups that contain page inlines
        var $inlineGroups = $('.inline-group').filter(function() {
            // Check if this group contains page preview items
            return $(this).find('.page-preview-carousel-item').length > 0;
        });
        
        $inlineGroups.each(function() {
            var $group = $(this);
            
            // Skip if carousel already initialized
            if ($group.find('.page-carousel-container').length > 0) {
                return;
            }
            
            // Find all inline-related divs (each represents a page)
            var $inlineForms = $group.find('.inline-related:not(.empty-form)').filter(function() {
                // Only include forms that have a preview item (i.e., existing pages)
                return $(this).find('.page-preview-carousel-item').length > 0;
            });
            
            if ($inlineForms.length === 0) {
                return; // No pages to show
            }
            
            // Get page numbers and sort forms by page number
            var formsWithPageNum = [];
            $inlineForms.each(function() {
                var $form = $(this);
                var $previewItem = $form.find('.page-preview-carousel-item');
                var pageNum = parseInt($previewItem.data('page-number')) || 0;
                formsWithPageNum.push({
                    $form: $form,
                    pageNumber: pageNum
                });
            });
            
            // Sort by page number
            formsWithPageNum.sort(function(a, b) {
                return a.pageNumber - b.pageNumber;
            });
            
            if (formsWithPageNum.length === 0) {
                return;
            }
            
            // Create carousel container
            var $carouselContainer = $('<div>', {
                'class': 'page-carousel-container'
            });
            
            // Create navigation controls
            var $controls = $('<div>', {
                'class': 'page-carousel-controls'
            });
            
            var $nav = $('<div>', {
                'class': 'page-carousel-nav'
            });
            
            var $prevBtn = $('<button>', {
                'class': 'page-carousel-btn',
                text: '← Previous Page',
                type: 'button'
            });
            
            var $nextBtn = $('<button>', {
                'class': 'page-carousel-btn',
                text: 'Next Page →',
                type: 'button'
            });
            
            var $indicator = $('<span>', {
                'class': 'page-carousel-indicator',
                text: 'Page ' + formsWithPageNum[0].pageNumber + ' of ' + formsWithPageNum.length
            });
            
            $nav.append($prevBtn, $indicator, $nextBtn);
            $controls.append($nav);
            $carouselContainer.append($controls);
            
            // Hide all forms except the first one
            formsWithPageNum.forEach(function(item, index) {
                if (index > 0) {
                    item.$form.hide();
                }
            });
            
            // Carousel state
            var currentIndex = 0;
            
            function updateCarousel() {
                // Hide all forms
                formsWithPageNum.forEach(function(item) {
                    item.$form.hide();
                });
                
                // Show current form
                if (formsWithPageNum[currentIndex]) {
                    formsWithPageNum[currentIndex].$form.show();
                }
                
                // Update buttons
                $prevBtn.prop('disabled', currentIndex === 0);
                $nextBtn.prop('disabled', currentIndex === formsWithPageNum.length - 1);
                
                // Update indicator
                var currentPageNum = formsWithPageNum[currentIndex].pageNumber;
                $indicator.text('Page ' + currentPageNum + ' of ' + formsWithPageNum.length);
                
                // Scroll to top of the inline form
                if (formsWithPageNum[currentIndex]) {
                    var offset = formsWithPageNum[currentIndex].$form.offset();
                    if (offset) {
                        $('html, body').animate({
                            scrollTop: offset.top - 100
                        }, 300);
                    }
                }
            }
            
            // Navigation handlers
            $prevBtn.on('click', function(e) {
                e.preventDefault();
                if (currentIndex > 0) {
                    currentIndex--;
                    updateCarousel();
                }
            });
            
            $nextBtn.on('click', function(e) {
                e.preventDefault();
                if (currentIndex < formsWithPageNum.length - 1) {
                    currentIndex++;
                    updateCarousel();
                }
            });
            
            // Keyboard navigation (when carousel container or forms are focused)
            $group.on('keydown', function(e) {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                    // Don't interfere with form inputs
                    return;
                }
                if (e.key === 'ArrowLeft' && currentIndex > 0) {
                    e.preventDefault();
                    currentIndex--;
                    updateCarousel();
                } else if (e.key === 'ArrowRight' && currentIndex < formsWithPageNum.length - 1) {
                    e.preventDefault();
                    currentIndex++;
                    updateCarousel();
                }
            });
            
            // Insert carousel controls after the heading
            var $heading = $group.find('h2, .inline-heading').first();
            if ($heading.length) {
                $carouselContainer.insertAfter($heading);
            } else {
                $group.prepend($carouselContainer);
            }
            
            // Initialize
            updateCarousel();
        });
    }
    
    // Start initialization
    initCarouselWhenReady();
})();
